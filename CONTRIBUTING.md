# Contributing

## Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

The app runs without an LLM key. Set `LLM_API_KEY` and `LLM_BASE_URL` only if you want to exercise the optional model path. Do not commit `.env`, database files, generated WAVs, or trace files.

## Checks
```bash
python -m unittest discover -s tests -v
python -m compileall -q agents app.py config.py health.py llm_client.py observability.py orchestrator.py retriever.py security.py tracker.py validation.py
```

Start a local server and run the deployment check:
```bash
uvicorn app:app --host 127.0.0.1 --port 8011
python scripts/smoke_test.py --base-url http://127.0.0.1:8011
```

## Guidelines
- Keep safety overrides, distress support and source citations intact.
- Do not add medication doses or diagnostic claims.
- New general-health behavior must not attach unrelated period advice or citations.
- Keep generated traces and personal health text out of commits.
- Add or update tests for routing, retrieval, validation, cookies and page contracts.
- Use small, focused commits with an imperative subject line.

## Reporting
Follow [SECURITY.md](SECURITY.md) for vulnerabilities. For clinical content concerns, open an issue with the source URL and the exact wording that needs review.
