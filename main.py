import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

def run_egp_scraper():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
    
    if creds_json:
        creds_dict = json.loads(creds_json)
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        
        # আপনার আসল গুগল শীটের নামটি এখানে হুবহু বসাবেন
        sheet_name = "EGP Notice Automation" 
        spreadsheet = client.open(sheet_name)
        
        departments = ["PWD", "EED", "HED", "LGED", "RHD", "DPHE", "BWDB"]
        
        for dept in departments:
            try:
                worksheet = spreadsheet.worksheet(dept)
                print(f"Checking notices for: {dept}")
            except Exception as e:
                print(f"Error for {dept}: {e}")

if __name__ == "__main__":
    run_egp_scraper()
