#!/bin/bash
# ====================================================================
# 🔧 ШВИДКЕ ВИПРАВЛЕННЯ: Встановити відсутні залежності
# ====================================================================

echo "======================================================================"
echo "🔧 Installing Missing Dependencies"
echo "======================================================================"
echo ""

cd /home/stuard/jobbot-norway-public/worker

# Перевірка чи є venv
if [ -d "venv" ]; then
    echo "✅ Virtual environment exists: venv/"
    echo "📦 Activating venv and installing supabase..."

    source venv/bin/activate
    pip install supabase==2.7.4

    echo ""
    echo "✅ supabase installed in venv!"

else
    echo "❌ No venv found. Installing globally..."
    pip3 install supabase==2.7.4

    echo ""
    echo "✅ supabase installed globally!"
fi

echo ""
echo "======================================================================"
echo "✅ Dependencies Fixed!"
echo "======================================================================"
echo ""
echo "📋 Verification:"
python3 -c "import supabase; print('✅ supabase import works')"
python3 -c "from playwright.sync_api import sync_playwright; print('✅ playwright import works')"

echo ""
echo "🎯 Next: Worker restart будe автоматично підхопить зміни"
