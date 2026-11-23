# Integer overflow, underflow and rounding
Arithmetic can wrap around (in unchecked blocks or old compiler versions), truncate when converting between types, or round in a direction that favors one party. Division before multiplication loses precision.
Look for: unchecked blocks, solidity versions before 0.8 without SafeMath, casts to smaller types, share and price calculations, subtraction of user-controlled values.
Common fixes: checked arithmetic, explicit bounds, multiply before divide, choose the rounding direction that protects the protocol.
Not a bug if: the compiler is 0.8+ and the line is not in an unchecked block (overflow reverts), or the value range is bounded by earlier checks. A revert on overflow is safe behavior.
