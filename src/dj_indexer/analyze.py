"""Analytics and breakdowns by folder, format, etc."""

import sqlite3
import argparse
from pathlib import Path


def analyze(conn: sqlite3.Connection, args: argparse.Namespace):
    """
    Run analytics queries with optional filters.

    Supports:
    - --folders: breakdown by folder path
    - Filter flags: --in-rekordbox, --not-in-rekordbox, --source, --format, --genre, --bpm-min, --bpm-max

    Args:
        conn: SQLite database connection
        args: Parsed command-line arguments
    """
    # Register DIRNAME function
    conn.create_function("DIRNAME", 1,
        lambda p: str(Path(p).parent) if p else None)

    if args.folders:
        _analyze_folders(conn, args)
    else:
        print("\nNo analysis type specified. Use --folders.\n")


def _analyze_folders(conn: sqlite3.Connection, args: argparse.Namespace):
    """Analyze track counts by folder path."""
    conditions = []
    params = []

    # Build WHERE clause from filters
    if args.in_rekordbox:
        conditions.append("in_rekordbox = 1")

    if args.not_in_rekordbox:
        conditions.append("in_rekordbox = 0")

    if args.source:
        conditions.append("source_label LIKE ?")
        params.append(f"%{args.source}%")

    if args.format:
        conditions.append("file_format = ?")
        params.append(args.format)

    if args.genre:
        conditions.append("genre LIKE ?")
        params.append(f"%{args.genre}%")

    if args.bpm_min is not None:
        conditions.append("bpm >= ?")
        params.append(args.bpm_min)

    if args.bpm_max is not None:
        conditions.append("bpm <= ?")
        params.append(args.bpm_max)

    where_clause = " AND ".join(conditions) if conditions else "1=1"

    # Query folder breakdown
    sql = f"""
        SELECT
            DIRNAME(filepath) as folder_path,
            COUNT(*) as track_count
        FROM tracks
        WHERE {where_clause}
        GROUP BY DIRNAME(filepath)
        ORDER BY track_count DESC
        LIMIT ?
    """
    params.append(args.limit)

    cursor = conn.cursor()
    cursor.execute(sql, params)
    rows = cursor.fetchall()

    if not rows:
        print("\nNo folders found matching criteria.\n")
        return

    # Find max width for alignment
    max_path_len = max((len(row[0] or "") for row in rows), default=0)
    max_path_len = max(max_path_len, len("Folder Path"))

    # Build filter description
    filter_parts = []
    if args.in_rekordbox:
        filter_parts.append("in rekordbox")
    if args.not_in_rekordbox:
        filter_parts.append("not in rekordbox")
    if args.source:
        filter_parts.append(f"source={args.source}")
    if args.format:
        filter_parts.append(f"format={args.format}")
    if args.genre:
        filter_parts.append(f"genre={args.genre}")
    if args.bpm_min is not None or args.bpm_max is not None:
        bpm_range = []
        if args.bpm_min is not None:
            bpm_range.append(f"{args.bpm_min}")
        if args.bpm_max is not None:
            bpm_range.append(f"{args.bpm_max}")
        filter_parts.append(f"bpm={'-'.join(bpm_range)}")

    filter_str = " | ".join(filter_parts) if filter_parts else ""
    title = f"Folder Analysis ({len(rows)} unique folders)"
    if filter_str:
        title += f" [{filter_str}]"

    print(f"\n{title}:\n")
    for path, count in rows:
        path_display = path or "(no path)"
        print(f"   {path_display.ljust(max_path_len)}  {count} track{'s' if count != 1 else ''}")

    print()
