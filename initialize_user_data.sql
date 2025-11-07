-- ============================================================
-- JobBot Norway - Initialize User Data
-- Creates default settings and dashboard stats for existing users
-- ============================================================

-- Replace YOUR_USER_ID with your actual user ID from auth.users
-- You can find it by running: SELECT id, email FROM auth.users;

-- ============================================================
-- 1. Create dashboard stats (if not exists)
-- ============================================================
INSERT INTO user_dashboard_stats (
    user_id,
    total_jobs,
    relevant_jobs,
    total_applications,
    pending_applications,
    completed_applications,
    nav_reports
)
VALUES (
    'YOUR_USER_ID',  -- Replace with your user ID
    0,  -- total_jobs
    0,  -- relevant_jobs
    0,  -- total_applications
    0,  -- pending_applications
    0,  -- completed_applications
    0   -- nav_reports
)
ON CONFLICT (user_id) DO NOTHING;

-- ============================================================
-- 2. Create default user settings (if not exists)
-- ============================================================
INSERT INTO user_settings (
    user_id,
    nav_search_urls,
    finn_search_urls,
    min_relevance_score,
    auto_apply_threshold,
    max_applications_per_day,
    require_manual_approval,
    telegram_enabled,
    unified_profile
)
VALUES (
    'YOUR_USER_ID',  -- Replace with your user ID
    ARRAY[]::text[],  -- Empty NAV search URLs
    ARRAY[]::text[],  -- Empty FINN search URLs
    70,  -- Default minimum relevance score
    85,  -- Default auto-apply threshold
    5,   -- Max 5 applications per day
    true,  -- Require manual approval by default
    false,  -- Telegram disabled by default
    '{}'::jsonb  -- Empty profile JSON
)
ON CONFLICT (user_id) DO NOTHING;

-- ============================================================
-- 3. Verify data was created
-- ============================================================
SELECT 'Dashboard stats created' as status, COUNT(*) as count
FROM user_dashboard_stats
WHERE user_id = 'YOUR_USER_ID';

SELECT 'User settings created' as status, COUNT(*) as count
FROM user_settings
WHERE user_id = 'YOUR_USER_ID';

-- ============================================================
-- QUICK GUIDE:
-- 1. Find your user ID: SELECT id, email FROM auth.users;
-- 2. Replace 'YOUR_USER_ID' with your actual ID (3 places)
-- 3. Run this SQL in Supabase SQL Editor
-- ============================================================
