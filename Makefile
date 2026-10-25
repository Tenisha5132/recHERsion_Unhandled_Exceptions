PYTHON ?= $(if $(wildcard .venv/bin/python),.venv/bin/python,python3)
UVICORN ?= $(if $(wildcard .venv/bin/uvicorn),.venv/bin/uvicorn,uvicorn)

install:
	$(PYTHON) -m pip install -r requirements.txt

install-embeddings:
	$(PYTHON) -m pip install -r requirements-embeddings.txt

run:
	$(UVICORN) app:app --host 0.0.0.0 --port 8000

seed:
	$(PYTHON) seed.py

ingest:
	$(PYTHON) ingest.py

test:
	$(PYTHON) -m unittest discover -s tests -v

check:
	$(PYTHON) -m compileall -q agents app.py config.py health.py llm_client.py observability.py orchestrator.py retriever.py security.py tracker.py validation.py scripts
	$(PYTHON) -m unittest discover -s tests -v

smoke:
	$(PYTHON) scripts/smoke_test.py --base-url $${BASE_URL:-http://127.0.0.1:8000}

docker:
	docker build -t rechersion .

sounds:
	$(PYTHON) -c "from sounds import ensure_builtin_sounds; print('generated', len(ensure_builtin_sounds()), 'sound files')"

.PHONY: install install-embeddings run seed ingest test check smoke docker sounds
