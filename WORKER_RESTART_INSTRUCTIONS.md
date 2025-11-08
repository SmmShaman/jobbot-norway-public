# 🔄 Worker Restart Instructions - MUST READ!

**⚠️ IMPORTANT: This file contains critical instructions for Terminal Claude**

## 🎯 Current Situation

Browser Claude has added DEBUG logging to `worker/worker.py` (lines 369-376) to diagnose why Skyvern returns empty job lists.

**The problem:** Worker is running OLD code without debug logs!

---

## ✅ STEP-BY-STEP: What Terminal Claude MUST do NOW

### Step 1: Pull Latest Code from Git

```bash
cd ~/jobbot-norway-public
git pull origin claude/jobbot-norway-metadata-011CUuyJhire2DdZRPu76sND
```

**Expected output:** Should pull commit with debug logging changes.

### Step 2: Verify Debug Logs are in Code

```bash
grep -n "DEBUG: Skyvern extracted_information keys" worker/worker.py
```

**Expected output:** Should show line 370 with the debug log.

If this command returns nothing, the code is OLD! Pull again.

### Step 3: Stop Current Worker Process

```bash
pkill -f "python.*worker.py"
```

**Verify it stopped:**
```bash
ps aux | grep worker.py
```

Should return nothing (except the grep command itself).

### Step 4: Restart Worker with New Code

```bash
cd ~/jobbot-norway-public/worker
export SUPABASE_SERVICE_KEY=$SUPABASE_SERVICE_ROLE_KEY
nohup python worker.py > worker.log 2>&1 &
```

**Verify it started:**
```bash
tail -20 worker.log
```

Should show:
```
🚀 Worker initialized: worker-XXXXXXXX
📡 Supabase: https://...
🤖 Skyvern: http://localhost:8000
```

### Step 5: Create New Test Task via Dashboard

Go to Dashboard and create a new scan task with a FINN.no URL:
```
https://www.finn.no/job/search?location=2.20001.22034.20097&occupation=0.23.19
```

### Step 6: Monitor Logs for DEBUG Output

```bash
tail -f worker.log
```

**What to look for:**
```
📥 Found 1 pending task(s)
📋 Processing task: XXXXXXXX...
🔍 STAGE 1: Extracting job URLs from listing page...
🤖 Calling Skyvern API: http://localhost:8000
✅ Skyvern task created: tsk_...
🔍 DEBUG: Skyvern extracted_information keys: [...]  ← THIS IS THE KEY LINE!
🔍 DEBUG: Full extracted_information: {...}
```

### Step 7: Copy Full DEBUG Output

When you see the debug lines, copy ALL of them and share with Browser Claude:
- `🔍 DEBUG: Skyvern extracted_information keys: ...`
- `🔍 DEBUG: Full extracted_information: ...`
- `⚠️ Skyvern task status: ...`
- `⚠️ Full Skyvern result: ...`

This will show us EXACTLY what Skyvern is returning and why jobs array is empty.

---

## 🐛 Troubleshooting

**If debug logs still don't appear:**

1. Check which worker.py is running:
   ```bash
   ps aux | grep worker.py | grep -v grep
   ```

2. Check if it's the right file:
   ```bash
   ls -la ~/jobbot-norway-public/worker/worker.py
   stat ~/jobbot-norway-public/worker/worker.py
   ```

3. Manually verify debug code is there:
   ```bash
   sed -n '369,376p' ~/jobbot-norway-public/worker/worker.py
   ```

   Should show:
   ```python
   # DEBUG: Log what Skyvern actually extracted
   logger.info(f"🔍 DEBUG: Skyvern extracted_information keys: {list(extracted_data.keys())}")
   logger.info(f"🔍 DEBUG: Full extracted_information: {json.dumps(extracted_data, indent=2, ensure_ascii=False)[:500]}...")
   ```

---

## 📋 Success Criteria

✅ Worker is running with NEW code (has debug logs)
✅ New task created via Dashboard
✅ DEBUG logs appear in worker.log
✅ Full Skyvern response is visible
✅ We can see WHY jobs array is empty

---

## 🎯 Next Steps After Debug Logs

Once Browser Claude sees the debug output, they will:
1. Analyze what Skyvern is returning
2. Fix the template or prompt if needed
3. Update extraction schema if needed
4. Test again until jobs are extracted properly

**This is a critical debugging step - we MUST see those debug logs!** 🔍
