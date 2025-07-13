import os
import json
from pathlib import Path

class EnhancedResumeReader:
    def __init__(self, username):
        self.username = username
        self.resumes_path = f'/app/data/users/{username}/resumes'
    
    def scan_all_files(self):
        """Сканує ВСІ файли в папці resumes/"""
        if not os.path.exists(self.resumes_path):
            os.makedirs(self.resumes_path, exist_ok=True)
            return {}
        
        files_found = {
            'txt_files': [],
            'json_files': [], 
            'pdf_files': [],
            'other_files': []
        }
        
        for file in os.listdir(self.resumes_path):
            file_path = os.path.join(self.resumes_path, file)
            if os.path.isfile(file_path):
                if file.endswith('.txt'):
                    files_found['txt_files'].append(file)
                elif file.endswith('.json'):
                    files_found['json_files'].append(file)
                elif file.endswith('.pdf'):
                    files_found['pdf_files'].append(file)
                else:
                    files_found['other_files'].append(file)
        
        return files_found
    
    def merge_all_content(self):
        """Об'єднує контент з УСІХ файлів"""
        files = self.scan_all_files()
        
        merged_profile = {
            'name': self.username,
            'skills': [],
            'experience_years': 0,
            'summaries': [],
            'all_text': [],
            'files_processed': []
        }
        
        # Читаємо всі TXT файли
        for txt_file in files['txt_files']:
            try:
                file_path = os.path.join(self.resumes_path, txt_file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    merged_profile['all_text'].append(f'=== {txt_file} ===\n{content}')
                    merged_profile['files_processed'].append(txt_file)
                print(f'✅ Прочитано: {txt_file}')
            except Exception as e:
                print(f'❌ Помилка {txt_file}: {e}')
        
        # Читаємо JSON файли
        for json_file in files['json_files']:
            try:
                file_path = os.path.join(self.resumes_path, json_file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    if 'unified_profile' in data:
                        up = data['unified_profile']
                        
                        # Ім'я
                        if 'personal_info' in up and 'name' in up['personal_info']:
                            merged_profile['name'] = up['personal_info']['name']
                        
                        # Досвід
                        if 'total_experience_years' in up:
                            merged_profile['experience_years'] = up['total_experience_years']
                        
                        # Резюме
                        if 'comprehensive_summary' in up:
                            merged_profile['summaries'].append(up['comprehensive_summary'])
                        
                        # Навички
                        if 'comprehensive_skills' in up:
                            skills_data = up['comprehensive_skills']
                            if 'technical' in skills_data:
                                merged_profile['skills'].extend(skills_data['technical'])
                            if 'soft_skills' in skills_data:
                                merged_profile['skills'].extend(skills_data['soft_skills'])
                    
                    merged_profile['files_processed'].append(json_file)
                    print(f'✅ Прочитано: {json_file}')
                    
            except Exception as e:
                print(f'❌ Помилка {json_file}: {e}')
        
        # PDF файли
        for pdf_file in files['pdf_files']:
            merged_profile['all_text'].append(f'=== PDF: {pdf_file} ===\nPDF резюме файл')
            merged_profile['files_processed'].append(pdf_file)
        
        return merged_profile
    
    def get_ai_analysis_text(self):
        """Створює оптимізований текст для AI аналізу"""
        profile = self.merge_all_content()
        
        # Об'єднуємо всі резюме в одне
        combined_summary = ' '.join(profile['summaries'])
        
        analysis_text = f"""ПРОФІЛЬ КАНДИДАТА: {profile['name']}

ДОСВІД: {profile['experience_years']} років

КЛЮЧОВІ НАВИЧКИ: {', '.join(profile['skills'][:20])}

РЕЗЮМЕ: {combined_summary[:800]}

ДОДАТКОВА ІНФОРМАЦІЯ:
{' '.join(profile['all_text'])[:1000]}

ФАЙЛИ ОБРОБЛЕННІ: {', '.join(profile['files_processed'])}
"""
        return analysis_text.strip()

