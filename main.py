import os
import json
import datetime
import threading
from flask import Flask, request, jsonify
from google.oauth2.credentials import Credentials
import gspread
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

# --- CONFIGURATION ---
SPREADSHEET_ID = "1MUvlihIOgCCMkX7KZuuhCnNwSVacRWD3SFgfWFOcvKo"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

def get_sheet_client():
    raw_json = os.environ.get("OAUTH_CREDENTIALS_JSON")
    if not raw_json:
        print("ERROR: OAUTH_CREDENTIALS_JSON environment variable is missing!")
        return None
        
    try:
        oauth_info = json.loads(raw_json)
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
        return None

def run_scraper_task(expansion):
    """The actual scraping logic run in a separate thread."""
    print(f"Starting scrape for {expansion}...")
    client = get_sheet_client()
    if not client:
        return

    try:
        sh = client.open_by_key(SPREADSHEET_ID)
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        worksheet = sh.add_worksheet(title=f"{expansion} ({timestamp})", rows="1000", cols="3")
        
        url = f"https://en.shadowverse-evolve.com/cards/searchresults/?expansion_name={expansion}"
        headers = {"User-Agent": "Mozilla/5.0"}
        
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        cards_data = []
        for link in soup.find_all('a', href=True):
            if "cardno=" in link['href']:
                card_no = link['href'].split('cardno=')[1].split('&')[0]
                img = link.find('img')
                name = img.get('title') if img else "Unknown"
                cards_data.append([card_no, name, f"https://en.shadowverse-evolve.com{link['href']}"])

        if cards_data:
            worksheet.append_row(["Card Number", "Card Name", "Link"])
            worksheet.format('A1:C1', {'textFormat': {'bold': True}})
            worksheet.append_rows(cards_data)
            print(f"Success: {len(cards_data)} cards added.")
    except Exception as e:
        print(f"Scraper Task Failed: {e}")

@app.route('/')
def home():
    return f"""
    <html>
        <body style="font-family: sans-serif; padding: 50px;">
            <h2>Shadowverse Scraper (Flask Edition)</h2>
            <p>Target: <code>{SPREADSHEET_ID}</code></p>
            <form action="/scrape" method="get">
                <input type="text" name="expansion" value="ECP02" required>
                <button type="submit">Scrape Now</button>
            </form>
        </body>
    </html>
    """

@app.route('/scrape')
def scrape():
    expansion = request.args.get('expansion')
    if not expansion:
        return "Expansion code missing", 400

    # Start the scraper in a background thread so the HTTP response returns immediately
    thread = threading.Thread(target=run_scraper_task, args=(expansion,))
    thread.start()

    return jsonify({
        "status": "Accepted",
        "message": f"Scraping for {expansion} has started in the background."
    })

if __name__ == "__main__":
    # Cloud Run passes the port via an environment variable
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)