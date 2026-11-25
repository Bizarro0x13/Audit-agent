# Evaluation results

Targets: Ethernaut @ `d05643a40a` (4 sets, 10 labeled bugs). 2 run(s) per variant per target; numbers are totals over all targets (averaged over runs).

Caveats: ground truth is a short list of the known, deliberate bugs. A finding that hits none of them may still be a real issue, so precision is a lower bound. Cost uses placeholder per-token prices (see models.py); token counts are exact. Small sample: treat differences as indicative, not proven.

| variant | recall | precision | findings | tokens in/out | est. cost | seconds | duplicate hits | gate failures | failed runs |
|---|---|---|---|---|---|---|---|---|---|
| single | 95% (9.5/10) | 100% (9.5/9.5) | 9.5 | 5834/3407 | $0.069 | 32 | 0.0 | 0.0 | 0 |
| graph_noverify | 100% (10.0/10) | 87% (10.0/11.5) | 11.5 | 16249/8442 | $0.175 | 93 | 0.0 | 0.0 | 0 |
| graph_verify | 100% (10.0/10) | 91% (10.0/11.0) | 11.0 | 34184/15404 | $0.334 | 162 | 0.0 | 0.0 | 0 |
