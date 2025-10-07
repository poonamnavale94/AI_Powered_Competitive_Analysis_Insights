# backend/main.py

import os
import json
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import gspread
from google.oauth2.service_account import Credentials

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
if not key_path or not os.path.exists(key_path):
    raise Exception(f"Google service account file not found at {key_path}")

creds = Credentials.from_service_account_file(key_path, scopes=SCOPES)
client = gspread.authorize(creds)

# -----------------------------
# FastAPI setup
# -----------------------------
app = FastAPI()

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://aipoweredcompetativeanalysis.netlify.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Google Sheets info
# -----------------------------
INSIGHTS_SHEET = "llm_insights"

# -----------------------------
# Helper function to fetch insights
# -----------------------------
def fetch_insights():
    try:
        sheet = client.open(INSIGHTS_SHEET).sheet1
        rows = sheet.get_all_records()

        if not rows:
            return {"message": "No insights found in sheet."}
        
        print("🔍 Sample row from Google Sheet:", rows[0])  
        return rows
    except Exception as e:
        return {"error": str(e)}

        # Clean and safely encode any problematic text
        cleaned_rows = []
        for row in rows:
            safe_row = {}
            for key, value in row.items():
                if isinstance(value, str):
                    # Replace newline & escape quotes to avoid invalid JSON
                    value = value.replace("\n", " ").replace("\r", " ").replace('"', "'")
                safe_row[key] = value
            cleaned_rows.append(safe_row)

        # Return JSON-safe structure
        return json.loads(json.dumps(cleaned_rows, ensure_ascii=False))

    except Exception as e:
        return {"error": str(e)}

# -----------------------------
# Root endpoint (for sanity check)
# -----------------------------
@app.get("/")
def root():
    return {"message": "FastAPI backend is running"}

# -----------------------------
# Insights endpoint
# -----------------------------
@app.get("/api/insights")
def get_insights():
    return fetch_insights()
