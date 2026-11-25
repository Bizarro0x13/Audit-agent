# Evaluation results

Targets: Ethernaut @ `d05643a40a` plus our own safe controls. 2 target group(s), 0 labeled bugs in this run. 2 repeat(s); mean ± std over repeats that fully completed.

Caveats: ground truth is a short list of deliberate bugs, so a finding that hits none of them may still be real and precision is a lower bound. Safe controls are original code reviewed once (see eval/safe/REVIEW.md); a finding on one counts as a false positive. Ethernaut is public and may be in model training data. Cost uses published per-model prices (models.py); token counts are exact. Treat differences inside the spread as noise.

| variant | group | recall | precision | FP file rate | findings | cost | tokens in/out | seconds | repeats used | failed runs |
|---|---|---|---|---|---|---|---|---|---|---|
| single | safe-heldout | - | - | 0% ±0% | 0.0 | $0.017 | 4456/768 | 8 | 2/2 | 0 |
| single | safe-train | - | - | 0% ±0% | 0.0 | $0.012 | 4372/375 | 4 | 2/2 | 0 |
| graph_noverify | safe-heldout | - | - | 0% ±0% | 0.0 | $0.032 | 7877/1904 | 23 | 2/2 | 0 |
| graph_noverify | safe-train | - | - | 0% ±0% | 0.0 | $0.041 | 9101/2680 | 28 | 2/2 | 0 |
| graph_noverify_rag | safe-heldout | - | - | 0% ±0% | 0.0 | $0.039 | 10518/2046 | 25 | 2/2 | 0 |
| graph_noverify_rag | safe-train | - | - | 0% ±0% | 0.0 | $0.031 | 8630/1818 | 20 | 2/2 | 0 |
| graph_verify | safe-heldout | - | - | 0% ±0% | 0.0 | $0.035 | 9570/1786 | 24 | 2/2 | 0 |
| graph_verify | safe-train | - | - | 0% ±0% | 0.0 | $0.033 | 7450/2272 | 25 | 2/2 | 0 |
| graph_verify_rag | safe-heldout | - | - | 0% ±0% | 0.0 | $0.038 | 10518/1942 | 22 | 2/2 | 0 |
| graph_verify_rag | safe-train | - | - | 0% ±0% | 0.0 | $0.033 | 9266/1850 | 21 | 2/2 | 0 |
