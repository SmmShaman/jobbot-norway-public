import asyncio
import os
import subprocess
import time
from playwright.async_api import async_playwright

async def main():
    fnr = os.getenv("FN_NUMBER")
    password = os.getenv("BANKID_PWD")
    display = ":99"

    print("🖥️ Starting display...")
    subprocess.run(["pkill", "-f", "Xvfb"], check=False)
    time.sleep(1)
    xvfb_process = subprocess.Popen(["Xvfb", display, "-screen", "0", "1920x1080x24", "-ac"])
    os.environ["DISPLAY"] = display
    time.sleep(2)
    print("✅ Display started")

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False, args=["--no-sandbox"])
            page = await browser.new_page()

            print("🌐 STEP 1: Going to NAV...")
            await page.goto("https://aktivitetsplan.nav.no/aktivitet/ny/stilling")
            await page.wait_for_load_state("networkidle")

            print("✅ STEP 2: Clicking BankID...")
            await page.evaluate("""() => {
                const elements = document.querySelectorAll('*');
                for (let el of elements) {
                    if ((el.textContent || '').trim() === 'BankID' && el.tagName === 'H2') {
                        el.click();
                        return;
                    }
                }
            }""")

            await asyncio.sleep(5)
            await page.wait_for_load_state("networkidle")

            print("✅ STEP 3: Filling FNR:", fnr)
            await page.evaluate("""(fnr) => {
                const inputs = document.querySelectorAll('input');
                if (inputs[0]) {
                    inputs[0].value = fnr;
                    inputs[0].dispatchEvent(new Event('input', {bubbles: true}));
                }
            }""", fnr)

            await asyncio.sleep(2)

            print("✅ STEP 4: Clicking Neste...")
            await page.evaluate("""() => {
                const buttons = document.querySelectorAll('button');
                for (let btn of buttons) {
                    if ((btn.textContent || '').toLowerCase().includes('neste')) {
                        btn.click();
                        return;
                    }
                }
            }""")

            await asyncio.sleep(5)

            print("🎯 STEP 5: COORDINATE CLICK on BankID-app (ONLY hidden button)...")
            await page.mouse.click(640, 338)

            print("📱 PUSH SENT! Please confirm on your mobile now!")
            print("⏰ Waiting for modal with broad selectors...")
            
            # Чекаємо появу модального вікна з широкими селекторами
            modal_found = False
            for i in range(60):  # 2 хвилини очікування
                await asyncio.sleep(1)
                if i % 5 == 0:  # Лог кожні 5 секунд
                    print(f"⏱️ {i+1}/60 seconds waiting for modal...")
                
                # Широкий пошук полів введення (не тільки password)
                password_field = await page.query_selector('input[type="password"]')
                if not password_field:
                    # Шукаємо поля з текстом про пароль
                    password_field = await page.query_selector('input[placeholder*="assord"]')
                if not password_field:
                    # Шукаємо поля з placeholder про код
                    password_field = await page.query_selector('input[placeholder*="ode"]')
                if not password_field:
                    # Шукаємо поля поблизу тексту "password"
                    password_field = await page.evaluate("""() => {
                        const labels = document.querySelectorAll('*');
                        for (let label of labels) {
                            if ((label.textContent || '').toLowerCase().includes('passord') || 
                                (label.textContent || '').toLowerCase().includes('password')) {
                                const nearby = label.parentElement?.querySelector('input') || 
                                             label.nextElementSibling?.querySelector?.('input') ||
                                             label.querySelector('input');
                                if (nearby) return nearby;
                            }
                        }
                        return null;
                    }""")
                
                if password_field:
                    print("✅ PASSWORD FIELD FOUND!")
                    modal_found = True
                    break
                
                # Якщо не знайшли, перевіряємо чи з'явився новий текст
                page_text = await page.inner_text('body')
                if any(word in page_text.lower() for word in ['dit bankid-passord', 'fyll inn', 'password', 'passord']):
                    print("✅ PASSWORD TEXT DETECTED - searching again...")
                    continue

            if modal_found:
                print("🔑 STEP 7: Filling password with standard Playwright methods...")
                
                # Знаходимо поле пароля знову
                password_selectors = [
                    'input[type="password"]',
                    'input[placeholder*="assord"]', 
                    'input[placeholder*="ode"]'
                ]
                
                filled = False
                for selector in password_selectors:
                    try:
                        field = await page.query_selector(selector)
                        if field and await field.is_visible():
                            await field.fill(password)  # Стандартний Playwright метод
                            print(f"✅ Password filled using {selector}")
                            filled = True
                            break
                    except Exception as e:
                        print(f"⚠️ Failed with {selector}: {e}")
                
                if not filled:
                    print("⚠️ Trying alternative fill method...")
                    await page.evaluate("""(pwd) => {
                        const inputs = document.querySelectorAll('input');
                        for (let input of inputs) {
                            if (input.offsetParent !== null) {  // visible
                                input.value = pwd;
                                input.dispatchEvent(new Event('input', {bubbles: true}));
                            }
                        }
                    }""", password)

                await asyncio.sleep(2)

                print("🎯 STEP 8: Clicking Neste with standard Playwright click...")
                
                # Знаходимо кнопку Neste
                next_selectors = [
                    'button:has-text("Neste")',
                    'button:has-text("neste")', 
                    'text=Neste',
                    'text=neste'
                ]
                
                clicked = False
                for selector in next_selectors:
                    try:
                        button = await page.query_selector(selector)
                        if button and await button.is_visible():
                            await button.click()  # Стандартний Playwright метод
                            print(f"✅ Neste clicked using {selector}")
                            clicked = True
                            break
                    except Exception as e:
                        print(f"⚠️ Failed with {selector}: {e}")
                
                if not clicked:
                    print("⚠️ Trying alternative click method...")
                    await page.evaluate("""() => {
                        const buttons = document.querySelectorAll('button');
                        for (let btn of buttons) {
                            if ((btn.textContent || '').toLowerCase().includes('neste')) {
                                btn.click();
                                return;
                            }
                        }
                    }""")

                print("✅ STEP 9: Waiting for redirect...")
                
                # Чекаємо редирект
                for i in range(20):
                    await asyncio.sleep(1)
                    current_url = page.url
                    if i % 3 == 0:
                        print(f"⏱️ Redirect check {i+1}/20 - URL: {current_url}")
                    
                    if 'nav.no' in current_url:
                        print("🎉 SUCCESS! Redirected back to NAV!")
                        break

                final_url = page.url
                print(f"🎉 FINAL URL: {final_url}")
                
                if 'nav.no' in final_url:
                    print("✅ AUTHENTICATION COMPLETED SUCCESSFULLY!")
                else:
                    print("⚠️ Still on BankID - may need more time")
                    
            else:
                print("❌ Modal never appeared or field not found")

            await browser.close()

    finally:
        xvfb_process.terminate()
        subprocess.run(["pkill", "-f", "Xvfb"], check=False)
        print("🔴 Display stopped")

if __name__ == "__main__":
    asyncio.run(main())
