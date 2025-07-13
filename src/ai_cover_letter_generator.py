"""AI-powered cover letter generator for individual job applications."""
import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
from openai import AzureOpenAI

class AICoverLetterGenerator:
    def __init__(self):
        self.client = AzureOpenAI(
            azure_endpoint=os.getenv("OPENAI_ENDPOINT"),
            api_key=os.getenv("OPENAI_KEY"),
            api_version="2024-05-01-preview"
        )
    
    def load_user_prompt(self, username: str) -> str:
        """Load user's custom prompt for cover letter generation."""
        prompt_file = Path(f"~/jobbot/data/users/{username}/cover_letter_prompt.txt").expanduser()
        
        if prompt_file.exists():
            return prompt_file.read_text(encoding='utf-8')
        else:
            # Create default prompt
            default_prompt = self._get_default_prompt(username)
            prompt_file.parent.mkdir(parents=True, exist_ok=True)
            prompt_file.write_text(default_prompt, encoding='utf-8')
            return default_prompt
    
    def _get_default_prompt(self, username: str) -> str:
        """Get default cover letter prompt for user."""
        return f"""
Ти професійний писарь cover letters. Створи персоналізований cover letter для користувача {username}.

ІНСТРУКЦІЇ:
1. Використовуй інформацію з резюме користувача
2. Адаптуй під конкретну вакансію та компанію
3. Пиши на норвезькій мові (bokmål)
4. Довжина: 200-400 слів
5. Структура: Вступ → Досвід → Мотивація → Заключення
6. Тон: Професійний, але теплий
7. Підкресли релевантний досвід та навички

ОСОБЛИВОСТІ СТИЛЮ:
- Конкретні приклади досягнень
- Зв'язок з цілями компанії
- Ентузіазм щодо ролі
- Норвезькі фрази та етикет

Завжди закінчуй: "Jeg ser frem til å høre fra dere."
        """
    
    async def generate_cover_letter(self, username: str, job_data: Dict[str, Any], 
                                   user_resume: Dict[str, Any]) -> Dict[str, Any]:
        """Generate personalized cover letter for specific job."""
        try:
            # Load user's custom prompt
            user_prompt = self.load_user_prompt(username)
            
            # Prepare job and resume data
            job_title = job_data.get('title', '')
            company = job_data.get('company', '')
            job_description = job_data.get('description', '')[:2000]  # Limit length
            
            # Extract key resume info
            resume_summary = user_resume.get('comprehensive_summary', '')
            experience = user_resume.get('all_work_experience', [])
            skills = user_resume.get('comprehensive_skills', {})
            
            # Build the complete prompt
            complete_prompt = f"""
{user_prompt}

ВАКАНСІЯ:
Назва: {job_title}
Компанія: {company}
Опис: {job_description}

РЕЗЮМЕ КОРИСТУВАЧА:
Профіль: {resume_summary}

Досвід роботи:
{self._format_experience(experience[:3])}  # Top 3 experiences

Навички:
Технічні: {', '.join(skills.get('technical', [])[:10])}
М'які навички: {', '.join(skills.get('soft_skills', [])[:5])}
Мови: {self._format_languages(skills.get('languages', []))}

ЗАВДАННЯ:
Створи унікальний cover letter для цієї конкретної вакансії.
Поверни ТІЛЬКИ текст cover letter (без заголовків чи форматування).
"""

            response = self.client.chat.completions.create(
                model=os.getenv("AZURE_OPENAI_DEPLOYMENT_CHAT", "gpt-4"),
                messages=[
                    {"role": "system", "content": "Ти експерт з написання cover letters на норвезькій мові."},
                    {"role": "user", "content": complete_prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            cover_letter_text = response.choices[0].message.content.strip()
            
            # Save to file
            cover_letter_path = self._save_cover_letter(username, job_data, cover_letter_text)
            
            print(f"✅ Generated cover letter for {job_title} at {company}")
            
            return {
                "success": True,
                "cover_letter": cover_letter_text,
                "file_path": cover_letter_path,
                "word_count": len(cover_letter_text.split()),
                "language": "norwegian"
            }
            
        except Exception as e:
            print(f"❌ Cover letter generation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "cover_letter": "",
                "file_path": ""
            }
    
    def _format_experience(self, experiences: list) -> str:
        """Format work experience for prompt."""
        formatted = []
        for exp in experiences:
            period = exp.get('period', '')
            role = exp.get('role', '')
            company = exp.get('company', '')
            formatted.append(f"• {period}: {role} at {company}")
        return '\n'.join(formatted)
    
    def _format_languages(self, languages: list) -> str:
        """Format languages for prompt."""
        formatted = []
        for lang in languages:
            name = lang.get('language', '')
            level = lang.get('spoken', '')
            formatted.append(f"{name} ({level})")
        return ', '.join(formatted)
    
    def _save_cover_letter(self, username: str, job_data: Dict[str, Any], 
                          cover_letter: str) -> str:
        """Save cover letter to file."""
        try:
            # Create filename
            job_title = job_data.get('title', 'job').replace(' ', '_').replace('/', '_')
            company = job_data.get('company', 'company').replace(' ', '_').replace('/', '_')
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            filename = f"cover_letter_{job_title}_{company}_{timestamp}.txt"
            
            # Save path
            letters_dir = Path(f"~/jobbot/data/users/{username}/letters").expanduser()
            letters_dir.mkdir(parents=True, exist_ok=True)
            file_path = letters_dir / filename
            
            # Write file
            file_path.write_text(cover_letter, encoding='utf-8')
            
            print(f"💾 Saved cover letter: {file_path}")
            return str(file_path)
            
        except Exception as e:
            print(f"❌ Error saving cover letter: {e}")
            return ""
    
    def update_user_prompt(self, username: str, new_prompt: str) -> bool:
        """Update user's custom cover letter prompt."""
        try:
            prompt_file = Path(f"~/jobbot/data/users/{username}/cover_letter_prompt.txt").expanduser()
            prompt_file.parent.mkdir(parents=True, exist_ok=True)
            prompt_file.write_text(new_prompt, encoding='utf-8')
            print(f"✅ Updated cover letter prompt for {username}")
            return True
        except Exception as e:
            print(f"❌ Error updating prompt: {e}")
            return False
    
    def generate_pdf_cover_letter(self, username: str, job_data: Dict[str, Any], 
                                cover_letter_text: str) -> str:
        """Generate PDF version of cover letter."""
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            from reportlab.lib.units import cm
            
            # Create filename
            job_title = job_data.get('title', 'job').replace(' ', '_')
            company = job_data.get('company', 'company').replace(' ', '_')
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            filename = f"cover_letter_{job_title}_{company}_{timestamp}.pdf"
            
            # Save path
            letters_dir = Path(f"~/jobbot/data/users/{username}/letters").expanduser()
            letters_dir.mkdir(parents=True, exist_ok=True)
            pdf_path = letters_dir / filename
            
            # Create PDF
            doc = SimpleDocTemplate(str(pdf_path), pagesize=A4,
                                  rightMargin=2*cm, leftMargin=2*cm,
                                  topMargin=2*cm, bottomMargin=2*cm)
            
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=16,
                spaceAfter=30,
            )
            
            # Build PDF content
            story = []
            story.append(Paragraph(f"Cover Letter - {job_data.get('title', '')}", title_style))
            story.append(Spacer(1, 12))
            
            # Split cover letter into paragraphs
            paragraphs = cover_letter_text.split('\n\n')
            for para in paragraphs:
                if para.strip():
                    story.append(Paragraph(para.strip(), styles['Normal']))
                    story.append(Spacer(1, 12))
            
            doc.build(story)
            print(f"📄 Generated PDF cover letter: {pdf_path}")
            return str(pdf_path)
            
        except ImportError:
            print("⚠️ ReportLab not installed. Install with: pip install reportlab")
            return ""
        except Exception as e:
            print(f"❌ Error generating PDF: {e}")
            return ""

if __name__ == "__main__":
    generator = AICoverLetterGenerator()
    print("✅ AI Cover Letter Generator created")
    
    # Create default prompts for existing users
    for user_dir in Path("~/jobbot/data/users").expanduser().iterdir():
        if user_dir.is_dir():
            username = user_dir.name
            generator.load_user_prompt(username)
            print(f"✅ Created default prompt for {username}")
