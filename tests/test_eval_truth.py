"""Checks on eval/truth.json: schema, line ranges, frozen train/heldout split (step 0.2)."""

import copy
import importlib.util
import shutil
import subprocess
import tempfile
from collections import defaultdict
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("eval_schema", ROOT / "eval" / "schema.py")
schema = importlib.util.module_from_spec(spec)
spec.loader.exec_module(schema)

TRUTH = schema.load()
BUGS = schema.bugs(TRUTH)
# Levels that teach near-identical lessons must sit on the same side of the split.
SIBLINGS = [("E05", "E06"), ("E17", "E18")]


def test_truth_schema_valid():
    assert schema.validate(TRUTH) == []


@pytest.mark.skipif(not schema.LEVELS.exists(), reason="Ethernaut cache not cloned yet")
def test_truth_ranges_inside_real_files_and_non_blank():
    assert schema.validate(TRUTH, schema.LEVELS) == []


def test_every_bug_matches_a_row_in_targets_md():
    text = (ROOT / "eval" / "targets.md").read_text()
    for b in BUGS:
        row = next(line for line in text.splitlines() if line.startswith(f"| {b['id']} "))
        cells = [c.strip() for c in row.strip("|").split("|")]
        assert cells[2] == b["file"] and cells[3] == b["family"] and cells[4] == b["difficulty"], b


def test_total_bugs_at_least_25_including_unseen():
    assert len(BUGS) >= 25
    assert sum(b["split"] == "unseen" for b in BUGS) >= 6


def test_unseen_files_are_ours_and_exist():
    unseen = [b for b in BUGS if b["split"] == "unseen"]
    for b in unseen:
        assert (schema.UNSEEN_DIR / b["file"]).exists(), b
    # no unseen file shares a name with an Ethernaut level used elsewhere
    other = {b["file"] for b in BUGS if b["split"] != "unseen"}
    assert not ({b["file"] for b in unseen} & other)


def test_unseen_bug_ranges_valid_against_unseen_dir():
    assert schema.validate(TRUTH, None, schema.UNSEEN_DIR) == []


def test_unseen_and_heldout_never_in_tuning_inputs():
    tuning = schema.tuning_targets(TRUTH)
    assert tuning and all(t["split"] == "train" for t in tuning.values())
    names = set(tuning)
    for n, t in TRUTH["targets"].items():
        if t["split"] in {"heldout", "unseen"}:
            assert n not in names


@pytest.mark.skipif(shutil.which("forge") is None, reason="forge not installed")
def test_unseen_contracts_compile():
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / "src").mkdir()
        for p in schema.UNSEEN_DIR.glob("*.sol"):
            shutil.copy(p, Path(d) / "src" / p.name)
        (Path(d) / "foundry.toml").write_text('[profile.default]\nsrc="src"\nout="out"\nlibs=[]\n')
        r = subprocess.run(["forge", "build"], cwd=d, capture_output=True, text=True,
                           check=False, timeout=600)
        assert r.returncode == 0, r.stderr[-800:]


def test_split_ratio_train_vs_heldout():
    seeded = [b for b in BUGS if b["split"] in {"train", "heldout"}]
    share = sum(b["split"] == "train" for b in seeded) / len(seeded)
    assert 0.55 <= share <= 0.65, share


def test_split_is_frozen():
    # If this fails, a bug was added, removed or moved between splits. After review,
    # run `python eval/schema.py --freeze`. Never move a target after seeing results.
    assert schema.LOCK.read_text().strip() == schema.split_hash(TRUTH)


def test_families_with_two_or_more_bugs_appear_in_both_splits():
    by_family = defaultdict(set)
    count = defaultdict(int)
    for b in BUGS:
        if b["split"] == "unseen":
            continue  # unseen is a separate judging set; it may add families
        by_family[b["family"]].add(b["split"])
        count[b["family"]] += 1
    for family, n in count.items():
        if n >= 2:
            assert {"train", "heldout"} <= by_family[family], family


def test_hard_bugs_in_both_splits():
    for split in ("train", "heldout"):
        assert sum(b["difficulty"] == "hard" for b in BUGS if b["split"] == split) >= 3


def test_sibling_levels_share_a_split():
    split = {b["id"]: b["split"] for b in BUGS}
    for a, b in SIBLINGS:
        assert split[a] == split[b], (a, b)


def test_same_file_never_in_two_splits():
    files = defaultdict(set)
    for b in BUGS:
        files[b["file"]].add(b["split"])
    assert all(len(s) == 1 for s in files.values())


def test_split_hash_changes_when_a_bug_moves():
    moved = copy.deepcopy(TRUTH)
    first = next(iter(moved["targets"]))
    moved["targets"][first]["truth"][0]["split"] = "heldout"
    assert schema.split_hash(moved) != schema.split_hash(TRUTH)
