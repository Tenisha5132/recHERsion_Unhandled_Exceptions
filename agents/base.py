import json
import os
import re
import time
from pathlib import Path

from config import BASE_DIR, LLM_API_KEY, LLM_MODEL, LLM_BASE_URL

TRACE_PATH = BASE_DIR / 'data' / 'agent_trace.jsonl'

def log_trace(agent, input_summary, output_summary, used_llm=False, ms=0):
    TRACE_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        'agent': agent,
        'input_summary': str(input_summary)[:200],
        'output_summary': str(output_summary)[:200],
        'used_llm': bool(used_llm),
        'fallback': not bool(used_llm),
        'ms': int(ms)
    }
    try:
        with open(TRACE_PATH, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry) + '\n')
    except Exception:
        pass
    return entry

class BaseAgent:
    def __init__(self, name):
        self.name = name

    def run(self, ctx):
        start = time.time()
        try:
            res = self._run(ctx)
            log_trace(self.name, ctx.get('input_summary',''), res.get('output_summary', res), used_llm=res.get('used_llm', False), ms=int((time.time()-start)*1000))
            res['agent'] = self.name
            res['trace_ms'] = int((time.time()-start)*1000)
            return res
        except Exception as e:
            log_trace(self.name, ctx.get('input_summary',''), f'ERR:{e}', used_llm=False, ms=int((time.time()-start)*1000))
            return {'agent': self.name, 'error': str(e), 'used_llm': False, 'fallback': True}

    def _run(self, ctx):
        raise NotImplementedError
