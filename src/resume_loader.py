import os
import json

def load_user_resume(username):
    """Завантажує резюме користувача"""
    resumes_path = f'/app/data/users/{username}/resumes'
    
    result = {
        'candidate_name': username,
        'experience_years': 0,
        'skills_list': [],
        'summary_text': '',
        'files_found': []
    }
    
    # Читаємо unified_profile.json
    json_file = os.path.join(resumes_path, 'unified_profile.json')
    if os.path.exists(json_file):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                profile = data['unified_profile']
                
                result['candidate_name'] = profile['personal_info']['name']
                result['experience_years'] = profile['total_experience_years']
                result['summary_text'] = profile['comprehensive_summary']
                
                # Збираємо навички
                skills = profile['comprehensive_skills']
                result['skills_list'].extend(skills.get('technical', []))
                result['skills_list'].extend(skills.get('soft_skills', []))
                
                result['files_found'].append('unified_profile.json')
                
        except Exception as e:
            print(f'Помилка читання JSON: {e}')
    
    # Читаємо resume.txt
    txt_file = os.path.join(resumes_path, 'resume.txt')
    if os.path.exists(txt_file):
        result['files_found'].append('resume.txt')
    
    return result

def create_ai_prompt(username):
    """Створює текст для AI аналізу"""
    resume_data = load_user_resume(username)
    
    prompt = f"""КАНДИДАТ: {resume_data['candidate_name']}
ДОСВІД РОБОТИ: {resume_data['experience_years']} років
КЛЮЧОВІ НАВИЧКИ: {', '.join(resume_data['skills_list'][:20])}

ДЕТАЛЬНЕ РЕЗЮМЕ:
{resume_data['summary_text'][:600]}

ФАЙЛИ РЕЗЮМЕ: {', '.join(resume_data['files_found'])}
"""
    return prompt

