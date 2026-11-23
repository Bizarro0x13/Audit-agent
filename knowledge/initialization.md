# Initialization mistakes
Ownership or configuration is set by a function that anyone can call, or never gets set. In older compiler versions a constructor was a function with the same name as the contract; a typo turns it into a normal public function. Proxy implementations may be left uninitialized.
Look for: initialize functions without a one-time guard, constructors declared by name, owners set in functions callable after deployment, upgradeable contracts with an open initializer.
Common fixes: constructor keyword, one-time initializer modifier, initialize implementation contracts.
Not a bug if: initialize is guarded to run once, the constructor sets the owner, or the function name differs from the contract only in a modern compiler where it is a plain function with an access check.
