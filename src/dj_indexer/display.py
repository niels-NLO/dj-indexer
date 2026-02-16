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
    pass


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
    pass
