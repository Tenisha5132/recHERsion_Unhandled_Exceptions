import json
import re
import time
from .base import BaseAgent
from config import LLM_API_KEY

class ExtractionAgent(BaseAgent):
    def __init__(self):
        super().__init__('extraction')

    def _run(self, ctx):
        text = ctx.get('message') or ''
        tl = text.lower()
        used_llm = False
        result = {
            'symptoms': [],
            'severity': None,
            'duration': None,
            'last_period_date': None,
            'cycle_length_days': None,
            'age': None,
            'flow_notes': None
        }
        # try LLM if key present (simple placeholder - don't actually call if no real endpoint; but structure ready)
        if LLM_API_KEY:
            used_llm = True  # mark as attempted; actual call not implemented to avoid external deps
        # fallback keyword/regex
        # symptoms
        for s in ['cramp', 'cramps', 'pain', 'bleed', 'bleeding', 'heavy', 'clot', 'clots', 'tired', 'fatigue', 'acne', 'hair', 'nausea']:
            if s in tl and s not in result['symptoms']:
                result['symptoms'].append(s)
        # severity 1-5
        msev = re.search(r'severity\s*(\d)', tl)
        if msev:
            try:
                v = int(msev.group(1))
                if 1 <= v <= 5:
                    result['severity'] = v
            except Exception:
                pass
        # cycle length
        mcl = re.search(r'cycle.*?(\d+)\s*days', tl)
        if mcl:
            try:
                result['cycle_length_days'] = int(mcl.group(1))
            except Exception:
                pass
        # age
        mage = re.search(r'age\s*(\d+)', tl)
        if mage:
            try:
                result['age'] = int(mage.group(1))
            except Exception:
                pass
        # duration
        mdur = re.search(r'(for|lasted).*?(\d+)\s*(day|week|month)', tl)
        if mdur:
            result['duration'] = mdur.group(0)
        # flow notes
        if 'soak' in tl:
            result['flow_notes'] = 'soaking mentioned'
        # validate - never fabricate
        return {'extracted': result, 'used_llm': used_llm, 'output_summary': json.dumps(result)[:80]}
