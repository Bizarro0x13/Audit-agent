# Evaluation targets (selection)

Our own labels for the public Ethernaut levels at the pinned commit in `truth.json`.
No upstream code is stored here. Ethernaut is AGPL-3.0, so the code is cloned into the
gitignored `eval/.cache/` at eval time.

Selection rules: one row per intended bug; spread over many bug families; a mix of easy,
medium and hard; include multi-contract cases; skip levels whose "bug" is not in the code
(for example a contract that cannot refuse forced ETH) and near-duplicates of a level
already chosen.

Contamination caveat: Ethernaut is public and widely discussed, so models may have seen
the older levels. Newer levels are probably less memorized. Phase 0.6 adds unseen targets
we write ourselves; recall on those is the cleanest signal.

Families: reentrancy, access-control, denial-of-service, delegatecall-storage, randomness,
data-exposure, callback-trust, arithmetic, caller-assumption, unchecked-return,
calldata-encoding, price-manipulation, input-validation, accounting.

| id | level | file | family | difficulty | cross_contract |
|----|-------|------|--------|------------|----------------|
| E01 | Reentrance | Reentrance.sol | reentrancy | easy | no |
| E02 | King | King.sol | denial-of-service | easy | no |
| E03 | Fallout | Fallout.sol | access-control | easy | no |
| E04 | Telephone | Telephone.sol | caller-assumption | easy | no |
| E05 | Delegation | Delegation.sol | delegatecall-storage | medium | no |
| E06 | Preservation | Preservation.sol | delegatecall-storage | hard | yes |
| E07 | CoinFlip | CoinFlip.sol | randomness | easy | no |
| E08 | Vault | Vault.sol | data-exposure | easy | no |
| E09 | Elevator | Elevator.sol | callback-trust | easy | no |
| E10 | NaughtCoin | NaughtCoin.sol | access-control | medium | yes |
| E11 | Token | Token.sol | arithmetic | easy | no |
| E12 | Fallback | Fallback.sol | access-control | easy | no |
| E13 | GatekeeperTwo | GatekeeperTwo.sol | caller-assumption | medium | no |
| E14 | Stake | Stake.sol | unchecked-return | medium | no |
| E15 | Switch | Switch.sol | calldata-encoding | hard | no |
| E16 | AlienCodex | AlienCodex.sol | arithmetic | hard | yes |
| E17 | Dex | Dex.sol | price-manipulation | medium | yes |
| E18 | DexTwo | DexTwo.sol | input-validation | medium | yes |
| E19 | PuzzleWallet | PuzzleWallet.sol | delegatecall-storage | hard | yes |
| E20 | PuzzleWallet | PuzzleWallet.sol | accounting | hard | yes |
| E21 | MagicAnimalCarousel | MagicAnimalCarousel.sol | arithmetic | hard | no |
| E22 | GoodSamaritan | GoodSamaritan.sol | callback-trust | hard | yes |
| E23 | HigherOrder | HigherOrder.sol | calldata-encoding | hard | no |

Considered and skipped: Force (no bug in the code), Shop (variant of Elevator), Privacy
(variant of Vault), Recovery (intended bug is off-chain address recovery), GatekeeperOne
(gas puzzle, not a vulnerability class), MagicNum (bytecode golf).

## Unseen targets (written for this project)

Original contracts in `eval/unseen/`, not derived from any public level, so models cannot
have memorized them as benchmark items. Each bug was proven with a Foundry exploit test by
an independent reviewer, and a separate blind audit found no unlabeled bugs (see
`eval/unseen/REVIEW.md`). Families here may include ones absent from the train/heldout
sets (signature-replay, accounting).

| id | level | file | family | difficulty | cross_contract |
|----|-------|------|--------|------------|----------------|
| U01 | (ours) YieldPool | YieldPool.sol | accounting | hard | no |
| U02 | (ours) AirdropClaim | AirdropClaim.sol | reentrancy | medium | no |
| U03 | (ours) StakeRewards | StakeRewards.sol | arithmetic | medium | no |
| U04 | (ours) Payroll | Payroll.sol | unchecked-return | medium | no |
| U05 | (ours) PayoutSplitter | PayoutSplitter.sol | denial-of-service | easy | no |
| U06 | (ours) Treasury | Treasury.sol | access-control | medium | no |
| U07 | (ours) ShareVault | ShareVault.sol | price-manipulation | medium | no |
| U08 | (ours) VoucherMint | VoucherMint.sol | signature-replay | hard | no |
