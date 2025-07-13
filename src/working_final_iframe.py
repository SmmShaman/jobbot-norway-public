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

            print("📱 PUSH SENT! Waiting for confirmation...")
            print("⏰ Please confirm on your mobile device now!")
            
            # Чекаємо довше і робимо screenshot
            modal_found = False
            for i in range(45):  # 45 * 2 = 90 секунд
                await asyncio.sleep(2)
                print(f"⏱️ Check {i+1}/45 ({(i+1)*2} seconds)")
                
                # Збережемо screenshot для діагностики
                if i == 10:  # Через 20 секунд
                    await page.screenshot(path="/app/after_push.png")
                    print("📸 Screenshot saved for diagnosis")
                
                # Перевіряємо основну сторінку
                password_main = await page.evaluate("""() => {
                    const inputs = document.querySelectorAll('input[type="password"], input[placeholder*="assord"], input[placeholder*="ode"]');
                    return inputs.length;
                }""")
                
                # Перевіряємо всі iframe
                frames = page.frames
                password_in_frames = 0
                
                for frame in frames:
                    try:
                        frame_passwords = await frame.evaluate("""() => {
                            const inputs = document.querySelectorAll('input[type="password"], input[placeholder*="assord"], input[placeholder*="ode"]');
                            return inputs.length;
                        }""")
                        password_in_frames += frame_passwords
                    except:
                        continue
                
                total_passwords = password_main + password_in_frames
                
                if total_passwords > 0:
                    print(f"✅ PASSWORD DETECTED! Main: {password_main}, Frames: {password_in_frames}")
                    modal_found = True
                    break
                
                # Перевіряємо зміну тексту на сторінці
                page_text = await page.evaluate("""() => {
                    return document.body.innerText.toLowerCase();
                }""")
                
                if any(word in page_text for word in ['password', 'passord', 'kode', 'pin']):
                    print("✅ PASSWORD TEXT DETECTED!")
                    modal_found = True
                    break
                
                # Показуємо поточний стан сторінки
                if i % 5 == 0:  # Кожні 10 секунд
                    current_text = page_text[:100].replace('\n', ' ')
                    print(f"   Current page text: {current_text}...")

            if modal_found:
                print("🔑 STEP 7: Filling password in all possible fields...")
                
                # Заповнюємо в основній сторінці
                await page.evaluate("""(pwd) => {
                    const inputs = document.querySelectorAll('input[type="password"], input[placeholder*="assord"], input[placeholder*="ode"]');
                    for (let input of inputs) {
                        input.value = pwd;
                        input.focus();
                        input.dispatchEvent(new Event('input', {bubbles: true}));
                        input.dispatchEvent(new Event('change', {bubbles: true}));
                        console.log('Password filled in main page');
                    }
                }""", password)
                
                # Заповнюємо у всіх iframe
                for frame in frames:
                    try:
                        await frame.evaluate("""(pwd) => {
                            const inputs = document.querySelectorAll('input[type="password"], input[placeholder*="assord"], input[placeholder*="ode"]');
                            for (let input of inputs) {
                                input.value = pwd;
                                input.focus();
                                input.dispatchEvent(new Event('input', {bubbles: true}));
                                input.dispatchEvent(new Event('change', {bubbles: true}));
                                console.log('Password filled in iframe');
                            }
                        }""", password)
                    except:
                        continue
                
                await asyncio.sleep(3)

                print("🎯 STEP 8: Clicking Next in all frames...")
                
                # Клікаємо в основній сторінці
                main_clicked = await page.evaluate("""() => {
                    const buttons = document.querySelectorAll('button');
                    for (let btn of buttons) {
                        const text = (btn.textContent || '').toLowerCase();
                        if (text.includes('neste') || text.includes('next') || text.includes('continue')) {
                            btn.click();
                            return true;
                        }
                    }
                    return false;
                }""")
                
                # Клікаємо у всіх iframe
                for frame in frames:
                    try:
                        await frame.evaluate("""() => {
                            const buttons = document.querySelectorAll('button');
                            for (let btn of buttons) {
                                const text = (btn.textContent || '').toLowerCase();
                                if (text.includes('neste') || text.includes('next') || text.includes('continue')) {
                                    btn.click();
                                    return true;
                                }
                            }
                        }""")
                    except:
                        continue
                
                print(f"✅ Button clicked in main: {main_clicked}")

                print("✅ STEP 9: Waiting for redirect (30 seconds)...")
                
                for i in range(15):  # 15 * 2 = 30 секунд
                    await asyncio.sleep(2)
                    current_url = page.url
                    print(f"⏱️ Redirect {i+1}/15 - URL: {current_url}")
                    
                    if 'nav.no' in current_url:
                        print("🎉 SUCCESS! Redirected to NAV!")
                        break

                final_url = page.url
                print(f"🎉 COMPLETE! Final URL: {final_url}")
                
                if 'nav.no' in final_url:
                    print("✅ AUTHENTICATION SUCCESS!")
                else:
                    print("⚠️ Still on BankID")
                    
            else:
                print("❌ Password modal never detected")
                await page.screenshot(path="/app/timeout_screenshot.png")
                print("📸 Timeout screenshot saved")

            await browser.close()

    finally:
        xvfb_process.terminate()
        subprocess.run(["pkill", "-f", "Xvfb"], check=False)
        print("🔴 Display stopped")

if __name__ == "__main__":
    asyncio.run(main())
