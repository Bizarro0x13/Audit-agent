# Authorization with tx.origin
tx.origin is the externally owned account that started the whole transaction. msg.sender is the immediate caller. Using tx.origin for authorization means any contract the user interacts with can act as that user.
Look for: tx.origin in require or if checks, tx.origin compared to owner, wallets or contracts that proxy calls for users.
Common fixes: authorize with msg.sender; use tx.origin only to block contracts, and know that this is fragile.
Not a bug if: tx.origin is only compared to msg.sender to forbid contract callers, or is used for logging. The bug is tx.origin used as the identity that grants rights.
