-- ============================================================
-- COMPLETE SYSTEM DEPLOYMENT - From Scratch
-- Run this ONCE in Supabase SQL Editor to create entire database
-- Safe to run multiple times (uses IF NOT EXISTS)
-- ============================================================

-- ============================================================
-- STEP 1: Create helper function
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

CREATE INDEX IF NOT EXISTS idx_profiles_user_id ON profiles(user_id);

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

CREATE INDEX IF NOT EXISTS idx_user_settings_user_id ON user_settings(user_id);

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
-- STEP 5: Create jobs table (MUST BE AFTER scan_tasks!)
-- ============================================================

CREATE TABLE IF NOT EXISTS jobs (
    -- Primary identifiers
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    scan_task_id UUID REFERENCES scan_tasks(id) ON DELETE SET NULL,

    -- Core job information
    title TEXT NOT NULL,
    company TEXT NOT NULL,
    location TEXT,
    url TEXT NOT NULL,
    source TEXT NOT NULL CHECK (source IN ('FINN', 'NAV')),

    -- Job details
    description TEXT,
    requirements TEXT[],
    responsibilities TEXT[],
    benefits TEXT[],

    -- Contact information
    contact_name TEXT,
    contact_email TEXT,
    contact_phone TEXT,

    -- Address details
    address TEXT,
    city TEXT,
    postalCode TEXT,
    county TEXT,
    country TEXT DEFAULT 'NORGE',

    -- Employment details
    employment_type TEXT,
    extent TEXT,
    salary_range TEXT,
    start_date TEXT,
    deadline TIMESTAMPTZ,

    -- Source-specific fields
    finnkode TEXT,
    application_url TEXT,

    -- Skyvern processing
    skyvern_status TEXT CHECK (skyvern_status IN ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED')),
    recording_url TEXT,
    task_id TEXT,
    processing_details JSONB,

    -- Processing status
    status TEXT NOT NULL DEFAULT 'NEW' CHECK (status IN ('NEW', 'REVIEWED', 'RELEVANT', 'NOT_RELEVANT', 'APPLIED', 'REJECTED', 'ARCHIVED')),
    is_processed BOOLEAN DEFAULT FALSE,
    _skip BOOLEAN DEFAULT FALSE,
    _skip_reason TEXT,

    -- Timestamps
    posted_date TIMESTAMPTZ,
    scraped_at TIMESTAMPTZ DEFAULT NOW(),
    sistEndret TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Unique constraint
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'unique_user_job_url'
        AND conrelid = 'jobs'::regclass
    ) THEN
        ALTER TABLE jobs ADD CONSTRAINT unique_user_job_url UNIQUE (user_id, url);
    END IF;
END $$;

-- Indexes
CREATE INDEX IF NOT EXISTS idx_jobs_user_id ON jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_jobs_scan_task_id ON jobs(scan_task_id);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_source ON jobs(source);
CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_jobs_url ON jobs(url);
CREATE INDEX IF NOT EXISTS idx_jobs_user_status ON jobs(user_id, status);
CREATE INDEX IF NOT EXISTS idx_jobs_finnkode ON jobs(finnkode);

-- RLS
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view own jobs" ON jobs;
DROP POLICY IF EXISTS "Users can insert own jobs" ON jobs;
DROP POLICY IF EXISTS "Users can update own jobs" ON jobs;
DROP POLICY IF EXISTS "Users can delete own jobs" ON jobs;

CREATE POLICY "Users can view own jobs"
    ON jobs FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own jobs"
    ON jobs FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own jobs"
    ON jobs FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own jobs"
    ON jobs FOR DELETE USING (auth.uid() = user_id);

-- Trigger
DROP TRIGGER IF EXISTS update_jobs_updated_at ON jobs;
CREATE TRIGGER update_jobs_updated_at
    BEFORE UPDATE ON jobs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- STEP 6: Create SQL Functions
-- ============================================================

-- Extract FINN.no job links from HTML
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

-- Create jobs from extracted links
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

-- Get pending Skyvern jobs
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
-- STEP 7: Verification & Testing
-- ============================================================

DO $$
DECLARE
    test_result RECORD;
    table_count INTEGER;
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '========================================';
    RAISE NOTICE '🔍 VERIFYING DEPLOYMENT';
    RAISE NOTICE '========================================';
    RAISE NOTICE '';

    -- Check tables
    SELECT COUNT(*) INTO table_count
    FROM information_schema.tables
    WHERE table_schema = 'public'
    AND table_name IN ('profiles', 'user_settings', 'scan_tasks', 'jobs');

    RAISE NOTICE '✅ Tables created: % of 4', table_count;

    -- Test function
    RAISE NOTICE '';
    RAISE NOTICE '🧪 Testing extract_finn_job_links function:';
    FOR test_result IN
        SELECT * FROM extract_finn_job_links('<a href="https://www.finn.no/job/ad/123456789">Test Job</a>')
    LOOP
        RAISE NOTICE '  ✅ Found: % (finnkode: %)', test_result.url, test_result.finnkode;
    END LOOP;

    RAISE NOTICE '';
    RAISE NOTICE '========================================';
    RAISE NOTICE '✅ DEPLOYMENT COMPLETE';
    RAISE NOTICE '========================================';
    RAISE NOTICE '';
    RAISE NOTICE 'Created:';
    RAISE NOTICE '  ✅ profiles table';
    RAISE NOTICE '  ✅ user_settings table';
    RAISE NOTICE '  ✅ scan_tasks table';
    RAISE NOTICE '  ✅ jobs table (with finnkode column)';
    RAISE NOTICE '  ✅ extract_finn_job_links() function';
    RAISE NOTICE '  ✅ create_jobs_from_finn_links() function';
    RAISE NOTICE '  ✅ get_pending_skyvern_jobs() function';
    RAISE NOTICE '';
    RAISE NOTICE '🎯 Next steps:';
    RAISE NOTICE '  1. Go to Dashboard → Settings';
    RAISE NOTICE '  2. Add a FINN.no search URL';
    RAISE NOTICE '  3. Click "Scan Now"';
    RAISE NOTICE '  4. Wait 10-30 seconds';
    RAISE NOTICE '  5. Check Jobs table for results';
    RAISE NOTICE '';
END $$;
