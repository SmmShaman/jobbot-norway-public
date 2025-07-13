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

            print("📱 PUSH SENT!")
            print("🚨 PLEASE CONFIRM ON YOUR MOBILE PHONE NOW!")
            print("⏰ Starting detailed DOM analysis...")
            
            # Детальний аналіз кожні 3 секунди
            for i in range(40):  # 40 * 3 = 120 секунд
                await asyncio.sleep(3)
                print(f"\n🔍 === ANALYSIS {i+1}/40 ({(i+1)*3} seconds) ===")
                
                # Аналіз URL
                current_url = page.url
                print(f"URL: {current_url}")
                
                # Аналіз title
                title = await page.title()
                print(f"Title: {title}")
                
                # Детальний аналіз всіх input елементів
                inputs_analysis = await page.evaluate("""() => {
                    const inputs = document.querySelectorAll('input');
                    return Array.from(inputs).map((input, index) => ({
                        index: index,
                        type: input.type || 'text',
                        placeholder: input.placeholder || '',
                        name: input.name || '',
                        id: input.id || '',
                        visible: input.offsetParent !== null,
                        value: input.value || '',
                        classList: Array.from(input.classList)
                    }));
                }""")
                print(f"Input fields found: {len(inputs_analysis)}")
                for inp in inputs_analysis:
                    print(f"  Input {inp['index']}: type='{inp['type']}' placeholder='{inp['placeholder']}' visible={inp['visible']}")
                
                # Аналіз тексту на сторінці
                page_text = await page.inner_text('body')
                important_words = ['password', 'passord', 'kode', 'pin', 'bankid', 'neste', 'logg', 'bekreft']
                found_words = [word for word in important_words if word in page_text.lower()]
                print(f"Important words found: {found_words}")
                print(f"Page text sample: {page_text[:200]}...")
                
                # Аналіз всіх frames
                frames = page.frames
                print(f"Frames found: {len(frames)}")
                for frame_idx, frame in enumerate(frames):
                    try:
                        frame_url = frame.url
                        frame_inputs = await frame.evaluate("""() => {
                            const inputs = document.querySelectorAll('input');
                            return inputs.length;
                        }""")
                        print(f"  Frame {frame_idx}: URL={frame_url}, inputs={frame_inputs}")
                    except Exception as e:
                        print(f"  Frame {frame_idx}: Error accessing - {e}")
                
                # Перевірка наявності елементів з ключовими словами
                password_related = await page.evaluate("""() => {
                    const elements = document.querySelectorAll('*');
                    const found = [];
                    Array.from(elements).forEach((el, index) => {
                        const text = (el.textContent || '').toLowerCase();
                        const attrs = Array.from(el.attributes || []).map(attr => attr.name + '=' + attr.value).join(' ');
                        if (text.includes('passord') || text.includes('password') || text.includes('kode') || 
                            attrs.includes('password') || attrs.includes('passord')) {
                            found.push({
                                tag: el.tagName,
                                text: text.substring(0, 50),
                                attributes: attrs.substring(0, 100),
                                visible: el.offsetParent !== null
                            });
                        }
                    });
                    return found.slice(0, 10); // Перші 10 знайдених
                }""")
                
                if password_related:
                    print("🔍 Password-related elements:")
                    for elem in password_related:
                        print(f"  {elem['tag']}: '{elem['text']}' visible={elem['visible']}")
                
                # Перевірка чи з'явилося щось нове
                if len(inputs_analysis) > 0:
                    password_inputs = [inp for inp in inputs_analysis if inp['type'] == 'password']
                    if password_inputs:
                        print("✅ PASSWORD INPUT FOUND!")
                        break
                
                # Якщо знайшли текст про пароль
                if 'passord' in page_text.lower() or 'password' in page_text.lower():
                    print("✅ PASSWORD TEXT FOUND!")
                    if i > 5:  # Дамо трохи часу на завантаження DOM
                        break

            print("\n🔍 === FINAL ANALYSIS ===")
            
            # Збереження screenshot
            await page.screenshot(path="/app/final_diagnostic.png", full_page=True)
            print("📸 Full page screenshot saved")
            
            # Фінальний аналіз HTML
            html_content = await page.content()
            print(f"HTML content length: {len(html_content)} characters")
            
            # Пошук прихованих елементів
            hidden_elements = await page.evaluate("""() => {
                const elements = document.querySelectorAll('*');
                const hidden = [];
                Array.from(elements).forEach(el => {
                    const style = window.getComputedStyle(el);
                    if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') {
                        const text = (el.textContent || '').trim();
                        if (text.includes('passord') || text.includes('password') || el.tagName === 'INPUT') {
                            hidden.push({
                                tag: el.tagName,
                                text: text.substring(0, 50),
                                display: style.display,
                                visibility: style.visibility,
                                opacity: style.opacity
                            });
                        }
                    }
                });
                return hidden.slice(0, 10);
            }""")
            
            if hidden_elements:
                print("🕵️ Hidden elements with password/input:")
                for elem in hidden_elements:
                    print(f"  {elem['tag']}: '{elem['text']}' display={elem['display']} visibility={elem['visibility']}")

            await browser.close()

    finally:
        xvfb_process.terminate()
        subprocess.run(["pkill", "-f", "Xvfb"], check=False)
        print("🔴 Display stopped")

if __name__ == "__main__":
    asyncio.run(main())
