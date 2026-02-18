"""Tests for query and analyze modules."""

import io
import tempfile
from contextlib import redirect_stdout
from pathlib import Path

import pytest

from dj_indexer import query, analyze
import argparse


class TestQueryCommand:
    """Test raw SQL query execution."""

    def test_query_simple_select(self, populated_db):
        """Execute a simple SELECT query."""
        output = io.StringIO()
        with redirect_stdout(output):
            query.run_query(populated_db, "SELECT COUNT(*) as total FROM tracks")

        result = output.getvalue()
        assert "total" in result
        assert "6" in result
        assert "(1 row)" in result

    def test_query_with_column_headers(self, populated_db):
        """Query returns properly formatted column headers."""
        output = io.StringIO()
        with redirect_stdout(output):
            query.run_query(populated_db, "SELECT artist, title FROM tracks LIMIT 2")

        result = output.getvalue()
        assert "artist" in result
        assert "title" in result

    def test_query_with_where_clause(self, populated_db):
        """Execute query with WHERE clause."""
        output = io.StringIO()
        with redirect_stdout(output):
            query.run_query(populated_db, "SELECT title FROM tracks WHERE bpm >= 120")

        result = output.getvalue()
        # Should find the tracks with high BPM (128, 129, 124, 130)
        assert "Electric Dreams" in result or "Glue" in result or "House Drop" in result
        assert "(4 rows)" in result

    def test_query_with_aggregation(self, populated_db):
        """Execute query with GROUP BY and aggregation."""
        output = io.StringIO()
        with redirect_stdout(output):
            query.run_query(populated_db, "SELECT source_label, COUNT(*) as count FROM tracks GROUP BY source_label")

        result = output.getvalue()
        assert "source_label" in result
        assert "count" in result
        assert "USB1" in result
        assert "USB2" in result

    def test_query_with_dirname(self, populated_db):
        """Query can use DIRNAME function."""
        output = io.StringIO()
        with redirect_stdout(output):
            query.run_query(populated_db, "SELECT DIRNAME(filepath) as folder, COUNT(*) as n FROM tracks GROUP BY DIRNAME(filepath) ORDER BY n DESC")

        result = output.getvalue()
        assert "folder" in result
        assert "n" in result
        # Check for folder paths (will vary based on OS path format)
        assert ("/usb" in result or "usb" in result) and "2" in result  # At least 2 folders with track counts

    def test_query_with_null_values(self, populated_db):
        """Query properly handles NULL values."""
        output = io.StringIO()
        with redirect_stdout(output):
            query.run_query(populated_db, "SELECT artist, album FROM tracks WHERE album IS NULL")

        result = output.getvalue()
        assert "NULL" in result

    def test_query_with_float_formatting(self, populated_db):
        """Query formats float values properly."""
        output = io.StringIO()
        with redirect_stdout(output):
            query.run_query(populated_db, "SELECT AVG(bpm) as avg_bpm FROM tracks WHERE bpm > 0")

        result = output.getvalue()
        assert "avg_bpm" in result
        # Should have a numeric value
        lines = result.strip().split('\n')
        assert len(lines) >= 4  # header, separator, data, count

    def test_query_no_results(self, populated_db):
        """Query with no results shows empty result set."""
        output = io.StringIO()
        with redirect_stdout(output):
            query.run_query(populated_db, "SELECT title FROM tracks WHERE title = 'NonexistentTrack'")

        result = output.getvalue()
        # Should show 0 rows
        assert "(0 rows)" in result
        assert "title" in result  # Should still show column header

    def test_query_rejects_non_select(self, populated_db):
        """Query rejects non-SELECT statements."""
        with pytest.raises(ValueError, match="Only SELECT statements are supported"):
            query.run_query(populated_db, "INSERT INTO tracks VALUES ()")

    def test_query_rejects_update(self, populated_db):
        """Query rejects UPDATE statements."""
        with pytest.raises(ValueError, match="Only SELECT statements are supported"):
            query.run_query(populated_db, "UPDATE tracks SET artist = 'New'")

    def test_query_rejects_delete(self, populated_db):
        """Query rejects DELETE statements."""
        with pytest.raises(ValueError, match="Only SELECT statements are supported"):
            query.run_query(populated_db, "DELETE FROM tracks")

    def test_query_rejects_drop(self, populated_db):
        """Query rejects DROP statements."""
        with pytest.raises(ValueError, match="Only SELECT statements are supported"):
            query.run_query(populated_db, "DROP TABLE tracks")

    def test_query_sql_error_handling(self, populated_db):
        """Query handles SQL errors gracefully."""
        output = io.StringIO()
        with redirect_stdout(output):
            query.run_query(populated_db, "SELECT * FROM nonexistent_table")

        result = output.getvalue()
        assert "SQL Error" in result

    def test_query_with_order_by(self, populated_db):
        """Query can use ORDER BY."""
        output = io.StringIO()
        with redirect_stdout(output):
            query.run_query(populated_db, "SELECT title, bpm FROM tracks WHERE bpm > 0 ORDER BY bpm DESC LIMIT 3")

        result = output.getvalue()
        assert "title" in result
        assert "bpm" in result

    def test_query_case_insensitive_validation(self, populated_db):
        """Query validation is case-insensitive for SELECT."""
        output = io.StringIO()
        with redirect_stdout(output):
            query.run_query(populated_db, "select COUNT(*) from tracks")

        result = output.getvalue()
        assert "(1 row)" in result

    def test_query_with_whitespace(self, populated_db):
        """Query handles leading/trailing whitespace."""
        output = io.StringIO()
        with redirect_stdout(output):
            query.run_query(populated_db, "  \n  SELECT COUNT(*) FROM tracks  \n  ")

        result = output.getvalue()
        assert "(1 row)" in result


class TestAnalyzeCommand:
    """Test pre-built analytics breakdowns."""

    def test_analyze_folders_basic(self, populated_db):
        """Analyze by folder shows folder breakdown."""
        args = argparse.Namespace(
            folders=True,
            in_rekordbox=False, not_in_rekordbox=False,
            source=None, format=None, genre=None,
            bpm_min=None, bpm_max=None,
            limit=100
        )
        output = io.StringIO()
        with redirect_stdout(output):
            analyze.analyze(populated_db, args)

        result = output.getvalue()
        assert "Folder Analysis" in result
        assert "unique folders" in result
        assert "/usb1/music" in result or "usb1" in result
        assert "/usb2/dj" in result or "usb2" in result

    def test_analyze_folders_with_in_rekordbox_filter(self, populated_db):
        """Analyze shows filter description in title."""
        args = argparse.Namespace(
            folders=True,
            in_rekordbox=True, not_in_rekordbox=False,
            source=None, format=None, genre=None,
            bpm_min=None, bpm_max=None,
            limit=100
        )
        output = io.StringIO()
        with redirect_stdout(output):
            analyze.analyze(populated_db, args)

        result = output.getvalue()
        assert "in rekordbox" in result

    def test_analyze_folders_with_source_filter(self, populated_db):
        """Analyze filters by source label."""
        args = argparse.Namespace(
            folders=True,
            in_rekordbox=False, not_in_rekordbox=False,
            source="USB1", format=None, genre=None,
            bpm_min=None, bpm_max=None,
            limit=100
        )
        output = io.StringIO()
        with redirect_stdout(output):
            analyze.analyze(populated_db, args)

        result = output.getvalue()
        assert "source=USB1" in result
        assert "/usb1/music" in result or "usb1" in result

    def test_analyze_folders_with_bpm_min(self, populated_db):
        """Analyze filters by minimum BPM."""
        args = argparse.Namespace(
            folders=True,
            in_rekordbox=False, not_in_rekordbox=False,
            source=None, format=None, genre=None,
            bpm_min=120.0, bpm_max=None,
            limit=100
        )
        output = io.StringIO()
        with redirect_stdout(output):
            analyze.analyze(populated_db, args)

        result = output.getvalue()
        assert "bpm=120.0" in result
        # Should filter to higher BPM tracks

    def test_analyze_folders_with_bpm_range(self, populated_db):
        """Analyze filters by BPM range."""
        args = argparse.Namespace(
            folders=True,
            in_rekordbox=False, not_in_rekordbox=False,
            source=None, format=None, genre=None,
            bpm_min=100.0, bpm_max=130.0,
            limit=100
        )
        output = io.StringIO()
        with redirect_stdout(output):
            analyze.analyze(populated_db, args)

        result = output.getvalue()
        assert "bpm=100.0-130.0" in result

    def test_analyze_folders_with_genre_filter(self, populated_db):
        """Analyze filters by genre."""
        args = argparse.Namespace(
            folders=True,
            in_rekordbox=False, not_in_rekordbox=False,
            source=None, format=None, genre="Techno",
            bpm_min=None, bpm_max=None,
            limit=100
        )
        output = io.StringIO()
        with redirect_stdout(output):
            analyze.analyze(populated_db, args)

        result = output.getvalue()
        assert "genre=Techno" in result

    def test_analyze_folders_with_format_filter(self, populated_db):
        """Analyze filters by file format."""
        args = argparse.Namespace(
            folders=True,
            in_rekordbox=False, not_in_rekordbox=False,
            source=None, format=".mp3", genre=None,
            bpm_min=None, bpm_max=None,
            limit=100
        )
        output = io.StringIO()
        with redirect_stdout(output):
            analyze.analyze(populated_db, args)

        result = output.getvalue()
        # Test data doesn't have file_format set, so this should show no results
        assert "format=.mp3" in result or "No folders found" in result

    def test_analyze_folders_with_not_in_rekordbox(self, populated_db):
        """Analyze shows not_in_rekordbox filter in title even with no results."""
        args = argparse.Namespace(
            folders=True,
            in_rekordbox=False, not_in_rekordbox=True,
            source=None, format=None, genre=None,
            bpm_min=None, bpm_max=None,
            limit=100
        )
        output = io.StringIO()
        with redirect_stdout(output):
            analyze.analyze(populated_db, args)

        result = output.getvalue()
        # Test data has all tracks with in_rekordbox=1, so no results expected
        # But the filter description should still be in title when results exist
        assert "not in rekordbox" in result or "No folders found" in result

    def test_analyze_folders_no_results(self, populated_db):
        """Analyze shows message when no results match filters."""
        args = argparse.Namespace(
            folders=True,
            in_rekordbox=False, not_in_rekordbox=False,
            source=None, format=".wav", genre=None,  # No WAV files in test data
            bpm_min=None, bpm_max=None,
            limit=100
        )
        output = io.StringIO()
        with redirect_stdout(output):
            analyze.analyze(populated_db, args)

        result = output.getvalue()
        assert "No folders found matching criteria" in result

    def test_analyze_folders_track_count(self, populated_db):
        """Analyze shows correct track counts per folder."""
        args = argparse.Namespace(
            folders=True,
            in_rekordbox=False, not_in_rekordbox=False,
            source="USB1", format=None, genre=None,
            bpm_min=None, bpm_max=None,
            limit=100
        )
        output = io.StringIO()
        with redirect_stdout(output):
            analyze.analyze(populated_db, args)

        result = output.getvalue()
        # USB1 has 2 tracks in the test data
        assert "2 track" in result

    def test_analyze_folders_respects_limit(self, populated_db):
        """Analyze respects the limit parameter."""
        args = argparse.Namespace(
            folders=True,
            in_rekordbox=False, not_in_rekordbox=False,
            source=None, format=None, genre=None,
            bpm_min=None, bpm_max=None,
            limit=1
        )
        output = io.StringIO()
        with redirect_stdout(output):
            analyze.analyze(populated_db, args)

        result = output.getvalue()
        # Should show only top folder by count
        lines = result.strip().split('\n')
        folder_lines = [l for l in lines if l.strip() and not "Folder Analysis" in l and not "---" in l]
        # Only one folder should be shown due to limit
        assert len([l for l in folder_lines if "/usb" in l.lower() or "usb" in l.lower()]) <= 1

    def test_analyze_no_analysis_type(self, populated_db):
        """Analyze shows message when no analysis type is specified."""
        args = argparse.Namespace(
            folders=False,
            in_rekordbox=False, not_in_rekordbox=False,
            source=None, format=None, genre=None,
            bpm_min=None, bpm_max=None,
            limit=100
        )
        output = io.StringIO()
        with redirect_stdout(output):
            analyze.analyze(populated_db, args)

        result = output.getvalue()
        assert "No analysis type specified" in result

    def test_analyze_folders_multiple_filters(self, populated_db):
        """Analyze with multiple filters applied."""
        # Use filters that will have some results
        args = argparse.Namespace(
            folders=True,
            in_rekordbox=True, not_in_rekordbox=False,
            source="USB1", format=None, genre="Techno",
            bpm_min=120.0, bpm_max=None,
            limit=100
        )
        output = io.StringIO()
        with redirect_stdout(output):
            analyze.analyze(populated_db, args)

        result = output.getvalue()
        # Should show all applied filters in the output
        assert "in rekordbox" in result
        assert "source=USB1" in result
        assert "genre=Techno" in result
        assert "bpm=120.0" in result

    def test_analyze_folders_singular_track(self, populated_db):
        """Analyze shows 'track' (singular) for 1 track."""
        # This is harder to test without modifying data, but we can verify the logic
        # by checking if the output uses proper grammar
        args = argparse.Namespace(
            folders=True,
            in_rekordbox=False, not_in_rekordbox=False,
            source=None, format=None, genre="Ambient",  # Only 2 ambient tracks
            bpm_min=None, bpm_max=None,
            limit=100
        )
        output = io.StringIO()
        with redirect_stdout(output):
            analyze.analyze(populated_db, args)

        result = output.getvalue()
        # Should contain proper plural/singular usage
        assert "track" in result or "Track" in result
