# ⚠️ URGENT TODO for Terminal Claude

## 🚨 Current Problem

Worker is running **OLD CODE** without debug logging!

Browser Claude added debug logs but Worker hasn't been restarted with new code.

---

## ✅ Quick Checklist (DO THIS NOW!)

- [ ] **Step 1:** `cd ~/jobbot-norway-public && git pull`
- [ ] **Step 2:** `pkill -f "python.*worker.py"` (stop old Worker)
- [ ] **Step 3:** Verify debug code exists: `grep -n "DEBUG: Skyvern extracted" worker/worker.py`
- [ ] **Step 4:** Restart Worker:
  ```bash
  cd worker
  export SUPABASE_SERVICE_KEY=$SUPABASE_SERVICE_ROLE_KEY
  nohup python worker.py > worker.log 2>&1 &
  ```
- [ ] **Step 5:** Create new task via Dashboard
- [ ] **Step 6:** `tail -f worker.log` - Look for `🔍 DEBUG:` lines
- [ ] **Step 7:** Copy and share ALL debug output with Browser Claude

---

## 📖 Full Details

See `WORKER_RESTART_INSTRUCTIONS.md` for complete step-by-step guide.

---

**⏰ Time estimate:** 2-3 minutes

**🎯 Goal:** Get debug logs showing EXACTLY what Skyvern returns
