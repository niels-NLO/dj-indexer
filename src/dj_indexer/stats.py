"""Collection statistics and reporting."""

import sqlite3


def show_stats(conn: sqlite3.Connection):
    """
    Print collection statistics in a formatted box.

    Includes:
    - Total tracks, in rekordbox, with cue points, with hot cues
    - RB tracks without cues (need prep)
    - Total cue points, playlists, duplicate filenames
    - BPM range (min, max, avg)
    - Tracks by source, by format, top genres

    Args:
        conn: SQLite database connection
    """
    pass
