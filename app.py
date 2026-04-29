import os
import json
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import HTMLResponse
from google.oauth2.credentials import Credentials
import gspread
import requests
from bs4 import BeautifulSoup

app = FastAPI()

# 1. Google Sheets OAuth Setup
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

def get_sheet_client():
    try:
        # Pulls the OAuth JSON from the Cloud Run Environment Variable (mounted from Secret Manager)
        oauth_info = json.loads(os.environ.get("OAUTH_CREDENTIALS_JSON"))
        
        # Build the credentials object using the refresh token
        creds = Credentials(
            token=None, # Set to None so it forces a refresh using the refresh_token
            refresh_token=oauth_info['refresh_token'],
            token_uri=oauth_info.get('token_uri', 'https://oauth2.googleapis.com/token'),
            client_id=oauth_info['client_id'],
            client_secret=oauth_info['client_secret'],
            scopes=SCOPES
        )
        
        return gspread.authorize(creds)
    except Exception as e:
        print(f"Auth Error: {e}")
        raise ValueError("Failed to authenticate. Check your OAuth JSON in Secret Manager.")

# 2. The Core Scraping Logic
def run_scraper_task(expansion: str, sheet_id: str):
    client = get_sheet_client()
    
    # Open the target spreadsheet and get the first tab
    sh = client.open_by_key(sheet_id)
    worksheet = sh.get_worksheet(0) 
    
    url = f"https://en.shadowverse-evolve.com/cards/searchresults/?expansion_name={expansion}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to fetch Shadowverse site. Status code: {response.status_code}")
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
        print("No cards found for this expansion.")
        return

    # Clear and rewrite
    worksheet.clear()
    worksheet.append_row(["Card Number", "Card Name", "Link"])
    worksheet.format('A1:C1', {'textFormat': {'bold': True}})
    worksheet.append_rows(cards_data)
    print(f"Successfully wrote {len(cards_data)} cards to the sheet.")

# 3. Web Endpoints
@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <html>
        <head><title>Shadowverse Scraper</title></head>
        <body style="font-family: Arial; padding: 50px;">
            <h2>Shadowverse Evolve Scraper</h2>
            <form action="/scrape" method="get">
                <label>Expansion Code (e.g., ECP02):</label><br>
                <input type="text" name="expansion" required style="margin-bottom: 15px;"><br>
                <label>Google Sheet ID:</label><br>
                <input type="text" name="sheet_id" required style="margin-bottom: 15px; width: 300px;"><br>
                <button type="submit" style="padding: 10px 20px;">Start Scraping</button>
            </form>
        </body>
    </html>
    """

@app.get("/scrape")
async def trigger_scrape(expansion: str, sheet_id: str, background_tasks: BackgroundTasks):
    if not expansion or not sheet_id:
        raise HTTPException(status_code=400, detail="Missing expansion or sheet_id parameter")
    
    background_tasks.add_task(run_scraper_task, expansion, sheet_id)
    
    return {
        "status": "success", 
        "message": f"Scraping started for {expansion}.",
        "sheet_link": f"https://docs.google.com/spreadsheets/d/{sheet_id}"
    }