"""Evaluation harness: run variants over a chosen split, score against truth.json.

Usage:
  uv run python eval/run_eval.py --split heldout --repeats 3
  uv run python eval/run_eval.py --split all --variants single,graph_verify
  uv run python eval/run_eval.py --dry-run          # fake client, no network, for CI

Splits: train | heldout | unseen (vulnerable targets), safe (safe controls), all.
A real run needs ANTHROPIC_API_KEY (from .env) and spends money; AGENT_MAX_USD caps each run.
Dry-run results are written to a temp folder, never over eval/results.*.
"""

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from agent.approval import approve_all
from agent.baseline import single_agent
from agent.env import load_env
from agent.graph import build_graph
from agent.metrics import (
    Bug,
    Span,
    bug_from_truth,
    compare_to_baseline,
    false_positives,
    score_bugs,
    summarize,
)
from agent.models import CostCapExceeded, Model
from agent.rag import Index
from agent.store import Store
from agent.tools.files import FileTools

HERE = Path(__file__).parent
CACHE = HERE / ".cache" / "ethernaut"
VARIANTS = ["single", "graph_noverify", "graph_noverify_rag", "graph_verify", "graph_verify_rag"]
SPLIT_CHOICES = ["train", "heldout", "unseen", "safe", "all"]


@dataclass
class Target:
    name: str
    kind: str  # "vuln" or "safe"
    split: str
    files: list[str]
    src: Path | None  # folder holding the files (None = not available, dry-run stubs them)
    bugs: list[Bug] = field(default_factory=list)


def fetch(truth: dict) -> Path:
    """Clone the pinned commit once into the gitignored cache."""
    if not (CACHE / ".git").exists():
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "clone", "-q", truth["repo"], str(CACHE)], check=True)
    subprocess.run(["git", "-C", str(CACHE), "checkout", "-q", truth["commit"]], check=True)
    return CACHE / truth["dir"]


def build_targets(truth: dict, manifest: dict, which: str, levels: Path | None) -> list[Target]:
    """Targets for a split. `safe` and `all` include the safe controls (grouped by split)."""
    out = []
    for name, t in truth["targets"].items():
        if which in (t["split"], "all"):
            bugs = [bug_from_truth(x) for x in t["truth"]]
            out.append(Target(name, "vuln", t["split"], t["files"], levels, bugs))
    if which in ("safe", "all"):
        by_split: dict[str, list[str]] = {}
        for c in manifest["controls"]:
            by_split.setdefault(c["split"], []).append(c["file"])
        for split, files in sorted(by_split.items()):
            out.append(Target(f"safe-{split}", "safe", split, files, HERE / "safe"))
    return out


def stage(target: Target, dry_run: bool = False) -> Path:
    """Copy the target's files into a temp folder. In dry-run, missing upstream files are
    replaced by stubs long enough for every labeled range."""
    d = Path(tempfile.mkdtemp(prefix="eval-target-"))
    needed = {}
    for b in target.bugs:
        for s in b.spans:
            needed[s.file] = max(needed.get(s.file, 0), s.line_end)
    for f in target.files:
        src = target.src / f if target.src else None
        if src is not None and src.exists():
            shutil.copy(src, d / f)
        elif dry_run:
            n = needed.get(f, 20) + 10
            (d / f).write_text("\n".join(f"// stub line {i}" for i in range(1, n + 1)) + "\n")
        else:
            raise FileNotFoundError(f"{f} not found under {target.src}")
    return d


def run_variant(variant: str, target_dir: Path, client=None, knowledge: Path | None = None) -> dict:
    store = Store(":memory:")
    store.start_run("e", str(target_dir))
    model = Model(store, "e", client=client)
    tools = FileTools(target_dir, store, "e")
    started = time.time()
    status = "ok"
    findings = []
    try:
        if variant == "single":
            findings = single_agent(model, tools)
        else:
            rag = Index.build(knowledge or HERE.parent / "knowledge") if variant.endswith("_rag") else None
            graph = build_graph(model, tools, store, approve_all,
                                report_path=target_dir / "report.md",
                                verify=variant.startswith("graph_verify"), rag=rag)
            result = graph.invoke({"run_id": "e", "target_root": str(target_dir),
                                   "auto_approved": True})
            approved = set(result.get("approved_ids", []))
            findings = [f for f in result.get("findings", []) if f.id in approved]
    except CostCapExceeded:
        status = "cost_cap"
    except Exception as exc:  # noqa: BLE001 - keep evaluating; the failure is recorded
        status = f"error: {type(exc).__name__}"
    tokens = store.db.execute(
        "SELECT COALESCE(SUM(input_tokens),0), COALESCE(SUM(output_tokens),0) FROM model_calls"
    ).fetchone()
    gate_fails = store.db.execute("SELECT COUNT(*) FROM gate_results WHERE passed = 0").fetchone()[0]
    return {
        "status": status,
        "spans": [Span(Path(f.file).name, f.line_start, f.line_end) for f in findings],
        "cost": store.run_cost("e"),
        "seconds": time.time() - started,
        "in_tokens": tokens[0],
        "out_tokens": tokens[1],
        "gate_failures": gate_fails,
    }


def run_all(targets: list[Target], variants: list[str], repeats: int, dry_run: bool = False,
            client_factory: Callable[[], object] | None = None, log=print) -> list[dict]:
    """One row per (target, variant, repeat). A failed run is a row with status != ok."""
    rows = []
    for t in targets:
        for variant in variants:
            for i in range(repeats):
                target_dir = stage(t, dry_run)
                r = run_variant(variant, target_dir, client_factory() if client_factory else None)
                spans = r["spans"]
                row = {"variant": variant, "target": t.name, "kind": t.kind, "split": t.split,
                       "run": i, "status": r["status"], "cost": r["cost"], "seconds": r["seconds"],
                       "in_tokens": r["in_tokens"], "out_tokens": r["out_tokens"],
                       "gate_failures": r["gate_failures"], "found": len(spans),
                       "spans": [[s.file, s.line_start, s.line_end] for s in spans]}
                if t.kind == "vuln":
                    m = score_bugs(spans, t.bugs)
                    row |= {"truth": m["truth"], "truth_hit": m["truth_hit"],
                            "found_hit": m["found_hit"], "hit_ids": m["hit_ids"]}
                else:
                    fp = false_positives(spans, t.files)
                    row |= {"safe_files": fp["safe_files"],
                            "files_with_findings": fp["files_with_findings"],
                            "findings_on_safe": fp["findings_on_safe"]}
                rows.append(row)
                log(f"{variant:19} {t.name:10} run{i}: {row['status']} found {row['found']} "
                    f"cost ${row['cost']:.3f} {row['seconds']:.0f}s")
    return rows


# ---- aggregation ----------------------------------------------------------------------


def group_key(t: Target) -> str:
    return t.name if t.kind == "safe" else t.split


def usable_repeats(rows: list[dict], variant: str, names: set[str], repeats: int) -> list[int]:
    """Repeat indices where every target in the group ran to completion. A repeat with any
    failed or cost-capped run is excluded from averages (and counted in the table)."""
    keep = []
    for i in range(repeats):
        rs = [r for r in rows if r["variant"] == variant and r["run"] == i and r["target"] in names]
        if len(rs) == len(names) and all(r["status"] == "ok" for r in rs):
            keep.append(i)
    return keep


def aggregate(rows: list[dict], targets: list[Target], repeats: int) -> list[dict]:
    """One entry per (variant, group) with per-metric summaries across usable repeats."""
    groups: dict[str, list[Target]] = {}
    for t in targets:
        groups.setdefault(group_key(t), []).append(t)
    out = []
    for variant in dict.fromkeys(r["variant"] for r in rows):
        for gname, ts in groups.items():
            names = {t.name for t in ts}
            keep = usable_repeats(rows, variant, names, repeats)
            mine = [r for r in rows if r["variant"] == variant and r["target"] in names]
            per = []
            for i in keep:
                rs = [r for r in mine if r["run"] == i]
                if ts[0].kind == "vuln":
                    th, tt = sum(r["truth_hit"] for r in rs), sum(r["truth"] for r in rs)
                    fh, ff = sum(r["found_hit"] for r in rs), sum(r["found"] for r in rs)
                    m = {"recall": th / tt if tt else 0.0, "precision": fh / ff if ff else 0.0}
                else:
                    sf = sum(r["safe_files"] for r in rs)
                    m = {"fp_rate": sum(r["files_with_findings"] for r in rs) / sf if sf else 0.0}
                m |= {"findings": sum(r["found"] for r in rs), "cost": sum(r["cost"] for r in rs),
                      "seconds": sum(r["seconds"] for r in rs),
                      "in_tokens": sum(r["in_tokens"] for r in rs),
                      "out_tokens": sum(r["out_tokens"] for r in rs)}
                per.append(m)
            keys = per[0].keys() if per else []
            out.append({
                "variant": variant, "group": gname, "kind": ts[0].kind, "repeats_used": len(keep),
                "repeats_asked": repeats,
                "failed_runs": sum(r["status"] != "ok" for r in mine),
                "metrics": {k: summarize([p[k] for p in per]) for k in keys},
                "per_repeat": per,
            })
    return out


def difficulty_recall(rows: list[dict], targets: list[Target], repeats: int) -> dict:
    """variant -> difficulty -> summary of recall over repeats where all vuln targets completed."""
    vt = [t for t in targets if t.kind == "vuln"]
    names = {t.name for t in vt}
    diff_of = {b.id: b.difficulty for t in vt for b in t.bugs}
    totals: dict[str, int] = {}
    for d in diff_of.values():
        totals[d] = totals.get(d, 0) + 1
    out: dict[str, dict] = {}
    for variant in dict.fromkeys(r["variant"] for r in rows):
        keep = usable_repeats(rows, variant, names, repeats)
        per: dict[str, list[float]] = {d: [] for d in totals}
        for i in keep:
            hit = {h for r in rows if r["variant"] == variant and r["run"] == i
                   and r["target"] in names for h in r["hit_ids"]}
            for d, total in totals.items():
                per[d].append(sum(1 for h in hit if diff_of.get(h) == d) / total)
        out[variant] = {d: summarize(v) for d, v in per.items()}
    return out


# ---- rendering ------------------------------------------------------------------------


def pct(s: dict) -> str:
    return f"{s['mean']:.0%} ±{s['std']:.0%}" if s["n"] else "n/a"


def render(rows, targets, repeats, truth, dry_run: bool) -> str:
    agg = aggregate(rows, targets, repeats)
    n_bugs = sum(len(t.bugs) for t in targets)
    banner = ("**DRY RUN: fake client, numbers say nothing about accuracy.**\n\n" if dry_run else "")
    intro = (
        f"Targets: Ethernaut @ `{truth['commit'][:10]}` plus our own safe controls. "
        f"{len(targets)} target group(s), {n_bugs} labeled bugs in this run. "
        f"{repeats} repeat(s); mean ± std over repeats that fully completed."
    )
    caveats = (
        "Caveats: ground truth is a short list of deliberate bugs, so a finding that hits none of "
        "them may still be real and precision is a lower bound. Safe controls are original code "
        "reviewed once (see eval/safe/REVIEW.md); a finding on one counts as a false positive. "
        "Ethernaut is public and may be in model training data. Cost uses published per-model "
        "prices (models.py); token counts are exact. Treat differences inside the spread as noise."
    )
    header = (
        "| variant | group | recall | precision | FP file rate | findings | cost | "
        "tokens in/out | seconds | repeats used | failed runs |"
    )
    out = ["# Evaluation results", "", banner + intro, "", caveats, "", header,
           "|---|---|---|---|---|---|---|---|---|---|---|"]
    for a in agg:
        m = a["metrics"]
        if not m:
            out.append(f"| {a['variant']} | {a['group']} | n/a | n/a | n/a | n/a | n/a | n/a | n/a "
                       f"| 0/{a['repeats_asked']} | {a['failed_runs']} |")
            continue
        rec = pct(m["recall"]) if "recall" in m else "-"
        prec = pct(m["precision"]) if "precision" in m else "-"
        fp = pct(m["fp_rate"]) if "fp_rate" in m else "-"
        out.append(
            f"| {a['variant']} | {a['group']} | {rec} | {prec} | {fp} | {m['findings']['mean']:.1f} "
            f"| ${m['cost']['mean']:.3f} | {m['in_tokens']['mean']:.0f}/{m['out_tokens']['mean']:.0f} "
            f"| {m['seconds']['mean']:.0f} | {a['repeats_used']}/{a['repeats_asked']} "
            f"| {a['failed_runs']} |")
    dr = difficulty_recall(rows, targets, repeats)
    if any(t.kind == "vuln" for t in targets):
        diffs = ["easy", "medium", "hard"]
        out += ["", "## Recall by difficulty (all vulnerable targets in this run)", "",
                "| variant | " + " | ".join(diffs) + " |", "|---|" + "---|" * len(diffs)]
        for v, per in dr.items():
            out.append(f"| {v} | " + " | ".join(pct(per[d]) if d in per else "-" for d in diffs) + " |")
    out += compare_section(agg)
    return "\n".join(out) + "\n"


def compare_section(agg: list[dict]) -> list[str]:
    """Rule 8 verdict of each variant against `single`, per vulnerable group."""
    base = {a["group"]: a for a in agg if a["variant"] == "single" and a["kind"] == "vuln"}
    lines = []
    for a in agg:
        b = base.get(a["group"])
        if a["variant"] == "single" or a["kind"] != "vuln" or b is None:
            continue
        if not a["per_repeat"] or not b["per_repeat"]:
            continue
        r = compare_to_baseline([p["recall"] for p in a["per_repeat"]],
                                [p["recall"] for p in b["per_repeat"]],
                                [p["cost"] for p in a["per_repeat"]],
                                [p["cost"] for p in b["per_repeat"]])
        lines.append(f"| {a['variant']} | {a['group']} | {r['verdict']} | "
                     f"{r['recall_gain']:+.0%} | ±{r['spread']:.0%} | {r['confidence']} |")
    if not lines:
        return []
    return ["", "## Rule 8 comparison against `single`", "",
            "| variant | group | verdict | recall gain | spread | confidence |",
            "|---|---|---|---|---|---|", *lines]


def write_results(rows, targets, repeats, truth, out_dir: Path, dry_run: bool) -> str:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "results.json").write_text(json.dumps(rows, indent=2))
    text = render(rows, targets, repeats, truth, dry_run)
    (out_dir / "results.md").write_text(text)
    return text


def main(argv: list[str] | None = None) -> None:
    load_env()
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=SPLIT_CHOICES, default="all")
    ap.add_argument("--repeats", type=int, default=1)
    ap.add_argument("--variants", default=",".join(VARIANTS))
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--out-dir", type=Path, default=None)
    args = ap.parse_args(argv)
    variants = args.variants.split(",")

    truth = json.loads((HERE / "truth.json").read_text())
    manifest = json.loads((HERE / "safe" / "manifest.json").read_text())
    if args.dry_run:
        levels = CACHE / truth["dir"] if (CACHE / ".git").exists() else None
    else:
        levels = fetch(truth)
    targets = build_targets(truth, manifest, args.split, levels)
    if not targets:
        raise SystemExit(f"no targets for split {args.split!r}")
    factory = None
    if args.dry_run:
        if str(HERE) not in sys.path:
            sys.path.insert(0, str(HERE))  # eval/ is not a package
        from dryrun import DryRunClient

        ranges = {}
        for t in targets:
            for b in t.bugs:
                ranges.setdefault(b.spans[0].file, []).append((b.spans[0].line_start, b.spans[0].line_end))
        safe = {f for t in targets if t.kind == "safe" for f in t.files}
        factory = lambda: DryRunClient(ranges, safe)
    out_dir = args.out_dir or (Path(tempfile.mkdtemp(prefix="eval-dry-")) if args.dry_run else HERE)
    rows = run_all(targets, variants, args.repeats, args.dry_run, factory)
    text = write_results(rows, targets, args.repeats, truth, out_dir, args.dry_run)
    print("\n" + text)
    print(f"written to {out_dir}")


if __name__ == "__main__":
    main()
