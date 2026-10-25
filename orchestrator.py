import time
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
        # router
        r = self.router.run(ctx)
        ctx['route'] = r
        # safety first
        s1 = self.safety.run(ctx)
        ctx['safety1'] = s1
        if s1.get('action') == 'urgent_override':
            # still save minimal entry? but override
            try:
                save_entry(anon_id, message, {})
            except Exception:
                pass
            # safety last
            s2 = self.safety.run(ctx)
            return {'route': r, 'safety': s1, 'safety_final': s2, 'override': 'urgent'}
        if s1.get('action') == 'distress_support':
            try:
                save_entry(anon_id, message, {})
            except Exception:
                pass
            s2 = self.safety.run(ctx)
            return {'route': r, 'safety': s1, 'safety_final': s2, 'override': 'distress'}
        # normal flow
        e = self.extraction.run(ctx)
        ctx['extracted'] = e.get('extracted')
        try:
            save_entry(anon_id, message, ctx['extracted'] or {})
        except Exception:
            pass
        ra = self.retriever.run(ctx)
        ctx['retrieved_chunks'] = ra.get('chunks')
        ctx['recent_entries'] = ra.get('recent_entries')
        i = self.insight.run(ctx)
        rem = self.remedy.run(ctx)
        m = self.mood.run(ctx)
        ctx['safety'] = s1
        s2 = self.safety.run(ctx)
        return {'route': r, 'safety': s1, 'extraction': e, 'retriever': ra, 'insight': i, 'remedy': rem, 'mood': m, 'safety_final': s2}
