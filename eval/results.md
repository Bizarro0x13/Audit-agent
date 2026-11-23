# Evaluation results

Targets: Ethernaut @ `d05643a40a` (3 sets, 8 labeled bugs). 1 run(s) per variant per target; numbers are totals over all targets (averaged over runs).

Caveats: ground truth is a short list of the known, deliberate bugs. A finding that hits none of them may still be a real issue, so precision is a lower bound. Cost uses placeholder per-token prices (see models.py); token counts are exact. Small sample: treat differences as indicative, not proven.

| variant | recall | precision | findings | tokens in/out | est. cost | seconds | gate failures | failed runs |
|---|---|---|---|---|---|---|---|---|
| single | 100% (8.0/8) | 91% (10.0/11.0) | 11.0 | 4165/2707 | $0.053 | 24 | 0.0 | 0 |
| graph_noverify | 100% (8.0/8) | 92% (12.0/13.0) | 13.0 | 9218/6614 | $0.127 | 64 | 0.0 | 0 |
| graph_verify | 100% (8.0/8) | 93% (14.0/15.0) | 15.0 | 29658/16230 | $0.332 | 164 | 0.0 | 0 |
