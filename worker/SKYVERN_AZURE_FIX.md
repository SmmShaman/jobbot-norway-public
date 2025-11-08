# 🔧 Fix: Skyvern Azure OpenAI Model Mismatch

## 🔍 Problem Identified

Worker templates are configured correctly, but **Skyvern is trying to use `OPENAI_GPT4O` model instead of Azure OpenAI**.

**Evidence from Skyvern logs:**
```json
{"model": "OPENAI_GPT4O", "messages": [...], "temperature": 0.0}
```

**Expected:** Should use `AZURE_OPENAI` or similar Azure model key.

---

## ✅ Solution: Update Skyvern Configuration

### Step 1: Locate Skyvern Configuration

Skyvern appears to be installed in: `/home/stuard/jobbot-public/skyvern/` (based on artifact paths)

Find the configuration files:
```bash
cd /home/stuard/jobbot-public/skyvern
# or wherever Skyvern is installed

# Look for these files:
ls -la .env
ls -la docker-compose.yml
```

### Step 2: Update Environment Variables

Edit `.env` file and change the `LLM_KEY`:

**BEFORE:**
```bash
LLM_KEY=OPENAI_GPT4O  # ❌ Wrong - trying to use OpenAI
```

**AFTER:**
```bash
LLM_KEY=AZURE_OPENAI  # ✅ Correct - use Azure OpenAI
```

**Or if using GPT-4o mini on Azure:**
```bash
LLM_KEY=AZURE_OPENAI_GPT4O_MINI
```

### Step 3: Verify Azure Configuration

Make sure these Azure environment variables are also set in `.env`:

```bash
# Azure OpenAI Configuration
ENABLE_AZURE=true
AZURE_DEPLOYMENT=your-deployment-name  # e.g., gpt-4o
AZURE_API_KEY=your-azure-api-key
AZURE_API_BASE=https://your-resource.openai.azure.com/
AZURE_API_VERSION=2024-02-01
```

### Step 4: Restart Skyvern

```bash
# Restart Skyvern container
docker-compose down
docker-compose up -d

# Or if using docker directly:
docker restart skyvern-skyvern-1
```

### Step 5: Test with Worker

After restarting Skyvern:
1. Run the Worker: `python worker.py`
2. Create a new scan task
3. Check logs for successful LLM requests
4. Verify jobs are extracted properly

---

## 📋 Available Azure LLM_KEY Values

Based on Skyvern documentation, these are valid Azure model keys:

- `AZURE_OPENAI` - Main Azure OpenAI model
- `AZURE_OPENAI_GPT4O_MINI` - GPT-4o mini on Azure
- `AZURE_OPENAI_O3_MINI` - O3 mini on Azure
- `AZURE_OPENAI_GPT4_1` - GPT-4.1 on Azure
- `AZURE_OPENAI_GPT5` - GPT-5 on Azure (if available)

Choose the one that matches your Azure deployment.

---

## 🎯 Expected Result

After fixing the configuration:

```
✅ Worker creates task
✅ Skyvern accepts task with Azure OpenAI
✅ LLM successfully extracts job listings
✅ Jobs appear in Dashboard
```

---

## 🐛 Troubleshooting

**If still failing:**

1. Check Skyvern logs:
   ```bash
   docker logs skyvern-skyvern-1 --tail 100
   ```

2. Verify Azure credentials:
   ```bash
   curl -X POST "https://your-resource.openai.azure.com/openai/deployments/your-deployment/chat/completions?api-version=2024-02-01" \
     -H "api-key: your-api-key" \
     -H "Content-Type: application/json" \
     -d '{"messages":[{"role":"user","content":"test"}]}'
   ```

3. Check Skyvern LLM config registry:
   ```bash
   docker exec -it skyvern-skyvern-1 cat /app/.env | grep -E "LLM_KEY|AZURE"
   ```

---

## 📚 References

- Skyvern LLM Configuration: https://github.com/Skyvern-AI/skyvern/blob/main/skyvern/forge/sdk/api/llm/config_registry.py
- Azure OpenAI Setup: https://github.com/Skyvern-AI/skyvern/blob/main/.env.example
