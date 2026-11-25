"""Checks on the evaluation target selection (eval/targets.md), step 0.1."""

import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
TARGETS = ROOT / "eval" / "targets.md"
LEVELS = ROOT / "eval" / ".cache" / "ethernaut" / "contracts" / "src" / "levels"
FAMILIES = {
    "reentrancy", "access-control", "denial-of-service", "delegatecall-storage", "randomness",
    "data-exposure", "callback-trust", "arithmetic", "caller-assumption", "unchecked-return",
    "calldata-encoding", "price-manipulation", "input-validation", "accounting",
}
DIFFICULTIES = {"easy", "medium", "hard"}


def rows():
    out = []
    for line in TARGETS.read_text().splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 6 and cells[0].startswith("E") and cells[0][1:].isdigit():
            out.append(dict(zip(["id", "level", "file", "family", "difficulty", "cross"], cells)))
    return out


def test_selection_has_enough_bugs_for_phase_0():
    # 25 total is the goal; 6 more come from the unseen targets written in step 0.6
    assert len(rows()) >= 19


def test_ids_unique_and_fields_valid():
    rs = rows()
    assert len({r["id"] for r in rs}) == len(rs)
    for r in rs:
        assert r["family"] in FAMILIES, r
        assert r["difficulty"] in DIFFICULTIES, r
        assert r["cross"] in {"yes", "no"}, r
        assert r["file"].endswith(".sol"), r


def test_mix_of_difficulty_and_multi_contract_cases():
    rs = rows()
    assert {r["difficulty"] for r in rs} == DIFFICULTIES
    assert sum(r["difficulty"] == "hard" for r in rs) >= 5
    assert sum(r["cross"] == "yes" for r in rs) >= 5
    assert len({r["family"] for r in rs}) >= 10


@pytest.mark.skipif(not LEVELS.exists(), reason="Ethernaut cache not cloned yet")
def test_every_selected_file_exists_at_pinned_commit():
    for r in rows():
        assert (LEVELS / r["file"]).exists(), r


def test_upstream_cache_is_gitignored_and_not_tracked():
    ignored = subprocess.run(
        ["git", "check-ignore", "-q", "eval/.cache/ethernaut"], check=False, cwd=ROOT
    ).returncode
    assert ignored == 0
    tracked = subprocess.run(
        ["git", "ls-files", "eval/.cache"], check=False, cwd=ROOT, capture_output=True, text=True
    ).stdout
    assert tracked.strip() == ""
