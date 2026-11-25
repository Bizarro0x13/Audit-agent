# Review record for the unseen targets

Eight original vulnerable contracts, written for this project (not copied or adapted from
any public level). They exist so recall can be measured on code a model has not seen as a
benchmark item. Labels are in `eval/truth.json` (ids U01-U08, split `unseen`).

## Verification done (2026-11-26)

1. All 8 compile with Solidity 0.8.38 (`forge build`; also checked by a test when forge
   is installed).
2. **Exploit proofs.** An independent engineer, given each claimed bug, wrote a Foundry
   exploit test for each. All 8 claims were confirmed with a concrete harm
   (stolen rewards, whole supply captured, zero rewards ever paid, payment marked paid
   but not sent, all ETH locked, treasury drained, deposit stolen by share inflation,
   voucher replayed to drain a second deployment). The test files were scratch work and
   are not committed.
3. **Blind audit.** A separate auditor, told nothing about the labels, audited all 8 and
   found exactly the labeled bugs and no unlabeled one. PayoutSplitter drew two
   mechanisms (one reverting member; an unbounded member list); both sit in the same
   function and share one label, since one fix removes both. Payroll's two consequences
   (payment lost with a return-false token; funds stuck with a no-return token) also share
   one label for the same reason.
4. **AirdropClaim was reworked** after the first verification: the original handed out
   ids with no value, so the harm was weak. It now hands out amounts from a capped supply,
   so re-entering the callback captures the whole supply and locks every other eligible
   account out. The reworked file was proven by an exploit test and re-audited blind:
   exactly one issue, the labeled one.

## Caveats (read before trusting the numbers)

- **Unseen only until published.** Once this repository is public, these contracts and
  their labels can enter model training data. "Unseen" holds for models trained before
  that. For a durable holdout, keep a private set outside the repo (idea logged in the dev
  plan).
- Difficulty tags are our estimate, not measured. Compare against recall by difficulty
  after the first real run and re-tag only before any tuning, then re-freeze.
- Some bugs depend on a precondition: Payroll needs a token whose transfer returns false
  (not reverts); ShareVault needs the attacker to be first or to front-run the first
  deposit; VoucherMint needs one signer behind two deployments; AirdropClaim needs an
  eligible contract address. These are real in the code but a reviewer may rate severity
  differently.
- A finding that matches a label by line range counts as a hit even if the stated reason
  differs. Spot-check hits by reading them once on the first real run.

## Rule

If a contract here is edited after any eval result exists on it, record the change in this
file and discard earlier results for that file. Never move a bug between splits.
