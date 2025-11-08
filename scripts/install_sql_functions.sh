#!/bin/bash

# Script to install SQL functions to Supabase
# Requires: SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables

set -e

echo "🔧 Installing SQL functions to Supabase..."
echo ""

# Check environment variables
if [ -z "$SUPABASE_URL" ]; then
    echo "❌ SUPABASE_URL is not set!"
    echo "Export it: export SUPABASE_URL='https://your-project.supabase.co'"
    exit 1
fi

if [ -z "$SUPABASE_SERVICE_KEY" ]; then
    echo "❌ SUPABASE_SERVICE_KEY is not set!"
    echo "Export it: export SUPABASE_SERVICE_KEY='your-service-key'"
    exit 1
fi

echo "✅ Environment variables found"
echo "📡 Supabase URL: $SUPABASE_URL"
echo ""

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SQL_FILE="$SCRIPT_DIR/../database/finn_link_extractor_function.sql"

if [ ! -f "$SQL_FILE" ]; then
    echo "❌ SQL file not found: $SQL_FILE"
    exit 1
fi

echo "📄 SQL file: $SQL_FILE"
echo ""

# Extract project ID from URL
PROJECT_ID=$(echo $SUPABASE_URL | sed 's/https:\/\/\(.*\)\.supabase\.co/\1/')
echo "🆔 Project ID: $PROJECT_ID"
echo ""

# Try to execute SQL using Supabase Management API
echo "🚀 Executing SQL functions..."
echo ""

# Read SQL file content
SQL_CONTENT=$(cat "$SQL_FILE")

# Execute via REST API (Supabase Data API doesn't support raw SQL)
# We need to use PostgREST or direct PostgreSQL connection

echo "⚠️  Note: Supabase REST API doesn't support raw SQL execution from scripts."
echo ""
echo "📋 Please execute the SQL manually:"
echo "   1. Open: https://supabase.com/dashboard/project/$PROJECT_ID/sql/new"
echo "   2. Copy the content from: $SQL_FILE"
echo "   3. Paste and click 'Run'"
echo ""
echo "Or if you have PostgreSQL connection string, use psql:"
echo "   psql 'postgresql://postgres:[YOUR-PASSWORD]@db.$PROJECT_ID.supabase.co:5432/postgres' < $SQL_FILE"
echo ""

# Alternative: Show instructions for using supabase CLI
echo "💡 Or install Supabase CLI and run:"
echo "   supabase login"
echo "   supabase db push --db-url 'your-connection-string'"
echo ""

exit 0
