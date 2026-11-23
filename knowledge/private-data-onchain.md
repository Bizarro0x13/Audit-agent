# Secrets stored on chain
Everything in contract storage is readable by anyone, including variables marked private. The private keyword only stops other contracts from reading it by name. Passwords, seeds and hidden game state can be read from storage or from transaction data.
Look for: password or secret variables, hidden answers, commit values stored in plain form.
Common fixes: store only hashes of commitments, move secrets off chain, use commit-reveal.
