-- ============================================================
-- Complete Jobs Table Schema with Duplicate Prevention
-- FIXED VERSION - Safe to run multiple times
-- ============================================================

-- First, drop the table if you want to start fresh (OPTIONAL, COMMENT OUT IF KEEPING DATA)
-- DROP TABLE IF EXISTS jobs CASCADE;

-- Create the jobs table
CREATE TABLE IF NOT EXISTS jobs (
    -- Primary identifiers
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    scan_task_id UUID REFERENCES scan_tasks(id) ON DELETE SET NULL,

    -- Core job information
    title TEXT NOT NULL,
    company TEXT NOT NULL,
    location TEXT,
    url TEXT NOT NULL, -- Original job posting URL (used for duplicate detection)
    source TEXT NOT NULL CHECK (source IN ('FINN', 'NAV')),

    -- Job details
    description TEXT,
    requirements TEXT[], -- Array of requirement strings
    responsibilities TEXT[], -- Array of responsibility strings
    benefits TEXT[], -- Array of benefit strings

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
    employment_type TEXT, -- fast, vikariat, etc.
    extent TEXT, -- heltid, deltid, percentage
    salary_range TEXT,
    start_date TEXT,
    deadline TIMESTAMPTZ, -- Application deadline

    -- Source-specific fields
    finnkode TEXT, -- FINN.no job code
    application_url TEXT, -- Direct application link

    -- Skyvern processing
    skyvern_status TEXT CHECK (skyvern_status IN ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED')),
    recording_url TEXT, -- Skyvern recording/video URL
    task_id TEXT, -- Skyvern task ID
    processing_details JSONB, -- Additional Skyvern metadata

    -- Processing status
    status TEXT NOT NULL DEFAULT 'NEW' CHECK (status IN ('NEW', 'REVIEWED', 'RELEVANT', 'NOT_RELEVANT', 'APPLIED', 'REJECTED', 'ARCHIVED')),
    is_processed BOOLEAN DEFAULT FALSE,
    _skip BOOLEAN DEFAULT FALSE, -- Mark to skip this job
    _skip_reason TEXT, -- Reason for skipping

    -- Timestamps
    posted_date TIMESTAMPTZ, -- When job was originally posted
    scraped_at TIMESTAMPTZ DEFAULT NOW(), -- When we scraped it
    sistEndret TIMESTAMPTZ, -- Last modified on source (Norwegian: "last changed")
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Add unique constraint if it doesn't exist
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

-- ============================================================
-- Indexes for Performance
-- ============================================================

-- Index on user_id for fast user queries
CREATE INDEX IF NOT EXISTS idx_jobs_user_id ON jobs(user_id);

-- Index on scan_task_id for tracking which scan found which jobs
CREATE INDEX IF NOT EXISTS idx_jobs_scan_task_id ON jobs(scan_task_id);

-- Index on status for filtering
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);

-- Index on source for filtering by job board
CREATE INDEX IF NOT EXISTS idx_jobs_source ON jobs(source);

-- Index on created_at for sorting by date
CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at DESC);

-- Index on URL for duplicate detection (already covered by unique constraint but good for lookups)
CREATE INDEX IF NOT EXISTS idx_jobs_url ON jobs(url);

-- Composite index for common queries
CREATE INDEX IF NOT EXISTS idx_jobs_user_status ON jobs(user_id, status);

-- ============================================================
-- Row Level Security (RLS)
-- ============================================================

ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if recreating
DROP POLICY IF EXISTS "Users can view own jobs" ON jobs;
DROP POLICY IF EXISTS "Users can insert own jobs" ON jobs;
DROP POLICY IF EXISTS "Users can update own jobs" ON jobs;
DROP POLICY IF EXISTS "Users can delete own jobs" ON jobs;

-- Policy: Users can only view their own jobs
CREATE POLICY "Users can view own jobs"
    ON jobs FOR SELECT
    USING (auth.uid() = user_id);

-- Policy: Users can insert their own jobs
CREATE POLICY "Users can insert own jobs"
    ON jobs FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Policy: Users can update their own jobs
CREATE POLICY "Users can update own jobs"
    ON jobs FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- Policy: Users can delete their own jobs
CREATE POLICY "Users can delete own jobs"
    ON jobs FOR DELETE
    USING (auth.uid() = user_id);

-- ============================================================
-- Trigger for Updated At
-- ============================================================

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Drop trigger if exists and create new one
DROP TRIGGER IF EXISTS update_jobs_updated_at ON jobs;
CREATE TRIGGER update_jobs_updated_at
    BEFORE UPDATE ON jobs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- Verification Query
-- ============================================================

-- Run this to verify everything was created correctly:
-- SELECT
--     tablename,
--     indexname,
--     indexdef
-- FROM pg_indexes
-- WHERE tablename = 'jobs';

-- Check constraints:
-- SELECT conname, contype
-- FROM pg_constraint
-- WHERE conrelid = 'jobs'::regclass;

-- Check policies:
-- SELECT policyname, cmd, qual
-- FROM pg_policies
-- WHERE tablename = 'jobs';

-- ============================================================
-- Done!
-- ============================================================
