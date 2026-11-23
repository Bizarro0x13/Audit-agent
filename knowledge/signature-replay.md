# Signature replay and malformed signatures
A signed message that is not bound to a nonce, chain, contract address and purpose can be reused. ECDSA signatures can be malleable, and ecrecover returns the zero address on failure.
Look for: ecrecover without a zero-address check, messages without a nonce or domain separator, permits and meta-transactions, signatures reusable across chains or contracts.
Common fixes: typed structured data with a domain separator, per-signer nonces, expiry, reject the zero address.
