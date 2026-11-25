"""Checks on the safe controls (eval/safe), step 0.3."""

import importlib.util
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("eval_schema", ROOT / "eval" / "schema.py")
schema = importlib.util.module_from_spec(spec)
spec.loader.exec_module(schema)

TRUTH = schema.load()
MANIFEST = json.loads(schema.SAFE_MANIFEST.read_text())
CONTROLS = MANIFEST["controls"]
HINTS = re.compile(r"vulnerab|\bbug\b|exploit|attack|insecure|unsafe|reentran|\bsafe\b", re.IGNORECASE)


def test_at_least_eight_controls_in_both_splits():
    assert len(CONTROLS) >= 8
    assert {c["split"] for c in CONTROLS} == {"train", "heldout"}


def test_safe_manifest_is_valid():
    assert schema.validate_safe(MANIFEST, TRUTH) == []


def test_safe_files_exist_and_are_all_listed():
    on_disk = {p.name for p in schema.SAFE_DIR.glob("*.sol")}
    assert on_disk == {c["file"] for c in CONTROLS}


def test_safe_not_flagged_by_truth():
    safe_files = {c["file"] for c in CONTROLS}
    truth_files = {b["file"] for b in schema.bugs(TRUTH)}
    assert not (safe_files & truth_files)
    for t in TRUTH["targets"].values():
        assert not (safe_files & set(t["files"]))


def test_every_twin_family_matches_and_splits_agree():
    bad = schema.validate_safe(MANIFEST, TRUTH)
    assert bad == []


def test_validator_catches_split_mismatch():
    broken = json.loads(json.dumps(MANIFEST))
    broken["controls"][0]["split"] = "heldout"  # S01's twin E01 is train
    assert any("differs from twin" in e for e in schema.validate_safe(broken, TRUTH))


def test_validator_catches_unlisted_file(tmp_path):
    shutil.copy(schema.SAFE_DIR / CONTROLS[0]["file"], tmp_path / "Extra.sol")
    errs = schema.validate_safe({"controls": []}, TRUTH, tmp_path)
    assert any("not in manifest" in e for e in errs)


def test_safe_files_carry_no_hint_comments():
    # The control must not tell the model it is safe (or what pattern it guards against).
    for c in CONTROLS:
        text = (schema.SAFE_DIR / c["file"]).read_text()
        comments = " ".join(re.findall(r"//[^\n]*|/\*.*?\*/", text, re.DOTALL))
        comments = comments.replace("SPDX-License-Identifier: MIT", "")
        assert not HINTS.search(comments), c["file"]
        assert not HINTS.search(c["file"].replace("Safe", "", 1)), c["file"]


@pytest.mark.skipif(shutil.which("forge") is None, reason="forge not installed")
def test_safe_files_compile_with_forge():
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / "src").mkdir()
        for p in schema.SAFE_DIR.glob("*.sol"):
            shutil.copy(p, Path(d) / "src" / p.name)
        (Path(d) / "foundry.toml").write_text('[profile.default]\nsrc="src"\nout="out"\nlibs=[]\n')
        r = subprocess.run(
            ["forge", "build"], cwd=d, capture_output=True, text=True, check=False, timeout=600
        )
        assert r.returncode == 0, r.stderr[-800:]
