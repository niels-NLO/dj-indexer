"""Tests for rekordbox XML import functionality."""

from pathlib import Path

import pytest

from dj_indexer import rekordbox_xml


class TestRekordboxXMLImport:
    """Test XML import with official pyrekordbox test files."""

    def test_rb5_xml_import_tracks(self, test_db, rb5_xml_path):
        """Test importing Rekordbox 5 XML and verifying track count."""
        assert rb5_xml_path.exists(), f"Test file not found: {rb5_xml_path}"

        rekordbox_xml.import_xml(test_db, rb5_xml_path)

        # Query tracks table
        cursor = test_db.execute(
            "SELECT COUNT(*) FROM tracks WHERE in_rekordbox = 1"
        )
        count = cursor.fetchone()[0]
        assert count == 6, f"Expected 6 tracks, got {count}"

    def test_rb5_xml_import_track_metadata(self, test_db, rb5_xml_path):
        """Test that track metadata is imported correctly."""
        rekordbox_xml.import_xml(test_db, rb5_xml_path)

        # Check for Demo Track 1
        cursor = test_db.execute(
            "SELECT title, artist, bpm, label FROM tracks WHERE title = 'Demo Track 1'"
        )
        row = cursor.fetchone()
        assert row is not None, "Demo Track 1 not found"
        title, artist, bpm, label = row
        assert artist == "Loopmasters", f"Expected artist 'Loopmasters', got {artist}"
        assert bpm == 128.0, f"Expected BPM 128.0, got {bpm}"
        assert label == "Loopmasters", f"Expected label 'Loopmasters', got {label}"

    def test_rb5_xml_import_cue_points(self, test_db, rb5_xml_path):
        """Test that cue points are imported correctly."""
        rekordbox_xml.import_xml(test_db, rb5_xml_path)

        # Demo Track 1 has 4 memory cues
        cursor = test_db.execute(
            """
            SELECT COUNT(*) FROM cue_points
            WHERE track_id = (SELECT id FROM tracks WHERE title = 'Demo Track 1')
            """
        )
        count = cursor.fetchone()[0]
        assert count == 4, f"Expected 4 cue points for Demo Track 1, got {count}"

    def test_rb5_xml_import_cue_positions(self, test_db, rb5_xml_path):
        """Test that cue point positions are accurate."""
        rekordbox_xml.import_xml(test_db, rb5_xml_path)

        # Check first cue point position (should be 0.025 seconds)
        cursor = test_db.execute(
            """
            SELECT position_sec FROM cue_points
            WHERE track_id = (SELECT id FROM tracks WHERE title = 'Demo Track 1')
            ORDER BY position_sec
            LIMIT 1
            """
        )
        row = cursor.fetchone()
        assert row is not None, "No cue points found"
        position = row[0]
        assert abs(position - 0.025) < 0.001, f"Expected position ~0.025, got {position}"

    def test_rb5_xml_import_playlists(self, test_db, rb5_xml_path):
        """Test that playlists are imported correctly."""
        rekordbox_xml.import_xml(test_db, rb5_xml_path)

        # RB5 has 2 playlists: "Sub Playlist" and "Playlist1"
        # Each should have 2 tracks (Demo Track 1 and Demo Track 2)
        cursor = test_db.execute(
            """
            SELECT COUNT(DISTINCT playlist_name) FROM playlists
            """
        )
        count = cursor.fetchone()[0]
        assert count == 2, f"Expected 2 playlists, got {count}"

        # Check that each playlist has 2 tracks
        cursor = test_db.execute(
            """
            SELECT playlist_name, COUNT(*) as track_count
            FROM playlists
            GROUP BY playlist_name
            ORDER BY playlist_name
            """
        )
        rows = cursor.fetchall()
        assert len(rows) == 2, f"Expected 2 playlists, got {len(rows)}"
        for playlist_name, track_count in rows:
            assert track_count == 2, (
                f"Playlist '{playlist_name}' should have 2 tracks, got {track_count}"
            )

    def test_rb6_xml_import_tracks(self, test_db, rb6_xml_path):
        """Test importing Rekordbox 6 XML and verifying track count."""
        assert rb6_xml_path.exists(), f"Test file not found: {rb6_xml_path}"

        rekordbox_xml.import_xml(test_db, rb6_xml_path)

        cursor = test_db.execute(
            "SELECT COUNT(*) FROM tracks WHERE in_rekordbox = 1"
        )
        count = cursor.fetchone()[0]
        assert count == 6, f"Expected 6 tracks, got {count}"

    def test_rb6_xml_import_tonality(self, test_db, rb6_xml_path):
        """Test that Rekordbox 6 tonality (musical_key) is imported."""
        rekordbox_xml.import_xml(test_db, rb6_xml_path)

        # RB6 Demo Track 1 has Tonality="Fm"
        cursor = test_db.execute(
            "SELECT musical_key FROM tracks WHERE title = 'Demo Track 1'"
        )
        row = cursor.fetchone()
        assert row is not None, "Demo Track 1 not found"
        musical_key = row[0]
        assert musical_key == "Fm", f"Expected musical_key 'Fm', got {musical_key}"

    def test_rb5_xml_filename_lower_matching(self, test_db, rb5_xml_path):
        """Test that filename matching works via filename_lower."""
        # First insert a track via scanner with a filename
        # Then import XML and verify it matches via filename_lower
        test_db.execute(
            """
            INSERT INTO tracks (filepath, filename, filename_lower, source_label, title, artist)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "/Volumes/USB/Music/Demo Track 1.mp3",
                "Demo Track 1.mp3",
                "demo track 1.mp3",
                "USB1",
                "From Scanner",
                "Unknown",
            ),
        )
        test_db.commit()

        # Import XML with different path format
        rekordbox_xml.import_xml(test_db, rb5_xml_path)

        # Verify the track was updated with rekordbox data
        cursor = test_db.execute(
            """
            SELECT artist, in_rekordbox FROM tracks
            WHERE filename_lower = 'demo track 1.mp3'
            """
        )
        row = cursor.fetchone()
        assert row is not None, "Track not found via filename_lower"
        artist, in_rekordbox = row
        # Artist should be updated from XML
        assert artist == "Loopmasters", f"Expected artist 'Loopmasters', got {artist}"
        assert in_rekordbox == 1, f"Expected in_rekordbox=1, got {in_rekordbox}"

    def test_rb5_xml_nonexistent_file(self, test_db):
        """Test error handling for nonexistent XML file."""
        nonexistent = Path("/nonexistent/path/database.xml")
        with pytest.raises(FileNotFoundError):
            rekordbox_xml.import_xml(test_db, nonexistent)

    def test_rb5_xml_import_comments(self, test_db, rb5_xml_path):
        """Test that Comments field is imported."""
        rekordbox_xml.import_xml(test_db, rb5_xml_path)

        # Demo Track 1 has Comments="Tracks by www.loopmasters.com"
        cursor = test_db.execute(
            "SELECT comments FROM tracks WHERE title = 'Demo Track 1'"
        )
        row = cursor.fetchone()
        assert row is not None
        comments = row[0]
        assert "loopmasters.com" in comments.lower(), f"Expected comment with URL, got {comments}"
