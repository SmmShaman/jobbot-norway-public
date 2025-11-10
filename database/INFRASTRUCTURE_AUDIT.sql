-- ============================================================
-- INFRASTRUCTURE AUDIT - Complete Database Check
-- Run this in Supabase SQL Editor to verify all components exist
-- ============================================================

-- 1. CHECK ALL TABLES
-- ============================================================
SELECT
    '=== EXISTING TABLES ===' as check_type,
    table_name,
    table_type
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;

-- Expected tables:
-- - applications
-- - cover_letters
-- - jobs
-- - monitoring_logs
-- - profiles
-- - resumes
-- - scan_tasks
-- - screenshots
-- - user_dashboard_stats
-- - user_settings

-- ============================================================
-- 2. CHECK ALL FUNCTIONS
-- ============================================================
SELECT
    '=== EXISTING FUNCTIONS ===' as check_type,
    routine_name,
    routine_type
FROM information_schema.routines
WHERE routine_schema = 'public'
AND routine_type = 'FUNCTION'
ORDER BY routine_name;

-- Expected functions:
-- - create_jobs_from_finn_links
-- - extract_finn_job_links
-- - get_pending_skyvern_jobs
-- - update_updated_at_column

-- ============================================================
-- 3. CHECK JOBS TABLE SCHEMA
-- ============================================================
SELECT
    '=== JOBS TABLE COLUMNS ===' as check_type,
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_schema = 'public'
AND table_name = 'jobs'
ORDER BY ordinal_position;

-- Expected critical columns:
-- - id (uuid)
-- - user_id (uuid, NOT NULL)
-- - scan_task_id (uuid, nullable)
-- - title (text, NOT NULL)
-- - company (text, NOT NULL)
-- - url (text, NOT NULL)
-- - finnkode (text, nullable)
-- - source (text, NOT NULL)
-- - status (text, NOT NULL)
-- - skyvern_status (text)

-- ============================================================
-- 4. CHECK SCAN_TASKS TABLE SCHEMA
-- ============================================================
SELECT
    '=== SCAN_TASKS TABLE COLUMNS ===' as check_type,
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_schema = 'public'
AND table_name = 'scan_tasks'
ORDER BY ordinal_position;

-- Expected critical columns:
-- - id (uuid)
-- - user_id (uuid, NOT NULL)
-- - url (text, NOT NULL)
-- - source (text, NOT NULL)
-- - scan_type (text, NOT NULL)
-- - status (text, NOT NULL)
-- - jobs_found (integer)
-- - jobs_saved (integer)

-- ============================================================
-- 5. CHECK USER_SETTINGS TABLE SCHEMA
-- ============================================================
SELECT
    '=== USER_SETTINGS TABLE COLUMNS ===' as check_type,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_schema = 'public'
AND table_name = 'user_settings'
ORDER BY ordinal_position;

-- Expected critical columns:
-- - user_id (uuid)
-- - finn_search_urls (text[] or jsonb)
-- - nav_search_urls (text[] or jsonb)

-- ============================================================
-- 6. CHECK INDEXES
-- ============================================================
SELECT
    '=== INDEXES ===' as check_type,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
AND tablename IN ('jobs', 'scan_tasks', 'user_settings')
ORDER BY tablename, indexname;

-- ============================================================
-- 7. CHECK CONSTRAINTS
-- ============================================================
SELECT
    '=== CONSTRAINTS ===' as check_type,
    conrelid::regclass AS table_name,
    conname AS constraint_name,
    contype AS constraint_type,
    pg_get_constraintdef(oid) AS definition
FROM pg_constraint
WHERE conrelid::regclass::text IN ('jobs', 'scan_tasks', 'user_settings')
ORDER BY table_name, constraint_name;

-- ============================================================
-- 8. CHECK RLS POLICIES
-- ============================================================
SELECT
    '=== RLS POLICIES ===' as check_type,
    tablename,
    policyname,
    permissive,
    roles,
    cmd,
    qual,
    with_check
FROM pg_policies
WHERE schemaname = 'public'
AND tablename IN ('jobs', 'scan_tasks', 'user_settings')
ORDER BY tablename, policyname;

-- ============================================================
-- 9. TEST FUNCTIONS
-- ============================================================

-- Test extract_finn_job_links
SELECT '=== TEST extract_finn_job_links ===' as check_type;
SELECT * FROM extract_finn_job_links('
<a href="https://www.finn.no/job/ad/436409474">Test Job 1</a>
<a href="/job/ad/436409475">Test Job 2</a>
') LIMIT 5;

-- ============================================================
-- 10. CHECK MISSING TABLES
-- ============================================================

DO $$
DECLARE
    expected_tables text[] := ARRAY[
        'applications',
        'cover_letters',
        'jobs',
        'monitoring_logs',
        'profiles',
        'resumes',
        'scan_tasks',
        'screenshots',
        'user_dashboard_stats',
        'user_settings'
    ];
    tbl text;
    exists_count int;
BEGIN
    RAISE NOTICE '=== MISSING TABLES CHECK ===';

    FOREACH tbl IN ARRAY expected_tables
    LOOP
        SELECT COUNT(*) INTO exists_count
        FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_name = tbl;

        IF exists_count = 0 THEN
            RAISE NOTICE '❌ MISSING: %', tbl;
        ELSE
            RAISE NOTICE '✅ EXISTS: %', tbl;
        END IF;
    END LOOP;
END $$;

-- ============================================================
-- SUMMARY
-- ============================================================
-- After running this script, check the results:
-- 1. All expected tables should exist
-- 2. All expected functions should exist
-- 3. Critical columns should be present
-- 4. RLS policies should be enabled
-- 5. Test functions should return valid results
-- ============================================================
