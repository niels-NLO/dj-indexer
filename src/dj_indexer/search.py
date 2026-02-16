"""Search queries, regex support, and special filter modes."""

import sqlite3
import argparse


def search_tracks(conn: sqlite3.Connection, args: argparse.Namespace):
    """
    Execute search with flexible filters.

    Supports:
    - Free-text search across multiple fields
    - Regex search (both broad and field-scoped)
    - Multiple filter flags (artist, title, genre, key, BPM range, source, format)
    - Special queries (no-cues, duplicates, playlists)
    - Playlist filtering

    Args:
        conn: SQLite database connection
        args: Parsed command-line arguments with search parameters
    """
    pass


def show_cues(conn: sqlite3.Connection, query: str):
    """
    Show detailed cue point information for tracks matching the query.

    Args:
        conn: SQLite database connection
        query: Search query to find matching tracks
    """
    pass
