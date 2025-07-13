"""Enhanced Google Sheets integration with AI-generated cover letters."""
import os
import json
from datetime import datetime
from typing import List, Dict, Any
import gspread
from google.oauth2.service_account import Credentials

class EnhancedSheetsTracker:
    def __init__(self):
        self.setup_sheets_client()
        self.sheet_name = "JobBot Applications Enhanced"
    
    def setup_sheets_client(self):
        """Setup Google Sheets client."""
        try:
            creds_json = json.loads(os.getenv("GOOGLE_CREDENTIALS_JSON"))
            credentials = Credentials.from_service_account_info(
                creds_json,
                scopes=[
                    'https://spreadsheets.google.com/feeds',
                    'https://www.googleapis.com/auth/drive'
                ]
            )
            self.gc = gspread.authorize(credentials)
            print("✅ Enhanced Google Sheets client initialized")
        except Exception as e:
            print(f"❌ Error setting up Google Sheets: {e}")
            self.gc = None
    
    def create_or_get_sheet(self) -> gspread.Spreadsheet:
        """Create or get the enhanced tracking spreadsheet."""
        try:
            try:
                sheet = self.gc.open(self.sheet_name)
                return sheet
            except gspread.SpreadsheetNotFound:
                sheet = self.gc.create(self.sheet_name)
                worksheet = sheet.sheet1
                
                # Enhanced headers
                headers = [
                    "Date", "Username", "Job Title", "Company", "Link", 
                    "AI Score", "Cover Letter", "Status", "Site", 
                    "Applied Date", "Response", "Notes"
                ]
                worksheet.append_row(headers)
                
                # Format headers
                worksheet.format('A1:L1', {
                    'backgroundColor': {'red': 0.2, 'green': 0.6, 'blue': 0.9},
                    'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}}
                })
                
                print(f"✅ Created enhanced spreadsheet: {self.sheet_name}")
                return sheet
        except Exception as e:
            print(f"❌ Error with spreadsheet: {e}")
            return None
    
    def log_job_application(self, username: str, job_data: Dict[str, Any], 
                           cover_letter: str = "", status: str = "NEW"):
        """Log job application with AI-generated cover letter."""
        if not self.gc:
            return False
        
        try:
            sheet = self.create_or_get_sheet()
            if not sheet:
                return False
            
            worksheet = sheet.sheet1
            
            # Prepare row data
            row = [
                datetime.now().strftime("%Y-%m-%d %H:%M"),  # Date
                username,                                    # Username
                job_data.get('title', ''),                  # Job Title
                job_data.get('company', ''),                # Company
                job_data.get('url', ''),                    # Link
                job_data.get('relevance_score', 0),         # AI Score
                cover_letter[:200] + "..." if len(cover_letter) > 200 else cover_letter,  # Cover Letter (truncated)
                status,                                      # Status
                job_data.get('source', 'arbeidsplassen'),   # Site
                datetime.now().strftime("%Y-%m-%d") if status == "APPLIED" else "",  # Applied Date
                "",                                          # Response
                f"Auto-generated via JobBot AI"             # Notes
            ]
            
            worksheet.append_row(row)
            print(f"✅ Logged to Enhanced Sheets: {job_data.get('title')} for {username}")
            return True
            
        except Exception as e:
            print(f"❌ Error logging to enhanced sheets: {e}")
            return False
    
    def update_application_status(self, job_url: str, new_status: str, response: str = ""):
        """Update status of existing application."""
        if not self.gc:
            return False
        
        try:
            sheet = self.create_or_get_sheet()
            if not sheet:
                return False
            
            worksheet = sheet.sheet1
            
            # Find row with matching URL
            url_col = 5  # Link column
            all_values = worksheet.get_all_values()
            
            for i, row in enumerate(all_values[1:], start=2):  # Skip header
                if row[url_col-1] == job_url:
                    worksheet.update_cell(i, 8, new_status)  # Status column
                    if response:
                        worksheet.update_cell(i, 11, response)  # Response column
                    worksheet.update_cell(i, 12, f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
                    print(f"✅ Updated status for {job_url}: {new_status}")
                    return True
            
            print(f"⚠️ Job URL not found in sheet: {job_url}")
            return False
            
        except Exception as e:
            print(f"❌ Error updating status: {e}")
            return False

if __name__ == "__main__":
    # Test enhanced sheets
    tracker = EnhancedSheetsTracker()
    
    test_job = {
        'title': 'AI Developer',
        'company': 'Tech AS',
        'source': 'arbeidsplassen',
        'url': 'https://example.com/job/ai-dev',
        'relevance_score': 92
    }
    
    test_cover_letter = "Dear Hiring Manager,\n\nI am writing to express my strong interest in the AI Developer position..."
    
    tracker.log_job_application("vitalii", test_job, test_cover_letter, "APPLIED")
