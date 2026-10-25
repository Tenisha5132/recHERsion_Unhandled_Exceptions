import re
import uuid

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from config import BASE_DIR, STATIC_DIR, TEMPLATES_DIR, ANON_ID_COOKIE
from orchestrator import Orchestrator
from tracker import get_entries, init_db
from curated_loader import load_curated
from disclaimer import DISCLAIMER

app = FastAPI(title="recHERsion MVP")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

orch = Orchestrator()

SNAKE_CASE = re.compile(r'\b[a-z]+(?:_[a-z]+)+\b')
PAIN_OR_CYCLE = re.compile(
    r'\b(period|periods|menstrual|cycle|cycles|bleed|bleeding|blood|'
    r'pain|painful|cramp|cramps|ache|aches|aching)\b',
    re.I)
LOW_MOOD = re.compile(
    r'\b(sad|sadness|stress|stressed|stressful|anxious|anxiety|overwhelm\w*|'
    r'low mood|depress\w*|lonely|upset)\b',
    re.I)
MILD_WORDS = ('cold', 'tired', 'fatigue', 'runny', 'sniff', 'flu', 'cough', 'slept badly')
THEME_EMOJI = {
    'neutral': '🌸',
    'mild': '☕',
    'low': '🫂',
    'discuss': '🩺',
    'urgent': '⚠️',
    'distress': '🤍',
}


@app.on_event("startup")
async def startup():
    init_db()


def get_anon_id(request: Request):
    anon = request.cookies.get(ANON_ID_COOKIE)
    if not anon:
        anon = str(uuid.uuid4())
    return anon


def _sanitize(value):
    text = '' if value is None else str(value)
    text = re.sub(r'\bTODO_VERIFY\b', ' ', text, flags=re.I)
    text = SNAKE_CASE.sub(lambda m: m.group(0).replace('_', ' '), text)
    return re.sub(r'\s+', ' ', text).strip()


def _clean_citations(items):
    out = []
    seen = set()
    for item in items or []:
        if not isinstance(item, dict):
            continue
        url = str(item.get('source_url') or '').strip()
        if not re.match(r'^https?://', url, re.I) or 'TODO_VERIFY' in url.upper():
            continue
        if url in seen:
            continue
        seen.add(url)
        out.append({'title': _sanitize(item.get('title') or url) or url, 'source_url': url})
    return out


def _theme_for(res, message):
    safety = res.get('safety') or {}
    action = safety.get('action')
    if action == 'urgent_override':
        return 'urgent'
    if action == 'distress_support':
        return 'distress'

    insight = res.get('insight') or {}
    if (insight.get('flag_level') or '').lower() == 'discuss':
        return 'discuss'

    extracted = ((res.get('extraction') or {}).get('extracted') or {})
    symptoms = [str(s).lower() for s in (extracted.get('symptoms') or [])]
    severity = extracted.get('severity')
    try:
        severity_value = float(severity) if severity is not None else 0.0
    except Exception:
        severity_value = 0.0

    text = (message or '').lower()
    has_cycle_or_pain = bool(PAIN_OR_CYCLE.search(text)) or any(
        s in symptoms for s in ['pain', 'cramp', 'cramps', 'bleed', 'bleeding', 'heavy'])
    mild = any(word in text for word in MILD_WORDS) or any(
        s in symptoms for s in ['tired', 'fatigue', 'cold'])

    if mild and severity_value <= 2 and not has_cycle_or_pain:
        return 'mild'
    if LOW_MOOD.search(text):
        return 'low'
    return 'neutral'


def _mood_payload(res, theme):
    mood = res.get('mood') or {}
    emoji = _sanitize(mood.get('emoji') or '') or THEME_EMOJI[theme]
    joke = None
    if theme == 'mild':
        joke = _sanitize(mood.get('joke') or '') or None
    return {'theme': theme, 'emoji': emoji, 'joke': joke}


def _safety_payload(res):
    safety = res.get('safety') or {}
    action = safety.get('action')
    if action not in ('ok', 'urgent_override', 'distress_support'):
        action = 'ok'
    message = _sanitize(safety.get('message') or '')
    if action == 'ok' and not message:
        message = 'No emergency red flags detected.'
    return {'action': action, 'message': message}


def _insight_payload(res):
    insight = res.get('insight')
    if not insight:
        action = (res.get('safety') or {}).get('action')
        if action == 'urgent_override':
            return {
                'flag_level': 'urgent',
                'pattern': 'Safety concern flagged for urgent medical attention',
                'reasoning': '',
                'citations': [],
                'questions_for_doctor': []
            }
        return {
            'flag_level': 'none',
            'pattern': "No pattern flagged from what you've shared",
            'reasoning': '',
            'citations': [],
            'questions_for_doctor': []
        }

    reasoning = insight.get('reasoning')
    if isinstance(reasoning, (list, tuple)):
        reasoning = '; '.join(item for item in (_sanitize(x) for x in reasoning) if item)
    else:
        reasoning = _sanitize(reasoning)

    questions = []
    for question in insight.get('questions_for_doctor') or []:
        text = _sanitize(question)
        if text and text not in questions:
            questions.append(text)

    flag_level = insight.get('flag_level')
    if flag_level not in ('none', 'discuss', 'urgent'):
        flag_level = 'none'

    return {
        'flag_level': flag_level,
        'pattern': _sanitize(insight.get('pattern') or ''),
        'reasoning': reasoning,
        'citations': _clean_citations(insight.get('citations')),
        'questions_for_doctor': questions
    }


def _remedy_payload(res):
    remedy = res.get('remedy') or {}
    advice = []
    for item in remedy.get('advice') or []:
        text = _sanitize(item.get('text') if isinstance(item, dict) else item)
        if text:
            advice.append(text)
    return {'advice': advice, 'citations': _clean_citations(remedy.get('citations'))}


def _trace_payload(res):
    entries = []
    for item in res.get('trace') or []:
        agent = _sanitize(item.get('agent') or 'agent')
        mode = item.get('mode')
        if mode not in ('rules', 'llm', 'fallback'):
            mode = 'rules'
        incoming = _sanitize(item.get('input_summary') or '')
        outgoing = _sanitize(item.get('output_summary') or '')
        summary = f'{incoming} -> {outgoing}' if incoming and outgoing else (outgoing or incoming)
        if len(summary) > 240:
            summary = summary[:237] + '...'
        try:
            ms = int(item.get('ms') or 0)
        except Exception:
            ms = 0
        entries.append({'agent': agent, 'mode': mode, 'summary': summary, 'ms': ms})
    return entries


def build_api_payload(res, message):
    theme = _theme_for(res, message)
    return {
        'mood': _mood_payload(res, theme),
        'safety': _safety_payload(res),
        'insight': _insight_payload(res),
        'remedy': _remedy_payload(res),
        'trace': _trace_payload(res)
    }


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    anon = get_anon_id(request)
    resp = templates.TemplateResponse(request, "mood_ui.html", {})
    resp.set_cookie(ANON_ID_COOKIE, anon)
    return resp


@app.post("/api/chat")
async def api_chat(request: Request):
    try:
        data = await request.json()
    except Exception:
        return JSONResponse({'error': 'Invalid JSON'}, status_code=400)
    message = str((data or {}).get('message') or '').strip()
    if not message:
        return JSONResponse({'error': 'message is required'}, status_code=400)
    anon = get_anon_id(request)
    result = orch.run(message, anon_id=anon)
    resp = JSONResponse(build_api_payload(result, message))
    resp.set_cookie(ANON_ID_COOKIE, anon)
    return resp


@app.post("/chat")
async def chat(request: Request, message: str = Form(...)):
    anon = get_anon_id(request)
    res = orch.run(message, anon_id=anon)
    resp = templates.TemplateResponse(request, "chat_result.html", {"result": res, "disclaimer": DISCLAIMER})
    resp.set_cookie(ANON_ID_COOKIE, anon)
    return resp


@app.get("/timeline")
async def timeline(request: Request):
    anon = get_anon_id(request)
    entries = get_entries(anon, limit=100)
    resp = templates.TemplateResponse(request, "timeline.html", {"entries": entries, "disclaimer": DISCLAIMER})
    resp.set_cookie(ANON_ID_COOKIE, anon)
    return resp


@app.get("/summary.pdf")
async def summary_pdf(request: Request):
    from summary_pdf import generate_summary
    anon = get_anon_id(request)
    path = generate_summary(anon)
    return FileResponse(path, media_type='application/pdf', filename='doctor_summary.pdf')


@app.post("/delete")
async def delete_data(request: Request):
    anon = get_anon_id(request)
    from tracker import get_conn
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('DELETE FROM entries WHERE anonymous_user_id=?', (anon,))
    conn.commit()
    conn.close()
    resp = RedirectResponse(url='/', status_code=303)
    resp.delete_cookie(ANON_ID_COOKIE)
    return resp


@app.get("/privacy")
async def privacy(request: Request):
    anon = get_anon_id(request)
    resp = templates.TemplateResponse(request, "privacy.html", {"disclaimer": DISCLAIMER})
    resp.set_cookie(ANON_ID_COOKIE, anon)
    return resp
