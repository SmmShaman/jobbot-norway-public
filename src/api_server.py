"""HTTP API server for n8n integration."""
from flask import Flask, request, jsonify
import asyncio
import json
from .multi_user_system import MultiUserJobSystem
from .user_specific_workflow import run_user_workflow
from .complete_user_workflow import run_complete_user_workflow

app = Flask(__name__)

@app.route('/api/users', methods=['GET'])
def get_users():
    """Get all users status."""
    try:
        system = MultiUserJobSystem()
        users_status = system.list_users_with_status()
        return jsonify({
            "success": True,
            "users": users_status
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/user/<username>/analyze', methods=['POST'])
def analyze_user_resumes(username):
    """Analyze resumes for user."""
    try:
        system = MultiUserJobSystem()
        result = system.analyze_user_resumes(username)
        
        if 'error' in result:
            return jsonify({"success": False, "error": result['error']}), 400
        
        return jsonify({
            "success": True, 
            "message": f"Resume analysis completed for {username}",
            "profile": result
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/user/<username>/find_jobs', methods=['POST'])
def find_jobs_for_user(username):
    """Find relevant jobs for user (no applications)."""
    try:
        async def run_find_jobs():
            from .user_specific_workflow import UserSpecificWorkflow
            workflow = UserSpecificWorkflow(username)
            
            # Get user config and profile
            config = workflow.system.get_user_config(username)
            user_profile = workflow.get_user_unified_profile()
            
            nav_config = config.get("search_sources", {}).get("arbeidsplassen.nav.no", {})
            search_urls = nav_config.get("search_urls", [])
            min_relevance = config.get("user_profile", {}).get("min_relevance_score", 30)
            
            # Find jobs
            from .playwright_job_analyzer import PlaywrightJobAnalyzer
            analyzer = PlaywrightJobAnalyzer()
            all_relevant_jobs = []
            
            for search_url in search_urls[:1]:  # Test with first URL
                relevant_jobs = await analyzer.analyze_jobs_with_playwright(
                    search_url, user_profile, min_relevance
                )
                all_relevant_jobs.extend(relevant_jobs)
            
            return all_relevant_jobs
        
        # Run async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        jobs = loop.run_until_complete(run_find_jobs())
        loop.close()
        
        return jsonify({
            "success": True,
            "username": username,
            "jobs_found": len(jobs),
            "jobs": jobs
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/user/<username>/workflow', methods=['POST'])
def run_full_workflow(username):
    """Run complete workflow with applications."""
    try:
        data = request.get_json() or {}
        apply_jobs = data.get('apply_jobs', False)  # Whether to actually apply
        
        async def run_workflow():
            if apply_jobs:
                from .complete_user_workflow import run_complete_user_workflow
                await run_complete_user_workflow(username)
                return {"type": "complete", "applied": True}
            else:
                from .user_specific_workflow import run_user_workflow
                await run_user_workflow(username)
                return {"type": "find_only", "applied": False}
        
        # Run async workflow
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(run_workflow())
        loop.close()
        
        return jsonify({
            "success": True,
            "username": username,
            "workflow_type": result["type"],
            "applications_submitted": result["applied"]
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/user/<username>/jobs', methods=['GET'])
def get_user_jobs(username):
    """Get jobs from user database."""
    try:
        system = MultiUserJobSystem()
        
        # Get jobs from user's database
        import sqlite3
        from pathlib import Path
        
        user_dir = Path(f"/app/data/users/{username}")
        db_path = user_dir / "jobs.db"
        
        if not db_path.exists():
            return jsonify({"success": True, "jobs": []})
        
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM jobs 
                ORDER BY created_at DESC 
                LIMIT 20
            """)
            jobs = [dict(row) for row in cursor.fetchall()]
        
        return jsonify({
            "success": True,
            "username": username,
            "jobs_count": len(jobs),
            "jobs": jobs
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "service": "jobbot-api"})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=3000, debug=True)

@app.route('/api/user/<username>/nav_report', methods=['POST'])
def submit_nav_report(username):
    """Semi-automated NAV reporting with BankID."""
    try:
        from .bankid_automation import BankIDAutomation
        from .job_manager import JobManager
        
        # Отримуємо подані заявки користувача
        job_manager = JobManager(username)
        applied_jobs = job_manager.get_applied_jobs_today()
        
        if not applied_jobs:
            return {"success": False, "message": "No jobs applied today"}
        
        # Запускаємо semi-automated процес
        automation = BankIDAutomation()
        config = load_user_config(username)
        
        # Асинхронний виклик
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        page = loop.run_until_complete(
            automation.login_with_user_confirmation(
                'https://www.nav.no/dagpenger/meldekort',
                config['nav_credentials']['fnr'],
                config['nav_credentials']['password']
            )
        )
        
        if page:
            # Заповнюємо форму автоматично
            loop.run_until_complete(
                automation.fill_nav_report_form(applied_jobs)
            )
            return {"success": True, "jobs_reported": len(applied_jobs)}
        else:
            return {"success": False, "message": "BankID confirmation failed"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}
