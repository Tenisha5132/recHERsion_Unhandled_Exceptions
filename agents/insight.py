import time
import json
from .base import BaseAgent
from rules_loader import load_rules
from disclaimer import DISCLAIMER

class InsightAgent(BaseAgent):
    def __init__(self):
        super().__init__('insight')

    def _run(self, ctx):
        extracted = ctx.get('extracted') or {}
        chunks = ctx.get('retrieved_chunks') or []
        message = (ctx.get('message') or '').lower()
        rules = load_rules()
        flag_level = 'none'
        pattern = 'pattern worth discussing with a doctor'
        reasoning = []
        citations = []
        questions = []
        # check cycle
        cl = extracted.get('cycle_length_days')
        if cl is not None:
            try:
                clv = int(cl)
                if clv < 21:
                    flag_level = 'discuss'
                    reasoning.append(f'Cycle length {clv} days < 21 days per NHS irregular periods guidance.')
                elif clv > 35:
                    flag_level = 'discuss'
                    reasoning.append(f'Cycle length {clv} days > 35 days per NHS irregular periods guidance.')
            except Exception:
                pass
        # keywords
        if any(k in message for k in ['pcos', 'pmos', 'facial hair', 'hirsutism']):
            flag_level = 'discuss'
            reasoning.append('Features that can be associated with PMOS/PCOS per guidance - pattern worth discussing with a doctor.')
        if any(k in message for k in ['endometriosis', 'pain during sex', 'severe period pain']):
            flag_level = 'discuss'
            reasoning.append('Symptoms that may relate to endometriosis per guidance - pattern worth discussing with a doctor.')
        if any(k in message for k in ['thyroid', 'tired all the time', 'cold all the time', 'gaining weight']):
            flag_level = 'discuss'
            reasoning.append('Symptoms that may relate to thyroid function per guidance - pattern worth discussing with a doctor.')
        if any(k in message for k in ['heavy', 'clot', 'soak', 'pad every hour', 'longer than 7 days']):
            if flag_level == 'none':
                flag_level = 'discuss'
            reasoning.append('Heavy bleeding features noted per NHS heavy periods guidance - pattern worth discussing with a doctor.')
        if any(k in message for k in ['haven\'t had a period', 'no period', 'missed period']) or (extracted.get('duration') and 'month' in str(extracted.get('duration')).lower()):
            flag_level = 'discuss' if flag_level == 'none' else flag_level
            questions.append('Ask your doctor whether a pregnancy test is appropriate (if relevant).')
            reasoning.append('Missed/absent periods noted - pattern worth discussing with a doctor.')
        # age-aware
        age = extracted.get('age')
        if age is not None and age < 16 and flag_level == 'discuss' and any(k in message for k in ['just started', 'young']):
            reasoning.append('Age-aware: cycles can be irregular for the first 1-2 years after periods start (adolescent note).')
            flag_level = 'none'  # be conservative per note
        # citations
        for c in chunks[:3]:
            citations.append({'title': c.get('title'), 'source_url': c.get('source_url')})
        if not citations:
            return {'flag_level': 'none', 'pattern': pattern, 'reasoning': ['no guidance found'], 'citations': [], 'questions_for_doctor': questions, 'disclaimer': DISCLAIMER, 'used_llm': False, 'output_summary': 'no guidance'}
        out = {
            'flag_level': flag_level,
            'pattern': pattern,
            'reasoning': reasoning or ['Pattern worth discussing with a doctor based on retrieved guidance.'],
            'citations': citations,
            'questions_for_doctor': questions,
            'disclaimer': DISCLAIMER,
            'used_llm': False,
            'output_summary': flag_level
        }
        return out
