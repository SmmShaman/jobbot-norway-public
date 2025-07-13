"""AI-powered form analyzer with text-based selectors for job application forms."""
import os
import json
import base64
from typing import Dict, List, Any
from openai import AzureOpenAI


class ImprovedAIFormAnalyzer:
    def __init__(self):
        self.client = AzureOpenAI(
            azure_endpoint=os.getenv("OPENAI_ENDPOINT"),
            api_key=os.getenv("OPENAI_KEY"),
            api_version="2024-05-01-preview"
        )

    async def analyze_application_form(self, screenshot_path: str, html_content: str,
                                     job_title: str, company: str) -> Dict[str, Any]:
        """Analyze job application form and return text-based filling instructions."""
        
        # Для тестування без реального скріншоту
        if not os.path.exists(screenshot_path):
            return self._get_fallback_analysis()
        
        # НОВИЙ ПРОМПТ з текстовими інструкціями
        prompt = f"""
Проаналізуй форму заявки на роботу.

Вакансія: {job_title}
Компанія: {company}

HTML код форми:
{html_content[:2000]}...

ЗАВДАННЯ: Створи інструкції для автоматичного заповнення форми.
ВАЖЛИВО: Використовуй ТЕКСТОВІ селектори Playwright, НЕ CSS!

Playwright селектори:
- page.fill('input[placeholder*="email"]', value)
- page.click('text=Submit Application')
- page.fill('label:has-text("Name") >> input', value)

ПОВЕРНИ JSON:
{{
    "page_type": "application_form",
    "form_fields": [
        {{
            "field_type": "email",
            "label": "Email",
            "playwright_selectors": [
                "input[type='email']",
                "input[placeholder*='email']"
            ],
            "fill_value": "{{email}}",
            "required": true
        }}
    ],
    "submit_button": {{
        "playwright_selectors": ["text=Submit", "button[type='submit']"]
    }}
}}
"""

        try:
            # Простий тест без AI поки що
            print(f"🔍 Аналізуємо форму для: {job_title}")
            print(f"📝 HTML довжина: {len(html_content)} символів")
            
            # Повертаємо тестовий результат
            return self._get_fallback_analysis()
                
        except Exception as e:
            print(f"❌ Помилка аналізу: {e}")
            return self._get_fallback_analysis()

    def _get_fallback_analysis(self) -> Dict[str, Any]:
        """Return fallback analysis when AI fails."""
        return {
            "page_type": "application_form",
            "form_fields": [
                {
                    "field_type": "text",
                    "label": "Name",
                    "playwright_selectors": [
                        "input[placeholder*='name']",
                        "input[placeholder*='navn']",
                        "label:has-text('Name') >> input"
                    ],
                    "fill_value": "{name}",
                    "required": True
                },
                {
                    "field_type": "email",
                    "label": "Email",
                    "playwright_selectors": [
                        "input[type='email']",
                        "input[placeholder*='email']",
                        "label:has-text('Email') >> input"
                    ],
                    "fill_value": "{email}",
                    "required": True
                }
            ],
            "submit_button": {
                "playwright_selectors": [
                    "text=Submit",
                    "text=Send",
                    "button[type='submit']"
                ]
            },
            "cookies_button": {
                "found": True,
                "playwright_selectors": [
                    "text=Accept",
                    "text=Agree"
                ]
            }
        }


# Test function
async def test_improved_analyzer():
    """Test the improved form analyzer."""
    analyzer = ImprovedAIFormAnalyzer()
    
    result = await analyzer.analyze_application_form(
        screenshot_path="/app/data/screenshots/test_form.png",
        html_content="<form><input placeholder='Your email' type='email'><button>Submit</button></form>",
        job_title="Python Developer",
        company="Test Company"
    )
    
    print("🔍 Analysis Result:")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_improved_analyzer())
