# Evaluation results

Targets: Ethernaut @ `d05643a40a` plus our own safe controls. 13 target group(s), 31 labeled bugs in this run. 2 repeat(s); mean ± std over repeats that fully completed.

Caveats: ground truth is a short list of deliberate bugs, so a finding that hits none of them may still be real and precision is a lower bound. Safe controls are original code reviewed once (see eval/safe/REVIEW.md); a finding on one counts as a false positive. Ethernaut is public and may be in model training data. Cost uses published per-model prices (models.py); token counts are exact. Treat differences inside the spread as noise.

| variant | group | recall | precision | FP file rate | findings | cost | tokens in/out | seconds | repeats used | failed runs |
|---|---|---|---|---|---|---|---|---|---|---|
| single | train | 92% ±0% | 92% ±0% | - | 13.0 | $0.072 | 8143/5600 | 48 | 2/2 | 0 |
| single | heldout | 100% ±0% | 91% ±0% | - | 11.0 | $0.069 | 9079/5078 | 44 | 2/2 | 0 |
| single | unseen | 81% ±9% | 100% ±0% | - | 6.5 | $0.042 | 5554/3050 | 25 | 2/2 | 0 |
| single | safe-heldout | - | - | 0% ±0% | 0.0 | $0.017 | 4456/768 | 8 | 2/2 | 0 |
| single | safe-train | - | - | 0% ±0% | 0.0 | $0.012 | 4372/375 | 4 | 2/2 | 0 |
| graph_noverify | train | 92% ±11% | 80% ±2% | - | 15.0 | $0.198 | 24690/16074 | 156 | 2/2 | 0 |
| graph_noverify | heldout | 100% ±0% | 92% ±11% | - | 12.5 | $0.168 | 21117/13878 | 123 | 2/2 | 0 |
| graph_noverify | unseen | 94% ±9% | 100% ±0% | - | 7.5 | $0.112 | 14722/8690 | 85 | 2/2 | 0 |
| graph_noverify | safe-heldout | - | - | 0% ±0% | 0.0 | $0.032 | 7877/1904 | 23 | 2/2 | 0 |
| graph_noverify | safe-train | - | - | 0% ±0% | 0.0 | $0.041 | 9101/2680 | 28 | 2/2 | 0 |
| graph_noverify_rag | train | 96% ±5% | 83% ±5% | - | 15.0 | $0.219 | 34324/16515 | 150 | 2/2 | 0 |
| graph_noverify_rag | heldout | 95% ±7% | 91% ±1% | - | 11.5 | $0.202 | 33198/14772 | 138 | 2/2 | 0 |
| graph_noverify_rag | unseen | 88% ±18% | 100% ±0% | - | 7.0 | $0.127 | 20267/9140 | 92 | 2/2 | 0 |
| graph_noverify_rag | safe-heldout | - | - | 0% ±0% | 0.0 | $0.039 | 10518/2046 | 25 | 2/2 | 0 |
| graph_noverify_rag | safe-train | - | - | 0% ±0% | 0.0 | $0.031 | 8630/1818 | 20 | 2/2 | 0 |
| graph_verify | train | 96% ±5% | 78% ±4% | - | 16.0 | $0.391 | 54936/29552 | 264 | 2/2 | 0 |
| graph_verify | heldout | 100% ±0% | 88% ±5% | - | 12.5 | $0.309 | 45788/23136 | 209 | 2/2 | 0 |
| graph_verify | unseen | 88% ±0% | 100% ±0% | - | 7.0 | $0.177 | 26414/12952 | 119 | 2/2 | 0 |
| graph_verify | safe-heldout | - | - | 0% ±0% | 0.0 | $0.035 | 9570/1786 | 24 | 2/2 | 0 |
| graph_verify | safe-train | - | - | 0% ±0% | 0.0 | $0.033 | 7450/2272 | 25 | 2/2 | 0 |
| graph_verify_rag | train | 96% ±5% | 81% ±7% | - | 15.5 | $0.382 | 62163/27088 | 254 | 2/2 | 0 |
| graph_verify_rag | heldout | 100% ±0% | 96% ±6% | - | 11.5 | $0.340 | 55876/24248 | 226 | 2/2 | 0 |
| graph_verify_rag | unseen | 81% ±9% | 100% ±0% | - | 6.5 | $0.178 | 28811/12532 | 120 | 2/2 | 0 |
| graph_verify_rag | safe-heldout | - | - | 0% ±0% | 0.0 | $0.038 | 10518/1942 | 22 | 2/2 | 0 |
| graph_verify_rag | safe-train | - | - | 0% ±0% | 0.0 | $0.033 | 9266/1850 | 21 | 2/2 | 0 |

## Recall by difficulty (all vulnerable targets in this run)

| variant | easy | medium | hard |
|---|---|---|---|
| single | 100% ±0% | 91% ±0% | 85% ±7% |
| graph_noverify | 95% ±7% | 100% ±0% | 90% ±14% |
| graph_noverify_rag | 100% ±0% | 91% ±13% | 90% ±0% |
| graph_verify | 95% ±7% | 95% ±6% | 95% ±7% |
| graph_verify_rag | 100% ±0% | 95% ±6% | 85% ±7% |

## Rule 8 comparison against `single`

| variant | group | verdict | recall gain | spread | confidence |
|---|---|---|---|---|---|
| graph_noverify | train | no_gain | +0% | ±11% | low |
| graph_noverify | heldout | no_gain | +0% | ±0% | low |
| graph_noverify | unseen | better | +12% | ±9% | low |
| graph_noverify_rag | train | no_gain | +4% | ±5% | low |
| graph_noverify_rag | heldout | no_gain | -5% | ±7% | low |
| graph_noverify_rag | unseen | no_gain | +6% | ±18% | low |
| graph_verify | train | no_gain | +4% | ±5% | low |
| graph_verify | heldout | no_gain | +0% | ±0% | low |
| graph_verify | unseen | no_gain | +6% | ±9% | low |
| graph_verify_rag | train | no_gain | +4% | ±5% | low |
| graph_verify_rag | heldout | no_gain | +0% | ±0% | low |
| graph_verify_rag | unseen | no_gain | +0% | ±9% | low |
