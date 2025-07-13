"""Complete AI-powered application system using real resume data."""
import asyncio
import os
from playwright.async_api import async_playwright
from resume_loader import create_ai_prompt, load_user_resume
from openai import AzureOpenAI


class CompleteApplicationSystem:
    def __init__(self):
        self.client = AzureOpenAI(
            azure_endpoint=os.getenv("OPENAI_ENDPOINT"),
            api_key=os.getenv("OPENAI_KEY"),
            api_version="2024-05-01-preview"
        )
    
    async def create_personalized_application(self, job_title, company, job_description, username):
        """Create personalized application based on real resume."""
        print(f"📋 Створюємо персональну заявку для {username}")
        
        # Завантажуємо реальне резюме
        resume_data = load_user_resume(username)
        ai_prompt = create_ai_prompt(username)
        
        print(f"✅ Резюме завантажено: {resume_data['candidate_name']}")
        print(f"📊 Досвід: {resume_data['experience_years']} років")
        
        # AI промпт для створення заявки
        application_prompt = f"""
На основі РЕАЛЬНОГО резюме створи персональну заявку норвезькою мовою.

ВАКАНСІЯ:
Посада: {job_title}
Компанія: {company}
Опис: {job_description[:800]}

РЕАЛЬНЕ РЕЗЮМЕ КАНДИДАТА:
{ai_prompt}

ЗАВДАННЯ:
Створи професійну заявку норвезькою мовою (150-250 слів) що:
1. Підкреслює РЕАЛЬНИЙ досвід кандидата
2. Показує як досвід підходить до вакансії
3. Згадує конкретні навички з резюме
4. Має професійний норвезький тон
5. Персоналізована для {company}

Поверни JSON:
{{
    "cover_letter": "повна заявка норвезькою мовою",
    "key_skills_match": ["які навички з резюме підходять"],
    "experience_highlight": "головний досвід що треба підкреслити",
    "motivation": "чому цікава ця позиція"
}}
"""
        
        try:
            response = self.client.chat.completions.create(
                model=os.getenv("AZURE_OPENAI_DEPLOYMENT_CHAT", "gpt-4"),
                messages=[{"role": "user", "content": application_prompt}],
                max_tokens=1500,
                temperature=0.7
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            
            # Додаємо персональні дані з резюме
            result['personal_data'] = {
                'first_name': 'Vitalii',
                'last_name': 'Berbeha',
                'full_name': resume_data['candidate_name'],
                'email': 'stuardbmw@gmail.com',  # З config.json
                'phone': '+47 925 64 334',  # З config.json
                'city': 'Lena, Norway'
            }
            
            return result
            
        except Exception as e:
            print(f"❌ Помилка створення заявки: {e}")
            return self._get_fallback_application(resume_data, job_title, company)
    
    def _get_fallback_application(self, resume_data, job_title, company):
        """Fallback заявка якщо AI не працює."""
        return {
            "cover_letter": f"""Kjære {company} team,

Jeg skriver for å uttrykke min interesse for stillingen som {job_title}. Med mine {resume_data['experience_years']} års erfaring innen prosjektledelse og teknologiutvikling, tror jeg at jeg kan bidra positivt til teamet deres.

Min bakgrunn inkluderer:
- Omfattende erfaring med AI-verktøy og automatisering
- Prosjektledelse og SaaS-applikasjonsutvikling
- Entreprenøriell erfaring og forretningsutvikling
- Flerspråklig kompetanse (ukrainsk, russisk, norsk, engelsk)

Jeg ser frem til muligheten til å diskutere hvordan mine ferdigheter kan støtte {company} sine mål.

Med vennlig hilsen,
{resume_data['candidate_name']}""",
            "key_skills_match": resume_data['skills_list'][:3],
            "experience_highlight": f"{resume_data['experience_years']} års erfaring i prosjektledelse",
            "motivation": f"Interessert i å bidra til {company} med teknologiske løsninger",
            "personal_data": {
                'first_name': 'Vitalii',
                'last_name': 'Berbeha',
                'full_name': resume_data['candidate_name'],
                'email': 'stuardbmw@gmail.com',
                'phone': '+47 925 64 334',
                'city': 'Lena, Norway'
            }
        }
    
    async def smart_fill_iframe_form(self, frame, application_data):
        """Smart form filling using real application data."""
        print(f"\n📝 ЗАПОВНЕННЯ ФОРМИ РЕАЛЬНИМИ ДАНИМИ")
        print("-" * 40)
        
        # Знаходимо всі поля
        inputs = await frame.query_selector_all('input')
        textareas = await frame.query_selector_all('textarea')
        
        filled_count = 0
        personal_data = application_data['personal_data']
        cover_letter = application_data['cover_letter']
        
        # Заповнюємо input поля
        for input_el in inputs:
            try:
                input_type = await input_el.get_attribute('type') or 'text'
                name = (await input_el.get_attribute('name') or '').lower()
                id_attr = (await input_el.get_attribute('id') or '').lower()
                placeholder = (await input_el.get_attribute('placeholder') or '').lower()
                
                field_text = f"{name} {id_attr} {placeholder}"
                
                # Визначаємо що заповняти
                if input_type == 'hidden':
                    continue
                elif any(word in field_text for word in ['fornavn', 'first', 'fname']):
                    await input_el.fill(personal_data['first_name'])
                    print(f"✅ First name: {personal_data['first_name']}")
                    filled_count += 1
                elif any(word in field_text for word in ['etternavn', 'last', 'lname', 'surname']):
                    await input_el.fill(personal_data['last_name'])
                    print(f"✅ Last name: {personal_data['last_name']}")
                    filled_count += 1
                elif any(word in field_text for word in ['email', 'e-post', 'mail']):
                    await input_el.fill(personal_data['email'])
                    print(f"✅ Email: {personal_data['email']}")
                    filled_count += 1
                elif any(word in field_text for word in ['phone', 'telefon', 'mobil', 'tlf']):
                    await input_el.fill(personal_data['phone'])
                    print(f"✅ Phone: {personal_data['phone']}")
                    filled_count += 1
                elif any(word in field_text for word in ['by', 'city', 'sted', 'location']):
                    await input_el.fill(personal_data['city'])
                    print(f"✅ City: {personal_data['city']}")
                    filled_count += 1
                elif input_type == 'checkbox' and any(word in field_text for word in ['godtar', 'agree', 'vilkår']):
                    await input_el.click()
                    print(f"✅ Checkbox agreement")
                    filled_count += 1
                    
            except Exception as e:
                print(f"❌ Помилка з input: {e}")
        
        # Заповнюємо textarea cover letter
        for textarea in textareas:
            try:
                await textarea.fill(cover_letter)
                print(f"✅ Cover letter заповнено ({len(cover_letter)} символів)")
                filled_count += 1
            except Exception as e:
                print(f"❌ Помилка з textarea: {e}")
        
        return filled_count
    
    async def test_complete_system(self):
        """Test complete system with real resume data."""
        print("🚀 ТЕСТУВАННЯ ПОВНОЇ СИСТЕМИ З РЕАЛЬНИМ РЕЗЮМЕ")
        print("=" * 60)
        
        # Тестові дані вакансії
        job_data = {
            'title': 'Project Manager - AI/Tech',
            'company': 'KillNoise',
            'description': 'We are looking for an experienced project manager with AI and technology background to lead our innovation projects.'
        }
        
        # Створюємо персональну заявку
        application = await self.create_personalized_application(
            job_data['title'],
            job_data['company'],
            job_data['description'],
            'vitalii'
        )
        
        print(f"\n📋 СТВОРЕНА ЗАЯВКА:")
        print("-" * 25)
        print(f"🎯 Підходящі навички: {application['key_skills_match']}")
        print(f"⭐ Ключовий досвід: {application['experience_highlight']}")
        print(f"\n📝 Заявка норвезькою:")
        print(application['cover_letter'])
        
        # Тестуємо заповнення форми
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=['--no-sandbox'])
            page = await browser.new_page()
            
            try:
                print(f"\n🌐 Завантажуємо форму KillNoise...")
                await page.goto('https://killnoi.se/?dest=application&country=no', timeout=30000)
                await page.wait_for_timeout(8000)
                
                # Знаходимо iframe з формою
                form_frame = None
                for frame in page.frames:
                    try:
                        inputs = await frame.query_selector_all('input')
                        if len(inputs) > 10:
                            form_frame = frame
                            break
                    except:
                        continue
                
                if form_frame:
                    filled_count = await self.smart_fill_iframe_form(form_frame, application)
                    
                    # Результат
                    await page.screenshot(path='/app/data/screenshots/complete_system_result.png', full_page=True)
                    
                    print(f"\n📊 ФІНАЛЬНИЙ РЕЗУЛЬТАТ:")
                    print("-" * 25)
                    print(f"✅ Заповнено полів: {filled_count}")
                    print(f"📸 Скріншот: complete_system_result.png")
                    print(f"📧 Використано email: {application['personal_data']['email']}")
                    print(f"📱 Використано телефон: {application['personal_data']['phone']}")
                    
                else:
                    print("❌ Форма не знайдена")
                    
            except Exception as e:
                print(f"❌ Помилка: {e}")
            finally:
                await browser.close()


async def main():
    system = CompleteApplicationSystem()
    await system.test_complete_system()


if __name__ == "__main__":
    asyncio.run(main())
