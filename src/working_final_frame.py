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

            print("🌐 STEP 1-5: Standard flow...")
            await page.goto("https://aktivitetsplan.nav.no/aktivitet/ny/stilling")
            await page.wait_for_load_state("networkidle")

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

            await page.evaluate("""(fnr) => {
                const inputs = document.querySelectorAll('input');
                if (inputs[0]) {
                    inputs[0].value = fnr;
                    inputs[0].dispatchEvent(new Event('input', {bubbles: true}));
                }
            }""", fnr)
            await asyncio.sleep(2)

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

            print("🎯 STEP 5: COORDINATE CLICK...")
            await page.mouse.click(640, 338)

            print("📱 PUSH SENT! Please confirm on your mobile!")
            print("⏰ Waiting for Frame 1 to load with input field...")
            
            # Чекаємо Frame 1 з input полем
            password_frame = None
            for i in range(90):  # 90 секунд очікування
                await asyncio.sleep(1)
                if i % 10 == 0:
                    print(f"⏱️ {i+1}/90 seconds - searching for password frame...")
                
                frames = page.frames
                for frame in frames:
                    if 'csfe.bankid.no' in frame.url:
                        try:
                            # Перевіряємо чи є input поля в цьому frame
                            inputs_count = await frame.evaluate("""() => {
                                return document.querySelectorAll('input').length;
                            }""")
                            
                            if inputs_count > 0:
                                print(f"✅ FOUND PASSWORD FRAME! URL: {frame.url}")
                                print(f"✅ Input fields in frame: {inputs_count}")
                                password_frame = frame
                                break
                        except Exception as e:
                            # Cross-origin обмеження - очікуване
                            continue
                
                if password_frame:
                    break

            if password_frame:
                print("🔑 STEP 7: Filling password in Frame 1...")
                
                try:
                    # Заповнюємо пароль в iframe
                    await password_frame.fill('input', password)
                    print("✅ Password filled in iframe using frame.fill()")
                except Exception as e:
                    print(f"⚠️ frame.fill() failed: {e}")
                    try:
                        # Альтернативний метод
                        await password_frame.evaluate("""(pwd) => {
                            const inputs = document.querySelectorAll('input');
                            if (inputs.length > 0) {
                                inputs[0].value = pwd;
                                inputs[0].focus();
                                inputs[0].dispatchEvent(new Event('input', {bubbles: true}));
                                inputs[0].dispatchEvent(new Event('change', {bubbles: true}));
                                console.log('Password filled via evaluate');
                            }
                        }""", password)
                        print("✅ Password filled using frame.evaluate()")
                    except Exception as e2:
                        print(f"❌ Both methods failed: {e2}")

                await asyncio.sleep(2)

                print("🎯 STEP 8: Clicking Neste in Frame 1...")
                
                try:
                    # Натискаємо кнопку в iframe
                    await password_frame.click('button:has-text("Neste")')
                    print("✅ Neste clicked in iframe using frame.click()")
                except Exception as e:
                    print(f"⚠️ frame.click() failed: {e}")
                    try:
                        # Альтернативний метод
                        await password_frame.evaluate("""() => {
                            const buttons = document.querySelectorAll('button');
                            for (let btn of buttons) {
                                const text = (btn.textContent || '').toLowerCase();
                                if (text.includes('neste')) {
                                    btn.click();
                                    console.log('Neste clicked via evaluate');
                                    return;
                                }
                            }
                        }""")
                        print("✅ Neste clicked using frame.evaluate()")
                    except Exception as e2:
                        print(f"❌ Both click methods failed: {e2}")

                print("✅ STEP 9: Waiting for redirect...")
                
                # Чекаємо редирект
                for i in range(20):
                    await asyncio.sleep(1)
                    current_url = page.url
                    if i % 3 == 0:
                        print(f"⏱️ Redirect {i+1}/20 - URL: {current_url}")
                    
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
                print("❌ Password frame never appeared")
                print("🔍 Available frames:")
                for i, frame in enumerate(page.frames):
                    print(f"   Frame {i}: {frame.url}")

            await browser.close()

    finally:
        xvfb_process.terminate()
        subprocess.run(["pkill", "-f", "Xvfb"], check=False)
        print("🔴 Display stopped")

if __name__ == "__main__":
    asyncio.run(main())
