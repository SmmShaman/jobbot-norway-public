"""Automatic job application module for NAV using Playwright."""
import asyncio
import json
from datetime import datetime
from playwright.async_api import async_playwright
from typing import Dict, Any, List

class NAVAutoApplicator:
    def __init__(self, user_config: Dict[str, Any]):
        self.user_config = user_config
        self.user_info = user_config.get('user_info', {})
        self.nav_credentials = user_config.get('nav_credentials', {})
        
    async def initialize_browser(self):
        """Initialize browser with user session."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=False)  # Show for debugging
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()

    async def close_browser(self):
        """Close browser."""
        if hasattr(self, 'browser'):
            await self.browser.close()
        if hasattr(self, 'playwright'):
            await self.playwright.stop()

    async def login_to_nav(self) -> bool:
        """Login to NAV arbeidsplassen."""
        try:
            print("🔐 Logging into NAV...")
            
            # Go to NAV login page
            await self.page.goto("https://arbeidsplassen.nav.no/min-side", wait_until='networkidle')
            
            # Look for login button/link
            login_selectors = [
                'text=Logg inn',
                '[href*="login"]',
                'button:has-text("Logg inn")',
                'a:has-text("Logg inn")'
            ]
            
            login_clicked = False
            for selector in login_selectors:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=3000)
                    if element:
                        await element.click()
                        login_clicked = True
                        break
                except:
                    continue
            
            if not login_clicked:
                print("⚠️ Could not find login button, assuming already on login page")
            
            await self.page.wait_for_timeout(3000)
            
            # Check if we need ID-porten authentication
            if "idporten" in self.page.url.lower() or "eid.difi.no" in self.page.url.lower():
                print("🆔 ID-porten authentication required")
                
                # Fill FNR if field exists
                fnr = self.nav_credentials.get('fnr', '')
                if fnr:
                    fnr_selectors = ['input[name="pid"]', 'input[id="username"]', 'input[type="text"]']
                    for selector in fnr_selectors:
                        try:
                            fnr_field = await self.page.wait_for_selector(selector, timeout=2000)
                            if fnr_field:
                                await fnr_field.fill(fnr)
                                print("✅ FNR filled")
                                break
                        except:
                            continue
                
                # Note: Password/BankID requires manual intervention
                print("⚠️ Manual authentication required (BankID/password)")
                print("🖱️ Please complete authentication manually...")
                
                # Wait for successful login (redirect back to arbeidsplassen)
                try:
                    await self.page.wait_for_url("**/arbeidsplassen.nav.no/**", timeout=60000)
                    print("✅ Login successful!")
                    return True
                except:
                    print("❌ Login timeout or failed")
                    return False
            else:
                print("ℹ️ Already logged in or no authentication required")
                return True
                
        except Exception as e:
            print(f"❌ Login error: {e}")
            return False

    async def apply_to_job(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply to a specific job."""
        try:
            job_url = job_data.get('url', '')
            job_title = job_data.get('title', 'Unknown Job')
            
            print(f"📝 Applying to: {job_title}")
            print(f"🔗 URL: {job_url}")
            
            # Navigate to job page
            await self.page.goto(job_url, wait_until='networkidle')
            await self.page.wait_for_timeout(3000)
            
            # Look for apply button
            apply_selectors = [
                'text=Søk på jobben',
                'text=Send søknad',
                'button:has-text("Søk")',
                'a:has-text("Søk på jobben")',
                '[href*="apply"]',
                '[href*="soknad"]'
            ]
            
            apply_button = None
            for selector in apply_selectors:
                try:
                    apply_button = await self.page.wait_for_selector(selector, timeout=3000)
                    if apply_button:
                        break
                except:
                    continue
            
            if not apply_button:
                return {
                    'status': 'ERROR',
                    'message': 'Apply button not found',
                    'job_title': job_title
                }
            
            # Click apply button
            await apply_button.click()
            await self.page.wait_for_timeout(5000)
            
            # Check if external application (redirected away from NAV)
            current_url = self.page.url
            if "arbeidsplassen.nav.no" not in current_url:
                return {
                    'status': 'EXTERNAL',
                    'message': f'External application required: {current_url}',
                    'external_url': current_url,
                    'job_title': job_title
                }
            
            # Fill application form if on NAV
            await self.fill_application_form()
            
            # Submit application
            submit_result = await self.submit_application()
            
            return {
                'status': 'SUCCESS' if submit_result else 'ERROR',
                'message': 'Application submitted successfully' if submit_result else 'Submission failed',
                'job_title': job_title,
                'applied_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'ERROR',
                'message': str(e),
                'job_title': job_data.get('title', 'Unknown')
            }

    async def fill_application_form(self):
        """Fill application form with user data."""
        try:
            print("📝 Filling application form...")
            
            # Personal information
            name = self.user_info.get('full_name', '')
            email = self.user_info.get('email', '')
            phone = self.user_info.get('phone', '')
            
            # Fill name fields
            name_selectors = [
                'input[name*="name"]',
                'input[id*="name"]',
                'input[placeholder*="navn"]'
            ]
            
            for selector in name_selectors:
                try:
                    field = await self.page.query_selector(selector)
                    if field and name:
                        await field.fill(name)
                        print(f"✅ Filled name: {selector}")
                except:
                    continue
            
            # Fill email fields
            email_selectors = [
                'input[type="email"]',
                'input[name*="email"]',
                'input[name*="epost"]'
            ]
            
            for selector in email_selectors:
                try:
                    field = await self.page.query_selector(selector)
                    if field and email:
                        await field.fill(email)
                        print(f"✅ Filled email: {selector}")
                except:
                    continue
            
            # Fill phone fields
            phone_selectors = [
                'input[type="tel"]',
                'input[name*="phone"]',
                'input[name*="telefon"]'
            ]
            
            for selector in phone_selectors:
                try:
                    field = await self.page.query_selector(selector)
                    if field and phone:
                        await field.fill(phone)
                        print(f"✅ Filled phone: {selector}")
                except:
                    continue
            
            # Fill cover letter if text area exists
            cover_letter_selectors = [
                'textarea[name*="letter"]',
                'textarea[name*="message"]',
                'textarea[placeholder*="søknad"]'
            ]
            
            for selector in cover_letter_selectors:
                try:
                    field = await self.page.query_selector(selector)
                    if field:
                        cover_text = "Jeg er interessert i denne stillingen og mener jeg har relevante kvalifikasjoner. Jeg ser frem til å høre fra dere."
                        await field.fill(cover_text)
                        print(f"✅ Filled cover letter: {selector}")
                        break
                except:
                    continue
                    
        except Exception as e:
            print(f"⚠️ Form filling error: {e}")

    async def submit_application(self) -> bool:
        """Submit the application."""
        try:
            print("🚀 Submitting application...")
            
            # Look for submit buttons
            submit_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                'text=Send søknad',
                'text=Send',
                'button:has-text("Send")',
                'button:has-text("Søk")'
            ]
            
            for selector in submit_selectors:
                try:
                    submit_button = await self.page.wait_for_selector(selector, timeout=3000)
                    if submit_button:
                        await submit_button.click()
                        await self.page.wait_for_timeout(5000)
                        
                        # Check for success indicators
                        success_indicators = [
                            'text=Søknad sendt',
                            'text=Takk for søknaden',
                            'text=Søknaden er mottatt',
                            '[class*="success"]'
                        ]
                        
                        for indicator in success_indicators:
                            try:
                                success_element = await self.page.wait_for_selector(indicator, timeout=5000)
                                if success_element:
                                    print("✅ Application submitted successfully!")
                                    return True
                            except:
                                continue
                        
                        # If no success indicator, assume success if no error
                        print("✅ Application likely submitted (no error detected)")
                        return True
                        
                except:
                    continue
            
            print("❌ Could not find submit button")
            return False
            
        except Exception as e:
            print(f"❌ Submission error: {e}")
            return False

if __name__ == "__main__":
    # Test the applicator
    print("🧪 NAV Auto-Applicator Test Module")
