import re
from .base import BaseAgent
from config import HELPLINE_NUMBER


def _norm(text):
    t = (text or '').lower().replace('\u2019', "'").replace('\u2018', "'")
    return re.sub(r'\s+', ' ', t)


_COUNT = r'(?:[2-9]|\d{2,}|two|three|four|five|six|seven|eight|several|many)'
_HOUR = r'(?:every|each|per|an?)\s*(?:hour|hr|30\s*min\w*|half\s*(?:an\s*)?hour)'

_BLEED = [
    r"\b(?:soak\w*|bleed\w*\s+through|go(?:ing)?\s+through|gone\s+through|chang\w+)\b.{0,40}\b(?:pads?|tampons?|cups?|liners?)\b.{0,40}\b" + _HOUR,
    r"\b(?:pads?|tampons?)\b.{0,30}\b" + _HOUR,
    r"\b" + _COUNT + r"\s+(?:\w+\s+)?(?:pads?|tampons?)\b.{0,30}\b(?:in|within|over|last|past)\s+(?:an?|the|\d+|two|three|four|couple\s+of|few)?\s*(?:hours?|hrs?)\b",
    r"\b(?:can'?t|cannot|won'?t|wont)\s+stop\s+bleeding\b",
    r"\bbleeding\s+(?:won'?t|wont|will\s+not|doesn'?t|isn'?t|is\s+not)\s+stop\w*",
    r"\bha?emorrhag\w*",
]
_FAINT = r"\b(?:fainted|fainting|passed\s+out|passing\s+out|pass\s+out|blacked\s+out|black\s+out|collapsed|lost\s+consciousness|about\s+to\s+faint|going\s+to\s+faint|feel(?:ing)?\s+faint)\b"
_CHEST = r"\bchest\s+(?:pain|tightness|pressure|hurts?)\b"
_BREATH = (r"\b(?:can'?t|cannot)\s+breathe\b|\bstruggling\s+to\s+breathe\b|\b(?:trouble|difficulty)\s+breathing\b"
           r"|\bsevere\s+short\w*\s+of\s+breath\b|\bvery\s+short\s+of\s+breath\b|\bgasping\b")
_HEAVY = r"(?:heav\w+|a\s+lot|so\s+much|too\s+much|profuse|gushing|flooding)"
_DIZZY = r"\b(?:dizz\w+|light-?\s?headed|weak|pale|breathless)\b"
_INTENSE = r"\b(?:severe|sharp|stabbing|intense|unbearable|terrible|worst|excruciating)\b"

_DISTRESS = [
    r"\bsuicid\w*",
    r"\bwant(?:ed)?\s+to\s+die\b",
    r"\b(?:don'?t|do\s+not|dont|no\s+longer)\s+want\s+to\s+(?:live|be\s+alive|be\s+here|exist|wake\s+up)\b",
    r"\bend\s+(?:it\s+all|my\s+life|everything)\b",
    r"\bending\s+(?:it\s+all|my\s+life)\b",
    r"\b(?:hurt|harm|cut|cutting|injure|kill)\s+my\s*self\b",
    r"\bself[\s-]?harm\w*",
    r"\bno\s+(?:reason|point)\s+(?:to|in)\s+(?:live|living|going\s+on)\b",
    r"\bbetter\s+off\s+(?:dead|without\s+me)\b",
    r"\bwish\s+i\s+(?:was|were)\s+(?:dead|never\s+born)\b",
    r"\bcan'?t\s+go\s+on\b",
    # Hinglish
    r"\bmar\s*(?:jana|jaana|na)\s+(?:chahti|chahta)\b",
    r"\bjee?n[ae]\s+(?:nahi|nahin|nhi)\s+(?:chahti|chahta)\b",
    r"\bjee?ne\s+ka\s+(?:mann?|mood)\s+(?:nahi|nahin|nhi)\b",
    r"\bkhud\s*ko\s+(?:khatam|nuksan)\b",
]

_LABELS = {
    'heavy_bleeding': 'very heavy bleeding',
    'heavy_bleeding_with_dizziness': 'heavy bleeding with dizziness or weakness',
    'fainting': 'fainting or collapsing',
    'sudden_severe_pain': 'sudden severe pelvic or abdominal pain',
    'breathing': 'difficulty breathing',
    'chest_pain': 'chest pain or pressure',
}


def detect_red_flags(t):
    flags = []
    if any(re.search(p, t) for p in _BLEED):
        flags.append('heavy_bleeding')
    elif (re.search(r"\bbleed\w*\b.{0,30}\b" + _HEAVY + r"|\b" + _HEAVY + r"\b.{0,30}\bbleed\w*", t)
          and re.search(_DIZZY, t)):
        flags.append('heavy_bleeding_with_dizziness')
    if re.search(_FAINT, t):
        flags.append('fainting')
    if (re.search(r"\b(?:sudden|suddenly|out\s+of\s+nowhere)\b", t)
            and re.search(_INTENSE, t)
            and re.search(r"\b(?:pain|cramp\w*|ache)\b", t)
            and re.search(r"\b(?:pelvi\w*|abdom\w*|belly|stomach|tummy|side)\b", t)):
        flags.append('sudden_severe_pain')
    if re.search(_BREATH, t):
        flags.append('breathing')
    if re.search(_CHEST, t):
        flags.append('chest_pain')
    return flags


_DIAG = re.compile(
    r"\byou\s+(?:definitely\s+|probably\s+|likely\s+)?(?:have|are\s+suffering\s+from|suffer\s+from)\s+"
    r"(?:pcos|pmos|endometriosis|hypothyroidism|an?a?emia|diabetes|a\s+thyroid\s+(?:problem|condition))\b",
    re.I)


def scrub_diagnostic(text):
    """Final-pass filter: soften any diagnostic claim in text written by other agents."""
    return _DIAG.sub("Your symptoms may fit a pattern worth discussing with a doctor (not a diagnosis)", text or '')


def _helpline_line():
    h = str(HELPLINE_NUMBER or '').strip()
    if not h or 'TODO' in h.upper():
        return ''
    return f" You can also call {h}."


class SafetyAgent(BaseAgent):
    def __init__(self):
        super().__init__('safety')

    def _run(self, ctx):
        t = _norm(ctx.get('message'))
        flags = detect_red_flags(t)
        distress = any(re.search(p, t) for p in _DISTRESS)

        if distress:
            msg = ("I'm really sorry you're feeling this way, and I'm glad you said it. You don't have to carry this alone. "
                   "Please reach out to someone you trust right now: a friend, a family member or a counsellor. "
                   "If you think you might act on these thoughts or you feel unsafe, call your local emergency number "
                   "(112 in India) or go to the nearest emergency department." + _helpline_line())
            if flags:
                msg += (" If you also have heavy bleeding, fainting, or trouble breathing, "
                        "please get emergency medical care too.")
            return {'action': 'distress_support', 'red_flags': flags, 'message': msg,
                    'output_summary': 'distress', 'used_llm': False, 'mode': 'rules'}

        if flags:
            what = ', '.join(_LABELS[f] for f in flags)
            msg = (f"This could be serious. You mentioned {what}. Please get medical help now: go to the nearest "
                   "emergency department or call your local emergency number (112 in India). If you feel faint, "
                   "don't go alone. This app is screening and awareness support only. It cannot diagnose or treat.")
            return {'action': 'urgent_override', 'red_flags': flags, 'message': msg,
                    'output_summary': 'urgent: ' + ','.join(flags), 'used_llm': False, 'mode': 'rules'}

        return {'action': 'ok', 'output_summary': 'no red flags', 'used_llm': False, 'mode': 'rules'}
