"""AI-powered cover letter generation service."""
import json
from datetime import datetime
from typing import Dict, Any, Optional
from openai import AzureOpenAI
from ..config import settings


class CoverLetterGenerator:
    """Service for generating personalized cover letters using AI."""

    def __init__(self):
        """Initialize Azure OpenAI client."""
        self.client = AzureOpenAI(
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_key=settings.AZURE_OPENAI_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION
        )
        self.deployment = settings.AZURE_OPENAI_DEPLOYMENT

    def get_default_prompt(self, language: str = "norwegian") -> str:
        """Get default cover letter generation prompt.

        Args:
            language: Target language for cover letter

        Returns:
            Default prompt template
        """
        if language == "norwegian":
            return """
Ти професійний писарь cover letters. Створи персоналізований cover letter.

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
        else:
            return """
You are a professional cover letter writer. Create a personalized cover letter.

INSTRUCTIONS:
1. Use information from the user's resume
2. Adapt to the specific job and company
3. Write in English
4. Length: 200-400 words
5. Structure: Introduction → Experience → Motivation → Conclusion
6. Tone: Professional yet warm
7. Highlight relevant experience and skills

STYLE FEATURES:
- Specific examples of achievements
- Connection to company goals
- Enthusiasm for the role
- Professional business etiquette
            """

    def _format_experience(self, experiences: list) -> str:
        """Format work experience for prompt.

        Args:
            experiences: List of experience dictionaries

        Returns:
            Formatted experience text
        """
        if not experiences:
            return "No experience provided"

        formatted = []
        for exp in experiences[:3]:  # Top 3 experiences
            period = exp.get('period', exp.get('dates', ''))
            role = exp.get('role', exp.get('title', ''))
            company = exp.get('company', '')
            formatted.append(f"• {period}: {role} at {company}")

        return '\n'.join(formatted)

    def _format_skills(self, skills: Dict[str, Any]) -> str:
        """Format skills for prompt.

        Args:
            skills: Skills dictionary

        Returns:
            Formatted skills text
        """
        if not skills:
            return "No skills provided"

        parts = []

        if 'technical' in skills and skills['technical']:
            technical = skills['technical'][:10]
            parts.append(f"Technical: {', '.join(technical)}")

        if 'soft_skills' in skills and skills['soft_skills']:
            soft = skills['soft_skills'][:5]
            parts.append(f"Soft skills: {', '.join(soft)}")

        if 'languages' in skills and skills['languages']:
            langs = [f"{lang.get('language', '')} ({lang.get('level', '')})"
                    for lang in skills['languages'][:3]]
            parts.append(f"Languages: {', '.join(langs)}")

        return '\n'.join(parts) if parts else "No skills provided"

    async def generate_cover_letter(
        self,
        job_data: Dict[str, Any],
        user_profile: Dict[str, Any],
        custom_prompt: Optional[str] = None,
        language: str = "norwegian"
    ) -> Dict[str, Any]:
        """Generate personalized cover letter for a specific job.

        Args:
            job_data: Job information (title, company, description)
            user_profile: User profile with resume data
            custom_prompt: Optional custom generation prompt
            language: Target language for cover letter

        Returns:
            Dictionary with generation results
        """
        try:
            # Use custom or default prompt
            base_prompt = custom_prompt or self.get_default_prompt(language)

            # Extract job data
            job_title = job_data.get('title', '')
            company = job_data.get('company', '')
            job_description = job_data.get('description', '')[:2000]  # Limit length

            # Extract profile data
            resume_summary = user_profile.get('summary', user_profile.get('comprehensive_summary', ''))
            experience = user_profile.get('experience', user_profile.get('all_work_experience', []))
            skills = user_profile.get('skills', user_profile.get('comprehensive_skills', {}))

            # Build complete prompt
            complete_prompt = f"""
{base_prompt}

ВАКАНСІЯ / JOB:
Назва / Title: {job_title}
Компанія / Company: {company}
Опис / Description: {job_description}

ПРОФІЛЬ КОРИСТУВАЧА / USER PROFILE:
Summary: {resume_summary}

Досвід роботи / Work Experience:
{self._format_experience(experience)}

Навички / Skills:
{self._format_skills(skills)}

ЗАВДАННЯ / TASK:
Створи унікальний cover letter для цієї конкретної вакансії.
Create a unique cover letter for this specific job posting.
Поверни ТІЛЬКИ текст cover letter (без заголовків чи форматування).
Return ONLY the cover letter text (without headers or formatting).
"""

            # Generate with OpenAI
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {
                        "role": "system",
                        "content": f"You are an expert cover letter writer in {language}."
                    },
                    {
                        "role": "user",
                        "content": complete_prompt
                    }
                ],
                temperature=0.7,
                max_tokens=1000
            )

            cover_letter_text = response.choices[0].message.content.strip()

            print(f"✅ Generated cover letter for {job_title} at {company}")

            return {
                "success": True,
                "cover_letter": cover_letter_text,
                "word_count": len(cover_letter_text.split()),
                "language": language,
                "job_title": job_title,
                "company": company,
                "generated_at": datetime.now().isoformat()
            }

        except Exception as e:
            print(f"❌ Cover letter generation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "cover_letter": "",
                "word_count": 0
            }

    async def generate_batch(
        self,
        jobs: list[Dict[str, Any]],
        user_profile: Dict[str, Any],
        custom_prompt: Optional[str] = None,
        language: str = "norwegian"
    ) -> list[Dict[str, Any]]:
        """Generate cover letters for multiple jobs.

        Args:
            jobs: List of job postings
            user_profile: User profile data
            custom_prompt: Optional custom prompt
            language: Target language

        Returns:
            List of generation results
        """
        results = []

        for job in jobs:
            result = await self.generate_cover_letter(
                job_data=job,
                user_profile=user_profile,
                custom_prompt=custom_prompt,
                language=language
            )

            results.append({
                "job": job,
                "letter": result
            })

        return results

    def generate_pdf(
        self,
        cover_letter_text: str,
        job_title: str,
        company: str
    ) -> Optional[bytes]:
        """Generate PDF version of cover letter.

        Args:
            cover_letter_text: Cover letter content
            job_title: Job title
            company: Company name

        Returns:
            PDF bytes or None if generation fails
        """
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            from reportlab.lib.units import cm
            from io import BytesIO

            # Create PDF in memory
            buffer = BytesIO()

            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=2*cm,
                leftMargin=2*cm,
                topMargin=2*cm,
                bottomMargin=2*cm
            )

            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=16,
                spaceAfter=30,
            )

            # Build PDF content
            story = []
            story.append(Paragraph(f"Cover Letter - {job_title}", title_style))
            story.append(Paragraph(f"Company: {company}", styles['Heading2']))
            story.append(Spacer(1, 20))

            # Split cover letter into paragraphs
            paragraphs = cover_letter_text.split('\n\n')
            for para in paragraphs:
                if para.strip():
                    story.append(Paragraph(para.strip(), styles['Normal']))
                    story.append(Spacer(1, 12))

            doc.build(story)

            # Get PDF bytes
            pdf_bytes = buffer.getvalue()
            buffer.close()

            print(f"📄 Generated PDF cover letter ({len(pdf_bytes)} bytes)")
            return pdf_bytes

        except ImportError:
            print("⚠️ ReportLab not installed. Install with: pip install reportlab")
            return None
        except Exception as e:
            print(f"❌ Error generating PDF: {e}")
            return None
