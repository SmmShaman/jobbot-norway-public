"""Form analysis and automation service for job applications."""
import json
import httpx
from typing import Dict, List, Any, Optional
from openai import AzureOpenAI
from ..config import settings


class FormAnalyzer:
    """Service for analyzing and automating job application forms."""

    def __init__(self):
        """Initialize form analyzer with Azure OpenAI."""
        self.client = AzureOpenAI(
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_key=settings.AZURE_OPENAI_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION
        )
        self.deployment = settings.AZURE_OPENAI_DEPLOYMENT
        self.skyvern_url = settings.SKYVERN_API_URL

    async def analyze_application_form(
        self,
        html_content: str,
        job_title: str,
        company: str,
        screenshot_base64: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze job application form and return filling instructions.

        Args:
            html_content: HTML content of the form
            job_title: Job title
            company: Company name
            screenshot_base64: Optional base64 encoded screenshot

        Returns:
            Dictionary with form analysis and filling instructions
        """
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
            "fill_value": "{{{{email}}}}",
            "required": true
        }}
    ],
    "submit_button": {{
        "playwright_selectors": ["text=Submit", "button[type='submit']"]
    }}
}}
"""

        try:
            print(f"🔍 Analyzing form for: {job_title} at {company}")

            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at analyzing web forms and creating automation scripts."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,
                max_tokens=1500
            )

            result_text = response.choices[0].message.content.strip()

            # Clean and parse JSON
            result_text = result_text.replace('```json', '').replace('```', '').strip()
            analysis = json.loads(result_text)

            print(f"✅ Form analysis complete: {len(analysis.get('form_fields', []))} fields found")
            return analysis

        except Exception as e:
            print(f"❌ Form analysis error: {e}")
            return self._get_fallback_analysis()

    def _get_fallback_analysis(self) -> Dict[str, Any]:
        """Return fallback analysis when AI fails.

        Returns:
            Default form structure
        """
        return {
            "page_type": "application_form",
            "form_fields": [
                {
                    "field_type": "text",
                    "label": "Name",
                    "playwright_selectors": [
                        "input[placeholder*='name']",
                        "input[placeholder*='navn']",
                        "label:has-text('Name') >> input",
                        "label:has-text('Navn') >> input"
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
                        "input[placeholder*='e-post']",
                        "label:has-text('Email') >> input"
                    ],
                    "fill_value": "{email}",
                    "required": True
                },
                {
                    "field_type": "tel",
                    "label": "Phone",
                    "playwright_selectors": [
                        "input[type='tel']",
                        "input[placeholder*='phone']",
                        "input[placeholder*='telefon']",
                        "label:has-text('Phone') >> input"
                    ],
                    "fill_value": "{phone}",
                    "required": False
                },
                {
                    "field_type": "textarea",
                    "label": "Cover Letter",
                    "playwright_selectors": [
                        "textarea[placeholder*='cover']",
                        "textarea[placeholder*='motivasjon']",
                        "label:has-text('Cover Letter') >> textarea"
                    ],
                    "fill_value": "{cover_letter}",
                    "required": False
                }
            ],
            "submit_button": {
                "playwright_selectors": [
                    "text=Submit",
                    "text=Send",
                    "text=Søk",
                    "button[type='submit']"
                ]
            },
            "cookies_button": {
                "found": True,
                "playwright_selectors": [
                    "text=Accept",
                    "text=Agree",
                    "text=Godta",
                    "button:has-text('Accept')"
                ]
            }
        }

    async def submit_via_skyvern(
        self,
        url: str,
        form_data: Dict[str, Any],
        form_analysis: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Submit application using Skyvern automation.

        Args:
            url: Application form URL
            form_data: Data to fill in the form
            form_analysis: Optional pre-analyzed form structure

        Returns:
            Submission result
        """
        try:
            print(f"🚀 Submitting application via Skyvern: {url}")

            async with httpx.AsyncClient(timeout=120) as client:
                response = await client.post(
                    f"{self.skyvern_url}/api/v1/tasks",
                    json={
                        "url": url,
                        "navigation_goal": "Fill and submit job application form",
                        "data_extraction_goal": "Confirm submission success",
                        "form_data": form_data,
                        "form_analysis": form_analysis
                    }
                )
                response.raise_for_status()

            result = response.json()
            print(f"✅ Skyvern submission initiated: {result.get('task_id')}")

            return {
                "success": True,
                "task_id": result.get("task_id"),
                "status": result.get("status"),
                "message": "Application submission started"
            }

        except httpx.ConnectError:
            print("❌ Skyvern not available. Is it running on port 8000?")
            return {
                "success": False,
                "error": "Skyvern service not available",
                "message": "Please start Skyvern: docker run -p 8000:8000 skyvern/skyvern"
            }
        except Exception as e:
            print(f"❌ Skyvern submission error: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Application submission failed"
            }

    async def check_skyvern_status(self, task_id: str) -> Dict[str, Any]:
        """Check status of Skyvern automation task.

        Args:
            task_id: Skyvern task ID

        Returns:
            Task status
        """
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(
                    f"{self.skyvern_url}/api/v1/tasks/{task_id}"
                )
                response.raise_for_status()

            result = response.json()
            return {
                "success": True,
                "status": result.get("status"),
                "progress": result.get("progress"),
                "result": result.get("result")
            }

        except Exception as e:
            print(f"❌ Status check error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def generate_playwright_script(
        self,
        form_analysis: Dict[str, Any],
        form_data: Dict[str, str]
    ) -> str:
        """Generate Playwright automation script from form analysis.

        Args:
            form_analysis: Form structure from analyze_application_form
            form_data: Data to fill in the form

        Returns:
            Python Playwright script
        """
        script_lines = [
            "from playwright.async_api import async_playwright",
            "",
            "async def fill_application_form():",
            "    async with async_playwright() as p:",
            "        browser = await p.chromium.launch(headless=False)",
            "        page = await browser.new_page()",
            "        ",
            "        # Navigate to form",
            "        await page.goto(form_data['url'])",
            "        await page.wait_for_load_state('networkidle')",
            "        ",
            "        # Handle cookies if present",
        ]

        cookies = form_analysis.get("cookies_button", {})
        if cookies.get("found"):
            selectors = cookies.get("playwright_selectors", [])
            if selectors:
                script_lines.append(f"        try:")
                script_lines.append(f"            await page.click('{selectors[0]}', timeout=3000)")
                script_lines.append(f"        except:")
                script_lines.append(f"            pass  # No cookies popup")
                script_lines.append("        ")

        # Fill form fields
        script_lines.append("        # Fill form fields")
        for field in form_analysis.get("form_fields", []):
            field_type = field.get("field_type")
            selectors = field.get("playwright_selectors", [])
            fill_value = field.get("fill_value", "")

            if selectors:
                value_key = fill_value.strip("{}").strip()
                script_lines.append(f"        # Fill {field.get('label')}")
                script_lines.append(f"        try:")
                script_lines.append(f"            await page.fill('{selectors[0]}', form_data['{value_key}'])")
                script_lines.append(f"        except:")
                script_lines.append(f"            print('Could not fill {field.get('label')}')")
                script_lines.append("        ")

        # Submit button
        submit = form_analysis.get("submit_button", {})
        submit_selectors = submit.get("playwright_selectors", [])
        if submit_selectors:
            script_lines.append("        # Submit form")
            script_lines.append(f"        await page.click('{submit_selectors[0]}')")
            script_lines.append("        await page.wait_for_timeout(5000)")

        script_lines.extend([
            "        ",
            "        await browser.close()",
            "",
            "if __name__ == '__main__':",
            "    import asyncio",
            "    asyncio.run(fill_application_form())"
        ])

        return "\n".join(script_lines)
