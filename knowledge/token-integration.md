# Token behavior assumptions
Not every token behaves like a plain ERC20. Some charge fees on transfer, rebase balances, have blacklists, return no value, or use unusual decimals. Code that credits the requested amount instead of the amount actually received will drift out of sync.
Look for: accounting that trusts the amount parameter, transferFrom without measuring the balance change, hard coded 18 decimals, approvals that must be reset to zero first.
Common fixes: measure balance deltas, allow only known tokens, use safe transfer helpers.
Not a bug if: the token is fixed and known to be a plain ERC20, or the code measures the balance change around the transfer.
