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

            print("📱 PUSH SENT! Please confirm on your mobile device")
            print("⏰ Waiting with 2-second intervals (60 seconds total)...")
            
            modal_found = False
            for i in range(30):  # 30 * 2 секунди = 60 секунд
                await asyncio.sleep(2)  # Перевірка кожні 2 секунди
                check_num = i + 1
                print(f"⏱️ Check {check_num}/30 ({check_num*2} seconds)")
                
                # Перевіряємо чи з'явилося поле пароля
                password_visible = await page.evaluate("""() => {
                    const inputs = document.querySelectorAll('input[type="password"]');
                    return inputs.length > 0;
                }""")
                
                if password_visible:
                    print("✅ PASSWORD MODAL DETECTED!")
                    modal_found = True
                    break
                    
                # Перевіряємо текст на сторінці
                page_text = await page.evaluate("""() => {
                    return document.body.innerText.toLowerCase();
                }""")
                
                if 'password' in page_text or 'passord' in page_text:
                    print("✅ PASSWORD TEXT DETECTED!")
                    modal_found = True
                    break

            if not modal_found:
                print("❌ No password modal detected after 60 seconds")
                print("🔄 Modal may not have appeared - extending wait time...")
                
                # Додаткових 30 секунд очікування
                for i in range(15):
                    await asyncio.sleep(2)
                    print(f"⏱️ Extended wait {i+1}/15...")
                    
                    password_visible = await page.evaluate("""() => {
                        const inputs = document.querySelectorAll('input[type="password"]');
                        return inputs.length > 0;
                    }""")
                    
                    if password_visible:
                        print("✅ PASSWORD MODAL FINALLY DETECTED!")
                        modal_found = True
                        break

            if modal_found:
                print("🔑 STEP 7: Filling password...")
                
                # Заповнюємо пароль
                await page.evaluate("""(pwd) => {
                    const inputs = document.querySelectorAll('input[type="password"]');
                    if (inputs.length > 0) {
                        inputs[0].value = pwd;
                        inputs[0].focus();
                        inputs[0].dispatchEvent(new Event('input', {bubbles: true}));
                        inputs[0].dispatchEvent(new Event('change', {bubbles: true}));
                        console.log('Password filled');
                    }
                }""", password)
                
                await asyncio.sleep(3)  # Пауза після заповнення

                print("🎯 STEP 8: Clicking Neste...")
                button_clicked = await page.evaluate("""() => {
                    const buttons = document.querySelectorAll('button');
                    for (let btn of buttons) {
                        const text = (btn.textContent || '').toLowerCase();
                        if (text.includes('neste')) {
                            btn.click();
                            console.log('Neste button clicked');
                            return true;
                        }
                    }
                    return false;
                }""")
                
                if button_clicked:
                    print("✅ Neste button clicked")
                else:
                    print("⚠️ Neste button not found")

                print("✅ STEP 9: Waiting for redirect (20 seconds)...")
                
                # Чекаємо редирект 20 секунд
                for i in range(10):  # 10 * 2 секунди = 20 секунд
                    await asyncio.sleep(2)
                    current_url = page.url
                    print(f"⏱️ Redirect check {i+1}/10 - URL: {current_url}")
                    
                    if 'nav.no' in current_url:
                        print("🎉 SUCCESS! Redirected back to NAV!")
                        break

                final_url = page.url
                print(f"🎉 COMPLETE! Final URL: {final_url}")
                
                if 'nav.no' in final_url:
                    print("✅ AUTHENTICATION SUCCESS!")
                else:
                    print("⚠️ Still on BankID - authentication may need more time")
            else:
                print("❌ Could not detect password modal - please try manual confirmation")

            await browser.close()

    finally:
        xvfb_process.terminate()
        subprocess.run(["pkill", "-f", "Xvfb"], check=False)
        print("🔴 Display stopped")

if __name__ == "__main__":
    asyncio.run(main())
