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


# ---- Phase 0.4: bugs with several accepted ranges, grouped recall, false positives, spread ----


@dataclass(frozen=True)
class Bug:
    """A ground-truth bug. A finding hits it if it overlaps ANY of its spans (primary first,
    then alternates for bugs that are visible in more than one place)."""

    id: str
    spans: tuple[Span, ...]
    family: str = ""
    difficulty: str = ""
    split: str = ""


def bug_from_truth(entry: dict) -> Bug:
    spans = [Span(entry["file"], entry["line_start"], entry["line_end"])]
    spans += [Span(entry["file"], a, b) for a, b in entry.get("alt_ranges", [])]
    return Bug(entry["id"], tuple(spans), entry.get("family", ""),
               entry.get("difficulty", ""), entry.get("split", ""))


def hits_bug(found: list[Span], bug: Bug) -> bool:
    return any(overlaps(f, s) for f in found for s in bug.spans)


def score_bugs(found: list[Span], bugs: list[Bug]) -> dict:
    """Like score(), but each bug can be matched through any of its spans.
    precision counts a finding as correct if it overlaps any span of any bug."""
    hit_ids = [b.id for b in bugs if hits_bug(found, b)]
    found_hit = [f for f in found if any(overlaps(f, s) for b in bugs for s in b.spans)]
    return {
        "truth": len(bugs),
        "found": len(found),
        "truth_hit": len(hit_ids),
        "found_hit": len(found_hit),
        "recall": len(hit_ids) / len(bugs) if bugs else 0.0,
        "precision": len(found_hit) / len(found) if found else 0.0,
        "hit_ids": hit_ids,
    }


def recall_by(found: list[Span], bugs: list[Bug], key: str) -> dict[str, dict]:
    """Recall per group; key is 'family', 'difficulty' or 'split'."""
    groups: dict[str, list[Bug]] = {}
    for b in bugs:
        groups.setdefault(getattr(b, key), []).append(b)
    out = {}
    for name, members in sorted(groups.items()):
        hit = sum(hits_bug(found, b) for b in members)
        out[name] = {"hit": hit, "total": len(members), "recall": hit / len(members)}
    return out


def false_positives(found: list[Span], safe_files: list[str]) -> dict:
    """Findings on safe controls. fp_file_rate = share of safe files that drew any finding."""
    on_safe = [f for f in found if f.file in set(safe_files)]
    files_hit = {f.file for f in on_safe}
    return {
        "safe_files": len(safe_files),
        "files_with_findings": len(files_hit),
        "findings_on_safe": len(on_safe),
        "fp_file_rate": len(files_hit) / len(safe_files) if safe_files else 0.0,
    }


def summarize(values: list[float]) -> dict:
    """mean / min / max / sample std over repeats (std is 0 with fewer than 2 values)."""
    n = len(values)
    if n == 0:
        return {"n": 0, "mean": 0.0, "min": 0.0, "max": 0.0, "std": 0.0}
    mean = sum(values) / n
    std = (sum((v - mean) ** 2 for v in values) / (n - 1)) ** 0.5 if n > 1 else 0.0
    return {"n": n, "mean": mean, "min": min(values), "max": max(values), "std": std}


def compare_to_baseline(cand_recall: list[float], base_recall: list[float],
                        cand_cost: list[float], base_cost: list[float],
                        min_gain: float = 0.05, cheaper_by: float = 0.10) -> dict:
    """DEV-PLAN rule 8. A feature is 'better' only if its recall beats the baseline by more than
    the larger run-to-run std AND by at least min_gain (5 points). 'cheaper_same_recall' if recall
    is not worse than the spread and cost is at least cheaper_by (10%) lower. confidence is 'low'
    with fewer than 3 repeats on either side, since spread is then unreliable."""
    c, b = summarize(cand_recall), summarize(base_recall)
    spread = max(c["std"], b["std"])
    gain = c["mean"] - b["mean"]
    cost_c, cost_b = summarize(cand_cost)["mean"], summarize(base_cost)["mean"]
    if gain > spread and gain >= min_gain:
        verdict = "better"
    elif gain < -spread and -gain >= min_gain:
        verdict = "worse"
    elif gain >= -spread and cost_b > 0 and cost_c <= cost_b * (1 - cheaper_by):
        verdict = "cheaper_same_recall"
    else:
        verdict = "no_gain"
    return {"verdict": verdict, "recall_gain": gain, "spread": spread,
            "confidence": "low" if min(c["n"], b["n"]) < 3 else "ok"}
