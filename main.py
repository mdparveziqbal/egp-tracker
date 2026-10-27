import os
import json
import requests
from bs4 import BeautifulSoup
import gspread
from oauth2client.service_account import ServiceAccountCredentials

def scrape_egp_notices():
    # Google Credentials Setup
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
    
    if not creds_json:
        print("Error: GOOGLE_CREDENTIALS_JSON is missing.")
        return

    creds_dict = json.loads(creds_json)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    
    # Google Sheet Name
    sheet_name = "EGP Notice Automation"
    try:
        spreadsheet = client.open(sheet_name)
    except Exception as e:
        print(f"Error opening spreadsheet: {e}")
        return

    # Map of Departments
    departments = {
        "PWD": "Public Works Department",
        "EED": "Education Engineering Department",
        "HED": "Health Engineering Department",
        "LGED": "Local Government Engineering Department",
        "RHD": "Roads and Highways Department",
        "DPHE": "Department of Public Health Engineering",
        "BWDB": "Bangladesh Water Development Board"
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }

    base_url = "https://www.eprocure.gov.bd/resources/common/TenderList.jsp"

    for dept_code, dept_fullname in departments.items():
        print(f"Scraping notices for: {dept_code}...")
        try:
            # Check or get worksheet
            try:
                worksheet = spreadsheet.worksheet(dept_code)
            except gspread.exceptions.WorksheetNotFound:
                worksheet = spreadsheet.add_worksheet(title=dept_code, rows="100", cols="10")
                worksheet.append_row(["Tender ID", "Ministry/Organization", "Title / Description", "Publish Date", "Closing Date"])

            params = {"agencyName": dept_code}
            response = requests.get(base_url, headers=headers, params=params, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                tables = soup.find_all('table')
                
                rows_added = 0
                for table in tables:
                    rows = table.find_all('tr')
                    for row in rows:
                        cols = [td.get_text(strip=True) for td in row.find_all('td')]
                        if len(cols) >= 3:
                            first_col = cols[0].lower()
                            # ফিল্টার: মেনু বা হেডার টেক্সট বাদ দিয়ে শুধুমাত্র টেন্ডার আইডি বা প্রাসঙ্গিক সারি নেওয়া
                            if any(keyword in first_col for keyword in ["etenders", "annual", "contracts", "advance", "go to", "search", "organization", "tender id", "home"]):
                                continue
                            
                            # অতিরিক্ত যাচাই: টেন্ডার আইডিতে সংখ্যা বা নির্দিষ্ট ফরম্যাট থাকতে পারে
                            worksheet.append_row(cols[:5])
                            rows_added += 1
                
                if rows_added == 0:
                    print(f"No valid notices found for {dept_code} right now.")
                else:
                    print(f"Added {rows_added} notices to {dept_code} tab.")
            else:
                print(f"Failed to fetch data for {dept_code}, HTTP Status: {response.status_code}")

        except Exception as e:
            print(f"Error processing {dept_code}: {e}")

if __name__ == "__main__":
    scrape_egp_notices()
