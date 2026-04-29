import os
import json
import datetime
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import HTMLResponse
from google.oauth2.credentials import Credentials
import gspread
import requests
from bs4 import BeautifulSoup

app = FastAPI()

# --- CONFIGURATION ---
# The specific Spreadsheet ID you provided
SPREADSHEET_ID = "1MUvlihIOgCCMkX7KZuuhCnNwSVacRWD3SFgfWFOcvKo"
# Scopes for Google Sheets and Drive access
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

def get_sheet_client():
    try:
        # Pulls the OAuth JSON from the Cloud Run Environment Variable
        oauth_info = json.loads(os.environ.get("OAUTH_CREDENTIALS_JSON"))
        
        creds = Credentials(
            token=None,
            refresh_token=oauth_info['refresh_token'],
            token_uri=oauth_info.get('token_uri', 'https://oauth2.googleapis.com/token'),
            client_id=oauth_info['client_id'],
            client_secret=oauth_info['client_secret'],
            scopes=SCOPES
        )
        return gspread.authorize(creds)
    except Exception as e:
        print(f"Auth Error: {e}")
        raise ValueError("Failed to authenticate. Ensure OAUTH_CREDENTIALS_JSON is set in Secret Manager.")

def run_scraper_task(expansion: str):
    client = get_sheet_client()
    
    # Open the hardcoded spreadsheet
    sh = client.open_by_key(SPREADSHEET_ID)
    
    # Create a unique title for the new worksheet
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    worksheet_title = f"{expansion} ({timestamp})"
    
    # Create the new worksheet
    worksheet = sh.add_worksheet(title=worksheet_title, rows="1000", cols="3")
    
    url = f"https://en.shadowverse-evolve.com/cards/searchresults/?expansion_name={expansion}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Fetch failed for {expansion}. Status: {response.status_code}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    cards_data = []
    
    for link in soup.find_all('a', href=True):
        if "cardno=" in link['href']:
            card_no = link['href'].split('cardno=')[1].split('&')[0]
            img = link.find('img')
            name = img.get('title') if img else "Unknown"
            full_link = f"https://en.shadowverse-evolve.com{link['href']}"
            cards_data.append([card_no, name, full_link])

    if not cards_data:
        print(f"No cards found for expansion: {expansion}")
        return

    # Write headers and format
    worksheet.append_row(["Card Number", "Card Name", "Link"])
    worksheet.format('A1:C1', {'textFormat': {'bold': True}})
    
    # Upload data
    worksheet.append_rows(cards_data)
    print(f"Task Complete: Created '{worksheet_title}' with {len(cards_data)} rows.")

@app.get("/", response_class=HTMLResponse)
def home():
    return f"""
    <html>
        <head><title>Shadowverse Scraper</title></head>
        <body style="font-family: sans-serif; padding: 50px; background-color: #f0f2f5;">
            <div style="max-width: 450px; margin: auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
                <h2 style="color: #1a73e8; margin-top: 0;">Shadowverse Scraper</h2>
                <p style="color: #5f6368;">Target Spreadsheet:<br><b>{SPREADSHEET_ID}</b></p>
                <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
                <form action="/scrape" method="get">
                    <label style="font-weight: bold; display: block; margin-bottom: 8px;">Expansion Code:</label>
                    <input type="text" name="expansion" value="ECP02" required style="width: 100%; padding: 10px; border: 1px solid #dadce0; border-radius: 4px; box-sizing: border-box; margin-bottom: 20px;">
                    <button type="submit" style="width: 100%; background-color: #1a73e8; color: white; padding: 12px; border: none; border-radius: 4px; font-weight: bold; cursor: pointer;">Generate New Tab</button>
                </form>
            </div>
        </body>
    </html>
    """

@app.get("/scrape")
async def trigger_scrape(expansion: str, background_tasks: BackgroundTasks):
    if not expansion:
        raise HTTPException(status_code=400, detail="Expansion code is required")
    
    background_tasks.add_task(run_scraper_task, expansion)
    return {{
        "status": "Accepted",
        "message": f"Scraping started for {expansion}. A new tab will appear in the spreadsheet shortly.",
        "spreadsheet_id": SPREADSHEET_ID
    }}