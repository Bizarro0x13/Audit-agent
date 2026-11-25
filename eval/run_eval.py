"""Evaluation harness: run each variant on each public target, score against truth.json.

Usage: uv run python eval/run_eval.py [--repeats N] [--variants single,graph_noverify,graph_verify]
Needs ANTHROPIC_API_KEY (from .env). Spends real money: see AGENT_MAX_USD (per run cap).
"""

import argparse
import json
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from agent.approval import approve_all
from agent.baseline import single_agent
from agent.env import load_env
from agent.graph import build_graph
from agent.metrics import Span, score
from agent.models import CostCapExceeded, Model
from agent.rag import Index
from agent.store import Store
from agent.tools.files import FileTools

HERE = Path(__file__).parent
CACHE = HERE / ".cache" / "ethernaut"
VARIANTS = ["single", "graph_noverify", "graph_noverify_rag", "graph_verify", "graph_verify_rag"]


def fetch(truth: dict) -> Path:
    """Clone the pinned commit once into the gitignored cache."""
    if not (CACHE / ".git").exists():
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "clone", "-q", truth["repo"], str(CACHE)], check=True)
    subprocess.run(["git", "-C", str(CACHE), "checkout", "-q", truth["commit"]], check=True)
    return CACHE / truth["dir"]


def stage(src: Path, files: list[str]) -> Path:
    d = Path(tempfile.mkdtemp(prefix="eval-target-"))
    for f in files:
        shutil.copy(src / f, d / f)
    return d


def run_variant(variant: str, target_dir: Path) -> dict:
    store = Store(":memory:")
    store.start_run("e", str(target_dir))
    model = Model(store, "e")
    tools = FileTools(target_dir, store, "e")
    started = time.time()
    status = "ok"
    findings = []
    try:
        if variant == "single":
            findings = single_agent(model, tools)
        else:
            graph = build_graph(model, tools, store, approve_all,
                                report_path=target_dir / "report.md",
                                verify=variant.startswith("graph_verify"),
                                rag=Index.build(HERE.parent / "knowledge")
                                if variant.endswith("_rag") else None)
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


def main() -> None:
    load_env()
    ap = argparse.ArgumentParser()
    ap.add_argument("--repeats", type=int, default=1)
    ap.add_argument("--variants", default=",".join(VARIANTS))
    args = ap.parse_args()
    variants = args.variants.split(",")

    truth = json.loads((HERE / "truth.json").read_text())
    src = fetch(truth)
    rows = []  # (variant, target, run_index, metrics dict)
    for name, t in truth["targets"].items():
        target_dir = stage(src, t["files"])
        truth_spans = [Span(x["file"], x["line_start"], x["line_end"]) for x in t["truth"]]
        for variant in variants:
            for i in range(args.repeats):
                r = run_variant(variant, target_dir)
                m = score(r["spans"], truth_spans) | {k: r[k] for k in
                    ("status", "cost", "seconds", "in_tokens", "out_tokens", "gate_failures")}
                rows.append((variant, name, i, m))
                print(f"{variant:15} {name:12} run{i}: recall {m['recall']:.2f} "
                      f"found {m['found']} hit {m['found_hit']} cost ${m['cost']:.3f} "
                      f"{m['seconds']:.0f}s {m['status']}", flush=True)
    write_results(rows, truth, args.repeats)


def write_results(rows, truth, repeats) -> None:
    (HERE / "results.json").write_text(json.dumps(
        [{"variant": v, "target": n, "run": i, **m} for v, n, i, m in rows], indent=2))
    n_bugs = sum(len(t["truth"]) for t in truth["targets"].values())
    intro = (
        f"Targets: Ethernaut @ `{truth['commit'][:10]}` ({len(truth['targets'])} sets, "
        f"{n_bugs} labeled bugs). {repeats} run(s) per variant per target; numbers are totals "
        "over all targets (averaged over runs)."
    )
    caveats = (
        "Caveats: ground truth is a short list of the known, deliberate bugs. A finding that "
        "hits none of them may still be a real issue, so precision is a lower bound. "
        "Cost uses the published per-model prices in models.py (as of 2026-11-03); token counts are exact. "
        "Small sample: treat differences as indicative, not proven."
    )
    header = (
        "| variant | recall | precision | findings | tokens in/out | est. cost | seconds "
        "| duplicate hits | gate failures | failed runs |"
    )
    out = ["# Evaluation results", "", intro, "", caveats, "", header,
           "|---|---|---|---|---|---|---|---|---|---|"]
    for variant in dict.fromkeys(v for v, *_ in rows):
        ms = [m for v, _, _, m in rows if v == variant]
        n = max(1, repeats)
        th = sum(m["truth_hit"] for m in ms) / n
        tt = sum(m["truth"] for m in ms) / n
        fh = sum(m["found_hit"] for m in ms) / n
        ff = sum(m["found"] for m in ms) / n
        out.append(
            f"| {variant} | {th / tt:.0%} ({th:.1f}/{tt:.0f}) | "
            f"{(fh / ff if ff else 0):.0%} ({fh:.1f}/{ff:.1f}) | {ff:.1f} | "
            f"{sum(m['in_tokens'] for m in ms) / n:.0f}/{sum(m['out_tokens'] for m in ms) / n:.0f} | "
            f"${sum(m['cost'] for m in ms) / n:.3f} | {sum(m['seconds'] for m in ms) / n:.0f} | "
            f"{(fh - th):.1f} | {sum(m['gate_failures'] for m in ms) / n:.1f} | "
            f"{sum(m['status'] != 'ok' for m in ms)} |")
    (HERE / "results.md").write_text("\n".join(out) + "\n")
    print("\n" + "\n".join(out))


if __name__ == "__main__":
    main()
