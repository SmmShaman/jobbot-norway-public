-- ============================================================
-- DEPLOY ALL CRITICAL TABLES - Single Script Deployment
-- Run this ONCE in Supabase SQL Editor to set up minimum viable system
-- ============================================================

-- This script creates all critical tables needed for basic operation
-- in the correct order (respecting dependencies)

-- ============================================================
-- STEP 1: Create update_updated_at_column function (if not exists)
-- ============================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- ============================================================
-- STEP 2: Create profiles table
-- ============================================================

CREATE TABLE IF NOT EXISTS profiles (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    full_name TEXT,
    email TEXT,
    phone TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view own profile" ON profiles;
DROP POLICY IF EXISTS "Users can insert own profile" ON profiles;
DROP POLICY IF EXISTS "Users can update own profile" ON profiles;

CREATE POLICY "Users can view own profile"
    ON profiles FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own profile"
    ON profiles FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own profile"
    ON profiles FOR UPDATE USING (auth.uid() = user_id);

DROP TRIGGER IF EXISTS update_profiles_updated_at ON profiles;
CREATE TRIGGER update_profiles_updated_at
    BEFORE UPDATE ON profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- STEP 3: Create user_settings table
-- ============================================================

CREATE TABLE IF NOT EXISTS user_settings (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    finn_search_urls TEXT[] DEFAULT '{}',
    nav_search_urls TEXT[] DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE user_settings ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view own settings" ON user_settings;
DROP POLICY IF EXISTS "Users can insert own settings" ON user_settings;
DROP POLICY IF EXISTS "Users can update own settings" ON user_settings;

CREATE POLICY "Users can view own settings"
    ON user_settings FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own settings"
    ON user_settings FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own settings"
    ON user_settings FOR UPDATE USING (auth.uid() = user_id);

DROP TRIGGER IF EXISTS update_user_settings_updated_at ON user_settings;
CREATE TRIGGER update_user_settings_updated_at
    BEFORE UPDATE ON user_settings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- STEP 4: Create scan_tasks table
-- ============================================================

CREATE TABLE IF NOT EXISTS scan_tasks (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    source TEXT NOT NULL CHECK (source IN ('FINN', 'NAV')),
    scan_type TEXT NOT NULL CHECK (scan_type IN ('MANUAL', 'SCHEDULED', 'RETRY')),
    status TEXT NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED')),
    worker_id TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    jobs_found INTEGER DEFAULT 0,
    jobs_saved INTEGER DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_scan_tasks_user_id ON scan_tasks(user_id);
CREATE INDEX IF NOT EXISTS idx_scan_tasks_status ON scan_tasks(status);
CREATE INDEX IF NOT EXISTS idx_scan_tasks_created_at ON scan_tasks(created_at DESC);

ALTER TABLE scan_tasks ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view own scan tasks" ON scan_tasks;
DROP POLICY IF EXISTS "Users can insert own scan tasks" ON scan_tasks;
DROP POLICY IF EXISTS "Service role can view all scan tasks" ON scan_tasks;
DROP POLICY IF EXISTS "Service role can update all scan tasks" ON scan_tasks;

CREATE POLICY "Users can view own scan tasks"
    ON scan_tasks FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own scan tasks"
    ON scan_tasks FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Service role can view all scan tasks"
    ON scan_tasks FOR SELECT TO service_role USING (true);

CREATE POLICY "Service role can update all scan tasks"
    ON scan_tasks FOR UPDATE TO service_role USING (true);

DROP TRIGGER IF EXISTS update_scan_tasks_updated_at ON scan_tasks;
CREATE TRIGGER update_scan_tasks_updated_at
    BEFORE UPDATE ON scan_tasks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- STEP 5: Ensure jobs table has finnkode column
-- ============================================================

ALTER TABLE jobs ADD COLUMN IF NOT EXISTS finnkode TEXT;
CREATE INDEX IF NOT EXISTS idx_jobs_finnkode ON jobs(finnkode);

-- ============================================================
-- STEP 6: Create/Update SQL Functions
-- ============================================================

-- Function to extract FINN.no job links from HTML
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

    RETURN;
END;
$$ LANGUAGE plpgsql;

-- Function to create jobs from extracted links
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

-- Function to get pending Skyvern jobs
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
-- VERIFICATION
-- ============================================================

-- Test the extraction function
DO $$
DECLARE
    test_result RECORD;
BEGIN
    RAISE NOTICE '=== TESTING extract_finn_job_links ===';
    FOR test_result IN
        SELECT * FROM extract_finn_job_links('<a href="https://www.finn.no/job/ad/123456789">Test Job</a>')
    LOOP
        RAISE NOTICE 'Found: % (finnkode: %)', test_result.url, test_result.finnkode;
    END LOOP;
END $$;

-- ============================================================
-- SUCCESS MESSAGE
-- ============================================================

DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '========================================';
    RAISE NOTICE '✅ ALL CRITICAL TABLES CREATED';
    RAISE NOTICE '========================================';
    RAISE NOTICE '';
    RAISE NOTICE '✅ profiles';
    RAISE NOTICE '✅ user_settings';
    RAISE NOTICE '✅ scan_tasks';
    RAISE NOTICE '✅ jobs (finnkode column added)';
    RAISE NOTICE '✅ extract_finn_job_links()';
    RAISE NOTICE '✅ create_jobs_from_finn_links()';
    RAISE NOTICE '✅ get_pending_skyvern_jobs()';
    RAISE NOTICE '';
    RAISE NOTICE 'Next steps:';
    RAISE NOTICE '1. Go to Dashboard → Settings';
    RAISE NOTICE '2. Add FINN.no search URL';
    RAISE NOTICE '3. Click "Scan Now"';
    RAISE NOTICE '4. Check Jobs table for results';
    RAISE NOTICE '';
END $$;
