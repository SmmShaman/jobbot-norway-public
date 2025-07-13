"""Test NAV BankID login process."""
import asyncio
from playwright.async_api import async_playwright
import os

async def test_nav_login():
    """Тестування процесу логіну на NAV."""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=["--start-maximized"]
        )
        
        page = await browser.new_page()
        
        try:
            print("🌐 Opening NAV aktivitetsplan...")
            await page.goto("https://aktivitetsplan.nav.no/aktivitet/ny/stilling")
            
            print("⏳ Waiting for page load...")
            await page.wait_for_timeout(5000)
            
            # Скріншот початкового стану
            await page.screenshot(path="/app/data/nav_step1.png")
            print("📸 Screenshot saved: nav_step1.png")
            
            print("Current URL:", page.url)
            print("Page title:", await page.title())
            
            # Шукаємо кнопку логіну
            login_selectors = [
                "button:has-text('Logg inn')",
                "a:has-text('Logg inn')", 
                "[data-testid='login']",
                ".navds-button--primary",
                "button[type='button']"
            ]
            
            login_button = None
            for selector in login_selectors:
                try:
                    login_button = await page.query_selector(selector)
                    if login_button:
                        text = await login_button.inner_text()
                        print(f"✅ Found login button: {selector} - '{text}'")
                        break
                except:
                    continue
            
            if login_button:
                print("🔐 Clicking login button...")
                await login_button.click()
                await page.wait_for_timeout(5000)
                
                await page.screenshot(path="/app/data/nav_step2.png")
                print("📸 Screenshot saved: nav_step2.png")
                print("URL after login click:", page.url)
                
                # Чекаємо BankID форму
                print("⏳ Looking for BankID form...")
                
                # Перевіряємо чи з'явилася форма логіну
                bankid_selectors = [
                    "[name='fnr']",
                    "[data-testid='fnr']", 
                    "input[placeholder*='personnummer']",
                    "#fnr",
                    "input[type='text']"
                ]
                
                await page.wait_for_timeout(3000)
                
                for selector in bankid_selectors:
                    try:
                        element = await page.query_selector(selector)
                        if element:
                            print(f"✅ Found FNR input: {selector}")
                            
                            # Заповнюємо дані
                            fnr = os.getenv('FN_NUMBER', '11057912345')
                            password = os.getenv('BANKID_PWD', 'QWEpoi123987')
                            
                            await page.fill(selector, fnr)
                            print("📝 FNR filled")
                            
                            # Шукаємо поле пароля
                            password_input = await page.query_selector("input[type='password']")
                            if password_input:
                                await password_input.fill(password)
                                print("📝 Password filled")
                                
                                await page.screenshot(path="/app/data/nav_step3.png")
                                print("📸 Screenshot with credentials saved")
                                
                                # Натискаємо submit
                                submit_button = await page.query_selector("button[type='submit']")
                                if submit_button:
                                    await submit_button.click()
                                    print("🔐 Submit clicked - waiting for BankID confirmation...")
                                    
                                    await page.wait_for_timeout(3000)
                                    await page.screenshot(path="/app/data/nav_step4.png")
                                    print("📸 Screenshot after submit saved")
                                    
                                    print("\n📱 CONFIRM LOGIN ON YOUR PHONE!")
                                    print("⏳ Waiting 60 seconds for confirmation...")
                                    
                                    # Чекаємо успішний логін
                                    try:
                                        await page.wait_for_url("**/aktivitetsplan.nav.no/**", timeout=60000)
                                        print("✅ LOGIN SUCCESS!")
                                        
                                        await page.screenshot(path="/app/data/nav_success.png")
                                        print("📸 Success screenshot saved")
                                        
                                        print("🎯 We are now logged in - can interact with forms!")
                                        
                                    except:
                                        print("❌ Login timeout or failed")
                            break
                    except:
                        continue
            else:
                print("❌ Login button not found")
                # Показуємо доступні кнопки
                buttons = await page.query_selector_all("button, a")
                print(f"Found {len(buttons)} clickable elements")
                
                for i, btn in enumerate(buttons[:10]):
                    try:
                        text = await btn.inner_text()
                        if text.strip():
                            print(f"  {i}: '{text.strip()[:30]}'")
                    except:
                        continue
            
            # Тримаємо браузер відкритим
            print("\n⏸️ Browser kept open for inspection")
            print("Press Ctrl+C to close...")
            await page.wait_for_timeout(300000)  # 5 хвилин
            
        except Exception as e:
            print(f"❌ Error: {e}")
            await page.screenshot(path="/app/data/nav_error.png")
        
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_nav_login())
