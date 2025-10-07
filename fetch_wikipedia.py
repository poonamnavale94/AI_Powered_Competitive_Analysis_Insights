# fetch_wikipedia.py

import os
import gspread
import wikipedia
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv

# -------------------------
# Load environment variables
# -------------------------
load_dotenv()  # Make sure your .env is in the same directory

# Google Sheets credentials
key_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
if not key_path:
    raise ValueError("Google service account JSON path not found. Please set GOOGLE_APPLICATION_CREDENTIALS in .env")

gc = gspread.service_account(filename=key_path)
sheet_name = "wikipedia_summaries"
try:
    sheet = gc.open(sheet_name).sheet1
except gspread.SpreadsheetNotFound:
    # If sheet does not exist, create one
    sh = gc.create(sheet_name)
    sheet = sh.sheet1

# -------------------------
# Define competitors and keywords
# -------------------------
competitors = [
    "Philips OptiChamber",
    "GSK Volumatic",
    "PARI Vortex",
    "AeroChamber Plus"
]

keywords = [
    "Health Canada updates",
    "device safety",
    "recalls",
    "licenses",
    "regulations",
    "approval",
    "compliance"
]

# -------------------------
# Calculate 8-month cutoff date
# -------------------------
today = datetime.today()
eight_months_ago = today - timedelta(days=30*8)  # Approximate 8 months

# -------------------------
# Helper function to fetch Wikipedia summary
# -------------------------
def fetch_wiki_summary(keyword):
    try:
        search_results = wikipedia.search(keyword)
        if search_results:
            page_title = search_results[0]  # Take first relevant page
            page = wikipedia.page(page_title)
            summary = page.summary
            last_edit = datetime.strptime(page.lastmod, "%Y-%m-%dT%H:%M:%SZ") if hasattr(page, "lastmod") else today
            return page.title, summary, last_edit
        else:
            print(f"No Wikipedia page found for {keyword}")
            return None, None, None
    except wikipedia.DisambiguationError as e:
        try:
            page = wikipedia.page(e.options[0])
            summary = page.summary
            last_edit = datetime.strptime(page.lastmod, "%Y-%m-%dT%H:%M:%SZ") if hasattr(page, "lastmod") else today
            return page.title, summary, last_edit
        except Exception as inner_e:
            print(f"Error resolving disambiguation for {keyword}: {inner_e}")
            return None, None, None
    except wikipedia.PageError:
        print(f"No Wikipedia page found for {keyword}")
        return None, None, None
    except Exception as e:
        print(f"Error fetching {keyword}: {str(e)}")
        return None, None, None

# -------------------------
# Fetch Wikipedia summaries
# -------------------------
records = []

for comp in competitors:
    title, summary, last_edit = fetch_wiki_summary(comp)
    if summary and last_edit >= eight_months_ago:
        # Check if any of our keywords are in summary (case-insensitive)
        if any(kw.lower() in summary.lower() for kw in keywords):
            record = {
                "page": title,
                "summary": summary,
                "competitor": comp,
                "retrieved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            records.append(record)

# -------------------------
# Save to Google Sheet
# -------------------------
if records:
    df = pd.DataFrame(records)
    sheet.clear()  # Optional: clear previous data
    sheet.update([df.columns.values.tolist()] + df.values.tolist())
    print(f"Updated Google Sheet '{sheet_name}' with {len(records)} records.")
else:
    print("No relevant records found in last 8 months.")