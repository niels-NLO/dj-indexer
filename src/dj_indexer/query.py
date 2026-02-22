"""Run raw SQL SELECT queries against the database."""

import sqlite3
import re
from pathlib import Path
from typing import Tuple, List, Optional


def run_query(conn: sqlite3.Connection, sql: str, export_args: Optional[object] = None):
    """
    Execute a raw SQL SELECT query and print results in tabular format.

    Registers REGEXP and DIRNAME helper functions for use in queries.

    Args:
        conn: SQLite database connection
        sql: SQL SELECT statement to execute
        export_args: Optional args object for CSV export (with export_csv, columns, path_conversion, volume_map attributes)

    Raises:
        ValueError: If SQL is not a SELECT statement
    """
    # Validate that this is a SELECT query
    sql_stripped = sql.strip()
    if not sql_stripped.upper().startswith("SELECT"):
        raise ValueError("Only SELECT statements are supported")

    # Execute and get results
    rows, column_names = _execute_query(conn, sql_stripped)

    if rows is None:
        return

    # Print results
    _print_tabular_results(rows, column_names)

    # Handle CSV export if requested
    if export_args and hasattr(export_args, 'export_csv') and export_args.export_csv:
        _export_query_results(rows, column_names, export_args)


def _execute_query(conn: sqlite3.Connection, sql: str) -> Tuple[Optional[List], Optional[List[str]]]:
    """
    Execute a SQL SELECT query and return rows and column names.

    Args:
        conn: SQLite database connection
        sql: SQL SELECT statement (must be stripped and validated)

    Returns:
        Tuple of (rows, column_names) or (None, None) on error
    """
    # Register helper functions
    _register_helpers(conn)

    cursor = conn.cursor()
    try:
        cursor.execute(sql)
        rows = cursor.fetchall()
    except sqlite3.Error as e:
        print(f"\nSQL Error: {e}\n")
        return None, None

    # Get column names from cursor description
    if not cursor.description:
        print("\nNo results returned.\n")
        return None, None

    column_names = [desc[0] for desc in cursor.description]
    return rows, column_names


def _print_tabular_results(rows: List, column_names: List[str]):
    """Print query results in tabular format."""
    # Calculate column widths
    col_widths = [len(name) for name in column_names]
    for row in rows:
        for i, cell in enumerate(row):
            cell_str = _format_cell(cell)
            col_widths[i] = max(col_widths[i], len(cell_str))

    # Print header
    print()
    header_parts = []
    for name, width in zip(column_names, col_widths):
        header_parts.append(name.ljust(width))
    print("   " + " | ".join(header_parts))

    # Print separator
    sep_parts = []
    for width in col_widths:
        sep_parts.append("-" * width)
    print("   " + "-+-".join(sep_parts))

    # Print rows
    for row in rows:
        row_parts = []
        for cell, width in zip(row, col_widths):
            cell_str = _format_cell(cell)
            row_parts.append(cell_str.ljust(width))
        print("   " + " | ".join(row_parts))

    # Print summary
    print(f"\n({len(rows)} row{'s' if len(rows) != 1 else ''})\n")


def _format_cell(value):
    """Format a cell value for display."""
    if value is None:
        return "NULL"
    if isinstance(value, float):
        # Format floats reasonably
        if value == int(value):
            return str(int(value))
        return f"{value:.2f}"
    return str(value)


def _export_query_results(rows: List, column_names: List[str], export_args: object):
    """Export query results to CSV with optional path conversion."""
    from . import export_results

    # Parse volume mappings from format: ["USB1=E", "USB2=F"]
    volume_mappings = None
    if hasattr(export_args, 'volume_map') and export_args.volume_map:
        volume_mappings = {}
        for mapping in export_args.volume_map:
            if '=' in mapping:
                volume_name, drive = mapping.split('=', 1)
                volume_mappings[volume_name.strip()] = drive.strip()

    # Parse path conversion direction
    path_conversion = None
    if hasattr(export_args, 'path_conversion') and export_args.path_conversion:
        if export_args.path_conversion == 'mac-to-windows':
            path_conversion = {'from_platform': 'mac', 'to_platform': 'windows'}
        elif export_args.path_conversion == 'windows-to-mac':
            path_conversion = {'from_platform': 'windows', 'to_platform': 'mac'}

    # Export to CSV
    export_results.export_to_csv(
        rows=rows,
        column_names=column_names,
        output_path=Path(export_args.export_csv),
        selected_columns=export_args.columns if hasattr(export_args, 'columns') else None,
        path_conversion=path_conversion,
        volume_mappings=volume_mappings
    )


def _register_helpers(conn: sqlite3.Connection):
    """Register REGEXP and DIRNAME functions on the connection."""
    # REGEXP function for regex matching
    conn.create_function("REGEXP", 2,
        lambda pat, val: bool(re.search(pat, val, re.IGNORECASE)) if val else False)

    # DIRNAME function to extract directory path
    conn.create_function("DIRNAME", 1,
        lambda p: str(Path(p).parent) if p else None)
