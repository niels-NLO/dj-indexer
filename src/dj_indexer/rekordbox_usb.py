"""ANLZ binary file parsing from rekordbox USB exports via pyrekordbox."""

import sqlite3
from pathlib import Path


def import_usb(conn: sqlite3.Connection, usb_path: Path):
    """
    Scan rekordbox USB export's PIONEER/USBANLZ folder for ANLZ binary files.

    Matches to existing tracks by filename, extracts cue points and analysis data.

    Args:
        conn: SQLite database connection
        usb_path: Path to rekordbox USB drive root
    """
    pass
