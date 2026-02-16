"""CLI interface with argparse command routing."""

import argparse
from pathlib import Path

from dj_indexer import db, scanner, rekordbox_xml, rekordbox_usb, search, stats, export


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="dj-indexer",
        description="Index USB drives and rekordbox collections into a searchable SQLite database"
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=Path("dj_music_index.db"),
        help="Path to SQLite database (default: dj_music_index.db)"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # scan command
    scan_parser = subparsers.add_parser("scan", help="Scan directory for audio files")
    scan_parser.add_argument("directory", type=Path, help="Directory to scan")
    scan_parser.add_argument("--label", required=True, help="Source label for scanned files")

    # import-xml command
    import_xml_parser = subparsers.add_parser("import-xml", help="Import rekordbox XML collection")
    import_xml_parser.add_argument("xml_file", type=Path, help="Path to rekordbox XML file")

    # import-rb-usb command
    import_usb_parser = subparsers.add_parser("import-rb-usb", help="Import rekordbox USB ANLZ files")
    import_usb_parser.add_argument("usb_path", type=Path, help="Path to rekordbox USB drive")

    # search command
    search_parser = subparsers.add_parser("search", help="Search tracks")
    search_parser.add_argument("query", nargs="?", default=None, help="Free-text search query")
    search_parser.add_argument("--regex", "-r", action="store_true", help="Regex search on all fields")
    search_parser.add_argument("--artist", "-a", help="Filter by artist")
    search_parser.add_argument("--title", "-t", help="Filter by title")
    search_parser.add_argument("--filename", help="Filter by filename")
    search_parser.add_argument("--genre", "-g", help="Filter by genre")
    search_parser.add_argument("--key", "-k", help="Filter by musical key")
    search_parser.add_argument("--bpm-min", type=float, help="Minimum BPM")
    search_parser.add_argument("--bpm-max", type=float, help="Maximum BPM")
    search_parser.add_argument("--source", "-s", help="Filter by source label")
    search_parser.add_argument("--format", help="Filter by file format")
    search_parser.add_argument("--in-rekordbox", action="store_true", help="Only rekordbox tracks")
    search_parser.add_argument("--not-in-rekordbox", action="store_true", help="Only non-rekordbox tracks")
    search_parser.add_argument("--no-cues", action="store_true", help="RB tracks without cue points")
    search_parser.add_argument("--duplicates", action="store_true", help="Show duplicate filenames")
    search_parser.add_argument("--playlists", action="store_true", help="List all playlists")
    search_parser.add_argument("--playlist", help="Filter by playlist name")
    search_parser.add_argument("--re", action="store_true", help="Enable regex mode for field filters")
    search_parser.add_argument("--limit", type=int, default=100, help="Max results (default: 100)")

    # cues command
    cues_parser = subparsers.add_parser("cues", help="Show cue points for tracks")
    cues_parser.add_argument("query", help="Search query for tracks")

    # stats command
    subparsers.add_parser("stats", help="Show collection statistics")

    # export command
    export_parser = subparsers.add_parser("export", help="Export tracks to CSV")
    export_parser.add_argument("output", type=Path, help="Output CSV file")
    export_parser.add_argument("--playlists", action="store_true", help="Also export playlists")

    # export-playlists command
    export_pl_parser = subparsers.add_parser("export-playlists", help="Export playlists to CSV")
    export_pl_parser.add_argument("output", type=Path, help="Output CSV file")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Get database connection
    conn = db.get_db(args.db)

    # Route to appropriate command handler
    try:
        if args.command == "scan":
            scanner.scan_directory(conn, args.directory, args.label)
        elif args.command == "import-xml":
            rekordbox_xml.import_xml(conn, args.xml_file)
        elif args.command == "import-rb-usb":
            rekordbox_usb.import_usb(conn, args.usb_path)
        elif args.command == "search":
            search.search_tracks(conn, args)
        elif args.command == "cues":
            search.show_cues(conn, args.query)
        elif args.command == "stats":
            stats.show_stats(conn)
        elif args.command == "export":
            export.export_csv(conn, args.output, args.playlists)
        elif args.command == "export-playlists":
            export.export_playlists(conn, args.output)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
