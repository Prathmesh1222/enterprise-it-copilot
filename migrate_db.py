import pandas as pd
import sqlite3
import os

print("Migrating CSV to SQLite database...")

# Load the real dataset
csv_path = 'data/tickets.csv'
db_path = 'data/tickets.db'

if os.path.exists(db_path):
    os.remove(db_path)

df = pd.read_csv(csv_path)

# Connect to sqlite
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Create table with an auto-incrementing ID
cursor.execute('''
CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject TEXT,
    body TEXT,
    answer TEXT,
    type TEXT,
    queue TEXT,
    priority TEXT
)
''')

# Insert data
for _, row in df.iterrows():
    cursor.execute('''
    INSERT INTO tickets (subject, body, answer, type, queue, priority)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (str(row.get('subject', '')), str(row.get('body', '')), str(row.get('answer', '')), 
          str(row.get('type', '')), str(row.get('queue', '')), str(row.get('priority', ''))))

conn.commit()
conn.close()

print(f"Successfully migrated {len(df)} tickets to {db_path}!")
