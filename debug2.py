import toml
import gspread
from google.oauth2.service_account import Credentials

try:
    secrets = toml.load('.streamlit/secrets.toml')
    creds = Credentials.from_service_account_info(
        secrets['gcp_service_account'], 
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    client = gspread.authorize(creds)
    sheet = client.open_by_url(secrets['google_sheets']['spreadsheet_url'])
    ws = sheet.worksheet('USERS')
    print("=== GOOGLE SHEETS 'USERS' DATA ===")
    print("HEADERS:", ws.row_values(1))
    records = ws.get_all_records()
    print(f"TOTAL ROWS: {len(records)}")
    for i, row in enumerate(records):
        print(f"ROW {i}:", row)
except Exception as e:
    print("ERROR:", e)
