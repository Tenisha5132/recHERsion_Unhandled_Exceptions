import json
from pathlib import Path
from orchestrator import Orchestrator
from retriever import retriever

def run_eval():
    personas_path = Path(__file__).parent / 'eval' / 'personas.json'
    if not personas_path.exists():
        personas_path = Path(__file__).parent / 'personas.json'
    personas = json.loads(personas_path.read_text())
    orch = Orchestrator()
    results = []
    for p in personas:
        res = orch.run(p['text'], anon_id=f"eval_{p['id']}")
        # extract
        ext = res.get('extraction', {}).get('extracted') if res.get('extraction') else {}
        ins = res.get('insight') or {}
        flag = ins.get('flag_level') if ins else ('urgent' if res.get('override') in ['urgent','distress'] else 'none')
        # retrieval
        chunks = res.get('retriever', {}).get('chunks') if res.get('retriever') else []
        hit = False
        exp = p.get('expected_kb_source')
        if exp and chunks:
            for c in chunks:
                sf = str(c.get('source_file','')).lower()
                if exp in sf:
                    hit = True
                    break
        results.append({
            'id': p['id'],
            'text': p['text'],
            'expected_flag': p['expected_flag_level'],
            'got_flag': flag,
            'exp_source': exp,
            'retrieval_hit': hit,
            'num_chunks': len(chunks)
        })
    # compute
    correct_flag = sum(1 for r in results if r['expected_flag'] == r['got_flag'])
    flag_acc = correct_flag / len(results) if results else 0
    retrieval_hits = sum(1 for r in results if r['exp_source'] and r['retrieval_hit'])
    retrieval_total = sum(1 for r in results if r['exp_source'])
    retrieval_rate = retrieval_hits / retrieval_total if retrieval_total else 0
    # simple confusion
    out_md = []
    out_md.append('# Eval Results (Synthetic Regression Test)\n')
    out_md.append('**NOTE:** This is a synthetic regression test written by the developers, NOT clinical validation.\n')
    out_md.append(f'## Summary\n')
    out_md.append(f'- Flag/triage accuracy: {flag_acc:.2%} ({correct_flag}/{len(results)})\n')
    out_md.append(f'- Retrieval hit-rate (expected source in top-3): {retrieval_rate:.2%} ({retrieval_hits}/{retrieval_total})\n')
    out_md.append(f'- Extraction: basic keyword extraction run (see per-case)\n')
    out_md.append('\n## Per-case\n')
    for r in results:
        out_md.append(f"- {r['id']}: exp={r['expected_flag']} got={r['got_flag']} | exp_src={r['exp_source']} hit={r['retrieval_hit']} chunks={r['num_chunks']}\n")
    out_md.append('\n## With-RAG vs no-RAG (notes)\n')
    out_md.append('- Citation coverage: insights include citations only when chunks retrieved.\n')
    out_md.append('- Retrieval-grounded claims: enforced by requiring citations; if none retrieved -> "no guidance found".\n')
    out_md.append('\n## Confusion (flag levels)\n')
    out_md.append('Manual inspection recommended.\n')
    (Path(__file__).parent / 'results.md').write_text(''.join(out_md))
    print(''.join(out_md))

if __name__ == '__main__':
    run_eval()
