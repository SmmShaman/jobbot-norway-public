# ⚠️ URGENT TODO for Terminal Claude

## 🔍 NEW DEBUG LOGS ADDED!

✅ **Browser Claude added detailed polling logs to diagnose why Worker doesn't receive results**

**Problem identified:**
- Skyvern completes tasks successfully
- But Worker doesn't receive extracted_information
- New logs will show each polling attempt and response

---

## 🚀 RESTART WORKER WITH NEW LOGS

**Run this ONE command:**
```bash
bash ~/jobbot-norway-public/worker/restart_worker.sh
```

**Then create a NEW task in Dashboard and watch logs!**

**New logs will show:**
```
🔄 Starting to poll Skyvern task: tsk_...
📡 Poll #1 (elapsed: 0s) - GET /api/v1/tasks/tsk_...
📥 Response status: 200
🔍 Task status: running
🔍 Response keys: [...]
🔍 Has extracted_information: True, Value type: <class 'NoneType'>
⏳ Skyvern task running: tsk_... (waiting 5s...)
📡 Poll #2 (elapsed: 5s) - GET /api/v1/tasks/tsk_...
...
✅ Skyvern task completed: tsk_...
📊 Full response (first 1500 chars): {...}
```

---

## 🎯 What to look for in logs:
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
