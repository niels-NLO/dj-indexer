"""Tests for scanner module - audio file discovery and metadata extraction.

TODO: Add format coverage tests for all 11 supported audio formats:
- Current coverage: FLAC (reliable minimal file creation)
- Need to add: MP3, WAV, AIFF, AAC, M4A, OGG, OPUS, WMA, ALAC

These formats require real audio files (mutagen's minimal file creation is unreliable
for most formats). To add format testing:

1. Create testfiles/audio_samples/ directory with minimal valid files for each format
2. Can download free sample audio or use:
   - ffmpeg to convert existing test files to each format
   - Free audio sample libraries
3. Create a fixture that loads these pre-made files
4. Add format-specific test cases to TestScannerFormats class

See conftest.py test_audio_dir fixture for detailed TODO.
"""

import pytest

from dj_indexer import scanner


class TestScannerBasic:
    """Test basic scanner functionality."""

    def test_scanner_counts_files(self, test_db, test_audio_dir):
        """Test that scanner finds and imports all audio files."""
        scanner.scan_directory(test_db, test_audio_dir, "TestLibrary")

        # Query track count (fixture creates 3 FLAC test files)
        cursor = test_db.execute("SELECT COUNT(*) FROM tracks")
        count = cursor.fetchone()[0]
        assert count == 3, f"Expected 3 tracks, got {count}"

    def test_scanner_imports_metadata(self, test_db, test_audio_dir):
        """Test that scanner imports files and stores them in database."""
        scanner.scan_directory(test_db, test_audio_dir, "TestLibrary")

        # Verify all 3 test files were imported
        cursor = test_db.execute("SELECT COUNT(*) FROM tracks")
        count = cursor.fetchone()[0]
        assert count == 3, f"Expected 3 tracks, got {count}"

        # Verify each track has basic fields populated
        cursor = test_db.execute(
            "SELECT filename, filepath, source_label FROM tracks ORDER BY filename"
        )
        rows = cursor.fetchall()
        assert len(rows) == 3
        for filename, filepath, source_label in rows:
            assert filename is not None and filename.endswith(".flac")
            assert filepath is not None
            assert source_label == "TestLibrary"

    def test_scanner_imports_metadata_fields(self, test_db, test_audio_dir):
        """Test that scanner populates all expected database fields."""
        scanner.scan_directory(test_db, test_audio_dir, "TestLibrary")

        # Verify all expected columns exist and have data
        cursor = test_db.execute(
            """
            SELECT filename, source_label, file_format, duration_sec
            FROM tracks LIMIT 1
            """
        )
        row = cursor.fetchone()
        assert row is not None
        filename, source_label, file_format, duration_sec = row
        assert filename is not None
        assert source_label == "TestLibrary"
        assert file_format == ".flac"

    def test_scanner_stores_source_label(self, test_db, test_audio_dir):
        """Test that source label is stored correctly."""
        scanner.scan_directory(test_db, test_audio_dir, "USB1-Main")

        cursor = test_db.execute(
            "SELECT DISTINCT source_label FROM tracks"
        )
        rows = cursor.fetchall()
        assert len(rows) == 1, f"Expected 1 source label, got {len(rows)}"
        assert rows[0][0] == "USB1-Main", f"Expected 'USB1-Main', got '{rows[0][0]}'"

    def test_scanner_stores_filename_lower(self, test_db, test_audio_dir):
        """Test that filename_lower is stored for cross-platform matching."""
        scanner.scan_directory(test_db, test_audio_dir, "TestLibrary")

        cursor = test_db.execute(
            "SELECT filename, filename_lower FROM tracks LIMIT 1"
        )
        row = cursor.fetchone()
        assert row is not None
        filename, filename_lower = row
        assert filename_lower == filename.lower(), (
            f"Expected filename_lower to match {filename.lower()}, got '{filename_lower}'"
        )

    def test_scanner_stores_file_format(self, test_db, test_audio_dir):
        """Test that file format is stored correctly."""
        scanner.scan_directory(test_db, test_audio_dir, "TestLibrary")

        cursor = test_db.execute(
            "SELECT DISTINCT file_format FROM tracks ORDER BY file_format"
        )
        formats = [row[0] for row in cursor.fetchall()]

        # Fixture creates only FLAC files
        assert ".flac" in formats, f"Expected .flac format, got {formats}"

    def test_scanner_stores_filepath(self, test_db, test_audio_dir):
        """Test that full filepath is stored."""
        scanner.scan_directory(test_db, test_audio_dir, "TestLibrary")

        cursor = test_db.execute(
            "SELECT filepath FROM tracks LIMIT 1"
        )
        row = cursor.fetchone()
        assert row is not None
        filepath = row[0]
        assert str(test_audio_dir) in filepath, (
            f"Expected filepath to contain {test_audio_dir}, got {filepath}"
        )
        assert filepath.endswith(".flac"), (
            f"Expected filepath to end with '.flac', got {filepath}"
        )


class TestScannerFormats:
    """Test scanner with audio formats."""

    def test_scanner_flac_format(self, test_db, test_audio_dir):
        """Test FLAC file scanning (supported format)."""
        scanner.scan_directory(test_db, test_audio_dir, "TestLibrary")

        cursor = test_db.execute(
            "SELECT COUNT(*) FROM tracks WHERE file_format = '.flac'"
        )
        count = cursor.fetchone()[0]
        assert count == 3, f"Expected 3 FLAC files, got {count}"

        # Verify all files are stored with proper filenames
        cursor = test_db.execute(
            "SELECT filename FROM tracks WHERE file_format = '.flac' ORDER BY filename"
        )
        filenames = [row[0] for row in cursor.fetchall()]
        assert all(f.endswith(".flac") for f in filenames), f"Expected all FLAC files, got {filenames}"
        assert len(filenames) == 3


class TestScannerErrorHandling:
    """Test scanner error handling."""

    def test_scanner_nonexistent_directory(self, test_db):
        """Test scanner with nonexistent directory."""
        with pytest.raises(FileNotFoundError):
            scanner.scan_directory(test_db, "/nonexistent/path", "TestLibrary")

    def test_scanner_empty_directory(self, test_db, tmp_path):
        """Test scanner with empty directory."""
        scanner.scan_directory(test_db, tmp_path, "TestLibrary")

        cursor = test_db.execute("SELECT COUNT(*) FROM tracks")
        count = cursor.fetchone()[0]
        assert count == 0, f"Expected 0 tracks for empty directory, got {count}"


class TestScannerUpsert:
    """Test scanner upsert behavior."""

    def test_scanner_rescan_updates_metadata(self, test_db, test_audio_dir):
        """Test that rescanning updates track metadata without creating duplicates."""
        # First scan
        scanner.scan_directory(test_db, test_audio_dir, "TestLibrary")

        cursor = test_db.execute("SELECT COUNT(*) FROM tracks")
        initial_count = cursor.fetchone()[0]
        assert initial_count == 3, f"Expected 3 tracks after first scan, got {initial_count}"

        # Rescan same directory
        scanner.scan_directory(test_db, test_audio_dir, "TestLibrary")

        cursor = test_db.execute("SELECT COUNT(*) FROM tracks")
        final_count = cursor.fetchone()[0]

        # Should not create duplicates - upsert should replace
        assert final_count == initial_count, (
            f"Rescan created duplicates: {initial_count} → {final_count}"
        )

    def test_scanner_preserves_rekordbox_flag(self, test_db, test_audio_dir):
        """Test that rescanning preserves in_rekordbox flag."""
        # First scan
        scanner.scan_directory(test_db, test_audio_dir, "TestLibrary")

        # Get the first track filename
        cursor = test_db.execute("SELECT filename FROM tracks LIMIT 1")
        row = cursor.fetchone()
        assert row is not None
        test_filename = row[0]

        # Manually set in_rekordbox for that track
        test_db.execute(
            f"UPDATE tracks SET in_rekordbox = 1 WHERE filename = '{test_filename}'"
        )
        test_db.commit()

        # Verify it was set
        cursor = test_db.execute(
            f"SELECT in_rekordbox FROM tracks WHERE filename = '{test_filename}'"
        )
        assert cursor.fetchone()[0] == 1

        # Rescan
        scanner.scan_directory(test_db, test_audio_dir, "TestLibrary")

        # Check that in_rekordbox is still 1
        cursor = test_db.execute(
            f"SELECT in_rekordbox FROM tracks WHERE filename = '{test_filename}'"
        )
        row = cursor.fetchone()
        assert row is not None, f"Track '{test_filename}' not found after rescan"
        assert row[0] == 1, "in_rekordbox flag was not preserved during rescan"
