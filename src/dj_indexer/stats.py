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
    cursor = conn.cursor()

    # Check if database is empty
    cursor.execute("SELECT COUNT(*) FROM tracks")
    total_tracks = cursor.fetchone()[0]

    if total_tracks == 0:
        print("Database is empty. No tracks indexed yet.")
        print("\nStart by scanning a directory:")
        print("  uv run dj-indexer scan <directory> --label <name>")
        return

    # Query statistics
    cursor.execute("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN in_rekordbox = 1 THEN 1 ELSE 0 END) as in_rekordbox,
            COUNT(DISTINCT track_id) as tracks_with_cues,
            COUNT(DISTINCT CASE WHEN cue_type LIKE 'hot_cue_%' THEN track_id END) as tracks_with_hot_cues,
            COUNT(DISTINCT cue_points.track_id) as has_any_cues
        FROM tracks
        LEFT JOIN cue_points ON tracks.id = cue_points.track_id
    """)
    row = cursor.fetchone()
    total, in_rb, tracks_with_cues, tracks_with_hot, tracks_with_any_cues = row

    # RB tracks without cues
    cursor.execute("""
        SELECT COUNT(*)
        FROM tracks
        WHERE in_rekordbox = 1 AND id NOT IN (
            SELECT DISTINCT track_id FROM cue_points
        )
    """)
    rb_no_cues = cursor.fetchone()[0]

    # Total cue points
    cursor.execute("SELECT COUNT(*) FROM cue_points")
    total_cues = cursor.fetchone()[0]

    # Playlists
    cursor.execute("SELECT COUNT(DISTINCT playlist_name) FROM playlists")
    num_playlists = cursor.fetchone()[0]

    # Duplicate filenames
    cursor.execute("""
        SELECT COUNT(DISTINCT filename_lower)
        FROM tracks
        WHERE filename_lower IN (
            SELECT filename_lower FROM tracks GROUP BY filename_lower HAVING COUNT(*) > 1
        )
    """)
    duplicates = cursor.fetchone()[0]

    # BPM stats
    cursor.execute("""
        SELECT MIN(bpm), MAX(bpm), AVG(bpm)
        FROM tracks
        WHERE bpm IS NOT NULL
    """)
    bpm_row = cursor.fetchone()
    bpm_min, bpm_max, bpm_avg = bpm_row if bpm_row[0] else (None, None, None)

    # Tracks by source
    cursor.execute("""
        SELECT source_label, COUNT(*) FROM tracks GROUP BY source_label ORDER BY COUNT(*) DESC
    """)
    by_source = cursor.fetchall()

    # Tracks by format
    cursor.execute("""
        SELECT file_format, COUNT(*) FROM tracks WHERE file_format IS NOT NULL GROUP BY file_format ORDER BY COUNT(*) DESC
    """)
    by_format = cursor.fetchall()

    # Top genres
    cursor.execute("""
        SELECT genre, COUNT(*) FROM tracks WHERE genre IS NOT NULL GROUP BY genre ORDER BY COUNT(*) DESC LIMIT 5
    """)
    top_genres = cursor.fetchall()

    # Print formatted statistics box
    print("\n" + "=" * 60)
    print("DJ MUSIC INDEX STATISTICS".center(60))
    print("=" * 60)

    print(f"\nTracks:")
    print(f"  Total:                 {total:,}")
    print(f"  In Rekordbox:          {in_rb:,} ({in_rb/total*100:.1f}%)" if in_rb else f"  In Rekordbox:          0")
    print(f"  With any cue points:   {tracks_with_any_cues:,}" if tracks_with_any_cues else f"  With any cue points:   0")
    print(f"  With hot cues:         {tracks_with_hot:,}" if tracks_with_hot else f"  With hot cues:         0")
    if rb_no_cues:
        print(f"  [!] RB tracks no cues:  {rb_no_cues} (need prep)")

    print(f"\nCue Points:")
    print(f"  Total cue points:      {total_cues:,}")

    print(f"\nPlaylists & Duplicates:")
    print(f"  Playlists:             {num_playlists:,}")
    print(f"  Duplicate files:       {duplicates}")

    if bpm_min:
        print(f"\nBPM Range:")
        print(f"  Min:                   {bpm_min:.1f}")
        print(f"  Max:                   {bpm_max:.1f}")
        print(f"  Average:               {bpm_avg:.1f}")

    if by_source:
        print(f"\nTracks by Source:")
        for source, count in by_source:
            print(f"  {source:30s} {count:,}")

    if by_format:
        print(f"\nTracks by Format:")
        for fmt, count in by_format:
            fmt_display = fmt if fmt else "(unknown)"
            print(f"  {fmt_display:30s} {count:,}")

    if top_genres:
        print(f"\nTop Genres:")
        for genre, count in top_genres:
            print(f"  {genre:30s} {count:,}")

    print("\n" + "=" * 60)
