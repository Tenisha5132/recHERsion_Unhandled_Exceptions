#!/bin/bash
cd "$(dirname "$0")"
uvicorn app:app --host 0.0.0.0 --port 8000
