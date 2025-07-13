from flask import Flask, jsonify
import sys
import os
sys.path.append('/app/src')

app = Flask(__name__)

@app.route('/api/users', methods=['GET'])
def get_users():
    users_dir = '/app/data/users'
    if os.path.exists(users_dir):
        users = [d for d in os.listdir(users_dir) if os.path.isdir(os.path.join(users_dir, d))]
        return jsonify({"users": users, "status": "success"})
    return jsonify({"users": [], "status": "no_users_found"})

@app.route('/api/workflow/<username>', methods=['POST'])
def run_workflow(username):
    try:
        import workflow_integration
        workflow = workflow_integration.WorkflowIntegration(username)
        import asyncio
        result = asyncio.run(workflow.run_daily_workflow())
        return jsonify({"status": "success", "username": username, "result": result})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/api/bankid/<username>', methods=['POST'])
def run_bankid(username):
    return jsonify({
        "status": "bankid_triggered",
        "message": f"BankID workflow started for {username}",
        "next_step": "confirm_push_notification"
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)
