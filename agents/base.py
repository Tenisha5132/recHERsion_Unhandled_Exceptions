import json
import time

from config import BASE_DIR

TRACE_PATH = BASE_DIR / 'data' / 'agent_trace.jsonl'


def _one_line(value):
    return ' '.join(str(value or '').split())[:200]


def log_trace(agent, input_summary, output_summary, used_llm=False, ms=0, mode=None):
    TRACE_PATH.parent.mkdir(parents=True, exist_ok=True)
    if mode is None:
        mode = 'llm' if used_llm else 'rules'
    entry = {
        'agent': agent,
        'input_summary': _one_line(input_summary),
        'output_summary': _one_line(output_summary),
        'used_llm': bool(used_llm),
        'fallback': mode == 'fallback',
        'mode': mode,
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
            ms = int((time.time() - start) * 1000)
            used_llm = bool(res.get('used_llm', False))
            mode = res.get('mode') or ('llm' if used_llm else ('fallback' if res.get('llm_attempted') else 'rules'))
            log_trace(self.name, ctx.get('input_summary', ''), res.get('output_summary', res), used_llm=used_llm, ms=ms, mode=mode)
            res['agent'] = self.name
            res['mode'] = mode
            res['trace_ms'] = ms
            return res
        except Exception as e:
            ms = int((time.time() - start) * 1000)
            log_trace(self.name, ctx.get('input_summary', ''), f'ERR:{e}', used_llm=False, ms=ms, mode='fallback')
            return {'agent': self.name, 'error': str(e), 'used_llm': False, 'fallback': True,
                    'mode': 'fallback', 'trace_ms': ms, 'output_summary': f'ERR:{e}'}

    def _run(self, ctx):
        raise NotImplementedError
