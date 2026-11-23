"""Single-agent baseline: ONE model call over all files. No plan, gates, verifier, or approval.
Exists so the evaluation can show what the multi-step graph adds (or does not add)."""

from agent.nodes.analyze import SYSTEM, numbered
from agent.schemas import Finding, FindingDraft


def single_agent(model, tools) -> list[Finding]:
    parts = [f"<file path={f!r}>\n{numbered(tools.read_file(f))}\n</file>" for f in tools.list_files()]
    drafts = model.call("baseline", SYSTEM, "\n\n".join(parts), schema=list[FindingDraft])
    return [Finding(id=f"F-{i:03d}", **d.model_dump()) for i, d in enumerate(drafts, start=1)]
