# fetch_reviews_selenium_2025.py
import os
from datetime import datetime
from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

# Load env
load_dotenv()

# === Google Sheets Setup ===
SHEET_NAME = "webdata_reviews"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", 
          "https://www.googleapis.com/auth/drive"]

key_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

creds = Credentials.from_service_account_file(key_path, scopes=SCOPES)
client = gspread.authorize(creds)
sheet = client.open(SHEET_NAME).sheet1

# === Selenium Setup ===
chrome_options = Options()
chrome_options.add_argument("--headless")  # Run in headless mode
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(options=chrome_options)

# === Helper function to scrape a page of reviews ===
def scrape_reviews_page():
    reviews_data = []

    review_blocks = driver.find_elements(By.CSS_SELECTOR, "div.ebay-review-section")
    for block in review_blocks:
        try:
            product_title = driver.find_element(By.CSS_SELECTOR, "h1").text.strip()
        except:
            product_title = "N/A"

        try:
            reviewer = block.find_element(By.CSS_SELECTOR, "a.reviewer").text.strip()
        except:
            reviewer = "Anonymous"

        try:
            rating = block.find_element(By.CSS_SELECTOR, "meta[itemprop='ratingValue']").get_attribute("content")
        except:
            rating = "N/A"

        try:
            review_text = block.find_element(By.CSS_SELECTOR, "p[itemprop='reviewBody']").text.strip()
        except:
            review_text = "N/A"

        try:
            review_date = block.find_element(By.CSS_SELECTOR, "span[itemprop='datePublished']").text.strip()
        except:
            review_date = "N/A"

        # Keep only 2025 reviews
        if "2025" in review_date:
            reviews_data.append([
                "ebay",
                product_title,
                reviewer,
                rating,
                review_text,
                review_date,
                driver.current_url,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ])
    return reviews_data

# === Main scraping logic ===
if __name__ == "__main__":
    ebay_urls = [
        "https://www.ebay.com/urw/Philips-1079830-Respironics-OptiChamber-Diamond-Valved-Holding-Chamber/product-reviews/6011379270"
    ]

    all_reviews = []

    for url in ebay_urls:
        print(f"🔎 Scraping reviews from {url} ...")
        driver.get(url)
        wait = WebDriverWait(driver, 10)

        while True:
            # Scrape current page
            reviews = scrape_reviews_page()
            all_reviews.extend(reviews)

            # Try to click "Next" page
            try:
                next_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a[aria-label='Next page']")))
                driver.execute_script("arguments[0].click();", next_btn)
                wait.until(EC.staleness_of(next_btn))  # Wait for page load
            except:
                # No more pages
                break

    driver.quit()

    if all_reviews:
        sheet.append_rows(all_reviews)
        print(f"✅ Stored {len(all_reviews)} 2025 reviews into {SHEET_NAME}")
    else:
        print("⚠️ No 2025 reviews found.")
