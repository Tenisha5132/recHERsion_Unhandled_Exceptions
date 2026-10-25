import os
import json
import re
from pathlib import Path

import yaml
from config import BASE_DIR, KB_DIR, CHUNK_WORDS

FRONT_MATTER_RE = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.DOTALL)

def parse_front_matter(text):
    m = FRONT_MATTER_RE.match(text)
    if not m:
        return {}, text
    fm_text = m.group(1)
    try:
        fm = yaml.safe_load(fm_text) or {}
    except Exception:
        fm = {}
    body = text[m.end():]
    return fm, body

def chunk_text_words(text, chunk_words=CHUNK_WORDS):
    words = re.findall(r'\S+', text)
    chunks = []
    for i in range(0, len(words), chunk_words):
        chunk = ' '.join(words[i:i+chunk_words])
        if chunk.strip():
            chunks.append(chunk)
    return chunks

def ingest():
    KB_DIR.mkdir(parents=True, exist_ok=True)
    items = []
    for md in sorted(KB_DIR.glob('*.md')):
        try:
            content = md.read_text(encoding='utf-8')
        except Exception:
            continue
        fm, body = parse_front_matter(content)
        chunks = chunk_text_words(body)
        for idx, ch in enumerate(chunks):
            items.append({
                'id': f"{md.stem}_{idx}",
                'source_file': md.name,
                'title': fm.get('title', md.stem),
                'source_url': fm.get('source_url', ''),
                'publisher': fm.get('publisher', ''),
                'retrieved_date': fm.get('retrieved_date', ''),
                'aliases': fm.get('aliases', []),
                'chunk': ch,
                'chunk_idx': idx
            })
    out_path = BASE_DIR / 'data' / 'kb_chunks.json'
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(items, indent=2), encoding='utf-8')
    return items

if __name__ == '__main__':
    items = ingest()
    print(f'Ingested {len(items)} chunks')
