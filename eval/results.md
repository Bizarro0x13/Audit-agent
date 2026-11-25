# Evaluation results

Targets: Ethernaut @ `d05643a40a` (4 sets, 10 labeled bugs). 2 run(s) per variant per target; numbers are totals over all targets (averaged over runs).

Caveats: ground truth is a short list of the known, deliberate bugs. A finding that hits none of them may still be a real issue, so precision is a lower bound. Cost uses the published per-model prices in models.py (as of 2026-11-03); token counts are exact. Small sample: treat differences as indicative, not proven.

| variant | recall | precision | findings | tokens in/out | est. cost | seconds | duplicate hits | gate failures | failed runs |
|---|---|---|---|---|---|---|---|---|---|
| single | 100% (10.0/10) | 100% (11.0/11.0) | 11.0 | 5834/4178 | $0.053 | 34 | 1.0 | 0.0 | 0 |
| graph_noverify | 100% (10.0/10) | 91% (10.0/11.0) | 11.0 | 17310/8082 | $0.102 | 92 | 0.0 | 0.5 | 0 |
| graph_noverify_rag | 100% (10.0/10) | 91% (10.0/11.0) | 11.0 | 22878/8804 | $0.121 | 94 | 0.0 | 0.0 | 0 |
| graph_verify | 100% (10.0/10) | 91% (10.0/11.0) | 11.0 | 31576/13670 | $0.187 | 147 | 0.0 | 0.5 | 0 |
| graph_verify_rag | 100% (10.0/10) | 91% (10.0/11.0) | 11.0 | 48236/20527 | $0.289 | 200 | 0.0 | 0.5 | 0 |
