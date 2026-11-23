# Reentrancy
A function makes an external call (send ETH, call a token, call a callback) before it finishes updating its own state. The callee can call back into the same or another function while the old state is still visible, so a check passes twice or a balance is spent twice.
Look for: external calls followed by a state write, balances read before a transfer, callbacks from token standards, functions that share state but not the same lock.
Common fixes: update state before the call (checks-effects-interactions), use a reentrancy guard, pull instead of push payments.
Not a bug if: all state writes happen before the external call, a reentrancy guard covers every function sharing that state, or the call target is a fixed trusted contract with no callback.
