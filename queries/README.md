# Saved SQL Queries

Reusable SQL query collection for analyzing your music collection by folders, sources, and Rekordbox status.

## Quick Start

### Run a saved query
```bash
uv run dj-indexer query --query-file queries/rekordbox_by_source.sql
```

### Run an inline query
```bash
uv run dj-indexer query "SELECT source_label, COUNT(*) FROM tracks GROUP BY source_label"
```

---

## Available Queries

### 1. `folders_by_source.sql`
**Folder breakdown by source label**

Shows track counts in each folder, organized by USB/source.

```bash
uv run dj-indexer query --query-file queries/folders_by_source.sql
```

**Example output:**
```
source_label | folder                          | track_count | rb_tracks
--------------+---------------------------------+-------------+----------
USB1         | /Volumes/USB1/Music/Techno     | 124         | 120
USB1         | /Volumes/USB1/Music/House     | 89          | 85
USB2-Backup  | /Volumes/USB2/Archive/2023    | 67          | 42
```

---

### 2. `rekordbox_folders.sql`
**Folders containing Rekordbox tracks**

Shows only folders with tracks in Rekordbox, with coverage percentage.

```bash
uv run dj-indexer query --query-file queries/rekordbox_folders.sql
```

**Example output:**
```
folder                                | total_tracks | rb_tracks | percent_rb
--------------------------------------+--------------+-----------+----------
/Volumes/USB1/Music/Techno           | 124          | 124       | 100.0
/Volumes/USB1/Music/House           | 89           | 87        | 97.8
/Volumes/USB2/Archive/2023          | 67           | 42        | 62.7
```

---

### 3. `non_rekordbox_folders.sql`
**Folders with tracks NOT in Rekordbox**

Identifies what still needs to be added to Rekordbox.

```bash
uv run dj-indexer query --query-file queries/non_rekordbox_folders.sql
```

**Example output:**
```
folder                        | not_rb_tracks | source_label
------------------------------+---------------+---------------
/Volumes/USB2/Archive/2022  | 45            | USB2-Backup
/Volumes/USB3/Backup        | 23            | USB3
```

---

### 4. `source_folder_analysis.sql`
**Detailed source and folder analysis**

Comprehensive breakdown: tracks, RB status, BPM average, genres per folder.

```bash
uv run dj-indexer query --query-file queries/source_folder_analysis.sql
```

**Example output:**
```
source_label | folder                     | total_count | rb_count | non_rb_count | avg_bpm | genre_count
--------------+----------------------------+-------------+----------+---------------+---------+-----------
USB1         | /Volumes/USB1/Music/Techno | 124         | 120      | 4            | 127.5   | 3
USB1         | /Volumes/USB1/Music/House | 89          | 85       | 4            | 124.2   | 2
USB2-Backup  | /Volumes/USB2/Archive     | 67          | 42       | 25           | 115.8   | 8
```

---

### 5. `rekordbox_by_source.sql`
**Rekordbox tracks grouped by source**

Shows Rekordbox coverage by USB/source.

```bash
uv run dj-indexer query --query-file queries/rekordbox_by_source.sql
```

**Example output:**
```
source_label | total_tracks | rb_tracks | non_rb_tracks | percent_rb
--------------+--------------+-----------+---------------+----------
USB1         | 213          | 205       | 8             | 96.2
USB2-Backup  | 112          | 67        | 45            | 59.8
USB3         | 45           | 12        | 33            | 26.7
```

---

### 6. `folder_rekordbox_coverage.sql`
**Rekordbox coverage by folder**

Shows what percentage of each folder is prepared. Great for identifying gaps.

```bash
uv run dj-indexer query --query-file queries/folder_rekordbox_coverage.sql
```

**Example output:**
```
folder                           | total_tracks | rb_tracks | percent_prepared
----------------------------------+--------------+-----------+-----------------
/Volumes/USB3/Backup            | 45           | 8         | 17.8
/Volumes/USB2/Archive/2022      | 55           | 35        | 63.6
/Volumes/USB1/Music/House       | 89           | 87        | 97.8
/Volumes/USB1/Music/Techno      | 124          | 124       | 100.0
```

---

### 7. `genre_by_source_folder.sql`
**Genre distribution by source and folder**

Shows what genres exist in each USB/folder combination.

```bash
uv run dj-indexer query --query-file queries/genre_by_source_folder.sql
```

**Example output:**
```
source_label | folder                     | genre      | track_count | avg_bpm | rb_count
--------------+----------------------------+------------+-------------+---------+----------
USB1         | /Volumes/USB1/Music/House | Deep House | 34          | 120.5   | 33
USB1         | /Volumes/USB1/Music/House | Tech House | 28          | 126.2   | 27
USB1         | /Volumes/USB1/Music/Techno| Dark       | 45          | 128.1   | 45
USB1         | /Volumes/USB1/Music/Techno| Minimal    | 32          | 125.0   | 32
```

---

## Inline Command Examples

### By Folder and Rekordbox Status

**Count tracks in each folder:**
```bash
uv run dj-indexer query "SELECT DIRNAME(filepath), COUNT(*) FROM tracks GROUP BY DIRNAME(filepath) ORDER BY COUNT(*) DESC"
```

**Folders with more than 50 Rekordbox tracks:**
```bash
uv run dj-indexer query "SELECT DIRNAME(filepath), COUNT(*) as rb_count FROM tracks WHERE in_rekordbox=1 GROUP BY DIRNAME(filepath) HAVING COUNT(*) > 50 ORDER BY rb_count DESC"
```

**Get all folders on USB1 only:**
```bash
uv run dj-indexer query "SELECT DISTINCT DIRNAME(filepath) FROM tracks WHERE source_label LIKE '%USB1%' ORDER BY DIRNAME(filepath)"
```

---

### By Source Filter

**Count tracks on each USB drive:**
```bash
uv run dj-indexer query "SELECT source_label, COUNT(*) as count FROM tracks GROUP BY source_label ORDER BY count DESC"
```

**USB drives with Rekordbox coverage:**
```bash
uv run dj-indexer query "SELECT source_label, COUNT(CASE WHEN in_rekordbox=1 THEN 1 END) as rb_count, COUNT(*) as total FROM tracks GROUP BY source_label ORDER BY rb_count DESC"
```

**Get all folders from USB2 with non-Rekordbox tracks:**
```bash
uv run dj-indexer query "SELECT DISTINCT DIRNAME(filepath) FROM tracks WHERE source_label LIKE '%USB2%' AND in_rekordbox=0"
```

---

### By Rekordbox Flag

**Folders with 100% Rekordbox coverage:**
```bash
uv run dj-indexer query "SELECT DIRNAME(filepath), COUNT(*) FROM tracks WHERE in_rekordbox=1 GROUP BY DIRNAME(filepath) HAVING COUNT(*) = (SELECT COUNT(*) FROM tracks t2 WHERE DIRNAME(t2.filepath) = DIRNAME(tracks.filepath))"
```

**Folders with zero Rekordbox tracks:**
```bash
uv run dj-indexer query "SELECT DIRNAME(filepath), COUNT(*) FROM tracks WHERE in_rekordbox=0 GROUP BY DIRNAME(filepath) HAVING NOT EXISTS (SELECT 1 FROM tracks t2 WHERE DIRNAME(t2.filepath) = DIRNAME(tracks.filepath) AND t2.in_rekordbox=1) ORDER BY COUNT(*) DESC"
```

**Show preparation status by folder:**
```bash
uv run dj-indexer query "SELECT DIRNAME(filepath), COUNT(*) as total, SUM(CASE WHEN in_rekordbox=1 THEN 1 ELSE 0 END) as prepared, ROUND(100.0*SUM(CASE WHEN in_rekordbox=1 THEN 1 ELSE 0 END)/COUNT(*), 1) as percent FROM tracks GROUP BY DIRNAME(filepath) ORDER BY percent ASC"
```

---

### Combined: Folder + Source + Rekordbox

**Rekordbox preparation status by USB and folder:**
```bash
uv run dj-indexer query "SELECT source_label, DIRNAME(filepath), COUNT(*) as total, SUM(CASE WHEN in_rekordbox=1 THEN 1 ELSE 0 END) as in_rb, ROUND(100.0*SUM(CASE WHEN in_rekordbox=1 THEN 1 ELSE 0 END)/COUNT(*), 1) as percent_prep FROM tracks GROUP BY source_label, DIRNAME(filepath) ORDER BY source_label, percent_prep"
```

**Find folders on USB1 that need work (less than 80% Rekordbox coverage):**
```bash
uv run dj-indexer query "SELECT DIRNAME(filepath), COUNT(*) as total, SUM(CASE WHEN in_rekordbox=1 THEN 1 ELSE 0 END) as in_rb FROM tracks WHERE source_label='USB1' GROUP BY DIRNAME(filepath) HAVING CAST(SUM(CASE WHEN in_rekordbox=1 THEN 1 ELSE 0 END) AS FLOAT)/COUNT(*) < 0.8 ORDER BY total DESC"
```

**Top 10 folders by track count, showing Rekordbox status and source:**
```bash
uv run dj-indexer query "SELECT source_label, DIRNAME(filepath), COUNT(*) as track_count, SUM(CASE WHEN in_rekordbox=1 THEN 1 ELSE 0 END) as rb_count FROM tracks GROUP BY source_label, DIRNAME(filepath) ORDER BY track_count DESC LIMIT 10"
```

---

## Adding New Queries

To add your own query:

1. Create a new `.sql` file in the `queries/` directory
2. Add a comment describing the query purpose
3. Add usage instructions with the query example
4. Write the SQL statement

**Template:**
```sql
-- Brief description of what this query does
-- Usage: dj-indexer query --query-file queries/my_query.sql

SELECT
    column1,
    column2,
    COUNT(*) as count
FROM tracks
GROUP BY column1, column2
ORDER BY count DESC;
```

---

## Common Patterns

### Filter by source label
```sql
WHERE source_label = 'USB1'
WHERE source_label LIKE '%USB%'
WHERE source_label IN ('USB1', 'USB2-Backup')
```

### Filter by Rekordbox status
```sql
WHERE in_rekordbox = 1          -- Only Rekordbox tracks
WHERE in_rekordbox = 0          -- Only non-Rekordbox tracks
WHERE in_rekordbox IS NOT NULL  -- Has been checked
```

### Extract folder from filepath
```sql
DIRNAME(filepath)               -- Get parent directory
SUBSTR(DIRNAME(filepath), 1, INSTR(DIRNAME(filepath)||'/', '/')-1)  -- Get root folder
```

### Calculate percentages
```sql
ROUND(100.0 * SUM(CASE WHEN condition THEN 1 ELSE 0 END) / COUNT(*), 1)
```

### Group and count combinations
```sql
GROUP BY source_label, DIRNAME(filepath)
GROUP BY source_label, genre, DIRNAME(filepath)
```

---

## Helper Functions

Available in all queries:

**DIRNAME(filepath)** — Extract directory from full path
```sql
SELECT DIRNAME('/Volumes/USB1/Music/Techno/track.mp3')
-- Returns: /Volumes/USB1/Music/Techno
```

**REGEXP(pattern, column)** — Regex pattern matching (case-insensitive)
```sql
SELECT * FROM tracks WHERE REGEXP('bicep|objekt', artist)
```

---

## Performance Tips

1. **Use indexes** — Queries on `source_label`, `in_rekordbox`, `DIRNAME(filepath)` are fast
2. **Group early** — Use `GROUP BY` to reduce rows before sorting
3. **Limit results** — Add `LIMIT 50` to large result sets
4. **Use WHERE before GROUP BY** — Filter before grouping when possible

---

## Maintenance

To keep this collection organized:
- Document your query's purpose in the header comment
- Include usage example showing how to run it
- Add to this README with description and example output
- Prefix similar queries with a category (e.g., `folder_`, `source_`, `rekordbox_`)
