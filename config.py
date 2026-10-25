import os
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
KB_DIR = BASE_DIR / "knowledge_base"
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

DB_PATH = DATA_DIR / "app.db"

# LLM
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-3.5-turbo")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "")

# Helplines (TODO_VERIFY)
HELPLINE_NUMBER = os.getenv("HELPLINE_NUMBER", "TODO_VERIFY")

# Tracking
ANON_ID_COOKIE = "rechers_anon_id"
REDIS_URL = os.getenv("REDIS_URL", "")

# Retrieval
TOP_K = 3
CHUNK_WORDS = 170
EMBED_MODEL = "all-MiniLM-L6-v2"
