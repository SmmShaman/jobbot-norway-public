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

            # Логуємо всі navigation events
            page.on('framenavigated', lambda frame: print(f"🔄 Frame navigated: {frame.url}"))
            page.on('request', lambda request: print(f"📤 Request: {request.method} {request.url}"))
            page.on('response', lambda response: print(f"📥 Response: {response.status} {response.url}"))

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
            
            # Знаходимо password frame
            password_frame = None
            for i in range(90):
                await asyncio.sleep(1)
                if i % 10 == 0:
                    print(f"⏱️ {i+1}/90 seconds - searching for password frame...")
                
                frames = page.frames
                for frame in frames:
                    if 'csfe.bankid.no' in frame.url:
                        try:
                            inputs_count = await frame.evaluate("() => document.querySelectorAll('input').length")
                            if inputs_count > 0:
                                print(f"✅ FOUND PASSWORD FRAME! URL: {frame.url}")
                                password_frame = frame
                                break
                        except:
                            continue
                if password_frame:
                    break

            if password_frame:
                print("🔑 STEP 7: Filling password...")
                await password_frame.fill('input', password)
                print("✅ Password filled")
                
                await asyncio.sleep(2)
                
                # Скріншот перед натисканням Neste
                await page.screenshot(path="/app/before_neste_click.png")
                print("📸 Screenshot before Neste click saved")

                print("🎯 STEP 8: Clicking Neste...")
                await password_frame.click('button:has-text("Neste")')
                print("✅ Neste clicked")

                print("🔍 === DETAILED FLOW ANALYSIS AFTER NESTE CLICK ===")
                
                # Детальний аналіз кожні 2 секунди протягом 30 секунд
                for i in range(15):  # 15 * 2 = 30 секунд
                    await asyncio.sleep(2)
                    step = i + 1
                    print(f"\n📊 === STEP {step}/15 ({step*2} seconds after Neste) ===")
                    
                    # Поточний URL головної сторінки
                    main_url = page.url
                    print(f"🌐 Main page URL: {main_url}")
                    
                    # Заголовок сторінки
                    title = await page.title()
                    print(f"📄 Page title: {title}")
                    
                    # Аналіз всіх frames
                    frames = page.frames
                    print(f"🖼️ Total frames: {len(frames)}")
                    
                    for frame_idx, frame in enumerate(frames):
                        frame_url = frame.url
                        try:
                            frame_title = await frame.title()
                            frame_text = await frame.inner_text('body')
                            frame_text_preview = frame_text[:100].replace('\n', ' ') if frame_text else "No text"
                            print(f"   Frame {frame_idx}: {frame_url}")
                            print(f"   Title: {frame_title}")
                            print(f"   Text: {frame_text_preview}...")
                            
                            # Перевірка наявності форм/кнопок
                            forms_count = await frame.evaluate("() => document.querySelectorAll('form').length")
                            buttons_count = await frame.evaluate("() => document.querySelectorAll('button').length")
                            inputs_count = await frame.evaluate("() => document.querySelectorAll('input').length")
                            
                            if forms_count > 0 or buttons_count > 0 or inputs_count > 0:
                                print(f"   Elements: {forms_count} forms, {buttons_count} buttons, {inputs_count} inputs")
                                
                        except Exception as e:
                            print(f"   Frame {frame_idx}: {frame_url} (Access denied: {e})")
                    
                    # Перевірка чи з'явилися повідомлення про помилки
                    page_text = await page.inner_text('body')
                    error_words = ['error', 'feil', 'problem', 'failed', 'timeout']
                    found_errors = [word for word in error_words if word.lower() in page_text.lower()]
                    if found_errors:
                        print(f"⚠️ Possible errors detected: {found_errors}")
                    
                    # Перевірка успішних індикаторів
                    success_words = ['success', 'completed', 'ferdig', 'godkjent', 'logget inn']
                    found_success = [word for word in success_words if word.lower() in page_text.lower()]
                    if found_success:
                        print(f"✅ Success indicators: {found_success}")
                    
                    # Скріншот кожні 10 секунд
                    if step % 5 == 0:
                        await page.screenshot(path=f"/app/flow_step_{step}.png")
                        print(f"📸 Screenshot at step {step} saved")
                    
                    # Перевірка чи повернулися в NAV
                    if 'nav.no' in main_url and 'aktivitet' in main_url:
                        print("🎉 SUCCESS! Returned to NAV aktivitetsplan!")
                        break
                    elif 'nav.no' in main_url:
                        print("🔄 Redirected to NAV (but not aktivitetsplan)")
                        break
                    elif 'id-porten' in main_url:
                        print("🔄 Still in ID-porten flow")
                    elif 'bankid' in main_url:
                        print("🔄 Still in BankID flow")
                    else:
                        print(f"🤔 Unknown state: {main_url}")

                # Фінальний стан
                final_url = page.url
                final_title = await page.title()
                
                print(f"\n🎯 === FINAL STATE ===")
                print(f"🌐 Final URL: {final_url}")
                print(f"📄 Final title: {final_title}")
                
                if 'nav.no' in final_url:
                    print("✅ AUTHENTICATION COMPLETED SUCCESSFULLY!")
                else:
                    print("⚠️ Authentication may not be complete")
                    
                # Фінальний скріншот
                await page.screenshot(path="/app/final_state.png", full_page=True)
                print("📸 Final full page screenshot saved")
                    
            else:
                print("❌ Password frame never appeared")

            await browser.close()

    finally:
        xvfb_process.terminate()
        subprocess.run(["pkill", "-f", "Xvfb"], check=False)
        print("🔴 Display stopped")

if __name__ == "__main__":
    asyncio.run(main())
