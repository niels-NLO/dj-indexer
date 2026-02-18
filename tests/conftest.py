"""Shared test fixtures and configuration."""

import shutil
import sqlite3
import tempfile
from pathlib import Path

import pytest
from mutagen.flac import FLAC
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TCON, TBPM, TKEY
from mutagen.wave import WAVE
from mutagen.oggvorbis import OggVorbis
from mutagen.oggflac import OggFLAC
from mutagen.oggopus import OggOpus
from mutagen.asf import ASF

from dj_indexer import db


@pytest.fixture
def test_db():
    """Create a temporary test database."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)

    conn = db.get_db(db_path)
    yield conn
    conn.close()

    # Cleanup
    db_path.unlink(missing_ok=True)
    (db_path.parent / f"{db_path.name}-wal").unlink(missing_ok=True)
    (db_path.parent / f"{db_path.name}-shm").unlink(missing_ok=True)


@pytest.fixture
def rb5_xml_path():
    """Path to Rekordbox 5 test XML file."""
    return Path(__file__).parent.parent / "testfiles" / "rb5_database.xml"


@pytest.fixture
def rb6_xml_path():
    """Path to Rekordbox 6 test XML file."""
    return Path(__file__).parent.parent / "testfiles" / "rb6_database.xml"


@pytest.fixture
def test_audio_dir():
    """Create temporary directory with test FLAC files (simplest to create validly).

    FLAC is the simplest format to create with valid metadata for testing.
    Real audio files are complex to create with minimal code, so we focus on FLAC.

    TODO: Add coverage for remaining formats by downloading real test files:
    - ALAC (.alac) - Apple Lossless Audio Codec
    - AIFF (.aiff, .aif) - Audio Interchange File Format
    - MP3 (.mp3) - currently created but validation is unreliable
    - WAV (.wav) - currently created but validation is unreliable
    - AAC (.aac) - Advanced Audio Coding
    - M4A (.m4a) - MPEG-4 Audio
    - OGG (.ogg) - Ogg Vorbis
    - OPUS (.opus) - Opus Audio
    - WMA (.wma) - Windows Media Audio

    Steps to implement:
    1. Download or create minimal valid audio files for each format
    2. Store them in testfiles/audio_samples/ directory
    3. Create a fixture that copies these files to a temp directory
    4. Add format-specific tests to test_scanner.py
    """
    temp_dir = Path(tempfile.mkdtemp(prefix="dj_indexer_test_audio_"))

    # Test metadata to apply to all files
    metadata = {
        "title": "Test Track",
        "artist": "Test Artist",
        "album": "Test Album",
        "genre": "Test Genre",
        "bpm": "128",
        "key": "2A",
    }

    # Create multiple test files - we'll use FLAC as it's most reliable
    # In a real scenario, you'd use actual audio files or a test audio library
    _create_test_flac(temp_dir / "test_track_01.flac", metadata)
    _create_test_flac(temp_dir / "test_track_02.flac", metadata)
    _create_test_flac(temp_dir / "test_track_03.flac", metadata)

    yield temp_dir

    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


def _create_test_mp3(path: Path, metadata: dict):
    """Create a minimal valid MP3 file with ID3 tags."""
    # MP3 header for silent frame (approximately 26 bytes)
    mp3_frame = b"\xFF\xFB\x90\x00" + b"\x00" * 22  # Minimal valid MPEG frame
    path.write_bytes(mp3_frame * 100)  # Repeat to make it longer

    # Add ID3 tags
    audio = ID3()
    audio["TIT2"] = TIT2(text=[metadata["title"]])
    audio["TPE1"] = TPE1(text=[metadata["artist"]])
    audio["TALB"] = TALB(text=[metadata["album"]])
    audio["TCON"] = TCON(text=[metadata["genre"]])
    audio["TBPM"] = TBPM(text=[metadata["bpm"]])
    audio["TKEY"] = TKEY(text=[metadata["key"]])
    audio.save(str(path), v2_version=3)


def _create_test_wav(path: Path, metadata: dict):
    """Create a minimal valid WAV file with ID3 tags."""
    # Minimal WAV header + RIFF structure
    wav_header = (
        b"RIFF"  # ChunkID
        + b"\x24\x00\x00\x00"  # ChunkSize (36 bytes)
        + b"WAVE"  # Format
        + b"fmt "  # Subchunk1ID
        + b"\x10\x00\x00\x00"  # Subchunk1Size (16 bytes)
        + b"\x01\x00"  # AudioFormat (1 = PCM)
        + b"\x01\x00"  # NumChannels (1)
        + b"\x44\xAC\x00\x00"  # SampleRate (44100 Hz)
        + b"\x88\x58\x01\x00"  # ByteRate
        + b"\x02\x00"  # BlockAlign
        + b"\x10\x00"  # BitsPerSample
        + b"data"  # Subchunk2ID
        + b"\x00\x00\x00\x00"  # Subchunk2Size
    )
    path.write_bytes(wav_header)

    # Add ID3 tags
    audio = ID3()
    audio["TIT2"] = TIT2(text=[metadata["title"]])
    audio["TPE1"] = TPE1(text=[metadata["artist"]])
    audio["TALB"] = TALB(text=[metadata["album"]])
    audio["TCON"] = TCON(text=[metadata["genre"]])
    audio["TBPM"] = TBPM(text=[metadata["bpm"]])
    audio["TKEY"] = TKEY(text=[metadata["key"]])
    audio.save(str(path), v2_version=3)


def _create_test_flac(path: Path, metadata: dict):
    """Create a minimal valid FLAC file with Vorbis comments."""
    # Minimal FLAC structure (simplified for testing)
    flac_header = (
        b"fLaC"  # FLAC signature
        + b"\x80"  # Metadata block type 0 (STREAMINFO), last block
        + b"\x00\x00\x22"  # Metadata block length (34 bytes)
        + b"\x00\x10"  # Min block size
        + b"\x00\x10"  # Max block size
        + b"\x00\x00\x00"  # Min frame size
        + b"\x00\x00\x00"  # Max frame size
        + b"\xAC\x40"  # Sample rate (44100 Hz)
        + b"\x01"  # Channels (1)
        + b"\x08"  # Bits per sample (16)
        + b"\x00\x00\x00\x00\x00"  # Total samples
        + b"\x00" * 16  # MD5 signature
    )
    path.write_bytes(flac_header)

    # Add Vorbis comments
    audio = FLAC(str(path))
    audio["TITLE"] = metadata["title"]
    audio["ARTIST"] = metadata["artist"]
    audio["ALBUM"] = metadata["album"]
    audio["GENRE"] = metadata["genre"]
    audio["BPM"] = metadata["bpm"]
    audio["INITIALKEY"] = metadata["key"]
    audio.save()


def _create_test_ogg(path: Path, metadata: dict):
    """Create a minimal valid OGG Vorbis file."""
    # Create empty OGG file and add tags
    path.touch()
    audio = OggVorbis(str(path))
    audio["TITLE"] = metadata["title"]
    audio["ARTIST"] = metadata["artist"]
    audio["ALBUM"] = metadata["album"]
    audio["GENRE"] = metadata["genre"]
    audio["BPM"] = metadata["bpm"]
    audio["INITIALKEY"] = metadata["key"]
    audio.save()


def _create_test_opus(path: Path, metadata: dict):
    """Create a minimal valid OGG Opus file."""
    # Create empty OPUS file and add tags
    path.touch()
    audio = OggOpus(str(path))
    audio["TITLE"] = metadata["title"]
    audio["ARTIST"] = metadata["artist"]
    audio["ALBUM"] = metadata["album"]
    audio["GENRE"] = metadata["genre"]
    audio["BPM"] = metadata["bpm"]
    audio["INITIALKEY"] = metadata["key"]
    audio.save()


@pytest.fixture
def populated_db(test_db):
    """Create a test database with various tracks, cues, and playlists for search testing."""
    cursor = test_db.cursor()

    # Insert test tracks with varied metadata
    test_tracks = [
        # (filepath, filename, filename_lower, source_label, title, artist, album, genre, bpm, musical_key)
        ("/usb1/music/track1.mp3", "track1.mp3", "track1.mp3", "USB1", "Electric Dreams", "Bicep", "Isles", "Techno", 128.0, "2A"),
        ("/usb1/music/track2.mp3", "track2.mp3", "track2.mp3", "USB1", "Glue", "Bicep", "Isles", "Techno", 129.0, "11B"),
        ("/usb2/dj/ambient.flac", "ambient.flac", "ambient.flac", "USB2", "Ambient Waves", "Jon Hopkins", "Emerald Rush", "Ambient", 110.0, "6D"),
        ("/usb2/dj/house_track.flac", "house_track.flac", "house_track.flac", "USB2", "House Drop", "Fisher", "Losing It", "House", 124.0, "1D"),
        ("/external/backup/duplicate.mp3", "duplicate.mp3", "duplicate.mp3", "External", "Duplicate Track", "Unknown Artist", None, "Techno", 130.0, None),
        ("/external/backup/chill.mp3", "chill.mp3", "chill.mp3", "External", "Chill Vibes", "Jon Hopkins", "Night Vision", "Ambient", 95.0, "8B"),
    ]

    track_ids = {}
    for filepath, filename, filename_lower, source_label, title, artist, album, genre, bpm, musical_key in test_tracks:
        cursor.execute("""
            INSERT INTO tracks (filepath, filename, filename_lower, source_label, title, artist, album, genre, bpm, musical_key, in_rekordbox)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        """, (filepath, filename, filename_lower, source_label, title, artist, album, genre, bpm, musical_key))
        track_ids[filename] = cursor.lastrowid

    # Insert cue points for some tracks
    cues_data = [
        # (track_id_key, cue_type, cue_name, cue_num, position_sec)
        ("track1.mp3", "memory_cue", "Intro", -1, 0.0),
        ("track1.mp3", "hot_cue_A", "Drop", 0, 32.5),
        ("track1.mp3", "hot_cue_B", "Break", 1, 64.0),
        ("track2.mp3", "memory_cue", "Start", -1, 0.0),
        ("track2.mp3", "hot_cue_A", "Breakdown", 0, 45.0),
        ("ambient.flac", "memory_cue", "Peak", -1, 120.0),
        ("house_track.flac", "hot_cue_A", "Drop", 0, 30.0),
        ("house_track.flac", "hot_cue_B", "Outro", 1, 240.0),
        ("chill.mp3", "hot_cue_A", "Verse", 0, 15.0),
    ]

    for track_id_key, cue_type, cue_name, cue_num, position_sec in cues_data:
        track_id = track_ids[track_id_key]
        cursor.execute("""
            INSERT INTO cue_points (track_id, cue_type, cue_name, cue_num, position_sec)
            VALUES (?, ?, ?, ?, ?)
        """, (track_id, cue_type, cue_name, cue_num, position_sec))

    # Insert playlists
    playlists_data = [
        # (playlist_name, playlist_path, track_id_key, position)
        ("Techno Bangers", "root/Techno Bangers", "track1.mp3", 1),
        ("Techno Bangers", "root/Techno Bangers", "track2.mp3", 2),
        ("Ambient Chill", "root/Ambient/Chill", "ambient.flac", 1),
        ("Ambient Chill", "root/Ambient/Chill", "chill.mp3", 2),
        ("House Vibes", "root/Genre/House", "house_track.flac", 1),
    ]

    for playlist_name, playlist_path, track_id_key, position in playlists_data:
        track_id = track_ids[track_id_key]
        cursor.execute("""
            INSERT INTO playlists (playlist_name, playlist_path, track_id, position)
            VALUES (?, ?, ?, ?)
        """, (playlist_name, playlist_path, track_id, position))

    test_db.commit()
    return test_db
