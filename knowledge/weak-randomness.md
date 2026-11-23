# Weak on-chain randomness
Values such as block.timestamp, blockhash, block.number, block.prevrandao and msg.sender are visible or influenceable before or while a transaction executes. A contract that uses them as a random source can be predicted or replayed by another contract in the same transaction.
Look for: lotteries, games, NFT trait or minting rolls, random selection of winners that hash block fields.
Common fixes: verifiable randomness oracles, commit-reveal schemes with a delay.
