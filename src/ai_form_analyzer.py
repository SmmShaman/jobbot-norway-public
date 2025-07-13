"""AI-powered form analyzer for job application forms."""
import os
import json
import base64
from typing import Dict, List, Any
from openai import AzureOpenAI

class AIFormAnalyzer:
    def __init__(self):
        self.client = AzureOpenAI(
            azure_endpoint=os.getenv("OPENAI_ENDPOINT"),
            api_key=os.getenv("OPENAI_KEY"),
            api_version="2024-05-01-preview"
        )
    
    async def analyze_application_form(self, screenshot_path: str, html_content: str, 
                                     job_title: str, company: str) -> Dict[str, Any]:
        """Analyze job application form and return filling instructions."""
        
        # Encode screenshot
        with open(screenshot_path, "rb") as image_file:
            screenshot_b64 = base64.b64encode(image_file.read()).decode()
        
        prompt = f"""
        Проаналізуй форму заявки на роботу і визнач як її заповнити.
        
        Вакансія: {job_title}
        Компанія: {company}
        
        HTML код форми:
        {html_content[:3000]}...
        
        ЗАВДАННЯ:
        1. Знайди всі поля для заповнення (input, textarea, select)
        2. Визнач селектори для кожного поля
        3. Знайди поля для завантаження файлів (CV, Cover Letter)
        4. Знайди чекбокси та радіо-кнопки
        5. Знайди кнопку відправки
        6. Визнач які поля обов'язкові
        
        Поверни ТІЛЬКИ валідний JSON:
        {{
            "form_fields": [
                {{
                    "field_type": "text|email|phone|textarea|select|file|checkbox|radio",
                    "selector": "CSS selector",
                    "label": "Field label",
                    "required": true/false,
                    "placeholder": "placeholder text",
                    "suggested_value": "what to fill based on field type"
                }}
            ],
            "submit_button": {{
                "selector": "CSS selector for submit button",
                "text": "button text"
            }},
            "cookies_accept": {{
                "found": true/false,
                "selector": "CSS selector if found"
            }},
            "special_instructions": [
                "Any special steps needed"
            ]
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model=os.getenv("AZURE_OPENAI_DEPLOYMENT_CHAT", "gpt-4"),
                messages=[
                    {
                        "role": "user", 
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/png;base64,{screenshot_b64}"}
                            }
                        ]
                    }
                ],
                temperature=0.1,
                max_tokens=2000
            )
            
            raw_response = response.choices[0].message.content
            
            # Clean and parse JSON
            clean_response = self._clean_json_response(raw_response)
            result = json.loads(clean_response)
            
            print(f"✅ AI analyzed form for {job_title} at {company}")
            return result
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing error: {e}")
            print(f"Raw response: {raw_response[:200]}...")
            return self._get_fallback_analysis()
            
        except Exception as e:
            print(f"❌ AI form analysis error: {e}")
            return self._get_fallback_analysis()
    
    def _clean_json_response(self, response: str) -> str:
        """Clean markdown formatting from JSON response."""
        response = response.strip()
        if response.startswith('```json'):
            response = response[7:]
        if response.endswith('```'):
            response = response[:-3]
        return response.strip()
    
    def _get_fallback_analysis(self) -> Dict[str, Any]:
        """Return fallback analysis if AI fails."""
        return {
            "form_fields": [
                {
                    "field_type": "text",
                    "selector": "input[name*='name'], input[id*='name']",
                    "label": "Name",
                    "required": True,
                    "suggested_value": "full_name"
                },
                {
                    "field_type": "email",
                    "selector": "input[type='email'], input[name*='email']",
                    "label": "Email",
                    "required": True,
                    "suggested_value": "email"
                },
                {
                    "field_type": "phone",
                    "selector": "input[type='tel'], input[name*='phone']",
                    "label": "Phone",
                    "required": False,
                    "suggested_value": "phone"
                },
                {
                    "field_type": "file",
                    "selector": "input[type='file']",
                    "label": "CV/Resume",
                    "required": True,
                    "suggested_value": "cv_file"
                }
            ],
            "submit_button": {
                "selector": "button[type='submit'], input[type='submit']",
                "text": "Submit"
            },
            "cookies_accept": {
                "found": True,
                "selector": "button:contains('Accept'), button:contains('OK')"
            },
            "special_instructions": [
                "Accept cookies first",
                "Fill required fields",
                "Upload CV file",
                "Submit application"
            ]
        }

if __name__ == "__main__":
    analyzer = AIFormAnalyzer()
    print("✅ AI Form Analyzer initialized")
