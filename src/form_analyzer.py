import os
import json
from openai import AzureOpenAI

class FormAnalyzer:
    def __init__(self):
        self.client = AzureOpenAI(
            azure_endpoint=os.getenv("OPENAI_ENDPOINT"),
            api_key=os.getenv("OPENAI_KEY"),
            api_version="2024-05-01-preview"
        )
    
    async def analyze_form(self, screenshot_path, html_content, job_title, company):
        try:
            # Simple HTML analysis
            has_name_field = "name" in html_content.lower()
            has_email_field = "email" in html_content.lower() or "@" in html_content
            has_phone_field = "phone" in html_content.lower() or "tel" in html_content.lower()
            has_file_field = "file" in html_content.lower() or "upload" in html_content.lower()
            has_textarea = "textarea" in html_content.lower()
            has_checkbox = "checkbox" in html_content.lower()
            
            # Create field list
            fields = []
            
            if has_name_field:
                fields.append({
                    "field_type": "text",
                    "selector": "input[type='text']",
                    "label": "Name",
                    "fill_with": "full_name"
                })
            
            if has_email_field:
                fields.append({
                    "field_type": "email", 
                    "selector": "input[type='email']",
                    "label": "Email",
                    "fill_with": "email"
                })
            
            if has_phone_field:
                fields.append({
                    "field_type": "tel",
                    "selector": "input[type='tel']", 
                    "label": "Phone",
                    "fill_with": "phone"
                })
            
            if has_file_field:
                fields.append({
                    "field_type": "file",
                    "selector": "input[type='file']",
                    "label": "CV Upload",
                    "fill_with": "cv_file"
                })
            
            if has_textarea:
                fields.append({
                    "field_type": "textarea",
                    "selector": "textarea",
                    "label": "Cover Letter", 
                    "fill_with": "cover_letter_text"
                })
            
            if has_checkbox:
                fields.append({
                    "field_type": "checkbox",
                    "selector": "input[type='checkbox']",
                    "label": "Agreement",
                    "fill_with": "agree_terms"
                })
            
            instructions = {
                "form_fields": fields,
                "submit_button": "button[type='submit']",
                "notes": f"Simple analysis found {len(fields)} potential fields"
            }
            
            return {"instructions": instructions, "success": True}
            
        except Exception as e:
            return {"error": str(e), "success": False}
