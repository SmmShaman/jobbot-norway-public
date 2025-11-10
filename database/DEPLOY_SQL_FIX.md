# 🔧 SQL Function Fix Deployment

## Problem
The SQL function `extract_finn_job_links()` was using the old FINN.no URL pattern `?finnkode=123`, but FINN.no now uses the new format `/job/ad/123456789`. This caused the worker to return empty results even though HTML was fetched successfully.

## Solution
Updated `database/finn_link_extractor_function.sql` to support:
1. ✅ New absolute URL format: `https://www.finn.no/job/ad/436409474`
2. ✅ New relative URL format: `/job/ad/436409474`
3. ✅ Old finnkode parameter format (fallback): `?finnkode=123`

## Deployment Steps

### 1. Open Supabase SQL Editor
Go to: https://supabase.com/dashboard/project/ptrmidlhfdbybxmyovtm/sql

### 2. Copy and Execute the SQL
Open the file `database/finn_link_extractor_function.sql` and copy the entire contents.

Paste it into the SQL Editor and click **Run**.

### 3. Verify the Update
Run this test query to verify the function works:

```sql
SELECT * FROM extract_finn_job_links('
<a href="https://www.finn.no/job/ad/436409474">Test Job 1</a>
<a href="/job/ad/436409475">Test Job 2</a>
');
```

**Expected result:**
```
url                                          | finnkode   | title
---------------------------------------------|------------|-------------
https://www.finn.no/job/ad/436409474        | 436409474  | Job 436409474
https://www.finn.no/job/ad/436409475        | 436409475  | Job 436409475
```

### 4. Test with Worker
After applying the SQL fix, create a new scan task from the dashboard:
1. Go to Dashboard
2. Click "Scan Now"
3. Check Jobs table - you should see new jobs appear

## What Changed

### Old Pattern (line 14)
```sql
pattern TEXT := 'href="(https?://[^"]*finnkode=\\d+)"';
```

### New Pattern (lines 19-61)
```sql
-- Pattern 1: Absolute URL (https://www.finn.no/job/ad/436409474)
regexp_matches(html_content, 'href="(https://www\.finn\.no/job/[^"]*?(\d{6,}))"', 'gi')

-- Pattern 2: Relative URL (/job/ad/436409474)
regexp_matches(html_content, 'href="(/job/[^"]*?(\d{6,}))"', 'gi')

-- Pattern 3: Old format (fallback)
regexp_matches(html_content, 'href="(https?://[^"]*finnkode=(\d+))"', 'gi')
```

## Troubleshooting

### If you still get empty results:
1. Check worker logs: `journalctl -u worker_v2 -n 100 --no-pager`
2. Verify HTML contains job links: Look for "Found '/job/ad/' pattern in HTML" message
3. Check scan_tasks status: `SELECT id, status, jobs_found, error_message FROM scan_tasks ORDER BY created_at DESC LIMIT 5;`

### If you see SQL syntax errors:
- Make sure you copied the ENTIRE contents of `finn_link_extractor_function.sql`
- The file should start with `-- ============================================================`
- The file should end with `COMMENT ON FUNCTION get_pending_skyvern_jobs...`
