# recHERsion MVP

## Problem
recHERsion MVP is a multi-agent RAG app for PS1 "Women's Healthcare" (gaps in diagnosis, symptom tracking, health awareness, access to clinical insights). This app is screening/awareness support only — not a diagnosis.

## Architecture (ASCII)
```
User (Browser) -> FastAPI (app.py)
                    |-> Orchestrator
                        |-> router -> safety(1) -> extraction -> tracker(save) -> retriever -> insight -> remedy -> mood -> safety(2)
                    |-> SQLite (tracker.py)
                    |-> RAG (ingest.py, retriever.py) using knowledge_base/ + embeddings/BM25
                    |-> Templates/Static (HTML/CSS/JS, canvas charts)
                    |-> PDF summary (summary_pdf.py via reportlab)
```

## Setup
```bash
pip install fastapi uvicorn pyyaml sentence-transformers rank_bm25 numpy reportlab jinja2 python-multipart
cp .env.example .env
```

## Run
```bash
make run
# or
./run.sh
# or
uvicorn app:app --host 0.0.0.0 --port 8000
```

## Pages
The app is split into focused pages instead of one long screen:

- `/` — private chat, mood theming and support cards
- `/sounds` — built-in soundscapes plus your own local music uploads
- `/timeline` — saved journal entries, PDF summary and delete controls
- `/support` — emergency numbers, helplines and nearby-care map searches
- `/privacy` — what is stored, what stays in the browser and what leaves the device
- `/login` — optional display-name cookie; no password or email

## Seed
```bash
make seed
# or
python seed.py
```

## Ingest KB
```bash
make ingest
# or
python ingest.py
```

## Sound library
The `/sounds` page includes 15 generated ambient loops: calm, focus, sleep, breathing, grounding, nature, noise, uplift and mindful categories. The WAV files are generated locally on first use by `sounds.py`; they are not committed to git.

- The built-in player supports volume, looping and a 15/30/60/90 minute sleep timer.
- Your own music can be added with the file picker.
- Uploaded audio stays in the browser using IndexedDB. It is not uploaded to the server.
- Removing a track deletes it from that browser.
- Audio is a comfort tool, not treatment.

## Agents
- router: classify message
- safety: red flags + distress first and last; strips diagnostic claims
- extraction: free text -> structured JSON with nulls
- retriever: top-3 chunks + recent log entries
- insight: rules-based, cites chunks, age-aware, suggests pregnancy test when relevant, never diagnoses
- remedy: safe self-care from KB only
- mood: deterministic, jokes only for mild non-pain cases when safe

## Privacy & Limitations
- No names/emails/phone. anonymous_user_id in browser cookie. Data in local SQLite DB.
- If LLM key set, de-identified message text may be sent to provider.
- Not a medical device, not diagnosis. Synthetic eval only.
- LLM fallback behavior: app runs without key with rule-based fallbacks; UI/trace indicate fallback.
- Clinical content only from knowledge_base/ built from provided sources.
- Thresholds in rules.yaml with source_url/kb_file or TODO_VERIFY; features degrade gracefully.

## Credits
### Libraries
- FastAPI, Uvicorn, Jinja2, python-multipart - ASGI/web
- PyYAML - rules/config
- sentence-transformers (all-MiniLM-L6-v2) - embeddings
- rank_bm25 - BM25 fallback
- numpy - cosine similarity
- reportlab - PDF
- sqlite3 - storage

### Models
- sentence-transformers/all-MiniLM-L6-v2 (Apache 2.0)

### Knowledge base sources
- https://www.nhs.uk/conditions/heavy-periods/
- https://www.nhs.uk/conditions/heavy-periods/diagnosis/
- https://www.nhs.uk/conditions/irregular-periods/
- https://www.nhs.uk/conditions/irregular-periods/treatment/
- https://www.who.int/news-room/fact-sheets/detail/polycystic-ovary-syndrome
- https://www.nhs.uk/conditions/polyendocrine-metabolic-ovarian-syndrome-pmos/
- https://www.nhs.uk/conditions/endometriosis/
- https://www.nhs.uk/conditions/underactive-thyroid-hypothyroidism/

All knowledge-base files are my-own-words summaries. Licences respected.

## Demo script (3-minute)
1. Start app, go to home
2. Send urgent-like message (e.g. soaking hourly for 2h + faint) -> urgent banner
3. Send PMOS-related message -> insight with citations
4. View timeline + chart, download PDF summary
5. Check agent trace panel
