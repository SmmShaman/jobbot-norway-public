-- ============================================================
-- Complete Jobs Table Schema with Duplicate Prevention
-- ============================================================

-- Drop existing table if recreating (BE CAREFUL!)
-- DROP TABLE IF EXISTS jobs CASCADE;

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
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Duplicate prevention: unique constraint on user + URL
    CONSTRAINT unique_user_job_url UNIQUE (user_id, url)
);

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

-- Create trigger
DROP TRIGGER IF EXISTS update_jobs_updated_at ON jobs;
CREATE TRIGGER update_jobs_updated_at
    BEFORE UPDATE ON jobs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- Function: Upsert Job (Insert or Update on Conflict)
-- ============================================================

CREATE OR REPLACE FUNCTION upsert_job(
    p_user_id UUID,
    p_url TEXT,
    p_title TEXT,
    p_company TEXT,
    p_source TEXT,
    p_scan_task_id UUID DEFAULT NULL,
    p_location TEXT DEFAULT NULL,
    p_description TEXT DEFAULT NULL,
    p_contact_name TEXT DEFAULT NULL,
    p_contact_email TEXT DEFAULT NULL,
    p_contact_phone TEXT DEFAULT NULL,
    p_address TEXT DEFAULT NULL,
    p_city TEXT DEFAULT NULL,
    p_postal_code TEXT DEFAULT NULL,
    p_county TEXT DEFAULT NULL,
    p_country TEXT DEFAULT 'NORGE',
    p_employment_type TEXT DEFAULT NULL,
    p_extent TEXT DEFAULT NULL,
    p_salary_range TEXT DEFAULT NULL,
    p_start_date TEXT DEFAULT NULL,
    p_deadline TIMESTAMPTZ DEFAULT NULL,
    p_posted_date TIMESTAMPTZ DEFAULT NULL,
    p_finnkode TEXT DEFAULT NULL,
    p_application_url TEXT DEFAULT NULL,
    p_requirements TEXT[] DEFAULT NULL,
    p_responsibilities TEXT[] DEFAULT NULL,
    p_benefits TEXT[] DEFAULT NULL
) RETURNS UUID AS $$
DECLARE
    v_job_id UUID;
BEGIN
    -- Insert or update on conflict
    INSERT INTO jobs (
        user_id, url, title, company, source, scan_task_id,
        location, description,
        contact_name, contact_email, contact_phone,
        address, city, postalCode, county, country,
        employment_type, extent, salary_range, start_date, deadline,
        posted_date, finnkode, application_url,
        requirements, responsibilities, benefits,
        status, is_processed, scraped_at
    ) VALUES (
        p_user_id, p_url, p_title, p_company, p_source, p_scan_task_id,
        p_location, p_description,
        p_contact_name, p_contact_email, p_contact_phone,
        p_address, p_city, p_postal_code, p_county, p_country,
        p_employment_type, p_extent, p_salary_range, p_start_date, p_deadline,
        p_posted_date, p_finnkode, p_application_url,
        p_requirements, p_responsibilities, p_benefits,
        'NEW', FALSE, NOW()
    )
    ON CONFLICT (user_id, url)
    DO UPDATE SET
        -- Update only if job details changed
        title = EXCLUDED.title,
        company = EXCLUDED.company,
        description = COALESCE(EXCLUDED.description, jobs.description),
        contact_name = COALESCE(EXCLUDED.contact_name, jobs.contact_name),
        contact_email = COALESCE(EXCLUDED.contact_email, jobs.contact_email),
        contact_phone = COALESCE(EXCLUDED.contact_phone, jobs.contact_phone),
        address = COALESCE(EXCLUDED.address, jobs.address),
        city = COALESCE(EXCLUDED.city, jobs.city),
        postalCode = COALESCE(EXCLUDED.postalCode, jobs.postalCode),
        county = COALESCE(EXCLUDED.county, jobs.county),
        employment_type = COALESCE(EXCLUDED.employment_type, jobs.employment_type),
        extent = COALESCE(EXCLUDED.extent, jobs.extent),
        salary_range = COALESCE(EXCLUDED.salary_range, jobs.salary_range),
        start_date = COALESCE(EXCLUDED.start_date, jobs.start_date),
        deadline = COALESCE(EXCLUDED.deadline, jobs.deadline),
        requirements = COALESCE(EXCLUDED.requirements, jobs.requirements),
        responsibilities = COALESCE(EXCLUDED.responsibilities, jobs.responsibilities),
        benefits = COALESCE(EXCLUDED.benefits, jobs.benefits),
        sistEndret = NOW(), -- Mark as updated
        updated_at = NOW()
    RETURNING id INTO v_job_id;

    RETURN v_job_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- Comments
-- ============================================================

COMMENT ON TABLE jobs IS 'Stores all scraped job listings with full details';
COMMENT ON COLUMN jobs.url IS 'Original job posting URL - used for duplicate detection';
COMMENT ON CONSTRAINT unique_user_job_url ON jobs IS 'Prevents duplicate jobs per user based on URL';
COMMENT ON FUNCTION upsert_job IS 'Safely insert or update job, preventing duplicates by URL';
