# ⚠️ URGENT TODO for Terminal Claude

## 🎉 ROOT CAUSE FOUND & FIXED!

✅ **Browser Claude identified the problem:**
- Skyvern 2.0 API uses `navigation_goal` + `data_extraction_goal` (NOT `prompt`)
- Field name was `data_extraction_schema` but should be `extracted_information_schema`
- Cookie banner was blocking content (now handling it!)

✅ **All templates fixed:**
- FINN template updated with correct field names + cookie handling
- NAV template updated
- DETAIL template updated
- Timeouts increased to 90 seconds

---

## 🚀 TEST THE FIX NOW!

**Step 1: Pull latest changes**
```bash
cd ~/jobbot-norway-public
git pull origin claude/jobbot-norway-metadata-011CUuyJhire2DdZRPu76sND
```

**Step 2: Restart Worker**
```bash
pkill -f "python.*worker.py"
cd ~/jobbot-norway-public/worker
export SUPABASE_SERVICE_KEY=$SUPABASE_SERVICE_ROLE_KEY
nohup python worker.py > worker.log 2>&1 &
```

**Step 3: Create NEW task via Dashboard**
Use a FINN.no URL like:
```
https://www.finn.no/job/search?location=2.20001.22034.20097&published=1
```

**Step 4: Monitor logs**
```bash
tail -f ~/jobbot-norway-public/worker/worker.log
```

**What to look for:**
```
🔍 DEBUG: Full Skyvern result keys: [..., 'navigation_goal', 'data_extraction_goal', 'extracted_information_schema', ...]
🔍 DEBUG: extracted_information type: <class 'dict'>
🔍 DEBUG: extracted_information keys: ['jobs']  ← SHOULD SEE THIS!
✅ Found X job URLs  ← SHOULD SEE JOBS!
```

---

## ✅ Previous Checklist (ALREADY DONE!)

- [ ] **Step 1:** `cd ~/jobbot-norway-public && git pull` (get latest fix!)
- [ ] **Step 2:** `pkill -f "python.*worker.py"` (stop old Worker)
- [ ] **Step 3:** Verify fix exists: `grep -n "Full Skyvern result keys" worker/worker.py`
  - Should show line ~366
- [ ] **Step 4:** Restart Worker:
  ```bash
  cd ~/jobbot-norway-public/worker
  export SUPABASE_SERVICE_KEY=$SUPABASE_SERVICE_ROLE_KEY
  nohup python worker.py > worker.log 2>&1 &
  ```
- [ ] **Step 5:** Create new task via Dashboard with FINN.no URL
- [ ] **Step 6:** `tail -f worker.log` - Look for these lines:
  ```
  🔍 DEBUG: Full Skyvern result keys: [...]
  🔍 DEBUG: Skyvern result (first 2000 chars): {...}
  🔍 DEBUG: extracted_information type: ...
  ```
- [ ] **Step 7:** Copy and share ALL debug output with Browser Claude

---

## 🐛 What Was Fixed

**Problem:** Worker crashed with `'NoneType' object has no attribute 'get'`

**Fix:**
- Added safety check for `extracted_information = None`
- Added full response logging (2000 chars)
- Added type checking before calling `.get()`

**Now:** Worker won't crash AND we'll see complete Skyvern response structure

---

## 📖 Full Details

See `WORKER_RESTART_INSTRUCTIONS.md` for complete step-by-step guide.

---

**⏰ Time estimate:** 2-3 minutes

**🎯 Goal:** See FULL Skyvern response to understand why jobs array is empty
