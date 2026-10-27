import os
import json
import requests
from bs4 import BeautifulSoup
import gspread
from oauth2client.service_account import ServiceAccountCredentials

def scrape_egp_notices():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
    
    if not creds_json:
        print("Error: GOOGLE_CREDENTIALS_JSON is missing.")
        return

    creds_dict = json.loads(creds_json)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    
    sheet_name = "EGP Notice Automation"
    try:
        spreadsheet = client.open(sheet_name)
    except Exception as e:
        print(f"Error opening spreadsheet: {e}")
        return

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
            try:
                worksheet = spreadsheet.worksheet(dept_code)
            except gspread.exceptions.WorksheetNotFound:
                worksheet = spreadsheet.add_worksheet(title=dept_code, rows="100", cols="10")
                worksheet.append_row(["Tender ID", "Ministry/Organization", "Title / Description", "Publish Date", "Closing Date"])

            params = {"agencyName": dept_code}
            response = requests.get(base_url, headers=headers, params=params, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # শুধুমাত্র টেন্ডার লিস্টের টেবিল বা ডেটা রো খোঁজার জন্য সুনির্দিষ্ট ট্যাগ ফিল্টার
                rows_added = 0
                tables = soup.find_all('table')
                
                for table in tables:
                    # মেনু টেবিলগুলো এড়িয়ে চলার জন্য চেক করা
                    table_text = table.get_text()
                    if "Home Page" in table_text and "View All Notifications" in table_text and len(table.find_all('tr')) < 3:
                        continue
                        
                    rows = table.find_all('tr')
                    for row in rows:
                        cols = [td.get_text(strip=True) for td in row.find_all('td')]
                        # টেন্ডারের সারিগুলোতে সাধারণত একাধিক কলাম এবং সংখ্যাসূচক বা নির্দিষ্ট বড় ডেটা থাকে
                        if len(cols) >= 4:
                            row_string = " ".join(cols).lower()
                            # মেনু বা নেভিগেশন কিওয়ার্ডগুলো বাদ দেওয়া
                            if any(bad_word in row_string for bad_word in ["home page", "etenders", "annual procurement", "advance search", "view all notifications", "sitemap", "contact us"]):
                                continue
                            
                            # অতিরিক্ত ফিল্টার: যদি প্রথম কলামটি খুব ছোট বা ফাকা হয়
                            if cols[0] == "" or len(cols[0]) < 3:
                                continue
                                
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
