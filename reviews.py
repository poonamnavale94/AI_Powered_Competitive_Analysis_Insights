# reviews.py
import os
import hashlib
import time
import requests
from bs4 import BeautifulSoup
import gspread
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials

# ----------------------
# Setup Google Sheets
# ----------------------
load_dotenv()
google_credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_file(google_credentials_path, scopes=scope)
client = gspread.authorize(creds)

SHEET_NAME = "online_reviews_rating"
sheet = client.open(SHEET_NAME).sheet1

# Add header if first time
if sheet.row_count == 1:
    header = ["review_id", "product_name", "review_title", "review_text", "rating",
              "reviewer_name", "review_date", "retailer", "verified_purchase", "url"]
    sheet.append_row(header)

# ----------------------
# Helper to generate ID
# ----------------------
def gen_id(*args):
    raw = "|".join([str(a) for a in args if a])
    return hashlib.md5(raw.encode()).hexdigest()[:10]

# ----------------------
# eBay Reviews
# ----------------------
def scrape_ebay():
    url = "https://www.ebay.com/urw/Philips-1079830-Respironics-OptiChamber-Diamond-Valved-Holding-Chamber/product-reviews/6011379270"
    resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(resp.text, "html.parser")
    reviews = soup.find_all("div", class_="ebay-review-section")
    rows = []
    for r in reviews:
        title = r.find("h3", class_="review-item-title")
        body = r.find("p", {"itemprop": "reviewBody"})
        rating = r.find("div", class_="ebay-star-rating")
        name = r.find("span", class_="review-item-author")
        date = r.find("span", class_="review-item-date")
        row = [
            gen_id(title, body, name, date),
            "OptiChamber Diamond Spacer",
            title.text.strip() if title else "",
            body.text.strip() if body else "",
            rating.text.strip() if rating else "",
            name.text.strip() if name else "",
            date.text.strip() if date else "",
            "eBay",
            "N/A",
            url
        ]
        rows.append(row)
    return rows

# ----------------------
# Amazon UK Reviews (first page)
# ----------------------
def scrape_amazon_uk():
    url = "https://www.amazon.co.uk/product-reviews/B00BLTBJHC"
    resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(resp.text, "html.parser")
    reviews = soup.find_all("div", {"data-hook": "review"})
    rows = []
    for r in reviews:
        title = r.find("a", {"data-hook": "review-title"})
        body = r.find("span", {"data-hook": "review-body"})
        rating = r.find("i", {"data-hook": "review-star-rating"})
        name = r.find("span", class_="a-profile-name")
        date = r.find("span", {"data-hook": "review-date"})
        verified = "Yes" if r.find("span", {"data-hook": "avp-badge"}) else "No"
        row = [
            gen_id(title, body, name, date),
            "OptiChamber Diamond Spacer",
            title.text.strip() if title else "",
            body.text.strip() if body else "",
            rating.text.strip() if rating else "",
            name.text.strip() if name else "",
            date.text.strip() if date else "",
            "Amazon UK",
            verified,
            url
        ]
        rows.append(row)
    return rows

# ----------------------
# DirectHomeMedical Reviews
# ----------------------
def scrape_directhome():
    url = "https://www.directhomemedical.com/optichamber-diamond-vhc-philips-respironics.html"
    resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(resp.text, "html.parser")
    reviews = soup.find_all("div", class_="jdgm-rev")  # Judge.me widget
    rows = []
    for r in reviews:
        title = r.find("div", class_="jdgm-rev__title")
        body = r.find("div", class_="jdgm-rev__body")
        rating = r.find("span", class_="jdgm-rev__rating")
        name = r.find("span", class_="jdgm-rev__author")
        date = r.find("span", class_="jdgm-rev__timestamp")
        row = [
            gen_id(title, body, name, date),
            "OptiChamber Diamond Spacer",
            title.text.strip() if title else "",
            body.text.strip() if body else "",
            rating.text.strip() if rating else "",
            name.text.strip() if name else "",
            date.text.strip() if date else "",
            "DirectHomeMedical",
            "N/A",
            url
        ]
        rows.append(row)
    return rows

# ----------------------
# RespShop Reviews
# ----------------------
def scrape_respshop():
    url = "https://www.respshop.com/products/optichamber-diamond-valved-holding-chamber-by-philips-respironics"
    resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(resp.text, "html.parser")
    reviews = soup.find_all("div", class_="review")
    rows = []
    for r in reviews:
        title = r.find("div", class_="review-title")
        body = r.find("div", class_="review-text")
        rating = r.find("div", class_="review-rating")
        name = r.find("span", class_="review-author")
        date = r.find("span", class_="review-date")
        row = [
            gen_id(title, body, name, date),
            "OptiChamber Diamond Spacer",
            title.text.strip() if title else "",
            body.text.strip() if body else "",
            rating.text.strip() if rating else "",
            name.text.strip() if name else "",
            date.text.strip() if date else "",
            "RespShop",
            "N/A",
            url
        ]
        rows.append(row)
    return rows

# ----------------------
# JustNebulizers Reviews
# ----------------------
def scrape_justnebulizers():
    url = "https://justnebulizers.com/products/optichamber-diamond"
    resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(resp.text, "html.parser")
    reviews = soup.find_all("div", class_="jdgm-rev")
    rows = []
    for r in reviews:
        title = r.find("div", class_="jdgm-rev__title")
        body = r.find("div", class_="jdgm-rev__body")
        rating = r.find("span", class_="jdgm-rev__rating")
        name = r.find("span", class_="jdgm-rev__author")
        date = r.find("span", class_="jdgm-rev__timestamp")
        row = [
            gen_id(title, body, name, date),
            "OptiChamber Diamond Spacer",
            title.text.strip() if title else "",
            body.text.strip() if body else "",
            rating.text.strip() if rating else "",
            name.text.strip() if name else "",
            date.text.strip() if date else "",
            "JustNebulizers",
            "N/A",
            url
        ]
        rows.append(row)
    return rows

# ----------------------
# Main runner
# ----------------------
all_reviews = []
for scraper in [scrape_ebay, scrape_amazon_uk, scrape_directhome, scrape_respshop, scrape_justnebulizers]:
    try:
        rows = scraper()
        print(f"✅ {scraper.__name__} collected {len(rows)} reviews")
        all_reviews.extend(rows)
        time.sleep(2)  # polite crawl
    except Exception as e:
        print(f"⚠️ Error in {scraper.__name__}: {e}")

# Push to Google Sheet
for row in all_reviews:
    sheet.append_row(row)

print(f"🎉 Done! Inserted {len(all_reviews)} reviews into {SHEET_NAME}")