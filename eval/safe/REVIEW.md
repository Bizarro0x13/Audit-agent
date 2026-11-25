# Review record for the safe controls

Purpose: a safe control that is secretly exploitable would corrupt the false-positive rate,
so each file was reviewed before use.

## What was done (2026-11-25)

1. **Author review.** Each contract was written as the correct form of a pattern whose
   vulnerable twin is in `truth.json` (see `manifest.json`). Code is original, not copied
   from upstream.
2. **Compile check.** All 12 compile with Solidity 0.8.38 through `forge build`
   (also run by `tests/test_eval_safe.py` when `forge` is installed).
3. **Independent adversarial review.** A separate reviewer with a fresh context, told only
   to audit and not told the files were meant to be safe, traced every file for theft,
   locked funds, privilege escalation, liveness breaks and accounting corruption.
   Result: no exploitable issue found in any file.

## Limits of this review (read before trusting the numbers)

- The independent review was done by tracing the code. It did not run exploit tests.
- It is one reviewer, one pass. A subtle bug could still exist.
- Therefore: the first time any control draws a finding in a real eval run, a human reads
  that finding once. If it is real, the control is fixed and all earlier runs on it are
  discarded. If it is a legitimate-but-arguable concern, it stays counted as a false
  positive and is listed below.

## Known arguable points (a finding here is counted as a false positive, but is debatable)

- `SafePool`: the owner's seeded liquidity can never be withdrawn. It only affects the
  owner's own deposit, by design.
- `SafePool` and `SafeStaking`: they assume the deployer-chosen tokens do not rebase
  downward or charge the sender more than the amount. Fee-on-transfer tokens are handled
  by measuring the balance change.
- `SafeToken`: no approve/transferFrom, so it is not a full ERC20. Not a vulnerability.
- `SafeAuction` and `SafeShop`: if the seller is a contract that rejects ETH, the seller's
  own payout reverts. This hurts only the deployer.
- `SafeRegistry`: names can be front-run. No funds are involved.

## Rule

Never edit a control after seeing eval results on it without recording the change here
and discarding earlier results for that file.
