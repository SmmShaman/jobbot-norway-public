"""Enhanced form filling with better field detection."""
import os
import asyncio
from datetime import datetime
from playwright.async_api import async_playwright

class FormFiller:
    def __init__(self):
        self.fill_delay = 1000  # Increased delay
    
    def prepare_user_data(self, username, job_data):
        """Prepare user data for form filling."""
        try:
            import json
            config_path = f'/app/data/users/{username}/config.json'
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            user_info = config['user_info']
            
            # Find CV file
            cv_files = []
            resumes_dir = f'/app/data/users/{username}/resumes'
            if os.path.exists(resumes_dir):
                for file in os.listdir(resumes_dir):
                    if file.endswith(('.pdf', '.doc', '.docx')):
                        cv_files.append(os.path.join(resumes_dir, file))
            
            # Find cover letter
            cover_letter_text = ''
            letters_dir = f'/app/data/users/{username}/letters'
            if os.path.exists(letters_dir):
                letter_files = [f for f in os.listdir(letters_dir) if f.endswith('.txt')]
                if letter_files:
                    latest_letter = sorted(letter_files)[-1]
                    letter_path = os.path.join(letters_dir, latest_letter)
                    with open(letter_path, 'r', encoding='utf-8') as f:
                        cover_letter_text = f.read()
            
            # Load resume for experience
            try:
                from resume_loader import create_ai_prompt
                resume_text = create_ai_prompt(username)
            except:
                resume_text = 'Experienced professional'
            
            user_data = {
                'first_name': user_info['full_name'].split()[0],
                'last_name': user_info['full_name'].split()[-1],
                'full_name': user_info['full_name'],
                'email': user_info['email'],
                'phone': user_info['phone'],
                'cv_file': cv_files[0] if cv_files else None,
                'cover_letter_text': cover_letter_text,
                'experience': resume_text[:500] if len(resume_text) > 500 else resume_text,
                'skills': 'Python, Project Management, Customer Service',
                'agree_terms': True
            }
            
            return user_data
            
        except Exception as e:
            return {'error': str(e)}
    
    async def smart_fill_field(self, page, field, value):
        """Smart field filling with multiple attempts."""
        selector = field['selector']
        field_type = field['field_type']
        
        try:
            # Wait for element
            await page.wait_for_selector(selector, timeout=5000)
            element = await page.query_selector(selector)
            
            if not element:
                return False
                
            # Check if element is visible
            if not await element.is_visible():
                return False
            
            # Fill based on type
            if field_type == 'file':
                if value and os.path.exists(value):
                    await element.set_input_files(value)
                    return True
                    
            elif field_type == 'checkbox':
                if field['fill_with'] == 'agree_terms' or value:
                    await element.check()
                    return True
                    
            elif field_type in ['text', 'email', 'tel', 'textarea']:
                # Clear field first
                await element.clear()
                await page.wait_for_timeout(500)
                
                # Type slowly
                await element.type(str(value), delay=50)
                await page.wait_for_timeout(500)
                
                # Verify value was entered
                filled_value = await element.input_value() if field_type != 'textarea' else await element.inner_text()
                if str(value).lower() in filled_value.lower():
                    return True
                    
            elif field_type == 'select':
                options = await page.query_selector_all(f'{selector} option')
                if options and len(options) > 1:
                    await element.select_option(index=1)
                    return True
            
            return False
            
        except Exception as e:
            print(f'Error filling field {field.get("label", "unknown")}: {e}')
            return False
    
    async def fill_form_universally(self, employer_url, instructions, user_data, username):
        """Enhanced universal form filling."""
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                await page.goto(employer_url, timeout=30000)
                await page.wait_for_load_state('networkidle')
                
                # Handle cookies again if needed
                cookie_selectors = ['text="Acceptere"', 'text="Accept"', '[id*="cookie"] button']
                for selector in cookie_selectors:
                    try:
                        element = await page.query_selector(selector)
                        if element and await element.is_visible():
                            await element.click()
                            await page.wait_for_timeout(1000)
                            break
                    except:
                        continue
                
                filled_fields = 0
                total_fields = len(instructions.get('form_fields', []))
                
                print(f'Attempting to fill {total_fields} fields...')
                
                # Fill each field with enhanced logic
                for i, field in enumerate(instructions.get('form_fields', [])):
                    fill_with = field['fill_with']
                    value = user_data.get(fill_with, '')
                    
                    if not value and fill_with != 'agree_terms':
                        print(f'Skipping field {field.get("label", "unknown")} - no value')
                        continue
                    
                    print(f'Filling field {i+1}/{total_fields}: {field.get("label", "unknown")}')
                    
                    success = await self.smart_fill_field(page, field, value)
                    if success:
                        filled_fields += 1
                        print(f'✅ Field filled: {field.get("label", "unknown")}')
                    else:
                        print(f'❌ Failed to fill: {field.get("label", "unknown")}')
                    
                    await page.wait_for_timeout(self.fill_delay)
                
                # Take final screenshot
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                screenshot_path = f'/app/data/screenshots/{username}_filled_form_{timestamp}.png'
                await page.screenshot(path=screenshot_path, full_page=True)
                
                print(f'Form filling completed: {filled_fields}/{total_fields} fields filled')
                
                await browser.close()
                
                return {
                    'success': True,
                    'filled_fields': filled_fields,
                    'total_fields': total_fields,
                    'screenshot': screenshot_path,
                    'form_url': employer_url
                }
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
