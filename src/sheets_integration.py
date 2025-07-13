"""Google Sheets integration for job application tracking."""
import os
import json
from datetime import datetime
from typing import List, Dict, Any
import gspread
from google.oauth2.service_account import Credentials

class SheetsTracker:
    def __init__(self):
        self.setup_sheets_client()
        self.sheet_name = "JobBot Applications"
    
    def setup_sheets_client(self):
        """Setup Google Sheets client."""
        try:
            # Parse credentials from environment variable
            creds_json = json.loads(os.getenv("GOOGLE_CREDENTIALS_JSON"))
            
            # Create credentials object
            credentials = Credentials.from_service_account_info(
                creds_json,
                scopes=[
                    'https://spreadsheets.google.com/feeds',
                    'https://www.googleapis.com/auth/drive'
                ]
            )
            
            self.gc = gspread.authorize(credentials)
            print("✅ Google Sheets client initialized")
            
        except Exception as e:
            print(f"❌ Error setting up Google Sheets: {e}")
            self.gc = None
    
    def create_or_get_sheet(self) -> gspread.Spreadsheet:
        """Create or get the tracking spreadsheet."""
        try:
            # Try to open existing sheet
            try:
                sheet = self.gc.open(self.sheet_name)
                return sheet
            except gspread.SpreadsheetNotFound:
                # Create new sheet
                sheet = self.gc.create(self.sheet_name)
                
                # Setup headers
                worksheet = sheet.sheet1
                headers = [
                    "Date", "Job Title", "Company", "Source", "URL", 
                    "Relevance Score", "Status", "Applied Date", "Notes"
                ]
                worksheet.append_row(headers)
                
                print(f"✅ Created new spreadsheet: {self.sheet_name}")
                return sheet
                
        except Exception as e:
            print(f"❌ Error with spreadsheet: {e}")
            return None
    
    def log_application(self, job_data: Dict[str, Any], status: str = "APPLIED"):
        """Log job application to Google Sheets."""
        if not self.gc:
            return False
        
        try:
            sheet = self.create_or_get_sheet()
            if not sheet:
                return False
            
            worksheet = sheet.sheet1
            
            # Prepare row data
            row = [
                datetime.now().strftime("%Y-%m-%d %H:%M"),
                job_data.get('title', ''),
                job_data.get('company', ''),
                job_data.get('source', ''),
                job_data.get('url', ''),
                job_data.get('relevance_score', ''),
                status,
                datetime.now().strftime("%Y-%m-%d") if status == "APPLIED" else "",
                f"Automated application via JobBot"
            ]
            
            worksheet.append_row(row)
            print(f"✅ Logged to Google Sheets: {job_data.get('title')}")
            return True
            
        except Exception as e:
            print(f"❌ Error logging to sheets: {e}")
            return False
    
    def update_daily_stats(self, stats: Dict[str, int]):
        """Update daily statistics in a separate sheet."""
        if not self.gc:
            return False
        
        try:
            sheet = self.create_or_get_sheet()
            if not sheet:
                return False
            
            # Get or create stats worksheet
            try:
                stats_ws = sheet.worksheet("Daily Stats")
            except gspread.WorksheetNotFound:
                stats_ws = sheet.add_worksheet("Daily Stats", rows=100, cols=10)
                headers = ["Date", "Total Jobs", "Applied", "Pending", "Errors"]
                stats_ws.append_row(headers)
            
            # Add today's stats
            today = datetime.now().strftime("%Y-%m-%d")
            row = [
                today,
                stats.get('total_jobs', 0),
                stats.get('status_applied', 0),
                stats.get('status_new', 0) + stats.get('status_analyzed', 0),
                stats.get('status_error', 0)
            ]
            
            stats_ws.append_row(row)
            print("✅ Updated daily stats in Google Sheets")
            return True
            
        except Exception as e:
            print(f"❌ Error updating stats: {e}")
            return False

if __name__ == "__main__":
    # Test sheets integration
    tracker = SheetsTracker()
    
    test_job = {
        'title': 'Test Developer',
        'company': 'Test AS',
        'source': 'finn.no',
        'url': 'https://example.com/job/123',
        'relevance_score': 85
    }
    
    tracker.log_application(test_job)
