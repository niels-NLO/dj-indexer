"""USB/directory scanning with mutagen audio metadata extraction."""

import sqlite3
from pathlib import Path


AUDIO_EXTENSIONS = {
    ".mp3", ".wav", ".flac", ".aiff", ".aif", ".aac", ".m4a",
    ".ogg", ".opus", ".wma", ".alac"
}


def scan_directory(conn: sqlite3.Connection, directory: Path, label: str):
    """
    Walk directory tree recursively, extract audio metadata with mutagen, insert into tracks table.

    Args:
        conn: SQLite database connection
        directory: Root directory to scan
        label: Source label for scanned files (e.g. "USB1", "USB2")
    """
    pass
