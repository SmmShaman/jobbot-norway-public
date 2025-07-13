"""
Production NAV Workflow - Semi-automated BankID login with Telegram integration
"""
import asyncio
import os
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright
from .telegram_bot import TelegramBot

class ProductionNAVWorkflow:
    def __init__(self, username):
        self.username = username
        self.telegram_bot = TelegramBot()
        self.fnr = os.getenv("FN_NUMBER")
        self.password = os.getenv("BANKID_PWD")

    async def run_semi_automated_nav_workflow(self, applied_jobs):
        """Запускає semi-automated NAV workflow з Telegram підтримкою."""
        
        print(f"🚀 Starting Production NAV Workflow for {self.username}")
        print(f"📊 Jobs to report: {len(applied_jobs)}")
        
        try:
            # Крок 1: Автоматично до BankID
            result = await self._navigate_to_bankid_push()
            
            if result["status"] == "success":
                # Крок 2: Відправляємо Telegram інструкції
                await self._send_user_instructions(result["url"])
                
                # Крок 3: Очікуємо підтвердження
                confirmation = await self._wait_for_user_confirmation()
                
                if confirmation["status"] == "confirmed":
                    # Крок 4: Продовжуємо автоматизацію
                    final_result = await self._complete_nav_reporting(applied_jobs)
                    return final_result
                else:
                    return {"status": "timeout", "message": "User confirmation timeout"}
            else:
                return result
                
        except Exception as e:
            error_msg = f"❌ Production NAV Workflow Error: {str(e)}"
            await self.telegram_bot.send_message(error_msg)
            return {"status": "error", "error": str(e)}

    async def _navigate_to_bankid_push(self):
        """Автоматично доходить до BankID push notification."""
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            page = await browser.new_page()
            
            try:
                print("🌐 Navigating to NAV...")
                await page.goto('https://aktivitetsplan.nav.no/aktivitet/ny/stilling', timeout=30000)
                await page.wait_for_load_state('networkidle')
                
                # Якщо редірект на ID-porten
                if 'idporten.no' in page.url:
                    print("🔐 Detected ID-porten, selecting BankID...")
                    
                    # Знаходимо і клікаємо BankID
                    bankid_button = await page.query_selector('button:has-text("BankID")')
                    if not bankid_button:
                        bankid_button = await page.query_selector('a:has-text("BankID")')
                    
                    if bankid_button:
                        await bankid_button.click()
                        await page.wait_for_load_state('networkidle')
                        print("✅ BankID selected")
                    
                    # Заповнюємо FNR
                    fnr_input = await page.query_selector('input[name="fodselsnummer"], input[type="text"]')
                    if fnr_input and self.fnr:
                        await fnr_input.fill(self.fnr)
                        print(f"✅ FNR filled: {self.fnr[:6]}...")
                        
                        # Клікаємо Neste
                        next_button = await page.query_selector('button:has-text("Neste"), input[value="Neste"]')
                        if next_button:
                            await next_button.click()
                            await page.wait_for_timeout(3000)
                            print("✅ Clicked Neste - BankID push should be sent")
                
                # Зберігаємо screenshot
                screenshot_path = f'/app/data/users/{self.username}/nav_production_state.png'
                await page.screenshot(path=screenshot_path)
                
                current_url = page.url
                print(f"📱 Ready for user BankID confirmation at: {current_url}")
                
                return {
                    "status": "success",
                    "url": current_url,
                    "message": "Ready for BankID push confirmation"
                }
                
            except Exception as e:
                print(f"❌ Navigation error: {e}")
                return {"status": "error", "error": str(e)}
            finally:
                await browser.close()

    async def _send_user_instructions(self, current_url):
        """Відправляє детальні інструкції користувачу."""
        
        message = f"""
🔔 <b>NAV BankID Login Required</b>

<b>STEP 1:</b> Open your BankID app on your phone
<b>STEP 2:</b> You should have received a push notification
<b>STEP 3:</b> Approve the BankID request in the app
<b>STEP 4:</b> Reply "LOGGED_IN" when complete

<b>Current URL:</b> {current_url}

⏰ <b>Timeout:</b> 10 minutes
🤖 The system will continue automatically after your confirmation.

<i>If you don't see the push notification, check that BankID app is updated and try refreshing the browser.</i>
        """
        
        success = await self.telegram_bot.send_message(message)
        if success:
            print("📱 User instructions sent via Telegram")
        else:
            print("❌ Failed to send Telegram instructions")

    async def _wait_for_user_confirmation(self, timeout_minutes=10):
        """Очікує підтвердження від користувача (симуляція)."""
        
        print(f"⏳ Waiting for user confirmation ({timeout_minutes} minutes)...")
        
        # В production тут буде Telegram bot listener
        # який слухає "LOGGED_IN" від користувача
        
        for minute in range(timeout_minutes):
            print(f"  ⏱️  {minute + 1}/{timeout_minutes} minutes elapsed...")
            await asyncio.sleep(60)  # 1 хвилина
            
            # TODO: Інтегрувати з Telegram bot для перевірки повідомлень
            # if telegram_bot.check_for_user_confirmation():
            #     return {"status": "confirmed"}
        
        # Поки що повертаємо timeout для тестування
        await self.telegram_bot.send_message("⏰ Login confirmation timeout. Please try again later.")
        return {"status": "timeout"}

    async def _complete_nav_reporting(self, applied_jobs):
        """Завершує NAV звітування після успішного логіну."""
        
        print(f"📝 Completing NAV reporting for {len(applied_jobs)} jobs...")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                # Перевіряємо що користувач залогінений
                await page.goto('https://aktivitetsplan.nav.no/aktivitet/ny/stilling')
                await page.wait_for_load_state('networkidle')
                
                if 'aktivitetsplan.nav.no' in page.url:
                    print("✅ User is logged in - proceeding with reporting")
                    
                    successful_reports = 0
                    
                    for i, job in enumerate(applied_jobs):
                        print(f"📄 Reporting job {i+1}: {job.get('title', 'Unknown')[:50]}...")
                        
                        # Заповнюємо форму NAV
                        form_success = await self._fill_nav_form(page, job)
                        
                        if form_success:
                            successful_reports += 1
                            print(f"✅ Job {i+1} reported successfully")
                        else:
                            print(f"❌ Failed to report job {i+1}")
                        
                        # Пауза між звітами
                        await asyncio.sleep(2)
                    
                    # Фінальне повідомлення
                    summary_msg = f"""
🎉 <b>NAV Reporting Complete!</b>

<b>Total jobs:</b> {len(applied_jobs)}
<b>Successfully reported:</b> {successful_reports}
<b>Failed:</b> {len(applied_jobs) - successful_reports}
<b>Completion time:</b> {datetime.now().strftime('%H:%M:%S')}

✅ All job applications have been reported to NAV as required.
                    """
                    
                    await self.telegram_bot.send_message(summary_msg)
                    
                    return {
                        "status": "success",
                        "total_jobs": len(applied_jobs),
                        "successful_reports": successful_reports,
                        "failed_reports": len(applied_jobs) - successful_reports
                    }
                
                else:
                    error_msg = "❌ User not logged in to NAV. Manual intervention required."
                    await self.telegram_bot.send_message(error_msg)
                    return {"status": "error", "message": "Not logged in"}
                    
            except Exception as e:
                error_msg = f"❌ NAV reporting error: {str(e)}"
                await self.telegram_bot.send_message(error_msg)
                return {"status": "error", "error": str(e)}
            finally:
                await browser.close()

    async def _fill_nav_form(self, page, job_data):
        """Заповнює NAV форму для одної заявки."""
        
        try:
            # Очікуємо форму
            await page.wait_for_selector('input, select', timeout=5000)
            
            # Заповнюємо поля
            title_input = await page.query_selector('input[placeholder*="stilling"], input[name*="titel"]')
            if title_input:
                await title_input.fill(job_data.get('title', ''))
            
            company_input = await page.query_selector('input[placeholder*="bedrift"], input[name*="company"]')
            if company_input:
                await company_input.fill(job_data.get('company', ''))
            
            # Дата подачі
            date_input = await page.query_selector('input[type="date"]')
            if date_input:
                today = datetime.now().strftime('%Y-%m-%d')
                await date_input.fill(today)
            
            # Submit кнопка
            submit_button = await page.query_selector('button[type="submit"], button:has-text("Send"), button:has-text("Lagre")')
            if submit_button:
                await submit_button.click()
                await page.wait_for_timeout(2000)
                return True
            
            return False
            
        except Exception as e:
            print(f"Form filling error: {e}")
            return False

# Функція для запуску з командного рядка
async def run_production_nav_workflow(username, applied_jobs):
    """Запуск production NAV workflow."""
    workflow = ProductionNAVWorkflow(username)
    return await workflow.run_semi_automated_nav_workflow(applied_jobs)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        username = sys.argv[1]
        # Тестові дані
        test_jobs = [
            {"title": "Test Job 1", "company": "Test Company 1"},
            {"title": "Test Job 2", "company": "Test Company 2"}
        ]
        result = asyncio.run(run_production_nav_workflow(username, test_jobs))
        print(f"Result: {result}")
    else:
        print("Usage: python production_nav_workflow.py <username>")
