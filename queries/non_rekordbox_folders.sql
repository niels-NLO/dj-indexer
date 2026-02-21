-- Folders with non-Rekordbox tracks
-- Shows folders with tracks NOT in Rekordbox (in_rekordbox=0)
-- Useful for finding what still needs to be added to Rekordbox
-- Usage: dj-indexer query --query-file queries/non_rekordbox_folders.sql

SELECT
    DIRNAME(filepath) as folder,
    COUNT(*) as not_rb_tracks,
    source_label
FROM tracks
WHERE in_rekordbox = 0
GROUP BY DIRNAME(filepath), source_label
ORDER BY not_rb_tracks DESC, folder;
