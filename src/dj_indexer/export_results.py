"""Export search and query results to CSV with optional path conversion."""

import csv
from pathlib import Path
from typing import List, Dict, Any, Optional


def export_to_csv(
    rows: List[tuple],
    column_names: List[str],
    output_path: Path,
    selected_columns: Optional[List[str]] = None,
    path_conversion: Optional[Dict[str, str]] = None,
    volume_mappings: Optional[Dict[str, str]] = None,
):
    """
    Export query/search results to CSV.

    Args:
        rows: List of result tuples from database query
        column_names: List of column names matching the row structure
        output_path: Path to output CSV file
        selected_columns: Specific columns to export (None = all). Must match column_names.
        path_conversion: Dict with keys "from_platform" and "to_platform" ("mac" or "windows")
        volume_mappings: Dict mapping volume names to drive letters
                        e.g., {"USB1": "E", "USB2": "F"}
    """
    if not rows:
        print(f"\nNo results to export.\n")
        return

    # Determine which columns to export
    if selected_columns is None:
        export_cols = column_names
        col_indices = list(range(len(column_names)))
    else:
        col_indices = []
        export_cols = []
        for col in selected_columns:
            if col in column_names:
                col_indices.append(column_names.index(col))
                export_cols.append(col)
            else:
                print(f"\nWarning: Column '{col}' not found. Skipping.\n")

        if not col_indices:
            print(f"\nError: No valid columns selected.\n")
            return

    # Write CSV
    try:
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(export_cols)

            for row in rows:
                export_row = []
                for idx in col_indices:
                    value = row[idx]

                    # Convert path if requested
                    if (path_conversion and
                        export_cols[col_indices.index(idx)] in
                        ('filepath', 'path', 'file_path')):
                        value = _convert_path(
                            value,
                            path_conversion.get('from_platform'),
                            path_conversion.get('to_platform'),
                            volume_mappings
                        )

                    export_row.append(value)

                writer.writerow(export_row)

        print(f"\n✓ Exported {len(rows)} rows to {output_path}")
        print(f"  Columns: {', '.join(export_cols)}\n")

    except Exception as e:
        print(f"\nError writing CSV: {e}\n")


def _convert_path(
    filepath: Optional[str],
    from_platform: Optional[str],
    to_platform: Optional[str],
    volume_mappings: Optional[Dict[str, str]],
) -> Optional[str]:
    """
    Convert file path between Mac and Windows formats.

    Args:
        filepath: Original file path
        from_platform: Source platform ("mac" or "windows")
        to_platform: Target platform ("mac" or "windows")
        volume_mappings: Dict mapping volume names to drive letters

    Returns:
        Converted filepath or original if no conversion needed
    """
    if not filepath or not from_platform or not to_platform:
        return filepath

    if from_platform == to_platform:
        return filepath

    from_platform = from_platform.lower()
    to_platform = to_platform.lower()

    try:
        p = Path(filepath)

        if from_platform == "mac" and to_platform == "windows":
            return _mac_to_windows(filepath, volume_mappings)
        elif from_platform == "windows" and to_platform == "mac":
            return _windows_to_mac(filepath, volume_mappings)

    except Exception:
        pass

    return filepath


def _mac_to_windows(
    mac_path: str,
    volume_mappings: Optional[Dict[str, str]],
) -> str:
    """
    Convert Mac path to Windows path.

    Examples:
        /Volumes/USB1/Music/song.mp3 → E:\Music\song.mp3
        /Volumes/ExternalDrive/backup/file.mp3 → F:\backup\file.mp3
    """
    if not mac_path.startswith("/Volumes/"):
        return mac_path

    parts = mac_path.split("/")
    if len(parts) < 3:
        return mac_path

    volume_name = parts[2]

    # Get drive letter from mapping
    if volume_mappings and volume_name in volume_mappings:
        drive = volume_mappings[volume_name]
    else:
        # Try to auto-detect if mapping not provided
        # Default: use first letter of volume name
        drive = volume_name[0].upper() if volume_name else "X"

    # Build Windows path
    remaining_path = "\\".join(parts[3:]) if len(parts) > 3 else ""
    if remaining_path:
        return f"{drive}:\\{remaining_path}"
    else:
        return f"{drive}:\\"


def _windows_to_mac(
    windows_path: str,
    volume_mappings: Optional[Dict[str, str]],
) -> str:
    """
    Convert Windows path to Mac path.

    Examples:
        E:\Music\song.mp3 → /Volumes/USB1/Music/song.mp3
        F:\backup\file.mp3 → /Volumes/ExternalDrive/backup/file.mp3
    """
    # Parse Windows path
    if ":\\" not in windows_path:
        return windows_path

    drive_letter = windows_path[0].upper()

    # Get volume name from mapping (reverse lookup)
    volume_name = None
    if volume_mappings:
        for vol, drv in volume_mappings.items():
            if drv.upper() == drive_letter:
                volume_name = vol
                break

    if not volume_name:
        # Default: use generic volume name
        volume_name = f"Volume{drive_letter}"

    # Build Mac path
    remaining_path = windows_path[3:].replace("\\", "/") if len(windows_path) > 3 else ""
    if remaining_path:
        return f"/Volumes/{volume_name}/{remaining_path}"
    else:
        return f"/Volumes/{volume_name}"


def get_column_options(
    column_names: List[str],
    default_columns: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Get available columns and defaults for export.

    Args:
        column_names: All available column names from query
        default_columns: Default columns to export

    Returns:
        Dict with 'available' and 'default' keys
    """
    return {
        "available": column_names,
        "default": default_columns or column_names,
    }
