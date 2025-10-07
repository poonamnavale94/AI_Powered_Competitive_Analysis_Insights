# llm_generate_insights.py

import os
import json
from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials
from openai import OpenAI

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
def fetch_enriched(sheet_name):
    """Fetch enriched data (list of dicts)."""
    try:
        sheet = client.open(sheet_name).sheet1
        return sheet.get_all_records()
    except gspread.SpreadsheetNotFound:
        print(f"⚠️ Sheet {sheet_name} not found.")
        return []

def safe_parse_llm_output(raw_text):
    """Clean LLM output and return as dict."""
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {"executive_summary": cleaned}

def write_insights(sheet_name, llm_json):
    """Write LLM output safely to Google Sheet as JSON string."""
    try:
        sheet = client.open(sheet_name).sheet1
    except gspread.SpreadsheetNotFound:
        sheet = client.create(sheet_name).sheet1

    sheet.clear()
    sheet.append_row(["insights_raw"])
    safe_text = json.dumps(llm_json)
    sheet.append_row([safe_text])

# -----------------------------
# Main logic
# -----------------------------
if __name__ == "__main__":
    enriched_reviews = fetch_enriched(REVIEWS_ENRICHED)
    enriched_reddit = fetch_enriched(REDDIT_ENRICHED)
    enriched_summaries = fetch_enriched(SUMMARIES_ENRICHED)

    all_texts = []
    for dataset in [enriched_reviews, enriched_reddit, enriched_summaries]:
        for row in dataset:
            if "enriched_analysis" in row and row["enriched_analysis"]:
                all_texts.append(row["enriched_analysis"])

    combined_text = "\n".join(all_texts)
    print(f"✅ Combined enriched rows: {len(all_texts)}")

    if combined_text.strip():
        insight_prompt = f"""
You are an AI analyst helping a product team with competitive analysis to make them understand competitor's performance and overall in general user and market insights 
for B2B and B2C audience segment. Remember competitor product is Philips OptiChamber Diamond valved holding chamber, please do not look into any other Philips product and get yourself confused.

Based on the input data (reviews, Reddit posts, summaries), produce structured and actionable insights, since the exsisting data is limited due to stricted scrapping so you are free to add knowledgable and relevant information BUT do not over do it and give false information without cross verifying with source info, in JSON with the following fields:

{{
  "executive_summary": "High-level overview of competitor's perception, competitor activity, and market dynamics.(if possible scan social media about their activity, if they are active and engage but stick to product)",
  "competitor_insights": [
    {{"competitor": "Name of competitor", "strengths": ["List 5 key strengths"], "weaknesses": ["List 5 weaknesses"]}}
  ],
  "recommendations_for_product_manager": ["Top 5 product recommendations with specific details based on competitors product's insights (Philips OptiChamber Diamond valved holding chamber). Specific product development or strategic recommendations based on competitor gaps, opportunities, or user feedback."],
  "recommendations_for_marketing_team": {{
    "campaign_themes": ["Top 5 marketing themes on Themes or narratives that marketing team can use for marketing campaign like newsletter which is based on any specific keyword, user painpoint etc."],
    "keywords": ["Top 5 high-frequency words or phrases, List of high-frequency words, hashtags, or phrases from Reddit or reviews worth leveraging."],
    "Marketing_campaign": ["Top 5 newsletter topics with details"],
    "pain_points": ["Top 5 common frustrations or unmet needs expressed by users that marketing can address in messaging for Asthma Management"],
    "market_gaps": ["Top 5 opportunities, where competitors (Philips OptiChamber Diamond valved holding chamber) is weak or user needs are not being met"]
  }},
  "regulatory_notes": {{
    "FDA": "Relevant FDA approvals or recalls for Philips OptiChamber Diamond, give insights or update from FDA for Philips OptiChamber Diamond valved holding chamber",
    "recalls": "Notable competitor recall issues, we have limited information try to get as much as information from web",
    "approvals": "New treatment approvals to track, we have limited information try to get as much as information from web or social media",
    "regulations": "Compliance reminders, give insights or update on regulation related info for Philips OptiChamber Diamond valved holding chamber"
  }}
}}

Combined enriched data:
{combined_text}
"""
        insight_resp = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": insight_prompt}],
            temperature=0.0,
            max_tokens=1200
        )

        llm_output = insight_resp.choices[0].message.content
        parsed_insights = safe_parse_llm_output(llm_output)
        write_insights(INSIGHTS_SHEET, parsed_insights)
        print(f"✅ LLM Insights written to {INSIGHTS_SHEET}.")
    else:
        print("⚠️ No enriched data found to generate insights.")
