run:
	uvicorn app:app --host 0.0.0.0 --port 8000

seed:
	python seed.py

ingest:
	python ingest.py

test:
	python -m unittest discover -s tests -v

sounds:
	python -c "from sounds import ensure_builtin_sounds; print('generated', len(ensure_builtin_sounds()), 'sound files')"

.PHONY: run seed ingest test sounds
