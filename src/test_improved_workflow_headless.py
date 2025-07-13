"""Complete test of improved workflow with real job application (headless)."""
import asyncio
import os
from playwright.async_api import async_playwright
from improved_ai_form_analyzer import ImprovedAIFormAnalyzer
from improved_smart_filler import ImprovedSmartFiller


class ImprovedWorkflowTest:
    def __init__(self):
        self.analyzer = ImprovedAIFormAnalyzer()
        self.filler = ImprovedSmartFiller()
        
    async def ensure_screenshots_dir(self):
        """Ensure screenshots directory exists."""
        screenshots_dir = "/app/data/screenshots"
        os.makedirs(screenshots_dir, exist_ok=True)
        return screenshots_dir
        
    async def test_real_job_application(self):
        """Test complete workflow with real job application."""
        print("🚀 ТЕСТУВАННЯ ПОКРАЩЕНОГО WORKFLOW")
        print("=" * 50)
        
        await self.ensure_screenshots_dir()
        
        # Реальна вакансія для тестування
        job_data = {
            "title": "Python Developer",
            "company": "KillNoise",
            "url": "https://killnoise.com/nb/pages/jobs-at-killnoise"
        }
        
        user_data = {
            "name": "Vitalii Berbeha",
            "email": "vitalii.berbeha@example.com",
            "phone": "+47 123 45 678"
        }
        
        async with async_playwright() as p:
            # Запускаємо браузер в headless режимі
            browser = await p.chromium.launch(
                headless=True,  # Обов'язково для Docker
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            page = await browser.new_page()
            
            try:
                print(f"🔍 Переходимо на: {job_data['url']}")
                await page.goto(job_data['url'], timeout=30000)
                await page.wait_for_timeout(5000)
                
                # Робимо скріншот початкової сторінки
                screenshot_path = "/app/data/screenshots/improved_workflow_start.png"
                await page.screenshot(path=screenshot_path, full_page=True)
                print(f"📸 Скріншот збережено: {screenshot_path}")
                
                # Отримуємо HTML
                html_content = await page.content()
                print(f"📄 HTML отримано: {len(html_content)} символів")
                
                # Аналізуємо сторінку
                print("\n🤖 АНАЛІЗ СТОРІНКИ")
                print("-" * 30)
                analysis = await self.analyzer.analyze_application_form(
                    screenshot_path=screenshot_path,
                    html_content=html_content,
                    job_title=job_data['title'],
                    company=job_data['company']
                )
                
                print(f"📊 Тип сторінки: {analysis['page_type']}")
                print(f"📝 Знайдено полів: {len(analysis['form_fields'])}")
                
                # Обробляємо cookies
                print("\n🍪 СПРОБА ОБРОБКИ COOKIES")
                print("-" * 30)
                cookies_success = await self.filler.handle_cookies(page, analysis['cookies_button'])
                if cookies_success:
                    await page.wait_for_timeout(2000)
                    print("✅ Cookies оброблені")
                else:
                    print("ℹ️ Cookies не знайдені")
                
                # Шукаємо форму заявки
                print("\n🔍 ПОШУК ФОРМИ ЗАЯВКИ")
                print("-" * 25)
                
                application_selectors = [
                    "text=Apply",
                    "text=Søk stilling", 
                    "a:has-text('Apply')",
                    "button:has-text('Apply')",
                    "[href*='application']",
                    "[href*='apply']"
                ]
                
                application_found = False
                for selector in application_selectors:
                    try:
                        elements = await page.query_selector_all(selector)
                        if elements:
                            print(f"✅ Знайдено: {selector}")
                            await elements[0].click()
                            await page.wait_for_timeout(3000)
                            application_found = True
                            break
                        else:
                            print(f"❌ Не знайдено: {selector}")
                    except Exception as e:
                        print(f"❌ Помилка з {selector}: {str(e)[:50]}...")
                        continue
                
                # Пробуємо заповнити поля
                print(f"\n📝 ЗАПОВНЕННЯ ПОЛІВ")
                print("-" * 20)
                filled_count = 0
                for field in analysis['form_fields']:
                    success = await self.filler.smart_fill_field(page, field, user_data)
                    if success:
                        filled_count += 1
                    await page.wait_for_timeout(1000)
                
                print(f"✅ Заповнено полів: {filled_count}/{len(analysis['form_fields'])}")
                
                # Фінальний скріншот
                await page.screenshot(path="/app/data/screenshots/improved_final_result.png")
                print("📸 Фінальний скріншот збережено")
                
                print("\n⚠️ Форма НЕ відправлена (тільки тестування)")
                
            except Exception as e:
                print(f"❌ Помилка workflow: {e}")
                await page.screenshot(path="/app/data/screenshots/improved_error.png")
            
            finally:
                await browser.close()
        
        print("\n🎯 ТЕСТ ЗАВЕРШЕНО!")


async def main():
    tester = ImprovedWorkflowTest()
    await tester.test_real_job_application()


if __name__ == "__main__":
    asyncio.run(main())
