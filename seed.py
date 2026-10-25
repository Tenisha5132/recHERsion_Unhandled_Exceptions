import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from tracker import init_db, save_entry, get_conn, DATA_DIR
import uuid

def seed():
    init_db()
    # persona 1
    anon1 = 'seed_persona1_' + str(uuid.uuid4())[:8]
    # create ~3 months of entries
    base = datetime.now() - timedelta(days=90)
    entries1 = []
    # cycle gaps ~40-55 days pattern
    for i in range(3):
        d = base + timedelta(days=i*45 + random.randint(-5,5))
        if i == 0:
            entries1.append((d, "Periods started late this cycle, feeling tired and some acne", {"symptoms": ["tired", "acne"], "cycle_length_days": 48, "severity": 2}))
        elif i == 1:
            entries1.append((d, "Cycle came late again, quite fatigued", {"symptoms": ["tired", "fatigue"], "cycle_length_days": 52, "severity": 2}))
        else:
            entries1.append((d, "Mild cold today, just tired", {"symptoms": ["tired", "cold"], "cycle_length_days": 45, "severity": 1}))
    # save
    conn = get_conn()
    cur = conn.cursor()
    for d, txt, ex in entries1:
        cur.execute('INSERT INTO entries (anonymous_user_id, created_at, raw_text, extracted_json) VALUES (?,?,?,?)',
                    (anon1, d.strftime('%Y-%m-%d %H:%M:%S'), txt + ' [SYNTHETIC]', json.dumps(ex)))
    conn.commit()
    conn.close()
    # persona 2 - urgent
    anon2 = 'seed_persona2_' + str(uuid.uuid4())[:8]
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('INSERT INTO entries (anonymous_user_id, created_at, raw_text, extracted_json) VALUES (?,?,?,?)',
                (anon2, (datetime.now()-timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S'), 
                 "Soaking through a pad every hour for 2 hours, feeling faint [SYNTHETIC]", 
                 json.dumps({"symptoms": ["bleed", "heavy"], "severity": 5})))
    conn.commit()
    conn.close()
    print('Seeded synthetic personas')
    return anon1, anon2

if __name__ == '__main__':
    seed()
