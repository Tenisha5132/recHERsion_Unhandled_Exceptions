from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from tracker import get_entries
from config import BASE_DIR
from disclaimer import DISCLAIMER
from datetime import datetime

def generate_summary(anon_id):
    entries = get_entries(anon_id, limit=100)
    out = BASE_DIR / 'data' / 'doctor_summary.pdf'
    out.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(out), pagesize=letter)
    width, height = letter
    y = height - 40
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, y, "recHERsion - Clinician Summary (De-identified)")
    y -= 20
    c.setFont("Helvetica", 9)
    c.drawString(40, y, f"Generated: {datetime.now().isoformat()}")
    y -= 15
    c.drawString(40, y, "SCREENING SUPPORT ONLY — NOT DIAGNOSIS")
    y -= 25
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, y, "Timeline of logged symptoms")
    y -= 15
    c.setFont("Helvetica", 8)
    for e in entries[:30]:
        txt = (e.get('raw_text') or '')[:80]
        c.drawString(40, y, f"- {e.get('created_at')} | {txt}")
        y -= 12
        if y < 60:
            c.showPage()
            y = height - 40
    y -= 10
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, y, "Flagged patterns / Suggested questions for doctor")
    y -= 15
    c.setFont("Helvetica", 8)
    c.drawString(40, y, "- Ask whether evaluation for PMOS/PCOS, thyroid, iron deficiency is appropriate (if symptoms fit).")
    y -= 12
    c.drawString(40, y, "- Ask about pregnancy test if missed periods apply.")
    y -= 12
    c.drawString(40, y, "- For heavy bleeding/red flags, ask about urgent evaluation.")
    y -= 25
    c.setFont("Helvetica-Oblique", 7)
    c.drawString(40, y, DISCLAIMER)
    c.save()
    return str(out)
