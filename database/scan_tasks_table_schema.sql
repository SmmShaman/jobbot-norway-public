-- ============================================================
-- Scan Tasks Table Schema
-- Tracks background job scanning tasks for the worker
-- ============================================================

CREATE TABLE IF NOT EXISTS scan_tasks (
    -- Primary key
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,

    -- User reference
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    -- Task details
    url TEXT NOT NULL, -- FINN.no or NAV search URL to scan
    source TEXT NOT NULL CHECK (source IN ('FINN', 'NAV')),
    scan_type TEXT NOT NULL CHECK (scan_type IN ('MANUAL', 'SCHEDULED', 'RETRY')),

    -- Processing status
    status TEXT NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED')),
    worker_id TEXT, -- Which worker is processing this task

    -- Retry logic
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,

    -- Results
    jobs_found INTEGER DEFAULT 0, -- How many job links were extracted
    jobs_saved INTEGER DEFAULT 0, -- How many were successfully saved
    error_message TEXT, -- Error if failed

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at TIMESTAMPTZ, -- When processing started
    completed_at TIMESTAMPTZ -- When processing finished (success or failure)
);

-- ============================================================
-- Indexes
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_scan_tasks_user_id ON scan_tasks(user_id);
CREATE INDEX IF NOT EXISTS idx_scan_tasks_status ON scan_tasks(status);
CREATE INDEX IF NOT EXISTS idx_scan_tasks_created_at ON scan_tasks(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_scan_tasks_user_status ON scan_tasks(user_id, status);

-- ============================================================
-- Row Level Security (RLS)
-- ============================================================

ALTER TABLE scan_tasks ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view own scan tasks" ON scan_tasks;
DROP POLICY IF EXISTS "Users can insert own scan tasks" ON scan_tasks;
DROP POLICY IF EXISTS "Users can update own scan tasks" ON scan_tasks;
DROP POLICY IF EXISTS "Users can delete own scan tasks" ON scan_tasks;

CREATE POLICY "Users can view own scan tasks"
    ON scan_tasks FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own scan tasks"
    ON scan_tasks FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own scan tasks"
    ON scan_tasks FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own scan tasks"
    ON scan_tasks FOR DELETE
    USING (auth.uid() = user_id);

-- ============================================================
-- Service role bypass (for worker)
-- ============================================================

-- Allow service role to select all tasks
CREATE POLICY "Service role can view all scan tasks"
    ON scan_tasks FOR SELECT
    TO service_role
    USING (true);

-- Allow service role to update all tasks
CREATE POLICY "Service role can update all scan tasks"
    ON scan_tasks FOR UPDATE
    TO service_role
    USING (true)
    WITH CHECK (true);

-- ============================================================
-- Trigger for updated_at
-- ============================================================

DROP TRIGGER IF EXISTS update_scan_tasks_updated_at ON scan_tasks;
CREATE TRIGGER update_scan_tasks_updated_at
    BEFORE UPDATE ON scan_tasks
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- Comments
-- ============================================================

COMMENT ON TABLE scan_tasks IS 'Background job scanning tasks processed by worker';
COMMENT ON COLUMN scan_tasks.url IS 'Search URL to scan for job listings';
COMMENT ON COLUMN scan_tasks.scan_type IS 'MANUAL (user-initiated), SCHEDULED (cron), or RETRY';
COMMENT ON COLUMN scan_tasks.status IS 'PENDING (waiting), PROCESSING (in progress), COMPLETED, or FAILED';
COMMENT ON COLUMN scan_tasks.worker_id IS 'ID of worker processing this task';
COMMENT ON COLUMN scan_tasks.jobs_found IS 'Number of job links extracted from HTML';
COMMENT ON COLUMN scan_tasks.jobs_saved IS 'Number of jobs successfully saved to database';
