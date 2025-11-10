-- ============================================================
-- FINN.no Link Extraction Function
-- Extracts individual job URLs from FINN.no search results HTML
-- Updated to support new FINN.no URL format: /job/ad/123456789
-- ============================================================

-- Function to extract FINN.no job links from HTML content
CREATE OR REPLACE FUNCTION extract_finn_job_links(html_content TEXT)
RETURNS TABLE (
    url TEXT,
    finnkode TEXT,
    title TEXT
) AS $$
DECLARE
    match RECORD;
    full_url TEXT;
    job_id TEXT;
BEGIN
    -- Pattern 1: Absolute URL with new format (https://www.finn.no/job/ad/436409474)
    FOR match IN
        SELECT
            regexp_matches[1] as matched_url,
            regexp_matches[2] as id
        FROM regexp_matches(html_content, 'href="(https://www\.finn\.no/job/[^"]*?(\d{6,}))"', 'gi') AS regexp_matches
    LOOP
        job_id := match.id;
        full_url := match.matched_url;

        IF job_id IS NOT NULL THEN
            RETURN QUERY SELECT full_url, job_id, 'Job ' || job_id;
        END IF;
    END LOOP;

    -- Pattern 2: Relative URL (/job/ad/436409474)
    FOR match IN
        SELECT
            regexp_matches[1] as path,
            regexp_matches[2] as id
        FROM regexp_matches(html_content, 'href="(/job/[^"]*?(\d{6,}))"', 'gi') AS regexp_matches
    LOOP
        job_id := match.id;
        full_url := 'https://www.finn.no' || match.path;

        IF job_id IS NOT NULL THEN
            RETURN QUERY SELECT full_url, job_id, 'Job ' || job_id;
        END IF;
    END LOOP;

    -- Pattern 3: Old format with finnkode parameter (fallback)
    FOR match IN
        SELECT
            regexp_matches[1] as matched_url
        FROM regexp_matches(html_content, 'href="(https?://[^"]*finnkode=(\d+))"', 'gi') AS regexp_matches
    LOOP
        full_url := match.matched_url;
        job_id := substring(full_url FROM 'finnkode=(\d+)');

        IF job_id IS NOT NULL THEN
            RETURN QUERY SELECT full_url, job_id, 'Job ' || job_id;
        END IF;
    END LOOP;

    RETURN;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- Helper function to create job entries from extracted links
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
                'FINN.no', -- Updated to match NOT NULL constraint
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

-- ============================================================
-- Function to get jobs pending Skyvern processing
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

-- ============================================================
-- Comments
-- ============================================================

COMMENT ON FUNCTION extract_finn_job_links IS 'Extracts individual job URLs with finnkode from FINN.no search results HTML - supports new /job/ad/ID format';
COMMENT ON FUNCTION create_jobs_from_finn_links IS 'Creates job entries from extracted FINN.no links, handling duplicates automatically';
COMMENT ON FUNCTION get_pending_skyvern_jobs IS 'Retrieves jobs that are pending Skyvern content extraction';
