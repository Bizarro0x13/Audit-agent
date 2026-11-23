from pathlib import Path


def make_report_node(out_path: str | Path = "report.md"):
    def report(state):
        lines = [f"# Audit report for {state['target_root']}", ""]
        approved = set(state.get("approved_ids", []))
        findings = [f for f in state.get("findings", []) if f.id in approved]
        if state.get("auto_approved"):
            lines += ["> NOTE: findings were auto-approved (no human review).", ""]
        if not findings:
            lines.append("No approved findings.")
        for f in findings:
            lines += [
                f"## {f.id} [{f.severity.value}] {f.title}",
                f"Location: {f.file}:{f.line_start}-{f.line_end}  (status: {f.status.value})",
                "",
                f.description,
                "",
                f"Impact: {f.impact}",
                f"Verifier: {f.verifier_note or '(not verified)'}",
                "",
            ]
        Path(out_path).write_text("\n".join(lines))
        return {}

    return report
