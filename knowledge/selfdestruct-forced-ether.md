# Forced ether and balance assumptions
A contract cannot refuse ETH sent through selfdestruct or as a block reward recipient. Logic that assumes address(this).balance equals the sum of tracked deposits can be broken by forced ETH.
Look for: invariants written with address(this).balance, equality checks on balance, accounting that reads live balances.
Common fixes: track balances in storage, use greater-or-equal checks, do not depend on exact balances.
Not a bug if: the contract uses its own internal accounting variable instead of address(this).balance, and uses >= rather than == for balance checks.
