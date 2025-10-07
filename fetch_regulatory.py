import requests
from bs4 import BeautifulSoup
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import re
import os
from dotenv import load_dotenv

# --- Google Sheets Setup ---
load_dotenv()
key_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
if not key_path:
    raise ValueError("❌ GOOGLE_APPLICATION_CREDENTIALS not set in .env")

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(key_path, scope)
gc = gspread.authorize(creds)

sheet_name = "regulatory_updates"
sheet = gc.open(sheet_name).sheet1

# --- Sources & Keywords ---
SOURCES = [
    {"url": "https://recalls-rappels.canada.ca/en", "type": "recall"},
    {"url": "https://health-products.canada.ca/mdall-limh/index-eng.jsp", "type": "approval"},
    {"url": "https://www.canada.ca/en/health-canada/services/drugs-health-products/medeffect-canada.html", "type": "safety_notice"},
]

KEYWORDS = ["recall", "safety", "approval", "licence", "warning", "update", "compliance"]
COMPETITORS = ["Philips OptiChamber", "GSK Volumatic", "PARI Vortex", "AeroChamber Plus"]
ASTHMA_TERMS = ["asthma", "spacer", "valved holding chamber", "nebulizer", "inhaler"]

def fetch_updates():
    updates = []
    for source in SOURCES:
        try:
            response = requests.get(source["url"], timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            text = soup.get_text(separator=" ", strip=True)
            text_lower = text.lower()

            # --- Filter for asthma/competitor + regulatory keywords ---
            device_match = any(c.lower() in text_lower for c in COMPETITORS) or any(t in text_lower for t in ASTHMA_TERMS)
            keyword_match = any(re.search(rf"\b{k.lower()}\b", text_lower) for k in KEYWORDS)

            if device_match and keyword_match:
                updates.append({
                    "source_url": source["url"],
                    "source_type": source["type"],
                    "competitor": next((c for c in COMPETITORS if c.lower() in text_lower), "N/A"),
                    "product": "Asthma Device",
                    "country": "Canada",
                    "raw_text": text[:500],
                    "summarized": "Asthma-related regulatory update detected.",
                    "date": datetime.today().strftime("%Y-%m-%d")
                })

        except Exception as e:
            print(f"Error fetching {source['url']}: {e}")

    return updates

def save_to_gsheet(updates):
    for update in updates:
        row = [
            update["source_url"],
            update["source_type"],
            update["competitor"],
            update["product"],
            update["country"],
            update["raw_text"],
            update["summarized"],
            update["date"]
        ]
        sheet.append_row(row)

if __name__ == "__main__":
    updates = fetch_updates()
    if updates:
        save_to_gsheet(updates)
        print(f"Saved {len(updates)} regulatory updates.")
    else:
        print("No relevant regulatory updates found.")