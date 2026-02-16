"""Import rekordbox XML collection via pyrekordbox."""

import sqlite3
from pathlib import Path


def import_xml(conn: sqlite3.Connection, xml_path: Path):
    """
    Import rekordbox XML collection export.

    Uses pyrekordbox.rbxml.RekordboxXml to parse the XML.
    Matches tracks by filename_lower, imports cue points and playlists.

    Args:
        conn: SQLite database connection
        xml_path: Path to rekordbox XML file
    """
    pass
