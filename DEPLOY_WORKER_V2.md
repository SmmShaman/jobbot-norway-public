# 🚀 Deploy Worker v2 - Quick Guide

## 🔍 What Changed

**Discovery:** FINN.no is a **React/Next.js SPA** (Single Page Application) that loads job listings via JavaScript.

**Solution:** Updated Worker v2 to use **Playwright** (browser automation) instead of simple HTTP requests.

### Before vs After:

| Method | Works? | Speed | Why |
|--------|--------|-------|-----|
| ❌ `requests.get()` | No | Fast | Can't execute JavaScript |
| ✅ **Playwright** | Yes | 5-10s | Renders React, extracts real links |

---

## 📋 Prerequisites

### 1. Install SQL Functions in Supabase

**Manual installation required** (automated script blocked by DNS in this environment)

**Quick steps:**
1. Open: https://supabase.com/dashboard/project/ptrmidlhfdbybxmyovtm/sql/new
2. Copy contents from: `database/finn_link_extractor_function.sql`
3. Paste into SQL Editor
4. Click **Run** (or press F5)

**Verify installation:**
```sql
SELECT routine_name, routine_type
FROM information_schema.routines
WHERE routine_schema = 'public'
  AND routine_name LIKE '%finn%'
ORDER BY routine_name;
```

Should show 3 functions:
- ✅ `create_jobs_from_finn_links`
- ✅ `extract_finn_job_links`
- ✅ `get_pending_skyvern_jobs`

**See detailed guide:** `INSTALL_SQL_NOW.md`

---

## 🖥️ Install Worker v2 on Local PC

### Step 1: Update Dependencies

```bash
cd worker
pip install -r requirements.txt
playwright install chromium
```

**New dependency:** `playwright==1.40.0` (for React/SPA scraping)

### Step 2: Verify Environment Variables

Ensure your `.env` file has:

```bash
# Supabase
SUPABASE_URL=https://ptrmidlhfdbybxmyovtm.supabase.co
SUPABASE_SERVICE_KEY=your_service_role_key_here

# Skyvern
SKYVERN_API_URL=http://localhost:8000
```

### Step 3: Test Playwright Extraction

Test with your filtered search URL:

```bash
python scripts/test_finn_playwright.py
```

**Expected output:**
```
🧪 Testing FINN.no Link Extraction with Playwright
============================================================
🌐 Launching browser for: https://www.finn.no/job/search?...
📄 Loading page with JavaScript rendering...
⏳ Waiting for job listings to appear...
✅ Job listings loaded!

✅ Found 1 unique job links:

1. finnkode=378776848
   URL: https://www.finn.no/job/fulltime/ad.html?finnkode=378776848
```

### Step 4: Start Worker v2

```bash
cd worker
python worker_v2.py
```

**Expected output:**
```
============================================================
🤖 JobBot Worker v2 Started
🆔 Worker ID: worker-v2-a3f4d8c1
⏱️ Poll Interval: 10s
📝 New Architecture: Link Extraction → Individual Processing
============================================================

💤 No pending tasks. Waiting 10s...
```

---

## 🧪 Test End-to-End Flow

### 1. Create Scan Task via Dashboard

**Frontend:** https://jobbot-norway.netlify.app

1. Login
2. Go to **Scan** page
3. Enter FINN.no search URL:
   ```
   https://www.finn.no/job/search?location=2.20001.22034.20097&location=2.20001.22034.20098&location=2.20001.22034.20085&published=1
   ```
4. Select **Source:** FINN
5. Click **Start Scan**

### 2. Watch Real-Time Processing

**Worker v2 log output:**
```
📥 Found 1 pending task(s)
============================================================
📋 Processing task: a3f4d8c1...
🌐 Source: FINN
🔗 URL: https://www.finn.no/job/search?...
============================================================

🌐 Launching browser for: https://www.finn.no/job/search?...
📄 Loading page with JavaScript rendering...
⏳ Waiting for job listings...
✅ Job listings loaded!
✅ HTML fetched: 487213 characters

🔍 Extracting job links from HTML...
✅ Created/updated 1 job entries
📊 Created 1 job entries

🔍 Processing job 1/1: finnkode=378776848
🤖 Calling Skyvern for: https://www.finn.no/job/fulltime/ad.html?finnkode=378776848...
✅ Skyvern task created: task_abc123
⏳ Skyvern task processing: task_abc123
✅ Skyvern task completed: task_abc123
✅ Updated job a3f4d8c1... with Skyvern details
✅ Job 1/1 processed successfully

✅ Task completed: 1/1 jobs processed
```

### 3. Watch Frontend Update in Real-Time

**Jobs page** (auto-refreshes every 5 seconds):

**Step 1 (Instant):** Job appears as link
```
📌 Job #378776848
   🔗 https://www.finn.no/job/fulltime/ad.html?finnkode=378776848
   ⏳ Waiting for details...
```

**Step 2 (5-60s later):** Job gains details
```
✅ Senior Developer
   🏢 Acme Corp
   📍 Oslo, Norway
   💼 Full-time
   📧 jobs@acme.com
   ⏰ Deadline: 2025-12-01
```

---

## 🏗️ Architecture Overview

### Worker v2 Flow:

```
Dashboard → Supabase scan_task (PENDING)
              ↓
        Worker v2 detects
              ↓
    1. Launch Playwright browser → Render React page
              ↓
    2. Extract finnkode links from HTML
              ↓
    3. Create job entries (skyvern_status='PENDING')
              ↓
    4. For each job:
       - Call Skyvern → Extract details (30-60s)
       - Update job (skyvern_status='COMPLETED')
              ↓
    5. Mark scan_task as COMPLETED
              ↓
        Frontend auto-refreshes → Shows new jobs!
```

### Performance:

| Phase | Method | Time | Cost |
|-------|--------|------|------|
| **Link extraction** | Playwright | 5-10s | $0.00 |
| **Job details** | Skyvern (per job) | 30-60s | $0.10 |

**Example:** Search with 10 jobs
- Extraction: 10 seconds (all links at once)
- Processing: 5-10 minutes (10 jobs × 30-60s each)
- Total time: **5-10 minutes**
- Total cost: **$1.00** (10 jobs × $0.10)

---

## 🔧 Troubleshooting

### Issue: "No job links extracted"

**Possible causes:**
1. ❌ SQL functions not installed in Supabase
2. ❌ Playwright not installed
3. ❌ No jobs matching search filters

**Solutions:**
```bash
# 1. Verify SQL functions
# Run query in Supabase SQL Editor (see Prerequisites)

# 2. Install Playwright
pip install playwright
playwright install chromium

# 3. Test with broader search
# Remove location filters, try: https://www.finn.no/job/search?published=1
```

### Issue: "Playwright timeout"

**Cause:** FINN.no page loading slowly

**Solution:** Increase timeout in `worker_v2.py:147`:
```python
page.goto(url, wait_until='networkidle', timeout=60000)  # 60s instead of 30s
```

### Issue: "Skyvern connection refused"

**Cause:** Skyvern not running

**Solution:**
```bash
# Start Skyvern
docker-compose up -d skyvern

# Verify it's running
curl http://localhost:8000/api/v1/health
```

---

## 📊 Monitoring

### Check Worker Status

```bash
# View worker logs
tail -f worker/worker.log
```

### Check Database

```sql
-- Pending scan tasks
SELECT id, source, url, status, created_at
FROM scan_tasks
WHERE status = 'PENDING'
ORDER BY created_at DESC;

-- Jobs awaiting Skyvern processing
SELECT id, finnkode, url, skyvern_status, created_at
FROM jobs
WHERE skyvern_status = 'PENDING'
ORDER BY created_at DESC;

-- Recent Skyvern results
SELECT id, finnkode, title, company, skyvern_status, updated_at
FROM jobs
WHERE skyvern_status IN ('COMPLETED', 'FAILED')
ORDER BY updated_at DESC
LIMIT 10;
```

---

## 🎯 Next Steps

### Immediate:
1. ✅ Install SQL functions manually
2. ✅ Install Playwright: `pip install playwright && playwright install chromium`
3. ✅ Restart Worker v2: `python worker/worker_v2.py`
4. ✅ Test with real FINN.no search URL

### Future Optimization (Worker v3):
Based on `ARCHITECTURE_RECOMMENDATIONS.md`:

1. **Use Playwright for job details too** (instead of Skyvern)
   - Speed: 5s per job (10x faster)
   - Cost: $0.00 (vs $0.10)
   - Reliability: 85-90%

2. **Hybrid approach** (recommended):
   - Try Playwright first (90% success, 5s)
   - Fallback to Skyvern (10% complex jobs, 60s)
   - Result: 5-10s average, 90% cost savings

3. **Check for JSON-LD structured data**
   - Some sites include job data in `<script type="application/ld+json">`
   - Ultra-fast (<1s), most reliable

**See:** `ARCHITECTURE_RECOMMENDATIONS.md` for full analysis

---

## ✅ Success Criteria

Worker v2 is working correctly when:

1. ✅ Test script extracts finnkode from FINN.no search
2. ✅ Worker creates job entries with `skyvern_status='PENDING'`
3. ✅ Jobs appear instantly in dashboard (as links)
4. ✅ Skyvern processes each job and updates details
5. ✅ Frontend shows progressive enhancement (link → full details)

---

## 📚 Related Documentation

- **SQL Functions:** `INSTALL_SQL_NOW.md`
- **Architecture:** `ARCHITECTURE_RECOMMENDATIONS.md`
- **Worker v2 README:** `worker/README_V2.md`
- **Migration Guide:** `MIGRATION_V2.md`

---

## 🆘 Need Help?

**Check logs:**
```bash
# Worker logs
tail -f worker/worker.log

# Test extraction
python scripts/test_finn_playwright.py

# Verify SQL functions
# See INSTALL_SQL_NOW.md
```

**Common commands:**
```bash
# Install everything
pip install -r worker/requirements.txt
playwright install chromium

# Start worker
cd worker && python worker_v2.py

# Test FINN.no extraction
python scripts/test_finn_playwright.py
```

---

🎉 **Ready to deploy!** Start with SQL functions, then Worker v2.
