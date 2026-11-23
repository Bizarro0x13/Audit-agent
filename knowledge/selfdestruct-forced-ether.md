# Forced ether and balance assumptions
A contract cannot refuse ETH sent through selfdestruct or as a block reward recipient. Logic that assumes address(this).balance equals the sum of tracked deposits can be broken by forced ETH.
Look for: invariants written with address(this).balance, equality checks on balance, accounting that reads live balances.
Common fixes: track balances in storage, use greater-or-equal checks, do not depend on exact balances.
