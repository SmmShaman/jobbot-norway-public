#!/bin/bash
# ============================================================
# Deploy SQL Functions on VM (where DNS works)
# Run this script on your Google Cloud VM
# ============================================================

set -e

echo "======================================================================"
echo "🗄️ Deploying SQL Functions to Supabase"
echo "======================================================================"
echo ""

DB_PASSWORD="QWEpoi123987@"
DB_HOST="db.ptrmidlhfdbybxmyovtm.supabase.co"
DB_PORT="5432"
DB_NAME="postgres"
DB_USER="postgres"

CONN_STRING="postgresql://${DB_USER}@${DB_HOST}:${DB_PORT}/${DB_NAME}"

echo "🔗 Connection: ${DB_HOST}"
echo ""

# Navigate to database directory
cd "$(dirname "$0")"

# Deploy Function 1
echo "======================================================================"
echo "📤 Deploying Function 1: extract_finn_job_links()"
echo "======================================================================"
PGPASSWORD="${DB_PASSWORD}" psql "${CONN_STRING}" -f function_1_extract_links.sql -v ON_ERROR_STOP=1
echo "✅ Function 1 deployed"
echo ""

# Deploy Function 2
echo "======================================================================"
echo "📤 Deploying Function 2: create_jobs_from_finn_links()"
echo "======================================================================"
PGPASSWORD="${DB_PASSWORD}" psql "${CONN_STRING}" -f function_2_create_jobs.sql -v ON_ERROR_STOP=1
echo "✅ Function 2 deployed"
echo ""

# Deploy Function 3
echo "======================================================================"
echo "📤 Deploying Function 3: get_pending_skyvern_jobs()"
echo "======================================================================"
PGPASSWORD="${DB_PASSWORD}" psql "${CONN_STRING}" -f function_3_get_pending.sql -v ON_ERROR_STOP=1
echo "✅ Function 3 deployed"
echo ""

# Verify
echo "======================================================================"
echo "🔍 Verifying deployed functions..."
echo "======================================================================"
PGPASSWORD="${DB_PASSWORD}" psql "${CONN_STRING}" -c "
SELECT routine_name, routine_type
FROM information_schema.routines
WHERE routine_schema = 'public'
  AND routine_name IN (
    'extract_finn_job_links',
    'create_jobs_from_finn_links',
    'get_pending_skyvern_jobs'
  )
ORDER BY routine_name;
"

echo ""
echo "======================================================================"
echo "✅ DEPLOYMENT SUCCESSFUL!"
echo "======================================================================"
echo ""
echo "📋 Deployed functions:"
echo "  1. ✅ extract_finn_job_links(html_content TEXT)"
echo "  2. ✅ create_jobs_from_finn_links(user_id, scan_task_id, html_content)"
echo "  3. ✅ get_pending_skyvern_jobs(user_id, limit)"
echo ""
echo "🔄 Worker can now extract jobs from FINN.no!"
echo ""
echo "📊 Next step: Restart worker"
echo "   sudo systemctl restart worker_v2"
echo ""
echo "======================================================================"
