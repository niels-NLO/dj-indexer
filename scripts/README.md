# File Management Scripts

Scripts for copying/moving files from DJ Indexer CSV exports. Perfect for batch operations on search and query results.

## Quick Start

### Windows (PowerShell)

```powershell
.\copy_files.ps1 -CsvFile results.csv -DestinationPath "D:\Staging"
```

### Mac/Linux (Bash)

```bash
chmod +x copy_files.sh
./copy_files.sh -c results.csv -d ~/Music/Staging
```

---

## Workflow

### 1. Export from DJ Indexer

```bash
# Search and export results to CSV
uv run dj-indexer search --genre "Techno" --export-csv results.csv

# Query and export results to CSV
uv run dj-indexer query --query-file queries/preparation_status.sql --export-csv prep_status.csv

# Export with path conversion (Windows)
uv run dj-indexer search --bpm-min 120 --export-csv results.csv --path-conversion mac-to-windows --volume-map USB1=E USB2=F
```

### 2. Use Script to Copy/Move Files

```bash
# Copy all files to staging directory
./copy_files.sh -c results.csv -d ~/Music/Staging

# Move files (organizes with subfolder structure)
./copy_files.sh -c results.csv -d ~/Music/Archive -m move --subfolder

# Skip files that already exist
./copy_files.sh -c results.csv -d ~/Music/Backup --skip-exists
```

---

## Windows PowerShell Script

### Usage

```powershell
.\copy_files.ps1 -CsvFile <file> -DestinationPath <path> [OPTIONS]
```

### Required Parameters

- **`-CsvFile`** — Path to CSV file (must have 'filepath' column)
- **`-DestinationPath`** — Where to copy/move files

### Optional Parameters

- **`-FilepathColumn`** — Name of filepath column (default: 'filepath')
- **`-Mode`** — 'copy' (default) or 'move'
- **`-CreateSubfolders`** — Recreate source folder structure in destination
- **`-SkipIfExists`** — Skip files that already exist
- **`-Verbose`** — Show detailed progress

### Examples

**Copy files to staging directory:**
```powershell
.\copy_files.ps1 -CsvFile techno_tracks.csv -DestinationPath "D:\Staging"
```

**Move files with folder structure:**
```powershell
.\copy_files.ps1 -CsvFile results.csv -DestinationPath "E:\Archive" -Mode move -CreateSubfolders
```

**Copy, skip existing files:**
```powershell
.\copy_files.ps1 -CsvFile library.csv -DestinationPath "F:\Backup" -SkipIfExists
```

**Verbose output:**
```powershell
.\copy_files.ps1 -CsvFile results.csv -DestinationPath "D:\Analysis" -Verbose
```

### Output

```
Loaded 145 records from CSV
[1] Copied: Track_1.mp3
[2] Copied: Track_2.flac
[3] Skipped (exists): Track_3.wav
...
========================================
Operation Complete
========================================
Total processed:  145
Successful:       143
Failed:           0
Skipped:          2
Not found:        0
========================================
```

---

## Mac/Linux Bash Script

### Usage

```bash
./copy_files.sh -c <csv_file> -d <destination> [OPTIONS]
```

### Required Parameters

- **`-c, --csv`** — Path to CSV file
- **`-d, --destination`** — Destination directory

### Optional Parameters

- **`-m, --mode`** — 'copy' (default) or 'move'
- **`--column`** — Filepath column name (default: 'filepath')
- **`--subfolder`** — Recreate source folder structure
- **`--skip-exists`** — Skip files that already exist
- **`-v, --verbose`** — Show detailed output
- **`-h, --help`** — Show help message

### Examples

**Copy files to staging directory:**
```bash
./copy_files.sh -c techno_tracks.csv -d ~/Music/Staging
```

**Move files with folder structure:**
```bash
./copy_files.sh -c results.csv -d ~/Music/Archive -m move --subfolder
```

**Copy, skip existing files:**
```bash
./copy_files.sh -c library.csv -d ~/Music/Backup --skip-exists
```

**Verbose output:**
```bash
./copy_files.sh -c results.csv -d ~/DJ/Prep -v
```

### Output

```
Creating destination directory: ~/Music/Staging
[1] Copied: Track_1.mp3
[2] Copied: Track_2.flac
[3] Skipped (exists): Track_3.wav
...
========================================
Operation Complete
========================================
Total processed:  145
Successful:       143
Failed:           0
Skipped:          2
Not found:        0
========================================
```

---

## CSV Path Conversion

### Export with Path Conversion

When exporting search/query results, convert paths between Mac and Windows:

**Mac → Windows:**
```bash
uv run dj-indexer search --genre "Techno" \
  --export-csv results.csv \
  --path-conversion mac-to-windows \
  --volume-map USB1=E USB2=F Archive=G
```

**Windows → Mac:**
```bash
uv run dj-indexer search --genre "Techno" \
  --export-csv results.csv \
  --path-conversion windows-to-mac \
  --volume-map E=USB1 F=USB2 G=Archive
```

### Volume Mapping Format

Specify drive-to-volume mappings:

```
--volume-map USB1=E USB2=F BackupDrive=G
```

Maps:
- `/Volumes/USB1/file.mp3` ↔ `E:\file.mp3`
- `/Volumes/USB2/file.mp3` ↔ `F:\file.mp3`
- `/Volumes/BackupDrive/file.mp3` ↔ `G:\file.mp3`

### Conversion Examples

**Mac path to Windows:**
```
/Volumes/USB1/Music/Techno/track.mp3 → E:\Music\Techno\track.mp3
```

**Windows path to Mac:**
```
F:\Archive\2024\file.mp3 → /Volumes/USB2/Archive/2024/file.mp3
```

---

## CSV Export Options

### Select Specific Columns

Export only the columns you need:

```bash
# Search results with selected columns
uv run dj-indexer search --genre "House" \
  --export-csv results.csv \
  --columns artist title bpm filepath

# Query results with selected columns
uv run dj-indexer query --query-file queries/preparation_status.sql \
  --export-csv prep.csv \
  --columns source_label folder total_tracks in_rekordbox percent_ready
```

### Available Columns (from search)

- `artist`
- `title`
- `filename`
- `filepath`
- `bpm`
- `musical_key`
- `source_label`
- `in_rekordbox`
- `genre`
- `duration_sec`
- `file_format`

---

## Common Use Cases

### Use Case 1: DJ Set Preparation

Find all Techno tracks in Rekordbox, copy to laptop for mixing:

```bash
# Export Techno tracks in Rekordbox
uv run dj-indexer search --genre "Techno" --in-rekordbox \
  --export-csv techno_ready.csv \
  --columns artist title bpm filepath

# Copy to laptop staging area
.\copy_files.ps1 -CsvFile techno_ready.csv -DestinationPath "D:\DJ\Tonight" -CreateSubfolders
```

### Use Case 2: Archive Management

Move all 2024 records to archive drive:

```bash
# Find tracks from 2024 folders
uv run dj-indexer query --query-file queries/folders_by_source.sql \
  --export-csv archive_2024.csv \
  --path-conversion windows-to-mac

# Move to archive (Mac)
./copy_files.sh -c archive_2024.csv -d ~/Archive/2024 -m move --subfolder
```

### Use Case 3: Backup Unindexed Music

Find non-Rekordbox tracks on USB2, backup them:

```bash
# Export non-RB tracks from USB2
uv run dj-indexer search --not-in-rekordbox --source "USB2" \
  --export-csv usb2_unindexed.csv

# Copy to backup location
./copy_files.sh -c usb2_unindexed.csv -d ~/Backups/USB2_Unindexed --skip-exists
```

### Use Case 4: Cross-Platform Workflow

Scan on Mac, move files on Windows:

```bash
# On Mac: Search and convert paths to Windows
uv run dj-indexer search --genre "Minimal" \
  --export-csv minimal_win.csv \
  --path-conversion mac-to-windows \
  --volume-map USB1=E USB2=F

# Transfer CSV to Windows

# On Windows: Copy files with converted paths
.\copy_files.ps1 -CsvFile minimal_win.csv -DestinationPath "D:\Analysis" -CreateSubfolders
```

---

## Troubleshooting

### File Not Found

**Problem:** Script reports files not found

**Solutions:**
- Check CSV filepath column matches actual file locations
- Verify volume names in path conversion mapping
- Ensure source files haven't been moved/deleted

### Permission Denied

**Problem:** Script can't copy/move files (Mac/Linux)

**Solutions:**
```bash
# Check file permissions
ls -l /path/to/file

# Adjust permissions if needed
chmod u+rw /path/to/file
```

### CSV Column Not Found

**Problem:** Script can't find filepath column

**Solutions:**
- Check CSV header matches column name (case-sensitive)
- Use `--column` parameter to specify custom column name
- Export CSV from dj-indexer with `--columns filepath ...`

### Destination Permission Issues (Windows)

**Problem:** PowerShell can't write to destination

**Solutions:**
- Run PowerShell as Administrator
- Check destination folder permissions
- Ensure destination disk has free space

---

## Advanced: Custom Bash Script

For more control, write your own script using the CSV:

```bash
#!/bin/bash

# Read CSV and copy files with custom logic
while IFS=',' read -r artist title filepath bpm; do
    if [[ ! -f "$filepath" ]]; then
        echo "Not found: $filepath"
        continue
    fi

    # Custom destination based on BPM
    if (( $(echo "$bpm > 125" | bc -l) )); then
        dest_dir="~/Music/HighEnergy"
    else
        dest_dir="~/Music/Chill"
    fi

    mkdir -p "$dest_dir"
    cp "$filepath" "$dest_dir/"
    echo "Copied: $title"
done < results.csv
```

---

## Tips

1. **Always backup first** — Use `--skip-exists` to preserve existing files
2. **Test with small export** — Export 10 tracks before batch operations
3. **Use subfolders** — `--subfolder` helps organize archived music
4. **Check paths** — Verify CSV paths are correct before running script
5. **Monitor progress** — Watch for errors in script output
6. **Cross-platform** — Use path conversion when moving between Mac/Windows
