-- ============================================================
-- JobBot Norway - Complete Database Schema
-- All tables required for the application
-- ============================================================

-- ============================================================
-- 1. PROFILES TABLE
-- User profile information
-- ============================================================
CREATE TABLE IF NOT EXISTS profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    full_name TEXT,
    email TEXT,
    phone TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- 2. USER SETTINGS TABLE
-- User preferences and search configurations
-- ============================================================
CREATE TABLE IF NOT EXISTS user_settings (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL UNIQUE REFERENCES auth.users(id) ON DELETE CASCADE,

    -- Search URLs
    nav_search_urls TEXT[] DEFAULT ARRAY[]::TEXT[],
    finn_search_urls TEXT[] DEFAULT ARRAY[]::TEXT[],

    -- AI/Automation settings
    min_relevance_score INTEGER DEFAULT 70,
    auto_apply_threshold INTEGER DEFAULT 85,
    max_applications_per_day INTEGER DEFAULT 5,
    require_manual_approval BOOLEAN DEFAULT true,

    -- Notifications
    telegram_enabled BOOLEAN DEFAULT false,
    telegram_chat_id TEXT,

    -- Unified profile (JSON with skills, experience, etc.)
    unified_profile JSONB DEFAULT '{}'::JSONB,

    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- 3. JOBS TABLE
-- Scraped and analyzed job listings
-- ============================================================
CREATE TABLE IF NOT EXISTS jobs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    -- Job details
    title TEXT NOT NULL,
    company TEXT NOT NULL,
    location TEXT,
    description TEXT,
    url TEXT NOT NULL,
    source TEXT NOT NULL CHECK (source IN ('NAV', 'FINN')),

    -- AI Analysis
    relevance_score INTEGER DEFAULT 0,
    ai_analysis JSONB DEFAULT '{}'::JSONB,

    -- Status
    status TEXT NOT NULL DEFAULT 'NEW' CHECK (status IN ('NEW', 'ANALYZED', 'APPROVED', 'APPLIED', 'REJECTED')),

    -- Timestamps
    discovered_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    applied_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Unique constraint to prevent duplicate jobs
    UNIQUE(user_id, url)
);

-- ============================================================
-- 4. APPLICATIONS TABLE
-- Track submitted job applications
-- ============================================================
CREATE TABLE IF NOT EXISTS applications (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,

    -- Application details
    status TEXT NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'SUBMITTED', 'FAILED', 'CONFIRMED')),
    submission_method TEXT CHECK (submission_method IN ('SKYVERN', 'MANUAL', 'EMAIL')),

    -- Screenshots and evidence
    screenshot_url TEXT,
    confirmation_data JSONB DEFAULT '{}'::JSONB,

    -- Error tracking
    error_message TEXT,

    -- NAV reporting
    nav_reported BOOLEAN DEFAULT false,
    nav_reported_at TIMESTAMPTZ,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- 5. COVER LETTERS TABLE
-- AI-generated cover letters for applications
-- ============================================================
CREATE TABLE IF NOT EXISTS cover_letters (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,

    -- Cover letter content
    content TEXT NOT NULL,
    language TEXT DEFAULT 'norwegian' CHECK (language IN ('norwegian', 'english')),

    -- Generation metadata
    generated_by TEXT DEFAULT 'ai',
    generation_prompt TEXT,

    -- Status
    approved BOOLEAN DEFAULT false,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(job_id)
);

-- ============================================================
-- INDEXES for better query performance
-- ============================================================

-- Profiles
CREATE INDEX IF NOT EXISTS idx_profiles_email ON profiles(email);

-- User settings
CREATE INDEX IF NOT EXISTS idx_user_settings_user_id ON user_settings(user_id);

-- Jobs
CREATE INDEX IF NOT EXISTS idx_jobs_user_id ON jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_relevance_score ON jobs(relevance_score DESC);
CREATE INDEX IF NOT EXISTS idx_jobs_discovered_at ON jobs(discovered_at DESC);
CREATE INDEX IF NOT EXISTS idx_jobs_user_status ON jobs(user_id, status);

-- Applications
CREATE INDEX IF NOT EXISTS idx_applications_user_id ON applications(user_id);
CREATE INDEX IF NOT EXISTS idx_applications_job_id ON applications(job_id);
CREATE INDEX IF NOT EXISTS idx_applications_status ON applications(status);
CREATE INDEX IF NOT EXISTS idx_applications_created_at ON applications(created_at DESC);

-- Cover letters
CREATE INDEX IF NOT EXISTS idx_cover_letters_user_id ON cover_letters(user_id);
CREATE INDEX IF NOT EXISTS idx_cover_letters_job_id ON cover_letters(job_id);

-- ============================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- ============================================================

-- Enable RLS on all tables
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE applications ENABLE ROW LEVEL SECURITY;
ALTER TABLE cover_letters ENABLE ROW LEVEL SECURITY;

-- Profiles policies
CREATE POLICY "Users can view own profile" ON profiles FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Users can insert own profile" ON profiles FOR INSERT WITH CHECK (auth.uid() = id);
CREATE POLICY "Users can update own profile" ON profiles FOR UPDATE USING (auth.uid() = id);

-- User settings policies
CREATE POLICY "Users can view own settings" ON user_settings FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own settings" ON user_settings FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own settings" ON user_settings FOR UPDATE USING (auth.uid() = user_id);

-- Jobs policies
CREATE POLICY "Users can view own jobs" ON jobs FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own jobs" ON jobs FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own jobs" ON jobs FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete own jobs" ON jobs FOR DELETE USING (auth.uid() = user_id);

-- Applications policies
CREATE POLICY "Users can view own applications" ON applications FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own applications" ON applications FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own applications" ON applications FOR UPDATE USING (auth.uid() = user_id);

-- Cover letters policies
CREATE POLICY "Users can view own cover letters" ON cover_letters FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own cover letters" ON cover_letters FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own cover letters" ON cover_letters FOR UPDATE USING (auth.uid() = user_id);

-- ============================================================
-- AUTOMATIC UPDATED_AT TRIGGERS
-- ============================================================

-- Profiles
DROP TRIGGER IF EXISTS update_profiles_updated_at ON profiles;
CREATE TRIGGER update_profiles_updated_at
    BEFORE UPDATE ON profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- User settings
DROP TRIGGER IF EXISTS update_user_settings_updated_at ON user_settings;
CREATE TRIGGER update_user_settings_updated_at
    BEFORE UPDATE ON user_settings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Jobs
DROP TRIGGER IF EXISTS update_jobs_updated_at ON jobs;
CREATE TRIGGER update_jobs_updated_at
    BEFORE UPDATE ON jobs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Applications
DROP TRIGGER IF EXISTS update_applications_updated_at ON applications;
CREATE TRIGGER update_applications_updated_at
    BEFORE UPDATE ON applications
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Cover letters
DROP TRIGGER IF EXISTS update_cover_letters_updated_at ON cover_letters;
CREATE TRIGGER update_cover_letters_updated_at
    BEFORE UPDATE ON cover_letters
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- AUTOMATIC PROFILE CREATION ON USER SIGNUP
-- ============================================================

CREATE OR REPLACE FUNCTION initialize_user_profile()
RETURNS TRIGGER AS $$
BEGIN
    -- Create profile
    INSERT INTO profiles (id, email, full_name)
    VALUES (
        NEW.id,
        NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'full_name', '')
    )
    ON CONFLICT (id) DO NOTHING;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to create profile on user signup
DROP TRIGGER IF EXISTS on_auth_user_created_profile ON auth.users;
CREATE TRIGGER on_auth_user_created_profile
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION initialize_user_profile();

-- ============================================================
-- STORAGE BUCKETS
-- ============================================================

-- Create storage buckets (if not exist)
-- Note: Run these separately in Supabase Storage UI if needed:
-- 1. resumes (for PDF resumes)
-- 2. screenshots (for application screenshots)

-- ============================================================
-- VERIFICATION
-- ============================================================

-- List all tables
SELECT 'Tables created:' as info;
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
AND table_type = 'BASE TABLE'
ORDER BY table_name;

-- List all RLS policies
SELECT 'RLS policies created:' as info;
SELECT tablename, policyname
FROM pg_policies
WHERE schemaname = 'public'
ORDER BY tablename, policyname;
