import os
import json

class SimpleResumeReader:
    def __init__(self, username):
        self.username = username
        self.resumes_path = f'/app/data/users/{username}/resumes'
    
    def get_profile(self):
        profile = {
            'name': self.username,
            'skills': [],
            'experience_years': 0,
            'summary': ''
        }
        
        # Читаємо unified_profile.json
        json_path = os.path.join(self.resumes_path, 'unified_profile.json')
        if os.path.exists(json_path):
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    up = data['unified_profile']
                    
                    profile['name'] = up['personal_info']['name']
                    profile['experience_years'] = up['total_experience_years'] 
                    profile['summary'] = up['comprehensive_summary']
                    
                    # Навички
                    skills = up['comprehensive_skills']
                    profile['skills'].extend(skills.get('technical', []))
                    profile['skills'].extend(skills.get('soft_skills', []))
                    
                    print(f'✅ JSON профіль завантажено для {profile[name]}')
            except Exception as e:
                print(f'❌ Помилка JSON: {e}')
        
        return profile
    
    def get_ai_text(self):
        profile = self.get_profile()
        return f"""КАНДИДАТ: {profile['name']}
ДОСВІД: {profile['experience_years']} років
НАВИЧКИ: {', '.join(profile['skills'][:15])}
РЕЗЮМЕ: {profile['summary'][:500]}"""

