import sys
import os

# Append current dir so app can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from app import load_table
    df = load_table('USERS')
    print("=== DEBUG USERS TABLE ===")
    if df.empty:
        print("THE TABLE IS EMPTY OR NO DATA WAS FOUND.")
    else:
        print("COLUMNS:", df.columns.tolist())
        for idx, row in df.iterrows():
            print(f"ROW {idx}:", row.to_dict())
            
except Exception as e:
    print("ERROR DURING DEBUG:", e)
