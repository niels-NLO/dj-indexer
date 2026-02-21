# DJ Indexer Database Schema

Complete documentation of the SQLite database structure, tables, columns, and relationships.

## Overview

The DJ Indexer uses SQLite with the following design principles:
- **WAL mode** — Write-Ahead Logging for better concurrency
- **Foreign keys** — Enforced referential integrity
- **Cascading deletes** — Removing a track automatically removes its cue points and playlists
- **Cross-platform** — Uses `filename_lower` for matching across Mac/Windows paths
- **Efficient indexing** — Indexes on frequently searched columns

## Quick Navigation

- [File Path and Folder Organization](#file-path-and-folder-organization)
- [tracks Table](#tracks-table)
- [cue_points Table](#cue_points-table)
- [playlists Table](#playlists-table)
- [anlz_data Table](#anlz_data-table)
- [Data Flow Diagram](#data-flow-diagram)
- [Cross-Platform Matching](#cross-platform-matching)
- [Constraints & Integrity](#constraints--integrity)
- [Indexing Strategy](#indexing-strategy)
- [Performance Considerations](#performance-considerations)
- [Example Queries](#example-queries)

## Table Relationships

```
tracks (1)
├── cue_points (many) — one-to-many relationship
├── playlists (many) — one-to-many relationship (track position in playlists)
└── anlz_data (many) — one-to-many relationship (beat grid, waveform data)
```

---

## File Path and Folder Organization

### Path Storage

The `filepath` column stores the **complete, platform-specific path** to each audio file:

**Mac example:**
```
/Volumes/USB1/Music/Techno/Bicep/Glue.mp3
/Volumes/USB1/Music/House/Fisher/Losing It.flac
/Volumes/USB2-Backup/Archive/2023/Deep House/Track.mp3
```

**Windows example:**
```
E:\Music\Techno\Bicep\Glue.mp3
F:\Backups\House\Fisher\Losing It.flac
D:\Archive\2023\Deep House\Track.mp3
```

### Folder Extraction with DIRNAME()

The `DIRNAME()` function extracts the directory path from `filepath`:

```
filepath: /Volumes/USB1/Music/Techno/Bicep/Glue.mp3
DIRNAME(): /Volumes/USB1/Music/Techno/Bicep
```

**Works cross-platform:**
```python
# Implementation in query.py
conn.create_function("DIRNAME", 1,
    lambda p: str(Path(p).parent) if p else None)
```

### Folder Analysis & Grouping

**Common use case: Track counts by folder**

```bash
# See all folders and their track counts
uv run dj-indexer query "SELECT DIRNAME(filepath) as folder, COUNT(*) as tracks FROM tracks GROUP BY folder ORDER BY tracks DESC"
```

**Output example:**
```
folder                                           | tracks
-------------------------------------------------+-------
/Volumes/USB1/Music/Techno                      | 342
/Volumes/USB1/Music/House                       | 218
/Volumes/USB1/Music/Ambient                     | 156
/Volumes/USB2-Backup/Archive/2023               | 89
/Volumes/USB2-Backup/Archive/2022               | 45
```

### Folder Hierarchy Analysis

**Analyze folder structure by depth:**

```bash
# Top-level folders (one level deep from mount point)
uv run dj-indexer query "SELECT SUBSTR(DIRNAME(filepath), 1, INSTR(DIRNAME(filepath)||'/', '/')-1) as root, COUNT(*) FROM tracks GROUP BY root"

# Specific folder structure for USB1
uv run dj-indexer query "SELECT DIRNAME(filepath), COUNT(*) FROM tracks WHERE DIRNAME(filepath) LIKE '/Volumes/USB1/%' GROUP BY DIRNAME(filepath) ORDER BY COUNT(*) DESC"
```

### Organize & Search by Folder

**Find all tracks in a specific folder:**
```bash
uv run dj-indexer query "SELECT artist, title, bpm FROM tracks WHERE DIRNAME(filepath) = '/Volumes/USB1/Music/Techno' ORDER BY artist, title"
```

**Find tracks in a folder pattern:**
```bash
# All tracks in any "Techno" folder
uv run dj-indexer query "SELECT DIRNAME(filepath), COUNT(*) FROM tracks WHERE DIRNAME(filepath) LIKE '%/Techno%' GROUP BY DIRNAME(filepath)"

# All tracks from 2024 archives
uv run dj-indexer query "SELECT DIRNAME(filepath), COUNT(*) FROM tracks WHERE DIRNAME(filepath) LIKE '%/2024/%' GROUP BY DIRNAME(filepath)"
```

### Folder Statistics

**Analyze music collection by folder location:**

```bash
# Techno tracks by folder
uv run dj-indexer analyze --folders --genre Techno

# Rekordbox-prepared tracks by location
uv run dj-indexer analyze --folders --in-rekordbox

# Specific USB drive breakdown
uv run dj-indexer analyze --folders --source "USB1"
```

### Cross-Platform Folder Matching

**Important:** Folders are **NOT matched cross-platform** because paths differ.

**Scenario:**
- Mac scan: `/Volumes/USB1/Music/Techno/track.mp3`
- Windows RB import: `E:\Music\Techno\track.mp3`

**Same track, different folders!**

Solution: Match by `filename_lower`, update `in_rekordbox` flag, keep both folder paths:

```
tracks.id: 1
tracks.filepath: /Volumes/USB1/Music/Techno/track.mp3        (from Mac)
tracks.filename_lower: track.mp3

tracks.id: 1 (same)
tracks.rb_location: file:///E|/Music/Techno/track.mp3        (from RB XML)
```

---

## `tracks` Table

Core table containing all audio tracks in the collection.

### Column Definitions

| Column | Type | Purpose | Notes |
|--------|------|---------|-------|
| `id` | INTEGER PRIMARY KEY | Unique identifier | Auto-incremented, used to reference from other tables |
| `filepath` | TEXT UNIQUE | Full file path | Platform-specific: `/Volumes/USB1/...` (Mac) or `E:\Music\...` (Windows) |
| `filename` | TEXT | Basename only | e.g., `Glue.mp3` |
| `filename_lower` | TEXT | Lowercase filename | Used for cross-platform matching between Mac and Windows |
| `source_label` | TEXT | User-provided label | e.g., "USB1", "USB2-Backup", "rekordbox XML" |
| `title` | TEXT (nullable) | Track title | Extracted from metadata; may be NULL if not tagged |
| `artist` | TEXT (nullable) | Artist name | Extracted from metadata; may be NULL |
| `album` | TEXT (nullable) | Album name | Extracted from metadata; may be NULL |
| `genre` | TEXT (nullable) | Music genre | Extracted from metadata; may be NULL |
| `bpm` | REAL (nullable) | Beats per minute | Extracted from metadata; may be NULL or 0 if not set |
| `musical_key` | TEXT (nullable) | Musical key | Format: Camelot (e.g., "2A") or Open Key; may be NULL |
| `duration_sec` | REAL (nullable) | Track length in seconds | Calculated from audio; may be NULL |
| `bitrate` | INTEGER (nullable) | Bitrate in kbps | Extracted from audio; may be NULL |
| `sample_rate` | INTEGER (nullable) | Sample rate in Hz | Extracted from audio; may be NULL |
| `file_format` | TEXT (nullable) | File extension | e.g., ".mp3", ".flac", ".wav"; may be NULL |
| `file_size` | INTEGER (nullable) | File size in bytes | May be NULL |
| `in_rekordbox` | INTEGER | Rekordbox flag | 0 = not in RB, 1 = imported from rekordbox XML/USB |
| `rb_track_id` | TEXT (nullable) | Rekordbox TrackID | Internal ID from rekordbox; used for matching |
| `rb_location` | TEXT (nullable) | Rekordbox file URL | Original file location from rekordbox XML |
| `comments` | TEXT (nullable) | User comments | From rekordbox or audio metadata |
| `rating` | INTEGER (nullable) | Rating (0-5) | From rekordbox; may be NULL |
| `label` | TEXT (nullable) | Record label | From rekordbox metadata |
| `remixer` | TEXT (nullable) | Remixer name | From rekordbox metadata |
| `color` | TEXT (nullable) | Rekordbox color | Color assigned in rekordbox (e.g., "Red", "Blue") |
| `date_indexed` | TEXT | Timestamp | Created on first insertion; default: `datetime('now')` |

### Indexes

- `idx_tracks_filename` — Fast lookup by filename
- `idx_tracks_filename_lower` — Fast cross-platform lookup (critical for Mac/Windows matching)
- `idx_tracks_artist` — Search by artist
- `idx_tracks_title` — Search by title
- `idx_tracks_genre` — Filter by genre
- `idx_tracks_bpm` — BPM range queries
- `idx_tracks_source_label` — Filter by USB/source
- `idx_tracks_musical_key` — Filter by key

### Example Rows

**From USB scan (Mac):**
```
id: 1
filepath: /Volumes/USB1/Music/Bicep/Glue.mp3
filename: Glue.mp3
filename_lower: glue.mp3
source_label: USB1 - Main
title: Glue
artist: Bicep
album: Isles
genre: Techno
bpm: 129.0
musical_key: 11B
in_rekordbox: 0
date_indexed: 2024-02-21 10:30:45
```

**From Rekordbox import:**
```
id: 2
filepath: E:\Music\Bicep\Glue.mp3
filename: Glue.mp3
filename_lower: glue.mp3  ← Matches the Mac entry (cross-platform)
source_label: rekordbox XML
title: Glue
artist: Bicep
album: Isles
genre: Techno
bpm: 129.0
musical_key: 11B
in_rekordbox: 1
rb_track_id: 12345
rb_location: file:///E|/Music/Bicep/Glue.mp3
rating: 5
label: Ninja Tune
color: Red
```

---

## `cue_points` Table

Stores all cue points (hot cues, memory cues, and loops) for tracks.

### Column Definitions

| Column | Type | Purpose | Notes |
|--------|------|---------|-------|
| `id` | INTEGER PRIMARY KEY | Unique identifier | Auto-incremented |
| `track_id` | INTEGER (FK) | Reference to track | Foreign key to `tracks(id)`; deletes cascade |
| `cue_type` | TEXT | Type of cue | Values: `"memory_cue"`, `"hot_cue_A"` through `"hot_cue_H"` |
| `cue_name` | TEXT (nullable) | User label | e.g., "Drop", "Break", "Intro" |
| `cue_num` | INTEGER | Cue position number | -1 for memory cues; 0-7 for hot cues A-H |
| `position_sec` | REAL | Position in seconds | Timestamp within the track |
| `is_loop` | INTEGER | Loop flag | 0 = cue point, 1 = loop marker |
| `loop_end_sec` | REAL (nullable) | Loop end position | Only set if `is_loop = 1` |
| `color_red` | INTEGER (nullable) | Red channel (0-255) | RGB color value |
| `color_green` | INTEGER (nullable) | Green channel (0-255) | RGB color value |
| `color_blue` | INTEGER (nullable) | Blue channel (0-255) | RGB color value |

### Indexes

- `idx_cue_points_track_id` — Fast lookup of cues for a track

### Hot Cue Mapping

Hot cues use numeric positions mapped to letters:
- `cue_num=0` → `hot_cue_A`
- `cue_num=1` → `hot_cue_B`
- ...
- `cue_num=7` → `hot_cue_H`
- `cue_num=-1` → `memory_cue` (unlimited, not assigned to a letter)

### Example Rows

**Memory cue:**
```
id: 101
track_id: 1
cue_type: memory_cue
cue_name: Intro Mark
cue_num: -1
position_sec: 5.5
is_loop: 0
```

**Hot cue with color:**
```
id: 102
track_id: 1
cue_type: hot_cue_A
cue_name: Drop
cue_num: 0
position_sec: 32.5
is_loop: 0
color_red: 255
color_green: 0
color_blue: 0
```

**Loop marker:**
```
id: 103
track_id: 1
cue_type: hot_cue_B
cue_name: Breakdown
cue_num: 1
position_sec: 64.0
loop_end_sec: 96.0
is_loop: 1
```

---

## `playlists` Table

Maps tracks to their positions within playlists (imported from rekordbox).

### Column Definitions

| Column | Type | Purpose | Notes |
|--------|------|---------|-------|
| `id` | INTEGER PRIMARY KEY | Unique identifier | Auto-incremented |
| `playlist_name` | TEXT | Playlist name | Leaf node name; e.g., "Techno Bangers" |
| `playlist_path` | TEXT | Full playlist path | Hierarchical path; e.g., "root/Genre/Techno Bangers" |
| `track_id` | INTEGER (FK) | Reference to track | Foreign key to `tracks(id)`; deletes cascade |
| `position` | INTEGER | Order in playlist | 1-indexed position within the playlist |

### Indexes

- `idx_playlists_track_id` — Fast lookup of playlists containing a track

### Example Rows

```
id: 1
playlist_name: Techno Bangers
playlist_path: root/Techno Bangers
track_id: 1
position: 1

id: 2
playlist_name: Techno Bangers
playlist_path: root/Techno Bangers
track_id: 3
position: 2

id: 3
playlist_name: Chill Vibes
playlist_path: root/Genre/Ambient/Chill
track_id: 5
position: 1
```

**Nested playlist structure:**
```
root/
├── Techno Bangers/
│   ├── track_id=1, position=1
│   └── track_id=3, position=2
├── Genre/
│   └── Ambient/
│       └── Chill/
│           └── track_id=5, position=1
└── House/
    └── track_id=2, position=1
```

---

## `anlz_data` Table

Stores references to Rekordbox ANLZ analysis files (beat grids, waveforms, cue points).

### Column Definitions

| Column | Type | Purpose | Notes |
|--------|------|---------|-------|
| `id` | INTEGER PRIMARY KEY | Unique identifier | Auto-incremented |
| `track_id` | INTEGER (FK) | Reference to track | Foreign key to `tracks(id)`; deletes cascade |
| `has_beat_grid` | INTEGER | Beat grid flag | 0 or 1; indicates if ANLZ0000.DAT contains beat grid |
| `has_waveform` | INTEGER | Waveform flag | 0 or 1; indicates if analysis includes waveform preview |
| `has_waveform_color` | INTEGER | Color waveform flag | 0 or 1; indicates if waveform has color data |
| `anlz_path` | TEXT (nullable) | Path to ANLZ file | File path for reference; e.g., `PIONEER/USBANLZ/xxx/uuid/ANLZ0000.DAT` |

### Indexes

- `idx_anlz_data_track_id` — Fast lookup of analysis data for a track

### Example Rows

```
id: 1
track_id: 1
has_beat_grid: 1
has_waveform: 1
has_waveform_color: 1
anlz_path: PIONEER/USBANLZ/01/uuid-1234/ANLZ0000.DAT

id: 2
track_id: 2
has_beat_grid: 0
has_waveform: 0
has_waveform_color: 0
anlz_path: NULL
```

---

## Data Flow Diagram

### 1. USB Scan Workflow (Mac)

```
USB Drive → Scanner (mutagen)
             ↓
         Extract metadata:
         - filepath, filename, title, artist, album, genre, bpm, key, duration
         - bitrate, sample_rate, file_format, file_size
             ↓
         Insert/Update tracks table
         - filename_lower = filename.lower()
         - in_rekordbox = 0
         - source_label = user-provided label (e.g., "USB1")
```

### 2. Rekordbox XML Import Workflow

```
Rekordbox XML → Parser (pyrekordbox)
             ↓
         Extract from XML:
         - Tracks: name, artist, album, genre, bpm, tonality, etc.
         - Cue points: name, position, type, hot cue number
         - Playlists: hierarchical structure
             ↓
         Match to existing tracks by filename_lower:
         ├─ Match found:
         │  └─ Update existing track with RB metadata (using COALESCE)
         │     - Set in_rekordbox = 1, rb_track_id, rb_location, etc.
         │
         └─ No match:
            └─ Insert as new track with source_label = "rekordbox XML"
             ↓
         Insert cue_points for matched/new tracks
             ↓
         Insert playlists (with playlist_path hierarchy)
```

### 3. Rekordbox USB ANLZ Import Workflow

```
Rekordbox USB → ANLZ Scanner (pyrekordbox.anlz)
             ↓
         Parse ANLZ binary files in PIONEER/USBANLZ/
         Extract:
         - Beat grid data
         - Waveform preview
         - Cue points (convert ms → seconds)
             ↓
         Match to existing tracks by filename
             ↓
         Insert anlz_data with analysis flags
             ↓
         Insert/Update cue_points
```

### 4. Search Query Workflow

```
Search Command → Build WHERE clause
             ↓
         Construct SQL query with:
         - Field filters (LIKE or REGEXP)
         - BPM range filters
         - Rekordbox status filters
         - Special modes (no-cues, duplicates, playlists)
             ↓
         JOIN tracks with cue_points to count cues
             ↓
         Execute and format results
             ↓
         Display with full filepath, badges, cue counts
```

---

## Cross-Platform Matching

**Critical Design:** All cross-platform matching uses `filename_lower`, not full filepath.

**Why?** File paths differ:
- Mac: `/Volumes/USB1/Music/Artist/Song.mp3`
- Windows: `E:\Music\Artist\Song.mp3`

**Solution:**
1. Scan on Mac → store `filename_lower = "song.mp3"`
2. Import XML on Windows with same filename → match by `filename_lower`
3. Single database now contains metadata from both sources
4. Display shows platform-specific `filepath` for current platform

**Example:**
```
Track 1 (Mac scan):
  filepath: /Volumes/USB1/Music/Bicep/Glue.mp3
  filename_lower: glue.mp3
  in_rekordbox: 0

Track 2 (RB import on Windows):
  filepath: E:\Music\Bicep\Glue.mp3
  filename_lower: glue.mp3  ← MATCHES!
  in_rekordbox: 1           ← UPDATED AFTER MATCH
```

---

## Constraints & Integrity

### Foreign Keys

All foreign keys enforce **CASCADE ON DELETE**:
- Deleting a `tracks` row → deletes all related `cue_points`, `playlists`, `anlz_data`
- Maintains referential integrity

### Unique Constraints

- `tracks.filepath` — UNIQUE (prevents duplicate entries for same file)

### Data Type Conversions

Metadata extraction uses safe converters in `db.py`:
- `safe_int(value)` — returns None if not numeric
- `safe_float(value)` — returns None if not numeric

### NULL Handling

Most metadata columns allow NULL:
- Tracks without ID3 tags → metadata is NULL
- Graceful handling of incomplete metadata
- Queries use `IS NULL` / `IS NOT NULL` checks

---

## Indexing Strategy

10 indexes created for fast queries:

| Index | Purpose |
|-------|---------|
| `idx_tracks_filename` | Free-text search by filename |
| `idx_tracks_filename_lower` | **Critical** — cross-platform matching |
| `idx_tracks_artist` | Filter/search by artist |
| `idx_tracks_title` | Filter/search by title |
| `idx_tracks_genre` | Filter by genre |
| `idx_tracks_bpm` | Range queries (BPM min/max) |
| `idx_tracks_source_label` | Filter by USB/source |
| `idx_tracks_musical_key` | Filter by key |
| `idx_cue_points_track_id` | Lookup cues for a track |
| `idx_playlists_track_id` | Lookup playlists for a track |

---

## Performance Considerations

### Query Optimization

1. **Use `filename_lower` for matching** — fastest, indexed
2. **BPM range queries** — use indexed numeric column
3. **JOIN with cue_points** — use `GROUP BY` to count efficiently
4. **Limit results** — default 100, configurable

### Common Slow Patterns (Avoid)

```sql
-- BAD: Full table scan
SELECT * FROM tracks WHERE filepath LIKE '%song%'

-- GOOD: Use filename_lower or indexed fields
SELECT * FROM tracks WHERE filename_lower LIKE '%song%'
```

### Scalability

- WAL mode allows concurrent reads during writes
- Indexes keep searches fast even with thousands of tracks
- Foreign key constraints prevent orphaned rows
- Tested with 5000+ tracks

---

## Example Queries

### Get all tracks by artist in Rekordbox

```sql
SELECT
  id, title, artist, bpm, musical_key, source_label,
  COUNT(CASE WHEN cue_type LIKE 'hot_cue_%' THEN 1 END) as hot_cues
FROM tracks t
LEFT JOIN cue_points cp ON t.id = cp.track_id
WHERE artist = ? AND in_rekordbox = 1
GROUP BY t.id
ORDER BY title
```

### Find duplicate filenames across sources

```sql
SELECT filename_lower, COUNT(*) as copies
FROM tracks
GROUP BY filename_lower
HAVING COUNT(*) > 1
ORDER BY filename_lower
```

### BPM distribution by genre

```sql
SELECT
  genre,
  MIN(bpm) as min_bpm,
  MAX(bpm) as max_bpm,
  ROUND(AVG(bpm), 1) as avg_bpm,
  COUNT(*) as track_count
FROM tracks
WHERE genre IS NOT NULL AND bpm > 0
GROUP BY genre
ORDER BY avg_bpm DESC
```

### Rekordbox tracks without cues

```sql
SELECT t.id, t.artist, t.title
FROM tracks t
WHERE t.in_rekordbox = 1
AND t.id NOT IN (SELECT DISTINCT track_id FROM cue_points)
ORDER BY t.artist, t.title
```

---

## Backup & Migration

### Full Backup

SQLite database is a single file:
```bash
# Mac
cp ~/dj_music_index.db ~/backups/dj_music_index_2024-02-21.db

# Windows
copy C:\Users\YourName\dj_music_index.db C:\backups\dj_music_index_2024-02-21.db
```

### Transfer Between Systems

```bash
# 1. On Mac: backup database
cp ~/dj_music_index.db ~/dj_index_backup.db

# 2. Copy to Windows machine
scp ~/dj_index_backup.db user@windows:/Downloads/

# 3. On Windows: use with import-xml
uv run dj-indexer --db ~/Downloads/dj_index_backup.db import-xml collection.xml
```

### Verify Integrity

```bash
# SQLite built-in check
sqlite3 dj_music_index.db "PRAGMA integrity_check;"
```

Should return: `ok`
