"""Database connection, schema, and utilities."""

import sqlite3
from pathlib import Path


def safe_int(value):
    """Safely convert value to int, returning None if not possible."""
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def safe_float(value):
    """Safely convert value to float, returning None if not possible."""
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def get_db(db_path: Path) -> sqlite3.Connection:
    """
    Open or create SQLite database with schema.

    Enables WAL mode and foreign keys.
    Creates schema if database is new.
    """
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    # Enable WAL and foreign keys
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA foreign_keys = ON")

    # Create tables if not exist
    _create_schema(conn)

    conn.commit()
    return conn


def _create_schema(conn: sqlite3.Connection):
    """Create all tables if they don't exist."""

    # tracks table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tracks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filepath TEXT UNIQUE,
            filename TEXT,
            filename_lower TEXT,
            source_label TEXT,
            title TEXT,
            artist TEXT,
            album TEXT,
            genre TEXT,
            bpm REAL,
            musical_key TEXT,
            duration_sec REAL,
            bitrate INTEGER,
            sample_rate INTEGER,
            file_format TEXT,
            file_size INTEGER,
            in_rekordbox INTEGER DEFAULT 0,
            rb_track_id TEXT,
            rb_location TEXT,
            comments TEXT,
            rating INTEGER,
            label TEXT,
            remixer TEXT,
            color TEXT,
            date_indexed TEXT DEFAULT (datetime('now'))
        )
    """)

    # cue_points table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cue_points (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            track_id INTEGER NOT NULL,
            cue_type TEXT,
            cue_name TEXT,
            cue_num INTEGER,
            position_sec REAL,
            is_loop INTEGER DEFAULT 0,
            loop_end_sec REAL,
            color_red INTEGER,
            color_green INTEGER,
            color_blue INTEGER,
            FOREIGN KEY (track_id) REFERENCES tracks(id) ON DELETE CASCADE
        )
    """)

    # playlists table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS playlists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            playlist_name TEXT,
            playlist_path TEXT,
            track_id INTEGER,
            position INTEGER,
            FOREIGN KEY (track_id) REFERENCES tracks(id) ON DELETE CASCADE
        )
    """)

    # anlz_data table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS anlz_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            track_id INTEGER NOT NULL,
            has_beat_grid INTEGER DEFAULT 0,
            has_waveform INTEGER DEFAULT 0,
            has_waveform_color INTEGER DEFAULT 0,
            anlz_path TEXT,
            FOREIGN KEY (track_id) REFERENCES tracks(id) ON DELETE CASCADE
        )
    """)

    # Create indexes
    _create_indexes(conn)


def _create_indexes(conn: sqlite3.Connection):
    """Create indexes for common search queries."""
    indexes = [
        ("idx_tracks_filename", "tracks", "filename"),
        ("idx_tracks_filename_lower", "tracks", "filename_lower"),
        ("idx_tracks_artist", "tracks", "artist"),
        ("idx_tracks_title", "tracks", "title"),
        ("idx_tracks_genre", "tracks", "genre"),
        ("idx_tracks_bpm", "tracks", "bpm"),
        ("idx_tracks_source_label", "tracks", "source_label"),
        ("idx_tracks_musical_key", "tracks", "musical_key"),
        ("idx_cue_points_track_id", "cue_points", "track_id"),
        ("idx_playlists_track_id", "playlists", "track_id"),
    ]

    for idx_name, table, column in indexes:
        conn.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table}({column})")
