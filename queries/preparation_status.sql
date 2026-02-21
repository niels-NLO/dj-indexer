-- DJ Preparation Status Report
-- Shows which folders are ready for DJing (have Rekordbox cues)
-- Highlights folders that need work
-- Usage: dj-indexer query --query-file queries/preparation_status.sql

SELECT
    source_label,
    DIRNAME(filepath) as folder,
    COUNT(*) as total_tracks,
    SUM(CASE WHEN in_rekordbox=1 THEN 1 ELSE 0 END) as in_rekordbox,
    SUM(CASE WHEN in_rekordbox=0 THEN 1 ELSE 0 END) as not_in_rekordbox,
    ROUND(100.0 * SUM(CASE WHEN in_rekordbox=1 THEN 1 ELSE 0 END) / COUNT(*), 1) as percent_ready,
    CASE
        WHEN ROUND(100.0 * SUM(CASE WHEN in_rekordbox=1 THEN 1 ELSE 0 END) / COUNT(*), 1) = 100 THEN 'READY'
        WHEN ROUND(100.0 * SUM(CASE WHEN in_rekordbox=1 THEN 1 ELSE 0 END) / COUNT(*), 1) >= 80 THEN 'MOSTLY READY'
        WHEN ROUND(100.0 * SUM(CASE WHEN in_rekordbox=1 THEN 1 ELSE 0 END) / COUNT(*), 1) >= 50 THEN 'PARTIAL'
        ELSE 'NEEDS WORK'
    END as status
FROM tracks
GROUP BY source_label, DIRNAME(filepath)
ORDER BY percent_ready DESC, total_tracks DESC;
