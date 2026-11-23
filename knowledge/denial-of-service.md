# Denial of service
A function can be made to revert, run out of gas, or become unreachable, blocking other users. Typical causes: pushing ETH to an address that always reverts, loops over unbounded user-controlled arrays, a required step that one party can refuse to take, and griefing through dust deposits.
Look for: transfer or call to a stored address inside a state-changing path, for loops over dynamic arrays, logic that depends on a single external party succeeding.
Common fixes: pull payments, bounded loops or batching, isolate external failures so they do not block core logic.
