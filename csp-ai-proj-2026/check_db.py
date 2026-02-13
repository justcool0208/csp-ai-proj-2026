import sqlite3
import json

DB_PATH = "c:/Users/rohit/OneDrive/Desktop/CSP/energy-management-system/energy_system.db"
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute("SELECT * FROM appliances")
rows = cursor.fetchall()
print("ID | Name | kW | Dur | Start | End | Pri")
for r in rows:
    print(f"{r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]} | {r[5]} | {r[6]}")
conn.close()
