-- Genre distribution by source and folder
-- Shows music genres available in each USB/source and folder
-- Usage: dj-indexer query --query-file queries/genre_by_source_folder.sql

SELECT
    source_label,
    DIRNAME(filepath) as folder,
    genre,
    COUNT(*) as track_count,
    ROUND(AVG(bpm), 1) as avg_bpm,
    COUNT(CASE WHEN in_rekordbox=1 THEN 1 END) as rb_count
FROM tracks
WHERE genre IS NOT NULL
GROUP BY source_label, DIRNAME(filepath), genre
ORDER BY source_label, folder, track_count DESC;
