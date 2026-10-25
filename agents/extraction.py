import json
import re
import statistics
from .base import BaseAgent
from config import LLM_API_KEY


def _norm(text):
    t = (text or '').lower()
    t = t.replace('\u2019', "'").replace('\u2018', "'")
    t = t.replace('\u2013', '-').replace('\u2014', '-')
    return re.sub(r'\s+', ' ', t)


def _number(value):
    try:
        if value is None or value == '':
            return None
        return float(value)
    except Exception:
        return None


def _clean_num(value):
    if value is None:
        return None
    return int(value) if float(value).is_integer() else round(float(value), 1)


def _median(values):
    if not values:
        return None
    return _clean_num(statistics.median(values))


def _overlaps(span, blocked):
    start, end = span
    return any(not (end <= b_start or start >= b_end) for b_start, b_end in blocked)


def _has_cycle_context(text):
    return bool(re.search(r'\b(cycle|cycles|gap|gaps|period|periods|interval|intervals|every|apart|after|between)\b', text))


def parse_cycle_length(text):
    tl = _norm(text)
    gaps = []
    blocked = []

    def add(value):
        if value is None:
            return
        value = _clean_num(value)
        if 5 <= value <= 400:
            gaps.append(value)

    for m in re.finditer(r'\b(\d{1,3})\s*(?:-|to)\s*(\d{1,3})\s*(days?|weeks?)\b', tl):
        context = tl[max(0, m.start() - 50):m.end() + 50]
        if not _has_cycle_context(context):
            continue
        multiplier = 7 if m.group(3).startswith('week') else 1
        add(int(m.group(1)) * multiplier)
        add(int(m.group(2)) * multiplier)
        blocked.append((m.start(), m.end()))

    for m in re.finditer(r'\b(\d{1,3}(?:(?:\s*,\s*|\s+and\s+|\s*&\s*)\d{1,3})+)\s*(days?|weeks?)\b', tl):
        if _overlaps((m.start(), m.end()), blocked):
            continue
        context = tl[max(0, m.start() - 50):m.end() + 50]
        if not _has_cycle_context(context):
            continue
        multiplier = 7 if m.group(2).startswith('week') else 1
        for value in re.findall(r'\d{1,3}', m.group(1)):
            add(int(value) * multiplier)
        blocked.append((m.start(), m.end()))

    for m in re.finditer(r'\b(\d{1,3})\s*(?:weeks?|wks?)\b', tl):
        if _overlaps((m.start(), m.end()), blocked):
            continue
        context = tl[max(0, m.start() - 50):m.end() + 50]
        if not _has_cycle_context(context):
            continue
        add(int(m.group(1)) * 7)
        blocked.append((m.start(), m.end()))

    single_patterns = [
        r'\b(\d{1,3})\s*days?\s*apart\b',
        r'\bevery\s+(\d{1,3})\s*days?\b',
        r'\b(\d{1,3})\s*days?\s*(?:cycle|cycles|gap|gaps|between periods|interval)\b',
        r'\b(?:cycle|cycles|gap|gaps|interval)\b[^.\d]{0,30}?(\d{1,3})\s*days?\b',
        r'\bafter\s+(\d{1,3})\s*days?\b',
    ]
    for pattern in single_patterns:
        for m in re.finditer(pattern, tl):
            if _overlaps((m.start(), m.end()), blocked):
                continue
            add(int(m.group(1)))
            blocked.append((m.start(), m.end()))

    return _median(gaps), gaps


def _months_without_period(tl):
    patterns = [
        r"(?:haven'?t|hasn'?t|have not|has not|no)\s+(?:had\s+)?(?:a\s+)?period\s+(?:for|in|since)\s+(\d{1,2})\s*(day|week|month)s?",
        r"(?:missed|no)\s+(?:a\s+)?periods?\s+(?:for|in)\s+(\d{1,2})\s*(day|week|month)s?",
        r"(?:no\s+period|missed\s+period)\s+(?:for\s+)?(\d{1,2})\s*(day|week|month)s?",
    ]
    for pattern in patterns:
        m = re.search(pattern, tl)
        if m:
            value = int(m.group(1))
            unit = m.group(2)
            if unit == 'day':
                return round(value / 30.0, 1)
            if unit == 'week':
                return round(value / 4.345, 1)
            return value
    return None


class ExtractionAgent(BaseAgent):
    def __init__(self):
        super().__init__('extraction')

    def _run(self, ctx):
        text = ctx.get('message') or ''
        tl = _norm(text)
        result = {
            'symptoms': [],
            'severity': None,
            'duration': None,
            'last_period_date': None,
            'cycle_length_days': None,
            'gaps': [],
            'no_period_months': None,
            'age': None,
            'flow_notes': None
        }

        for s in ['cramp', 'cramps', 'pain', 'bleed', 'bleeding', 'heavy', 'clot', 'clots', 'tired', 'fatigue', 'acne', 'hair', 'nausea']:
            if s in tl and s not in result['symptoms']:
                result['symptoms'].append(s)

        msev = re.search(r'severity\s*(\d)', tl)
        if msev:
            try:
                v = int(msev.group(1))
                if 1 <= v <= 5:
                    result['severity'] = v
            except Exception:
                pass

        cycle_length, gaps = parse_cycle_length(text)
        result['cycle_length_days'] = cycle_length
        result['gaps'] = gaps
        result['no_period_months'] = _months_without_period(tl)

        mage = re.search(r'(?:age\s*|\bi\'?m\s+|\bi\s+am\s+)(\d{1,2})\b', tl)
        if mage:
            try:
                result['age'] = int(mage.group(1))
            except Exception:
                pass

        mdur = re.search(r'(for|lasted).*?(\d+)\s*(day|week|month)', tl)
        if mdur:
            result['duration'] = mdur.group(0)

        if 'soak' in tl:
            result['flow_notes'] = 'soaking mentioned'

        llm_attempted = bool(LLM_API_KEY)
        mode = 'fallback' if llm_attempted else 'rules'
        return {
            'extracted': result,
            'used_llm': False,
            'llm_attempted': llm_attempted,
            'mode': mode,
            'output_summary': json.dumps(result)[:160]
        }
