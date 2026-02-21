-- Folders with Rekordbox tracks
-- Shows only folders containing tracks marked as in_rekordbox=1
-- Usage: dj-indexer query --query-file queries/rekordbox_folders.sql

SELECT
    DIRNAME(filepath) as folder,
    COUNT(*) as total_tracks,
    COUNT(CASE WHEN in_rekordbox=1 THEN 1 END) as rb_tracks,
    ROUND(100.0 * COUNT(CASE WHEN in_rekordbox=1 THEN 1 END) / COUNT(*), 1) as percent_rb
FROM tracks
GROUP BY DIRNAME(filepath)
HAVING COUNT(CASE WHEN in_rekordbox=1 THEN 1 END) > 0
ORDER BY percent_rb DESC, rb_tracks DESC;
