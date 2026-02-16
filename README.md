# DJ Music Indexer

A Python CLI utility for DJs to index music files across multiple USB drives and rekordbox collections into a single searchable SQLite database.

## Features

- **Scan USB drives** and extract audio metadata (title, artist, BPM, key, duration, bitrate, etc.)
- **Import rekordbox XML** collections with cue points, hot cues, and playlists
- **Cross-platform support**: scan on Mac, import rekordbox metadata on Windows via filename matching
- **Rich search** with regex, filters (BPM range, genre, artist, key, etc.), and special modes (no-cues, duplicates, playlists)
- **Cue point details** showing exact positions, loop info, and hot cue assignments
- **Collection statistics** with breakdown by source, format, BPM range, and cue preparedness
- **CSV export** of full track index and playlists

## Quick Start

```bash
# Install dependencies
uv add mutagen pyrekordbox

# Scan a USB drive
uv run dj-indexer scan /Volumes/USB1 --label "USB1"

# Import rekordbox XML
uv run dj-indexer import-xml collection.xml

# Search
uv run dj-indexer search "bicep"
uv run dj-indexer search --re --artist "bicep|objekt" --bpm-min 120

# Show cue points
uv run dj-indexer cues "strobe"

# Export
uv run dj-indexer export tracks.csv --playlists
```

## Supported Audio Formats

MP3, WAV, FLAC, AIFF, AAC, M4A, OGG, OPUS, WMA, ALAC

## Database

SQLite database (`dj_music_index.db`) with tables for tracks, cue points, playlists, and analysis metadata.

See `CLAUDE.md` for full specification and schema details.

## Testing

The project includes a comprehensive test suite using pytest. Tests verify:
- Scanner module (audio metadata extraction from 11 formats)
- Rekordbox XML import (tracks, cue points, playlists)
- Cross-platform filename matching
- Error handling and edge cases

### Running Tests

**Setup** (one-time, required on all platforms):
```bash
# Install test dependencies
uv pip install -e ".[test]"
```

**Run tests**:
```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run specific test file
uv run pytest tests/test_rekordbox_xml.py -v

# Run specific test
uv run pytest tests/test_rekordbox_xml.py::TestRekordboxXMLImport::test_rb5_xml_import_tracks -v

# Run with short summary
uv run pytest tests/ -q
```

### Test Files

- `tests/conftest.py` — Shared pytest fixtures (temporary databases, test file paths)
- `tests/test_rekordbox_xml.py` — XML import tests (10 tests covering tracks, metadata, cues, playlists)
- `testfiles/rb5_database.xml` — Rekordbox 5 official test file (6 tracks with cue points)
- `testfiles/rb6_database.xml` — Rekordbox 6 official test file (6 tracks with metadata)

### Test Coverage

Run tests to verify:
1. **Scanner**: Metadata extraction from MP3, WAV, FLAC, M4A, OGG, OPUS, WMA, AIFF, AAC, ALAC
2. **XML Import**:
   - Track count and metadata (artist, BPM, label, comments)
   - Cue point extraction with accurate positions
   - Playlist hierarchy and track assignments
   - Rekordbox 5 and 6 format support
   - Cross-platform filename matching (Mac `/Volumes/` ↔ Windows `C:\`)
3. **Error Handling**: Missing files, malformed XML, unreadable audio
