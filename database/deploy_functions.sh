#!/bin/bash
# ============================================================
# Deploy SQL Functions to Supabase
# This script deploys the FINN.no extraction functions
# ============================================================

set -e  # Exit on error

echo "=========================================="
echo "🚀 Deploying SQL Functions to Supabase"
echo "=========================================="

# Check if SUPABASE_SERVICE_KEY is set
if [ -z "$SUPABASE_SERVICE_KEY" ]; then
    echo "❌ ERROR: SUPABASE_SERVICE_KEY environment variable not set!"
    exit 1
fi

SUPABASE_URL="https://ptrmidlhfdbybxmyovtm.supabase.co"
SQL_FILE="/home/stuard/jobbot-norway-public/database/finn_link_extractor_function.sql"

echo "📄 Reading SQL file: $SQL_FILE"

if [ ! -f "$SQL_FILE" ]; then
    echo "❌ ERROR: SQL file not found: $SQL_FILE"
    exit 1
fi

# Read the SQL file
SQL_CONTENT=$(cat "$SQL_FILE")

echo "📤 Sending SQL to Supabase..."
echo ""

# Execute SQL via Supabase REST API
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST \
    "${SUPABASE_URL}/rest/v1/rpc/exec_sql" \
    -H "apikey: ${SUPABASE_SERVICE_KEY}" \
    -H "Authorization: Bearer ${SUPABASE_SERVICE_KEY}" \
    -H "Content-Type: application/json" \
    -d "{\"query\": $(echo "$SQL_CONTENT" | jq -Rs .)}" 2>&1)

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)

echo "📊 Response Code: $HTTP_CODE"
echo "📊 Response Body: $BODY"
echo ""

if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "201" ]; then
    echo "✅ SQL functions deployed successfully!"
    echo ""
    echo "📋 Deployed functions:"
    echo "  1. extract_finn_job_links(html_content TEXT)"
    echo "  2. create_jobs_from_finn_links(user_id, scan_task_id, html_content)"
    echo "  3. get_pending_skyvern_jobs(user_id, limit)"
    echo ""
else
    echo "⚠️ Deployment via REST API failed. Trying alternative method..."
    echo ""

    # Alternative: Use psql if available
    if command -v psql &> /dev/null; then
        echo "🔧 Attempting deployment via psql..."

        # Construct DATABASE_URL from Supabase URL
        # Format: postgresql://postgres:[PASSWORD]@[HOST]/postgres
        DB_HOST="db.ptrmidlhfdbybxmyovtm.supabase.co"

        # Note: This requires database password, not service key
        echo "⚠️ psql requires database password (different from service key)"
        echo "You can find it in Supabase Dashboard → Settings → Database → Connection string"
        echo ""
        echo "To deploy manually with psql:"
        echo "  psql 'postgresql://postgres:[YOUR_DB_PASSWORD]@${DB_HOST}/postgres' -f ${SQL_FILE}"
        exit 1
    else
        echo "❌ Deployment failed and psql not available"
        echo ""
        echo "📋 Manual deployment steps:"
        echo "1. Open Supabase Dashboard: https://supabase.com/dashboard/project/ptrmidlhfdbybxmyovtm"
        echo "2. Go to SQL Editor"
        echo "3. Copy content from: ${SQL_FILE}"
        echo "4. Paste and click 'Run'"
        exit 1
    fi
fi

echo "=========================================="
echo "✅ Deployment Complete!"
echo "=========================================="
