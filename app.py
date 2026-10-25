from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uuid
from pathlib import Path

from config import BASE_DIR, STATIC_DIR, TEMPLATES_DIR, ANON_ID_COOKIE
from orchestrator import Orchestrator
from tracker import get_entries, init_db
from curated_loader import load_curated
from disclaimer import DISCLAIMER

app = FastAPI(title="recHERsion MVP")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

orch = Orchestrator()

@app.on_event("startup")
async def startup():
    init_db()

def get_anon_id(request: Request):
    anon = request.cookies.get(ANON_ID_COOKIE)
    if not anon:
        anon = str(uuid.uuid4())
    return anon

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    anon = get_anon_id(request)
    entries = get_entries(anon, limit=20)
    curated = load_curated()
    resp = templates.TemplateResponse("index.html", {"request": request, "entries": entries, "curated": curated, "disclaimer": DISCLAIMER, "seeded_label": "[SYNTHETIC]"})
    resp.set_cookie(ANON_ID_COOKIE, anon)
    return resp

@app.post("/chat")
async def chat(request: Request, message: str = Form(...)):
    anon = get_anon_id(request)
    res = orch.run(message, anon_id=anon)
    # store trace in session-like way via file? orchestrator already logs
    resp = templates.TemplateResponse("chat_result.html", {"request": request, "result": res, "disclaimer": DISCLAIMER})
    resp.set_cookie(ANON_ID_COOKIE, anon)
    return resp

@app.get("/timeline")
async def timeline(request: Request):
    anon = get_anon_id(request)
    entries = get_entries(anon, limit=100)
    resp = templates.TemplateResponse("timeline.html", {"request": request, "entries": entries, "disclaimer": DISCLAIMER})
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
    resp = templates.TemplateResponse("privacy.html", {"request": request, "disclaimer": DISCLAIMER})
    resp.set_cookie(ANON_ID_COOKIE, anon)
    return resp
