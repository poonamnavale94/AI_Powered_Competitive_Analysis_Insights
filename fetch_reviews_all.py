import time
import gspread
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from google.oauth2.service_account import Credentials
from datetime import datetime
import os

# === Google Sheets Setup ===
SHEET_NAME = "webdata_reviews"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", 
          "https://www.googleapis.com/auth/drive"]
key_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")  # ensure your env variable is set

creds = Credentials.from_service_account_file(key_path, scopes=SCOPES)
client = gspread.authorize(creds)
sheet = client.open(SHEET_NAME).sheet1

# === Selenium Setup ===
chrome_options = Options()
chrome_options.add_argument("--headless=new")  # run in headless mode
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")

driver = webdriver.Chrome(options=chrome_options)

# === Helper functions ===
def scrape_ebay_reviews(url):
    driver.get(url)
    time.sleep(3)  # wait for page load
    reviews_data = []

    while True:
        review_blocks = driver.find_elements(By.CSS_SELECTOR, "div.ebay-review-section")
        for block in review_blocks:
            try:
                reviewer = block.find_element(By.CSS_SELECTOR, "a.review-item-author").text
            except:
                reviewer = "Anonymous"
            try:
                rating = block.find_element(By.CSS_SELECTOR, "meta[itemprop='ratingValue']").get_attribute("content")
            except:
                rating = "N/A"
            try:
                review_text = block.find_element(By.CSS_SELECTOR, "p[itemprop='reviewBody']").text
            except:
                review_text = "N/A"
            try:
                review_date = block.find_element(By.CSS_SELECTOR, "span[itemprop='datePublished']").text.strip()
            except:
                review_date = "N/A"

            # Filter 2024 & 2025
            if review_date != "N/A":
                year = int("20" + review_date.split("/")[-1])
                if year not in [2024, 2025]:
                    continue

            product_title = driver.find_element(By.CSS_SELECTOR, "h1").text.strip()

            reviews_data.append([
                "ebay",
                product_title,
                reviewer,
                rating,
                review_text,
                review_date,
                url,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ])

        # check if "Next" button exists
        try:
            next_btn = driver.find_element(By.CSS_SELECTOR, "a[aria-label='Next page']")
            if "disabled" in next_btn.get_attribute("class"):
                break
            next_btn.click()
            time.sleep(2)
        except:
            break

    return reviews_data

def scrape_simple_reviews(url, source_name):
    driver.get(url)
    time.sleep(3)
    reviews_data = []

    # change selector based on site
    review_blocks = driver.find_elements(By.CSS_SELECTOR, ".review")  # generic; adjust per site
    for block in review_blocks:
        try:
            reviewer = block.find_element(By.CSS_SELECTOR, ".reviewer").text
        except:
            reviewer = "Anonymous"
        try:
            review_text = block.find_element(By.CSS_SELECTOR, ".review-text").text
        except:
            review_text = "N/A"
        try:
            review_date = block.find_element(By.CSS_SELECTOR, ".review-date").text.strip()
        except:
            review_date = "N/A"

        # Filter 2024 & 2025
        if review_date != "N/A":
            year = int("20" + review_date.split("/")[-1])
            if year not in [2024, 2025]:
                continue

        product_title = driver.find_element(By.TAG_NAME, "h1").text.strip()

        reviews_data.append([
            source_name,
            product_title,
            reviewer,
            "N/A",  # rating not available
            review_text,
            review_date,
            url,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ])
    return reviews_data

# === Main logic ===
if __name__ == "__main__":
    urls = [
        ("https://www.ebay.com/urw/Philips-1079830-Respironics-OptiChamber-Diamond-Valved-Holding-Chamber/product-reviews/6011379270", "ebay"),
        ("https://justnebulizers.com/products/optichamber-diamond?srsltid=AfmBOoovbTSw0XHLaSiBgYNZxYm8SfrEkh3pUeVAR9uwQHWvHrrA1U8h", "JustNebulizers"),
        ("https://www.vitalitymedical.com/optichamber-asthma-spacer.html?srsltid=AfmBOopE6gSckbE53-5nz6kow4NtG44YXY3u63A1hfYOo4CB3htoYuIY", "VitalityMedical")
    ]

    all_reviews = []
    for link, source_name in urls:
        print(f"🔎 Scraping {source_name} reviews from {link} ...")
        if source_name == "ebay":
            reviews = scrape_ebay_reviews(link)
        else:
            reviews = scrape_simple_reviews(link, source_name)
        all_reviews.extend(reviews)

    if all_reviews:
        sheet.append_rows(all_reviews)
        print(f"✅ Stored {len(all_reviews)} reviews into {SHEET_NAME}")
    else:
        print("⚠️ No 2024/2025 reviews found.")

    driver.quit()
