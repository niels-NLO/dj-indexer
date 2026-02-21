-- Detailed source and folder analysis
-- Shows for each source: total tracks, RB tracks, folder breakdown
-- Usage: dj-indexer query --query-file queries/source_folder_analysis.sql

SELECT
    source_label,
    DIRNAME(filepath) as folder,
    COUNT(*) as total_count,
    SUM(CASE WHEN in_rekordbox=1 THEN 1 ELSE 0 END) as rb_count,
    SUM(CASE WHEN in_rekordbox=0 THEN 1 ELSE 0 END) as non_rb_count,
    ROUND(AVG(bpm), 1) as avg_bpm,
    COUNT(DISTINCT genre) as genre_count
FROM tracks
GROUP BY source_label, DIRNAME(filepath)
ORDER BY source_label, rb_count DESC;
