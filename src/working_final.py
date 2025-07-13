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

            print("🎯 STEP 5: COORDINATE CLICK on BankID-app...")
            await page.mouse.click(640, 338)

            print("⏰ STEP 6: Waiting for modal with detection...")
            modal_found = False
            for i in range(30):
                await asyncio.sleep(1)
                print(f"⏱️ {i+1}/30 seconds...")
                
                # Перевіряємо чи з'явилося поле пароля
                password_visible = await page.evaluate("""() => {
                    const inputs = document.querySelectorAll('input[type="password"]');
                    return inputs.length > 0 && inputs[0].offsetParent !== null;
                }""")
                
                if password_visible:
                    print("✅ Password field detected!")
                    modal_found = True
                    break

            if not modal_found:
                print("⚠️ Modal not detected, continuing anyway...")

            print("🔑 STEP 7: Filling password...")
            
            # Спочатку перевіряємо скільки полів пароля
            password_count = await page.evaluate("""() => {
                const inputs = document.querySelectorAll('input[type="password"]');
                return inputs.length;
            }""")
            print(f"🔍 Found {password_count} password fields")
            
            # Заповнюємо пароль
            if password_count > 0:
                await page.evaluate("""(pwd) => {
                    const inputs = document.querySelectorAll('input[type="password"]');
                    for (let input of inputs) {
                        input.value = pwd;
                        input.focus();
                        input.dispatchEvent(new Event('input', {bubbles: true}));
                        input.dispatchEvent(new Event('change', {bubbles: true}));
                    }
                }""", password)
                print("✅ Password filled in password fields")
            else:
                print("⚠️ No password fields found, trying all inputs")
                await page.evaluate("""(pwd) => {
                    const inputs = document.querySelectorAll('input');
                    for (let input of inputs) {
                        input.value = pwd;
                        input.dispatchEvent(new Event('input', {bubbles: true}));
                        input.dispatchEvent(new Event('change', {bubbles: true}));
                    }
                }""", password)

            await asyncio.sleep(2)

            print("🎯 STEP 8: Clicking Neste...")
            button_clicked = await page.evaluate("""() => {
                const buttons = document.querySelectorAll('button');
                for (let btn of buttons) {
                    const text = (btn.textContent || '').toLowerCase();
                    if (text.includes('neste')) {
                        btn.click();
                        return true;
                    }
                }
                return false;
            }""")
            
            if button_clicked:
                print("✅ Button clicked successfully")
            else:
                print("⚠️ No 'Neste' button found")

            print("✅ STEP 9: Waiting for final result...")
            
            # Чекаємо редирект до 15 секунд
            for i in range(15):
                await asyncio.sleep(1)
                current_url = page.url
                print(f"⏱️ {i+1}/15 - Current URL: {current_url}")
                
                if 'nav.no' in current_url:
                    print("🎉 SUCCESS! Redirected back to NAV!")
                    break

            final_url = page.url
            print(f"🎉 COMPLETE! Final URL: {final_url}")
            
            if 'nav.no' in final_url:
                print("✅ AUTHENTICATION SUCCESS!")
            else:
                print("⚠️ Authentication may not be complete")

            await browser.close()

    finally:
        xvfb_process.terminate()
        subprocess.run(["pkill", "-f", "Xvfb"], check=False)
        print("🔴 Display stopped")

if __name__ == "__main__":
    asyncio.run(main())
