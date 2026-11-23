# Evaluation results

Targets: Ethernaut @ `d05643a40a` (3 sets, 8 labeled bugs). 2 run(s) per variant per target; numbers are totals over all targets (averaged over runs).

Caveats: ground truth is a short list of the known, deliberate bugs. A finding that hits none of them may still be a real issue, so precision is a lower bound. Cost uses placeholder per-token prices (see models.py); token counts are exact. Small sample: treat differences as indicative, not proven.

| variant | recall | precision | findings | tokens in/out | est. cost | seconds | duplicate hits | gate failures | failed runs |
|---|---|---|---|---|---|---|---|---|---|
| single | 100% (8.0/8) | 91% (10.5/11.5) | 11.5 | 4165/2876 | $0.056 | 24 | 2.5 | 0.0 | 0 |
| graph_noverify | 100% (8.0/8) | 67% (12.0/18.0) | 18.0 | 11127/7920 | $0.152 | 79 | 4.0 | 0.0 | 0 |
| graph_noverify_rag | 100% (8.0/8) | 44% (9.5/21.5) | 21.5 | 23301/11170 | $0.237 | 97 | 1.5 | 0.0 | 0 |
| graph_verify | 100% (8.0/8) | 64% (12.5/19.5) | 19.5 | 66736/31160 | $0.668 | 286 | 4.5 | 2.0 | 0 |
| graph_verify_rag | 100% (8.0/8) | 56% (12.0/21.5) | 21.5 | 90734/30508 | $0.730 | 291 | 4.0 | 0.5 | 0 |
