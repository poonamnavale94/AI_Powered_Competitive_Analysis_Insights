import os
from dotenv import load_dotenv
import praw
from datetime import datetime, timedelta, timezone
from sheets_helper import open_ws

# -------------------------------
# Load environment variables
# -------------------------------
load_dotenv()
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT")

# -------------------------------
# Keywords for Competitive Analysis
# -------------------------------
KEYWORDS = [
    # Devices / Brand Names
    "Philips OptiChamber Diamond", "Philips Respironics spacer", "GSK Volumatic spacer",
    "PARI Vortex spacer", "Clement Clarke Able Spacer", "Omron asthma spacer",
    "Inspire Medical spacer", "BD AeroChamber", "philips optichamber",
    "philips optichamber diamond", "gsk volumatic", "gsk volumatic spacer",
    "teva aerochamber", "teva aerochamber plus", "omron inhaler spacer",
    "beclometasone inhaler", "aerochamber plus", "optichamber diamond",
    "volumatic spacer",

    # Symptoms / Triggers
    "shortness of breath", "wheezing", "lung pain", "phlegm", "mucus",
    "cough", "coughing fits", "chest tightness", "dry air", "upper respiratory infection",
    "allergic rhinitis", "occupational asthma", "allergy induced asthma",
    "eosinophils", "respiratory infection",

    # Medications
    "Symbicort", "Breo", "Flovent", "Pulmicort", "Advair",
    "Singulair", "montelukast", "biologics", "immunotherapy",
    "allergy shots", "rescue inhaler", "preventer inhaler",
    "controller inhaler", "steroid inhaler", "alternative inhaler",

    # Measurements
    "peak flow", "PEF", "FEV1",

    # Treatment / Management
    "cardio respiratory exercise", "breathing exercises", "DAO supplements",
    "inhaler overuse", "too many puffs", "spacer comfort",
    "device cleaning problems",

    # Lifestyle / Environment
    "smoking", "job not understanding", "exercise induced asthma",
    "organic mattress", "cleaning issues", "mold", "dust",
    "new paint", "fumes", "apartment", "anxiety with asthma",

    # General Concerns
    "cured asthma", "permanent lung damage", "side effects",
    "asthma flare up", "frequent episodes", "asthma scale",
    "quality of life", "cost", "can’t afford medication",
    "market share", "competitor update", "product comparison",
    "asthma device review",

    # Generic / Forum
    "asthma spacer experience", "spacer recommendation", "best inhaler chamber",
    "asthma", "copd", "respiratory therapy", "breathing issues", "lung health"
]

# -------------------------------
# Subreddits to fetch from
# -------------------------------
SUBREDDITS = [
    "asthma", "Canada", "Health", "inhaler", "spacer", "respiratory",
    "medicaldevices", "ChronicIllness", "pharmacy"
]

# -------------------------------
# Initialize Reddit API
# -------------------------------
reddit = praw.Reddit(
    client_id=REDDIT_CLIENT_ID,
    client_secret=REDDIT_CLIENT_SECRET,
    user_agent=REDDIT_USER_AGENT,
)

# -------------------------------
# Connect to Google Sheet
# -------------------------------
SPREADSHEET_NAME = "reddit_discussions"
sheet = open_ws(SPREADSHEET_NAME)

# -------------------------------
# Helper: Check if post/comment matches any keywords
# -------------------------------
def matches_keywords(text):
    text_lower = text.lower()
    for kw in KEYWORDS:
        if kw.lower() in text_lower:
            return kw
    return None

# -------------------------------
# Fetch Reddit posts
# -------------------------------
rows_to_add = []

for subreddit_name in SUBREDDITS:
    try:
        subreddit = reddit.subreddit(subreddit_name)
        for submission in subreddit.new(limit=50):
            post_date = datetime.fromtimestamp(submission.created_utc, tz=timezone.utc)
            if post_date < datetime.now(timezone.utc) - timedelta(days=280):
                continue

            matched_keyword = matches_keywords(submission.title + " " + submission.selftext)
            if matched_keyword:
                # Post text (truncate to 250 chars if long)
                post_text = submission.selftext.strip()
                if post_text:
                    post_text = post_text[:250] + ("..." if len(post_text) > 250 else "")
                else:
                    post_text = ""

                # -------------------------------
                # Fetch relevant comments based on keywords
                # -------------------------------
                relevant_comments = []
                try:
                    submission.comment_sort = "top"   # sort by top votes
                    submission.comments.replace_more(limit=None)  # fetch all comments
                    
                    for comment in submission.comments.list():
                        if len(relevant_comments) >= 100:
                            break
                        comment_body = comment.body.strip()
                        if matches_keywords(comment_body):
                            relevant_comments.append(comment_body)

                    # Combine relevant comments into single string (truncate each comment to 250 chars)
                    combined_comments = " || ".join(
                        c[:250] + ("..." if len(c) > 250 else "") for c in relevant_comments
                    )
                except Exception as e:
                    print(f"Error fetching comments for {submission.id}: {e}")
                    combined_comments = ""

                row = [
                    post_date.strftime("%Y-%m-%d %H:%M:%S"),  # Date
                    subreddit_name,                          # Subreddit
                    submission.title,                        # Title
                    post_text,                               # Text (truncated body)
                    submission.url,                          # URL
                    matched_keyword,                         # Keyword
                    combined_comments                         # Relevant Comments
                ]
                rows_to_add.append(row)
    except Exception as e:
        print(f"Error fetching from subreddit '{subreddit_name}': {e}")

# -------------------------------
# Write to Google Sheet in batch
# -------------------------------
if rows_to_add:
    try:
        sheet.append_rows(rows_to_add, value_input_option="USER_ENTERED")
        print(f"Added {len(rows_to_add)} new posts to the sheet.")
    except Exception as e:
        print(f"Error writing to Google Sheet: {e}")
else:
    print("No new posts found for your keywords.")

# -------------------------------
# Cleanup old rows (older than 399 days)
# -------------------------------
all_rows = sheet.get_all_records()
cutoff = datetime.now(timezone.utc) - timedelta(days=399)
rows_to_delete = []

for i, row in enumerate(all_rows, start=2):  # start=2 because first row is header
    row_date = datetime.strptime(row['Date'], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    if row_date < cutoff:
        rows_to_delete.append(i)

for idx in reversed(rows_to_delete):
    sheet.delete_rows(idx)

print(f"Cleaned up {len(rows_to_delete)} old rows.")