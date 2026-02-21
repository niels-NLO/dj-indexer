-- Rekordbox coverage by folder
-- Shows what percentage of each folder is in Rekordbox
-- Useful for identifying gaps in preparation
-- Usage: dj-indexer query --query-file queries/folder_rekordbox_coverage.sql

SELECT
    DIRNAME(filepath) as folder,
    COUNT(*) as total_tracks,
    SUM(CASE WHEN in_rekordbox=1 THEN 1 ELSE 0 END) as rb_tracks,
    ROUND(100.0 * SUM(CASE WHEN in_rekordbox=1 THEN 1 ELSE 0 END) / COUNT(*), 1) as percent_prepared
FROM tracks
GROUP BY DIRNAME(filepath)
ORDER BY percent_prepared ASC, total_tracks DESC
LIMIT 50;
