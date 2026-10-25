import time
import json
from .base import BaseAgent
from retriever import retriever
from tracker import get_recent_entries

class RetrieverAgent(BaseAgent):
    def __init__(self):
        super().__init__('retriever')

    def _run(self, ctx):
        message = ctx.get('message') or ''
        anon_id = ctx.get('anon_id')
        results = retriever.query(message, top_k=3)
        recent = []
        try:
            recent = get_recent_entries(anon_id, limit=5)
        except Exception:
            recent = []
        return {'chunks': results, 'recent_entries': recent, 'used_llm': False, 'output_summary': f'{len(results)} chunks'}
