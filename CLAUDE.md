# DJ Music Indexer — Project Specification

## Overview

Build a Python CLI utility called `dj-indexer` that indexes music files across multiple USB drives and rekordbox collections into a single searchable SQLite database. The user is a DJ preparing sets who needs to know what music is on each drive, whether tracks are in rekordbox, and whether they have cue points set.

## Development workflow

Support a workflow where I develop the code on a windows machine using claude caude.
Once I have updated code, commit and push to remote. I will then pull from remote on my mac and run the code.
When something is not working on the mac after testing, I will create an issue on the repository. I will then ask to look at the open issues.
Try to resolve the issues and do a new commit and push. I will then test again on mac.
I will work on main only, mostly from my windows computer.

### Documentation Sync

When implementing new features or changing command behavior, update both:
1. **CLAUDE.md** — Update the CLI specification and command descriptions in this file
2. **docs/usage-examples.md** — Add practical examples and usage patterns for end users

This keeps the specification and examples in sync with actual implementation.

## Cross-Platform Workflow

The tool must support a **Mac → Windows workflow**:

1. **On Mac**: scan USB drives to index filenames and audio metadata
2. **Copy** the SQLite database file to Windows
3. **On Windows**: import the rekordbox XML collection, which enriches the existing entries with cue points, playlists, and rekordbox metadata

Because file paths differ between Mac (`/Volumes/USB1/...`) and Windows (`E:\Music\...`), **all cross-referencing between USB scans and rekordbox imports must match on lowercase filename only** (stored as `filename_lower`), never on full file path.

## Project Setup

Initialize the project with `uv init` and declare all dependencies in `pyproject.toml`:

```bash
uv init dj-indexer
cd dj-indexer
uv add mutagen pyrekordbox
```

### Dependencies (required)

- **mutagen** — reads audio file metadata (ID3 tags, Vorbis comments, etc.) for MP3, FLAC, WAV, AIFF, AAC, M4A, OGG, OPUS, WMA, ALAC
- **pyrekordbox** — reads rekordbox XML exports, ANLZ binary analysis files (beat grids, waveforms, cue points), and rekordbox 6/7 databases

Both are **required** dependencies — no graceful degradation. If a dependency is missing, the tool should fail with a clear import error.

### Running

```bash
uv run dj-indexer scan /Volumes/USB1 --label "USB1"
```

## Project Structure

```
dj-indexer/
├── pyproject.toml
├── CLAUDE.md
├── README.md
└── src/
    └── dj_indexer/
        ├── __init__.py
        ├── __main__.py          # entry point: `python -m dj_indexer`
        ├── cli.py               # argparse CLI definition, command routing
        ├── db.py                # database connection, schema, migrations
        ├── scanner.py           # USB/directory scanning with mutagen
        ├── rekordbox_xml.py     # rekordbox XML import via pyrekordbox
        ├── rekordbox_usb.py     # ANLZ binary file parsing via pyrekordbox
        ├── search.py            # search queries, regex, filters, special modes
        ├── stats.py             # collection statistics
        ├── export.py            # CSV export
        └── display.py           # output formatting (print results, cue details)
```

### Module responsibilities

- **`cli.py`** — defines all argparse subcommands and flags, parses args, calls into the appropriate module. This is the only module that touches `argparse`.
- **`db.py`** — `get_db(path)` function that opens/creates the SQLite database, runs schema creation, sets PRAGMAs (WAL, foreign keys). All SQL schema lives here. Provides helper functions `safe_float()`, `safe_int()`.
- **`scanner.py`** — `scan_directory(conn, directory, label)` function. Walks the filesystem, calls mutagen, inserts into tracks table.
- **`rekordbox_xml.py`** — `import_xml(conn, xml_path)` function. Uses `pyrekordbox.rbxml.RekordboxXml` to parse the XML, import tracks, cue points, and playlists. Handles filename-based matching.
- **`rekordbox_usb.py`** — `import_usb(conn, usb_path)` function. Scans PIONEER/USBANLZ folder, parses ANLZ files with `pyrekordbox.anlz.AnlzFile`, extracts cue points and analysis metadata.
- **`search.py`** — `search_tracks(conn, args)` and `show_cues(conn, query)` functions. Builds SQL queries from filter args, handles regex registration, special modes (no-cues, duplicates, playlists).
- **`stats.py`** — `show_stats(conn)` function. Runs aggregate queries and prints the stats box.
- **`export.py`** — `export_csv(conn, output_path, include_playlists)` and `export_playlists(conn, output_path)` functions. Writes full track index and/or playlist contents to CSV.
- **`display.py`** — `print_results(rows, header)` and `print_cue_details(track, cues)` functions. Shared output formatting used by search and cues commands.
- **`__main__.py`** — just calls `cli.main()` so the package can be run with `python -m dj_indexer`.

### pyproject.toml

```toml
[project]
name = "dj-indexer"
version = "0.1.0"
description = "Index USB drives and rekordbox collections into a searchable SQLite database"
requires-python = ">=3.11"
dependencies = [
    "mutagen",
    "pyrekordbox",
]

[project.scripts]
dj-indexer = "dj_indexer.cli:main"
```

## CLI Interface

```
dj-indexer [--db PATH] <command> [args]
```

### Commands

#### `scan <directory> --label <name>`
Walk a directory tree recursively, find all audio files, extract metadata with mutagen, and insert into the `tracks` table.

- Audio extensions to detect: `.mp3`, `.wav`, `.flac`, `.aiff`, `.aif`, `.aac`, `.m4a`, `.ogg`, `.opus`, `.wma`, `.alac`
- Store: filepath, filename, filename_lower (for cross-platform matching), source_label, title, artist, album, genre, bpm, musical_key, duration_sec, bitrate, sample_rate, file_format, file_size
- Use `ON CONFLICT(filepath) DO UPDATE` with `COALESCE` to preserve existing metadata when re-scanning
- Print progress every 100 tracks

#### `import-xml <xml_file>`
Import a rekordbox XML collection export (created via File → Export Collection in XML format in rekordbox).

**Uses pyrekordbox** (`from pyrekordbox.rbxml import RekordboxXml`).

##### pyrekordbox XML API (verified):
```python
from pyrekordbox.rbxml import RekordboxXml

xml = RekordboxXml("collection.xml")
xml.num_tracks          # int
xml.product_name        # str
xml.product_version     # str

track = xml.get_track(idx)  # 0-indexed, returns Track object
# Track attributes (access via track["Key"]):
#   TrackID, Name, Artist, Composer, Album, Grouping, Genre, Kind, Size,
#   TotalTime, DiscNumber, TrackNumber, Year, AverageBpm, DateModified,
#   DateAdded, BitRate, SampleRate, Comments, PlayCount, LastPlayed,
#   Rating, Location, Remixer, Tonality, Label, Mix, Colour
# NOTE: "BPM" is NOT a valid key — use "AverageBpm"
# NOTE: "Location" is auto-decoded from file:// URL by pyrekordbox

track.marks  # list of PositionMark objects (cue points)
# PositionMark attributes: Name, Type, Start, End, Num
# Type values: "cue" or "loop" (pyrekordbox converts from numeric)
# Num: -1 = memory cue, 0-7 = hot cues A-H
# NOTE: Red/Green/Blue are NOT in PositionMark valid attribs

# Playlists:
root = xml.get_playlist()   # returns root Node
root.name                   # "root"
root.is_folder              # True
root.is_playlist            # False
root.get_playlists()        # list of child Nodes (folders + playlists)
root.treestr()              # pretty print tree

node.is_playlist            # True if leaf playlist
node.get_tracks()           # list of TrackID keys (ints)
```

##### Matching logic:
- Match rekordbox tracks to existing scanned tracks by `filename_lower` (case-insensitive filename match)
- If matched: update the existing row with rekordbox metadata (using `COALESCE(NULLIF(new, ''), existing)` to not overwrite good data with empty strings), set `in_rekordbox = 1`
- If not matched: insert as new track with `source_label = 'rekordbox XML'`
- Import cue points into `cue_points` table
- Recursively import playlists into `playlists` table, mapping rekordbox TrackID to database row ID

#### `import-rb-usb <usb_path>`
Scan a rekordbox USB export's `PIONEER/USBANLZ/` folder for ANLZ binary files.

Structure of a rekordbox USB export:
```
USB_DRIVE/
├── Contents/           # actual audio files
│   └── Artist/Album/track.mp3
└── PIONEER/
    ├── rekordbox/
    │   └── export.pdb
    ├── USBANLZ/        # analysis files per track
    │   └── xxx/uuid/
    │       ├── ANLZ0000.DAT   # beat grid, waveform
    │       └── ANLZ0000.EXT   # extended data, cue points
    └── MYSETTING.DAT
```

##### pyrekordbox ANLZ API:
```python
from pyrekordbox.anlz import AnlzFile

anlz = AnlzFile.parse_file("ANLZ0000.DAT")

# Check for tag types:
if "beat_grid" in anlz: ...
if "waveform_preview" in anlz: ...

# Get cue points:
cue_tags = anlz.getall_tags("PCOB")  # or "PCO2" for extended cues
# Cue entries have: hot_cue (int), time (milliseconds), loop_time (ms)

# Get track path:
path_tags = anlz.getall_tags("path")
```

- Walk all `.DAT` and `.EXT` files in `USBANLZ/`
- Match to existing tracks by filename
- Store beat grid/waveform availability in `anlz_data` table
- Extract cue points (convert ms → seconds)
- Also scan `Contents/` folder for audio metadata

#### `search [query] [filters]`

Flexible search with multiple filter modes:

| Flag | Description | Match type |
|------|-------------|------------|
| `query` (positional) | Free-text search | LIKE across title, artist, album, filename, genre, remixer, label, comments |
| `--regex` / `-r` | Regular expression search | Python `re` across title, artist, album, filename, genre, remixer, comments |
| `--artist` / `-a` | Filter by artist | LIKE (or regex with `--re`) |
| `--title` / `-t` | Filter by title | LIKE (or regex with `--re`) |
| `--filename` | Filter by filename | LIKE (or regex with `--re`) |
| `--genre` / `-g` | Filter by genre | LIKE (or regex with `--re`) |
| `--key` / `-k` | Filter by musical key | LIKE (or regex with `--re`) |
| `--bpm-min` | Minimum BPM | >= |
| `--bpm-max` | Maximum BPM | <= |
| `--source` / `-s` | Filter by source label | LIKE |
| `--format` | Filter by file format | exact (e.g. mp3, wav) |
| `--in-rekordbox` | Only rekordbox tracks | flag |
| `--not-in-rekordbox` | Only non-rekordbox tracks | flag |
| `--no-cues` | RB tracks without cue points | special query |
| `--duplicates` | Duplicate filenames across sources | special query |
| `--playlists` | List all playlists | special query |
| `--playlist <name>` | Show tracks in a playlist | LIKE (or regex with `--re`) on name/path |
| `--re` | Switch field filters to regex mode | boolean flag modifier |
| `--limit` | Max results (default: 100) | int |

**All filters combine with AND.**

##### The `--re` flag (regex mode for field filters):
When `--re` is present, all text field filters (`--artist`, `--title`, `--filename`, `--genre`, `--key`, `--playlist`) switch from LIKE to Python regex matching. This lets you scope regex to specific fields.

Examples:
```bash
# Regex scoped to artist field only
dj-indexer search --re --artist ".*jay.*z.*"

# Regex on artist + must be in rekordbox
dj-indexer search --re --artist "bicep|objekt" --in-rekordbox

# Regex on playlist name
dj-indexer search --re --playlist "techno|hard.*house"

# Regex on genre + BPM range (BPM is numeric, not affected by --re)
dj-indexer search --re --genre "tech(no|house)" --bpm-min 125 --bpm-max 140

# Broad regex (all fields) -- does NOT need --re
dj-indexer search --regex "bicep|objekt"

# Broad regex + additional field filter
dj-indexer search --regex "remix" --in-rekordbox --bpm-min 120
```

Note: `--regex` (broad all-fields search) and `--re` (field filter modifier) are independent. You can use both together -- the broad regex adds an additional AND condition on top of the field filters.

##### Regex implementation:
SQLite has no built-in regex. Register a Python function on the connection:
```python
conn.create_function("REGEXP", 2,
    lambda pat, val: bool(re.search(pat, val, re.IGNORECASE)) if val else False)
```

When `--re` is active, field filters generate `REGEXP(?, t.column)` conditions instead of `t.column LIKE ?`. The REGEXP function must be registered once per connection when any regex feature is used.

##### Output format:
```
Search results (3 tracks):

   Bicep -- Glue
     129 BPM | 2A | USB1 [RB]  [3H/4C]
     /Volumes/USB1/Music/Bicep/Glue.mp3

   Bicep -- Atlas
     132 BPM | 11B | USB1 [RB]  [2H/2C]
     /Volumes/USB1/Music/Bicep/Atlas.mp3

   Unknown Artist -- Bicep - Glue.mp3
     ? BPM | ? | USB3 - Backup
     E:\Music\Backups\Bicep - Glue.mp3
```

- Show artist, title (or filename if no title), BPM, key, source label
- `[RB]` badge if `in_rekordbox = 1`
- `[3H/4C]` = 3 hot cues, 4 total cues
- `[NO CUES]` if in rekordbox but zero cue points
- Full file path on second line (platform-specific: Mac uses `/Volumes/...`, Windows uses drive letters)


#### `query <sql>` or `query --query-file <path>`
Run raw SQL SELECT queries against the database for custom analysis.

```bash
# Inline SQL
dj-indexer query "SELECT DISTINCT source_label FROM tracks WHERE in_rekordbox=1"

# From file (for multi-line queries)
dj-indexer query --query-file ~/my_query.sql
```

Tabular output with aligned columns and row count. Helper functions available:
- `DIRNAME(filepath)` — extract directory path (works cross-platform)
- `REGEXP(pattern, column)` — regex matching (case-insensitive)

Examples:
```bash
# Count tracks per folder
dj-indexer query "SELECT DIRNAME(filepath), COUNT(*) FROM tracks GROUP BY DIRNAME(filepath) ORDER BY COUNT(*) DESC"

# Find tracks with regex pattern in artist
dj-indexer query "SELECT artist, title FROM tracks WHERE REGEXP('bicep|fisher', artist)"
```

Only SELECT statements allowed (queries that modify data are rejected).


#### `analyze --folders [filters]`
Pre-built analytics breakdowns without requiring SQL knowledge.

**Options:**
- `--folders` — show track counts grouped by folder path
- `--in-rekordbox` — filter to rekordbox tracks only
- `--not-in-rekordbox` — filter to non-rekordbox tracks only
- `--source <label>` — filter by source label (e.g., "USB1")
- `--genre <genre>` — filter by genre
- `--format <format>` — filter by file format (e.g., ".mp3")
- `--bpm-min <bpm>` — minimum BPM
- `--bpm-max <bpm>` — maximum BPM
- `--limit <n>` — max results (default: 100)

Examples:
```bash
# All folders
dj-indexer analyze --folders

# Rekordbox tracks only
dj-indexer analyze --folders --in-rekordbox

# Specific source + BPM range
dj-indexer analyze --folders --source "USB1" --bpm-min 120 --bpm-max 140

# Multiple filters
dj-indexer analyze --folders --genre Techno --bpm-min 125 --source "USB1"
```

Output shows folder path and track count:
```
Folder Analysis (47 unique folders):

   /Volumes/USB1/Techno                       34 tracks
   /Volumes/USB1/House                        28 tracks
   /Volumes/USB1/Ambient                      12 tracks
```


#### `cues <query>`
Show detailed cue point information for tracks matching the query.

```
Deadmau5 — Strobe (10:37)
   128.0 BPM | 10A | USB3
   Cue points (6):
     [0:00.02] Memory Cue: Intro Mark
     [0:00.05] Hot Cue A: Start
     [4:00.50] Hot Cue B: Build
     [5:00.10] Hot Cue C: Drop
     [9:40.00] Hot Cue D: Outro
```

#### `stats`
Print collection statistics in a formatted box:
- Total tracks, in rekordbox, tracks with cue points, tracks with hot cues
- RB tracks without cues (highlighted as "need prep")
- Total cue points, playlists, duplicate filenames
- BPM range (min–max, avg)
- Tracks by source, by format, top genres

#### `export <output.csv> [--playlists]`
Export full index to CSV with columns: filename, title, artist, album, genre, bpm, musical_key, duration_sec, bitrate, file_format, source_label, in_rekordbox, filepath, comments, label, remixer, num_cues, num_hot_cues, cue_summary (concatenated cue info string).

With `--playlists`, export a separate CSV of all playlists with columns: playlist_name, playlist_path, position, title, artist, bpm, musical_key, filename. If an output filename is given like `tracks.csv`, the playlist file is auto-named `tracks_playlists.csv`.

```bash
# Export tracks only
dj-indexer export all_tracks.csv

# Export tracks + playlists
dj-indexer export all_tracks.csv --playlists

# Export playlists only
dj-indexer export-playlists playlists.csv
```

#### `export-playlists <output.csv>`
Standalone command to export all playlists to CSV. Each row is one track-in-playlist entry with columns: playlist_name, playlist_path, position, track_id, filename, title, artist, album, genre, bpm, musical_key.

## Database Schema

SQLite database (default: `dj_music_index.db`). Use WAL journal mode and foreign keys.

### `tracks` table
```sql
CREATE TABLE tracks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filepath TEXT UNIQUE,         -- full path (platform-specific)
    filename TEXT,                -- basename only
    filename_lower TEXT,          -- lowercase basename (for cross-platform matching)
    source_label TEXT,            -- user-provided label e.g. "USB1", "Rekordbox USB"
    title TEXT,
    artist TEXT,
    album TEXT,
    genre TEXT,
    bpm REAL,
    musical_key TEXT,             -- e.g. "2A", "11B" (Camelot/Open Key)
    duration_sec REAL,
    bitrate INTEGER,
    sample_rate INTEGER,
    file_format TEXT,             -- e.g. ".mp3", ".flac"
    file_size INTEGER,
    in_rekordbox INTEGER DEFAULT 0,
    rb_track_id TEXT,             -- rekordbox TrackID from XML
    rb_location TEXT,             -- original rekordbox location URL
    comments TEXT,
    rating INTEGER,
    label TEXT,                   -- record label
    remixer TEXT,
    color TEXT,                   -- rekordbox track color
    date_indexed TEXT DEFAULT (datetime('now'))
);
```

### `cue_points` table
```sql
CREATE TABLE cue_points (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    track_id INTEGER NOT NULL,
    cue_type TEXT,                -- "memory_cue", "hot_cue_A" through "hot_cue_H"
    cue_name TEXT,                -- user label e.g. "Drop", "Break"
    cue_num INTEGER,              -- -1 for memory, 0-7 for hot cues
    position_sec REAL,
    is_loop INTEGER DEFAULT 0,
    loop_end_sec REAL,
    color_red INTEGER,
    color_green INTEGER,
    color_blue INTEGER,
    FOREIGN KEY (track_id) REFERENCES tracks(id) ON DELETE CASCADE
);
```

### `playlists` table
```sql
CREATE TABLE playlists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    playlist_name TEXT,           -- leaf name e.g. "Techno Bangers"
    playlist_path TEXT,           -- full path e.g. "root/Genre/Techno Bangers"
    track_id INTEGER,
    position INTEGER,             -- track order within playlist
    FOREIGN KEY (track_id) REFERENCES tracks(id) ON DELETE CASCADE
);
```

### `anlz_data` table
```sql
CREATE TABLE anlz_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    track_id INTEGER NOT NULL,
    has_beat_grid INTEGER DEFAULT 0,
    has_waveform INTEGER DEFAULT 0,
    has_waveform_color INTEGER DEFAULT 0,
    anlz_path TEXT,
    FOREIGN KEY (track_id) REFERENCES tracks(id) ON DELETE CASCADE
);
```

### Indexes
Create indexes on: `filename`, `filename_lower`, `artist`, `title`, `genre`, `bpm`, `source_label`, `musical_key`, `cue_points.track_id`, `playlists.track_id`.

## Key Design Decisions

1. **Filename-based matching**: All cross-referencing uses `filename_lower` to work across Mac/Windows. This means duplicate filenames on different drives could collide — the first match wins, which is acceptable for this use case.

2. **COALESCE on updates**: When importing rekordbox XML over existing scanned data, use `COALESCE(NULLIF(new_value, ''), existing_value)` to avoid overwriting good ID3 metadata with empty rekordbox fields.

3. **ON CONFLICT upsert**: Scanning the same directory twice updates rather than duplicates.

4. **Cue type naming**: Memory cues are `"memory_cue"`, hot cues are `"hot_cue_A"` through `"hot_cue_H"` (mapped from `Num` 0-7 via `chr(65 + num)`).

5. **pyrekordbox for all rekordbox parsing**: Use pyrekordbox exclusively for XML and ANLZ parsing — it auto-decodes file:// URLs and provides a clean typed API.

6. **Proper package structure**: Logically separated modules under `src/dj_indexer/` with a CLI entry point registered in `pyproject.toml`.

## Error Handling

- Gracefully skip unreadable audio files (log warning, continue scanning)
- Handle missing/malformed XML fields with safe defaults
- Validate directory exists before scanning
- Check for PIONEER folder structure before ANLZ import
- Wrap all database operations in try/except

## Testing

Test against a mock rekordbox XML with:
- 5-8 tracks across multiple genres/BPMs
- Mix of tracks with hot cues, memory cues, loops, and no cues
- Nested playlist folder structure
- Tracks that should match scanned USB files by filename

Test scenarios:
1. Scan a directory → verify track count and metadata extraction
2. Import XML → verify matching, cue point extraction, playlist import
3. Search by free text, artist, regex, BPM range, genre
4. `--no-cues` finds RB tracks without cue points
5. `--duplicates` finds files on multiple drives
6. `--not-in-rekordbox` finds unmatched tracks
7. `cues` command shows detailed cue info with timestamps
8. `stats` shows accurate totals
9. Cross-platform: scan on "Mac" paths, import XML with "Windows" paths, verify matching works via filename_lower

## Example Usage Session

Basic workflow example:

```bash
# Step 1: Scan USB drives (on Mac)
uv run dj-indexer scan /Volumes/USB1 --label "USB1 - Main"
uv run dj-indexer scan /Volumes/USB2 --label "USB2 - DJ Music"

# Step 2: Copy db to Windows, then import rekordbox XML
uv run dj-indexer import-xml "C:\Users\me\rekordbox_collection.xml"

# Step 3: Explore and search
uv run dj-indexer stats
uv run dj-indexer search "bicep"
uv run dj-indexer search --artist "Aphex Twin" --in-rekordbox
uv run dj-indexer search --no-cues
uv run dj-indexer cues "strobe"
uv run dj-indexer export all_tracks.csv --playlists
```

**For comprehensive examples** covering all commands, see [docs/usage-examples.md](docs/usage-examples.md):
- Scanning multiple USB drives
- Cross-platform workflows (Mac → Windows)
- All search and filter options
- Regex patterns and complex queries
- Cue points and playlist management
- CSV export workflows
- Database management and tips
