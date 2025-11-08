# ⚠️ STOP! READ THIS FIRST!

## Make sure you're on the correct branch!

**Current active branch: `claude/continue-metadata-scheduler-011CUvwSPhPwyxdh3jTQYAYu` (Worker v2)**

**Check your branch:**

```bash
git branch  # Should show * claude/continue-metadata-scheduler-011CUvwSPhPwyxdh3jTQYAYu
```

**If you're on the wrong branch, update:**

```bash
git fetch origin
git checkout claude/continue-metadata-scheduler-011CUvwSPhPwyxdh3jTQYAYu
git pull origin claude/continue-metadata-scheduler-011CUvwSPhPwyxdh3jTQYAYu
```

## After updating, you will see:

1. **README.md** - Full 500+ lines with complete instructions
2. **SESSION_CONTEXT.md** - Full project context
3. **QUICK_START.md** - Quick reference
4. **MIGRATION_V2.md** - Worker v2 migration guide
5. **QUICK_INSTALL_SQL.md** - SQL installation instructions
6. **database/finn_link_extractor_function.sql** - New SQL functions
7. **worker/worker_v2.py** - New Worker v2 implementation
8. **worker/README_V2.md** - Worker v2 documentation

## If you don't update first:

- ❌ You'll miss critical instructions
- ❌ You'll work on old code
- ❌ You won't see SESSION_CONTEXT.md
- ❌ You won't know what to do first

## DO THIS NOW:

```bash
# Step 1: Update repository
git pull origin claude/continue-metadata-scheduler-011CUvwSPhPwyxdh3jTQYAYu

# Step 2: Read SESSION_CONTEXT.md for full context
Read SESSION_CONTEXT.md

# Step 3: Read QUICK_START.md for immediate next steps
Read QUICK_START.md

# Step 4: Install SQL functions (see QUICK_INSTALL_SQL.md)
```

## 🆕 What's New in Worker v2:

- ⚡ **100x faster** link extraction (regex instead of Skyvern)
- 👁️ **Instant visibility** - jobs appear immediately
- 🔍 **Individual tracking** - per-job status with `skyvern_status`
- 🛡️ **Better reliability** - failed jobs don't block others
- 🚀 **Ready to scale** - parallel processing support

---

**This file exists to catch new sessions on old versions!**

If you already updated and README.md is 500+ lines, ignore this file.
