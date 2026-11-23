"""Scoring: does a finding match a ground-truth bug? Same file and overlapping line ranges."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Span:
    file: str  # base name, e.g. "Vault.sol"
    line_start: int
    line_end: int


def overlaps(a: Span, b: Span) -> bool:
    return a.file == b.file and a.line_start <= b.line_end and b.line_start <= a.line_end


def score(found: list[Span], truth: list[Span]) -> dict:
    """recall = truth bugs hit by at least one finding / all truth bugs.
    precision = findings that hit some truth bug / all findings.
    Findings that hit nothing may still be real bugs not in our list, so precision is a
    lower bound, not a false-positive rate."""
    hit_truth = [t for t in truth if any(overlaps(f, t) for f in found)]
    hit_found = [f for f in found if any(overlaps(f, t) for t in truth)]
    return {
        "truth": len(truth),
        "found": len(found),
        "truth_hit": len(hit_truth),
        "found_hit": len(hit_found),
        "recall": len(hit_truth) / len(truth) if truth else 0.0,
        "precision": len(hit_found) / len(found) if found else 0.0,
    }
