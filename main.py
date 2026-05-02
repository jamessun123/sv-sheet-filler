import sys
import json
import re
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://en.shadowverse-evolve.com"

def find_max_page(soup):
    """Find the maximum number of pages from the HTML."""
    pattern = r'var\smax_page\s*=\s*(\d+);'
    match = re.search(pattern, soup.prettify())
    if match:
        return int(match.group(1))
    else:
        return 1

def get_card_info(card_filter):
    """Get card details from the card page."""
    try:
        response = requests.get(BASE_URL + card_filter, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(response.text, 'html.parser')
        card_info = soup.find('div', class_='txt-Inner')
        if not card_info:
            return {"format": "Unknown", "rarity": "Unknown"}
        
        card_craft = "Unknown"
        card_rarity = "Unknown"
        
        # Find all dt elements that contain the labels
        for dt in card_info.find_all('dt'):
            dt_text = dt.text.strip()
            # Get the next dd element
            dd = dt.find_next('dd')
            if dd:
                if "Class" in dt_text:
                    card_craft = dd.text.strip()
                elif "Rarity" in dt_text:
                    card_rarity = dd.text.strip()
        
        return {
            "format": card_craft,
            "rarity": card_rarity
        }
    except Exception as e:
        return {"format": "Unknown", "rarity": "Unknown"}

def scrape_expansion(expansion):
    """Scrape all normal cards from a specific expansion and return as list of dicts."""
    base_url = f"https://en.shadowverse-evolve.com/cards/searchresults/?expansion_name={expansion}"
    headers = {"User-Agent": "Mozilla/5.0"}

    # Get first page
    response = requests.get(base_url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    max_page = find_max_page(soup)

    cards_data = []
    current_page = 1

    while current_page <= max_page:
        if current_page > 1:
            url = f"{base_url}&page={current_page}"
            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')

        # Parse cards on this page
        for link in soup.find_all('a', href=True):
            if "cardno=" in link['href']:
                card_no = link['href'].split('cardno=')[1].split('&')[0]
                # Filter for normal cards: second part starts with digit or 'T'
                second_part = card_no.split('-')[1]
                if second_part[0].isdigit() or second_part[0] == 'T':
                    img = link.find('img')
                    name = img.get('title') if img else "Unknown"
                    link_url = f"https://en.shadowverse-evolve.com{link['href']}"
                    
                    # Get craft and rarity from individual card page
                    card_filter = link['href']
                    card_details = get_card_info(card_filter)
                    craft = card_details["format"]
                    rarity = card_details["rarity"]
                    
                    cards_data.append({
                        "card_no": card_no,
                        "name": name,
                        "craft": craft,
                        "rarity": rarity,
                        "link": link_url
                    })

        current_page += 1

    return cards_data

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py <expansion_name>")
        sys.exit(1)
    expansion = sys.argv[1]
    cards = scrape_expansion(expansion)
    print(json.dumps(cards, indent=4))