"""Output formatting for search results and cue details."""

from typing import List, Tuple, Any


def print_results(rows: List[Tuple[Any, ...]], header: str = "Search results"):
    """
    Print formatted search results.

    Shows artist, title (or filename if no title), BPM, key, source label.
    Displays [RB] badge if in rekordbox, [XH/YC] for cues (X hot, Y total).

    Args:
        rows: List of result rows from database query
        header: Header text to display
    """
    if not rows:
        print(f"\n{header}: 0 tracks\n")
        return

    count = len(rows)
    print(f"\n{header} ({count} tracks):\n")

    for row in rows:
        # Row format: (id, artist, title, filename, bpm, musical_key, source_label, in_rekordbox, num_hot_cues, num_cues)
        artist, title, filename, bpm, musical_key, source_label, in_rekordbox, num_hot_cues, num_cues = row[1:10]

        # Build display title
        display_title = title if title else filename
        if artist:
            display_line = f"   {artist} -- {display_title}"
        else:
            display_line = f"   {display_title}"

        print(display_line)

        # Build metadata line
        bpm_str = f"{bpm:.0f}" if bpm else "?"
        key_str = musical_key if musical_key else "?"
        badges = ""

        # Add rekordbox badge
        if in_rekordbox:
            badges += " [RB]"

        # Add cue badges
        if in_rekordbox:
            if num_cues == 0:
                badges += "  [NO CUES]"
            elif num_hot_cues is not None:
                badges += f"  [{num_hot_cues}H/{num_cues}C]"

        print(f"     {bpm_str} BPM | {key_str} | {source_label}{badges}\n")


def print_cue_details(track: Tuple[Any, ...], cues: List[Tuple[Any, ...]]):
    """
    Print detailed cue point information for a track.

    Format:
    Artist — Title (duration)
       BPM | Key | Source
       Cue points (N):
         [H:MM:SS] Cue Type: Name
         ...

    Args:
        track: Track row from database
        cues: List of cue point rows
    """
    # Track format: (id, artist, title, filename, bpm, musical_key, source_label, duration_sec, ...)
    artist, title, filename, bpm, musical_key, source_label, duration_sec = track[1:8]

    # Build title line
    display_title = title if title else filename
    duration_str = _format_duration(duration_sec) if duration_sec else "?"

    if artist:
        print(f"\n{artist} — {display_title} ({duration_str})")
    else:
        print(f"\n{display_title} ({duration_str})")

    # Build metadata line
    bpm_str = f"{bpm:.0f}" if bpm else "?"
    key_str = musical_key if musical_key else "?"
    print(f"   {bpm_str} BPM | {key_str} | {source_label}")

    # Print cue points
    if not cues:
        print("   Cue points: None")
    else:
        print(f"   Cue points ({len(cues)}):")
        for cue in cues:
            # Cue format: (id, track_id, cue_type, cue_name, cue_num, position_sec, is_loop, loop_end_sec, ...)
            cue_type, cue_name, position_sec = cue[2], cue[3], cue[5]

            # Format cue type
            if cue_type == "memory_cue":
                cue_label = "Memory Cue"
            elif cue_type.startswith("hot_cue_"):
                letter = cue_type[-1].upper()
                cue_label = f"Hot Cue {letter}"
            else:
                cue_label = cue_type

            # Add cue name if present
            if cue_name:
                cue_label += f": {cue_name}"

            # Format position
            time_str = _format_duration(position_sec)
            print(f"     [{time_str}] {cue_label}")

    print()


def _format_duration(seconds: float) -> str:
    """Format duration in seconds to H:MM:SS or MM:SS format."""
    if seconds is None:
        return "?"

    total_seconds = int(seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60

    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes}:{secs:02d}"
