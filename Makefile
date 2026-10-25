install:
	pip install -r requirements.txt

install-embeddings:
	pip install -r requirements-embeddings.txt

run:
	uvicorn app:app --host 0.0.0.0 --port 8000

seed:
	python seed.py

ingest:
	python ingest.py

test:
	python -m unittest discover -s tests -v

check:
	python -m compileall -q agents app.py config.py health.py llm_client.py observability.py orchestrator.py retriever.py security.py tracker.py validation.py
	python -m unittest discover -s tests -v

smoke:
	python scripts/smoke_test.py --base-url $${BASE_URL:-http://127.0.0.1:8000}

docker:
	docker build -t rechersion .

sounds:
	python -c "from sounds import ensure_builtin_sounds; print('generated', len(ensure_builtin_sounds()), 'sound files')"

.PHONY: install install-embeddings run seed ingest test check smoke docker sounds
