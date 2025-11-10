-- ============================================================
-- Function 2: Create job entries from extracted links
-- ============================================================

CREATE OR REPLACE FUNCTION create_jobs_from_finn_links(
    p_user_id UUID,
    p_scan_task_id UUID,
    p_html_content TEXT
) RETURNS TABLE (
    job_id UUID,
    job_url TEXT,
    finnkode TEXT
) AS $$
DECLARE
    v_link RECORD;
    v_job_id UUID;
BEGIN
    -- Extract links and create job entries
    FOR v_link IN
        SELECT * FROM extract_finn_job_links(p_html_content)
    LOOP
        -- Try to insert job, skip if duplicate
        BEGIN
            INSERT INTO jobs (
                user_id,
                scan_task_id,
                url,
                finnkode,
                title,
                company,
                source,
                status,
                skyvern_status,
                scraped_at
            ) VALUES (
                p_user_id,
                p_scan_task_id,
                v_link.url,
                v_link.finnkode,
                v_link.title,
                'FINN.no',
                'FINN',
                'NEW',
                'PENDING',
                NOW()
            )
            ON CONFLICT (user_id, url) DO UPDATE
            SET
                scan_task_id = EXCLUDED.scan_task_id,
                finnkode = EXCLUDED.finnkode,
                skyvern_status = 'PENDING',
                updated_at = NOW()
            RETURNING id, url, finnkode INTO v_job_id, v_link.url, v_link.finnkode;

            RETURN QUERY SELECT v_job_id, v_link.url, v_link.finnkode;

        EXCEPTION WHEN OTHERS THEN
            -- Log error but continue processing other links
            RAISE NOTICE 'Error creating job for URL %: %', v_link.url, SQLERRM;
        END;
    END LOOP;

    RETURN;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION create_jobs_from_finn_links IS 'Creates job entries from extracted FINN.no links, handling duplicates automatically';
