import re
from .base import BaseAgent
from disclaimer import DISCLAIMER

_MEDICATION = re.compile(
    r'\b(medicine|medicines|medication|medications|tablet|tablets|pill|pills|'
    r'contracept\w*|tranexamic|painkiller\w*|anti[- ]inflammatory|levothyroxine|'
    r'metformin|dose|doses|dosage|mg|surgery|surgical|hysterectomy|oophorectomy|'
    r'antibiotic\w*|hormonal treatment\w*|treatment\w*)\b',
    re.I)
_TRACKING = re.compile(r'\b(track|tracking|diary|log|logging|monitor|record|app of periods)\b', re.I)
_SELF_CARE = re.compile(
    r'\b(self[- ]care|lifestyle|healthy (?:diet|eating)|balanced diet|'
    r'(?:regular|gentle|daily|moderate) exercise|weight (?:loss|management)|'
    r'support for mental health|(?:get enough|good quality|prioriti[sz]e) sleep|'
    r'manage (?:stress|anxiety)|reduce stress)\b',
    re.I)
_ADVICE = re.compile(
    r'\b(can help|may help|helps?|helping|try|consider|aim|keep|maintain|'
    r'make sure|should|recommended|important|measures?)\b',
    re.I)
_SEE_GP = re.compile(
    r'\b(see a gp|see your gp|speak to a gp|speak to your gp|talk to a gp|'
    r'talk to your gp|contact a gp|contact your gp|should speak to a gp|'
    r'medical help|seek help|go to the nearest|call your local emergency|'
    r'speak to a doctor|talk to a doctor)\b',
    re.I)


def _sentences(text):
    clean = re.sub(r'\s+', ' ', text or '').strip()
    return [s.strip() for s in re.split(r'(?<=[.!?])\s+', clean) if s.strip()]


def _usable_sentences(text):
    parts = _sentences(text)
    for index, sentence in enumerate(parts):
        if index == 0 and not re.match(r'[A-Z0-9]', sentence):
            continue
        if not re.search(r'[.!?]$', sentence):
            continue
        yield sentence


def _category(sentence):
    if _MEDICATION.search(sentence):
        return None
    if _TRACKING.search(sentence):
        return 'tracking'
    if _SEE_GP.search(sentence):
        return 'when to see a GP'
    if _SELF_CARE.search(sentence) and (_ADVICE.search(sentence) or re.search(r'lifestyle|self[- ]care', sentence, re.I)):
        return 'self-care'
    return None


def _grouped_sources(chunks):
    groups = {}
    order = []
    for chunk in chunks:
        key = chunk.get('source_file') or chunk.get('source_url') or chunk.get('title')
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(chunk)
    for key in order:
        items = sorted(groups[key], key=lambda c: c.get('chunk_idx', 0))
        text = ' '.join(str(c.get('chunk') or '') for c in items)
        yield items[0], text


class RemedyAgent(BaseAgent):
    def __init__(self):
        super().__init__('remedy')

    def _run(self, ctx):
        chunks = ctx.get('retrieved_chunks') or []
        advice = []
        seen = set()
        citations = []

        for chunk, text in _grouped_sources(chunks):
            title = chunk.get('title')
            source_url = chunk.get('source_url')
            for sentence in _usable_sentences(text):
                category = _category(sentence)
                if not category:
                    continue
                sentence = sentence[:1].upper() + sentence[1:]
                key = sentence.lower()
                if key in seen:
                    continue
                seen.add(key)
                advice.append({
                    'text': sentence,
                    'category': category,
                    'title': title,
                    'source_url': source_url
                })
                if source_url and not any(c.get('source_url') == source_url for c in citations):
                    citations.append({'title': title or source_url, 'source_url': source_url})
                if len(advice) >= 6:
                    break
            if len(advice) >= 6:
                break

        return {
            'advice': advice,
            'citations': citations,
            'disclaimer': DISCLAIMER,
            'used_llm': False,
            'mode': 'rules',
            'output_summary': f'{len(advice)} KB tips' if advice else 'no KB self-care tips'
        }
