
import sqlite3
import pandas as pd
import os

DB_NAME = "Employee_Details.DB"
DATA_FOLDER = "data"

conn = sqlite3.connect(DB_NAME)

for f in os.listdir(DATA_FOLDER):
    file_path = os.path.join(DATA_FOLDER, f)

    if f.endswith(".csv"):
        df = pd.read_csv(file_path)
        df.to_sql("employee_details", conn, if_exists="replace", index=False)
        print(f"[OK] Loaded CSV → employee_details")

    elif f.endswith(".xlsx") or f.endswith(".xls"):
        df = pd.read_excel(file_path)
        df.to_sql("employee_details", conn, if_exists="replace", index=False)
        print(f"[OK] Loaded Excel → employee_details")

    else:
        print(f"[SKIP] Unsupported file: {f}")

conn.commit()
conn.close()
print("\n✅ All files imported → employee_details ready!")
