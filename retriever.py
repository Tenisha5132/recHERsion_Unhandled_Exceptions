import json
import math
import os
import re
from pathlib import Path

from config import BASE_DIR, EMBED_MODEL, MIN_RETRIEVAL_SCORE, TOP_K

STOPWORDS = set('''
a an and are as at be been being but by can could did do does doing done feel feeling
for from get got had has have having he her here hers herself him himself his how i if
im in into is it its itself just like me more most my myself no nor not now of off on
once only or other our ours ourselves out over own really same she should so some such
take than that the their theirs them themselves then there these they this those through
to today too under until up very was we were what when where which while who whom why
will with would you your yours yourself yourselves
'''.split())

TOKEN_PATTERN = re.compile(r"[a-z0-9']+")


def _query_terms(text):
    return [
        token for token in TOKEN_PATTERN.findall((text or '').lower())
        if len(token) > 1 and token not in STOPWORDS
    ]


class SimpleBM25:
    def __init__(self, corpus):
        self.corpus = corpus
        self.corpus_size = len(corpus)
        self.avgdl = 0
        self.doc_freqs = []
        self.idf = {}
        self.doc_len = []
        if corpus:
            for document in corpus:
                self.doc_len.append(len(document))
            self.avgdl = sum(self.doc_len) / self.corpus_size
            self._initialize(corpus)
    
    def _initialize(self, corpus):
        nd = {}
        for document in corpus:
            frequencies = {}
            for word in document:
                frequencies[word] = frequencies.get(word, 0) + 1
            self.doc_freqs.append(frequencies)
            for word in frequencies:
                nd[word] = nd.get(word, 0) + 1
        for word, freq in nd.items():
            self.idf[word] = math.log((self.corpus_size - freq + 0.5) / (freq + 0.5) + 1.0)
    
    def get_scores(self, query):
        scores = [0.0] * self.corpus_size
        for q in query:
            if q not in self.idf:
                continue
            for i, doc in enumerate(self.doc_freqs):
                if q in doc:
                    score = self.idf[q] * (doc[q] * (1.2 + 1) / (doc[q] + 1.2 * (1 - 0.75 + 0.75 * self.doc_len[i] / self.avgdl)))
                    scores[i] += score
        return scores

class Retriever:
    def __init__(self):
        self.chunks = []
        self.embeddings = None
        self.model = None
        self.bm25 = None
        self.load()

    def load(self):
        kb_path = BASE_DIR / 'data' / 'kb_chunks.json'
        if kb_path.exists():
            try:
                self.chunks = json.loads(kb_path.read_text(encoding='utf-8'))
            except Exception:
                self.chunks = []
        # try embeddings
        try:
            from sentence_transformers import SentenceTransformer
            import numpy as np
            self.model = SentenceTransformer(EMBED_MODEL)
            self.np = np
            texts = [c['chunk'] for c in self.chunks]
            if texts:
                self.embeddings = self.model.encode(texts, normalize_embeddings=True)
        except Exception:
            self.model = None
            self.embeddings = None
        # bm25 fallback
        if self.model is None or self.embeddings is None:
            try:
                from rank_bm25 import BM25Okapi
                tokenized = [c['chunk'].lower().split() for c in self.chunks]
                self.bm25 = BM25Okapi(tokenized)
            except Exception:
                try:
                    tokenized = [c['chunk'].lower().split() for c in self.chunks]
                    self.bm25 = SimpleBM25(tokenized)
                except Exception:
                    self.bm25 = None

    def expand_query(self, q):
        ql = q.lower()
        if 'pcos' in ql and 'pmos' not in ql:
            q = q + ' PMOS polyendocrine metabolic ovarian syndrome'
        if 'pmos' in ql and 'pcos' not in ql:
            q = q + ' PCOS polycystic ovary syndrome'
        if 'heavy' in ql or 'bleed' in ql or 'clot' in ql or 'soak' in ql:
            q = q + ' heavy periods menorrhagia NHS'
        if 'irregular' in ql or 'miss' in ql or 'cycle' in ql:
            q = q + ' irregular periods cycle NHS'
        if 'endometri' in ql or ('pain' in ql and 'pelvic' in ql) or 'sex' in ql:
            q = q + ' endometriosis'
        if 'thyroid' in ql or ('tired' in ql and 'cold' in ql) or 'hypothyroid' in ql:
            q = q + ' underactive thyroid hypothyroidism'
        return q

    def query(self, q, top_k=5, min_score=None):
        q_exp = self.expand_query(q)
        results = []
        floor = MIN_RETRIEVAL_SCORE if min_score is None else min_score
        if self.model is not None and self.embeddings is not None and len(self.chunks) > 0:
            try:
                q_emb = self.model.encode([q_exp], normalize_embeddings=True)
                scores = self.np.dot(self.embeddings, q_emb.T).flatten()
                idxs = self.np.argsort(scores)[::-1][:top_k]
                for i in idxs:
                    score = float(scores[i])
                    if score < floor:
                        continue
                    results.append({
                        'chunk': self.chunks[i]['chunk'],
                        'source_url': self.chunks[i]['source_url'],
                        'title': self.chunks[i]['title'],
                        'source_file': self.chunks[i]['source_file'],
                        'score': score,
                        'method': 'embedding'
                    })
                return results
            except Exception:
                pass
        if self.bm25 is not None and len(self.chunks) > 0:
            try:
                tokenized_q = _query_terms(q_exp)
                if not tokenized_q:
                    return []
                scores = self.bm25.get_scores(tokenized_q)
                try:
                    import numpy as _np
                    idxs = _np.argsort(scores)[::-1][:top_k]
                except Exception:
                    idxs = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
                for i in idxs:
                    score = float(scores[i])
                    if score < floor:
                        continue
                    results.append({
                        'chunk': self.chunks[i]['chunk'],
                        'source_url': self.chunks[i]['source_url'],
                        'title': self.chunks[i]['title'],
                        'source_file': self.chunks[i]['source_file'],
                        'score': score,
                        'method': 'bm25'
                    })
                return results
            except Exception:
                pass
        return []

retriever = Retriever()
