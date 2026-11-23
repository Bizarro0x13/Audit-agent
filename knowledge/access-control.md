# Missing or weak access control
A function that changes ownership, funds, parameters or code can be called by anyone, or is protected by a check that can be satisfied by the wrong party.
Look for: public or external functions that write owner, admin, fee or implementation variables with no modifier; modifiers that compare against a variable an attacker can set; setters reachable during or after initialization.
Common fixes: explicit role checks on every privileged function, two-step ownership transfer, review who can call each function.
Not a bug if: the function has an owner or role check, is internal/private, or only touches the caller's own data. A public setter that only changes msg.sender's own record is not an access problem.
