# recHERsion MVP

[![tests](https://github.com/Tenisha5132/recHERsion_Unhandled_Exceptions/actions/workflows/tests.yml/badge.svg)](https://github.com/Tenisha5132/recHERsion_Unhandled_Exceptions/actions/workflows/tests.yml)

## Problem
recHERsion MVP is a multi-agent RAG app for PS1 "Women's Healthcare" (gaps in diagnosis, symptom tracking, health awareness, access to clinical insights). This app is screening/awareness support only — not a diagnosis.

## Architecture (ASCII)
```
User (Browser) -> FastAPI (app.py)
                    |-> Orchestrator
                        |-> router -> safety(1) -> extraction
                        |     |-> women's health: tracker(save) -> retriever -> insight -> remedy -> mood -> safety(2)
                        |     |-> general/off-topic: general -> mood -> safety(2)
                    |-> SQLite (tracker.py)
                    |-> RAG (ingest.py, retriever.py) using knowledge_base/ + embeddings/BM25
                    |-> Optional OpenAI-compatible LLM/SLM (llm_client.py)
                    |-> Templates/Static (HTML/CSS/JS pages)
                    |-> PDF summary (summary_pdf.py via reportlab)
```

## Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Semantic embeddings are optional. Without them the app uses BM25:
```bash
pip install -r requirements-embeddings.txt
```

## Run
```bash
make run
# or
./run.sh
# or
uvicorn app:app --host 0.0.0.0 --port 8000
```

## Scope-aware replies
The router keeps menstrual and reproductive health separate from general health:

- Period, cycle, bleeding, pelvic pain, fertility, pregnancy and menopause messages use the KB-grounded RAG path.
- A cold, cough, headache or other general symptom gets a general-health reply and GP/pharmacy support, without unrelated period sources.
- Off-topic messages get a short scope reply and no care cards.
- Urgent red flags and distress language still override every other route.
- Retrieval now applies stopword filtering and a relevance floor, so unrelated messages do not receive citations.

## LLM / SLM setup
The app works without a model key. To enable an OpenAI-compatible hosted model or a local SLM, edit `.env`:

```bash
LLM_API_KEY=your-key
LLM_MODEL=gpt-4o-mini
LLM_BASE_URL=https://api.openai.com/v1
```

For a local Ollama-style endpoint:

```bash
LLM_API_KEY=
LLM_MODEL=your-local-model
LLM_BASE_URL=http://localhost:11434/v1
```

The LLM is optional and is used for ambiguous routing and general/off-topic replies. Safety checks, red-flag overrides, retrieval and the women's-health insight path remain rule-based.

## Deployment
`requirements.txt` and `Procfile` are included. A typical hosted setup:

```bash
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port $PORT
```

Set `LLM_API_KEY`, `LLM_MODEL`, `LLM_BASE_URL`, `LLM_TIMEOUT`, `MIN_RETRIEVAL_SCORE` and `COOKIE_SECURE` in the host environment. Do not commit `.env`. Attach a persistent disk if saved journal entries must survive restarts, because SQLite is stored at `data/app.db`.

The health endpoint is `GET /healthz`. After deployment, verify the running app:

```bash
python scripts/smoke_test.py --base-url https://your-host
```

### Docker
```bash
docker build -t rechersion .
docker run --rm -p 8000:8000 --env-file .env rechersion
```

The image runs as a non-root user and checks `/healthz` with Docker's healthcheck. Mount a private volume at `/app/data` if you need durable journal storage.

## Tests
```bash
make check
# or
python -m unittest discover -s tests -v
```

The suite covers extraction, scope routing, retrieval relevance, general replies, config parsing, LLM fallbacks, cookies, tracker access, deployment health, security headers and page contracts. GitHub Actions runs it on Python 3.11 and 3.12.

## Pages
The app is split into focused pages instead of one long screen:

- `/` — private chat, mood theming and support cards
- `/sounds` — built-in soundscapes plus your own local music uploads
- `/timeline` — saved journal entries, PDF summary and delete controls
- `/support` — emergency numbers, helplines and nearby-care map searches
- `/privacy` — what is stored, what stays in the browser and what leaves the device
- `/login` — optional display-name cookie; no password or email

## Diagrams
- [Multi-agent workflow](docs/multi_agent_workflow.mmd) — request path through router, safety, extraction, the women's-health RAG branch, the general/off-topic branch, mood and final safety.
- [Features and guardrails](docs/features_and_guardrails.mmd) — what was added and the safety/privacy protections kept in place.

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
- router: classify message as women's health, general health, off-topic, urgent or distress
- safety: red flags + distress first and last; strips diagnostic claims
- extraction: free text -> structured JSON with nulls
- retriever: top-3 relevant chunks + recent log entries, with a relevance floor
- insight: rules-based, cites chunks, age-aware, suggests pregnancy test when relevant, never diagnoses
- remedy: safe self-care from KB only
- general: non-period health replies, using an optional LLM or a safe rules fallback
- mood: deterministic, jokes only for mild non-pain cases when safe

## Operations and troubleshooting
- `GET /healthz` reports the app version, retrieval backend, chunk count, and whether an LLM is configured. It never returns a key.
- `COOKIE_SECURE=true` is required behind HTTPS. Anonymous and display-name cookies are HTTP-only and SameSite=Lax.
- Security headers and `X-Request-ID` are attached to every HTTP response. Use the request ID when comparing a browser error with server output.
- If a cold or general-health message still mentions periods, check `tests/test_general_route.py` and `MIN_RETRIEVAL_SCORE`; general and off-topic routes must skip retrieval.
- If the model is not used, check `GET /healthz` and confirm `LLM_API_KEY` or `LLM_BASE_URL` is set in the running process. Rules fallback is expected without either.
- Generated sounds are gitignored and created on first use. If `/media/sounds/...` fails, confirm `static/sounds/` is writable by the app user.
- See [API contract](docs/API.md), [contributing](CONTRIBUTING.md) and [security policy](SECURITY.md).

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
- sentence-transformers (all-MiniLM-L6-v2) - optional embeddings
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
