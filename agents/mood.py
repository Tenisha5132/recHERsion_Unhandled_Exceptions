import re
import random
from .base import BaseAgent

JOKES = [
    "A cold is a good excuse for an early night.",
    "Tired days are allowed; a nap can be the plan.",
    "Warm drinks and a blanket are a fine combo.",
    "Even a sniffly day can be a slow day.",
    "Rest now, and let tomorrow be the busy one.",
    "A small cold deserves a small break.",
]

_CYCLE_OR_PAIN = re.compile(
    r'\b(period|periods|menstrual|cycle|cycles|bleed|bleeding|blood|'
    r'pain|painful|cramp|cramps|ache|aches|aching)\b',
    re.I)
_LOW = re.compile(
    r'\b(sad|sadness|stress|stressed|stressful|anxious|anxiety|overwhelm\w*|'
    r'low mood|depress\w*|lonely|upset)\b',
    re.I)


class MoodAgent(BaseAgent):
    def __init__(self):
        super().__init__('mood')

    def _run(self, ctx):
        extracted = ctx.get('extracted') or {}
        safety = ctx.get('safety') or ctx.get('safety1') or {}
        message = ctx.get('message') or ''
        symptoms = [str(s).lower() for s in (extracted.get('symptoms') or [])]
        severity = extracted.get('severity')
        severity_value = severity if isinstance(severity, (int, float)) else 0

        safety_clear = safety.get('action', 'ok') == 'ok' and not safety.get('red_flags')
        has_cycle_or_pain = bool(_CYCLE_OR_PAIN.search(message))
        if any(s in symptoms for s in ['pain', 'cramp', 'cramps', 'bleed', 'bleeding', 'heavy']):
            has_cycle_or_pain = True

        if not safety_clear:
            return {'theme': 'support', 'emoji': '🫂', 'joke': None, 'used_llm': False,
                    'mode': 'rules', 'output_summary': 'supportive, no joke'}

        mild_context = (
            any(term in message.lower() for term in ['cold', 'tired', 'sniff', 'rest', 'nap'])
            or any(s in symptoms for s in ['tired', 'fatigue', 'cold'])
        )

        if severity_value <= 2 and mild_context and not has_cycle_or_pain:
            joke = random.choice(JOKES)
            return {'theme': 'cheerful', 'emoji': '☕', 'joke': joke, 'used_llm': False,
                    'mode': 'rules', 'output_summary': 'mild joke'}

        if _LOW.search(message):
            return {'theme': 'low', 'emoji': '🫂', 'joke': None, 'used_llm': False,
                    'mode': 'rules', 'output_summary': 'low mood, no joke'}

        if has_cycle_or_pain:
            return {'theme': 'calm', 'emoji': '🌙', 'joke': None, 'used_llm': False,
                    'mode': 'rules', 'output_summary': 'cycle/pain content, no joke'}

        if severity_value >= 3:
            return {'theme': 'gentle', 'emoji': '🌥️', 'joke': None, 'used_llm': False,
                    'mode': 'rules', 'output_summary': 'gentle, no joke'}

        if mild_context:
            return {'theme': 'rest', 'emoji': '🧣', 'joke': None, 'used_llm': False,
                    'mode': 'rules', 'output_summary': 'restful, no joke'}

        return {'theme': 'neutral', 'emoji': '💬', 'joke': None, 'used_llm': False,
                'mode': 'rules', 'output_summary': 'neutral, no joke'}
