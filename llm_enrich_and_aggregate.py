# llm_enrich_and_aggregate.py

import os
from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials
from openai import OpenAI
import time
import pandas as pd
import json

# -----------------------------
# Load environment variables
# -----------------------------
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise Exception("OPENAI_API_KEY not found in .env")
print("OPENAI_API_KEY found: True")

# -----------------------------
# Google Sheets scopes and auth
# -----------------------------
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

key_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
creds = Credentials.from_service_account_file(key_path, scopes=SCOPES)
client = gspread.authorize(creds)

# -----------------------------
# Sheets info
# -----------------------------
REVIEWS_SHEET = "webdata_reviews"
REDDIT_SHEET = "reddit_discussions"
SUMMARIES_SHEET = "webdata_summaries"

REVIEWS_ENRICHED = "webdata_reviews_enriched"
REDDIT_ENRICHED = "reddit_discussions_enriched"
SUMMARIES_ENRICHED = "webdata_summaries_enriched"
INSIGHTS_SHEET = "llm_insights"

# -----------------------------
# OpenAI client
# -----------------------------
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# -----------------------------
# Helper functions
# -----------------------------
def fetch_sheet_data(sheet_name, limit=None):
    try:
        sheet = client.open(sheet_name).sheet1
    except gspread.SpreadsheetNotFound:
        raise Exception(f"Spreadsheet {sheet_name} not found. Create it manually and share with service account.")
    data = sheet.get_all_records()
    if limit:
        return data[:limit]
    return data

def fetch_existing_enriched(sheet_name):
    """Return list of already enriched row keys to skip"""
    try:
        sheet = client.open(sheet_name).sheet1
        data = sheet.get_all_records()
        if data:
            return set([json.dumps(r, sort_keys=True) for r in data])
        return set()
    except gspread.SpreadsheetNotFound:
        return set()

def write_enriched(sheet_name, data, headers, batch_size=10):
    """Write enriched data in batches"""
    try:
        sheet = client.open(sheet_name).sheet1
    except gspread.SpreadsheetNotFound:
        sheet = client.create(sheet_name).sheet1
        sheet.append_row(headers)

    # Convert list of dicts to list of lists
    rows = [[row.get(h, "") for h in headers] for row in data]

    # Batch append
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i + batch_size]
        sheet.append_rows(batch, value_input_option="RAW")

def write_insights(sheet_name, insight_json):
    try:
        sheet = client.open(sheet_name).sheet1
    except gspread.SpreadsheetNotFound:
        sheet = client.create(sheet_name).sheet1
    sheet.clear()
    sheet.append_row(list(insight_json.keys()))
    sheet.append_row(list(insight_json.values()))

def enrich_with_llm(record, source_type):
    """Enrich a single row with LLM"""
    prompt = f"""
You are an AI product analyst. Analyze the following {source_type} data and extract actionable insights for a Product Manager for their own product(AEROCHAMBER PLUS* FLOW-VU* Chamber) based on competitor product (Philips Respironics OptiChamber Diamond Spacer) .
Return JSON with:
- sentiment (positive/negative/neutral)
- common_pains
- common_praises
- feature_gaps
- competitor_mentions
- opportunities
- recommendations
- regulatory_notes (FDA, recalls, approvals, regulations)
Raw data:
{record}
JSON output only.
"""
    resp = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"user", "content": prompt}],
        temperature=0.0,
        max_tokens=500
    )
    enriched = resp.choices[0].message.content
    return {**record, "enriched_analysis": enriched}

# -----------------------------
# Main enrichment logic
# -----------------------------
if __name__ == "__main__":
    LIMIT = None  # for testing, set small number like 5

    # Fetch raw Reddit data
raw_reddit = fetch_sheet_data(REDDIT_SHEET, limit=LIMIT)

# Deduplicate by Title
import pandas as pd
df_reddit = pd.DataFrame(raw_reddit).drop_duplicates(subset=['Title'])
raw_reddit = df_reddit.to_dict(orient='records')
print(f"✅ Deduplicated Reddit posts. Remaining rows: {len(raw_reddit)}")
    # ---------- Reviews ----------
raw_reviews = fetch_sheet_data(REVIEWS_SHEET, limit=LIMIT)
existing_reviews = fetch_existing_enriched(REVIEWS_ENRICHED)
    # Skip already enriched
reviews_to_enrich = [r for r in raw_reviews if json.dumps(r, sort_keys=True) not in existing_reviews]
enriched_reviews = [enrich_with_llm(r, "review") for r in reviews_to_enrich]
if enriched_reviews:
        write_enriched(REVIEWS_ENRICHED, enriched_reviews, list(raw_reviews[0].keys()) + ["enriched_analysis"])
print(f"✅ Enrichment complete for {len(enriched_reviews)} review rows.")

    # ---------- Reddit ----------
     # Deduplicate Reddit posts based on Title only
import pandas as pd

df_reddit = pd.DataFrame(raw_reddit).drop_duplicates(subset=['Title'])
raw_reddit = df_reddit.to_dict(orient='records')

print(f"✅ Deduplicated Reddit posts. Remaining rows: {len(raw_reddit)}")

raw_reddit = fetch_sheet_data(REDDIT_SHEET, limit=LIMIT)
    # Deduplicate based on Title + Text
df_reddit = pd.DataFrame(raw_reddit).drop_duplicates(subset=['Title'])
raw_reddit = df_reddit.to_dict(orient='records')
existing_reddit = fetch_existing_enriched(REDDIT_ENRICHED)
reddit_to_enrich = [r for r in raw_reddit if json.dumps(r, sort_keys=True) not in existing_reddit]
enriched_reddit = [enrich_with_llm(r, "reddit") for r in reddit_to_enrich]
if enriched_reddit:
        write_enriched(REDDIT_ENRICHED, enriched_reddit, list(raw_reddit[0].keys()) + ["enriched_analysis"])
print(f"✅ Enrichment complete for {len(enriched_reddit)} reddit rows.")

    # ---------- Summaries ----------
raw_summaries = fetch_sheet_data(SUMMARIES_SHEET, limit=LIMIT)
existing_summaries = fetch_existing_enriched(SUMMARIES_ENRICHED)
summaries_to_enrich = [r for r in raw_summaries if json.dumps(r, sort_keys=True) not in existing_summaries]
enriched_summaries = [enrich_with_llm(r, "summary") for r in summaries_to_enrich]
if enriched_summaries:
        write_enriched(SUMMARIES_ENRICHED, enriched_summaries, list(raw_summaries[0].keys()) + ["enriched_analysis"])
print(f"✅ Enrichment complete for {len(enriched_summaries)} summary rows.")

    # ---------- Generate executive LLM Insights ----------
all_enriched_text = "\n".join([
        r["enriched_analysis"] for r in (enriched_reviews + enriched_reddit + enriched_summaries)
    ])
if all_enriched_text.strip():
        insight_prompt = f"""
You are an AI analyst helping a product team understand user and market insights for B2B and B2C market. Remember competitor product is Philips OptiChamber Diamond valved holding chamber.

Based on the input data (reviews, Reddit posts, summaries), produce structured insights in JSON with the following fields:

{
  "executive_summary": "High-level overview of product competitor perception, competitor activity, and market dynamics.",
  "competitor_insights": [
    {
      "competitor": "Name of competitor",
      "strengths": ["List of key strengths users mention"],
      "weaknesses": ["List of weaknesses or complaints users mention"]
    }
  ],
  "recommendations_for_our product manager for our product (Trudell medical internaltional AEROCHAMBER PLUS* FLOW-VU* Chamber)": [
    "Specific product development or strategic recommendations based on competitor gaps, opportunities, or user feedback."
  ],
  "recommendations_for_marketing team": {
    "campaign_themes": [
      "Themes or narratives marketing can use (e.g., durability, portability, affordability)any specific keyword, user painpoint etc."
    ],
    "keywords": [
      "List of high-frequency words, hashtags, or phrases from Reddit or reviews worth leveraging."
    ],
    "pain_points": [
      "Common frustrations or unmet needs expressed by users that marketing can address in messaging for Asthma Management,Bronchiectasis,COPD,Cystic Fibrosis,Inhaler."
    ],
    "market_gaps": [
      "Opportunities where competitors (Philips OptiChamber Diamond valved holding chamber) is weak or user needs aren’t being met."
    ]
  },
  "regulatory_notes": {
    "FDA": "Any relevant FDA approvals or recalls to monitor of competitor (Philips OptiChamber Diamond valved holding chamber)",
    "recalls": "Notable competitor recall issues",
    "approvals": "New treatment approvals to track of competitor (Philips OptiChamber Diamond valved holding chamber)",
    "regulations": "General compliance reminders of competitor (Philips OptiChamber Diamond valved holding chamber)"
  }
}

Ensure the JSON is valid and complete. Be concise but actionable.
Return JSON only.
Combined enriched data:
{all_enriched_text}
"""
        insight_resp = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role":"user","content": insight_prompt}],
            temperature=0.0,
            max_tokens=500
        )
        llm_insights = insight_resp.choices[0].message.content
        try:
            llm_insights_json = json.loads(llm_insights)
        except:
            llm_insights_json = {"insights_raw": llm_insights}
        write_insights(INSIGHTS_SHEET, llm_insights_json)
        print(f"✅ LLM Insights written to {INSIGHTS_SHEET}.")
