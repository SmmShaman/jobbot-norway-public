#!/usr/bin/env python3
from flask import Flask, jsonify, request
import sys
import os
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime

sys.path.append('/app/src')
app = Flask(__name__)

def load_azure_config():
    config = {}
    try:
        with open('/app/.env', 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    config[key] = value
    except:
        pass
    return config

azure_config = load_azure_config()

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "message": "Fixed Enhanced JobBot API"})

@app.route('/api/users', methods=['GET'])
def get_users():
    users_dir = '/app/data/users'
    if os.path.exists(users_dir):
        users = [d for d in os.listdir(users_dir) if os.path.isdir(os.path.join(users_dir, d))]
        return jsonify({"users": users, "status": "success"})
    return jsonify({"users": [], "status": "no_users_found"})

@app.route('/api/jobs/<username>', methods=['GET'])
def find_jobs_real(username):
    """ВИПРАВЛЕНИЙ реальний пошук вакансій + AI аналіз"""
    try:
        print(f"🔍 Starting FIXED job search for {username}")
        
        # 1. Завантажити конфіг користувача
        user_config = load_user_config(username)
        if not user_config:
            return jsonify({"error": "User config not found", "jobs": []})
        
        # 2. Скрапити arbeidsplassen.nav.no з правильними селекторами
        jobs = scrape_nav_jobs_fixed(user_config)
        print(f"📊 Found {len(jobs)} jobs from NAV")
        
        # 3. AI аналіз кожної вакансії
        analyzed_jobs = []
        for i, job in enumerate(jobs[:5]):  # Обмежити 5 для тестування
            print(f"🤖 Analyzing job {i+1}: {job['title']}")
            analysis = analyze_job_with_ai(job, user_config, username)
            job.update(analysis)
            analyzed_jobs.append(job)
        
        # 4. Сортувати за релевантністю
        analyzed_jobs.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        # 5. Зберегти в Google Sheets (мокап поки)
        save_to_sheets_log(username, analyzed_jobs)
        
        return jsonify({
            "username": username,
            "jobs": analyzed_jobs,
            "jobs_found": len(analyzed_jobs),
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"❌ Error in find_jobs_real: {e}")
        return jsonify({"error": str(e), "jobs": []})

def load_user_config(username):
    """Завантажити конфіг користувача"""
    try:
        config_path = f'/app/data/users/{username}/config.json'
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error loading config for {username}: {e}")
        return None

def scrape_nav_jobs_fixed(user_config):
    """ВИПРАВЛЕНИЙ scraper з правильними селекторами"""
    jobs = []
    
    # URL для Østre Toten + Vestre Toten
    nav_url = "https://arbeidsplassen.nav.no/stillinger?county=INNLANDET&v=5&municipal=INNLANDET.%C3%98STRE+TOTEN&municipal=INNLANDET.VESTRE+TOTEN"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(nav_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Знайти всі статті
        job_articles = soup.find_all('article')
        print(f"🔍 Found {len(job_articles)} articles")
        
        for i, article in enumerate(job_articles[:10]):  # Обмежити 10 для тестування
            try:
                # Назва вакансії - h2 тег
                title_elem = article.find('h2')
                title = title_elem.get_text(strip=True) if title_elem else f"Job {i+1}"
                
                # Компанія - пошук в aria-label або тексті
                aria_label = article.get('aria-label', '')
                company = "Unknown company"
                if ', ' in aria_label:
                    parts = aria_label.split(', ')
                    if len(parts) >= 2:
                        company = parts[1]
                
                # Посилання на вакансію
                link_elem = article.find('a', href=True)
                job_url = ""
                if link_elem:
                    href = link_elem['href']
                    if href.startswith('/'):
                        job_url = "https://arbeidsplassen.nav.no" + href
                    else:
                        job_url = href
                
                # Локація з aria-label
                location = "Østre Toten / Vestre Toten"
                if len(aria_label.split(', ')) >= 3:
                    location = aria_label.split(', ')[2]
                
                job_data = {
                    'title': title,
                    'company': company,
                    'location': location,
                    'url': job_url,
                    'source': 'arbeidsplassen.nav.no',
                    'scraped_at': datetime.now().isoformat(),
                    'aria_label': aria_label  # Для debug
                }
                
                jobs.append(job_data)
                print(f"✅ Job {i+1}: {title} at {company}")
                
            except Exception as e:
                print(f"⚠️ Error parsing job {i+1}: {e}")
                continue
        
        print(f"✅ Successfully scraped {len(jobs)} jobs from NAV")
        return jobs
        
    except Exception as e:
        print(f"❌ Error scraping NAV: {e}")
        return []

def analyze_job_with_ai(job, user_config, username):
    """AI аналіз релевантності вакансії"""
    try:
        user_info = user_config.get('user_info', {})
        
        # Prompt для Azure OpenAI
        prompt = f"""Проаналізуйте релевантність вакансії для кандидата в Норвегії:

ВАКАНСІЯ:
Назва: {job['title']}
Компанія: {job['company']}
Локація: {job['location']}

КАНДИДАТ ({username}):
Ім'я: {user_info.get('full_name', 'N/A')}
Поточна позиція: {user_info.get('current_position', 'N/A')}
Навички: {', '.join(user_info.get('skills', []))}
Освіта: {user_info.get('education', 'N/A')}
Мови: {', '.join(user_info.get('languages', []))}
Досвід: {user_info.get('years_experience', 'N/A')}

ЗАВДАННЯ:
Оцініть релевантність від 0 до 100 та дайте короткий коментар українською.

ФОРМАТ ВІДПОВІДІ JSON:
{{
  "relevance_score": 85,
  "reasoning": "Короткий коментар чому така оцінка",
  "key_matches": ["Python", "Management"],
  "recommendation": "APPLY"
}}"""

        # Викликати Azure OpenAI
        ai_response = call_azure_openai(prompt)
        
        try:
            # Очистити відповідь від можливих markdown блоків
            clean_response = ai_response.strip()
            if clean_response.startswith('```json'):
                clean_response = clean_response[7:]
            if clean_response.endswith('```'):
                clean_response = clean_response[:-3]
            
            result = json.loads(clean_response)
            return {
                'relevance_score': result.get('relevance_score', 50),
                'ai_reasoning': result.get('reasoning', 'AI analysis completed'),
                'key_matches': result.get('key_matches', []),
                'recommendation': result.get('recommendation', 'REVIEW')
            }
        except Exception as parse_error:
            print(f"⚠️ JSON parse error: {parse_error}")
            print(f"Raw AI response: {ai_response[:200]}...")
            # Fallback аналіз
            return {
                'relevance_score': 60,
                'ai_reasoning': 'AI analysis completed (JSON parse error)',
                'key_matches': [],
                'recommendation': 'REVIEW'
            }
            
    except Exception as e:
        print(f"❌ AI analysis error: {e}")
        return {
            'relevance_score': 50,
            'ai_reasoning': f'Error: {str(e)}',
            'key_matches': [],
            'recommendation': 'REVIEW'
        }

def call_azure_openai(prompt):
    """Викликати Azure OpenAI API"""
    try:
        endpoint = azure_config.get('OPENAI_ENDPOINT', '').rstrip('/')
        key = azure_config.get('OPENAI_KEY', '')
        deployment = azure_config.get('AZURE_OPENAI_DEPLOYMENT_CHAT', '')
        
        if not all([endpoint, key, deployment]):
            return '{"relevance_score": 50, "reasoning": "Azure config missing"}'
        
        url = f"{endpoint}/openai/deployments/{deployment}/chat/completions?api-version=2024-02-01"
        
        headers = {
            "Content-Type": "application/json",
            "api-key": key
        }
        
        payload = {
            "messages": [
                {"role": "system", "content": "Ви експерт з аналізу релевантності вакансій в Норвегії. Відповідайте тільки JSON без додаткового тексту."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 500,
            "temperature": 0.3
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            return data['choices'][0]['message']['content'].strip()
        else:
            print(f"❌ Azure API error: {response.status_code}")
            return '{"relevance_score": 50, "reasoning": "API error"}'
            
    except Exception as e:
        print(f"❌ Azure API exception: {e}")
        return f'{{"relevance_score": 50, "reasoning": "Exception: {str(e)}"}}'

def save_to_sheets_log(username, jobs):
    """Зберегти результати в локальний лог"""
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = f'/app/data/sheets_log_{username}_{timestamp}.json'
        
        log_data = []
        for job in jobs:
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'candidate': username,
                'job_title': job['title'],
                'company': job['company'],
                'location': job['location'],
                'relevance_score': f"{job.get('relevance_score', 0)}%",
                'ai_reasoning': job.get('ai_reasoning', ''),
                'key_matches': ', '.join(job.get('key_matches', [])),
                'recommendation': job.get('recommendation', 'REVIEW'),
                'applied': 'No',
                'application_status': 'Analyzed',
                'job_url': job['url']
            }
            log_data.append(log_entry)
        
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Saved {len(log_data)} jobs to {log_file}")
        
    except Exception as e:
        print(f"❌ Error saving to sheets log: {e}")

@app.route('/api/workflow/<username>', methods=['POST'])
def run_workflow_real(username):
    """РЕАЛЬНИЙ workflow: form filling + NAV reporting"""
    try:
        return jsonify({
            "status": "success",
            "username": username,
            "message": "Real workflow - TODO: integrate form filler",
            "applied_jobs": 0,
            "nav_reported": False
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    print('🚀 Starting FIXED Enhanced JobBot API server...')
    print('✅ Real scraping + AI analysis with CORRECT selectors')
    app.run(host='0.0.0.0', port=3000, debug=True)
