import time
import re
from .base import BaseAgent
from config import HELPLINE_NUMBER

class SafetyAgent(BaseAgent):
    def __init__(self):
        super().__init__('safety')

    def _run(self, ctx):
        text = (ctx.get('message') or '')
        tl = text.lower()
        # check red flags
        red_flags = []
        # soaking hourly for 2+ hours
        if re.search(r'soak.*(pad|tampon).*every.*hour', tl) and re.search(r'(2|two).*hour', tl):
            red_flags.append('soaking_hourly_2h')
        elif re.search(r'change.*pad.*every.*hour', tl) and ('2' in tl or 'two' in tl):
            red_flags.append('soaking_hourly_2h')
        if 'faint' in tl or 'pass out' in tl or 'passed out' in tl:
            red_flags.append('fainting_or_dizzy')
        if re.search(r'severe.*(sudden.*pelvic|pelvic.*pain)', tl):
            red_flags.append('severe_sudden_pelvic_pain')
        if re.search(r'severe.*shortness of breath|can\'t breathe.*severe', tl):
            red_flags.append('severe_shortness_of_breath')
        if 'chest pain' in tl:
            red_flags.append('chest_pain')
        if red_flags:
            msg = f"URGENT: This pattern may need immediate medical care. Red flags detected: {', '.join(red_flags)}. Seek local emergency care now. This app is screening/awareness support only — not a diagnosis."
            return {'action': 'urgent_override', 'red_flags': red_flags, 'message': msg, 'output_summary': 'urgent', 'used_llm': False}
        # distress
        distress = ['suicide', 'kill myself', 'want to die', 'self harm', 'end my life']
        if any(d in tl for d in distress):
            msg = f"I'm really sorry you're going through this. You don't have to face this alone. Please reach out to a trusted person or local emergency services/helpline. Helpline: {HELPLINE_NUMBER} (TODO_VERIFY). This is a supportive message, not medical advice."
            return {'action': 'distress_support', 'message': msg, 'output_summary': 'distress', 'used_llm': False}
        # strip diagnostic claims from other outputs if present
        return {'action': 'ok', 'output_summary': 'safe', 'used_llm': False}
