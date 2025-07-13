"""Fixed Enhanced API server with proper imports."""
from flask import Flask, jsonify, request
import asyncio
import sys
import os
from pathlib import Path

# Fix imports
sys.path.insert(0, '/app/src')

app = Flask(__name__)

@app.route('/api/users', methods=['GET'])
def get_users():
    """Get all users."""
    users_dir = '/app/data/users'
    if os.path.exists(users_dir):
        users = [d for d in os.listdir(users_dir) if os.path.isdir(os.path.join(users_dir, d))]
        return jsonify({"users": users, "status": "success"})
    return jsonify({"users": [], "status": "no_users_found"})

@app.route('/api/simple-workflow/<username>', methods=['POST'])
def run_simple_workflow(username):
    """Run simple workflow test."""
    try:
        import workflow_integration
        workflow = workflow_integration.WorkflowIntegration(username)
        result = asyncio.run(workflow.run_daily_workflow())
        
        return jsonify({
            "status": "success",
            "username": username,
            "result": result
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "username": username,
            "error": str(e)
        })

@app.route('/api/test-ai', methods=['POST'])
def test_ai():
    """Test AI analyzer."""
    try:
        import ai_analyzer
        
        result = ai_analyzer.analyze_job_relevance(
            "Python Developer",
            "We need Python developer with AI experience",
            "Python, AI, Machine Learning, Project Management"
        )
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/api/bankid/<username>', methods=['POST'])
def run_bankid(username):
    """Trigger BankID workflow."""
    return jsonify({
        "status": "bankid_triggered",
        "message": f"BankID workflow started for {username}",
        "next_step": "confirm_push_notification"
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    try:
        health_status = {
            "api": "healthy",
            "timestamp": str(asyncio.get_event_loop().time()),
            "components": {}
        }
        
        # Test basic imports
        try:
            import ai_analyzer
            health_status["components"]["ai_analyzer"] = "available"
        except Exception as e:
            health_status["components"]["ai_analyzer"] = f"error: {e}"
        
        try:
            import workflow_integration
            health_status["components"]["workflow"] = "available"
        except Exception as e:
            health_status["components"]["workflow"] = f"error: {e}"
        
        try:
            import telegram_bot
            health_status["components"]["telegram"] = "available"
        except Exception as e:
            health_status["components"]["telegram"] = f"error: {e}"
        
        return jsonify(health_status)
        
    except Exception as e:
        return jsonify({"api": "error", "error": str(e)}), 500

@app.route('/api/test-telegram', methods=['POST'])
def test_telegram():
    """Test Telegram integration."""
    try:
        import telegram_bot
        bot = telegram_bot.TelegramBot()
        
        # Test message
        result = bot.send_message("🧪 API Test: Enhanced JobBot system is working!")
        
        return jsonify({
            "status": "success",
            "telegram_result": result
        })
        
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    print("🚀 Starting Fixed Enhanced JobBot API Server...")
    app.run(host='0.0.0.0', port=3000, debug=True)
