# Evaluation results

Targets: Ethernaut @ `d05643a40a` (4 sets, 10 labeled bugs). 2 run(s) per variant per target; numbers are totals over all targets (averaged over runs).

Caveats: ground truth is a short list of the known, deliberate bugs. A finding that hits none of them may still be a real issue, so precision is a lower bound. Cost uses placeholder per-token prices (see models.py); token counts are exact. Small sample: treat differences as indicative, not proven.

| variant | recall | precision | findings | tokens in/out | est. cost | seconds | duplicate hits | gate failures | failed runs |
|---|---|---|---|---|---|---|---|---|---|
| single | 100% (10.0/10) | 100% (10.5/10.5) | 10.5 | 5834/3589 | $0.071 | 30 | 0.5 | 0.0 | 0 |
| graph_noverify | 100% (10.0/10) | 91% (10.0/11.0) | 11.0 | 15949/7754 | $0.164 | 85 | 0.0 | 1.0 | 0 |
| graph_verify | 100% (10.0/10) | 83% (10.0/12.0) | 12.0 | 35599/18186 | $0.380 | 184 | 0.0 | 0.0 | 0 |
