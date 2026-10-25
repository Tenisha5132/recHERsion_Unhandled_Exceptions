import time
from .base import BaseAgent
from disclaimer import DISCLAIMER

class RemedyAgent(BaseAgent):
    def __init__(self):
        super().__init__('remedy')

    def _run(self, ctx):
        chunks = ctx.get('retrieved_chunks') or []
        # only safe self-care from KB
        advice = []
        advice.append('Track your periods/symptoms (dates, flow, pain) - tracking can help discuss patterns with a GP.')
        advice.append('Rest and prioritize sleep when tired.')
        advice.append('If symptoms affect daily life, consider speaking to a GP.')
        citations = []
        for c in chunks[:2]:
            citations.append({'title': c.get('title'), 'source_url': c.get('source_url')})
        return {'advice': advice, 'citations': citations, 'disclaimer': DISCLAIMER, 'used_llm': False, 'output_summary': 'safe advice'}
