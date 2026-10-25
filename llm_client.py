import json
import re
from urllib import request

from config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL, LLM_TIMEOUT


def is_available():
    return bool(LLM_API_KEY or LLM_BASE_URL)


def _endpoint():
    base = (LLM_BASE_URL or 'https://api.openai.com/v1').rstrip('/')
    if base.endswith('/chat/completions'):
        return base
    return base + '/chat/completions'


def chat(messages, temperature=0.2, max_tokens=240):
    if not is_available():
        return None
    payload = {
        'model': LLM_MODEL,
        'messages': messages,
        'temperature': temperature,
        'max_tokens': max_tokens,
    }
    headers = {'Content-Type': 'application/json'}
    if LLM_API_KEY:
        headers['Authorization'] = f'Bearer {LLM_API_KEY}'
    req = request.Request(
        _endpoint(),
        data=json.dumps(payload).encode('utf-8'),
        headers=headers,
        method='POST',
    )
    try:
        with request.urlopen(req, timeout=LLM_TIMEOUT) as response:
            data = json.loads(response.read().decode('utf-8'))
        choices = data.get('choices') or []
        content = (choices[0].get('message') or {}).get('content') if choices else None
        return str(content).strip() if content else None
    except Exception:
        return None


def chat_json(messages, temperature=0.0, max_tokens=120):
    text = chat(messages, temperature=temperature, max_tokens=max_tokens)
    if not text:
        return None
    text = re.sub(r'^```(?:json)?\s*|\s*```$', '', text.strip(), flags=re.I)
    start, end = text.find('{'), text.rfind('}')
    if start == -1 or end <= start:
        return None
    try:
        value = json.loads(text[start:end + 1])
    except Exception:
        return None
    return value if isinstance(value, dict) else None
