"""Complete test of improved workflow with real job application."""
import asyncio
import os
from playwright.async_api import async_playwright
from improved_ai_form_analyzer import ImprovedAIFormAnalyzer
from improved_smart_filler import ImprovedSmartFiller


class ImprovedWorkflowTest:
    def __init__(self):
        self.analyzer = ImprovedAIFormAnalyzer()
        self.filler = ImprovedSmartFiller()
        
    async def test_real_job_application(self):
        """Test complete workflow with real job application."""
        print("🚀 ТЕСТУВАННЯ ПОКРАЩЕНОГО WORKFLOW")
        print("=" * 50)
        
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
            # Запускаємо браузер
            browser = await p.chromium.launch(headless=False)  # Показуємо браузер для демо
            page = await browser.new_page()
            
            try:
                print(f"🔍 Переходимо на: {job_data['url']}")
                await page.goto(job_data['url'])
                await page.wait_for_timeout(3000)
                
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
                
                # Обробляємо cookies якщо потрібно
                if analysis.get('cookies_button', {}).get('found'):
                    print("\n🍪 ОБРОБКА COOKIES")
                    print("-" * 20)
                    success = await self.filler.handle_cookies(page, analysis['cookies_button'])
                    if success:
                        await page.wait_for_timeout(2000)
                        # Новий скріншот після cookies
                        await page.screenshot(path="/app/data/screenshots/improved_after_cookies.png")
                
                # Шукаємо форму заявки
                print("\n🔍 ПОШУК ФОРМИ ЗАЯВКИ")
                print("-" * 25)
                
                # Шукаємо кнопки для переходу до заявки
                application_selectors = [
                    "text=Apply",
                    "text=Søk stilling", 
                    "text=Send søknad",
                    "text=Apply now",
                    "a[href*='application']",
                    "a[href*='apply']"
                ]
                
                application_found = False
                for selector in application_selectors:
                    try:
                        await page.wait_for_selector(selector, timeout=2000)
                        print(f"✅ Знайдено кнопку заявки: {selector}")
                        await page.click(selector)
                        await page.wait_for_timeout(3000)
                        application_found = True
                        break
                    except:
                        print(f"❌ Не знайдено: {selector}")
                        continue
                
                if application_found:
                    # Аналізуємо форму заявки
                    await page.screenshot(path="/app/data/screenshots/improved_application_form.png")
                    
                    form_html = await page.content()
                    form_analysis = await self.analyzer.analyze_application_form(
                        screenshot_path="/app/data/screenshots/improved_application_form.png",
                        html_content=form_html,
                        job_title=job_data['title'],
                        company=job_data['company']
                    )
                    
                    print(f"\n📋 АНАЛІЗ ФОРМИ ЗАЯВКИ")
                    print("-" * 25)
                    print(f"📝 Полів для заповнення: {len(form_analysis['form_fields'])}")
                    
                    # Заповнюємо форму
                    filled_count = 0
                    for field in form_analysis['form_fields']:
                        success = await self.filler.smart_fill_field(page, field, user_data)
                        if success:
                            filled_count += 1
                        await page.wait_for_timeout(1000)
                    
                    print(f"\n📊 РЕЗУЛЬТАТ ЗАПОВНЕННЯ")
                    print("-" * 25)
                    print(f"✅ Заповнено полів: {filled_count}/{len(form_analysis['form_fields'])}")
                    
                    # Фінальний скріншот
                    await page.screenshot(path="/app/data/screenshots/improved_final_result.png")
                    
                    # НЕ відправляємо форму (тільки тест)
                    print("⚠️ Форма НЕ відправлена (тільки тестування)")
                    
                else:
                    print("❌ Форма заявки не знайдена")
                
                await page.wait_for_timeout(5000)  # Пауза для огляду
                
            except Exception as e:
                print(f"❌ Помилка workflow: {e}")
                await page.screenshot(path="/app/data/screenshots/improved_error.png")
            
            finally:
                await browser.close()
        
        print("\n🎯 ТЕСТ ЗАВЕРШЕНО!")
        print("📁 Перевірте скріншоти в /app/data/screenshots/")


async def main():
    """Run the complete test."""
    tester = ImprovedWorkflowTest()
    await tester.test_real_job_application()


if __name__ == "__main__":
    asyncio.run(main())
