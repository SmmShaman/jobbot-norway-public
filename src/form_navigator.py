"""Enhanced navigation with cookie handling."""
import asyncio
import os
from datetime import datetime
from playwright.async_api import async_playwright

class FormNavigator:
    def __init__(self):
        self.screenshots_dir = '/app/data/screenshots'
        os.makedirs(self.screenshots_dir, exist_ok=True)
    
    async def handle_cookies(self, page):
        """Handle cookie consent dialogs."""
        cookie_selectors = [
            'text="Acceptere"',
            'text="Accept"', 
            'text="Godkjenn"',
            'text="OK"',
            '[id*="cookie"] button',
            '[class*="cookie"] button',
            '[data-testid*="cookie"]',
            '.cookie-consent button',
            '#cookie-consent button'
        ]
        
        for selector in cookie_selectors:
            try:
                element = await page.query_selector(selector)
                if element and await element.is_visible():
                    await element.click()
                    await page.wait_for_timeout(1000)
                    print(f'✅ Clicked cookie consent: {selector}')
                    return True
            except:
                continue
        
        print('⚠️ No cookie consent found')
        return False
    
    async def navigate_to_application(self, job_url, username):
        """Navigate to employer application form with cookie handling."""
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                # Navigate to job page
                await page.goto(job_url, timeout=30000)
                await page.wait_for_timeout(2000)
                
                # Take job page screenshot
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                job_screenshot = f'{self.screenshots_dir}/{username}_job_page_{timestamp}.png'
                await page.screenshot(path=job_screenshot, full_page=True)
                
                # Find application button
                apply_selectors = [
                    'text="Gå til søknad"',
                    'text="Send søknad"',
                    'text="Søk på stillingen"',
                    '[href*="søknad"]',
                    '[href*="apply"]',
                    '.apply-button'
                ]
                
                apply_button = None
                for selector in apply_selectors:
                    try:
                        apply_button = await page.query_selector(selector)
                        if apply_button and await apply_button.is_visible():
                            break
                    except:
                        continue
                
                if not apply_button:
                    await browser.close()
                    return {'error': 'Application button not found', 'success': False}
                
                # Get application URL
                href = await apply_button.get_attribute('href')
                if href:
                    employer_url = href if href.startswith('http') else f'{page.url.split("/stillinger")[0]}{href}'
                else:
                    await apply_button.click()
                    await page.wait_for_timeout(3000)
                    employer_url = page.url
                
                # Navigate to employer site
                if employer_url != job_url:
                    await page.goto(employer_url, timeout=30000)
                    await page.wait_for_load_state('networkidle')
                
                # Handle cookies first
                await self.handle_cookies(page)
                await page.wait_for_timeout(2000)
                
                # Take form screenshot after cookies
                form_screenshot = f'{self.screenshots_dir}/{username}_employer_form_{timestamp}.png'
                await page.screenshot(path=form_screenshot, full_page=True)
                
                # Get clean HTML content
                html_content = await page.content()
                
                await browser.close()
                
                return {
                    'employer_url': employer_url,
                    'job_screenshot': job_screenshot,
                    'form_screenshot': form_screenshot,
                    'html_content': html_content,
                    'success': True
                }
                
        except Exception as e:
            return {'error': str(e), 'success': False}
