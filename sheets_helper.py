import gspread
from google.oauth2.service_account import Credentials
import os

def _get_creds():
    cred_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if not cred_path or not os.path.exists(cred_path):
        raise RuntimeError("GOOGLE_APPLICATION_CREDENTIALS not set or file not found.")

    # Explicitly request both Sheets and Drive scopes
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    return Credentials.from_service_account_file(cred_path, scopes=scopes)

# Global gspread client
_gc = gspread.authorize(_get_creds())

def open_ws(spreadsheet_title, worksheet_index=0):
    """Open a Google Spreadsheet by its title and return the first worksheet by default."""
    sh = _gc.open(spreadsheet_title)
    return sh.get_worksheet(worksheet_index)

def ensure_header(ws, header):
    """Make sure the worksheet has the right header row."""
    existing = ws.row_values(1)
    if existing != header:
        ws.delete_rows(1)
        ws.insert_row(header, 1)

def get_existing_values_in_column(ws, col_name):
    """Return all values in a given column by column name."""
    header = ws.row_values(1)
    if col_name not in header:
        return set()
    col_index = header.index(col_name) + 1
    return set(ws.col_values(col_index)[1:])

def append_dicts(ws, rows, columns):
    """Append list of dicts to sheet following given column order."""
    values = [[r.get(c, "") for c in columns] for r in rows]
    ws.append_rows(values, value_input_option="RAW")
    return len(values)