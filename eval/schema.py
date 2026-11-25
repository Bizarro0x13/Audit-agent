"""Validation for eval/truth.json and the frozen train/heldout split.

Usage:
  python eval/schema.py            validate truth.json (and check the split lock)
  python eval/schema.py --freeze   rewrite eval/split.lock after a reviewed, intentional change
"""

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
TRUTH = HERE / "truth.json"
LOCK = HERE / "split.lock"
LEVELS = HERE / ".cache" / "ethernaut" / "contracts" / "src" / "levels"
SPLITS = {"train", "heldout", "unseen"}
DIFFICULTIES = {"easy", "medium", "hard"}
REQUIRED = ["id", "file", "line_start", "line_end", "bug_class", "family", "difficulty", "split"]


def load(path: Path = TRUTH) -> dict:
    return json.loads(path.read_text())


def bugs(truth: dict) -> list[dict]:
    return [b for t in truth["targets"].values() for b in t["truth"]]


def split_hash(truth: dict) -> str:
    """Hash of (bug id, split) pairs. Changes only if a bug is added, removed or moved."""
    pairs = sorted(f"{b['id']}:{b['split']}" for b in bugs(truth))
    return hashlib.sha256("\n".join(pairs).encode()).hexdigest()


def validate(truth: dict, levels: Path | None = None) -> list[str]:
    errs: list[str] = []
    seen_ids: set[str] = set()
    for tname, t in truth["targets"].items():
        if t.get("split") not in SPLITS:
            errs.append(f"{tname}: bad split {t.get('split')!r}")
        for b in t["truth"]:
            where = f"{tname}/{b.get('id', '?')}"
            for key in REQUIRED:
                if key not in b:
                    errs.append(f"{where}: missing {key}")
            if any(k not in b for k in REQUIRED):
                continue
            if b["id"] in seen_ids:
                errs.append(f"{where}: duplicate id")
            seen_ids.add(b["id"])
            if b["split"] != t["split"]:
                errs.append(f"{where}: bug split {b['split']} differs from target split {t['split']}")
            if b["difficulty"] not in DIFFICULTIES:
                errs.append(f"{where}: bad difficulty {b['difficulty']!r}")
            if b["file"] not in t["files"]:
                errs.append(f"{where}: file {b['file']} not listed in the target's files")
            ranges = [(b["line_start"], b["line_end"])] + [tuple(r) for r in b.get("alt_ranges", [])]
            for start, end in ranges:
                if not (1 <= start <= end):
                    errs.append(f"{where}: invalid range {start}-{end}")
                    continue
                if levels is not None and (levels / b["file"]).exists():
                    lines = (levels / b["file"]).read_text().splitlines()
                    if end > len(lines):
                        errs.append(f"{where}: range {start}-{end} beyond {b['file']} ({len(lines)} lines)")
                    elif not any(x.strip() for x in lines[start - 1 : end]):
                        errs.append(f"{where}: range {start}-{end} is blank")
    return errs


def main() -> int:
    truth = load()
    if "--freeze" in sys.argv:
        LOCK.write_text(split_hash(truth) + "\n")
        print("split.lock updated:", split_hash(truth))
        return 0
    errs = validate(truth, LEVELS if LEVELS.exists() else None)
    if LOCK.exists() and LOCK.read_text().strip() != split_hash(truth):
        errs.append("split changed since it was frozen (run --freeze only after review)")
    for e in errs:
        print("ERROR:", e)
    print("ok" if not errs else f"{len(errs)} problem(s)")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
