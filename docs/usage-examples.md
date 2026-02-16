# DJ Indexer Usage Examples

Complete examples for all commands and workflows.

## Table of Contents

- [Basic Setup](#basic-setup)
- [Scanning USB Drives](#scanning-usb-drives)
- [Importing Rekordbox Collections](#importing-rekordbox-collections)
- [Cross-Platform Workflow (Mac → Windows)](#cross-platform-workflow-mac--windows)
- [Search and Filtering](#search-and-filtering)
- [Cue Points and Playlists](#cue-points-and-playlists)
- [Exporting Data](#exporting-data)
- [Database Management](#database-management)

---

## Basic Setup

### Install Dependencies

```bash
# Install runtime dependencies
uv sync

# Install with test dependencies
uv sync --extra test
```

### Verify Installation

```bash
uv run dj-indexer --help
```

---

## Scanning USB Drives

### Scan a Single USB Drive

```bash
# Mac
uv run dj-indexer scan /Volumes/USB1 --label "USB1-Main"

# Windows
uv run dj-indexer scan E:\Music --label "USB1-Main"
```

### Scan Multiple USB Drives

```bash
# Mac: Scan all drives into same database
uv run dj-indexer scan /Volumes/USB1 --label "USB1"
uv run dj-indexer scan /Volumes/USB2 --label "USB2-Backup"
uv run dj-indexer scan /Volumes/USB3 --label "USB3-Archive"

# Windows
uv run dj-indexer scan E:\Music --label "USB1"
uv run dj-indexer scan F:\Music --label "USB2-Backup"
```

### Scan to External USB Database

```bash
# Mac: Save database to external USB
uv run dj-indexer --db /Volumes/ExternalUSB/dj_music_index.db scan /Volumes/USB1 --label "USB1"

# Windows: Save database to external USB
uv run dj-indexer --db E:\dj_music_index.db scan F:\Music --label "USB1"
```

### View Scan Progress

Scanner prints progress every 100 tracks:
```
Scanning /Volumes/USB1 with label 'USB1'...
  Indexed 100 tracks...
  Indexed 200 tracks...
Scan complete. Indexed 247 tracks.
```

---

## Importing Rekordbox Collections

### Import Rekordbox XML

```bash
# Basic import (uses default dj_music_index.db)
uv run dj-indexer import-xml ~/Downloads/collection.xml

# Import to specific database
uv run dj-indexer --db ~/Music/dj_index.db import-xml ~/Downloads/collection.xml

# Import to external USB (Mac)
uv run dj-indexer --db /Volumes/ExternalUSB/dj_music_index.db import-xml ~/Downloads/collection.xml

# Import to external USB (Windows)
uv run dj-indexer --db E:\dj_music_index.db import-xml "C:\Users\YourName\Downloads\collection.xml"
```

### What Gets Imported

- ✅ Track metadata (title, artist, album, genre, BPM, key, bitrate, sample rate)
- ✅ Cue points (memory cues and hot cues A-H)
- ✅ Playlist structure (folders and nested playlists)
- ✅ Comments, label, remixer information
- ✅ Cross-platform matching by filename

### Example: Full Import Workflow

```bash
# Rekordbox 5 collection
uv run dj-indexer import-xml ~/Downloads/RB5_Collection.xml

# Rekordbox 6 collection
uv run dj-indexer --db ~/Music/rb6_index.db import-xml ~/Downloads/RB6_Collection.xml
```

---

## Cross-Platform Workflow (Mac → Windows)

The complete workflow for Mac → USB → Windows:

### Step 1: Mac - Scan USB Drives

```bash
# Check USB drives mounted on Mac
ls /Volumes

# Scan multiple drives to external USB database
uv run dj-indexer --db /Volumes/ExternalUSB/dj_music_index.db \
  scan /Volumes/USB1 --label "USB1-Main"

uv run dj-indexer --db /Volumes/ExternalUSB/dj_music_index.db \
  scan /Volumes/USB2 --label "USB2-Backup"

# Verify
uv run dj-indexer --db /Volumes/ExternalUSB/dj_music_index.db stats
```

### Step 2: Mac - Optional: Import Rekordbox XML

```bash
uv run dj-indexer --db /Volumes/ExternalUSB/dj_music_index.db \
  import-xml ~/Downloads/collection.xml
```

### Step 3: Transfer USB to Windows

1. Eject USB from Mac (`Cmd+E` or right-click → Eject)
2. Connect USB to Windows
3. Note the drive letter (check File Explorer)

### Step 4: Windows - Search and Analyze

```bash
# Find the drive letter (let's say E:\)
# Database is at E:\dj_music_index.db

# View statistics
uv run dj-indexer --db E:\dj_music_index.db stats

# Search and filter
uv run dj-indexer --db E:\dj_music_index.db search "bicep"

# Find tracks needing cue prep
uv run dj-indexer --db E:\dj_music_index.db search --no-cues

# Export for analysis
uv run dj-indexer --db E:\dj_music_index.db export C:\Users\YourName\Downloads\tracks.csv
```

### Key Points

✅ **Automatic Filename Matching**: Cross-platform matching works via `filename_lower`
- Mac path: `/Volumes/USB1/Music/Artist/Track.mp3`
- Windows path: `E:\Music\Artist\Track.mp3`
- Both match on filename: `track.mp3`

✅ **No Data Loss**: SQLite databases are portable and work identically on Mac/Windows

✅ **Metadata Preservation**: All scanner metadata is preserved when importing XML

---

## Search and Filtering

### Free-Text Search

```bash
# Search across all fields (title, artist, album, filename, genre, etc.)
uv run dj-indexer search "bicep"

# Case-insensitive, matches partials
uv run dj-indexer search "deep"  # Matches "DeepDish", "Deeper", etc.
```

### Regex Search

```bash
# Broad regex across all fields
uv run dj-indexer search --regex "bicep|objekt|mall.*grab"

# Regex for artist only
uv run dj-indexer search --re --artist "bicep|objekt"

# Multiple conditions with regex
uv run dj-indexer search --regex "remix" --in-rekordbox --bpm-min 120
```

### Filter by Artist

```bash
# LIKE search (partial match)
uv run dj-indexer search --artist "Aphex"

# Regex search (exact patterns)
uv run dj-indexer search --re --artist "Aphex Twin|Autechre"
```

### Filter by Title

```bash
uv run dj-indexer search --title "Strobe"
uv run dj-indexer search --re --title "^Untitled|Demo"
```

### Filter by Genre

```bash
uv run dj-indexer search --genre "techno"
uv run dj-indexer search --re --genre "tech(no|house)" --bpm-min 120
```

### Filter by BPM Range

```bash
# Between 120-130 BPM
uv run dj-indexer search --bpm-min 120 --bpm-max 130

# Minimum BPM only
uv run dj-indexer search --bpm-min 128

# Maximum BPM only
uv run dj-indexer search --bpm-max 140
```

### Filter by Musical Key

```bash
uv run dj-indexer search --key "11B"
uv run dj-indexer search --re --key "^11.*|^2A"
```

### Filter by File Format

```bash
# Only MP3 files
uv run dj-indexer search --format mp3

# Only FLAC or WAV
uv run dj-indexer search --format flac
uv run dj-indexer search --format wav
```

### Filter by Source

```bash
# Only from USB1
uv run dj-indexer search --source "USB1"

# Only from Rekordbox XML
uv run dj-indexer search --source "rekordbox"
```

### Rekordbox Status Filters

```bash
# Only tracks in Rekordbox
uv run dj-indexer search --in-rekordbox

# Only tracks NOT in Rekordbox
uv run dj-indexer search --not-in-rekordbox

# Rekordbox tracks without cue points (need prep)
uv run dj-indexer search --no-cues

# Tracks with duplicate filenames (on multiple drives)
uv run dj-indexer search --duplicates
```

### Complex Queries (Multiple Filters)

```bash
# Techno tracks 125-130 BPM in Rekordbox with cues
uv run dj-indexer search --genre techno --bpm-min 125 --bpm-max 130 --in-rekordbox

# Dubstep tracks on USB3 not yet in Rekordbox
uv run dj-indexer search --genre dubstep --source "USB3" --not-in-rekordbox

# Remixes between 120-140 BPM in Rekordbox
uv run dj-indexer search --regex "remix" --bpm-min 120 --bpm-max 140 --in-rekordbox

# Tracks by specific artists in key 2A
uv run dj-indexer search --re --artist "bicep|objekt" --key "2A"
```

### Limit Results

```bash
# Limit to 50 results (default is 100)
uv run dj-indexer search --limit 50 "techno"

# Get first 10 results
uv run dj-indexer search "deep" --limit 10
```

---

## Cue Points and Playlists

### Show Cue Points for Tracks

```bash
# Find cue points for tracks matching "strobe"
uv run dj-indexer cues "strobe"

# Show detailed cue info
uv run dj-indexer cues "bicep"
```

**Output Example:**
```
Bicep — Glue (4:30)
   129 BPM | 2A | USB1
   Cue points (6):
     [0:05.10] Hot Cue A: Intro
     [1:30.50] Hot Cue B: Build
     [2:45.00] Hot Cue C: Drop
     [3:15.20] Memory Cue: Breakdown
     [4:10.00] Hot Cue D: Outro
```

### List All Playlists

```bash
uv run dj-indexer search --playlists
```

### Filter by Playlist

```bash
# Tracks in "Techno" playlist
uv run dj-indexer search --playlist "Techno"

# Regex on playlist name
uv run dj-indexer search --re --playlist "techno|house"
```

---

## Exporting Data

### Export All Tracks to CSV

```bash
# Export to current directory
uv run dj-indexer export all_tracks.csv

# Export to specific location (Mac)
uv run dj-indexer export ~/Music/backups/all_tracks.csv

# Export to specific location (Windows)
uv run dj-indexer export "C:\Users\YourName\Music\all_tracks.csv"
```

**CSV Columns:**
```
filename, title, artist, album, genre, bpm, musical_key, duration_sec,
bitrate, file_format, source_label, in_rekordbox, filepath, comments,
label, remixer, num_cues, num_hot_cues, cue_summary
```

### Export with Playlists

```bash
# Creates two files:
#   - all_tracks.csv (full track index)
#   - all_tracks_playlists.csv (playlist contents)
uv run dj-indexer export all_tracks.csv --playlists
```

### Export Playlists Only

```bash
uv run dj-indexer export-playlists playlists.csv
```

**Playlist CSV Columns:**
```
playlist_name, playlist_path, position, track_id, filename, title, artist,
album, genre, bpm, musical_key
```

### Example: Backup Workflow

```bash
# Full backup to external drive (Mac)
uv run dj-indexer export /Volumes/Backup/dj_index_$(date +%Y%m%d).csv --playlists

# Full backup to external drive (Windows)
uv run dj-indexer export E:\Backups\dj_index.csv --playlists
```

---

## Database Management

### Use Custom Database Location

```bash
# All commands support --db flag
uv run dj-indexer --db ~/Music/my_index.db scan /Volumes/USB1 --label "USB1"

# Can be local or on USB/external drive
uv run dj-indexer --db /Volumes/ExternalUSB/dj_music_index.db stats
```

### View Database Statistics

```bash
# Basic statistics
uv run dj-indexer stats

# From specific database
uv run dj-indexer --db ~/Music/my_index.db stats
```

**Output:**
```
============================================================
                 DJ MUSIC INDEX STATISTICS
============================================================

Tracks:
  Total:                 1,247
  In Rekordbox:          1,100 (88.2%)
  With any cue points:   892
  With hot cues:         756
  [!] RB tracks no cues:  245 (need prep)

Cue Points:
  Total cue points:      3,547

Playlists & Duplicates:
  Playlists:             42
  Duplicate files:       3

Tracks by Source:
  USB1                           450
  USB2-Backup                    320
  rekordbox XML                  477

Tracks by Format:
  .mp3                           602
  .flac                          345
  .wav                           198
  .m4a                           102

BPM Distribution:
  Range: 80-150 BPM
  Average: 124.3 BPM

============================================================
```

### Database Location Best Practices

```bash
# Default location (current directory)
# dj_music_index.db

# Organized locations:
# Mac
~/Music/dj_indexer/dj_music_index.db

# Windows
C:\Users\YourName\Music\dj_indexer\dj_music_index.db

# External USB (portable, cross-platform)
/Volumes/ExternalUSB/dj_music_index.db  (Mac)
E:\dj_music_index.db                     (Windows)
```

---

## Tips & Tricks

### Rapid Search Iteration

```bash
# Use short flags for faster typing
uv run dj-indexer search "techno" -a "bicep" -k "2A" --bpm-min 120

# Short flags:
# -a = --artist
# -t = --title
# -g = --genre
# -k = --key
# -s = --source
# -r = --regex
```

### Save Search Results

```bash
# Export filtered search results
# (Note: search command outputs to terminal, use export for full dataset)
uv run dj-indexer export results.csv
# Then filter in Excel/spreadsheet
```

### Find Gaps in Collection

```bash
# Tracks not yet in Rekordbox
uv run dj-indexer search --not-in-rekordbox

# Rekordbox tracks without cues
uv run dj-indexer search --no-cues

# Duplicate filenames (potential issues)
uv run dj-indexer search --duplicates
```

### Prepare for DJing

```bash
# High-energy tracks (130+ BPM)
uv run dj-indexer search --bpm-min 130 --in-rekordbox

# Tracks with full cue points prepared
uv run dj-indexer search --no-cues --in-rekordbox
# (this returns empty = all tracks have cues!)

# Specific key + BPM for mixing
uv run dj-indexer search --key "11B" --bpm-min 128 --bpm-max 132
```

---

## Troubleshooting

### Command Not Found: `uv`

```bash
# Make sure uv is installed
which uv

# If not found, install: https://docs.astral.sh/uv/
```

### pytest Not Found

```bash
# Install test dependencies first
uv sync --extra test

# Then run tests
uv run pytest tests/
```

### Database Locked (Windows)

```bash
# Make sure no Windows Explorer window is open on USB drive
# Or wait a few seconds for Windows indexing to complete
```

### USB Drive Not Recognized

**Mac:**
```bash
# Check mounted volumes
ls /Volumes

# If USB doesn't appear, try reconnecting
# Check System Information → USB
```

**Windows:**
```bash
# Check Device Manager or Disk Management
# Assign drive letter if needed
```

### Interrupted XML Import (Ctrl+C or Crash)

If you interrupt the `import-xml` command with Ctrl+C or it crashes mid-way:

**The database is safe!** The import uses incremental commits, so:
- Already-imported tracks are saved in the database
- Playlists are fully replaced on each run (always fresh)
- Cue points are refreshed per track

Just **re-run the same command**:
```bash
# Simply re-run, it will:
# 1. Skip tracks already imported (marked as "already done")
# 2. Re-import playlists from XML
# 3. Complete where it left off
uv run dj-indexer import-xml ~/Downloads/collection.xml
```

Progress output shows tracks skipped:
```
[3/4] Importing tracks and metadata...
  Processing: 100%|##########| 1000/1000 [00:05<00:00, 198.5track/s]
  (700 imported, 300 skipped - already done)
```

**No data loss, no corruption** — the import is designed to be fully resumable.

