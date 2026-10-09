import os
import json
import httpx
from pathlib import Path
from typing import List, Dict, Any, Optional
from config import BASE_DIR

SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "15WIJkzbXbs-bj8BLaUBDNE8HwUCF1-Z_0MZmKE18byA")
SHEET_API_KEY = os.getenv("GOOGLE_SHEETS_API_KEY", "AIzaSyBAG2NPhDJpQgYfOamVNgySEuEQtmSP08w")
SERVICE_ACCOUNT_FILE = BASE_DIR / "service_account.json"

def fetch_ready_rows_from_sheets(sheet_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Fetch all rows from Google Sheet where Status == 'Ready' using the Google Sheets API key.
    """
    sid = sheet_id or SHEET_ID
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{sid}/values/Sheet1!A1:I100?key={SHEET_API_KEY}"
    
    response = httpx.get(url, timeout=15.0)
    response.raise_for_status()
    data = response.json()
    
    rows = data.get("values", [])
    if not rows:
        return []
        
    headers = [h.strip() for h in rows[0]]
    ready_tasks = []
    
    for idx, row in enumerate(rows[1:], start=2):
        if not row:
            continue
        # Map row to dictionary based on header names
        row_dict = {headers[i]: row[i] if i < len(row) else "" for i in range(len(headers))}
        row_dict["_row_number"] = idx
        
        status = row_dict.get("Status", "").strip().lower()
        if status == "ready":
            ready_tasks.append(row_dict)
            
    return ready_tasks

def update_sheet_finished_video(row_number: int, video_url: str, sheet_id: Optional[str] = None):
    """
    Updates the Google Sheet cell with Status='Finished' and Finished Video=video_url.
    Uses service_account.json if present.
    """
    sid = sheet_id or SHEET_ID
    if SERVICE_ACCOUNT_FILE.exists():
        import gspread
        gc = gspread.service_account(filename=str(SERVICE_ACCOUNT_FILE))
        sheet = gc.open_by_key(sid).sheet1
        sheet.update_cell(row_number, 8, "Finished")
        sheet.update_cell(row_number, 9, video_url)
        print(f"[Google Sheets] Updated Row {row_number} to Finished in Google Sheets!")
    else:
        print(f"\n[Notice] Google Sheets updated in memory/local DB for row {row_number}.")
        print(f"To automatically write back the 'Finished Video' link to Google Sheets,")
        print(f"download a free 'service_account.json' from Google Cloud Console and place it in the folder.")
