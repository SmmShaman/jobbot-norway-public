-- ============================================================
-- JobBot Norway - Scan Tasks Queue
-- Table for managing Skyvern scanning tasks
-- ============================================================

-- ============================================================
-- SCAN TASKS TABLE (черга завдань для Worker)
-- ============================================================
CREATE TABLE IF NOT EXISTS scan_tasks (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    -- Task details
    url TEXT NOT NULL,  -- URL для сканування (FINN.no або NAV.no з фільтрами)
    source TEXT NOT NULL CHECK (source IN ('FINN', 'NAV')),  -- Джерело
    scan_type TEXT NOT NULL DEFAULT 'MANUAL' CHECK (scan_type IN ('MANUAL', 'SCHEDULED', 'QUICK')),

    -- Status tracking
    status TEXT NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED')),

    -- Worker info
    worker_id TEXT,  -- ID worker'а який обробляє задачу
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,

    -- Results
    jobs_found INTEGER DEFAULT 0,
    jobs_saved INTEGER DEFAULT 0,

    -- Error handling
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,

    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- INDEXES
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_scan_tasks_user_id ON scan_tasks(user_id);
CREATE INDEX IF NOT EXISTS idx_scan_tasks_status ON scan_tasks(status);
CREATE INDEX IF NOT EXISTS idx_scan_tasks_created_at ON scan_tasks(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_scan_tasks_pending ON scan_tasks(status, created_at) WHERE status = 'PENDING';

-- ============================================================
-- ROW LEVEL SECURITY
-- ============================================================
ALTER TABLE scan_tasks ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own scan tasks"
    ON scan_tasks FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own scan tasks"
    ON scan_tasks FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own scan tasks"
    ON scan_tasks FOR UPDATE
    USING (auth.uid() = user_id);

-- Service role can do everything (for Worker)
CREATE POLICY "Service role can manage all scan tasks"
    ON scan_tasks FOR ALL
    USING (auth.role() = 'service_role');

-- ============================================================
-- UPDATED_AT TRIGGER
-- ============================================================
DROP TRIGGER IF EXISTS update_scan_tasks_updated_at ON scan_tasks;
CREATE TRIGGER update_scan_tasks_updated_at
    BEFORE UPDATE ON scan_tasks
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- UPDATE EXISTING JOBS TABLE
-- Add fields for better tracking
-- ============================================================
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS scan_task_id UUID REFERENCES scan_tasks(id);
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS contact_email TEXT;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS contact_phone TEXT;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS deadline DATE;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS salary_range TEXT;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS employment_type TEXT;  -- Full-time, Part-time, Contract
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS requirements TEXT[];  -- Array of requirements
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS benefits TEXT[];  -- Array of benefits

-- Index for scan_task_id
CREATE INDEX IF NOT EXISTS idx_jobs_scan_task_id ON jobs(scan_task_id);

-- ============================================================
-- VERIFICATION
-- ============================================================
SELECT 'scan_tasks table created successfully' as status;

SELECT 'Current pending tasks:' as info, COUNT(*) as count
FROM scan_tasks
WHERE status = 'PENDING';
