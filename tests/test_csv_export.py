"""Tests for CSV export functionality in search and query commands."""

import csv
import sqlite3
import tempfile
from pathlib import Path
from unittest import mock

import pytest

from dj_indexer import db, search, query, export_results


class TestSearchCSVExport:
    """Tests for CSV export in search command."""

    def test_search_export_csv_basic(self, test_db):
        """Test basic CSV export from search results."""
        # Insert test data
        cursor = test_db.cursor()
        cursor.execute("""
            INSERT INTO tracks (filepath, filename, filename_lower, source_label,
                               title, artist, genre, bpm, musical_key, file_format, in_rekordbox)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            '/Volumes/USB1/Track1.mp3', 'Track1.mp3', 'track1.mp3', 'USB1',
            'Track 1', 'Artist A', 'Techno', 128.0, '2A', '.mp3', 1
        ))
        test_db.commit()

        # Export to CSV
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.csv', delete=False) as f:
            csv_path = Path(f.name)

        try:
            args = mock.Mock(
                export_csv=csv_path,
                columns=['artist', 'title', 'bpm'],
                path_conversion=None,
                volume_map=None
            )

            # Get search results manually
            cursor.execute("""
                SELECT
                    t.id, t.artist, t.title, t.filename, t.filepath, t.bpm, t.musical_key,
                    t.source_label, t.in_rekordbox,
                    COUNT(CASE WHEN cp.cue_type LIKE 'hot_cue_%' THEN 1 END) as num_hot_cues,
                    COUNT(cp.id) as num_cues
                FROM tracks t
                LEFT JOIN cue_points cp ON t.id = cp.track_id
                WHERE 1=1
                GROUP BY t.id
            """)
            rows = cursor.fetchall()

            column_names = [
                'id', 'artist', 'title', 'filename', 'filepath', 'bpm',
                'musical_key', 'source_label', 'in_rekordbox', 'num_hot_cues', 'num_cues'
            ]

            # Export
            search._export_search_results(rows, column_names, args)

            # Verify CSV
            with open(csv_path) as f:
                reader = csv.DictReader(f)
                rows_read = list(reader)

            assert len(rows_read) == 1
            assert rows_read[0]['artist'] == 'Artist A'
            assert rows_read[0]['title'] == 'Track 1'
            assert rows_read[0]['bpm'] == '128.0'
        finally:
            csv_path.unlink(missing_ok=True)

    def test_search_export_csv_all_columns(self, test_db):
        """Test CSV export with all columns."""
        cursor = test_db.cursor()
        cursor.execute("""
            INSERT INTO tracks (filepath, filename, filename_lower, source_label,
                               title, artist, genre, bpm, musical_key, file_format, in_rekordbox)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            '/Volumes/USB1/Track1.mp3', 'Track1.mp3', 'track1.mp3', 'USB1',
            'Track 1', 'Artist A', 'Techno', 128.0, '2A', '.mp3', 1
        ))
        test_db.commit()

        with tempfile.NamedTemporaryFile(mode='w+', suffix='.csv', delete=False) as f:
            csv_path = Path(f.name)

        try:
            args = mock.Mock(
                export_csv=csv_path,
                columns=None,  # Export all columns
                path_conversion=None,
                volume_map=None
            )

            cursor.execute("""
                SELECT
                    t.id, t.artist, t.title, t.filename, t.filepath, t.bpm, t.musical_key,
                    t.source_label, t.in_rekordbox,
                    COUNT(CASE WHEN cp.cue_type LIKE 'hot_cue_%' THEN 1 END) as num_hot_cues,
                    COUNT(cp.id) as num_cues
                FROM tracks t
                LEFT JOIN cue_points cp ON t.id = cp.track_id
                GROUP BY t.id
            """)
            rows = cursor.fetchall()

            column_names = [
                'id', 'artist', 'title', 'filename', 'filepath', 'bpm',
                'musical_key', 'source_label', 'in_rekordbox', 'num_hot_cues', 'num_cues'
            ]

            search._export_search_results(rows, column_names, args)

            # Verify all columns in CSV
            with open(csv_path) as f:
                reader = csv.DictReader(f)
                rows_read = list(reader)

            assert len(rows_read) == 1
            # Check that all columns are present
            for col in column_names:
                assert col in reader.fieldnames
        finally:
            csv_path.unlink(missing_ok=True)

    def test_search_export_csv_path_conversion_mac_to_windows(self, test_db):
        """Test CSV export with Mac to Windows path conversion."""
        cursor = test_db.cursor()
        cursor.execute("""
            INSERT INTO tracks (filepath, filename, filename_lower, source_label,
                               title, artist, genre, bpm, musical_key, file_format, in_rekordbox)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            '/Volumes/USB1/Techno/Track1.mp3', 'Track1.mp3', 'track1.mp3', 'USB1',
            'Track 1', 'Artist A', 'Techno', 128.0, '2A', '.mp3', 1
        ))
        test_db.commit()

        with tempfile.NamedTemporaryFile(mode='w+', suffix='.csv', delete=False) as f:
            csv_path = Path(f.name)

        try:
            args = mock.Mock(
                export_csv=csv_path,
                columns=['filepath'],
                path_conversion='mac-to-windows',
                volume_map=['USB1=E', 'USB2=F']
            )

            cursor.execute("""
                SELECT
                    t.id, t.artist, t.title, t.filename, t.filepath, t.bpm, t.musical_key,
                    t.source_label, t.in_rekordbox,
                    COUNT(CASE WHEN cp.cue_type LIKE 'hot_cue_%' THEN 1 END) as num_hot_cues,
                    COUNT(cp.id) as num_cues
                FROM tracks t
                LEFT JOIN cue_points cp ON t.id = cp.track_id
                GROUP BY t.id
            """)
            rows = cursor.fetchall()

            column_names = [
                'id', 'artist', 'title', 'filename', 'filepath', 'bpm',
                'musical_key', 'source_label', 'in_rekordbox', 'num_hot_cues', 'num_cues'
            ]

            search._export_search_results(rows, column_names, args)

            # Verify path conversion
            with open(csv_path) as f:
                reader = csv.DictReader(f)
                rows_read = list(reader)

            assert len(rows_read) == 1
            # Mac path /Volumes/USB1/... should be converted to E:\...
            assert rows_read[0]['filepath'] == 'E:\\Techno\\Track1.mp3'
        finally:
            csv_path.unlink(missing_ok=True)

    def test_search_export_csv_path_conversion_windows_to_mac(self, test_db):
        """Test CSV export with Windows to Mac path conversion."""
        cursor = test_db.cursor()
        cursor.execute("""
            INSERT INTO tracks (filepath, filename, filename_lower, source_label,
                               title, artist, genre, bpm, musical_key, file_format, in_rekordbox)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            'E:\\Music\\Track1.mp3', 'Track1.mp3', 'track1.mp3', 'Windows',
            'Track 1', 'Artist A', 'Techno', 128.0, '2A', '.mp3', 1
        ))
        test_db.commit()

        with tempfile.NamedTemporaryFile(mode='w+', suffix='.csv', delete=False) as f:
            csv_path = Path(f.name)

        try:
            args = mock.Mock(
                export_csv=csv_path,
                columns=['filepath'],
                path_conversion='windows-to-mac',
                volume_map=['USB1=E', 'USB2=F']
            )

            cursor.execute("""
                SELECT
                    t.id, t.artist, t.title, t.filename, t.filepath, t.bpm, t.musical_key,
                    t.source_label, t.in_rekordbox,
                    COUNT(CASE WHEN cp.cue_type LIKE 'hot_cue_%' THEN 1 END) as num_hot_cues,
                    COUNT(cp.id) as num_cues
                FROM tracks t
                LEFT JOIN cue_points cp ON t.id = cp.track_id
                GROUP BY t.id
            """)
            rows = cursor.fetchall()

            column_names = [
                'id', 'artist', 'title', 'filename', 'filepath', 'bpm',
                'musical_key', 'source_label', 'in_rekordbox', 'num_hot_cues', 'num_cues'
            ]

            search._export_search_results(rows, column_names, args)

            # Verify path conversion
            with open(csv_path) as f:
                reader = csv.DictReader(f)
                rows_read = list(reader)

            assert len(rows_read) == 1
            # Windows path E:\... should be converted to /Volumes/USB1/...
            assert rows_read[0]['filepath'] == '/Volumes/USB1/Music/Track1.mp3'
        finally:
            csv_path.unlink(missing_ok=True)

    def test_search_export_csv_multiple_rows(self, test_db):
        """Test CSV export with multiple search results."""
        cursor = test_db.cursor()
        cursor.executemany("""
            INSERT INTO tracks (filepath, filename, filename_lower, source_label,
                               title, artist, genre, bpm, musical_key, file_format, in_rekordbox)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            ('/Volumes/USB1/Track1.mp3', 'Track1.mp3', 'track1.mp3', 'USB1',
             'Track 1', 'Artist A', 'Techno', 128.0, '2A', '.mp3', 1),
            ('/Volumes/USB1/Track2.mp3', 'Track2.mp3', 'track2.mp3', 'USB1',
             'Track 2', 'Artist B', 'Techno', 130.0, '1A', '.mp3', 0),
            ('/Volumes/USB2/Track3.mp3', 'Track3.mp3', 'track3.mp3', 'USB2',
             'Track 3', 'Artist C', 'Techno', 126.0, '3A', '.mp3', 1),
        ])
        test_db.commit()

        with tempfile.NamedTemporaryFile(mode='w+', suffix='.csv', delete=False) as f:
            csv_path = Path(f.name)

        try:
            args = mock.Mock(
                export_csv=csv_path,
                columns=['artist', 'bpm'],
                path_conversion=None,
                volume_map=None
            )

            cursor.execute("""
                SELECT
                    t.id, t.artist, t.title, t.filename, t.filepath, t.bpm, t.musical_key,
                    t.source_label, t.in_rekordbox,
                    COUNT(CASE WHEN cp.cue_type LIKE 'hot_cue_%' THEN 1 END) as num_hot_cues,
                    COUNT(cp.id) as num_cues
                FROM tracks t
                LEFT JOIN cue_points cp ON t.id = cp.track_id
                GROUP BY t.id
            """)
            rows = cursor.fetchall()

            column_names = [
                'id', 'artist', 'title', 'filename', 'filepath', 'bpm',
                'musical_key', 'source_label', 'in_rekordbox', 'num_hot_cues', 'num_cues'
            ]

            search._export_search_results(rows, column_names, args)

            # Verify CSV
            with open(csv_path) as f:
                reader = csv.DictReader(f)
                rows_read = list(reader)

            assert len(rows_read) == 3
            assert rows_read[0]['artist'] == 'Artist A'
            assert rows_read[1]['artist'] == 'Artist B'
            assert rows_read[2]['artist'] == 'Artist C'
        finally:
            csv_path.unlink(missing_ok=True)


class TestQueryCSVExport:
    """Tests for CSV export in query command."""

    def test_query_export_csv_basic(self, test_db):
        """Test basic CSV export from query results."""
        # Insert test data
        cursor = test_db.cursor()
        cursor.executemany("""
            INSERT INTO tracks (filepath, filename, filename_lower, source_label,
                               title, artist, genre, bpm, musical_key, file_format, in_rekordbox)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            ('/Volumes/USB1/Track1.mp3', 'Track1.mp3', 'track1.mp3', 'USB1',
             'Track 1', 'Artist A', 'Techno', 128.0, '2A', '.mp3', 1),
            ('/Volumes/USB1/Track2.mp3', 'Track2.mp3', 'track2.mp3', 'USB1',
             'Track 2', 'Artist B', 'House', 125.0, '10A', '.mp3', 0),
        ])
        test_db.commit()

        with tempfile.NamedTemporaryFile(mode='w+', suffix='.csv', delete=False) as f:
            csv_path = Path(f.name)

        try:
            args = mock.Mock(
                export_csv=csv_path,
                columns=None,
                path_conversion=None,
                volume_map=None
            )

            sql = "SELECT artist, genre FROM tracks"
            rows, column_names = query._execute_query(test_db, sql)

            # Verify results before export
            assert len(rows) == 2
            assert column_names == ['artist', 'genre']

            # Export
            query._export_query_results(rows, column_names, args)

            # Verify CSV
            with open(csv_path) as f:
                reader = csv.DictReader(f)
                rows_read = list(reader)

            assert len(rows_read) == 2
            assert rows_read[0]['artist'] == 'Artist A'
            assert rows_read[0]['genre'] == 'Techno'
        finally:
            csv_path.unlink(missing_ok=True)

    def test_query_export_csv_with_aggregation(self, test_db):
        """Test CSV export from aggregated query results."""
        cursor = test_db.cursor()
        cursor.executemany("""
            INSERT INTO tracks (filepath, filename, filename_lower, source_label,
                               title, artist, genre, bpm, musical_key, file_format, in_rekordbox)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            ('/Volumes/USB1/Track1.mp3', 'Track1.mp3', 'track1.mp3', 'USB1',
             'Track 1', 'Artist A', 'Techno', 128.0, '2A', '.mp3', 1),
            ('/Volumes/USB1/Track2.mp3', 'Track2.mp3', 'track2.mp3', 'USB1',
             'Track 2', 'Artist A', 'Techno', 130.0, '1A', '.mp3', 1),
            ('/Volumes/USB1/Track3.mp3', 'Track3.mp3', 'track3.mp3', 'USB1',
             'Track 3', 'Artist B', 'House', 125.0, '10A', '.mp3', 0),
        ])
        test_db.commit()

        with tempfile.NamedTemporaryFile(mode='w+', suffix='.csv', delete=False) as f:
            csv_path = Path(f.name)

        try:
            args = mock.Mock(
                export_csv=csv_path,
                columns=None,
                path_conversion=None,
                volume_map=None
            )

            sql = "SELECT artist, COUNT(*) as count FROM tracks GROUP BY artist ORDER BY count DESC"
            rows, column_names = query._execute_query(test_db, sql)

            assert len(rows) == 2
            assert rows[0][1] == 2  # Artist A has 2 tracks
            assert rows[1][1] == 1  # Artist B has 1 track

            query._export_query_results(rows, column_names, args)

            # Verify CSV
            with open(csv_path) as f:
                reader = csv.DictReader(f)
                rows_read = list(reader)

            assert len(rows_read) == 2
            assert int(rows_read[0]['count']) == 2
        finally:
            csv_path.unlink(missing_ok=True)

    def test_query_export_csv_column_selection(self, test_db):
        """Test CSV export with column selection in query."""
        cursor = test_db.cursor()
        cursor.execute("""
            INSERT INTO tracks (filepath, filename, filename_lower, source_label,
                               title, artist, genre, bpm, musical_key, file_format, in_rekordbox)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            '/Volumes/USB1/Track1.mp3', 'Track1.mp3', 'track1.mp3', 'USB1',
            'Track 1', 'Artist A', 'Techno', 128.0, '2A', '.mp3', 1
        ))
        test_db.commit()

        with tempfile.NamedTemporaryFile(mode='w+', suffix='.csv', delete=False) as f:
            csv_path = Path(f.name)

        try:
            args = mock.Mock(
                export_csv=csv_path,
                columns=['artist', 'genre'],
                path_conversion=None,
                volume_map=None
            )

            sql = "SELECT artist, genre, bpm FROM tracks"
            rows, column_names = query._execute_query(test_db, sql)

            assert column_names == ['artist', 'genre', 'bpm']

            query._export_query_results(rows, column_names, args)

            # Verify CSV has only selected columns
            with open(csv_path) as f:
                reader = csv.DictReader(f)
                rows_read = list(reader)

            assert list(reader.fieldnames) == ['artist', 'genre']
        finally:
            csv_path.unlink(missing_ok=True)

    def test_query_export_csv_with_path_conversion(self, test_db):
        """Test CSV export with path conversion in query."""
        cursor = test_db.cursor()
        cursor.executemany("""
            INSERT INTO tracks (filepath, filename, filename_lower, source_label,
                               title, artist, genre, bpm, musical_key, file_format, in_rekordbox)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            ('/Volumes/USB1/Techno/Track1.mp3', 'Track1.mp3', 'track1.mp3', 'USB1',
             'Track 1', 'Artist A', 'Techno', 128.0, '2A', '.mp3', 1),
            ('/Volumes/USB2/House/Track2.mp3', 'Track2.mp3', 'track2.mp3', 'USB2',
             'Track 2', 'Artist B', 'House', 125.0, '10A', '.mp3', 0),
        ])
        test_db.commit()

        with tempfile.NamedTemporaryFile(mode='w+', suffix='.csv', delete=False) as f:
            csv_path = Path(f.name)

        try:
            args = mock.Mock(
                export_csv=csv_path,
                columns=['filepath'],
                path_conversion='mac-to-windows',
                volume_map=['USB1=E', 'USB2=F']
            )

            sql = "SELECT filepath FROM tracks ORDER BY filepath"
            rows, column_names = query._execute_query(test_db, sql)

            query._export_query_results(rows, column_names, args)

            # Verify path conversion
            with open(csv_path) as f:
                reader = csv.DictReader(f)
                rows_read = list(reader)

            assert len(rows_read) == 2
            assert rows_read[0]['filepath'] == 'E:\\Techno\\Track1.mp3'
            assert rows_read[1]['filepath'] == 'F:\\House\\Track2.mp3'
        finally:
            csv_path.unlink(missing_ok=True)


class TestVolumeMapParsing:
    """Tests for volume mapping parsing."""

    def test_parse_volume_map_single(self, test_db):
        """Test parsing single volume mapping."""
        args = mock.Mock(
            export_csv=Path('/tmp/test.csv'),
            columns=None,
            path_conversion='mac-to-windows',
            volume_map=['USB1=E']
        )

        cursor = test_db.cursor()
        cursor.execute("""
            INSERT INTO tracks (filepath, filename, filename_lower, source_label,
                               title, artist, genre, bpm, musical_key, file_format, in_rekordbox)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            '/Volumes/USB1/Track.mp3', 'Track.mp3', 'track.mp3', 'USB1',
            'Track', 'Artist', 'Techno', 128.0, '2A', '.mp3', 1
        ))
        test_db.commit()

        # Parse mapping within export function
        volume_mappings = {}
        for mapping in args.volume_map:
            if '=' in mapping:
                volume_name, drive = mapping.split('=', 1)
                volume_mappings[volume_name.strip()] = drive.strip()

        assert volume_mappings == {'USB1': 'E'}

    def test_parse_volume_map_multiple(self):
        """Test parsing multiple volume mappings."""
        volume_map = ['USB1=E', 'USB2=F', 'Archive=G']

        volume_mappings = {}
        for mapping in volume_map:
            if '=' in mapping:
                volume_name, drive = mapping.split('=', 1)
                volume_mappings[volume_name.strip()] = drive.strip()

        assert volume_mappings == {
            'USB1': 'E',
            'USB2': 'F',
            'Archive': 'G'
        }

    def test_parse_volume_map_with_spaces(self):
        """Test parsing volume mappings with extra spaces."""
        volume_map = [' USB1 = E ', 'USB2= F', ' USB3 =G']

        volume_mappings = {}
        for mapping in volume_map:
            if '=' in mapping:
                volume_name, drive = mapping.split('=', 1)
                volume_mappings[volume_name.strip()] = drive.strip()

        assert volume_mappings == {
            'USB1': 'E',
            'USB2': 'F',
            'USB3': 'G'
        }


class TestPathConversion:
    """Tests for path conversion functionality."""

    def test_mac_to_windows_basic(self):
        """Test basic Mac to Windows path conversion."""
        from dj_indexer.export_results import _mac_to_windows

        mac_path = '/Volumes/USB1/Music/Track.mp3'
        volume_mappings = {'USB1': 'E'}

        result = _mac_to_windows(mac_path, volume_mappings)
        assert result == 'E:\\Music\\Track.mp3'

    def test_mac_to_windows_nested_folders(self):
        """Test Mac to Windows conversion with nested folders."""
        from dj_indexer.export_results import _mac_to_windows

        mac_path = '/Volumes/Archive/2024/Techno/Artist/Track.mp3'
        volume_mappings = {'Archive': 'G'}

        result = _mac_to_windows(mac_path, volume_mappings)
        assert result == 'G:\\2024\\Techno\\Artist\\Track.mp3'

    def test_mac_to_windows_unmapped_volume(self):
        """Test Mac to Windows conversion with unmapped volume."""
        from dj_indexer.export_results import _mac_to_windows

        mac_path = '/Volumes/UnmappedVolume/Track.mp3'
        volume_mappings = {'USB1': 'E'}

        # Should use first letter of volume name as fallback
        result = _mac_to_windows(mac_path, volume_mappings)
        assert result.startswith('U:\\')

    def test_windows_to_mac_basic(self):
        """Test basic Windows to Mac path conversion."""
        from dj_indexer.export_results import _windows_to_mac

        windows_path = 'E:\\Music\\Track.mp3'
        volume_mappings = {'USB1': 'E'}

        result = _windows_to_mac(windows_path, volume_mappings)
        assert result == '/Volumes/USB1/Music/Track.mp3'

    def test_windows_to_mac_nested_folders(self):
        """Test Windows to Mac conversion with nested folders."""
        from dj_indexer.export_results import _windows_to_mac

        windows_path = 'G:\\2024\\Techno\\Artist\\Track.mp3'
        volume_mappings = {'Archive': 'G'}

        result = _windows_to_mac(windows_path, volume_mappings)
        assert result == '/Volumes/Archive/2024/Techno/Artist/Track.mp3'

    def test_windows_to_mac_unmapped_drive(self):
        """Test Windows to Mac conversion with unmapped drive."""
        from dj_indexer.export_results import _windows_to_mac

        windows_path = 'Z:\\Music\\Track.mp3'
        volume_mappings = {'USB1': 'E'}

        # Should use generic volume name as fallback
        result = _windows_to_mac(windows_path, volume_mappings)
        assert result.startswith('/Volumes/VolumeZ/')

    def test_non_path_string_unchanged(self):
        """Test that non-path strings are returned unchanged."""
        from dj_indexer.export_results import _mac_to_windows, _windows_to_mac

        # Mac path without /Volumes prefix
        result = _mac_to_windows('/Users/me/track.mp3', {})
        assert result == '/Users/me/track.mp3'

        # Windows path without drive letter
        result = _windows_to_mac('relative/path/track.mp3', {})
        assert result == 'relative/path/track.mp3'


class TestCSVExportEdgeCases:
    """Tests for edge cases in CSV export."""

    def test_export_empty_results(self, test_db):
        """Test CSV export with no results."""
        # Use a unique filename that doesn't exist yet
        import uuid
        csv_path = Path(tempfile.gettempdir()) / f"test_export_empty_{uuid.uuid4()}.csv"

        try:
            rows = []
            column_names = ['artist', 'title', 'bpm']

            export_results.export_to_csv(
                rows=rows,
                column_names=column_names,
                output_path=csv_path,
                selected_columns=['artist']
            )

            # Should not create file when there are no results (returns early)
            # The function prints "No results to export" and returns
            assert not csv_path.exists()
        finally:
            csv_path.unlink(missing_ok=True)

    def test_export_with_none_values(self, test_db):
        """Test CSV export with NULL values."""
        cursor = test_db.cursor()
        cursor.execute("""
            INSERT INTO tracks (filepath, filename, filename_lower, source_label,
                               title, artist, genre, bpm, musical_key, file_format, in_rekordbox)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            '/Volumes/USB1/Track.mp3', 'Track.mp3', 'track.mp3', 'USB1',
            'Track', None,  # NULL artist
            'Techno', None,  # NULL bpm
            '2A', '.mp3', 1
        ))
        test_db.commit()

        with tempfile.NamedTemporaryFile(mode='w+', suffix='.csv', delete=False) as f:
            csv_path = Path(f.name)

        try:
            args = mock.Mock(
                export_csv=csv_path,
                columns=['artist', 'bpm'],
                path_conversion=None,
                volume_map=None
            )

            cursor.execute("SELECT artist, bpm FROM tracks")
            rows = cursor.fetchall()

            export_results.export_to_csv(
                rows=rows,
                column_names=['artist', 'bpm'],
                output_path=csv_path,
                selected_columns=args.columns
            )

            with open(csv_path) as f:
                reader = csv.DictReader(f)
                rows_read = list(reader)

            # NULL values should be empty in CSV
            assert rows_read[0]['artist'] == ''
            assert rows_read[0]['bpm'] == ''
        finally:
            csv_path.unlink(missing_ok=True)

    def test_export_with_special_characters(self, test_db):
        """Test CSV export with special characters in data."""
        cursor = test_db.cursor()
        cursor.execute("""
            INSERT INTO tracks (filepath, filename, filename_lower, source_label,
                               title, artist, genre, bpm, musical_key, file_format, in_rekordbox)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            '/Volumes/USB1/Track.mp3', 'Track.mp3', 'track.mp3', 'USB1',
            'Track, With "Comma" and "Quotes"', 'Artist, Name', 'Techno', 128.0, '2A', '.mp3', 1
        ))
        test_db.commit()

        with tempfile.NamedTemporaryFile(mode='w+', suffix='.csv', delete=False) as f:
            csv_path = Path(f.name)

        try:
            args = mock.Mock(
                export_csv=csv_path,
                columns=['title', 'artist'],
                path_conversion=None,
                volume_map=None
            )

            cursor.execute("SELECT title, artist FROM tracks")
            rows = cursor.fetchall()

            export_results.export_to_csv(
                rows=rows,
                column_names=['title', 'artist'],
                output_path=csv_path,
                selected_columns=args.columns
            )

            # Verify CSV is properly escaped
            with open(csv_path) as f:
                reader = csv.DictReader(f)
                rows_read = list(reader)

            assert rows_read[0]['title'] == 'Track, With "Comma" and "Quotes"'
            assert rows_read[0]['artist'] == 'Artist, Name'
        finally:
            csv_path.unlink(missing_ok=True)

    def test_export_invalid_column_skipped(self, test_db):
        """Test that invalid columns are skipped with warning."""
        cursor = test_db.cursor()
        cursor.execute("""
            INSERT INTO tracks (filepath, filename, filename_lower, source_label,
                               title, artist, genre, bpm, musical_key, file_format, in_rekordbox)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            '/Volumes/USB1/Track.mp3', 'Track.mp3', 'track.mp3', 'USB1',
            'Track', 'Artist', 'Techno', 128.0, '2A', '.mp3', 1
        ))
        test_db.commit()

        with tempfile.NamedTemporaryFile(mode='w+', suffix='.csv', delete=False) as f:
            csv_path = Path(f.name)

        try:
            # Request valid and invalid columns
            cursor.execute("SELECT artist, title FROM tracks")
            rows = cursor.fetchall()

            export_results.export_to_csv(
                rows=rows,
                column_names=['artist', 'title'],
                output_path=csv_path,
                selected_columns=['artist', 'nonexistent_column', 'title']
            )

            # Should export only valid columns
            with open(csv_path) as f:
                reader = csv.DictReader(f)
                assert set(reader.fieldnames) == {'artist', 'title'}
        finally:
            csv_path.unlink(missing_ok=True)
