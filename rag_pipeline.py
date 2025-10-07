# fetch_web_to_sheets.py
import os
from datetime import datetime
from dotenv import load_dotenv
import gspread
from langchain_google_community import GoogleSearchAPIWrapper

# 1️⃣ Load environment variables
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")
GOOGLE_SHEET_NAME = "webdata_summaries"
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

if not GOOGLE_API_KEY or not GOOGLE_CSE_ID:
    raise ValueError("❌ GOOGLE_API_KEY or GOOGLE_CSE_ID missing in .env")

# 2️⃣ Authenticate Google Sheets
gc = gspread.service_account(filename=GOOGLE_APPLICATION_CREDENTIALS)
sh = gc.open(GOOGLE_SHEET_NAME)
worksheet = sh.sheet1  # first sheet

# 3️⃣ Setup Google Search via LangChain
search = GoogleSearchAPIWrapper()

# 4️⃣ Define queries
queries = [
    "Philips OptiChamber Diamond product reviews site:ebay.com",
    "Philips OptiChamber Diamond product reviews site:directhomemedical.com",
    "Philips OptiChamber Diamond news OR recalls OR regulatory OR article OR campaign"
]

all_rows = []

# 5️⃣ Fetch results and structure data
for q in queries:
    results = search.results(q, num_results=5)  # top 5 per query
    for r in results:
        row = [
            r.get("source", "web"),          # source
            r.get("title", ""),              # title
            r.get("snippet", r.get("content", "")),  # snippet
            r.get("link", r.get("url", "")), # url
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),  # retrieved_at
            ""                               # additional_info placeholder
        ]
        all_rows.append(row)

# 6️⃣ Append rows to Google Sheet
if all_rows:
    worksheet.append_rows(all_rows)
    print(f"✅ Added {len(all_rows)} rows to {GOOGLE_SHEET_NAME}")
else:
    print("⚠️ No results fetched")