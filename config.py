import math
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")


def env_float(name, default, minimum=None, maximum=None):
    raw = os.getenv(name)
    if raw is None or not str(raw).strip():
        value = float(default)
    else:
        try:
            value = float(str(raw).strip())
        except (TypeError, ValueError):
            value = float(default)
    if not math.isfinite(value):
        value = float(default)
    if minimum is not None:
        value = max(float(minimum), value)
    if maximum is not None:
        value = min(float(maximum), value)
    return value


def _load_env_file(path):
    if not path.exists():
        return
    try:
        lines = path.read_text(encoding='utf-8').splitlines()
    except Exception:
        return
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        if line.startswith('export '):
            line = line[7:].strip()
        key, _, value = line.partition('=')
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


_load_env_file(BASE_DIR / '.env')

DATA_DIR = BASE_DIR / "data"
KB_DIR = BASE_DIR / "knowledge_base"
STATIC_DIR = BASE_DIR / "static"
SOUNDS_DIR = STATIC_DIR / "sounds"
TEMPLATES_DIR = BASE_DIR / "templates"

DB_PATH = DATA_DIR / "app.db"

# LLM / SLM (OpenAI-compatible endpoint)
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "")
LLM_TIMEOUT = env_float("LLM_TIMEOUT", 10.0, minimum=1.0, maximum=120.0)

# Helplines (TODO_VERIFY)
HELPLINE_NUMBER = os.getenv("HELPLINE_NUMBER", "TODO_VERIFY")

# Tracking
ANON_ID_COOKIE = "rechers_anon_id"
DISPLAY_NAME_COOKIE = "rechers_name"
REDIS_URL = os.getenv("REDIS_URL", "")

# Retrieval
TOP_K = 3
MIN_RETRIEVAL_SCORE = env_float("MIN_RETRIEVAL_SCORE", 0.30, minimum=0.0, maximum=1.0)
CHUNK_WORDS = 170
MAX_MESSAGE_CHARS = 2000
EMBED_MODEL = "all-MiniLM-L6-v2"
