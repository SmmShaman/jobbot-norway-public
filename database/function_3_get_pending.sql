-- ============================================================
-- Function 3: Get jobs pending Skyvern processing
-- ============================================================

CREATE OR REPLACE FUNCTION get_pending_skyvern_jobs(
    p_user_id UUID,
    p_limit INTEGER DEFAULT 10
) RETURNS TABLE (
    id UUID,
    url TEXT,
    finnkode TEXT,
    title TEXT,
    scan_task_id UUID
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        jobs.id,
        jobs.url,
        jobs.finnkode,
        jobs.title,
        jobs.scan_task_id
    FROM jobs
    WHERE
        jobs.user_id = p_user_id
        AND jobs.skyvern_status = 'PENDING'
        AND jobs.source = 'FINN'
    ORDER BY jobs.created_at DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_pending_skyvern_jobs IS 'Retrieves jobs that are pending Skyvern content extraction';
