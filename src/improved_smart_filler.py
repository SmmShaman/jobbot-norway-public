"""Improved form filler using text-based Playwright selectors."""
import os
import asyncio
from playwright.async_api import async_playwright


class ImprovedSmartFiller:
    def __init__(self):
        self.fill_delay = 1000  # ms between fills
    
    async def smart_fill_field(self, page, field, user_data):
        """Smart field filling with multiple Playwright selector strategies."""
        field_type = field['field_type']
        selectors = field['playwright_selectors']
        fill_value = self._get_fill_value(field, user_data)
        
        print(f"🔍 Trying to fill: {field['label']} with value: {fill_value}")
        
        # Try each selector strategy
        for i, selector in enumerate(selectors):
            try:
                print(f"   Strategy {i+1}: {selector}")
                
                # Wait for element with shorter timeout per strategy
                await page.wait_for_selector(selector, timeout=3000)
                
                # Check if element exists and is visible
                element = await page.query_selector(selector)
                if element and await element.is_visible():
                    
                    # Fill based on field type
                    if field_type == 'file':
                        if fill_value and os.path.exists(fill_value):
                            await element.set_input_files(fill_value)
                            print(f"✅ File uploaded: {fill_value}")
                            return True
                    
                    elif field_type == 'checkbox':
                        if not await element.is_checked():
                            await element.click()
                            print(f"✅ Checkbox checked")
                            return True
                    
                    elif field_type in ['text', 'email', 'phone', 'textarea']:
                        await element.clear()
                        await element.fill(fill_value)
                        print(f"✅ Field filled: {fill_value}")
                        return True
                    
                    elif field_type == 'select':
                        await element.select_option(label=fill_value)
                        print(f"✅ Option selected: {fill_value}")
                        return True
                
            except Exception as e:
                print(f"   ❌ Strategy {i+1} failed: {e}")
                continue
        
        print(f"❌ All strategies failed for: {field['label']}")
        return False
    
    async def handle_cookies(self, page, cookies_config):
        """Handle cookie consent with multiple strategies."""
        if not cookies_config.get('found'):
            return True
            
        selectors = cookies_config['playwright_selectors']
        
        for selector in selectors:
            try:
                await page.wait_for_selector(selector, timeout=2000)
                await page.click(selector)
                print(f"✅ Cookies accepted with: {selector}")
                await page.wait_for_timeout(1000)
                return True
            except:
                continue
        
        print("⚠️ Could not handle cookies")
        return False
    
    async def submit_form(self, page, submit_config):
        """Submit form with multiple strategies."""
        selectors = submit_config['playwright_selectors']
        
        for selector in selectors:
            try:
                await page.wait_for_selector(selector, timeout=3000)
                button = await page.query_selector(selector)
                if button and await button.is_visible():
                    await button.click()
                    print(f"✅ Form submitted with: {selector}")
                    return True
            except:
                continue
        
        print("❌ Could not submit form")
        return False
    
    def _get_fill_value(self, field, user_data):
        """Get the value to fill based on field configuration."""
        fill_template = field.get('fill_value', '')
        
        if '{name}' in fill_template:
            return user_data.get('name', 'Vitalii Berbeha')
        elif '{email}' in fill_template:
            return user_data.get('email', 'vitalii@example.com')
        elif '{phone}' in fill_template:
            return user_data.get('phone', '+47 123 45 678')
        else:
            return fill_template


# Test function
async def test_improved_filler():
    """Test the improved form filler."""
    print("🧪 Testing Improved Smart Filler...")
    
    # Mock analysis result from improved analyzer
    analysis = {
        "form_fields": [
            {
                "field_type": "email",
                "label": "Email",
                "playwright_selectors": [
                    "input[type='email']",
                    "input[placeholder*='email']"
                ],
                "fill_value": "{email}",
                "required": True
            }
        ],
        "submit_button": {
            "playwright_selectors": ["text=Submit", "button[type='submit']"]
        },
        "cookies_button": {
            "found": True,
            "playwright_selectors": ["text=Accept"]
        }
    }
    
    user_data = {
        "name": "Vitalii Berbeha",
        "email": "vitalii@example.com",
        "phone": "+47 123 45 678"
    }
    
    filler = ImprovedSmartFiller()
    
    # Test value generation
    for field in analysis['form_fields']:
        value = filler._get_fill_value(field, user_data)
        print(f"📝 {field['label']}: {value}")
    
    print("✅ Test completed!")


if __name__ == "__main__":
    asyncio.run(test_improved_filler())
