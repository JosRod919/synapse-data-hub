import gspread
from google.oauth2.service_account import Credentials

def setup_google_sheet(credentials_file, sheet_url):
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    try:
        creds = Credentials.from_service_account_file(credentials_file, scopes=scopes)
        client = gspread.authorize(creds)
        sheet = client.open_by_url(sheet_url)
    except Exception as e:
        print(f"Error de conexión: {e}")
        return
    
    tables = {
        "USERS": ["USER_ID", "EMAIL", "FULL_NAME", "ROLE", "POSITION", "IS_ACTIVE", "WEEKLY_HOURS"],
        "BRANDS": ["BRAND_ID", "BRAND_NAME", "IS_ACTIVE"],
        "REQUEST_TYPES": ["TYPE_ID", "TYPE_NAME", "IS_ACTIVE"],
        "REQUESTS": ["REQUEST_ID", "TITLE", "REQUESTER_EMAIL", "BRAND_ID", "REQUEST_TYPE", "BUSINESS_CONTEXT", "EXPECTED_KPIS", "DATA_USAGE", "DEADLINE", "EFFORT_LEVEL", "SLA_EXPECTED", "RICE_REACH", "RICE_IMPACT", "RICE_CONFIDENCE", "RICE_EFFORT", "PRIORITY_SCORE", "TOTAL_ESTIMATED_HOURS", "STATUS", "ASSIGNED_TO", "COMPLETED_AT", "UPDATED_AT"],
        "WEEKLY_ASSIGNMENTS": ["ASSIGNMENT_ID", "REQUEST_ID", "USER_ID", "WEEK_START", "HOURS_ASSIGNED", "HOURS_MON", "HOURS_TUE", "HOURS_WED", "HOURS_THU", "HOURS_FRI", "CREATED_BY", "NOTES", "ADJUSTMENT_NOTES"],
        "TASK_REVIEWS": ["REVIEW_ID", "REQUEST_ID", "REVIEWED_BY", "PROGRESS_PERCENT", "STATUS", "BLOCKER_TYPE", "BLOCKER_DESCRIPTION", "ACTION_TAKEN", "HOURS_LOST", "NOTES", "REVIEW_DATE"]
    }
    
    print(f"Conectado a: {sheet.title}")
    
    for name, headers in tables.items():
        try:
            ws = sheet.worksheet(name)
            print(f"La hoja '{name}' ya existe. Verificando encabezados...")
            if not ws.row_values(1):
                ws.append_row(headers)
                print(f" -> Encabezados agregados a '{name}'.")
        except gspread.exceptions.WorksheetNotFound:
            print(f"Creando hoja '{name}'...")
            ws = sheet.add_worksheet(title=name, rows="100", cols=str(len(headers)))
            ws.append_row(headers)
            print(f" -> Hoja '{name}' creada con éxito.")
            
    print("\n¡Configuración completada! Tu base de datos está lista.")

if __name__ == "__main__":
    print("=== SYNAPSE: GOOGLE SHEETS SETUP ===")
    cred_file = input("Ruta al archivo JSON de credenciales (ej. credentials.json): ")
    url = input("URL completa de tu Google Sheet: ")
    setup_google_sheet(cred_file, url)
