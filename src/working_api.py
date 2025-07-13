from flask import Flask, jsonify, request
import sys
import os
import json
sys.path.append('/app/src')

app = Flask(__name__)

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "message": "JobBot API is running"})

@app.route('/api/users', methods=['GET'])
def get_users():
    users_dir = '/app/data/users'
    if os.path.exists(users_dir):
        users = [d for d in os.listdir(users_dir) if os.path.isdir(os.path.join(users_dir, d))]
        return jsonify({"users": users, "status": "success"})
    return jsonify({"users": [], "status": "no_users_found"})

@app.route('/api/jobs/<username>', methods=['GET'])
def find_jobs(username):
    return jsonify({"message": f"Finding jobs for {username}", "jobs": []})

@app.route('/api/apply/<username>', methods=['POST'])
def auto_apply(username):
    return jsonify({"message": f"Auto applying for {username}", "applied": 0})

@app.route('/api/workflow/<username>', methods=['POST'])
def run_workflow(username):
    try:
        return jsonify({
            "status": "success",
            "username": username,
            "message": f"Workflow started for {username}",
            "next_steps": ["scan_jobs", "analyze", "apply"]
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        })

@app.route('/api/bankid/<username>', methods=['POST'])
def run_bankid(username):
    # Завантажуємо конфіг користувача
    try:
        config_path = f'/app/data/users/{username}/config.json'
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        fnr = config.get('nav_credentials', {}).get('fnr', 'not_found')
        
        return jsonify({
            "status": "bankid_triggered",
            "username": username,
            "fnr": fnr[:3] + '***' + fnr[-2:],  # Частково приховуємо FNR
            "message": f"BankID workflow started for {username}",
            "next_step": "confirm_push_notification"
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error loading user config: {str(e)}"
        })


@app.route('/api/prompt/<username>', methods=['GET', 'POST'])
def manage_prompt(username):
    from cover_letter_generator import CoverLetterGenerator
    
    generator = CoverLetterGenerator(username)
    
    if request.method == 'GET':
        # Повертаємо поточний промпт
        prompt = generator.load_prompt_template()
        return jsonify({'prompt': prompt, 'status': 'success'})
    
    elif request.method == 'POST':
        # Оновлюємо промпт
        data = request.get_json()
        new_prompt = data.get('prompt', '')
        
        if generator.update_prompt_template(new_prompt):
            return jsonify({'status': 'success', 'message': 'Промпт оновлено'})
        else:
            return jsonify({'status': 'error', 'message': 'Помилка оновлення'})

if __name__ == '__main__':
    print('🚀 Starting JobBot API server...')
    app.run(host='0.0.0.0', port=3000, debug=True)
