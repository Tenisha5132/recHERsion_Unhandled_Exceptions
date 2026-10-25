import time
import random
from .base import BaseAgent

JOKES = [
    "Tea counts as self care.",
    "Pajamas are valid attire today.",
    "A good blanket is solid medical equipment.",
    "Hydration: water is free, worth it.",
    "Rest is productive too.",
    "Socks with personality are a win."
]

class MoodAgent(BaseAgent):
    def __init__(self):
        super().__init__('mood')

    def _run(self, ctx):
        extracted = ctx.get('extracted') or {}
        safety = ctx.get('safety') or {}
        symptoms = [str(s).lower() for s in (extracted.get('symptoms') or [])]
        severity = extracted.get('severity') or 0
        # never joke if safety flagged urgent/distress
        if safety.get('action') in ['urgent_override', 'distress_support']:
            return {'theme': 'neutral', 'emoji': '', 'joke': None, 'used_llm': False, 'output_summary': 'no joke'}
        # only mild non-pain tags
        mild = any(s in symptoms for s in ['tired', 'cold']) and not any(s in symptoms for s in ['pain', 'cramp', 'bleed', 'heavy'])
        if mild and severity <= 2:
            joke = random.choice(JOKES)
            return {'theme': 'calm', 'emoji': '☕', 'joke': joke, 'used_llm': False, 'output_summary': 'joke'}
        return {'theme': 'neutral', 'emoji': '', 'joke': None, 'used_llm': False, 'output_summary': 'no joke'}
