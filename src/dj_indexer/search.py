"""Search queries, regex support, and special filter modes."""

import sqlite3
import argparse
import re

from . import display


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
    # Register REGEXP function if needed
    if args.regex or args.re or args.no_cues or args.duplicates:
        conn.create_function("REGEXP", 2,
            lambda pat, val: bool(re.search(pat, val, re.IGNORECASE)) if val else False)

    cursor = conn.cursor()

    # Handle special queries first
    if args.playlists:
        _show_playlists(cursor)
        return

    if args.duplicates:
        _show_duplicates(cursor)
        return

    if args.no_cues:
        _show_no_cues(cursor, args.limit)
        return

    # Handle playlist filtering
    if args.playlist:
        _search_playlist(cursor, args, display)
        return

    # Build main search query
    sql, params = _build_search_query(args)
    cursor.execute(sql, params)
    rows = cursor.fetchall()

    # Format display title
    if args.query:
        header = f'Search results for "{args.query}"'
    elif args.artist:
        header = f'Tracks by "{args.artist}"'
    elif args.title:
        header = f'Tracks titled "{args.title}"'
    elif args.filename:
        header = f'Files matching "{args.filename}"'
    elif args.genre:
        header = f'Genre: {args.genre}'
    elif args.key:
        header = f'Key: {args.key}'
    elif args.source:
        header = f'Source: {args.source}'
    elif args.format:
        header = f'Format: {args.format}'
    elif args.in_rekordbox:
        header = "Rekordbox tracks"
    elif args.not_in_rekordbox:
        header = "Non-rekordbox tracks"
    else:
        header = "All tracks"

    # Convert to list of tuples for display function
    row_list = [tuple(row) for row in rows]
    display.print_results(row_list, header)


def show_cues(conn: sqlite3.Connection, query: str):
    """
    Show detailed cue point information for tracks matching the query.

    Args:
        conn: SQLite database connection
        query: Search query to find matching tracks
    """
    # Register REGEXP function for regex support
    conn.create_function("REGEXP", 2,
        lambda pat, val: bool(re.search(pat, val, re.IGNORECASE)) if val else False)

    cursor = conn.cursor()

    # Find matching tracks with free-text search
    where_clause = """
        (title LIKE ? OR artist LIKE ? OR album LIKE ? OR
         filename LIKE ? OR genre LIKE ? OR remixer LIKE ? OR
         label LIKE ? OR comments LIKE ?)
    """
    search_param = f"%{query}%"
    params = [search_param] * 8

    sql = f"""
        SELECT
            id, artist, title, filename, bpm, musical_key,
            source_label, duration_sec
        FROM tracks
        WHERE {where_clause}
        ORDER BY artist, title
    """

    cursor.execute(sql, params)
    tracks = cursor.fetchall()

    if not tracks:
        print(f'\nNo tracks found matching "{query}"\n')
        return

    # Show detailed cue info for each track
    for track in tracks:
        # Get cue points for this track
        cursor.execute("""
            SELECT id, track_id, cue_type, cue_name, cue_num, position_sec, is_loop, loop_end_sec
            FROM cue_points
            WHERE track_id = ?
            ORDER BY position_sec
        """, (track[0],))
        cues = cursor.fetchall()

        cue_list = [tuple(cue) for cue in cues]
        display.print_cue_details(tuple(track), cue_list)


def _build_search_query(args: argparse.Namespace):
    """Build SQL query and parameters from search arguments."""
    conditions = []
    params = []

    # Determine if we're doing broad regex search
    # If --regex flag is set, use regex instead of LIKE
    if args.regex and args.query:
        # Broad regex search (replaces free-text LIKE search)
        conditions.append("""
            (REGEXP(?, title) OR REGEXP(?, artist) OR REGEXP(?, album) OR
             REGEXP(?, filename) OR REGEXP(?, genre) OR REGEXP(?, remixer) OR
             REGEXP(?, label) OR REGEXP(?, comments))
        """)
        params.extend([args.query] * 8)
    elif args.query:
        # Free-text search with LIKE (only if --regex not used)
        search_param = f"%{args.query}%"
        conditions.append("""
            (title LIKE ? OR artist LIKE ? OR album LIKE ? OR
             filename LIKE ? OR genre LIKE ? OR remixer LIKE ? OR
             label LIKE ? OR comments LIKE ?)
        """)
        params.extend([search_param] * 8)

    # Field-specific filters
    if args.artist:
        if args.re:
            conditions.append("REGEXP(?, artist)")
            params.append(args.artist)
        else:
            conditions.append("artist LIKE ?")
            params.append(f"%{args.artist}%")

    if args.title:
        if args.re:
            conditions.append("REGEXP(?, title)")
            params.append(args.title)
        else:
            conditions.append("title LIKE ?")
            params.append(f"%{args.title}%")

    if args.filename:
        if args.re:
            conditions.append("REGEXP(?, filename)")
            params.append(args.filename)
        else:
            conditions.append("filename LIKE ?")
            params.append(f"%{args.filename}%")

    if args.genre:
        if args.re:
            conditions.append("REGEXP(?, genre)")
            params.append(args.genre)
        else:
            conditions.append("genre LIKE ?")
            params.append(f"%{args.genre}%")

    if args.key:
        if args.re:
            conditions.append("REGEXP(?, musical_key)")
            params.append(args.key)
        else:
            conditions.append("musical_key LIKE ?")
            params.append(f"%{args.key}%")

    if args.source:
        conditions.append("source_label LIKE ?")
        params.append(f"%{args.source}%")

    if args.format:
        conditions.append("file_format = ?")
        params.append(args.format)

    # BPM range
    if args.bpm_min is not None:
        conditions.append("bpm >= ?")
        params.append(args.bpm_min)

    if args.bpm_max is not None:
        conditions.append("bpm <= ?")
        params.append(args.bpm_max)

    # Rekordbox status
    if args.in_rekordbox:
        conditions.append("in_rekordbox = 1")

    if args.not_in_rekordbox:
        conditions.append("in_rekordbox = 0")

    # Build WHERE clause
    where_clause = " AND ".join(conditions) if conditions else "1=1"

    # Build full query
    sql = f"""
        SELECT
            t.id, t.artist, t.title, t.filename, t.filepath, t.bpm, t.musical_key,
            t.source_label, t.in_rekordbox,
            COUNT(CASE WHEN cp.cue_type LIKE 'hot_cue_%' THEN 1 END) as num_hot_cues,
            COUNT(cp.id) as num_cues
        FROM tracks t
        LEFT JOIN cue_points cp ON t.id = cp.track_id
        WHERE {where_clause}
        GROUP BY t.id
        ORDER BY t.artist, t.title
        LIMIT ?
    """
    params.append(args.limit)

    return sql, params


def _show_playlists(cursor):
    """Show all playlists."""
    cursor.execute("""
        SELECT DISTINCT playlist_name, playlist_path, COUNT(*) as num_tracks
        FROM playlists
        GROUP BY playlist_name, playlist_path
        ORDER BY playlist_path
    """)
    playlists = cursor.fetchall()

    if not playlists:
        print("\nNo playlists found.\n")
        return

    print(f"\nPlaylists ({len(playlists)}):\n")
    for pl in playlists:
        name, path, count = pl[0], pl[1], pl[2]
        print(f"   {path}")
        print(f"      {count} tracks\n")


def _show_duplicates(cursor):
    """Show tracks with duplicate filenames across sources."""
    cursor.execute("""
        SELECT
            filename_lower, COUNT(*) as count, GROUP_CONCAT(source_label, ', ') as sources
        FROM tracks
        GROUP BY filename_lower
        HAVING COUNT(*) > 1
        ORDER BY filename_lower
    """)
    duplicates = cursor.fetchall()

    if not duplicates:
        print("\nNo duplicate filenames found.\n")
        return

    print(f"\nDuplicate filenames ({len(duplicates)}):\n")
    for dup in duplicates:
        filename, count, sources = dup[0], dup[1], dup[2]
        print(f"   {filename}")
        print(f"      {count} copies on: {sources}\n")


def _show_no_cues(cursor, limit):
    """Show rekordbox tracks without cue points."""
    cursor.execute(f"""
        SELECT
            t.id, t.artist, t.title, t.filename, t.filepath, t.bpm, t.musical_key,
            t.source_label, t.in_rekordbox,
            COUNT(CASE WHEN cp.cue_type LIKE 'hot_cue_%' THEN 1 END) as num_hot_cues,
            COUNT(cp.id) as num_cues
        FROM tracks t
        LEFT JOIN cue_points cp ON t.id = cp.track_id
        WHERE t.in_rekordbox = 1 AND t.id NOT IN (
            SELECT DISTINCT track_id FROM cue_points
        )
        GROUP BY t.id
        ORDER BY t.artist, t.title
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()

    row_list = [tuple(row) for row in rows]
    display.print_results(row_list, "Rekordbox tracks without cues (need prep)")


def _search_playlist(cursor, args, display_module):
    """Search for tracks in a specific playlist."""
    playlist_query = args.playlist

    # Find matching playlists
    if args.re:
        # Build SQL to search with REGEXP
        cursor.execute("""
            SELECT DISTINCT playlist_name, playlist_path
            FROM playlists
            ORDER BY playlist_path
        """)
        all_playlists = cursor.fetchall()

        # Filter using Python regex
        matching = []
        for pl in all_playlists:
            if re.search(playlist_query, pl[1], re.IGNORECASE) or re.search(playlist_query, pl[0], re.IGNORECASE):
                matching.append(pl)
    else:
        # Use LIKE search
        cursor.execute("""
            SELECT DISTINCT playlist_name, playlist_path
            FROM playlists
            WHERE playlist_name LIKE ? OR playlist_path LIKE ?
            ORDER BY playlist_path
        """, (f"%{playlist_query}%", f"%{playlist_query}%"))
        matching = cursor.fetchall()

    if not matching:
        print(f'\nNo playlists found matching "{playlist_query}"\n')
        return

    # Show tracks from all matching playlists
    for pl in matching:
        playlist_name, playlist_path = pl[0], pl[1]

        cursor.execute(f"""
            SELECT
                t.id, t.artist, t.title, t.filename, t.filepath, t.bpm, t.musical_key,
                t.source_label, t.in_rekordbox,
                COUNT(CASE WHEN cp.cue_type LIKE 'hot_cue_%' THEN 1 END) as num_hot_cues,
                COUNT(cp.id) as num_cues,
                pl.position
            FROM playlists pl
            JOIN tracks t ON pl.track_id = t.id
            LEFT JOIN cue_points cp ON t.id = cp.track_id
            WHERE pl.playlist_path = ?
            GROUP BY t.id
            ORDER BY pl.position
            LIMIT ?
        """, (playlist_path, args.limit))
        rows = cursor.fetchall()

        if rows:
            row_list = [tuple(row[:11]) for row in rows]  # Remove position from display
            display_module.print_results(row_list, f"Playlist: {playlist_path}")
