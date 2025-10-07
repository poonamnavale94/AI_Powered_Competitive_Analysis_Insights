# fetch_news.py 
import feedparser
from urllib.parse import quote_plus, urlparse
from datetime import datetime, timedelta
from sheets_helper import open_ws, ensure_header, get_existing_values_in_column, append_dicts

# Your Google Sheet title must be exactly this:
SHEET_TITLE = "news_articles"

# Columns must match your sheet header
COLUMNS = ["published_at", "source", "title", "description", "url", "competitor"]

# Competitor keywords (Canada-focused)
COMPETITOR_KEYWORDS = [
    "Philips OptiChamber Diamond",
    "Philips Respironics spacer",
    "GSK Volumatic spacer",
    "PARI Vortex spacer",
    "Clement Clarke Able Spacer"
]

# Insight-oriented keywords
INSIGHT_KEYWORDS = [
    "launch", "market share", "regulatory", "clinical trial",
    "FDA approval", "patent", "recall", "merger", "acquisition"
]

# Industry context keywords
INDUSTRY_KEYWORDS = [
    "asthma", "respiratory", "inhaler", "spacer", "pulmonary"
]

def build_google_news_rss(keyword: str) -> str:
    query = quote_plus(f"{keyword} Canada")
    return f"https://news.google.com/rss/search?q={query}"

def is_relevant(entry, competitor_keywords, insight_keywords, industry_keywords):
    text = (getattr(entry, "title", "") + " " + getattr(entry, "summary", "")).lower()
    
    # Must match competitor/product keyword
    if not any(c.lower() in text for c in competitor_keywords):
        return False
    
    # Must match insight keyword
    if not any(i.lower() in text for i in insight_keywords):
        return False
    
    # Must match industry context keyword
    if not any(ind.lower() in text for ind in industry_keywords):
        return False
    
    return True

def fetch_news_rows():
    rows = []
    for keyword in COMPETITOR_KEYWORDS:
        url = build_google_news_rss(keyword)
        print(f"Fetching: {url}")
        feed = feedparser.parse(url)

        for entry in feed.entries[:15]:  # cap per keyword
            if not is_relevant(entry, COMPETITOR_KEYWORDS, INSIGHT_KEYWORDS, INDUSTRY_KEYWORDS):
                continue  # Skip irrelevant news

            # published_at
            published_at = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                published_at = datetime(*entry.published_parsed[:6]).isoformat()
            # source from link host
            source = ""
            link = getattr(entry, "link", "")
            if link:
                try:
                    source = urlparse(link).netloc
                except Exception:
                    source = ""

            rows.append({
                "published_at": published_at or "",
                "source": source,
                "title": getattr(entry, "title", ""),
                "description": getattr(entry, "summary", ""),
                "url": link,
                "competitor": keyword
            })
    return rows

def cleanup_old_rows(ws, cutoff_days=250):
    """Remove rows older than cutoff_days (keeps sheet fresh)"""
    cutoff = datetime.utcnow() - timedelta(days=cutoff_days)
    values = ws.get_all_records()

    # Keep only rows with published_at >= cutoff
    keep_rows = []
    for row in values:
        try:
            if row.get("published_at"):
                dt = datetime.fromisoformat(row["published_at"])
                if dt >= cutoff:
                    keep_rows.append(row)
        except Exception:
            keep_rows.append(row)

    # Rewrite sheet: header + kept rows
    ws.clear()
    ws.append_row(COLUMNS)
    for r in keep_rows:
        ws.append_row([r.get(col, "") for col in COLUMNS])

    print(f"🧹 Cleanup done: kept {len(keep_rows)} rows (last {cutoff_days} days).")

def main():
    ws = open_ws(SHEET_TITLE)
    ensure_header(ws, COLUMNS)
    existing_urls = get_existing_values_in_column(ws, "url")

    fetched = fetch_news_rows()
    new_rows = [r for r in fetched if r["url"] and r["url"] not in existing_urls]

    if new_rows:
        added = append_dicts(ws, new_rows, COLUMNS)
        print(f"✅ Added {added} news rows.")
    else:
        print("No new news rows to add.")

    # Run cleanup
    cleanup_old_rows(ws)

if __name__ == "__main__":
    main()