# DJ Indexer Usage Examples

Complete examples for all commands and workflows.

## Table of Contents

- [Basic Setup](#basic-setup)
- [Scanning USB Drives](#scanning-usb-drives)
- [Importing Rekordbox Collections](#importing-rekordbox-collections)
- [Cross-Platform Workflow (Mac → Windows)](#cross-platform-workflow-mac--windows)
- [Search and Filtering](#search-and-filtering)
- [Query and Analysis](#query-and-analysis)
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

The search command is your main tool for exploring your music collection. It supports free-text search, regex patterns, field-specific filters, and special modes.

### Basic Syntax

```bash
# Basic free-text search
uv run dj-indexer search "bicep"

# With filters
uv run dj-indexer search [query] [--filter1] [value1] [--filter2] [value2]

# Multiple filters combine with AND
uv run dj-indexer search --artist "bicep" --genre "techno" --bpm-min 120
# Results: Bicep tracks that are techno AND >= 120 BPM
```

### Free-Text Search

Free-text search looks across all fields: title, artist, album, filename, genre, remixer, label, comments.

```bash
# Search across all fields
uv run dj-indexer search "bicep"

# Case-insensitive, matches partials
uv run dj-indexer search "deep"  # Matches "DeepDish", "Deeper", Deepbass", etc.
uv run dj-indexer search "drop"  # Matches titles, cue names, etc.

# Multi-word search (partial match)
uv run dj-indexer search "final cut"
```

**Output:**
```
Search results for "bicep" (12 tracks):

   Bicep -- Glue
     129 BPM | 11B | USB1 [RB]  [2H/4C]
     /Volumes/USB1/Music/Bicep/Glue.mp3

   Bicep -- Atlas
     132 BPM | 2A | USB1 [RB]  [3H/5C]
     /Volumes/USB1/Music/Bicep/Atlas.mp3

   Unknown Artist -- bicep_remix.mp3
     ? BPM | ? | USB2
     E:\Music\Backups\bicep_remix.mp3
```

### Regex Search (Broad)

Use `--regex` (or `-r`) to search with Python regular expressions across all fields.

```bash
# Alternation: Bicep OR Objekt
uv run dj-indexer search --regex "bicep|objekt"

# Multiple artists with variations
uv run dj-indexer search --regex "aphex.*twin|autechre|plaza"

# Pattern matching
uv run dj-indexer search --regex "^untitled|demo|sample"  # Starts with...
uv run dj-indexer search --regex ".*remix$"  # Ends with remix

# Case-insensitive is built-in
uv run dj-indexer search --regex "DEEP|deep"  # Matches any case
```

**Regex Patterns:**
```
^pattern    # Starts with
pattern$    # Ends with
pat|tern    # Alternation (OR)
pat.*tern   # Matches anything between
[abc]       # Character class
(pat)*      # Grouping and repetition
```

### Field-Scoped Regex (--re flag)

Use `--re` to apply regex only to specific field filters. All regex field filters use the pattern directly (no `%` wildcard wrapping).

```bash
# Regex on artist field only
uv run dj-indexer search --re --artist "bicep|objekt|mall"

# Regex on title field
uv run dj-indexer search --re --title "^drop|^build"

# Regex on genre
uv run dj-indexer search --re --genre "tech(no|house)"

# Regex on filename
uv run dj-indexer search --re --filename ".*demo.*\.mp3$"

# Combine multiple field filters with regex
uv run dj-indexer search --re --artist "bicep|objekt" --genre "techno"

# Mix field filters with numeric/exact filters
uv run dj-indexer search --re --artist "bicep.*" --bpm-min 120 --in-rekordbox
```

### Filter by Artist

```bash
# LIKE search (partial match, case-insensitive)
uv run dj-indexer search --artist "Aphex"  # Matches "Aphex Twin", "Aphexy", etc.

# Regex for more precise patterns
uv run dj-indexer search --re --artist "Aphex Twin|Autechre"
uv run dj-indexer search --re --artist "^Lee.*"  # Artist names starting with Lee
```

### Filter by Title

```bash
# Partial match
uv run dj-indexer search --title "Strobe"

# Regex for exact patterns
uv run dj-indexer search --re --title "^Untitled"  # Starts with Untitled
uv run dj-indexer search --re --title "remix$"  # Ends with remix
uv run dj-indexer search --re --title "part (1|2|3)"  # Part 1, Part 2, or Part 3
```

### Filter by Genre

```bash
# Partial match
uv run dj-indexer search --genre "techno"  # Matches "Techno", "Techno House", etc.
uv run dj-indexer search --genre "house"

# Regex patterns
uv run dj-indexer search --re --genre "tech(no|house)"  # Techno or Techhouse
uv run dj-indexer search --re --genre "(electro|minimal|tech)"
```

### Filter by BPM Range

```bash
# Between two values
uv run dj-indexer search --bpm-min 120 --bpm-max 130  # 120-130 BPM tracks

# Minimum only (everything >= 128 BPM)
uv run dj-indexer search --bpm-min 128

# Maximum only (everything <= 110 BPM)
uv run dj-indexer search --bpm-max 110

# DJ use case: Find high-energy tracks
uv run dj-indexer search --bpm-min 128 --in-rekordbox

# Find breakbeats/drum & bass
uv run dj-indexer search --bpm-min 160
```

### Filter by Musical Key

```bash
# Exact key
uv run dj-indexer search --key "11B"
uv run dj-indexer search --key "2A"

# Key family (all A keys)
uv run dj-indexer search --re --key ".*A$"

# Camelot wheel compatible keys (for mixing)
uv run dj-indexer search --re --key "11B|12A|1B"  # Same key group for mixing
```

### Filter by Filename

```bash
# Partial match in filename
uv run dj-indexer search --filename "demo"

# Regex on filename
uv run dj-indexer search --re --filename "^test_.*\.mp3$"
```

### Filter by File Format

```bash
# Single format
uv run dj-indexer search --format mp3
uv run dj-indexer search --format flac

# Format filtering use cases
uv run dj-indexer search --format wav --in-rekordbox  # High-quality tracks in RB
```

### Filter by Source Label

```bash
# Exact source match
uv run dj-indexer search --source "USB1"
uv run dj-indexer search --source "rekordbox"

# Partial match for sources
uv run dj-indexer search --source "USB"  # Any USB drive
```

### Rekordbox Status Filters

```bash
# Only tracks in Rekordbox
uv run dj-indexer search --in-rekordbox

# Only tracks NOT in Rekordbox (not yet imported)
uv run dj-indexer search --not-in-rekordbox

# Rekordbox tracks without any cue points (need preparation)
uv run dj-indexer search --no-cues

# Find duplicate filenames across sources (potential conflicts)
uv run dj-indexer search --duplicates
```

### Advanced: Complex Multi-Filter Queries

Combine multiple filters with AND logic:

```bash
# DJ set preparation: Techno tracks ready for mixing
uv run dj-indexer search --genre techno --bpm-min 125 --bpm-max 135 --in-rekordbox

# Find gaps: Dubstep not yet prepped
uv run dj-indexer search --genre dubstep --not-in-rekordbox

# Remixes between 120-140 BPM in Rekordbox (with cues)
uv run dj-indexer search --regex "remix" --bpm-min 120 --bpm-max 140 --in-rekordbox

# Tracks by specific artists in compatible keys
uv run dj-indexer search --re --artist "bicep|objekt|tim" --key "2A"

# High-energy unreleased tracks on USB3
uv run dj-indexer search --source "USB3" --bpm-min 130 --not-in-rekordbox

# All ambient tracks, sorted by source
uv run dj-indexer search --genre ambient --limit 200

# Tracks needing prep: In RB but no cues
uv run dj-indexer search --in-rekordbox --no-cues
```

### Output Format

Each search result shows:

```
Artist -- Title
  BPM | Key | Source [RB] [XH/YC]
  /full/path/to/file.mp3
```

**Badges explained:**
- `[RB]` - Track is in Rekordbox
- `[3H/5C]` - 3 hot cues (A-H), 5 total cues
- `[NO CUES]` - Rekordbox track with no cue points (needs prep)
- `?` - Unknown value (not scanned/imported)

The full file path appears on the second line (platform-specific: Mac uses `/Volumes/...`, Windows uses drive letters like `E:\...`)

### Limit Results

```bash
# Default is 100 results
uv run dj-indexer search "techno"

# Limit to 50 results
uv run dj-indexer search --limit 50 "techno"

# Get first 10 results
uv run dj-indexer search "deep" --limit 10

# Use with filters
uv run dj-indexer search --bpm-min 128 --limit 30
```

### Search Best Practices

**Performance:**
```bash
# Fast: Using exact/numeric filters first
uv run dj-indexer search --bpm-min 120 --bpm-max 130 --limit 50

# Slower: Broad regex with many results
uv run dj-indexer search --regex ".*"  # Don't do this!
```

**Technique: Narrow down before searching**
```bash
# First, find the genre
uv run dj-indexer search --genre "techno"

# Then add BPM range
uv run dj-indexer search --genre "techno" --bpm-min 120 --bpm-max 130

# Then check Rekordbox status
uv run dj-indexer search --genre "techno" --bpm-min 120 --bpm-max 130 --in-rekordbox
```

**Regex: Be specific**
```bash
# Good: Specific alternation
uv run dj-indexer search --re --artist "bicep|objekt|plaza"

# Avoid: Overly broad patterns
uv run dj-indexer search --regex ".*"
```

### Short Flags for Rapid Searching

Use short flags to type faster:

```bash
# Long form
uv run dj-indexer search "techno" --artist "bicep" --genre "techno" --bpm-min 120

# Short form
uv run dj-indexer search "techno" -a "bicep" -g "techno" --bpm-min 120

# Available short flags:
# -r = --regex
# -a = --artist
# -t = --title
# -g = --genre
# -k = --key
# -s = --source
```

### Search Reference Table

| Use Case | Command | Example |
|----------|---------|---------|
| **Basic Search** | `search <query>` | `search "bicep"` |
| **Regex (Broad)** | `search --regex <pattern>` | `search --regex "bicep\|objekt"` |
| **Regex (Field)** | `search --re --field <pattern>` | `search --re --artist "bicep\|objekt"` |
| **Artist Filter** | `search --artist <name>` | `search --artist "bicep"` |
| **Title Filter** | `search --title <name>` | `search --title "glue"` |
| **Genre Filter** | `search --genre <name>` | `search --genre "techno"` |
| **Key Filter** | `search --key <key>` | `search --key "2A"` |
| **BPM Min** | `search --bpm-min <bpm>` | `search --bpm-min 120` |
| **BPM Max** | `search --bpm-max <bpm>` | `search --bpm-max 130` |
| **BPM Range** | `search --bpm-min X --bpm-max Y` | `search --bpm-min 120 --bpm-max 130` |
| **Format Filter** | `search --format <fmt>` | `search --format mp3` |
| **Source Filter** | `search --source <label>` | `search --source "USB1"` |
| **In Rekordbox** | `search --in-rekordbox` | `search --in-rekordbox` |
| **Not In RB** | `search --not-in-rekordbox` | `search --not-in-rekordbox` |
| **No Cues** | `search --no-cues` | `search --no-cues` |
| **Duplicates** | `search --duplicates` | `search --duplicates` |
| **Playlists List** | `search --playlists` | `search --playlists` |
| **Playlist Filter** | `search --playlist <name>` | `search --playlist "Techno"` |
| **Limit Results** | `search --limit <n>` | `search --limit 50` |
| **Show Cues** | `cues <query>` | `cues "bicep"` |

### Common Filter Combinations

```bash
# Tech house tracks (125-128 BPM)
uv run dj-indexer search --genre "house" --bpm-min 125 --bpm-max 128

# All remixes in Rekordbox
uv run dj-indexer search --regex "remix" --in-rekordbox

# Artist tracks on USB2 not in Rekordbox
uv run dj-indexer search --artist "bicep" --source "USB2" --not-in-rekordbox

# Prepared tracks in key 2A (120-130 BPM)
uv run dj-indexer search --key "2A" --bpm-min 120 --bpm-max 130 --in-rekordbox

# Ambient tracks that need cues prepared
uv run dj-indexer search --genre "ambient" --in-rekordbox --no-cues

# All FLAC files in Rekordbox
uv run dj-indexer search --format flac --in-rekordbox

# Recent demos from USB3
uv run dj-indexer search --regex "demo" --source "USB3"

# High-energy prepared tracks
uv run dj-indexer search --bpm-min 128 --in-rekordbox
```

---

## Query and Analysis

### Raw SQL Queries

The `query` command lets you run custom SQL SELECT statements for advanced analysis.

#### Inline SQL

```bash
# Count tracks per source
uv run dj-indexer query "SELECT source_label, COUNT(*) as count FROM tracks GROUP BY source_label"

# Find distinct artist names
uv run dj-indexer query "SELECT DISTINCT artist FROM tracks WHERE artist IS NOT NULL ORDER BY artist"

# Tracks without metadata
uv run dj-indexer query "SELECT title, artist, bpm FROM tracks WHERE title IS NULL OR bpm IS NULL"

# BPM statistics
uv run dj-indexer query "SELECT MIN(bpm), MAX(bpm), AVG(bpm) FROM tracks WHERE bpm > 0"
```

#### Query from File

For multi-line queries, save to a file and use `--query-file`:

```bash
# Create a query file
cat > my_analysis.sql << 'EOF'
SELECT
    source_label,
    COUNT(*) as total_tracks,
    COUNT(CASE WHEN in_rekordbox=1 THEN 1 END) as in_rb,
    COUNT(DISTINCT genre) as genres
FROM tracks
GROUP BY source_label
ORDER BY total_tracks DESC
EOF

# Run the query
uv run dj-indexer query --query-file my_analysis.sql
```

#### Using Helper Functions

Two helper functions are registered for advanced queries:

**DIRNAME(filepath)** - Extract the directory path from a full filepath:
```bash
# Count tracks per folder
uv run dj-indexer query "SELECT DIRNAME(filepath) as folder, COUNT(*) FROM tracks GROUP BY DIRNAME(filepath) ORDER BY COUNT(*) DESC"

# Find folders with many Rekordbox tracks
uv run dj-indexer query "SELECT DIRNAME(filepath), COUNT(*) as n FROM tracks WHERE in_rekordbox=1 GROUP BY DIRNAME(filepath) HAVING COUNT(*) > 10"
```

**REGEXP(pattern, column)** - Regex pattern matching (case-insensitive):
```bash
# Remixes by any artist
uv run dj-indexer query "SELECT artist, title FROM tracks WHERE REGEXP('remix', title)"

# Specific artists using regex
uv run dj-indexer query "SELECT * FROM tracks WHERE REGEXP('^(bicep|objekt|autechre)$', artist) AND in_rekordbox=1"

# Tracks with numbers in title
uv run dj-indexer query "SELECT title FROM tracks WHERE REGEXP('[0-9]', title)"
```

#### Example Queries

```bash
# Folders with most tracks
uv run dj-indexer query "SELECT DIRNAME(filepath) as folder, COUNT(*) as tracks, COUNT(CASE WHEN in_rekordbox=1 THEN 1 END) as in_rb FROM tracks GROUP BY folder ORDER BY tracks DESC LIMIT 20"

# Average BPM by genre
uv run dj-indexer query "SELECT genre, ROUND(AVG(bpm), 1) as avg_bpm, COUNT(*) as count FROM tracks WHERE genre IS NOT NULL AND bpm > 0 GROUP BY genre ORDER BY avg_bpm DESC"

# Tracks needing prep (in RB, no cues)
uv run dj-indexer query "SELECT artist, title FROM tracks WHERE in_rekordbox=1 AND id NOT IN (SELECT DISTINCT track_id FROM cue_points) ORDER BY artist, title"

# File format breakdown
uv run dj-indexer query "SELECT file_format, COUNT(*) as count FROM tracks WHERE file_format IS NOT NULL GROUP BY file_format ORDER BY count DESC"

# Duplicate filenames across sources
uv run dj-indexer query "SELECT filename_lower, COUNT(*) as copies, GROUP_CONCAT(source_label) as sources FROM tracks GROUP BY filename_lower HAVING COUNT(*) > 1"
```

### Collection Analytics

The `analyze` command provides pre-built analytics breakdowns without requiring SQL knowledge.

#### Analyze by Folder

Show track counts grouped by folder:

```bash
# All folders
uv run dj-indexer analyze --folders

# Only Rekordbox tracks
uv run dj-indexer analyze --folders --in-rekordbox

# Specific source
uv run dj-indexer analyze --folders --source "USB1"

# By genre
uv run dj-indexer analyze --folders --genre "Techno"

# BPM range
uv run dj-indexer analyze --folders --bpm-min 120 --bpm-max 140

# Combined filters (all must match)
uv run dj-indexer analyze --folders --source "USB1" --genre "Techno" --bpm-min 120 --in-rekordbox
```

**Output Example:**
```
Folder Analysis (47 unique folders) [in rekordbox | source=USB1 | genre=Techno | bpm=120.0]:

   /Volumes/USB1/Techno/Peak Time              34 tracks
   /Volumes/USB1/Techno/Dark Techno            28 tracks
   /Volumes/USB1/Techno/Minimal                15 tracks
   /Volumes/USB1/House/Tech House              12 tracks
```

#### Analyze Options

Available filters for `analyze --folders`:
- `--in-rekordbox` — only tracks in rekordbox
- `--not-in-rekordbox` — only tracks NOT in rekordbox
- `--source <label>` — specific USB/source (e.g., "USB1")
- `--genre <name>` — filter by genre
- `--format <ext>` — filter by file format (e.g., ".mp3")
- `--bpm-min <bpm>` — minimum BPM
- `--bpm-max <bpm>` — maximum BPM
- `--limit <n>` — max folders to show (default: 100)

---

## Cue Points and Playlists

### Show Detailed Cue Points

The `cues` command shows all cue points for tracks matching a search query, with exact positions and names.

```bash
# Find cue points for tracks matching "strobe"
uv run dj-indexer cues "strobe"

# Show detailed cue info for an artist
uv run dj-indexer cues "bicep"

# Search by partial title
uv run dj-indexer cues "drop"

# Cues for specific genre (free-text search)
uv run dj-indexer cues "ambient"
```

**Output Example:**
```
Bicep — Glue (4:30)
   129 BPM | 2A | USB1
   Cue points (6):
     [0:05] Hot Cue A: Intro
     [1:30] Hot Cue B: Build
     [2:45] Hot Cue C: Drop
     [3:15] Memory Cue: Breakdown
     [4:00] Hot Cue D: Outro
     [4:20] Hot Cue E: Outro build

Bicep — Atlas (5:15)
   132 BPM | 11B | USB1
   Cue points (5):
     [0:02] Memory Cue
     [0:30] Hot Cue A: Intro
     [2:15] Hot Cue B: Build
     [3:45] Hot Cue C: Drop
     [4:50] Hot Cue D: Outro
```

**Cue Types:**
- **Hot Cues** (A-H): Quick access cues, 8 available per track
- **Memory Cue**: Unnamed marker, typically at track start

### Inspect Track Preparation

```bash
# See all cues for prepared tracks
uv run dj-indexer cues "bicep"

# Identify which tracks need cue points
uv run dj-indexer search --no-cues

# Show cues for all high-energy tracks
uv run dj-indexer cues "techno" | grep "128\|130\|132"  # Manually filter by BPM
```

### List All Playlists

```bash
# Show all playlists and folder structure
uv run dj-indexer search --playlists
```

**Output:**
```
Playlists (23):

   root/DJ Sets/2024/Spring
      12 tracks

   root/DJ Sets/2024/Summer
      18 tracks

   root/Genre/Techno
      245 tracks

   root/Genre/House
      167 tracks

   root/Genre/Ambient
      89 tracks

   ... (more playlists)
```

### Filter by Playlist

```bash
# Show all tracks in a playlist
uv run dj-indexer search --playlist "Techno"

# Partial playlist name match
uv run dj-indexer search --playlist "Genre"  # Matches all playlists containing "Genre"

# Regex on playlist name/path
uv run dj-indexer search --re --playlist "Techno|House"

# Find all playlists from 2024
uv run dj-indexer search --re --playlist "2024"

# Look inside nested playlist folders
uv run dj-indexer search --re --playlist "DJ Sets.*Spring"
```

**Output:**
```
Playlist: root/Genre/Techno (245 tracks):

   Bicep -- Glue
     129 BPM | 2A | USB1 [RB]  [2H/4C]

   Objekt -- Gooey
     127 BPM | 1A | USB1 [RB]  [1H/3C]

   ... (all tracks in playlist)
```

### Playlist Use Cases

```bash
# Find DJ sets by date
uv run dj-indexer search --re --playlist "2024.*(Jan|Feb|Mar)"

# List all genre playlists
uv run dj-indexer search --re --playlist "Genre/.*"

# Show specific genre from playlists
uv run dj-indexer search --playlist "Techno"

# Find all collaborative playlists
uv run dj-indexer search --re --playlist "Collab|feat"
```

---

## Real-World DJ Scenarios

Practical search workflows for common DJ situations.

### Preparing for a DJ Set

**Find high-energy tracks in your key:**
```bash
# 125-135 BPM techno in key 2A
uv run dj-indexer search --genre techno --bpm-min 125 --bpm-max 135 --key "2A" --in-rekordbox
```

**Check track readiness (all cues set):**
```bash
# Tracks without cues (these need prep)
uv run dj-indexer search --no-cues

# View detailed cue points for your set
uv run dj-indexer cues "my_set_playlist"  # After adding tracks to a playlist
```

**Build transition chains (compatible keys + BPM):**
```bash
# Camelot wheel transitions from 2A (same harmonic family)
uv run dj-indexer search --re --key "11B|12A|1B" --bpm-min 120 --bpm-max 130

# Follow one track to next (compatible key, similar BPM)
uv run dj-indexer search --key "2A" --bpm-min 128 --bpm-max 134 --in-rekordbox
```

### Finding Specific Tracks

**Track stuck in your head:**
```bash
# Partial artist/title match
uv run dj-indexer search --artist "Aphex" --title "window"

# Wildcard search
uv run dj-indexer search --regex "aphex.*window|window.*aphex"
```

**Remixes of a track:**
```bash
# All remixes
uv run dj-indexer search --regex "remix"

# Remixes by specific artist
uv run dj-indexer search --regex "bicep.*remix|remix.*bicep"

# Original vs. remixes of a track
uv run dj-indexer search --title "track_name"  # Shows all versions
```

**Find unreleased/demo tracks:**
```bash
# Demos and unreleased
uv run dj-indexer search --regex "demo|unreleased|draft|wip"

# Demos on USB3 backup
uv run dj-indexer search --regex "demo" --source "USB3"
```

### Library Analysis

**Check collection coverage:**
```bash
# All tracks imported to Rekordbox
uv run dj-indexer search --in-rekordbox

# Tracks NOT yet in Rekordbox (gap analysis)
uv run dj-indexer search --not-in-rekordbox

# Tracks with cues prepared
uv run dj-indexer search --no-cues  # Returns tracks WITHOUT cues (prep needed)
```

**Find duplicate files across drives:**
```bash
# Identify duplicates (same filename on different drives)
uv run dj-indexer search --duplicates

# Find specific duplicate
uv run dj-indexer search --duplicates  # Then manually inspect for "my_track.mp3"
```

**Library statistics:**
```bash
# Overall stats
uv run dj-indexer stats

# Breakdown by source
uv run dj-indexer search --source "USB1"
uv run dj-indexer search --source "USB2"
uv run dj-indexer search --source "rekordbox"
```

### Genre/Energy Discovery

**Find new music energy levels:**
```bash
# Explore different BPM ranges
uv run dj-indexer search --bpm-min 100 --bpm-max 110     # Deep/Tech house
uv run dj-indexer search --bpm-min 120 --bpm-max 130     # Main room techno
uv run dj-indexer search --bpm-min 140 --bpm-max 160     # Peak time / Hard dance
uv run dj-indexer search --bpm-min 170                   # Drum & Bass
```

**Explore genre relationships:**
```bash
# Minimal techno with ambient touches
uv run dj-indexer search --re --genre "minimal|ambient" --bpm-min 100 --bpm-max 110

# Experimental electronica
uv run dj-indexer search --re --genre "experimental|ambient|glitch"

# Crossover tracks (techno + house)
uv run dj-indexer search --re --genre "tech.*house|house.*tech"
```

### Building Playlists

**Explore playlist contents:**
```bash
# What's in the Techno playlist?
uv run dj-indexer search --playlist "Techno"

# Tracks added to DJ set folders
uv run dj-indexer search --re --playlist "DJ Sets"

# All playlists with "2024" (recent sets)
uv run dj-indexer search --re --playlist "2024"
```

**Find gaps in playlists:**
```bash
# Techno tracks NOT in any playlist
uv run dj-indexer search --genre "techno" --not-in-rekordbox
```

### Quality Control

**Check for metadata issues:**
```bash
# Tracks with missing artist info
uv run dj-indexer search "Unknown Artist"

# Tracks with generic filename (likely metadata issues)
uv run dj-indexer search --re --filename "track.*\d+\.mp3"

# Confirm bitrate/quality (export to CSV and inspect)
uv run dj-indexer export quality_check.csv
```

**Verify imported tracks:**
```bash
# All tracks in Rekordbox (and therefore prepared)
uv run dj-indexer search --in-rekordbox

# Check a specific artist is fully imported
uv run dj-indexer search --artist "bicep" --in-rekordbox
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

