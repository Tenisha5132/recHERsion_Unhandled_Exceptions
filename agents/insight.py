import json
import re
from .base import BaseAgent
from .extraction import parse_cycle_length
from rules_loader import load_rules
from disclaimer import DISCLAIMER
from tracker import get_recent_entries

PATTERN_NONE = "No pattern flagged from what you've shared"
PATTERN_DISCUSS = "pattern worth discussing with a doctor"
NONE_DISCLAIMER = ("This app is for screening/awareness support only — not a medical diagnosis. "
                   "No pattern was flagged from what you've shared. If you have a medical emergency, "
                   "seek local emergency care immediately.")


def _number(value):
    try:
        if value is None or value == '':
            return None
        return float(value)
    except Exception:
        return None


def _fmt(value):
    value = _number(value)
    if value is None:
        return ''
    return str(int(value)) if value.is_integer() else str(round(value, 1))


def _cycles_from_extracted(extracted):
    values = []
    cl = _number(extracted.get('cycle_length_days'))
    if cl is not None:
        values.append(cl)
    for gap in extracted.get('gaps') or []:
        value = _number(gap)
        if value is not None:
            values.append(value)
    return values


def _entry_cycles(entry):
    extracted = entry.get('extracted_json')
    if isinstance(extracted, str):
        try:
            extracted = json.loads(extracted) or {}
        except Exception:
            extracted = {}
    if not isinstance(extracted, dict):
        extracted = {}
    values = _cycles_from_extracted(extracted)
    if not values:
        cycle_length, gaps = parse_cycle_length(entry.get('raw_text') or '')
        values = _cycles_from_extracted({'cycle_length_days': cycle_length, 'gaps': gaps})
    return values


def _recent_entries(ctx, current_extracted, message):
    entries = ctx.get('recent_entries')
    if not entries:
        try:
            entries = get_recent_entries(ctx.get('anon_id'), limit=5)
        except Exception:
            entries = []
    entries = list(entries or [])
    current = (message or '').strip()
    if not any((str(e.get('raw_text') or '').strip() == current) for e in entries):
        entries.insert(0, {'raw_text': message, 'extracted_json': json.dumps(current_extracted)})
    return entries


def _add_citation(citations, title, source_url):
    url = (source_url or '').strip()
    if not url:
        return
    if any(c.get('source_url') == url for c in citations):
        return
    citations.append({'title': title or url, 'source_url': url})


def _questions_for_doctor(matches, chunks, rules):
    questions = []
    if not matches:
        return questions

    def add(question):
        question = (question or '').strip()
        if question and question not in questions:
            questions.append(question)

    chunk_text = ' '.join(str(c.get('chunk') or '') for c in chunks).lower()
    keys = {m['key'] for m in matches}
    cycle_match = bool(keys & {'cycle_low', 'cycle_high'})
    heavy_match = bool(keys & {'heavy_soak', 'heavy_clot', 'heavy_flow'})

    if 'amenorrhoea' in keys:
        pregnancy = rules.get('pregnancy_test_suggestion') or {}
        if pregnancy.get('enabled') and ('pregnan' in chunk_text or not chunks):
            add('Ask your doctor whether a pregnancy test is appropriate.')

    if chunk_text and cycle_match:
        test_terms = []
        if re.search(r'\btsh\b', chunk_text):
            test_terms.append('TSH')
        if re.search(r'\bferritin\b', chunk_text):
            test_terms.append('ferritin')
        if re.search(r'hormone levels?|testosterone|androgen|insulin', chunk_text):
            test_terms.append('hormone levels')
        if test_terms:
            if len(test_terms) == 1:
                joined = test_terms[0]
            else:
                joined = ', '.join(test_terms[:-1]) + ' or ' + test_terms[-1]
            add(f'Ask your doctor whether tests such as {joined} are appropriate.')

    if chunk_text and heavy_match:
        if re.search(r'iron deficiency|anaemia|anemia|blood test', chunk_text):
            add('Ask your doctor whether a blood test for iron deficiency anaemia is appropriate.')

    return questions


class InsightAgent(BaseAgent):
    def __init__(self):
        super().__init__('insight')

    def _run(self, ctx):
        extracted = ctx.get('extracted') or {}
        chunks = ctx.get('retrieved_chunks') or []
        message = ctx.get('message') or ''
        rules = load_rules()
        matches = []

        def add_match(key, reason, meta, title):
            matches.append({'key': key, 'reason': reason, 'source_url': meta.get('source_url'), 'title': title})

        irregular = rules.get('irregular_cycle') or {}
        low_meta = irregular.get('gap_lt21_days') or {}
        high_meta = irregular.get('gap_gt35_days') or {}
        low = _number(low_meta.get('value'))
        high = _number(high_meta.get('value'))

        entries = _recent_entries(ctx, extracted, message)
        entry_values = [v for v in (_entry_cycles(e) for e in entries) if v]
        current_values = _cycles_from_extracted(extracted)
        if not current_values and entry_values:
            current_values = entry_values[0]
        total_entries = len(entry_values)

        low_entries = 0
        high_entries = 0
        if low is not None:
            low_entries = sum(1 for values in entry_values if any(v < low for v in values))
        if high is not None:
            high_entries = sum(1 for values in entry_values if any(v > high for v in values))

        if low is not None and low_entries:
            reason = f'cycle gap under {_fmt(low)} days'
            if low_entries > 1:
                reason += f', and it appears in {low_entries} of your last {total_entries} entries'
            add_match('cycle_low', reason, low_meta, low_meta.get('kb_file') or 'irregular cycle guidance')

        if high is not None and high_entries:
            reason = f'cycle gap over {_fmt(high)} days'
            if high_entries > 1:
                reason += f', and it appears in {high_entries} of your last {total_entries} entries'
            add_match('cycle_high', reason, high_meta, high_meta.get('kb_file') or 'irregular cycle guidance')

        heavy = rules.get('heavy_bleeding') or {}
        symptoms = [str(s).lower() for s in (extracted.get('symptoms') or [])]
        flow = str(extracted.get('flow_notes') or '').lower()
        soak_meta = heavy.get('soak_pad_tampon_hourly_2h') or {}
        clot_meta = heavy.get('passing_large_clots') or {}
        has_soak = 'soak' in flow
        has_clot = any('clot' in s for s in symptoms)
        has_heavy = any(s in ('heavy', 'bleed', 'bleeding') for s in symptoms)
        if has_soak and soak_meta:
            add_match('heavy_soak', 'soaking through pads or tampons', soak_meta, soak_meta.get('kb_file') or 'heavy bleeding guidance')
        if has_clot and clot_meta:
            add_match('heavy_clot', 'passing blood clots', clot_meta, clot_meta.get('kb_file') or 'heavy bleeding guidance')
        if has_heavy and heavy and not (has_soak or has_clot):
            add_match('heavy_flow', 'heavy bleeding mentioned', soak_meta, soak_meta.get('kb_file') or 'heavy bleeding guidance')

        amenorrhoea = rules.get('amenorrhoea') or {}
        missing_meta = amenorrhoea.get('definition_missing_3_months') or {}
        missing_months = _number(missing_meta.get('value'))
        no_period_months = _number(extracted.get('no_period_months'))
        if missing_months is not None and no_period_months is not None and no_period_months >= missing_months:
            reason = f'no period for {_fmt(no_period_months)} months'
            add_match('amenorrhoea', reason, missing_meta, missing_meta.get('kb_file') or 'amenorrhoea guidance')

        flag_level = 'discuss' if matches else 'none'
        reasons = [m['reason'] for m in matches]
        if flag_level == 'discuss':
            pattern = PATTERN_DISCUSS + ': ' + '; '.join(reasons)
        else:
            pattern = PATTERN_NONE

        citations = []
        for chunk in chunks:
            _add_citation(citations, chunk.get('title'), chunk.get('source_url'))
        for match in matches:
            _add_citation(citations, match.get('title'), match.get('source_url'))

        questions = _questions_for_doctor(matches, chunks, rules)

        output_summary = flag_level
        if reasons:
            output_summary = f'{flag_level}: {reasons[0]}'

        return {
            'flag_level': flag_level,
            'pattern': pattern,
            'reasoning': reasons,
            'citations': citations,
            'questions_for_doctor': questions,
            'disclaimer': DISCLAIMER if flag_level == 'discuss' else NONE_DISCLAIMER,
            'used_llm': False,
            'mode': 'rules',
            'output_summary': output_summary[:160]
        }
