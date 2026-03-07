import sqlite3
import json

conn = sqlite3.connect('ai_service_v3.db')
row = conn.execute('SELECT docs_json FROM ai_jobs WHERE docs_json IS NOT NULL ORDER BY rowid DESC LIMIT 1').fetchone()
if row and row[0]:
    docs = json.loads(row[0])
    print(f"Cached docs keys: {list(docs.keys())}")
    for k, v in docs.items():
        print(f"  - {k}: {len(v)} chars")
else:
    print("None found")
conn.close()
