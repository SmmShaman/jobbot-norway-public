-- ============================================================
-- JobBot Norway - Supabase Database Schema
-- Missing tables: monitoring_logs and user_dashboard_stats
-- ============================================================

-- Drop tables if they exist (for clean reinstall)
DROP TABLE IF EXISTS monitoring_logs CASCADE;
DROP TABLE IF EXISTS user_dashboard_stats CASCADE;

-- ============================================================
-- MONITORING LOGS TABLE
-- Stores history of all job scanning operations
-- ============================================================
CREATE TABLE monitoring_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    -- Scan information
    scan_type TEXT NOT NULL CHECK (scan_type IN ('MANUAL', 'SCHEDULED', 'QUICK')),
    status TEXT NOT NULL DEFAULT 'RUNNING' CHECK (status IN ('RUNNING', 'COMPLETED', 'FAILED')),

    -- Results
    jobs_found INTEGER DEFAULT 0,
    jobs_relevant INTEGER DEFAULT 0,

    -- Timing
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,

    -- Error tracking
    error_message TEXT,

    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Add indexes for better query performance
CREATE INDEX idx_monitoring_logs_user_id ON monitoring_logs(user_id);
CREATE INDEX idx_monitoring_logs_started_at ON monitoring_logs(started_at DESC);
CREATE INDEX idx_monitoring_logs_status ON monitoring_logs(status);

-- ============================================================
-- USER DASHBOARD STATS TABLE
-- Aggregated statistics for dashboard display
-- ============================================================
CREATE TABLE user_dashboard_stats (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL UNIQUE REFERENCES auth.users(id) ON DELETE CASCADE,

    -- Job statistics
    total_jobs INTEGER DEFAULT 0,
    relevant_jobs INTEGER DEFAULT 0,

    -- Application statistics
    total_applications INTEGER DEFAULT 0,
    pending_applications INTEGER DEFAULT 0,
    completed_applications INTEGER DEFAULT 0,

    -- NAV reports
    nav_reports INTEGER DEFAULT 0,

    -- Last activity
    last_scan_at TIMESTAMPTZ,
    last_application_at TIMESTAMPTZ,

    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Add index for user lookup
CREATE INDEX idx_dashboard_stats_user_id ON user_dashboard_stats(user_id);

-- ============================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- Users can only see their own data
-- ============================================================

-- Enable RLS
ALTER TABLE monitoring_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_dashboard_stats ENABLE ROW LEVEL SECURITY;

-- Monitoring logs policies
CREATE POLICY "Users can view own monitoring logs"
    ON monitoring_logs FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own monitoring logs"
    ON monitoring_logs FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own monitoring logs"
    ON monitoring_logs FOR UPDATE
    USING (auth.uid() = user_id);

-- Dashboard stats policies
CREATE POLICY "Users can view own dashboard stats"
    ON user_dashboard_stats FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own dashboard stats"
    ON user_dashboard_stats FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own dashboard stats"
    ON user_dashboard_stats FOR UPDATE
    USING (auth.uid() = user_id);

-- ============================================================
-- AUTOMATIC UPDATED_AT TRIGGER
-- ============================================================

-- Create trigger function if it doesn't exist
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Add triggers
CREATE TRIGGER update_monitoring_logs_updated_at
    BEFORE UPDATE ON monitoring_logs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_dashboard_stats_updated_at
    BEFORE UPDATE ON user_dashboard_stats
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- AUTOMATIC DASHBOARD STATS INITIALIZATION
-- Create stats row when user registers
-- ============================================================

CREATE OR REPLACE FUNCTION initialize_user_dashboard_stats()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO user_dashboard_stats (user_id)
    VALUES (NEW.id)
    ON CONFLICT (user_id) DO NOTHING;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to create dashboard stats on user signup
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION initialize_user_dashboard_stats();

-- ============================================================
-- SAMPLE DATA (Optional - for testing)
-- Uncomment to insert test data
-- ============================================================

/*
-- Insert sample monitoring log (replace with your user_id)
INSERT INTO monitoring_logs (user_id, scan_type, status, jobs_found, jobs_relevant, started_at, completed_at)
VALUES (
    'YOUR_USER_ID_HERE',
    'MANUAL',
    'COMPLETED',
    25,
    8,
    NOW() - INTERVAL '1 hour',
    NOW() - INTERVAL '50 minutes'
);

-- Insert sample dashboard stats (replace with your user_id)
INSERT INTO user_dashboard_stats (user_id, total_jobs, relevant_jobs, total_applications, nav_reports)
VALUES (
    'YOUR_USER_ID_HERE',
    25,
    8,
    3,
    1
)
ON CONFLICT (user_id)
DO UPDATE SET
    total_jobs = EXCLUDED.total_jobs,
    relevant_jobs = EXCLUDED.relevant_jobs,
    total_applications = EXCLUDED.total_applications,
    nav_reports = EXCLUDED.nav_reports;
*/

-- ============================================================
-- VERIFICATION QUERIES
-- Run these to verify tables were created successfully
-- ============================================================

-- List all tables
-- SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';

-- Check monitoring_logs structure
-- SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'monitoring_logs';

-- Check user_dashboard_stats structure
-- SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'user_dashboard_stats';

-- Check RLS policies
-- SELECT tablename, policyname FROM pg_policies WHERE tablename IN ('monitoring_logs', 'user_dashboard_stats');
