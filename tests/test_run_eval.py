"""Tests for the evaluation harness (eval/run_eval.py), step 0.5. No network anywhere."""

import importlib.util
import json
from pathlib import Path

import pytest

from agent.metrics import Bug, Span

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("run_eval", ROOT / "eval" / "run_eval.py")
ev = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ev)

TRUTH = json.loads((ROOT / "eval" / "truth.json").read_text())
MANIFEST = json.loads((ROOT / "eval" / "safe" / "manifest.json").read_text())


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    import anthropic

    def boom(*a, **k):
        raise AssertionError("tests must not create a real Anthropic client")

    monkeypatch.setattr(anthropic, "Anthropic", boom)


def targets(which):
    return ev.build_targets(TRUTH, MANIFEST, which, None)


def test_split_selection():
    assert {t.split for t in targets("train") if t.kind == "vuln"} == {"train"}
    assert all(t.kind == "vuln" for t in targets("train"))
    assert {t.split for t in targets("heldout")} == {"heldout"}
    safe = targets("safe")
    assert all(t.kind == "safe" and not t.bugs for t in safe)
    assert {t.name for t in safe} == {"safe-train", "safe-heldout"}
    allt = targets("all")
    assert sum(len(t.bugs) for t in allt) == 23
    assert {t.kind for t in allt} == {"vuln", "safe"}
    assert targets("unseen") == []  # none written yet (step 0.6)


def test_dry_run_end_to_end_writes_json_and_markdown(tmp_path):
    ev.main(["--dry-run", "--split", "heldout", "--repeats", "2", "--out-dir", str(tmp_path),
             "--variants", "single,graph_verify"])
    rows = json.loads((tmp_path / "results.json").read_text())
    text = (tmp_path / "results.md").read_text()
    # 4 heldout targets x 2 variants x 2 repeats
    assert len(rows) == 16 and all(r["status"] == "ok" for r in rows)
    assert "DRY RUN" in text


def test_results_table_has_required_columns(tmp_path):
    ev.main(["--dry-run", "--split", "all", "--repeats", "1", "--out-dir", str(tmp_path),
             "--variants", "single"])
    text = (tmp_path / "results.md").read_text()
    for col in ["variant", "group", "recall", "precision", "FP file rate", "cost",
                "tokens in/out", "seconds", "repeats used", "failed runs"]:
        assert col in text
    for group in ["train", "heldout", "safe-train", "safe-heldout"]:
        assert f"| {group} |" in text
    assert "Recall by difficulty" in text


def test_dry_run_never_overwrites_real_results(capsys):
    before = (ROOT / "eval" / "results.md").read_text()
    ev.main(["--dry-run", "--split", "safe", "--repeats", "1", "--variants", "single"])
    assert (ROOT / "eval" / "results.md").read_text() == before
    written = [x for x in capsys.readouterr().out.splitlines() if x.startswith("written to ")]
    assert written and str(ROOT / "eval") != written[-1].removeprefix("written to ")


def test_failed_run_is_recorded_not_fatal():
    class Boom:
        messages = None

        def __init__(self):
            self.messages = self

        def create(self, **kwargs):
            raise RuntimeError("provider exploded")

    t = targets("heldout")[0]
    d = ev.stage(t, dry_run=True)
    r = ev.run_variant("single", d, client=Boom())
    assert r["status"].startswith("error: ") and r["spans"] == []


def test_cost_cap_is_marked_and_excluded_from_averages(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "eval"))  # eval/ is not a package
    from dryrun import DryRunClient

    monkeypatch.setenv("AGENT_MAX_USD", "0.0000001")
    t = targets("heldout")[0]
    d = ev.stage(t, dry_run=True)
    r = ev.run_variant("single", d, client=DryRunClient({}, set()))
    assert r["status"] == "cost_cap"


def vrow(variant, target, run, hit, truth, found, found_hit, status="ok", hit_ids=()):
    return {"variant": variant, "target": target, "kind": "vuln", "split": "heldout", "run": run,
            "status": status, "cost": 0.1, "seconds": 1.0, "in_tokens": 10, "out_tokens": 5,
            "gate_failures": 0, "found": found, "spans": [], "truth": truth, "truth_hit": hit,
            "found_hit": found_hit, "hit_ids": list(hit_ids)}


def T(name, bugs, kind="vuln", split="heldout"):
    return ev.Target(name, kind, split, ["F.sol"], None, bugs)


def test_aggregate_known_values_and_failed_repeat_excluded():
    ts = [T("a", [Bug("1", (Span("F.sol", 1, 2),)), Bug("2", (Span("F.sol", 5, 6),))])]
    rows = [
        vrow("v", "a", 0, hit=2, truth=2, found=2, found_hit=2),      # recall 1.0
        vrow("v", "a", 1, hit=1, truth=2, found=2, found_hit=1),      # recall 0.5
        vrow("v", "a", 2, hit=0, truth=2, found=0, found_hit=0, status="cost_cap"),
    ]
    a = ev.aggregate(rows, ts, repeats=3)[0]
    assert a["repeats_used"] == 2 and a["repeats_asked"] == 3 and a["failed_runs"] == 1
    assert a["metrics"]["recall"]["mean"] == pytest.approx(0.75)
    assert a["metrics"]["precision"]["mean"] == pytest.approx(0.75)
    assert a["metrics"]["recall"]["n"] == 2


def test_aggregate_drops_a_repeat_if_any_target_in_the_group_failed():
    ts = [T("a", []), T("b", [])]
    rows = [
        vrow("v", "a", 0, 1, 1, 1, 1), vrow("v", "b", 0, 1, 1, 1, 1),
        vrow("v", "a", 1, 1, 1, 1, 1), vrow("v", "b", 1, 0, 1, 0, 0, status="error: X"),
    ]
    a = ev.aggregate(rows, ts, repeats=2)[0]
    assert a["repeats_used"] == 1 and a["failed_runs"] == 1


def test_safe_group_reports_fp_rate_not_recall():
    ts = [T("safe-train", [], kind="safe", split="train")]
    rows = [{"variant": "v", "target": "safe-train", "kind": "safe", "split": "train", "run": 0,
             "status": "ok", "cost": 0.1, "seconds": 1.0, "in_tokens": 1, "out_tokens": 1,
             "gate_failures": 0, "found": 3, "spans": [], "safe_files": 8,
             "files_with_findings": 2, "findings_on_safe": 3}]
    a = ev.aggregate(rows, ts, repeats=1)[0]
    assert a["metrics"]["fp_rate"]["mean"] == pytest.approx(0.25)
    assert "recall" not in a["metrics"]


def test_difficulty_recall_known_values():
    bugs = [Bug("1", (Span("F.sol", 1, 2),), difficulty="easy"),
            Bug("2", (Span("F.sol", 5, 6),), difficulty="hard"),
            Bug("3", (Span("F.sol", 8, 9),), difficulty="hard")]
    ts = [T("a", bugs)]
    rows = [vrow("v", "a", 0, 2, 3, 2, 2, hit_ids=["1", "3"])]
    d = ev.difficulty_recall(rows, ts, repeats=1)["v"]
    assert d["easy"]["mean"] == 1.0 and d["hard"]["mean"] == 0.5


def test_stage_makes_stubs_only_in_dry_run(tmp_path):
    t = ev.Target("x", "vuln", "train", ["Missing.sol"], tmp_path,
                  [Bug("1", (Span("Missing.sol", 40, 50),))])
    d = ev.stage(t, dry_run=True)
    assert len((d / "Missing.sol").read_text().splitlines()) >= 50
    with pytest.raises(FileNotFoundError):
        ev.stage(t, dry_run=False)


def test_compare_section_uses_single_as_baseline():
    def agg(variant, recalls, cost):
        return {"variant": variant, "group": "heldout", "kind": "vuln",
                "per_repeat": [{"recall": r, "cost": cost} for r in recalls]}
    lines = ev.compare_section([agg("single", [0.5, 0.5, 0.5], 1.0),
                                agg("graph", [0.8, 0.8, 0.8], 2.0)])
    assert any("graph" in x and "better" in x for x in lines)
    assert ev.compare_section([agg("graph", [0.8], 1.0)]) == []  # no baseline present
