from pathlib import Path


def make_report_node(out_path: str | Path = "report.md"):
    def report(state):
        lines = [f"# Audit report for {state['target_root']}", ""]
        findings = state.get("findings", [])
        if not findings:
            lines.append("No findings.")
        for f in findings:
            lines += [
                f"## {f.id} [{f.severity.value}] {f.title}",
                f"Location: {f.file}:{f.line_start}-{f.line_end}  (status: {f.status.value})",
                "",
                f.description,
                "",
                f"Impact: {f.impact}",
                "",
            ]
        Path(out_path).write_text("\n".join(lines))
        return {}

    return report
