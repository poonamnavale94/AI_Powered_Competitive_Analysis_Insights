# fetch_scrape_store.py
import os
import time
import requests
from datetime import datetime
from urllib.parse import urlparse
from dotenv import load_dotenv
from bs4 import BeautifulSoup

import gspread
from gspread.exceptions import APIError

# Optional playwright import (only used if installed)
USE_PLAYWRIGHT = False
try:
    if USE_PLAYWRIGHT:
        from playwright.sync_api import sync_playwright
except Exception:
    USE_PLAYWRIGHT = False

# -------------
# Config / ENV
# -------------
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")
GSHEET_NAME = "webdata_summaries"
SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

if not GOOGLE_API_KEY or not GOOGLE_CSE_ID:
    raise RuntimeError("GOOGLE_API_KEY or GOOGLE_CSE_ID missing in .env")

if not SERVICE_ACCOUNT_FILE:
    raise RuntimeError("GOOGLE_APPLICATION_CREDENTIALS missing in .env")

# polite scraping
REQUEST_DELAY = 1.0  # seconds between requests (increase if you see rate limits)
SEARCH_RESULTS_PER_QUERY = 5

# -------------
# Utilities
# -------------
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115 Safari/537.36"
}

def google_cse_search(query, num=5):
    """Return list of items from Google Custom Search API (dicts with title, snippet, link)"""
    params = {
        "key": GOOGLE_API_KEY,
        "cx": GOOGLE_CSE_ID,
        "q": query,
        "num": num
    }
    resp = requests.get("https://www.googleapis.com/customsearch/v1", params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    items = data.get("items", [])
    results = []
    for it in items:
        results.append({
            "title": it.get("title", ""),
            "snippet": it.get("snippet", ""),
            "link": it.get("link", ""),
            "displayLink": it.get("displayLink", "")
        })
    return results

def scrape_requests(url):
    """Fetch page with requests + BeautifulSoup and extract title + main text."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        # Title
        title = (soup.title.string or "").strip() if soup.title else ""

        # Try main/article first
        main = soup.find("main") or soup.find("article")
        paragraphs = []
        if main:
            paragraphs = [p.get_text(separator=" ", strip=True) for p in main.find_all("p")]
        else:
            # fallback selectors
            article = soup.find("article")
            if article:
                paragraphs = [p.get_text(separator=" ", strip=True) for p in article.find_all("p")]
            else:
                # generic fallback: body paragraphs
                body = soup.find("body")
                if body:
                    paragraphs = [p.get_text(separator=" ", strip=True) for p in body.find_all("p")]

        # If that yielded nothing useful, try meta description
        if not paragraphs:
            meta = soup.find("meta", attrs={"name":"description"}) or soup.find("meta", property="og:description")
            meta_text = meta["content"].strip() if meta and meta.get("content") else ""
            if meta_text:
                paragraphs = [meta_text]

        full_text = "\n\n".join([p for p in paragraphs if p])
        return {"title": title, "text": full_text[:20000]}  # limit length to 20k chars
    except Exception as e:
        return {"title": "", "text": "", "error": str(e)}

def scrape_playwright(url):
    """Render page with Playwright if installed (slower but handles JS sites)."""
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=30000)
            page.wait_for_load_state("networkidle", timeout=15000)
            content = page.content()
            browser.close()
        soup = BeautifulSoup(content, "html.parser")
        title = (soup.title.string or "").strip() if soup.title else ""
        paragraphs = [p.get_text(separator=" ", strip=True) for p in soup.find_all("p")]
        full_text = "\n\n".join([p for p in paragraphs if p])
        return {"title": title, "text": full_text[:20000]}
    except Exception as e:
        return {"title": "", "text": "", "error": str(e)}

def scrape_url(url):
    """Try requests first, then Playwright (if available) as fallback if content too small."""
    res = scrape_requests(url)
    if res.get("text") and len(res["text"]) > 200:
        return res, "requests"
    # fallback to Playwright if available
    if USE_PLAYWRIGHT:
        res2 = scrape_playwright(url)
        if res2.get("text") and len(res2["text"]) > 200:
            return res2, "playwright"
        return res2, "playwright_failed"
    return res, "requests_failed"

# -------------
# Google Sheets setup
# -------------
gc = gspread.service_account(filename=SERVICE_ACCOUNT_FILE)
sh = gc.open(GSHEET_NAME)
worksheet = sh.sheet1

# Check header (ensure header exists)
expected_header = ["source", "title", "snippet", "url", "retrieved_at", "additional_info"]
first_row = worksheet.row_values(1)
if not first_row or first_row[0].lower() != "source":
    # optionally set header
    try:
        worksheet.insert_row(expected_header, index=1)
    except APIError:
        pass

# -------------
# Main runner
# -------------
queries = [
    "Philips OptiChamber Diamond product reviews site:ebay.com",
    "Philips OptiChamber Diamond product reviews site:directhomemedical.com",
    "Philips OptiChamber Diamond reviews site:justnebulizers.com",
    "Philips OptiChamber Diamond news site:philips.com OR site:philips.ca OR site:news.google.com"
]

rows_to_append = []

for q in queries:
    print("Searching:", q)
    try:
        items = google_cse_search(q, num=SEARCH_RESULTS_PER_QUERY)
    except Exception as e:
        print("Search error:", e)
        items = []
    for it in items:
        url = it.get("link", "")
        snippet = it.get("snippet", "")
        source = it.get("displayLink") or urlparse(url).netloc
        retrieved_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        print(" -> scraping", url)
        scraped, method = scrape_url(url)
        title = scraped.get("title") or it.get("title") or ""
        full_text = scraped.get("text") or ""
        additional_info = f"scrape_method={method}; text_len={len(full_text)}"
        # If text is empty, indicate why
        if not full_text:
            if scraped.get("error"):
                additional_info += f"; error={scraped.get('error')}"
            else:
                additional_info += "; no_text_found"

        # Build row (store snippet as search snippet; full text stored in additional_info if short)
        # We store only snippet in the `snippet` column to keep sheet readable.
        # If you want the full text stored, you can add it to additional_info or a separate column.
        row = [
            source,
            title,
            snippet,
            url,
            retrieved_at,
            additional_info
        ]
        rows_to_append.append(row)
        time.sleep(REQUEST_DELAY)

# Batch append (do in chunks to avoid gspread rate limits)
BATCH = 50
for i in range(0, len(rows_to_append), BATCH):
    batch = rows_to_append[i:i+BATCH]
    try:
        worksheet.append_rows(batch, value_input_option="RAW")
        print(f"Appended rows {i}..{i+len(batch)-1}")
    except Exception as e:
        print("Failed append chunk:", e)
        # fallback: append one by one
        for r in batch:
            try:
                worksheet.append_row(r)
            except Exception as e2:
                print("append_row error", e2)

print("Done. Total rows appended:", len(rows_to_append))