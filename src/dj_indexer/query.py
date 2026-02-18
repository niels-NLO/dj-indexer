"""Run raw SQL SELECT queries against the database."""

import sqlite3
import re
from pathlib import Path


def run_query(conn: sqlite3.Connection, sql: str):
    """
    Execute a raw SQL SELECT query and print results in tabular format.

    Registers REGEXP and DIRNAME helper functions for use in queries.

    Args:
        conn: SQLite database connection
        sql: SQL SELECT statement to execute

    Raises:
        ValueError: If SQL is not a SELECT statement
    """
    # Validate that this is a SELECT query
    sql_stripped = sql.strip()
    if not sql_stripped.upper().startswith("SELECT"):
        raise ValueError("Only SELECT statements are supported")

    # Register helper functions
    _register_helpers(conn)

    cursor = conn.cursor()
    try:
        cursor.execute(sql_stripped)
        rows = cursor.fetchall()
    except sqlite3.Error as e:
        print(f"\nSQL Error: {e}\n")
        return

    # Get column names from cursor description
    if not cursor.description:
        print("\nNo results returned.\n")
        return

    column_names = [desc[0] for desc in cursor.description]

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


def _register_helpers(conn: sqlite3.Connection):
    """Register REGEXP and DIRNAME functions on the connection."""
    # REGEXP function for regex matching
    conn.create_function("REGEXP", 2,
        lambda pat, val: bool(re.search(pat, val, re.IGNORECASE)) if val else False)

    # DIRNAME function to extract directory path
    conn.create_function("DIRNAME", 1,
        lambda p: str(Path(p).parent) if p else None)
