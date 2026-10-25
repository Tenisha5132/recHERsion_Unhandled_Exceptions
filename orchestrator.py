try:
    from .base import BaseAgent
    from .router import RouterAgent
    from .safety import SafetyAgent
    from .extraction import ExtractionAgent
    from .retriever_agent import RetrieverAgent
    from .insight import InsightAgent
    from .remedy import RemedyAgent
    from .mood import MoodAgent
except Exception:
    from agents.base import BaseAgent
    from agents.router import RouterAgent
    from agents.safety import SafetyAgent
    from agents.extraction import ExtractionAgent
    from agents.retriever_agent import RetrieverAgent
    from agents.insight import InsightAgent
    from agents.remedy import RemedyAgent
    from agents.mood import MoodAgent
from tracker import save_entry


def _one_line(value):
    return ' '.join(str(value or '').split())[:200]


class Orchestrator:
    def __init__(self):
        self.router = RouterAgent()
        self.safety = SafetyAgent()
        self.extraction = ExtractionAgent()
        self.retriever = RetrieverAgent()
        self.insight = InsightAgent()
        self.remedy = RemedyAgent()
        self.mood = MoodAgent()

    def run(self, message, anon_id=None):
        ctx = {'message': message, 'input_summary': message, 'anon_id': anon_id}
        trace = []

        def add_trace(agent_name, inp, out, mode=None):
            out = out if isinstance(out, dict) else {}
            if mode is None:
                mode = out.get('mode') or ('llm' if out.get('used_llm') else 'rules')
            summary = out.get('output_summary')
            if not summary:
                summary = out.get('action') or out.get('category') or out.get('error') or ''
            trace.append({
                'agent': agent_name,
                'input_summary': _one_line(inp),
                'output_summary': _one_line(summary),
                'mode': mode,
                'ms': int(out.get('trace_ms') or 0)
            })

        r = self.router.run(ctx)
        ctx['route'] = r
        add_trace('router', message, r)

        s1 = self.safety.run(ctx)
        ctx['safety'] = s1
        ctx['safety1'] = s1
        add_trace('safety', message, s1)

        if s1.get('action') in ['urgent_override', 'distress_support']:
            override = 'urgent' if s1.get('action') == 'urgent_override' else 'distress'
            if s1.get('action') == 'urgent_override':
                try:
                    save_entry(anon_id, message, {})
                except Exception:
                    pass
            ctx['extracted'] = {}
            m = self.mood.run(ctx)
            add_trace('mood', message, m)
            s2 = self.safety.run(ctx)
            add_trace('safety_final', message, s2)
            return {'route': r, 'safety': s1, 'safety_final': s2, 'mood': m,
                    'override': override, 'trace': trace}

        e = self.extraction.run(ctx)
        ctx['extracted'] = e.get('extracted')
        add_trace('extraction', message, e)

        try:
            save_entry(anon_id, message, ctx['extracted'] or {})
        except Exception:
            pass

        ra = self.retriever.run(ctx)
        ctx['retrieved_chunks'] = ra.get('chunks')
        ctx['recent_entries'] = ra.get('recent_entries')
        add_trace('retriever', message, ra)

        i = self.insight.run(ctx)
        ctx['insight'] = i
        add_trace('insight', message, i)

        rem = self.remedy.run(ctx)
        add_trace('remedy', message, rem)

        m = self.mood.run(ctx)
        add_trace('mood', message, m)

        s2 = self.safety.run(ctx)
        add_trace('safety_final', message, s2)

        return {
            'route': r,
            'safety': s1,
            'extraction': e,
            'retriever': ra,
            'insight': i,
            'remedy': rem,
            'mood': m,
            'safety_final': s2,
            'trace': trace
        }
