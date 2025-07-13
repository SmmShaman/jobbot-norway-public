"""Improved workflow that handles iframe forms."""
import asyncio
from playwright.async_api import async_playwright
from improved_ai_form_analyzer import ImprovedAIFormAnalyzer
from improved_smart_filler import ImprovedSmartFiller


class IframeFormFiller:
    def __init__(self):
        self.analyzer = ImprovedAIFormAnalyzer()
        self.filler = ImprovedSmartFiller()
    
    async def find_form_iframe(self, page):
        """Find iframe with form fields."""
        frames = page.frames
        print(f"🖼️ Проверяем {len(frames)} фреймов...")
        
        for i, frame in enumerate(frames):
            try:
                frame_url = frame.url
                print(f"   Фрейм {i}: {frame_url[:80]}...")
                
                # Ищем поля в фрейме
                inputs = await frame.query_selector_all('input')
                textareas = await frame.query_selector_all('textarea')
                
                if len(inputs) > 5 or len(textareas) > 0:  # Значимое количество полей
                    print(f"   ✅ ФОРМА НАЙДЕНА в фрейме {i}: Input={len(inputs)}, Textarea={len(textareas)}")
                    return frame
                else:
                    print(f"   ❌ Мало полей в фрейме {i}: Input={len(inputs)}, Textarea={len(textareas)}")
            except Exception as e:
                print(f"   ❌ Ошибка анализа фрейма {i}: {e}")
        
        return None
    
    async def analyze_iframe_form(self, frame):
        """Analyze form fields in iframe."""
        print("\n🔍 АНАЛИЗ ПОЛЕЙ В IFRAME")
        print("-" * 30)
        
        # Получаем все поля
        inputs = await frame.query_selector_all('input')
        textareas = await frame.query_selector_all('textarea')
        selects = await frame.query_selector_all('select')
        
        print(f"📝 Найдено элементов:")
        print(f"   Input: {len(inputs)}")
        print(f"   Textarea: {len(textareas)}")
        print(f"   Select: {len(selects)}")
        
        # Анализируем первые 5 input полей
        print(f"\n📋 АНАЛИЗ ПЕРВЫХ 5 ПОЛЕЙ:")
        for i, input_el in enumerate(inputs[:5]):
            try:
                tag_name = await input_el.evaluate('el => el.tagName')
                input_type = await input_el.get_attribute('type') or 'text'
                placeholder = await input_el.get_attribute('placeholder') or ''
                name = await input_el.get_attribute('name') or ''
                id_attr = await input_el.get_attribute('id') or ''
                
                print(f"   Поле {i+1}: {tag_name} type='{input_type}' name='{name}' id='{id_attr}' placeholder='{placeholder}'")
                
            except Exception as e:
                print(f"   Поле {i+1}: Ошибка анализа - {e}")
        
        return {
            'inputs': inputs,
            'textareas': textareas,
            'selects': selects
        }
    
    async def smart_fill_iframe_field(self, frame, element, field_info, user_data):
        """Fill field in iframe with smart detection."""
        try:
            # Определяем тип поля
            input_type = await element.get_attribute('type') or 'text'
            placeholder = (await element.get_attribute('placeholder') or '').lower()
            name = (await element.get_attribute('name') or '').lower()
            id_attr = (await element.get_attribute('id') or '').lower()
            
            # Объединяем все атрибуты для анализа
            field_text = f"{placeholder} {name} {id_attr}".lower()
            
            print(f"🔍 Анализируем поле: type='{input_type}', text='{field_text[:50]}...'")
            
            # Определяем что заполнять
            if any(keyword in field_text for keyword in ['name', 'navn', 'full']):
                value = user_data.get('name', 'Vitalii Berbeha')
                await element.fill(value)
                print(f"✅ Name заполнено: {value}")
                return True
                
            elif any(keyword in field_text for keyword in ['email', 'e-mail']):
                value = user_data.get('email', 'vitalii.berbeha@example.com')
                await element.fill(value)
                print(f"✅ Email заполнено: {value}")
                return True
                
            elif any(keyword in field_text for keyword in ['phone', 'telefon', 'tlf']):
                value = user_data.get('phone', '+47 123 45 678')
                await element.fill(value)
                print(f"✅ Phone заполнено: {value}")
                return True
                
            elif input_type == 'text' and not field_text.strip():
                # Пустое текстовое поле - пробуем имя
                value = user_data.get('name', 'Vitalii Berbeha')
                await element.fill(value)
                print(f"✅ Общее поле заполнено именем: {value}")
                return True
                
            else:
                print(f"❓ Пропускаем неопознанное поле: {field_text[:30]}...")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка заполнения: {e}")
            return False
    
    async def test_killnoise_application(self):
        """Test complete workflow with iframe handling."""
        print("🚀 ТЕСТИРОВАНИЕ IFRAME WORKFLOW")
        print("=" * 50)
        
        user_data = {
            "name": "Vitalii Berbeha",
            "email": "vitalii.berbeha@example.com", 
            "phone": "+47 123 45 678"
        }
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=['--no-sandbox'])
            page = await browser.new_page()
            
            try:
                print("🔍 Переходим на форму заявки...")
                await page.goto('https://killnoi.se/?dest=application&country=no', timeout=30000)
                await page.wait_for_timeout(8000)  # Ждем загрузки
                
                # Ищем iframe с формой
                form_frame = await self.find_form_iframe(page)
                if not form_frame:
                    print("❌ Iframe с формой не найден!")
                    return
                
                # Анализируем поля в iframe
                form_data = await self.analyze_iframe_form(form_frame)
                
                # Заполняем поля
                print(f"\n📝 ЗАПОЛНЕНИЕ ПОЛЕЙ")
                print("-" * 20)
                
                filled_count = 0
                total_fields = len(form_data['inputs']) + len(form_data['textareas'])
                
                # Заполняем input поля
                for i, input_el in enumerate(form_data['inputs'][:10]):  # Первые 10 полей
                    success = await self.smart_fill_iframe_field(form_frame, input_el, {}, user_data)
                    if success:
                        filled_count += 1
                    await page.wait_for_timeout(500)  # Небольшая пауза
                
                # Заполняем textarea
                for textarea in form_data['textareas']:
                    try:
                        cover_letter = f"Dear KillNoise team,\n\nI am interested in applying for the Python Developer position. I have {user_data['name']} experience in software development.\n\nBest regards,\n{user_data['name']}"
                        await textarea.fill(cover_letter)
                        print(f"✅ Textarea заполнена cover letter")
                        filled_count += 1
                    except:
                        pass
                
                # Финальный скриншот
                await page.screenshot(path='/app/data/screenshots/iframe_filled_form.png', full_page=True)
                
                print(f"\n📊 РЕЗУЛЬТАТ")
                print("-" * 15)
                print(f"✅ Заполнено полей: {filled_count}")
                print(f"📝 Всего полей: {total_fields}")
                print(f"📈 Успешность: {(filled_count/total_fields)*100:.1f}%")
                print(f"📸 Скриншот: iframe_filled_form.png")
                
                print(f"\n⚠️ Форма НЕ отправлена (только тестирование)")
                
            except Exception as e:
                print(f"❌ Ошибка: {e}")
                await page.screenshot(path='/app/data/screenshots/iframe_error.png')
            
            finally:
                await browser.close()


async def main():
    filler = IframeFormFiller()
    await filler.test_killnoise_application()


if __name__ == "__main__":
    asyncio.run(main())
