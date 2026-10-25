import yaml
from config import BASE_DIR

def load_rules():
    p = BASE_DIR / 'rules.yaml'
    try:
        return yaml.safe_load(p.read_text(encoding='utf-8')) or {}
    except Exception:
        return {}
