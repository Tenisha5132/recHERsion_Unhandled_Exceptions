from .base import BaseAgent
from .safety import scrub_diagnostic
from llm_client import chat, is_available

LLM_SYSTEM_PROMPT = (
    'You are recHERsion, a cautious health information assistant. '
    'The app only cites a menstrual and reproductive health knowledge base. '
    'The user message is outside that sourced scope. Reply in at most 80 words. '
    'Do not diagnose, prescribe, give medicine doses, or invent sources. '
    'For a general health question, give brief general self-care and say when to seek care. '
    'For an unrelated question, say it is outside your scope and invite a menstrual or '
    'reproductive health question. Never attach period or gynaecology advice unless the '
    'message is actually about that topic.'
)

GENERAL_FALLBACK = (
    "I don't have a reliable source for this in my cited knowledge base, so I won't guess "
    "or attach unrelated advice. A pharmacist or GP can advise on general "
    "symptoms. Seek urgent care for trouble breathing, chest pain, fainting, or symptoms that "
    "are severe or getting worse."
)

OFF_TOPIC_FALLBACK = (
    "That is outside the menstrual and reproductive health topics I can answer from my cited "
    "sources. I can help with periods, cycle changes, bleeding, pelvic pain, PCOS or PMOS, "
    "endometriosis, thyroid, fertility, pregnancy and menopause questions."
)


class GeneralAgent(BaseAgent):
    def __init__(self):
        super().__init__('general')

    def _run(self, ctx):
        category = ((ctx.get('route') or {}).get('category') or '').strip()
        if category == 'off_topic':
            fallback = OFF_TOPIC_FALLBACK
        else:
            fallback = GENERAL_FALLBACK

        if is_available():
            reply = chat([
                {'role': 'system', 'content': LLM_SYSTEM_PROMPT},
                {'role': 'user', 'content': ctx.get('message') or ''},
            ], temperature=0.2, max_tokens=240)
            if reply:
                reply = scrub_diagnostic(reply)[:900].strip()
                return {
                    'reply': reply,
                    'used_llm': True,
                    'mode': 'llm',
                    'output_summary': f'{category or "general"} reply',
                }

        return {
            'reply': fallback,
            'used_llm': False,
            'mode': 'fallback' if is_available() else 'rules',
            'output_summary': f'{category or "general"} fallback',
        }
