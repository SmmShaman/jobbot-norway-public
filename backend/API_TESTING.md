# 🧪 API Testing Guide

## Quick Start

### Local Testing

1. **Start backend:**
```bash
cd backend
./start_dev.sh
```

2. **Access API docs:**
```
http://localhost:8000/docs
```

3. **Test health endpoint:**
```bash
curl http://localhost:8000/health
```

---

## API Endpoints

### 🏥 Health Check

**GET** `/health`

```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy"
}
```

---

### 👤 Settings Endpoints

#### Get User Profile

**GET** `/api/settings/profile/{user_id}`

```bash
curl http://localhost:8000/api/settings/profile/YOUR_USER_ID
```

#### Update User Profile

**PUT** `/api/settings/profile/{user_id}`

```bash
curl -X PUT http://localhost:8000/api/settings/profile/YOUR_USER_ID \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "John Doe",
    "phone": "+47 123 45 678",
    "fnr": "12345678901"
  }'
```

#### Get User Settings

**GET** `/api/settings/settings/{user_id}`

```bash
curl http://localhost:8000/api/settings/settings/YOUR_USER_ID
```

#### Update User Settings

**PUT** `/api/settings/settings/{user_id}`

```bash
curl -X PUT http://localhost:8000/api/settings/settings/YOUR_USER_ID \
  -H "Content-Type: application/json" \
  -d '{
    "nav_search_urls": [
      "https://arbeidsplassen.nav.no/stillinger?county=OSLO"
    ],
    "min_relevance_score": 75,
    "telegram_enabled": true
  }'
```

#### Upload Resume

**POST** `/api/settings/resume/{user_id}`

```bash
curl -X POST http://localhost:8000/api/settings/resume/YOUR_USER_ID \
  -F "file=@/path/to/resume.pdf"
```

---

### 💼 Jobs Endpoints

#### Scan Jobs Now

**POST** `/api/scan-jobs`

```bash
curl -X POST http://localhost:8000/api/scan-jobs \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "YOUR_USER_ID",
    "scan_type": "MANUAL"
  }'
```

**Response:**
```json
{
  "message": "Job scan completed successfully",
  "user_id": "abc-123",
  "scan_type": "MANUAL",
  "stats": {
    "total_found": 25,
    "new_jobs": 12,
    "analyzed": 12,
    "relevant": 5
  }
}
```

#### Get All Jobs

**POST** `/api/jobs`

```bash
curl -X POST http://localhost:8000/api/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "YOUR_USER_ID",
    "status": "ANALYZED"
  }'
```

**Response:**
```json
{
  "jobs": [
    {
      "id": "job-uuid-1",
      "title": "Python Developer",
      "company": "TechCorp AS",
      "location": "Oslo",
      "relevance_score": 85,
      "status": "ANALYZED",
      "ai_analysis": {
        "recommendation": "APPLY",
        "match_reasons": ["Strong Python skills", "Good location match"],
        "concerns": ["Requires 5+ years experience"]
      }
    }
  ],
  "count": 1
}
```

#### Re-analyze Single Job

**POST** `/api/analyze-job`

```bash
curl -X POST http://localhost:8000/api/analyze-job \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "YOUR_USER_ID",
    "job_id": "JOB_UUID"
  }'
```

#### Approve Job for Application

**POST** `/api/approve-job`

```bash
curl -X POST http://localhost:8000/api/approve-job \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "YOUR_USER_ID",
    "job_id": "JOB_UUID"
  }'
```

#### Get Dashboard Stats

**GET** `/api/dashboard-stats/{user_id}`

```bash
curl http://localhost:8000/api/dashboard-stats/YOUR_USER_ID
```

**Response:**
```json
{
  "total_jobs": 50,
  "new_jobs": 10,
  "analyzed_jobs": 35,
  "applied_jobs": 5,
  "total_applications": 5,
  "applications_this_week": 3
}
```

---

## Integration Testing

### Test Complete Workflow

```bash
#!/bin/bash

USER_ID="your-test-user-id"
API_URL="http://localhost:8000"

echo "1️⃣ Testing health..."
curl $API_URL/health

echo "\n2️⃣ Getting user profile..."
curl $API_URL/api/settings/profile/$USER_ID

echo "\n3️⃣ Updating settings..."
curl -X PUT $API_URL/api/settings/settings/$USER_ID \
  -H "Content-Type: application/json" \
  -d '{
    "nav_search_urls": ["https://arbeidsplassen.nav.no/stillinger?county=OSLO"],
    "min_relevance_score": 70
  }'

echo "\n4️⃣ Triggering job scan..."
curl -X POST $API_URL/api/scan-jobs \
  -H "Content-Type: application/json" \
  -d "{\"user_id\": \"$USER_ID\", \"scan_type\": \"MANUAL\"}"

echo "\n5️⃣ Getting dashboard stats..."
curl $API_URL/api/dashboard-stats/$USER_ID

echo "\n6️⃣ Getting all jobs..."
curl -X POST $API_URL/api/jobs \
  -H "Content-Type: application/json" \
  -d "{\"user_id\": \"$USER_ID\"}"

echo "\n✅ All tests completed!"
```

---

## Using FastAPI Swagger UI

The easiest way to test APIs:

1. **Open browser:**
```
http://localhost:8000/docs
```

2. **You'll see interactive API documentation**

3. **To test an endpoint:**
   - Click on endpoint
   - Click "Try it out"
   - Fill in parameters
   - Click "Execute"
   - See response below!

4. **Example - Test Scan Jobs:**
   - Expand `POST /api/scan-jobs`
   - Click "Try it out"
   - Fill in:
     ```json
     {
       "user_id": "your-test-user-id",
       "scan_type": "MANUAL"
     }
     ```
   - Click "Execute"
   - Watch the magic happen! ✨

---

## Common Issues

### ❌ "User settings not found"

**Cause:** Settings don't exist for user

**Solution:**
```bash
# Settings are auto-created on first GET
curl http://localhost:8000/api/settings/settings/YOUR_USER_ID
```

### ❌ "No search URLs configured"

**Cause:** User hasn't added any NAV or FINN URLs

**Solution:**
```bash
curl -X PUT http://localhost:8000/api/settings/settings/YOUR_USER_ID \
  -H "Content-Type: application/json" \
  -d '{
    "nav_search_urls": [
      "https://arbeidsplassen.nav.no/stillinger?county=OSLO"
    ]
  }'
```

### ❌ Connection refused

**Cause:** Backend not running

**Solution:**
```bash
cd backend
./start_dev.sh
```

### ❌ "Internal Server Error"

**Cause:** Check backend logs

**Solution:**
- Look at terminal where backend is running
- Common issues:
  - Missing environment variables
  - Supabase connection failed
  - Azure OpenAI key invalid

---

## Load Testing

### Using Apache Bench

```bash
# Test health endpoint - 1000 requests, 10 concurrent
ab -n 1000 -c 10 http://localhost:8000/health

# Test with POST data
ab -n 100 -c 5 -p request.json -T application/json \
  http://localhost:8000/api/scan-jobs
```

### Using Python requests

```python
import requests
import time

API_URL = "http://localhost:8000"
USER_ID = "test-user-id"

# Test response time
start = time.time()
response = requests.get(f"{API_URL}/api/settings/profile/{USER_ID}")
end = time.time()

print(f"Status: {response.status_code}")
print(f"Response time: {(end - start) * 1000:.2f}ms")
print(f"Response: {response.json()}")
```

---

## Monitoring Logs

### Backend Logs

Watch logs in real-time:
```bash
# In terminal where backend is running
# You'll see:
# - 🔍 Fetching job links
# - 📖 Fetching job details
# - 🤖 AI Score: 85% - APPLY
# - ✅ Job saved
```

### Supabase Logs

Monitor in Supabase Dashboard:
- Go to Supabase → Logs
- Filter by table (jobs, applications, monitoring_logs)

---

## Next Steps

1. ✅ Test all endpoints locally
2. ✅ Deploy to Railway
3. ✅ Test production endpoints
4. ✅ Integrate with frontend
5. 🎉 Celebrate! You have a working API!
