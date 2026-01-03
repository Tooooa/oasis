# -*- coding: utf-8 -*-
import sqlite3

db_path = r"D:\_Development\Agentguide\OASIS\oasis\outputs\databases\reddit_watermark_exp.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [t[0] for t in cursor.fetchall()]
print("Tables:", tables)

# Get schema for each table
for table in tables:
    cursor.execute(f"PRAGMA table_info({table})")
    columns = cursor.fetchall()
    print(f"\n{table}:")
    for col in columns:
        print(f"  {col[1]} ({col[2]})")

# Sample data from post table
print("\n--- Sample posts ---")
cursor.execute("SELECT * FROM post LIMIT 3")
for row in cursor.fetchall():
    print(row)

# Sample data from comment table
print("\n--- Sample comments ---")
cursor.execute("SELECT * FROM comment LIMIT 3")
for row in cursor.fetchall():
    print(row)

conn.close()
