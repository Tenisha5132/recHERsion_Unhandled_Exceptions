run:
	uvicorn app:app --host 0.0.0.0 --port 8000

seed:
	python seed.py

ingest:
	python ingest.py

.PHONY: run seed ingest
