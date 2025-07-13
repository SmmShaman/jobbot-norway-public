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

            print("⏰ STEP 6: Waiting and analyzing page...")
            for i in range(20):
                await asyncio.sleep(1)
                print(f"⏱️ {i+1}/20 seconds...")
                
                # Детальна діагностика DOM
                page_info = await page.evaluate("""() => {
                    return {
                        url: window.location.href,
                        title: document.title,
                        inputs_total: document.querySelectorAll('input').length,
                        inputs_password: document.querySelectorAll('input[type="password"]').length,
                        buttons_total: document.querySelectorAll('button').length,
                        visible_text: document.body ? document.body.innerText.substring(0, 200) : 'No body',
                        has_modal: !!document.querySelector('.modal, .popup, [role="dialog"]'),
                        all_input_types: Array.from(document.querySelectorAll('input')).map(inp => inp.type || 'text')
                    };
                }""")
                
                print(f"🔍 DEBUG {i+1}: URL: {page_info['url']}")
                print(f"   Title: {page_info['title']}")
                print(f"   Inputs: {page_info['inputs_total']} total, {page_info['inputs_password']} password")
                print(f"   Buttons: {page_info['buttons_total']}")
                print(f"   Modal: {page_info['has_modal']}")
                print(f"   Input types: {page_info['all_input_types']}")
                print(f"   Text snippet: {page_info['visible_text'][:100]}...")
                
                # Припинити якщо знайдено поле пароля
                if page_info['inputs_password'] > 0:
                    print("✅ Password field detected!")
                    break
                    
                # Або якщо текст містить ключові слова
                if any(word in page_info['visible_text'].lower() for word in ['password', 'passord', 'kode']):
                    print("✅ Password-related text detected!")
                    break

            print("🔑 STEP 7: Final analysis...")
            await asyncio.sleep(2)
            
            # Фінальна діагностика всіх елементів
            all_elements = await page.evaluate("""() => {
                const elements = document.querySelectorAll('*');
                return Array.from(elements).slice(0, 50).map(el => ({
                    tag: el.tagName,
                    type: el.type || '',
                    text: (el.textContent || '').trim().substring(0, 30),
                    visible: el.offsetParent !== null
                })).filter(el => el.text || el.type);
            }""")
            
            print("🔍 Page elements:")
            for elem in all_elements:
                print(f"   {elem['tag']} type='{elem['type']}' visible={elem['visible']} text='{elem['text']}'")

            await browser.close()

    finally:
        xvfb_process.terminate()
        subprocess.run(["pkill", "-f", "Xvfb"], check=False)
        print("🔴 Display stopped")

if __name__ == "__main__":
    asyncio.run(main())
