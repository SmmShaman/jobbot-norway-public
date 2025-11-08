# 🚀 Швидке встановлення SQL функцій

## Крок 1: Відкрийте Supabase SQL Editor

Перейдіть за посиланням:
```
https://supabase.com/dashboard/project/ptrmidlhfdbybxmyovtm/sql/new
```

## Крок 2: Скопіюйте та виконайте SQL

Скопіюйте **весь код нижче** та вставте в SQL Editor, потім натисніть **Run**:

```sql
-- ============================================================
-- FINN.no Link Extraction Function
-- Extracts individual job URLs from FINN.no search results HTML
-- ============================================================

-- Function to extract FINN.no job links from HTML content
CREATE OR REPLACE FUNCTION extract_finn_job_links(html_content TEXT)
RETURNS TABLE (
    url TEXT,
    finnkode TEXT,
    title TEXT
) AS $$
DECLARE
    pattern TEXT := 'href="(https?://[^"]*finnkode=\d+)"';
    matches TEXT[];
    match_url TEXT;
    code_match TEXT;
BEGIN
    -- Find all URLs with finnkode in the HTML
    FOR match_url IN
        SELECT regexp_matches[1]
        FROM regexp_matches(html_content, pattern, 'gi') AS regexp_matches
    LOOP
        -- Ensure URL is absolute
        IF match_url NOT LIKE 'http%' THEN
            match_url := 'https://www.finn.no' ||
                        CASE
                            WHEN match_url LIKE '/%' THEN match_url
                            ELSE '/' || match_url
                        END;
        END IF;

        -- Extract finnkode from URL
        code_match := substring(match_url FROM 'finnkode=(\d+)');

        IF code_match IS NOT NULL THEN
            RETURN QUERY SELECT
                match_url,
                code_match,
                'Job ' || code_match;
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
                'FINN Company', -- Placeholder, will be updated by Skyvern
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

COMMENT ON FUNCTION extract_finn_job_links IS 'Extracts individual job URLs with finnkode from FINN.no search results HTML';
COMMENT ON FUNCTION create_jobs_from_finn_links IS 'Creates job entries from extracted FINN.no links, handling duplicates automatically';
COMMENT ON FUNCTION get_pending_skyvern_jobs IS 'Retrieves jobs that are pending Skyvern content extraction';
```

## Крок 3: Перевірте встановлення

Після виконання SQL, перевірте що функції створились:

```sql
-- Перевірка функцій
SELECT routine_name
FROM information_schema.routines
WHERE routine_schema = 'public'
  AND routine_name LIKE '%finn%';
```

Має показати:
- `extract_finn_job_links`
- `create_jobs_from_finn_links`
- `get_pending_skyvern_jobs`

## Крок 4: Тестування

Протестуйте функцію екстракції:

```sql
-- Тест витягування лінків
SELECT * FROM extract_finn_job_links('
    <a href="https://www.finn.no/job/fulltime/ad.html?finnkode=123456">Developer</a>
    <a href="/job/parttime/ad.html?finnkode=789012">Designer</a>
');
```

## ✅ Готово!

Тепер можете запустити Worker v2:

```bash
cd ~/jobbot-norway-public/worker
python3 worker_v2.py
```

## 🔗 Корисні посилання

- **SQL Editor**: https://supabase.com/dashboard/project/ptrmidlhfdbybxmyovtm/sql/new
- **Database Functions**: https://supabase.com/dashboard/project/ptrmidlhfdbybxmyovtm/database/functions
- **Documentation**: `MIGRATION_V2.md`
- **Worker README**: `worker/README_V2.md`
