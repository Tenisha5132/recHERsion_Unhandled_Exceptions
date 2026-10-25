import json
import sqlite3
import uuid
from contextlib import contextmanager

from config import DATA_DIR, DB_PATH

DATA_DIR.mkdir(parents=True, exist_ok=True)


def get_conn():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def db_connection():
    conn = get_conn()
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    with db_connection() as conn:
        cur = conn.cursor()
        cur.execute('''CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            anonymous_user_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            raw_text TEXT,
            extracted_json TEXT
        )''')
        conn.commit()


def save_entry(anon_id, raw_text, extracted):
    if not anon_id:
        anon_id = str(uuid.uuid4())
    init_db()
    with db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            'INSERT INTO entries (anonymous_user_id, raw_text, extracted_json) VALUES (?,?,?)',
            (anon_id, raw_text, json.dumps(extracted)),
        )
        conn.commit()
    return anon_id


def get_entries(anon_id, limit=100):
    init_db()
    with db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            'SELECT * FROM entries WHERE anonymous_user_id=? ORDER BY created_at DESC LIMIT ?',
            (anon_id, limit),
        )
        rows = cur.fetchall()
    return [dict(row) for row in rows]


def get_recent_entries(anon_id, limit=5):
    return get_entries(anon_id, limit=limit)


def delete_entries(anon_id):
    init_db()
    with db_connection() as conn:
        cur = conn.cursor()
        cur.execute('DELETE FROM entries WHERE anonymous_user_id=?', (anon_id,))
        conn.commit()
        return cur.rowcount
