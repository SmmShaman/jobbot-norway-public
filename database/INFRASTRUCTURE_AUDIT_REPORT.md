# 🔍 INFRASTRUCTURE AUDIT REPORT

## Executive Summary

This document provides a complete audit of the JobBot database infrastructure based on **actual code requirements** vs **available SQL schemas**.

---

## 📊 AUDIT FINDINGS

### ✅ Tables WITH Schema Files

| Table | Schema File | Status |
|-------|-------------|--------|
| `jobs` | `jobs_table_schema_fixed.sql` | ✅ Schema exists |
| `scan_tasks` | `scan_tasks_table_schema.sql` | ✅ Schema exists |

### ❌ Tables WITHOUT Schema Files (CRITICAL)

These tables are **used in code** but have **NO SQL schema files**:

| Table | Used In | Missing Schema |
|-------|---------|----------------|
| `user_settings` | `web-app/src/lib/supabase.ts:117,128` | ❌ NO SCHEMA |
| `profiles` | `web-app/src/lib/supabase.ts:93,104` | ❌ NO SCHEMA |
| `resumes` | `web-app/src/lib/supabase.ts:58,70` | ❌ NO SCHEMA |
| `screenshots` | `web-app/src/lib/supabase.ts:80` | ❌ NO SCHEMA |
| `applications` | `web-app/src/lib/supabase.ts:185,200` | ❌ NO SCHEMA |
| `cover_letters` | `web-app/src/lib/supabase.ts:212,223,234` | ❌ NO SCHEMA |
| `user_dashboard_stats` | `web-app/src/lib/supabase.ts:247` | ❌ NO SCHEMA |
| `monitoring_logs` | `web-app/src/lib/supabase.ts:276` | ❌ NO SCHEMA |

### ✅ SQL Functions WITH Schema Files

| Function | Schema File | Status |
|----------|-------------|--------|
| `extract_finn_job_links` | `finn_link_extractor_function.sql` | ✅ Exists |
| `create_jobs_from_finn_links` | `finn_link_extractor_function.sql` | ✅ Exists |
| `get_pending_skyvern_jobs` | `finn_link_extractor_function.sql` | ✅ Exists |
| `update_updated_at_column` | `jobs_table_schema_fixed.sql` | ✅ Exists |

---

## 🔴 CRITICAL ISSUES

### Issue #1: Missing `user_settings` Table

**Impact:** HIGH - Dashboard "Scan Now" button relies on this

**Code expectation:**
```typescript
// web-app/src/lib/api.ts:24
const { data: settings, error: settingsError } = await supabase
  .from('user_settings')
  .select('finn_search_urls, nav_search_urls')
  .eq('user_id', request.user_id)
  .single();
```

**Required columns:**
- `user_id` (UUID, PRIMARY KEY)
- `finn_search_urls` (TEXT[] or JSONB)
- `nav_search_urls` (TEXT[] or JSONB)

### Issue #2: Worker Can't Create Scan Tasks

**Impact:** HIGH - Worker won't find any tasks without `scan_tasks` table

**Status:** Schema file exists (`scan_tasks_table_schema.sql`) but NOT YET APPLIED to database

### Issue #3: Missing Application & Cover Letter Tables

**Impact:** MEDIUM - Application submission features won't work

**Tables needed:**
- `applications`
- `cover_letters`

### Issue #4: Missing Profile & Resume Tables

**Impact:** MEDIUM - User profile management won't work

**Tables needed:**
- `profiles`
- `resumes`

### Issue #5: Missing Monitoring Tables

**Impact:** LOW - Dashboard stats won't show

**Tables needed:**
- `user_dashboard_stats`
- `monitoring_logs`

---

## 🎯 STEP-BY-STEP FIX PLAN

### Phase 1: Critical Tables (DO THIS FIRST)

#### Step 1.1: Run Infrastructure Audit
```sql
-- In Supabase SQL Editor, run:
-- Copy from: database/INFRASTRUCTURE_AUDIT.sql
```

This will show you **exactly** which tables exist right now.

#### Step 1.2: Create `scan_tasks` Table
```sql
-- Copy from: database/scan_tasks_table_schema.sql
-- Paste in Supabase SQL Editor and Run
```

#### Step 1.3: Update SQL Functions
```sql
-- Copy from: database/finn_link_extractor_function.sql
-- Paste in Supabase SQL Editor and Run
```

#### Step 1.4: Verify `jobs` Table Has All Columns
```sql
-- Check if finnkode column exists:
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'jobs'
AND column_name = 'finnkode';

-- If not exists, add it:
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS finnkode TEXT;
CREATE INDEX IF NOT EXISTS idx_jobs_finnkode ON jobs(finnkode);
```

### Phase 2: Create Missing Critical Tables

#### Step 2.1: Create `user_settings` Table
**Schema file needed** - will create based on code requirements

```sql
CREATE TABLE IF NOT EXISTS user_settings (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    finn_search_urls TEXT[] DEFAULT '{}',
    nav_search_urls TEXT[] DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- RLS
ALTER TABLE user_settings ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own settings"
    ON user_settings FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own settings"
    ON user_settings FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own settings"
    ON user_settings FOR UPDATE
    USING (auth.uid() = user_id);
```

#### Step 2.2: Create `profiles` Table
```sql
CREATE TABLE IF NOT EXISTS profiles (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    full_name TEXT,
    email TEXT,
    phone TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- RLS
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own profile"
    ON profiles FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own profile"
    ON profiles FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own profile"
    ON profiles FOR UPDATE
    USING (auth.uid() = user_id);
```

### Phase 3: Lower Priority Tables

These can be added later as features are needed:
- `resumes`
- `screenshots`
- `applications`
- `cover_letters`
- `user_dashboard_stats`
- `monitoring_logs`

---

## 📋 VERIFICATION CHECKLIST

After applying all fixes, verify:

```sql
-- 1. Check all tables exist
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;

-- Expected minimum:
-- - jobs
-- - profiles
-- - scan_tasks
-- - user_settings

-- 2. Test SQL functions
SELECT * FROM extract_finn_job_links('<a href="https://www.finn.no/job/ad/123456">Test</a>');

-- 3. Check worker can query scan_tasks
SELECT COUNT(*) FROM scan_tasks WHERE status = 'PENDING';

-- 4. Check user_settings exists
SELECT COUNT(*) FROM user_settings;
```

---

## 🚀 QUICK START (Minimum Viable System)

To get the system working RIGHT NOW, execute in this order:

1. **Run audit:** `INFRASTRUCTURE_AUDIT.sql`
2. **Create scan_tasks:** `scan_tasks_table_schema.sql`
3. **Update functions:** `finn_link_extractor_function.sql`
4. **Create user_settings:** (See Step 2.1 above)
5. **Create profiles:** (See Step 2.2 above)
6. **Verify jobs table:** Check it has `finnkode` column

Then test:
- Dashboard → Settings → Add search URL
- Dashboard → Scan Now
- Check Jobs table for results

---

## 📝 LESSONS LEARNED

### What Went Wrong:
1. ❌ Assumed tables exist because code references them
2. ❌ Didn't verify database state before making changes
3. ❌ Worked from summary instead of checking facts

### What Should Have Been Done:
1. ✅ Run `SELECT * FROM information_schema.tables` FIRST
2. ✅ Compare existing tables with code requirements
3. ✅ Create missing schemas BEFORE fixing functions
4. ✅ Test each component individually

### Key Principle:
**VERIFY FACTS → ANALYZE → FIX** (not the other way around)

---

## 🔗 FILES REFERENCE

| File | Purpose | Apply Order |
|------|---------|-------------|
| `INFRASTRUCTURE_AUDIT.sql` | Check current state | 1️⃣ FIRST |
| `scan_tasks_table_schema.sql` | Create scan_tasks | 2️⃣ |
| `finn_link_extractor_function.sql` | Update functions | 3️⃣ |
| `jobs_table_schema_fixed.sql` | Jobs table (if needed) | 4️⃣ |

**Missing schemas to create:**
- `user_settings_schema.sql` (CREATE THIS)
- `profiles_schema.sql` (CREATE THIS)
- `applications_schema.sql` (Later)
- `resumes_schema.sql` (Later)
