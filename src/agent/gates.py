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
