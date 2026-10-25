import time
from .base import BaseAgent

class RouterAgent(BaseAgent):
    def __init__(self):
        super().__init__('router')

    def _run(self, ctx):
        text = (ctx.get('message') or '').lower()
        # classify
        urgent_keywords = ['faint', 'pass out', 'soak.*hour', 'every hour.*2', 'severe.*pelvic.*pain', 'shortness of breath.*severe', 'chest pain']
        import re
        for k in urgent_keywords:
            if re.search(k, text):
                return {'category': 'urgent', 'output_summary': 'urgent keywords', 'used_llm': False}
        distress = ['suicide', 'kill myself', 'want to die', 'self harm', 'end my life']
        for d in distress:
            if d in text:
                return {'category': 'distress', 'output_summary': 'distress', 'used_llm': False}
        if any(w in text for w in ['period', 'bleed', 'cycle', 'cramp', 'pain', 'pcos', 'pmos']):
            return {'category': 'log_symptoms', 'output_summary': 'symptom related', 'used_llm': False}
        if any(w in text for w in ['what', 'why', 'how', 'info', 'explain']):
            return {'category': 'info_question', 'output_summary': 'info', 'used_llm': False}
        return {'category': 'log_symptoms', 'output_summary': 'default', 'used_llm': False}
