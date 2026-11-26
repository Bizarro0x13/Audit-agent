# Evaluation results

Targets: Ethernaut @ `d05643a40a` plus our own safe controls. 13 target group(s), 31 labeled bugs in this run. 3 repeat(s); mean ± std over repeats that fully completed. Models: analyst `claude-haiku-5-5`, verifier `claude-haiku-5-5`.

Caveats: ground truth is a short list of deliberate bugs, so a finding that hits none of them may still be real and precision is a lower bound. Safe controls are original code reviewed once (see eval/safe/REVIEW.md); a finding on one counts as a false positive. Ethernaut is public and may be in model training data. Cost uses published per-model prices (models.py); token counts are exact. Treat differences inside the spread as noise.

| variant | group | recall | precision | FP file rate | findings | cost | tokens in/out | seconds | repeats used | failed runs |
|---|---|---|---|---|---|---|---|---|---|---|
| single | train | 85% ±8% | 94% ±5% | - | 11.7 | $0.004 | 8143/6854 | 36 | 3/3 | 0 |
| single | heldout | 87% ±6% | 84% ±5% | - | 10.3 | $0.005 | 10148/8742 | 44 | 3/3 | 0 |
| single | unseen | 71% ±7% | 100% ±0% | - | 5.7 | $0.003 | 5554/3970 | 20 | 3/3 | 0 |
| single | safe-heldout | - | - | 0% ±0% | 0.0 | $0.001 | 4955/1343 | 8 | 3/3 | 0 |
| single | safe-train | - | - | 0% ±0% | 0.0 | $0.001 | 5868/1048 | 6 | 3/3 | 0 |
| graph_noverify | train | 85% ±8% | 86% ±12% | - | 14.0 | $0.012 | 25973/18683 | 107 | 3/3 | 0 |
| graph_noverify | heldout | 100% ±0% | 81% ±5% | - | 16.0 | $0.013 | 23473/21329 | 114 | 3/3 | 0 |
| graph_noverify | unseen | 75% ±0% | 100% ±0% | - | 6.0 | $0.007 | 16034/11330 | 66 | 3/3 | 0 |
| graph_noverify | safe-heldout | - | - | 0% ±0% | 0.0 | $0.002 | 10101/2403 | 18 | 3/3 | 0 |
| graph_noverify | safe-train | - | - | 0% ±0% | 0.0 | $0.002 | 7933/2479 | 17 | 3/3 | 0 |
| graph_noverify_rag | train | 85% ±8% | 85% ±1% | - | 13.7 | $0.013 | 35589/19706 | 112 | 3/3 | 0 |
| graph_noverify_rag | heldout | 100% ±0% | 88% ±8% | - | 13.7 | $0.018 | 35925/28222 | 148 | 3/3 | 0 |
| graph_noverify_rag | unseen | 79% ±14% | 100% ±0% | - | 6.3 | $0.008 | 20082/11571 | 67 | 3/3 | 0 |
| graph_noverify_rag | safe-heldout | - | - | 0% ±0% | 0.0 | $0.003 | 14297/2677 | 19 | 3/3 | 0 |
| graph_noverify_rag | safe-train | - | - | 0% ±0% | 0.0 | $0.002 | 11967/2134 | 16 | 3/3 | 0 |
| graph_verify | train | 90% ±4% | 88% ±5% | - | 14.0 | $0.022 | 48222/33458 | 185 | 3/3 | 0 |
| graph_verify | heldout | 100% ±0% | 91% ±8% | - | 13.7 | $0.019 | 44829/29595 | 159 | 3/3 | 0 |
| graph_verify | unseen | 83% ±7% | 100% ±0% | - | 6.7 | $0.011 | 24628/16781 | 96 | 3/3 | 0 |
| graph_verify | safe-heldout | - | - | 0% ±0% | 0.0 | $0.002 | 11084/2285 | 18 | 3/3 | 0 |
| graph_verify | safe-train | - | - | 0% ±0% | 0.0 | $0.002 | 10039/2159 | 17 | 3/3 | 0 |
| graph_verify_rag | train | 82% ±18% | 81% ±6% | - | 14.0 | $0.021 | 57477/30847 | 173 | 3/3 | 0 |
| graph_verify_rag | heldout | 100% ±0% | 93% ±7% | - | 13.0 | $0.023 | 56135/35555 | 189 | 3/3 | 0 |
| graph_verify_rag | unseen | 83% ±14% | 100% ±0% | - | 6.7 | $0.012 | 29745/17137 | 97 | 3/3 | 0 |
| graph_verify_rag | safe-heldout | - | - | 8% ±14% | 0.3 | $0.003 | 12675/2584 | 18 | 3/3 | 0 |
| graph_verify_rag | safe-train | - | - | 0% ±0% | 0.0 | $0.002 | 10151/2354 | 16 | 3/3 | 0 |

## Recall by difficulty (all vulnerable targets in this run)

| variant | easy | medium | hard |
|---|---|---|---|
| single | 87% ±12% | 79% ±5% | 80% ±10% |
| graph_noverify | 83% ±6% | 88% ±5% | 90% ±10% |
| graph_noverify_rag | 83% ±6% | 88% ±5% | 93% ±6% |
| graph_verify | 90% ±0% | 91% ±0% | 93% ±6% |
| graph_verify_rag | 83% ±12% | 85% ±14% | 97% ±6% |

## Rule 8 comparison against `single`

| variant | group | verdict | recall gain | spread | confidence |
|---|---|---|---|---|---|
| graph_noverify | train | no_gain | +0% | ±8% | ok |
| graph_noverify | heldout | better | +13% | ±6% | ok |
| graph_noverify | unseen | no_gain | +4% | ±7% | ok |
| graph_noverify_rag | train | no_gain | +0% | ±8% | ok |
| graph_noverify_rag | heldout | better | +13% | ±6% | ok |
| graph_noverify_rag | unseen | no_gain | +8% | ±14% | ok |
| graph_verify | train | no_gain | +5% | ±8% | ok |
| graph_verify | heldout | better | +13% | ±6% | ok |
| graph_verify | unseen | better | +12% | ±7% | ok |
| graph_verify_rag | train | no_gain | -3% | ±18% | ok |
| graph_verify_rag | heldout | better | +13% | ±6% | ok |
| graph_verify_rag | unseen | no_gain | +12% | ±14% | ok |
