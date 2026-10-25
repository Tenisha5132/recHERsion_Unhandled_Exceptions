import sqlite3
import json
import uuid
from pathlib import Path
from config import DB_PATH, DATA_DIR

DATA_DIR.mkdir(parents=True, exist_ok=True)

def get_conn():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        anonymous_user_id TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        raw_text TEXT,
        extracted_json TEXT
    )''')
    conn.commit()
    conn.close()

def save_entry(anon_id, raw_text, extracted):
    if not anon_id:
        anon_id = str(uuid.uuid4())
    init_db()
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('INSERT INTO entries (anonymous_user_id, raw_text, extracted_json) VALUES (?,?,?)',
                (anon_id, raw_text, json.dumps(extracted)))
    conn.commit()
    conn.close()
    return anon_id

def get_entries(anon_id, limit=100):
    init_db()
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('SELECT * FROM entries WHERE anonymous_user_id=? ORDER BY created_at DESC LIMIT ?', (anon_id, limit))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_recent_entries(anon_id, limit=5):
    return get_entries(anon_id, limit=limit)
