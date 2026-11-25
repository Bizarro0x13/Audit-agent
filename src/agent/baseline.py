"""Single-agent baseline: one analysis call over all files. No plan, gates, verifier, or approval.
Exists so the evaluation can show what the multi-step graph adds (or does not add).

Like the graph's analyze step, it retries an unparseable reply (with the error fed back) so the
comparison is not decided by who handles malformed JSON better. A reply that stays unparseable
after the retries raises, so the failure is visible in the eval instead of silently scoring zero."""

from agent.models import ModelOutputError
from agent.nodes.analyze import SYSTEM, numbered
from agent.schemas import Finding, FindingDraft

ATTEMPTS = 3


def single_agent(model, tools, attempts: int = ATTEMPTS) -> list[Finding]:
    parts = [f"<file path={f!r}>\n{numbered(tools.read_file(f))}\n</file>" for f in tools.list_files()]
    user = "\n\n".join(parts)
    for attempt in range(1, attempts + 1):
        try:
            drafts = model.call("baseline", SYSTEM, user, schema=list[FindingDraft])
            break
        except ModelOutputError as exc:
            if attempt == attempts:
                raise
            user = (
                "\n\n".join(parts)
                + "\n\nYour previous answer was not valid JSON for the schema: "
                + str(exc)[:200]
                + "\nReply with a JSON list only. Use [] if there is nothing to report."
            )
    return [Finding(id=f"F-{i:03d}", **d.model_dump()) for i, d in enumerate(drafts, start=1)]
