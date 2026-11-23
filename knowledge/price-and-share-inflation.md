# Share price inflation and first depositor issues
In vaults that mint shares in proportion to deposits, the first depositor can deposit a tiny amount and donate tokens directly to the vault to inflate the share price. Later depositors then receive zero or heavily rounded shares.
Look for: shares computed as amount * totalSupply / totalAssets, no minimum liquidity, balanceOf based total assets.
Common fixes: virtual shares or assets offset, minimum initial deposit, track assets internally.
Not a bug if: the vault mints dead shares or uses a virtual offset, enforces a minimum first deposit, or tracks assets with an internal variable that donations cannot change.
