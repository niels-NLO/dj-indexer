-- Rekordbox tracks grouped by source
-- Shows which USB drives have tracks in Rekordbox
-- Usage: dj-indexer query --query-file queries/rekordbox_by_source.sql

SELECT
    source_label,
    COUNT(*) as total_tracks,
    SUM(CASE WHEN in_rekordbox=1 THEN 1 ELSE 0 END) as rb_tracks,
    SUM(CASE WHEN in_rekordbox=0 THEN 1 ELSE 0 END) as non_rb_tracks,
    ROUND(100.0 * SUM(CASE WHEN in_rekordbox=1 THEN 1 ELSE 0 END) / COUNT(*), 1) as percent_rb
FROM tracks
GROUP BY source_label
ORDER BY percent_rb DESC, rb_tracks DESC;
