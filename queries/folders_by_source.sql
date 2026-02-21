-- Folder breakdown by source label
-- Shows track counts in each folder, grouped by USB/source
-- Usage: dj-indexer query --query-file queries/folders_by_source.sql

SELECT
    source_label,
    DIRNAME(filepath) as folder,
    COUNT(*) as track_count,
    COUNT(CASE WHEN in_rekordbox=1 THEN 1 END) as rb_tracks
FROM tracks
GROUP BY source_label, DIRNAME(filepath)
ORDER BY source_label, track_count DESC;
