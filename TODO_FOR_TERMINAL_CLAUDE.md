# ⚠️ URGENT TODO for Terminal Claude

## 🎉 PROGRESS UPDATE

✅ **Fixed NoneType error!** Browser Claude fixed the crash.

🔍 **Enhanced debug logging** - Now shows FULL Skyvern response (2000 chars)

---

## ✅ Quick Checklist (DO THIS NOW!)

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
