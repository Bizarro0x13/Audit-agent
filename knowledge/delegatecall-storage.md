# Delegatecall and storage layout
delegatecall runs another contract's code against the caller's storage. Variables are matched by storage slot position, not by name. A mismatched layout makes the library overwrite unrelated variables such as the owner. Delegatecall to an address or data that an outsider controls lets them run arbitrary code with the caller's identity.
Look for: delegatecall with user-supplied target or calldata, libraries that write state, upgradeable proxies with different variable order, fallback functions that forward msg.data.
Common fixes: fixed trusted targets, identical storage layouts, stateless libraries, storage gaps and unstructured slots.
