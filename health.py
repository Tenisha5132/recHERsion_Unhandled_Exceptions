from config import APP_VERSION, LLM_API_KEY, LLM_BASE_URL
from retriever import retriever


def health_snapshot():
    configured = bool(LLM_API_KEY or LLM_BASE_URL)
    return {
        'status': 'ok',
        'app': 'recHERsion',
        'version': APP_VERSION,
        'retrieval': {
            'backend': 'embedding' if retriever.model is not None else 'bm25',
            'chunks': len(retriever.chunks),
        },
        'llm': {
            'configured': configured,
            'mode': 'llm' if configured else 'rules',
        },
    }
