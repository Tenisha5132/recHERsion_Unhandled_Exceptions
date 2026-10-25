import asyncio
import re
import uuid
from urllib.parse import quote, unquote

from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException

from config import STATIC_DIR, TEMPLATES_DIR, ANON_ID_COOKIE, DISPLAY_NAME_COOKIE, SOUNDS_DIR, MAX_MESSAGE_CHARS, COOKIE_MAX_AGE, COOKIE_SECURE
from orchestrator import Orchestrator
from tracker import delete_entries, get_entries, init_db
from disclaimer import DISCLAIMER
from health import health_snapshot
from observability import RequestIdMiddleware
from security import SecurityHeadersMiddleware
from support import EMERGENCY_INDIA, FIND_A_HELPLINE, TELE_MANAS, build_support
from validation import validate_message
from sounds import SOUND_PROFILES, ensure_builtin_sounds, sound_cards, write_sound

app = FastAPI(title="recHERsion MVP")
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestIdMiddleware)
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

    async def warm_sounds():
        await asyncio.to_thread(ensure_builtin_sounds)

    asyncio.create_task(warm_sounds())


def _set_anon_cookie(response, anon_id):
    response.set_cookie(
        ANON_ID_COOKIE,
        anon_id,
        max_age=COOKIE_MAX_AGE,
        httponly=True,
        samesite='lax',
        secure=COOKIE_SECURE,
    )
    return response


def get_anon_id(request: Request):
    anon = request.cookies.get(ANON_ID_COOKIE)
    if not anon:
        anon = str(uuid.uuid4())
    return anon


def _clean_display_name(value):
    text = re.sub(r'\s+', ' ', str(value or '')).strip()
    text = ''.join(ch for ch in text if ch.isprintable() and ch not in '<>')
    return text[:40]


def get_display_name(request: Request):
    return _clean_display_name(unquote(request.cookies.get(DISPLAY_NAME_COOKIE) or ''))


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

    text = (message or '').lower()
    category = (res.get('route') or {}).get('category')
    if category == 'off_topic':
        return 'neutral'
    if category == 'general_health':
        return 'low' if LOW_MOOD.search(text) else 'mild'

    extracted = ((res.get('extraction') or {}).get('extracted') or {})
    symptoms = [str(s).lower() for s in (extracted.get('symptoms') or [])]
    severity = extracted.get('severity')
    try:
        severity_value = float(severity) if severity is not None else 0.0
    except Exception:
        severity_value = 0.0

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


def _general_payload(res):
    general = res.get('general') or {}
    category = (res.get('route') or {}).get('category') or ''
    return {
        'reply': _sanitize(general.get('reply') or ''),
        'mode': general.get('mode') or 'fallback',
        'scope': category,
    }


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


def _support_payload(res, theme):
    if ((res.get('route') or {}).get('category') or '') == 'off_topic':
        return None
    return build_support(theme, res)


def build_api_payload(res, message):
    theme = _theme_for(res, message)
    return {
        'mood': _mood_payload(res, theme),
        'safety': _safety_payload(res),
        'insight': _insight_payload(res),
        'remedy': _remedy_payload(res),
        'general': _general_payload(res),
        'support': _support_payload(res, theme),
        'trace': _trace_payload(res)
    }


@app.exception_handler(StarletteHTTPException)
async def http_error_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404 and not request.url.path.startswith('/api/'):
        return templates.TemplateResponse(request, "404.html", {
            "display_name": get_display_name(request),
            "nav_page": "",
        }, status_code=404)
    return JSONResponse({'detail': exc.detail}, status_code=exc.status_code)


@app.get("/healthz")
async def healthz():
    return JSONResponse(health_snapshot(), headers={'Cache-Control': 'no-store'})


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    anon = get_anon_id(request)
    resp = templates.TemplateResponse(request, "mood_ui.html", {
        "display_name": get_display_name(request),
        "nav_page": "chat",
        "max_message_chars": MAX_MESSAGE_CHARS
    })
    _set_anon_cookie(resp, anon)
    return resp


@app.get("/sounds", response_class=HTMLResponse)
async def sounds_page(request: Request):
    anon = get_anon_id(request)
    resp = templates.TemplateResponse(request, "sounds.html", {
        "sounds": sound_cards(),
        "display_name": get_display_name(request),
        "nav_page": "sounds",
        "disclaimer": DISCLAIMER
    })
    _set_anon_cookie(resp, anon)
    return resp


@app.get("/media/sounds/{slug}.wav")
async def builtin_sound(slug: str):
    profile = next((item for item in SOUND_PROFILES if item["slug"] == slug), None)
    if not profile:
        raise HTTPException(status_code=404, detail="Sound not found")
    path = SOUNDS_DIR / f"{slug}.wav"
    if not path.exists():
        await asyncio.to_thread(write_sound, profile)
    return FileResponse(path, media_type="audio/wav", headers={"Cache-Control": "public, max-age=86400"})


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    resp = templates.TemplateResponse(request, "login.html", {
        "display_name": get_display_name(request),
        "nav_page": "login",
        "disclaimer": DISCLAIMER
    })
    return resp


@app.post("/login")
async def login(request: Request, display_name: str = Form(...)):
    name = _clean_display_name(display_name)
    if not name:
        return templates.TemplateResponse(request, "login.html", {
            "display_name": "",
            "nav_page": "login",
            "error": "Please enter a name before continuing.",
            "disclaimer": DISCLAIMER
        }, status_code=400)
    resp = RedirectResponse(url='/', status_code=303)
    resp.set_cookie(
        DISPLAY_NAME_COOKIE,
        quote(name, safe=''),
        max_age=COOKIE_MAX_AGE,
        httponly=True,
        samesite='lax',
        secure=COOKIE_SECURE
    )
    return resp


@app.post("/logout")
async def logout():
    resp = RedirectResponse(url='/login', status_code=303)
    resp.delete_cookie(DISPLAY_NAME_COOKIE, secure=COOKIE_SECURE, samesite='lax')
    return resp


@app.post("/api/chat")
async def api_chat(request: Request):
    try:
        data = await request.json()
    except Exception:
        return JSONResponse({'error': 'Invalid JSON'}, status_code=400)
    payload = data if isinstance(data, dict) else {}
    message, error, status = validate_message(payload.get('message'))
    if error:
        return JSONResponse({'error': error}, status_code=status)
    anon = get_anon_id(request)
    result = orch.run(message, anon_id=anon)
    resp = JSONResponse(build_api_payload(result, message))
    _set_anon_cookie(resp, anon)
    return resp


@app.post("/chat")
async def chat(request: Request, message: str = Form(...)):
    message, error, status = validate_message(message)
    if error:
        raise HTTPException(status_code=status, detail=error)
    anon = get_anon_id(request)
    res = orch.run(message, anon_id=anon)
    resp = templates.TemplateResponse(request, "chat_result.html", {
        "result": res,
        "display_name": get_display_name(request),
        "nav_page": "chat",
        "disclaimer": DISCLAIMER
    })
    _set_anon_cookie(resp, anon)
    return resp


@app.get("/support", response_class=HTMLResponse)
async def support_page(request: Request):
    anon = get_anon_id(request)
    resp = templates.TemplateResponse(request, "support.html", {
        "support": build_support('neutral'),
        "emergency": EMERGENCY_INDIA,
        "helpline": TELE_MANAS,
        "global_help": FIND_A_HELPLINE,
        "display_name": get_display_name(request),
        "nav_page": "support",
        "disclaimer": DISCLAIMER
    })
    _set_anon_cookie(resp, anon)
    return resp


@app.get("/timeline")
async def timeline(request: Request):
    anon = get_anon_id(request)
    entries = get_entries(anon, limit=100)
    resp = templates.TemplateResponse(request, "timeline.html", {
        "entries": entries,
        "display_name": get_display_name(request),
        "nav_page": "journal",
        "disclaimer": DISCLAIMER
    })
    _set_anon_cookie(resp, anon)
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
    delete_entries(anon)
    resp = RedirectResponse(url='/', status_code=303)
    resp.delete_cookie(ANON_ID_COOKIE, secure=COOKIE_SECURE, samesite='lax')
    return resp


@app.get("/privacy")
async def privacy(request: Request):
    anon = get_anon_id(request)
    resp = templates.TemplateResponse(request, "privacy.html", {
        "display_name": get_display_name(request),
        "nav_page": "privacy",
        "disclaimer": DISCLAIMER
    })
    _set_anon_cookie(resp, anon)
    return resp
