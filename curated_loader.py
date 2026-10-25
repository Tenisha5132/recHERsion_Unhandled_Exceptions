import json
from config import BASE_DIR

def load_curated():
    p = BASE_DIR / 'curated_videos.json'
    if not p.exists():
        p.write_text(json.dumps([], indent=2), encoding='utf-8')
    try:
        data = json.loads(p.read_text(encoding='utf-8'))
        return data
    except Exception:
        return []

# template
if __name__ == '__main__':
    p = BASE_DIR / 'curated_videos.json'
    if not p.exists():
        p.write_text(json.dumps([], indent=2), encoding='utf-8')
        print('created template')
    else:
        print('exists')
