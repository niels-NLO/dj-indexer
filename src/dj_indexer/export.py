"""CSV export of tracks and playlists."""

import sqlite3
from pathlib import Path


def export_csv(conn: sqlite3.Connection, output_path: Path, include_playlists: bool = False):
    """
    Export full track index to CSV.

    Columns: filename, title, artist, album, genre, bpm, musical_key, duration_sec,
    bitrate, file_format, source_label, in_rekordbox, filepath, comments, label,
    remixer, num_cues, num_hot_cues, cue_summary

    If include_playlists is True, also exports playlists to a separate CSV.

    Args:
        conn: SQLite database connection
        output_path: Output CSV file path
        include_playlists: Also export playlists to a separate file
    """
    pass


def export_playlists(conn: sqlite3.Connection, output_path: Path):
    """
    Export all playlists to CSV.

    Each row is one track-in-playlist entry.
    Columns: playlist_name, playlist_path, position, track_id, filename, title,
    artist, album, genre, bpm, musical_key

    Args:
        conn: SQLite database connection
        output_path: Output CSV file path
    """
    pass
