"""Enhanced API server with all new AI components."""
from flask import Flask, jsonify, request
import asyncio
import sys
import os
sys.path.append('/app/src')

app = Flask(__name__)

@app.route('/api/users', methods=['GET'])
def get_users():
    """Get all users."""
    users_dir = '/app/data/users'
    if os.path.exists(users_dir):
        users = [d for d in os.listdir(users_dir) if os.path.isdir(os.path.join(users_dir, d))]
        return jsonify({"users": users, "status": "success"})
    return jsonify({"users": [], "status": "no_users_found"})

@app.route('/api/workflow/<username>', methods=['POST'])
def run_enhanced_workflow(username):
    """Run enhanced workflow for user."""
    try:
        from enhanced_workflow_integration import run_enhanced_workflow_for_user
        
        # Run async workflow
        result = asyncio.run(run_enhanced_workflow_for_user(username))
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "username": username,
            "error": str(e)
        })

@app.route('/api/generate-cover-letter', methods=['POST'])
def generate_cover_letter():
    """Generate cover letter for specific job."""
    try:
        data = request.get_json()
        username = data.get('username')
        job_data = data.get('job_data')
        
        if not username or not job_data:
            return jsonify({"error": "Missing username or job_data"}), 400
        
        from ai_cover_letter_generator import AICoverLetterGenerator
        from enhanced_workflow_integration import EnhancedWorkflowIntegration
        
        # Get user data
        workflow = EnhancedWorkflowIntegration(username)
        
        # Generate cover letter
        generator = AICoverLetterGenerator()
        result = asyncio.run(generator.generate_cover_letter(
            username, job_data, workflow.user_data["resume_data"]
        ))
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/analyze-job', methods=['POST'])
def analyze_job():
    """Analyze job relevance for user."""
    try:
        data = request.get_json()
        username = data.get('username')
        job_data = data.get('job_data')
        
        if not username or not job_data:
            return jsonify({"error": "Missing username or job_data"}), 400
        
        from ai_analyzer import analyze_job_relevance
        from enhanced_workflow_integration import EnhancedWorkflowIntegration
        
        # Get user data
        workflow = EnhancedWorkflowIntegration(username)
        user_skills = workflow._get_user_skills_summary()
        
        # Analyze job
        result = analyze_job_relevance(
            job_data.get('title', ''),
            job_data.get('description', ''),
            user_skills
        )
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/test-scraper', methods=['GET'])
def test_scraper():
    """Test multi-site scraper."""
    try:
        from multi_site_scraper import MultiSiteScraper
        
        scraper = MultiSiteScraper()
        
        # Test configuration
        test_config = {
            "search_sources": {
                "arbeidsplassen.nav.no": {
                    "enabled": True,
                    "search_urls": [
                        "https://arbeidsplassen.nav.no/stillinger?county=OSLO&v=5"
                    ]
                }
            }
        }
        
        # Run scraper test
        jobs = asyncio.run(scraper.scrape_all_sites(test_config))
        
        return jsonify({
            "status": "success",
            "jobs_found": len(jobs),
            "sample_jobs": jobs[:3] if jobs else []
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/bankid/<username>', methods=['POST'])
def run_bankid(username):
    """Trigger BankID workflow."""
    return jsonify({
        "status": "bankid_triggered",
        "message": f"BankID workflow started for {username}",
        "next_step": "confirm_push_notification"
    })

@app.route('/api/update-prompt/<username>', methods=['POST'])
def update_cover_letter_prompt(username):
    """Update user's cover letter prompt."""
    try:
        data = request.get_json()
        new_prompt = data.get('prompt')
        
        if not new_prompt:
            return jsonify({"error": "Missing prompt"}), 400
        
        from ai_cover_letter_generator import AICoverLetterGenerator
        
        generator = AICoverLetterGenerator()
        success = generator.update_user_prompt(username, new_prompt)
        
        if success:
            return jsonify({"status": "success", "message": "Prompt updated"})
        else:
            return jsonify({"error": "Failed to update prompt"}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    try:
        # Test all components
        health_status = {
            "api": "healthy",
            "components": {}
        }
        
        # Test AI Analyzer
        try:
            from ai_analyzer import analyze_job_relevance
            health_status["components"]["ai_analyzer"] = "available"
        except:
            health_status["components"]["ai_analyzer"] = "error"
        
        # Test Sheets Integration
        try:
            from enhanced_sheets_integration import EnhancedSheetsTracker
            health_status["components"]["sheets"] = "available"
        except:
            health_status["components"]["sheets"] = "error"
        
        # Test Scraper
        try:
            from multi_site_scraper import MultiSiteScraper
            health_status["components"]["scraper"] = "available"
        except:
            health_status["components"]["scraper"] = "error"
        
        # Test Cover Letter Generator
        try:
            from ai_cover_letter_generator import AICoverLetterGenerator
            health_status["components"]["cover_letter"] = "available"
        except:
            health_status["components"]["cover_letter"] = "error"
        
        return jsonify(health_status)
        
    except Exception as e:
        return jsonify({"api": "error", "error": str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get system statistics."""
    try:
        stats = {
            "users": [],
            "total_jobs": 0,
            "total_applications": 0
        }
        
        users_dir = '/app/data/users'
        if os.path.exists(users_dir):
            for username in os.listdir(users_dir):
                user_dir = os.path.join(users_dir, username)
                if os.path.isdir(user_dir):
                    user_stats = {
                        "username": username,
                        "jobs_file_exists": os.path.exists(os.path.join(user_dir, "saved_jobs.json")),
                        "letters_count": len(list(Path(user_dir).glob("letters/*.txt"))) if Path(user_dir).exists() else 0
                    }
                    stats["users"].append(user_stats)
        
        return jsonify(stats)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("🚀 Starting Enhanced JobBot API Server...")
    print("📊 Available endpoints:")
    print("  GET  /api/users")
    print("  POST /api/workflow/<username>")
    print("  POST /api/generate-cover-letter")
    print("  POST /api/analyze-job")
    print("  GET  /api/test-scraper")
    print("  POST /api/bankid/<username>")
    print("  POST /api/update-prompt/<username>")
    print("  GET  /api/health")
    print("  GET  /api/stats")
    
    app.run(host='0.0.0.0', port=3000, debug=True)
