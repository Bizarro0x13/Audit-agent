# Unchecked return values
Low-level calls (call, send, delegatecall) and some token functions return false instead of reverting. Ignoring the result lets the program continue as if the operation worked.
Look for: call or send without checking the boolean, ERC20 transfer or approve whose result is ignored, tokens that return nothing.
Common fixes: require the result, use safe wrappers for token calls.
