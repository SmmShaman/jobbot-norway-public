-- ============================================================
-- Function 1: Extract FINN.no job links from HTML
-- ============================================================

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

COMMENT ON FUNCTION extract_finn_job_links IS 'Extracts individual job URLs with finnkode from FINN.no search results HTML - supports new /job/ad/ID format';
