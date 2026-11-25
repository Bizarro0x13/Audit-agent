import copy
import json
from pathlib import Path

import pytest

from agent.metrics import (
    Bug,
    Span,
    bug_from_truth,
    compare_to_baseline,
    false_positives,
    hits_bug,
    overlaps,
    recall_by,
    score,
    score_bugs,
    summarize,
)


def S(f, a, b):
    return Span(f, a, b)


def test_overlap_rules():
    assert overlaps(S("A", 1, 5), S("A", 5, 9))  # touching ends count
    assert not overlaps(S("A", 1, 4), S("A", 5, 9))
    assert not overlaps(S("A", 1, 9), S("B", 1, 9))  # different file


def test_score_recall_and_precision():
    truth = [S("A", 10, 20), S("B", 1, 5)]
    found = [S("A", 15, 16), S("A", 12, 13), S("C", 1, 2)]  # 2 hit the same bug, 1 miss
    r = score(found, truth)
    assert r["recall"] == 0.5 and r["truth_hit"] == 1
    assert r["precision"] == 2 / 3


def test_score_empty_findings():
    r = score([], [S("A", 1, 2)])
    assert r["recall"] == 0.0 and r["precision"] == 0.0


# ---- Phase 0.4 ----

BUGS = [
    Bug("B1", (S("A", 10, 20), S("A", 40, 45)), "access-control", "easy", "train"),
    Bug("B2", (S("B", 1, 5),), "arithmetic", "hard", "train"),
    Bug("B3", (S("C", 1, 9),), "access-control", "hard", "heldout"),
    Bug("B4", (S("D", 1, 3),), "arithmetic", "easy", "heldout"),
]


def test_hits_bug_through_primary_or_alternate_span():
    assert hits_bug([S("A", 12, 13)], BUGS[0])      # primary
    assert hits_bug([S("A", 44, 50)], BUGS[0])      # alternate
    assert not hits_bug([S("A", 25, 30)], BUGS[0])  # between the two
    assert not hits_bug([S("B", 10, 20)], BUGS[0])  # right lines, wrong file


def test_score_bugs_known_values():
    found = [S("A", 44, 44), S("A", 12, 13), S("B", 2, 2), S("Z", 1, 1)]
    r = score_bugs(found, BUGS)
    assert r["truth"] == 4 and r["truth_hit"] == 2          # B1 (twice) and B2
    assert r["hit_ids"] == ["B1", "B2"]
    assert r["recall"] == 0.5
    assert r["found_hit"] == 3 and r["precision"] == 3 / 4  # Z misses


def test_score_bugs_empty_inputs_no_division_by_zero():
    assert score_bugs([], BUGS)["precision"] == 0.0
    r = score_bugs([S("A", 1, 1)], [])
    assert r["recall"] == 0.0 and r["precision"] == 0.0


def test_recall_by_difficulty_family_split():
    found = [S("A", 12, 13), S("B", 2, 2)]  # hits B1 (easy/ac/train) and B2 (hard/arith/train)
    d = recall_by(found, BUGS, "difficulty")
    assert d["easy"] == {"hit": 1, "total": 2, "recall": 0.5}
    assert d["hard"] == {"hit": 1, "total": 2, "recall": 0.5}
    f = recall_by(found, BUGS, "family")
    assert f["access-control"]["recall"] == 0.5 and f["arithmetic"]["recall"] == 0.5
    s = recall_by(found, BUGS, "split")
    assert s["train"]["recall"] == 1.0 and s["heldout"]["recall"] == 0.0


def test_false_positive_rate_on_safe_files():
    safe = [f"Safe{i}.sol" for i in range(8)]
    found = [S("Safe0.sol", 1, 2), S("Safe0.sol", 5, 6), S("Safe3.sol", 1, 1), S("A", 1, 1)]
    r = false_positives(found, safe)
    assert r["files_with_findings"] == 2 and r["findings_on_safe"] == 3
    assert r["fp_file_rate"] == 0.25
    assert false_positives([S("A", 1, 1)], safe)["fp_file_rate"] == 0.0
    assert false_positives([], [])["fp_file_rate"] == 0.0


def test_summarize_spread_known_values():
    s = summarize([0.5, 0.7, 0.9])
    assert s["n"] == 3 and s["min"] == 0.5 and s["max"] == 0.9
    assert s["mean"] == pytest.approx(0.7) and s["std"] == pytest.approx(0.2)
    assert summarize([0.4])["std"] == 0.0
    assert summarize([])["n"] == 0


def test_compare_better_needs_gain_beyond_spread_and_five_points():
    base = [0.50, 0.52, 0.48]            # mean .50, std .02
    good = [0.70, 0.72, 0.68]
    r = compare_to_baseline(good, base, [1, 1, 1], [1, 1, 1])
    assert r["verdict"] == "better" and r["confidence"] == "ok"
    small = [0.53, 0.55, 0.51]           # +3 points: under the 5 point floor
    assert compare_to_baseline(small, base, [1] * 3, [1] * 3)["verdict"] == "no_gain"
    noisy_base = [0.30, 0.50, 0.70]      # std .2 swamps a +10 point gain
    cand = [0.55, 0.60, 0.65]            # mean .60
    assert compare_to_baseline(cand, noisy_base, [1] * 3, [1] * 3)["verdict"] == "no_gain"


def test_compare_cheaper_same_recall_and_worse():
    base = [0.6, 0.6, 0.6]
    same = [0.6, 0.6, 0.6]
    assert compare_to_baseline(same, base, [0.5] * 3, [1.0] * 3)["verdict"] == "cheaper_same_recall"
    assert compare_to_baseline(same, base, [0.95] * 3, [1.0] * 3)["verdict"] == "no_gain"  # <10%
    assert compare_to_baseline([0.4] * 3, base, [1] * 3, [1] * 3)["verdict"] == "worse"


def test_compare_flags_low_confidence_with_few_repeats():
    r = compare_to_baseline([0.9], [0.5], [1], [1])
    assert r["verdict"] == "better" and r["confidence"] == "low"


def test_bug_from_truth_and_real_truth_file_round_trip():
    entry = {"id": "X", "file": "F.sol", "line_start": 3, "line_end": 4,
             "family": "arithmetic", "difficulty": "hard", "split": "train", "alt_ranges": [[9, 10]]}
    b = bug_from_truth(entry)
    assert b.spans == (S("F.sol", 3, 4), S("F.sol", 9, 10)) and b.difficulty == "hard"
    truth = json.loads((Path(__file__).resolve().parent.parent / "eval" / "truth.json").read_text())
    entries = [e for t in truth["targets"].values() for e in t["truth"]]
    bugs = [bug_from_truth(e) for e in entries]
    assert len(bugs) == 23
    # a finding on every primary span finds every bug
    found = [b.spans[0] for b in bugs]
    assert score_bugs(found, bugs)["recall"] == 1.0
    # and a finding only on an alternate span still finds that bug
    e16 = next(b for b in bugs if b.id == "E16")
    assert hits_bug([e16.spans[1]], e16)
    assert copy.deepcopy(entries) == entries
