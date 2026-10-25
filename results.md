# Eval Results (Synthetic Regression Test)
**NOTE:** This is a synthetic regression test written by the developers, NOT clinical validation.
## Summary
- Flag/triage accuracy: 90.00% (18/20)
- Retrieval hit-rate (expected source in top-3): 60.00% (9/15)
- Extraction: basic keyword extraction run (see per-case)

## Per-case
- 1: exp=discuss got=discuss | exp_src=pmos hit=True chunks=3
- 2: exp=urgent got=urgent | exp_src=heavy-periods hit=False chunks=0
- 3: exp=discuss got=urgent | exp_src=endometriosis hit=False chunks=0
- 4: exp=discuss got=discuss | exp_src=underactive-thyroid hit=False chunks=3
- 5: exp=discuss got=discuss | exp_src=irregular-periods hit=True chunks=3
- 6: exp=none got=none | exp_src=irregular-periods hit=False chunks=3
- 7: exp=none got=none | exp_src=heavy-periods hit=False chunks=3
- 8: exp=none got=none | exp_src=None hit=False chunks=3
- 9: exp=discuss got=none | exp_src=heavy-periods hit=True chunks=3
- 10: exp=urgent got=urgent | exp_src=None hit=False chunks=0
- 11: exp=discuss got=discuss | exp_src=pmos hit=True chunks=3
- 12: exp=discuss got=discuss | exp_src=pmos hit=True chunks=3
- 13: exp=urgent got=urgent | exp_src=None hit=False chunks=0
- 14: exp=discuss got=discuss | exp_src=heavy-periods hit=True chunks=3
- 15: exp=discuss got=discuss | exp_src=endometriosis hit=True chunks=3
- 16: exp=discuss got=discuss | exp_src=underactive-thyroid hit=False chunks=3
- 17: exp=discuss got=discuss | exp_src=irregular-periods hit=True chunks=3
- 18: exp=none got=none | exp_src=None hit=False chunks=3
- 19: exp=discuss got=discuss | exp_src=heavy-periods hit=True chunks=3
- 20: exp=none got=none | exp_src=None hit=False chunks=3

## With-RAG vs no-RAG (notes)
- Citation coverage: insights include citations only when chunks retrieved.
- Retrieval-grounded claims: enforced by requiring citations; if none retrieved -> "no guidance found".

## Confusion (flag levels)
Manual inspection recommended.
