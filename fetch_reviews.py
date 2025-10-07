import requests
from bs4 import BeautifulSoup
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# === Google Sheets Setup ===
SHEET_NAME = "webdata_reviews"  # your Google Sheet name

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

key_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

creds = Credentials.from_service_account_file(key_path, scopes=SCOPES)
client = gspread.authorize(creds)
sheet = client.open(SHEET_NAME).sheet1

# === Helper function to scrape reviews from an eBay product reviews page ===
def scrape_ebay_reviews(url):
    reviews_data = []

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/117.0 Safari/537.36"
    }

    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        print(f"❌ Failed to fetch {url}")
        return reviews_data

    soup = BeautifulSoup(resp.text, "html.parser")

    # --- Extract product title ---
    product_title = soup.find("h1")
    product_title = product_title.get_text(strip=True) if product_title else "N/A"

    # --- Extract all reviews ---
    review_blocks = soup.find_all("div", {"class": "ebay-review-section"})
    for block in review_blocks:
        reviewer = block.find("a", {"class": "reviewer"}).get_text(strip=True) if block.find("a", {"class": "reviewer"}) else "Anonymous"
        rating = block.find("meta", {"itemprop": "ratingValue"})
        rating = rating["content"] if rating else "N/A"
        review_text = block.find("p", {"itemprop": "reviewBody"})
        review_text = review_text.get_text(strip=True) if review_text else "N/A"
        review_date = block.find("span", {"itemprop": "datePublished"})
        review_date = review_date.get_text(strip=True) if review_date else "N/A"

        reviews_data.append([
            "ebay",  # source
            product_title,
            reviewer,
            rating,
            review_text,
            review_date,
            url,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ])

    return reviews_data


# === Main logic ===
if __name__ == "__main__":
    # Example eBay product review page (replace with your actual links)
    ebay_urls = [
        "https://www.ebay.com/urw/Philips-1079830-Respironics-OptiChamber-Diamond-Valved-Holding-Chamber/product-reviews/6011379270"
    ]

    all_reviews = []
    for link in ebay_urls:
        print(f"🔎 Scraping reviews from {link} ...")
        reviews = scrape_ebay_reviews(link)
        all_reviews.extend(reviews)

    if all_reviews:
        sheet.append_rows(all_reviews)
        print(f"✅ Stored {len(all_reviews)} reviews into {SHEET_NAME}")
    else:
        print("⚠️ No reviews found.")
