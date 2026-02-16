"""USB/directory scanning with mutagen audio metadata extraction."""

import sqlite3
from pathlib import Path

import mutagen

from . import db


AUDIO_EXTENSIONS = {
    ".mp3", ".wav", ".flac", ".aiff", ".aif", ".aac", ".m4a",
    ".ogg", ".opus", ".wma", ".alac"
}


def scan_directory(conn: sqlite3.Connection, directory: str, label: str):
    """
    Walk directory tree recursively, extract audio metadata with mutagen, insert into tracks table.

    Args:
        conn: SQLite database connection
        directory: Root directory to scan (string or Path-like)
        label: Source label for scanned files (e.g. "USB1", "USB2")
    """
    directory = Path(directory)
    _validate_directory(directory)

    print(f"Scanning {directory} with label '{label}'...")

    count = 0
    for audio_file in directory.rglob("*"):
        # Skip non-files and non-audio files
        if not audio_file.is_file():
            continue
        if audio_file.suffix.lower() not in AUDIO_EXTENSIONS:
            continue

        # Extract metadata
        metadata = _extract_metadata(audio_file)
        if metadata is None:
            print(f"  [WARN] Skipped unreadable file: {audio_file}")
            continue

        # Insert/update in database
        try:
            _insert_or_update_track(conn, audio_file, label, metadata)
            count += 1

            # Print progress every 100 tracks
            if count % 100 == 0:
                print(f"  Indexed {count} tracks...")

        except sqlite3.Error as e:
            print(f"  [WARN] Database error for {audio_file}: {e}")
            continue

    # Final commit
    conn.commit()
    print(f"Scan complete. Indexed {count} tracks.")


def _validate_directory(directory: Path):
    """Validate that directory exists and is readable."""
    if not directory.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")
    if not directory.is_dir():
        raise NotADirectoryError(f"Not a directory: {directory}")


def _extract_metadata(filepath: Path) -> dict | None:
    """
    Extract audio metadata from file using mutagen.

    Returns:
        dict with keys: title, artist, album, genre, bpm, musical_key, duration_sec, bitrate, sample_rate, file_format
        or None if file is unreadable
    """
    try:
        audio = mutagen.File(str(filepath))
        if audio is None:
            return None

        # Extract basic info from .info attribute (available on all formats)
        duration_sec = audio.info.length if hasattr(audio.info, "length") else None
        bitrate = audio.info.bitrate if hasattr(audio.info, "bitrate") else None
        sample_rate = audio.info.sample_rate if hasattr(audio.info, "sample_rate") else None

        # Format as file extension
        file_format = filepath.suffix.lower()

        # Extract tags based on format
        metadata = {
            "title": None,
            "artist": None,
            "album": None,
            "genre": None,
            "bpm": None,
            "musical_key": None,
            "duration_sec": duration_sec,
            "bitrate": bitrate,
            "sample_rate": sample_rate,
            "file_format": file_format,
            "comments": None,
            "label": None,
            "remixer": None,
        }

        # Format-specific tag extraction
        if hasattr(audio, "tags") and audio.tags:
            tags = audio.tags

            # Check if it's ID3 (MP3, WAV, AIFF)
            if tags.__class__.__name__ == "ID3":
                metadata["title"] = _get_id3_text(tags, "TIT2")
                metadata["artist"] = _get_id3_text(tags, "TPE1")
                metadata["album"] = _get_id3_text(tags, "TALB")
                metadata["genre"] = _get_id3_text(tags, "TCON")
                metadata["bpm"] = db.safe_float(_get_id3_text(tags, "TBPM"))
                metadata["musical_key"] = _get_id3_text(tags, "TKEY")
                metadata["comments"] = _get_id3_text(tags, "COMM")
                metadata["remixer"] = _get_id3_text(tags, "TPE4")
                metadata["label"] = _get_id3_text(tags, "TPUB")

            # Check if it's Vorbis (FLAC, OGG, OPUS)
            elif tags.__class__.__name__ == "VorbisComment":
                metadata["title"] = _get_vorbis_text(tags, "TITLE")
                metadata["artist"] = _get_vorbis_text(tags, "ARTIST")
                metadata["album"] = _get_vorbis_text(tags, "ALBUM")
                metadata["genre"] = _get_vorbis_text(tags, "GENRE")
                metadata["bpm"] = db.safe_float(_get_vorbis_text(tags, "BPM"))
                # Try multiple key field names
                metadata["musical_key"] = (
                    _get_vorbis_text(tags, "INITIALKEY")
                    or _get_vorbis_text(tags, "KEY")
                    or _get_vorbis_text(tags, "TONALITY")
                )
                metadata["comments"] = _get_vorbis_text(tags, "COMMENT")
                metadata["remixer"] = _get_vorbis_text(tags, "REMIXER")
                metadata["label"] = _get_vorbis_text(tags, "LABEL")

            # Check if it's MP4 (M4A, AAC, ALAC)
            elif tags.__class__.__name__ == "Atoms":
                metadata["title"] = _get_mp4_text(tags, "©nam")
                metadata["artist"] = _get_mp4_text(tags, "©ART")
                metadata["album"] = _get_mp4_text(tags, "©alb")
                metadata["genre"] = _get_mp4_text(tags, "©gen")
                metadata["bpm"] = db.safe_float(_get_mp4_text(tags, "tmpo"))
                metadata["musical_key"] = _get_mp4_text(tags, "tkey")
                metadata["comments"] = _get_mp4_text(tags, "©cmt")
                metadata["remixer"] = _get_mp4_text(tags, "remixer")
                metadata["label"] = _get_mp4_text(tags, "label")

            # Check if it's ASF/WMA
            elif tags.__class__.__name__ == "ASF":
                metadata["title"] = _get_asf_text(tags, "Title")
                metadata["artist"] = _get_asf_text(tags, "Author")
                metadata["album"] = _get_asf_text(tags, "WM/AlbumTitle")
                metadata["genre"] = _get_asf_text(tags, "WM/Genre")
                metadata["bpm"] = db.safe_float(_get_asf_text(tags, "WM/BeatsPerMinute"))
                metadata["comments"] = _get_asf_text(tags, "Description")
                metadata["remixer"] = _get_asf_text(tags, "WM/RemixedBy")
                metadata["label"] = _get_asf_text(tags, "WM/Publisher")
                # Musical key not standard in WMA, leave as None

        return metadata

    except Exception:
        # Silently skip unreadable files
        return None


def _get_id3_text(tags, key: str) -> str | None:
    """Safely extract text from ID3 tag."""
    try:
        if key in tags:
            value = tags[key].text
            if value and len(value) > 0:
                return str(value[0])
    except (KeyError, IndexError, AttributeError):
        pass
    return None


def _get_vorbis_text(tags, key: str) -> str | None:
    """Safely extract text from Vorbis comment."""
    try:
        if key in tags:
            value = tags[key]
            if value and len(value) > 0:
                return str(value[0])
    except (KeyError, IndexError, TypeError):
        pass
    return None


def _get_mp4_text(tags, key: str) -> str | None:
    """Safely extract text from MP4 atom."""
    try:
        if key in tags:
            value = tags[key]
            if value and len(value) > 0:
                # MP4 atoms often store as integers for tmpo (BPM)
                item = value[0]
                if isinstance(item, int):
                    return str(item)
                return str(item)
    except (KeyError, IndexError, TypeError):
        pass
    return None


def _get_asf_text(tags, key: str) -> str | None:
    """Safely extract text from ASF/WMA tag."""
    try:
        if key in tags:
            value = tags[key]
            if value and len(value) > 0:
                return str(value[0])
    except (KeyError, IndexError, TypeError):
        pass
    return None


def _insert_or_update_track(conn: sqlite3.Connection, filepath: Path, label: str, metadata: dict):
    """Insert or update a track in the database."""
    filepath_str = str(filepath)
    filename = filepath.name
    filename_lower = filename.lower()
    file_size = filepath.stat().st_size if filepath.exists() else None

    # Build values tuple
    values = (
        filepath_str,
        filename,
        filename_lower,
        label,
        metadata["title"],
        metadata["artist"],
        metadata["album"],
        metadata["genre"],
        metadata["bpm"],
        metadata["musical_key"],
        metadata["duration_sec"],
        metadata["bitrate"],
        metadata["sample_rate"],
        metadata["file_format"],
        file_size,
        metadata["comments"],
        metadata["label"],
        metadata["remixer"],
    )

    # Use ON CONFLICT to update existing tracks (but preserve rekordbox data)
    conn.execute("""
        INSERT INTO tracks (
            filepath, filename, filename_lower, source_label, title, artist, album, genre,
            bpm, musical_key, duration_sec, bitrate, sample_rate, file_format, file_size,
            comments, label, remixer
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(filepath) DO UPDATE SET
            filename = COALESCE(NULLIF(excluded.filename, ''), tracks.filename),
            source_label = excluded.source_label,
            title = COALESCE(NULLIF(excluded.title, ''), tracks.title),
            artist = COALESCE(NULLIF(excluded.artist, ''), tracks.artist),
            album = COALESCE(NULLIF(excluded.album, ''), tracks.album),
            genre = COALESCE(NULLIF(excluded.genre, ''), tracks.genre),
            bpm = COALESCE(excluded.bpm, tracks.bpm),
            musical_key = COALESCE(NULLIF(excluded.musical_key, ''), tracks.musical_key),
            duration_sec = COALESCE(excluded.duration_sec, tracks.duration_sec),
            bitrate = COALESCE(excluded.bitrate, tracks.bitrate),
            sample_rate = COALESCE(excluded.sample_rate, tracks.sample_rate),
            file_format = COALESCE(NULLIF(excluded.file_format, ''), tracks.file_format),
            file_size = COALESCE(excluded.file_size, tracks.file_size),
            comments = COALESCE(NULLIF(excluded.comments, ''), tracks.comments),
            label = COALESCE(NULLIF(excluded.label, ''), tracks.label),
            remixer = COALESCE(NULLIF(excluded.remixer, ''), tracks.remixer),
            date_indexed = datetime('now')
    """, values)
