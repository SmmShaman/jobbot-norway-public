import asyncio
import os
import subprocess
import time
from playwright.async_api import async_playwright

class HeadfulNAVWorkflow:
    def __init__(self, username):
        self.username = username
        self.fnr = os.getenv('FN_NUMBER')
        self.display = ':99'

    async def test_headful_approach(self):
        print('🖥️ Testing HEADFUL approach for BankID...')
        
        try:
            print('🖥️ Starting virtual display...')
            subprocess.run(['pkill', '-f', 'Xvfb'], check=False)
            subprocess.Popen([
                'Xvfb', self.display, 
                '-screen', '0', '1920x1080x24', 
                '-ac'
            ])
            os.environ['DISPLAY'] = self.display
            time.sleep(3)
            print(f'✅ Virtual display started: {self.display}')
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=False,
                    args=['--no-sandbox', '--disable-dev-shm-usage']
                )
                page = await browser.new_page()
                
                try:
                    print('🌐 Navigating to NAV...')
                    await page.goto('https://aktivitetsplan.nav.no/aktivitet/ny/stilling', timeout=30000)
                    await page.wait_for_load_state('networkidle')
                    
                    screenshot_path = f'/app/data/users/{self.username}/headful_test.png'
                    await page.screenshot(path=screenshot_path)
                    print(f'📷 Screenshot: {screenshot_path}')
                    
                    current_url = page.url
                    print(f'📍 URL: {current_url}')
                    
                    if 'idporten.no' in current_url:
                        print('✅ SUCCESS: ID-porten detected in HEADFUL mode!')
                        print('🎯 OS-level clicks should work with isTrusted=true')
                        return {'status': 'SUCCESS', 'url': current_url}
                    else:
                        page_title = await page.title()
                        print(f'📄 Title: {page_title}')
                        return {'status': 'partial', 'url': current_url, 'title': page_title}
                        
                except Exception as nav_error:
                    print(f'❌ Navigation error: {nav_error}')
                    return {'status': 'error', 'error': str(nav_error)}
                finally:
                    await browser.close()
                    
        except Exception as e:
            print(f'❌ Headful test error: {e}')
            return {'status': 'error', 'error': str(e)}
        finally:
            subprocess.run(['pkill', '-f', 'Xvfb'], check=False)
            print('🔴 Virtual display stopped')

async def main():
    print('🚀 Starting Headful BankID Test...')
    workflow = HeadfulNAVWorkflow('vitalii')
    result = await workflow.test_headful_approach()
    print('=' * 50)
    print('📊 HEADFUL TEST RESULT:')
    print(f'   Status: {result.get("status")}')
    print(f'   Message: {result.get("message", "N/A")}')
    if result.get('url'):
        print(f'   URL: {result.get("url")}')
    print('=' * 50)

if __name__ == '__main__':
    asyncio.run(main())
