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
