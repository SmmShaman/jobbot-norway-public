"""Cover letter generator with AI analysis."""
import os
import json
from datetime import datetime
from resume_loader import create_ai_prompt

class CoverLetterGenerator:
    def __init__(self, username):
        self.username = username
        self.letters_dir = f"/app/data/users/{username}/letters"
        self.prompts_dir = f"/app/data/users/{username}/prompts"
        os.makedirs(self.letters_dir, exist_ok=True)
        os.makedirs(self.prompts_dir, exist_ok=True)
        self.ensure_default_prompt()

    def ensure_default_prompt(self):
        prompt_file = os.path.join(self.prompts_dir, "cover_letter_prompt.txt")
        if not os.path.exists(prompt_file):
            default_prompt = """Создай профессиональное письмо на норвежском языке:

ВАКАНСИЯ: {job_title}
КОМПАНИЯ: {company}
ОПИСАНИЕ: {job_description}

ПРОФИЛЬ: {user_profile}

ТРЕБОВАНИЯ:
1. Норвежский язык (bokmål)
2. Профессиональный тон  
3. Максимум 200 слов
4. Подчеркни релевантный опыт

Начни с Kjære rekrutteringsteam и заверши Med vennlig hilsen"""
            
            with open(prompt_file, "w", encoding="utf-8") as f:
                f.write(default_prompt)

    def generate_cover_letter(self, job_title, company, job_description):
        """Generate cover letter for job application."""
        try:
            from openai import AzureOpenAI
            
            # Load user profile
            user_profile = create_ai_prompt(self.username)
            
            # Load prompt template
            prompt_file = os.path.join(self.prompts_dir, "cover_letter_prompt.txt")
            with open(prompt_file, "r", encoding="utf-8") as f:
                prompt_template = f.read()
            
            # Format prompt with job details
            formatted_prompt = prompt_template.format(
                job_title=job_title,
                company=company,
                job_description=job_description,
                user_profile=user_profile
            )
            
            # Generate cover letter using Azure OpenAI
            client = AzureOpenAI(
                azure_endpoint=os.getenv("OPENAI_ENDPOINT"),
                api_key=os.getenv("OPENAI_KEY"), 
                api_version="2024-05-01-preview"
            )
            response = client.chat.completions.create(
                model=os.getenv("AZURE_OPENAI_DEPLOYMENT_CHAT"),
                messages=[
                    {"role": "user", "content": formatted_prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            cover_letter = response.choices[0].message.content
            
            # Save cover letter
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_title = job_title.replace(" ", "_").replace("/", "_")
            filename = f"cover_letter_{safe_title}_{timestamp}.txt"
            letter_path = os.path.join(self.letters_dir, filename)
            
            with open(letter_path, "w", encoding="utf-8") as f:
                f.write(cover_letter)
            
            return {
                "cover_letter": cover_letter,
                "file_path": letter_path,
                "status": "success"
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "status": "error"
            }

def generate_cover_letter(username, job_title, company, job_description):
    """Generate cover letter using CoverLetterGenerator class."""
    generator = CoverLetterGenerator(username)
    return generator.generate_cover_letter(job_title, company, job_description)
