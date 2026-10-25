import re

from .base import BaseAgent
from llm_client import chat_json, is_available

URGENT_PATTERNS = [
    r'\bfaint\w*\b',
    r'\bpass(?:ed)?\s+out\b',
    r'\bsoak\w*\b.{0,40}\b(?:pad|tampon)\w*\b.{0,40}\b(?:every|an?|per)\s*hour\b',
    r'\bsevere\b.{0,30}\bpelvic\b.{0,30}\bpain\b',
    r'\b(?:can\'?t|cannot)\s+breathe\b',
    r'\bsevere\s+shortness\s+of\s+breath\b',
    r'\bchest\s+(?:pain|tightness|pressure)\b',
]

DISTRESS_PATTERNS = [
    r'\bsuicid\w*',
    r'\bkill\s+my\s*self\b',
    r'\bwant(?:ed)?\s+to\s+die\b',
    r'\bself[\s-]?harm\w*',
    r'\bend\s+my\s+life\b',
    r'\bmar\s*(?:jana|jaana|na)\s+(?:chahti|chahta)\b',
    r'\bjee?n[ae]\s+(?:nahi|nahin|nhi)\s+(?:chahti|chahta)\b',
]

DOMAIN_PATTERN = re.compile(
    r'\b(?:periods?|menstrual|menstruation|cycles?|spotting|bleed\w*|clots?|'
    r'cramps?|pelvic|ovary|ovarian|uterus|uterine|womb|pcos|pmos|endometriosis|'
    r'fibroids?|thyroid|hormon\w*|fertility|infertility|pregnan\w*|menopaus\w*|'
    r'perimenopaus\w*|contracept\w*|discharge|vagina\w*|vulva\w*|breasts?|'
    r'mammogram|cervical|pap\s*smear|hysterectomy|pms|pmdd|libido|hirsutism|'
    r'dyspareunia|intercourse)\b',
    re.I,
)

GENERAL_HEALTH_PATTERN = re.compile(
    r'\b(?:cold|colds|cough\w*|fever|flu|throat|headache\w*|migraine\w*|'
    r'nausea|vomit\w*|diarrh\w*|constipat\w*|rash\w*|allerg\w*|injur\w*|'
    r'sprain\w*|fracture\w*|tooth\w*|dental|earache\w*|eye|back\s+pain|joint\w*|'
    r'knee|stomach|indigestion|heartburn|acne|tired|fatigue\w*|exhaust\w*|'
    r'dizz\w*|sleep|insomnia|stress\w*|anxious|anxiety|low\s+mood|depress\w*|'
    r'sad|lonely)\b',
    re.I,
)

LLM_SYSTEM_PROMPT = (
    'You classify one message for a menstrual and reproductive health support app. '
    'Return ONLY JSON like {"category":"womens_health"}. '
    'Use womens_health for periods, cycles, bleeding, pelvic pain, hormones, fertility, '
    'pregnancy, menopause, breasts, or reproductive concerns. '
    'Use general_health for non-reproductive health such as cold, cough, fever, headache, '
    'injury, sleep or mood. Use off_topic for anything else. Do not diagnose.'
)


def _llm_category(text):
    if not is_available():
        return None
    data = chat_json([
        {'role': 'system', 'content': LLM_SYSTEM_PROMPT},
        {'role': 'user', 'content': text},
    ], max_tokens=80)
    if not data:
        return None
    category = str(data.get('category') or '').strip().lower()
    if category in ('womens_health', 'general_health', 'off_topic'):
        return category
    return None


class RouterAgent(BaseAgent):
    def __init__(self):
        super().__init__('router')

    def _run(self, ctx):
        text = (ctx.get('message') or '').strip()
        lowered = text.lower()

        for pattern in URGENT_PATTERNS:
            if re.search(pattern, lowered):
                return {'category': 'urgent', 'output_summary': 'urgent keywords', 'mode': 'rules'}
        for pattern in DISTRESS_PATTERNS:
            if re.search(pattern, lowered):
                return {'category': 'distress', 'output_summary': 'distress keywords', 'mode': 'rules'}

        if DOMAIN_PATTERN.search(lowered):
            return {'category': 'womens_health', 'output_summary': 'reproductive health topic', 'mode': 'rules'}
        if GENERAL_HEALTH_PATTERN.search(lowered):
            return {'category': 'general_health', 'output_summary': 'general health topic', 'mode': 'rules'}

        category = _llm_category(text)
        if category:
            return {'category': category, 'output_summary': f'llm: {category}', 'used_llm': True, 'mode': 'llm'}

        return {'category': 'off_topic', 'output_summary': 'outside health scope', 'mode': 'rules'}
