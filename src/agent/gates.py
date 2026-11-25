"""Gates: pure code, no model calls. A gate returns a list of error strings ([] = pass).

Gate 1 (schema) is enforced where the reply is parsed (models.py raises ModelOutputError);
the analyze node turns that into an error string for the same retry loop.
Gate 2 (citation) is here: a finding must point at real lines of a real file.
"""

from collections.abc import Callable

from agent.schemas import FindingDraft
from agent.tools.files import PathEscapeError

MAX_ATTEMPTS = 3


def citation_errors(finding: FindingDraft, read_file: Callable[[str], str]) -> list[str]:
    where = f"finding {finding.title!r}"
    try:
        lines = read_file(finding.file).splitlines()
    except (PathEscapeError, OSError):
        return [f"{where} cites file {finding.file!r}, which does not exist in the target"]
    start, end, count = finding.line_start, finding.line_end, len(lines)
    if start < 1 or start > end:
        return [f"{where} has an invalid line range {start}-{end}"]
    if end > count:
        return [f"{where} cites lines {start}-{end} but {finding.file} has {count} lines"]
    if not any(line.strip() for line in lines[start - 1 : end]):
        return [f"{where} cites lines {start}-{end} of {finding.file}, which are empty"]
    return []


def same_issue(a: FindingDraft, b: FindingDraft) -> bool:
    """Duplicate test: same file and the line ranges overlap by at least half of the shorter one.

    Exact-range matching missed near-duplicates (lines 19-26 vs 20-26). Requiring half-overlap
    keeps two different bugs that merely touch the same line from being merged.
    """
    if a.file != b.file:
        return False
    overlap = min(a.line_end, b.line_end) - max(a.line_start, b.line_start) + 1
    shorter = min(a.line_end - a.line_start, b.line_end - b.line_start) + 1
    return overlap > 0 and overlap * 2 >= shorter
