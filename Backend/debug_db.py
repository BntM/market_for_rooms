
import sqlite3
import os

try:
    conn = sqlite3.connect('market.db')
    cursor = conn.cursor()
    print("Checking admin_config columns:")
    cursor.execute("PRAGMA table_info(admin_config)")
    columns = cursor.fetchall()
    for col in columns:
        print(col)
    conn.close()
except Exception as e:
    print(f"Error: {e}")
