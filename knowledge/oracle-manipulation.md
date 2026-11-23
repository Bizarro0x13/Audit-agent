# Price oracle manipulation and staleness
A contract that reads a price from a pool spot price or a single source can be fooled by a large trade in the same transaction. Feeds can also be stale, zero, or report a different number of decimals than assumed.
Look for: prices read from reserves, balanceOf based valuation, missing freshness or sanity checks on feed data, mixed decimals.
Common fixes: time-weighted averages, multiple sources, validate round data, normalize decimals.
