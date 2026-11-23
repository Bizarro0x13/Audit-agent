# Evaluation results

Targets: Ethernaut @ `d05643a40a` (4 sets, 10 labeled bugs). 2 run(s) per variant per target; numbers are totals over all targets (averaged over runs).

Caveats: ground truth is a short list of the known, deliberate bugs. A finding that hits none of them may still be a real issue, so precision is a lower bound. Cost uses placeholder per-token prices (see models.py); token counts are exact. Small sample: treat differences as indicative, not proven.

| variant | recall | precision | findings | tokens in/out | est. cost | seconds | duplicate hits | gate failures | failed runs |
|---|---|---|---|---|---|---|---|---|---|
| single | 100% (10.0/10) | 83% (12.5/15.0) | 15.0 | 5446/3870 | $0.074 | 37 | 2.5 | 0.0 | 0 |
| graph_noverify | 100% (10.0/10) | 76% (15.5/20.5) | 20.5 | 15411/11119 | $0.213 | 112 | 5.5 | 0.0 | 0 |
| graph_noverify_rag | 100% (10.0/10) | 54% (11.0/20.5) | 20.5 | 26536/12684 | $0.270 | 114 | 1.0 | 0.0 | 0 |
| graph_verify | 100% (10.0/10) | 54% (16.5/30.5) | 30.5 | 121441/47916 | $1.083 | 435 | 6.5 | 1.5 | 0 |
| graph_verify_rag | 95% (9.5/10) | 50% (12.5/25.0) | 25.0 | 119631/38933 | $0.943 | 344 | 3.0 | 0.0 | 0 |
