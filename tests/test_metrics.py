from agent.metrics import Span, overlaps, score


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
