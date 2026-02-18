"""Tests for search and display modules."""

import argparse
import io
import sys
from contextlib import redirect_stdout

import pytest

from dj_indexer import search, display


class TestFreeTextSearch:
    """Test free-text search across all fields."""

    def test_search_by_title(self, populated_db):
        """Find track by title."""
        args = argparse.Namespace(
            query="Electric Dreams", regex=False, re=False,
            artist=None, title=None, filename=None, genre=None, key=None,
            bpm_min=None, bpm_max=None, source=None, format=None,
            in_rekordbox=False, not_in_rekordbox=False,
            no_cues=False, duplicates=False, playlists=False, playlist=None,
            limit=100
        )
        sql, params = search._build_search_query(args)
        cursor = populated_db.cursor()
        cursor.execute(sql, params)
        rows = cursor.fetchall()

        assert len(rows) == 1
        assert rows[0][2] == "Electric Dreams"  # title

    def test_search_by_artist(self, populated_db):
        """Find tracks by artist name."""
        args = argparse.Namespace(
            query="Jon Hopkins", regex=False, re=False,
            artist=None, title=None, filename=None, genre=None, key=None,
            bpm_min=None, bpm_max=None, source=None, format=None,
            in_rekordbox=False, not_in_rekordbox=False,
            no_cues=False, duplicates=False, playlists=False, playlist=None,
            limit=100
        )
        sql, params = search._build_search_query(args)
        cursor = populated_db.cursor()
        cursor.execute(sql, params)
        rows = cursor.fetchall()

        assert len(rows) == 2
        artists = [row[1] for row in rows]
        assert all(artist == "Jon Hopkins" for artist in artists)

    def test_search_by_filename(self, populated_db):
        """Find track by filename."""
        args = argparse.Namespace(
            query="track1.mp3", regex=False, re=False,
            artist=None, title=None, filename=None, genre=None, key=None,
            bpm_min=None, bpm_max=None, source=None, format=None,
            in_rekordbox=False, not_in_rekordbox=False,
            no_cues=False, duplicates=False, playlists=False, playlist=None,
            limit=100
        )
        sql, params = search._build_search_query(args)
        cursor = populated_db.cursor()
        cursor.execute(sql, params)
        rows = cursor.fetchall()

        assert len(rows) == 1
        assert rows[0][3] == "track1.mp3"  # filename

    def test_search_no_results(self, populated_db):
        """Return empty results for non-matching query."""
        args = argparse.Namespace(
            query="NonExistentTrack", regex=False, re=False,
            artist=None, title=None, filename=None, genre=None, key=None,
            bpm_min=None, bpm_max=None, source=None, format=None,
            in_rekordbox=False, not_in_rekordbox=False,
            no_cues=False, duplicates=False, playlists=False, playlist=None,
            limit=100
        )
        sql, params = search._build_search_query(args)
        cursor = populated_db.cursor()
        cursor.execute(sql, params)
        rows = cursor.fetchall()

        assert len(rows) == 0


class TestRegexSearch:
    """Test broad and field-scoped regex search."""

    def test_broad_regex_alternation(self, populated_db):
        """Search with regex alternation across all fields."""
        # Register REGEXP function
        import re as re_module
        populated_db.create_function("REGEXP", 2,
            lambda pat, val: bool(re_module.search(pat, val, re_module.IGNORECASE)) if val else False)

        args = argparse.Namespace(
            query="bicep|fisher", regex=True, re=False,
            artist=None, title=None, filename=None, genre=None, key=None,
            bpm_min=None, bpm_max=None, source=None, format=None,
            in_rekordbox=False, not_in_rekordbox=False,
            no_cues=False, duplicates=False, playlists=False, playlist=None,
            limit=100
        )
        sql, params = search._build_search_query(args)
        cursor = populated_db.cursor()
        cursor.execute(sql, params)
        rows = cursor.fetchall()

        assert len(rows) == 3  # 2 Bicep + 1 Fisher
        artists = [row[1] for row in rows]
        assert "Bicep" in artists
        assert "Fisher" in artists

    def test_regex_pattern_matching(self, populated_db):
        """Search with regex pattern."""
        # Register REGEXP function
        import re as re_module
        populated_db.create_function("REGEXP", 2,
            lambda pat, val: bool(re_module.search(pat, val, re_module.IGNORECASE)) if val else False)

        args = argparse.Namespace(
            query="^Electric.*", regex=True, re=False,
            artist=None, title=None, filename=None, genre=None, key=None,
            bpm_min=None, bpm_max=None, source=None, format=None,
            in_rekordbox=False, not_in_rekordbox=False,
            no_cues=False, duplicates=False, playlists=False, playlist=None,
            limit=100
        )
        sql, params = search._build_search_query(args)
        cursor = populated_db.cursor()
        cursor.execute(sql, params)
        rows = cursor.fetchall()

        assert len(rows) == 1
        assert rows[0][2] == "Electric Dreams"

    def test_regex_field_scoped_artist(self, populated_db):
        """Search with regex scoped to artist field."""
        # Register REGEXP function
        import re as re_module
        populated_db.create_function("REGEXP", 2,
            lambda pat, val: bool(re_module.search(pat, val, re_module.IGNORECASE)) if val else False)

        args = argparse.Namespace(
            query=None, regex=False, re=True,
            artist="bicep|fisher", title=None, filename=None, genre=None, key=None,
            bpm_min=None, bpm_max=None, source=None, format=None,
            in_rekordbox=False, not_in_rekordbox=False,
            no_cues=False, duplicates=False, playlists=False, playlist=None,
            limit=100
        )
        sql, params = search._build_search_query(args)
        cursor = populated_db.cursor()
        cursor.execute(sql, params)
        rows = cursor.fetchall()

        assert len(rows) == 3
        artists = [row[1] for row in rows]
        assert "Bicep" in artists
        assert "Fisher" in artists

    def test_regex_field_scoped_title(self, populated_db):
        """Search with regex scoped to title field."""
        # Register REGEXP function
        import re as re_module
        populated_db.create_function("REGEXP", 2,
            lambda pat, val: bool(re_module.search(pat, val, re_module.IGNORECASE)) if val else False)

        args = argparse.Namespace(
            query=None, regex=False, re=True,
            artist=None, title=".*wave.*", filename=None, genre=None, key=None,
            bpm_min=None, bpm_max=None, source=None, format=None,
            in_rekordbox=False, not_in_rekordbox=False,
            no_cues=False, duplicates=False, playlists=False, playlist=None,
            limit=100
        )
        sql, params = search._build_search_query(args)
        cursor = populated_db.cursor()
        cursor.execute(sql, params)
        rows = cursor.fetchall()

        assert len(rows) == 1
        assert "Ambient Waves" in rows[0][2]


class TestFieldFilters:
    """Test individual field filters."""

    def test_filter_by_artist(self, populated_db):
        """Filter by artist field."""
        args = argparse.Namespace(
            query=None, regex=False, re=False,
            artist="Bicep", title=None, filename=None, genre=None, key=None,
            bpm_min=None, bpm_max=None, source=None, format=None,
            in_rekordbox=False, not_in_rekordbox=False,
            no_cues=False, duplicates=False, playlists=False, playlist=None,
            limit=100
        )
        sql, params = search._build_search_query(args)
        cursor = populated_db.cursor()
        cursor.execute(sql, params)
        rows = cursor.fetchall()

        assert len(rows) == 2
        assert all(row[1] == "Bicep" for row in rows)

    def test_filter_by_title(self, populated_db):
        """Filter by title field."""
        args = argparse.Namespace(
            query=None, regex=False, re=False,
            artist=None, title="Chill", filename=None, genre=None, key=None,
            bpm_min=None, bpm_max=None, source=None, format=None,
            in_rekordbox=False, not_in_rekordbox=False,
            no_cues=False, duplicates=False, playlists=False, playlist=None,
            limit=100
        )
        sql, params = search._build_search_query(args)
        cursor = populated_db.cursor()
        cursor.execute(sql, params)
        rows = cursor.fetchall()

        assert len(rows) == 1
        assert "Chill Vibes" in rows[0][2]

    def test_filter_by_genre(self, populated_db):
        """Filter by genre field."""
        args = argparse.Namespace(
            query=None, regex=False, re=False,
            artist=None, title=None, filename=None, genre="Ambient", key=None,
            bpm_min=None, bpm_max=None, source=None, format=None,
            in_rekordbox=False, not_in_rekordbox=False,
            no_cues=False, duplicates=False, playlists=False, playlist=None,
            limit=100
        )
        sql, params = search._build_search_query(args)
        cursor = populated_db.cursor()
        cursor.execute(sql, params)
        rows = cursor.fetchall()

        # Should return 2 ambient tracks (ambient.flac and chill.mp3)
        assert len(rows) == 2

    def test_filter_by_source(self, populated_db):
        """Filter by source label."""
        args = argparse.Namespace(
            query=None, regex=False, re=False,
            artist=None, title=None, filename=None, genre=None, key=None,
            bpm_min=None, bpm_max=None, source="USB2", format=None,
            in_rekordbox=False, not_in_rekordbox=False,
            no_cues=False, duplicates=False, playlists=False, playlist=None,
            limit=100
        )
        sql, params = search._build_search_query(args)
        cursor = populated_db.cursor()
        cursor.execute(sql, params)
        rows = cursor.fetchall()

        assert len(rows) == 2
        assert all(row[7] == "USB2" for row in rows)


class TestBPMFilters:
    """Test BPM range filtering."""

    def test_bpm_minimum(self, populated_db):
        """Filter by minimum BPM."""
        args = argparse.Namespace(
            query=None, regex=False, re=False,
            artist=None, title=None, filename=None, genre=None, key=None,
            bpm_min=120.0, bpm_max=None, source=None, format=None,
            in_rekordbox=False, not_in_rekordbox=False,
            no_cues=False, duplicates=False, playlists=False, playlist=None,
            limit=100
        )
        sql, params = search._build_search_query(args)
        cursor = populated_db.cursor()
        cursor.execute(sql, params)
        rows = cursor.fetchall()

        assert len(rows) == 4
        assert all(row[5] >= 120.0 for row in rows)

    def test_bpm_maximum(self, populated_db):
        """Filter by maximum BPM."""
        args = argparse.Namespace(
            query=None, regex=False, re=False,
            artist=None, title=None, filename=None, genre=None, key=None,
            bpm_min=None, bpm_max=115.0, source=None, format=None,
            in_rekordbox=False, not_in_rekordbox=False,
            no_cues=False, duplicates=False, playlists=False, playlist=None,
            limit=100
        )
        sql, params = search._build_search_query(args)
        cursor = populated_db.cursor()
        cursor.execute(sql, params)
        rows = cursor.fetchall()

        assert len(rows) == 2
        assert all(row[5] <= 115.0 for row in rows)

    def test_bpm_range(self, populated_db):
        """Filter by BPM range."""
        args = argparse.Namespace(
            query=None, regex=False, re=False,
            artist=None, title=None, filename=None, genre=None, key=None,
            bpm_min=125.0, bpm_max=130.0, source=None, format=None,
            in_rekordbox=False, not_in_rekordbox=False,
            no_cues=False, duplicates=False, playlists=False, playlist=None,
            limit=100
        )
        sql, params = search._build_search_query(args)
        cursor = populated_db.cursor()
        cursor.execute(sql, params)
        rows = cursor.fetchall()

        assert len(rows) == 3
        assert all(125.0 <= row[5] <= 130.0 for row in rows)


class TestCombinedFilters:
    """Test combining multiple filters with AND logic."""

    def test_artist_and_genre(self, populated_db):
        """Combine artist and genre filters."""
        args = argparse.Namespace(
            query=None, regex=False, re=False,
            artist="Jon Hopkins", title=None, filename=None, genre="Ambient", key=None,
            bpm_min=None, bpm_max=None, source=None, format=None,
            in_rekordbox=False, not_in_rekordbox=False,
            no_cues=False, duplicates=False, playlists=False, playlist=None,
            limit=100
        )
        sql, params = search._build_search_query(args)
        cursor = populated_db.cursor()
        cursor.execute(sql, params)
        rows = cursor.fetchall()

        # Should return 2 Jon Hopkins ambient tracks
        assert len(rows) == 2
        assert all(row[1] == "Jon Hopkins" for row in rows)

    def test_genre_and_bpm_range(self, populated_db):
        """Combine genre and BPM filters."""
        args = argparse.Namespace(
            query=None, regex=False, re=False,
            artist=None, title=None, filename=None, genre="Techno", key=None,
            bpm_min=125.0, bpm_max=None, source=None, format=None,
            in_rekordbox=False, not_in_rekordbox=False,
            no_cues=False, duplicates=False, playlists=False, playlist=None,
            limit=100
        )
        sql, params = search._build_search_query(args)
        cursor = populated_db.cursor()
        cursor.execute(sql, params)
        rows = cursor.fetchall()

        # 3 tracks match: track1 (128, Techno), track2 (129, Techno), duplicate (130, Techno)
        assert len(rows) == 3
        # Column order: id, artist, title, filename, filepath, bpm, musical_key, source_label, ...
        assert all(row[5] >= 125.0 for row in rows)  # Check BPM

    def test_artist_source_and_bpm(self, populated_db):
        """Combine artist, source, and BPM filters."""
        args = argparse.Namespace(
            query=None, regex=False, re=False,
            artist="Jon Hopkins", title=None, filename=None, genre=None, key=None,
            bpm_min=None, bpm_max=120.0, source="External", format=None,
            in_rekordbox=False, not_in_rekordbox=False,
            no_cues=False, duplicates=False, playlists=False, playlist=None,
            limit=100
        )
        sql, params = search._build_search_query(args)
        cursor = populated_db.cursor()
        cursor.execute(sql, params)
        rows = cursor.fetchall()

        assert len(rows) == 1
        assert rows[0][1] == "Jon Hopkins"
        assert rows[0][7] == "External"
        assert rows[0][5] <= 120.0


class TestRekordboxFilters:
    """Test in_rekordbox and not_in_rekordbox filters."""

    def test_in_rekordbox_filter(self, populated_db):
        """Filter for tracks in rekordbox."""
        args = argparse.Namespace(
            query=None, regex=False, re=False,
            artist=None, title=None, filename=None, genre=None, key=None,
            bpm_min=None, bpm_max=None, source=None, format=None,
            in_rekordbox=True, not_in_rekordbox=False,
            no_cues=False, duplicates=False, playlists=False, playlist=None,
            limit=100
        )
        sql, params = search._build_search_query(args)
        cursor = populated_db.cursor()
        cursor.execute(sql, params)
        rows = cursor.fetchall()

        assert len(rows) == 6
        assert all(row[8] == 1 for row in rows)  # in_rekordbox column


class TestCueQueries:
    """Test cue-related special queries."""

    def test_show_cues_command(self, populated_db):
        """Test show_cues function displays correct information."""
        # Capture output
        f = io.StringIO()
        with redirect_stdout(f):
            search.show_cues(populated_db, "Bicep")
        output = f.getvalue()

        # Should show 2 tracks (both Bicep tracks)
        assert "Electric Dreams" in output
        assert "Glue" in output
        # Should show cue points
        assert "Cue points" in output
        assert "Drop" in output

    def test_show_cues_no_results(self, populated_db):
        """Test show_cues with no matching tracks."""
        f = io.StringIO()
        with redirect_stdout(f):
            search.show_cues(populated_db, "NonExistent")
        output = f.getvalue()

        assert "No tracks found" in output


class TestSpecialQueries:
    """Test special query modes."""

    def test_playlists_display(self, populated_db):
        """Test listing all playlists."""
        cursor = populated_db.cursor()
        f = io.StringIO()
        with redirect_stdout(f):
            search._show_playlists(cursor)
        output = f.getvalue()

        assert "Playlists" in output
        assert "Techno Bangers" in output
        assert "Ambient" in output  # Path contains "Ambient"
        assert "House" in output

    def test_duplicates_none(self, populated_db):
        """Test duplicates detection when none exist."""
        cursor = populated_db.cursor()
        f = io.StringIO()
        with redirect_stdout(f):
            search._show_duplicates(cursor)
        output = f.getvalue()

        assert "No duplicate" in output

    def test_no_cues_tracks(self, populated_db):
        """Test finding rekordbox tracks without cue points."""
        cursor = populated_db.cursor()
        f = io.StringIO()
        with redirect_stdout(f):
            search._show_no_cues(cursor, 100)
        output = f.getvalue()

        # "duplicate.mp3" has no cues
        assert "Duplicate Track" in output


class TestDisplayFormatting:
    """Test display module formatting functions."""

    def test_print_results_basic(self, populated_db):
        """Test basic result printing."""
        cursor = populated_db.cursor()
        cursor.execute("""
            SELECT
                t.id, t.artist, t.title, t.filename, t.filepath, t.bpm, t.musical_key,
                t.source_label, t.in_rekordbox,
                COUNT(CASE WHEN cp.cue_type LIKE 'hot_cue_%' THEN 1 END) as num_hot_cues,
                COUNT(cp.id) as num_cues
            FROM tracks t
            LEFT JOIN cue_points cp ON t.id = cp.track_id
            WHERE t.title = 'Electric Dreams'
            GROUP BY t.id
        """)
        rows = [tuple(row) for row in cursor.fetchall()]

        f = io.StringIO()
        with redirect_stdout(f):
            display.print_results(rows, "Test Results")
        output = f.getvalue()

        assert "Test Results" in output
        assert "Electric Dreams" in output
        assert "Bicep" in output
        assert "128" in output  # BPM
        assert "[RB]" in output  # rekordbox badge

    def test_print_results_with_cues(self, populated_db):
        """Test result printing with cue badges."""
        cursor = populated_db.cursor()
        cursor.execute("""
            SELECT
                t.id, t.artist, t.title, t.filename, t.filepath, t.bpm, t.musical_key,
                t.source_label, t.in_rekordbox,
                COUNT(CASE WHEN cp.cue_type LIKE 'hot_cue_%' THEN 1 END) as num_hot_cues,
                COUNT(cp.id) as num_cues
            FROM tracks t
            LEFT JOIN cue_points cp ON t.id = cp.track_id
            WHERE t.title = 'Electric Dreams'
            GROUP BY t.id
        """)
        rows = [tuple(row) for row in cursor.fetchall()]

        f = io.StringIO()
        with redirect_stdout(f):
            display.print_results(rows)
        output = f.getvalue()

        # Should show hot/total cues
        assert "[2H/3C]" in output or "[2H" in output  # 2 hot cues, 3 total

    def test_print_results_no_cues(self, populated_db):
        """Test result printing for tracks without cues."""
        cursor = populated_db.cursor()
        cursor.execute("""
            SELECT
                t.id, t.artist, t.title, t.filename, t.filepath, t.bpm, t.musical_key,
                t.source_label, t.in_rekordbox,
                COUNT(CASE WHEN cp.cue_type LIKE 'hot_cue_%' THEN 1 END) as num_hot_cues,
                COUNT(cp.id) as num_cues
            FROM tracks t
            LEFT JOIN cue_points cp ON t.id = cp.track_id
            WHERE t.title = 'Duplicate Track'
            GROUP BY t.id
        """)
        rows = [tuple(row) for row in cursor.fetchall()]

        f = io.StringIO()
        with redirect_stdout(f):
            display.print_results(rows)
        output = f.getvalue()

        assert "[NO CUES]" in output

    def test_print_results_empty(self):
        """Test result printing with no results."""
        f = io.StringIO()
        with redirect_stdout(f):
            display.print_results([], "Empty Results")
        output = f.getvalue()

        assert "0 tracks" in output

    def test_print_cue_details(self, populated_db):
        """Test detailed cue display."""
        cursor = populated_db.cursor()
        # Get a track
        cursor.execute("""
            SELECT id, artist, title, filename, bpm, musical_key, source_label, duration_sec
            FROM tracks
            WHERE title = 'Electric Dreams'
        """)
        track = tuple(cursor.fetchone())

        # Get cues for track
        cursor.execute("""
            SELECT id, track_id, cue_type, cue_name, cue_num, position_sec, is_loop, loop_end_sec
            FROM cue_points
            WHERE track_id = ?
            ORDER BY position_sec
        """, (track[0],))
        cues = [tuple(row) for row in cursor.fetchall()]

        f = io.StringIO()
        with redirect_stdout(f):
            display.print_cue_details(track, cues)
        output = f.getvalue()

        assert "Electric Dreams" in output
        assert "Bicep" in output
        assert "128" in output  # BPM
        assert "Cue points" in output
        assert "Memory Cue" in output
        assert "Hot Cue A" in output
        assert "Drop" in output

    def test_duration_formatting(self):
        """Test duration formatting helper."""
        assert display._format_duration(0.0) == "0:00"
        assert display._format_duration(15.5) == "0:15"
        assert display._format_duration(60.0) == "1:00"
        assert display._format_duration(125.5) == "2:05"
        assert display._format_duration(3661.0) == "1:01:01"
        assert display._format_duration(None) == "?"


class TestPlaylistFiltering:
    """Test playlist search and filtering."""

    def test_search_playlist_by_name(self, populated_db):
        """Search for playlist by name."""
        args = argparse.Namespace(
            query=None, regex=False, re=False,
            artist=None, title=None, filename=None, genre=None, key=None,
            bpm_min=None, bpm_max=None, source=None, format=None,
            in_rekordbox=False, not_in_rekordbox=False,
            no_cues=False, duplicates=False, playlists=False,
            playlist="Techno",
            limit=100
        )

        cursor = populated_db.cursor()
        f = io.StringIO()
        with redirect_stdout(f):
            search._search_playlist(cursor, args, display)
        output = f.getvalue()

        assert "Techno Bangers" in output or "Playlist:" in output

    def test_search_playlist_regex(self, populated_db):
        """Search for playlist with regex."""
        args = argparse.Namespace(
            query=None, regex=False, re=True,
            artist=None, title=None, filename=None, genre=None, key=None,
            bpm_min=None, bpm_max=None, source=None, format=None,
            in_rekordbox=False, not_in_rekordbox=False,
            no_cues=False, duplicates=False, playlists=False,
            playlist=".*Chill.*",
            limit=100
        )

        cursor = populated_db.cursor()
        f = io.StringIO()
        with redirect_stdout(f):
            search._search_playlist(cursor, args, display)
        output = f.getvalue()

        assert "Ambient Chill" in output or "Playlist:" in output
