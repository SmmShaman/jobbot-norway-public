-- ============================================================
-- ІНСТРУКЦІЯ:
-- 1. Відкрий: https://supabase.com/dashboard/project/ptrmidlhfdbybxmyovtm/sql/new
-- 2. Скопіюй ВСЕ ЩО НИЖЧЕ (від CREATE до кінця файлу)
-- 3. Вставай в SQL Editor
-- 4. Натисни "Run"
-- 5. Має показати: "Success. No rows returned"
-- ============================================================

-- Function 1: Extract job links from HTML
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
    -- Pattern 1: Absolute URL (https://www.finn.no/job/ad/436409474)
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

    -- Pattern 3: Old format (fallback)
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

-- Function 2: Create jobs from links
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
    FOR v_link IN
        SELECT * FROM extract_finn_job_links(p_html_content)
    LOOP
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
            RAISE NOTICE 'Error creating job for URL %: %', v_link.url, SQLERRM;
        END;
    END LOOP;

    RETURN;
END;
$$ LANGUAGE plpgsql;

-- Function 3: Get pending jobs
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
-- ГОТОВО! Після "Success" перевір що функції створено:
--
-- SELECT routine_name FROM information_schema.routines
-- WHERE routine_schema = 'public' AND routine_name LIKE '%finn%';
--
-- Має показати 3 функції!
-- ============================================================
