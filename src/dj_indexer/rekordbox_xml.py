"""Import rekordbox XML collection via pyrekordbox."""

import sqlite3
from pathlib import Path

from pyrekordbox.rbxml import RekordboxXml
from tqdm import tqdm

from . import db


def import_xml(conn: sqlite3.Connection, xml_path: Path):
    """
    Import rekordbox XML collection export.

    Uses pyrekordbox.rbxml.RekordboxXml to parse the XML.
    Matches tracks by filename_lower, imports cue points and playlists.

    Args:
        conn: SQLite database connection
        xml_path: Path to rekordbox XML file
    """
    xml_path = Path(xml_path)
    if not xml_path.exists():
        raise FileNotFoundError(f"XML file not found: {xml_path}")

    print(f"\n{'='*60}")
    print(f"Importing Rekordbox XML Collection")
    print(f"{'='*60}")
    print(f"File: {xml_path}\n")

    # Phase 1: Parse XML
    print("[1/4] Parsing XML file...")
    try:
        xml = RekordboxXml(str(xml_path))
    except Exception as e:
        raise ValueError(f"Failed to parse XML file: {e}")

    print(f"      Product: {xml.product_name} {xml.product_version}")
    print(f"      Tracks: {xml.num_tracks}\n")

    # Phase 2: Load existing tracks and already-imported ones
    print("[2/4] Loading existing tracks from database...")
    cursor = conn.execute("SELECT id, filename_lower FROM tracks")
    existing_tracks = {row[1]: row[0] for row in cursor.fetchall()}

    # Load rb_track_id values of already-imported tracks
    cursor = conn.execute(
        "SELECT rb_track_id FROM tracks WHERE in_rekordbox = 1 AND rb_track_id IS NOT NULL"
    )
    already_imported = {row[0] for row in cursor.fetchall()}

    print(f"      Found {len(existing_tracks)} existing tracks ({len(already_imported)} already imported from rekordbox)\n")

    # Phase 3: Import tracks with progress bar
    print("[3/4] Importing tracks and metadata...")
    imported_count = 0
    skipped_count = 0
    already_done_count = 0

    for idx in tqdm(range(xml.num_tracks), desc="  Processing", unit="track"):
        try:
            track = xml.get_track(idx)
            if track is None:
                continue

            track_id_str = str(track.get("TrackID")) if track.get("TrackID") is not None else None

            # Skip if already imported in a prior run
            if track_id_str and track_id_str in already_imported:
                already_done_count += 1
                continue

            title = track.get("Name") or None
            artist = track.get("Artist") or None
            album = track.get("Album") or None
            genre = track.get("Genre") or None
            bpm = db.safe_float(track.get("AverageBpm"))
            musical_key = track.get("Tonality") or None
            comments = track.get("Comments") or None
            label = track.get("Label") or None
            remixer = track.get("Remixer") or None
            bitrate = db.safe_int(track.get("BitRate"))
            sample_rate = db.safe_int(track.get("SampleRate"))
            duration_sec = db.safe_float(track.get("TotalTime"))
            location = track.get("Location")

            # Extract filename from location URL
            filename = None
            if location:
                # Location is like "file://localhost/C:/path/to/Demo Track 1.mp3"
                # pyrekordbox auto-decodes it, so we can just use the filename
                try:
                    path_obj = Path(location)
                    filename = path_obj.name
                except Exception:
                    pass

            if not filename:
                skipped_count += 1
                continue

            filename_lower = filename.lower()

            # Check if track exists in database (match by filename_lower)
            if filename_lower in existing_tracks:
                # Update existing track with rekordbox data
                track_id = existing_tracks[filename_lower]
                conn.execute(
                    """
                    UPDATE tracks SET
                        title = COALESCE(NULLIF(?, ''), title),
                        artist = COALESCE(NULLIF(?, ''), artist),
                        album = COALESCE(NULLIF(?, ''), album),
                        genre = COALESCE(NULLIF(?, ''), genre),
                        bpm = COALESCE(?, bpm),
                        musical_key = COALESCE(NULLIF(?, ''), musical_key),
                        comments = COALESCE(NULLIF(?, ''), comments),
                        label = COALESCE(NULLIF(?, ''), label),
                        remixer = COALESCE(NULLIF(?, ''), remixer),
                        bitrate = COALESCE(?, bitrate),
                        sample_rate = COALESCE(?, sample_rate),
                        duration_sec = COALESCE(?, duration_sec),
                        in_rekordbox = 1,
                        rb_track_id = ?,
                        rb_location = ?,
                        date_indexed = datetime('now')
                    WHERE id = ?
                    """,
                    (
                        title,
                        artist,
                        album,
                        genre,
                        bpm,
                        musical_key,
                        comments,
                        label,
                        remixer,
                        bitrate,
                        sample_rate,
                        duration_sec,
                        track_id_str,
                        location,
                        track_id,
                    ),
                )
            else:
                # Insert new track from rekordbox XML (or update if filepath already exists)
                cursor = conn.execute(
                    """
                    INSERT INTO tracks (
                        filepath, filename, filename_lower, source_label,
                        title, artist, album, genre, bpm, musical_key,
                        duration_sec, bitrate, sample_rate, file_format,
                        comments, label, remixer, in_rekordbox, rb_track_id, rb_location
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(filepath) DO UPDATE SET
                        filename = excluded.filename,
                        filename_lower = excluded.filename_lower,
                        source_label = COALESCE(NULLIF(excluded.source_label, ''), source_label),
                        title = COALESCE(NULLIF(excluded.title, ''), title),
                        artist = COALESCE(NULLIF(excluded.artist, ''), artist),
                        album = COALESCE(NULLIF(excluded.album, ''), album),
                        genre = COALESCE(NULLIF(excluded.genre, ''), genre),
                        bpm = COALESCE(excluded.bpm, bpm),
                        musical_key = COALESCE(NULLIF(excluded.musical_key, ''), musical_key),
                        duration_sec = COALESCE(excluded.duration_sec, duration_sec),
                        bitrate = COALESCE(excluded.bitrate, bitrate),
                        sample_rate = COALESCE(excluded.sample_rate, sample_rate),
                        file_format = COALESCE(NULLIF(excluded.file_format, ''), file_format),
                        comments = COALESCE(NULLIF(excluded.comments, ''), comments),
                        label = COALESCE(NULLIF(excluded.label, ''), label),
                        remixer = COALESCE(NULLIF(excluded.remixer, ''), remixer),
                        in_rekordbox = 1,
                        rb_track_id = excluded.rb_track_id,
                        rb_location = excluded.rb_location,
                        date_indexed = datetime('now')
                    """,
                    (
                        location,
                        filename,
                        filename_lower,
                        "rekordbox XML",
                        title,
                        artist,
                        album,
                        genre,
                        bpm,
                        musical_key,
                        duration_sec,
                        bitrate,
                        sample_rate,
                        Path(filename).suffix.lower(),
                        comments,
                        label,
                        remixer,
                        1,
                        track_id_str,
                        location,
                    ),
                )
                # Get track_id for cue insertion
                cursor = conn.execute(
                    "SELECT id FROM tracks WHERE filepath = ?",
                    (location,),
                )
                row = cursor.fetchone()
                track_id = row[0] if row else None

            if track_id is None:
                skipped_count += 1
                continue

            imported_count += 1

            # Delete existing cue points (idempotent: safe for re-run)
            conn.execute("DELETE FROM cue_points WHERE track_id = ?", (track_id,))

            # Import cue points for this track
            if hasattr(track, "marks") and track.marks:
                for mark in track.marks:
                    cue_type = _get_cue_type(mark.get("Type"), mark.get("Num"))
                    position_sec = db.safe_float(mark.get("Start"))
                    cue_name = mark.get("Name") or None
                    cue_num = db.safe_int(mark.get("Num"))

                    conn.execute(
                        """
                        INSERT INTO cue_points (
                            track_id, cue_type, cue_name, cue_num, position_sec
                        )
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (track_id, cue_type, cue_name, cue_num, position_sec),
                    )

            # Commit every 100 imported tracks for incremental progress
            if imported_count % 100 == 0:
                conn.commit()

        except Exception as e:
            skipped_count += 1
            tqdm.write(f"  [WARN] Error importing track {idx}: {e}")
            continue

    print()  # Blank line after progress bar
    print(f"  ({imported_count} imported, {already_done_count} skipped - already done)\n")

    # Phase 4: Import playlists
    print("[4/4] Importing playlists...")
    # Delete all existing playlists (idempotent: safe for re-run)
    conn.execute("DELETE FROM playlists")
    # Then re-import from XML
    playlist_count = _import_playlists(conn, xml, existing_tracks)
    if playlist_count > 0:
        print(f"      {playlist_count} playlists imported\n")
    else:
        print(f"      No playlists found\n")

    # Final commit to flush all changes
    conn.commit()

    # Summary
    print(f"{'='*60}")
    print(f"Import Complete")
    print(f"{'='*60}")
    print(f"[+] Tracks processed:     {xml.num_tracks}")
    print(f"[+] Tracks imported:      {imported_count}")
    print(f"[+] Tracks already done:  {already_done_count}")
    print(f"[+] Tracks skipped:       {skipped_count}")
    print(f"[+] Playlists:            {playlist_count}")
    print(f"{'='*60}\n")


def _get_cue_type(type_val: str | int | None, num: int | None) -> str:
    """Convert rekordbox cue type and num to our cue_type format."""
    if num is None:
        num = -1

    # Type: "0" or 0 = cue, "1" or 1 = loop
    # Num: -1 = memory cue, 0-7 = hot cues A-H
    if num == -1:
        return "memory_cue"
    else:
        # Convert 0-7 to A-H
        return f"hot_cue_{chr(65 + num)}"


def _import_playlists(conn: sqlite3.Connection, xml, existing_tracks: dict):
    """Import playlists from rekordbox XML.

    Returns:
        int: Total number of playlists imported
    """
    root = xml.get_playlist()
    if root is None:
        return 0

    playlist_count = [0]  # Use list to allow modification in nested function

    def _process_node(node, parent_path: str = ""):
        """Recursively process playlist nodes."""
        if node.is_playlist and not node.is_folder:
            # This is a leaf playlist
            playlist_name = node.name
            playlist_path = f"{parent_path}/{playlist_name}" if parent_path else playlist_name

            # Get track IDs from playlist
            track_ids = node.get_tracks()
            if track_ids:
                for position, track_id in enumerate(track_ids, 1):
                    # Find the track by rb_track_id in our database
                    cursor = conn.execute(
                        "SELECT id FROM tracks WHERE rb_track_id = ?",
                        (str(track_id),),
                    )
                    row = cursor.fetchone()
                    if row:
                        local_track_id = row[0]
                        conn.execute(
                            """
                            INSERT INTO playlists (playlist_name, playlist_path, track_id, position)
                            VALUES (?, ?, ?, ?)
                            """,
                            (playlist_name, playlist_path, local_track_id, position),
                        )
            playlist_count[0] += 1

        elif node.is_folder:
            # This is a folder, recurse into children
            new_path = f"{parent_path}/{node.name}" if parent_path else node.name
            for child in node.get_playlists():
                _process_node(child, new_path)

    # Process all children of root
    for child in tqdm(root.get_playlists(), desc="  Importing", unit="playlist"):
        _process_node(child)

    return playlist_count[0]
