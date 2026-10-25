from config import APP_VERSION, LLM_API_KEY, LLM_BASE_URL
from retriever import retriever
from tracker import database_ok


def health_snapshot():
    configured = bool(LLM_API_KEY or LLM_BASE_URL)
    database_up = database_ok()
    return {
        'status': 'ok' if database_up else 'degraded',
        'app': 'recHERsion',
        'version': APP_VERSION,
        'retrieval': {
            'backend': 'embedding' if retriever.model is not None else 'bm25',
            'chunks': len(retriever.chunks),
        },
        'database': {
            'status': 'ok' if database_up else 'unavailable',
        },
        'llm': {
            'configured': configured,
            'mode': 'llm' if configured else 'rules',
        },
    }
