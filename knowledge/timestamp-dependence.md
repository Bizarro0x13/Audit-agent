# Timestamp and block dependence
Block timestamps can be nudged by the block producer within a small range. Logic that depends on exact timing, or that uses block.number as a clock, can behave differently than expected, especially across chains.
Look for: time windows measured in seconds that decide money, deadlines, vesting, auctions.
Common fixes: tolerate drift, avoid decisions that depend on one second, document the time assumption.
Not a bug if: the time window is hours or days, so a seconds-level nudge by the block producer changes nothing.
