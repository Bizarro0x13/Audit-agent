import pytest

from agent.gates import citation_errors
from agent.schemas import FindingDraft
from agent.tools.files import PathEscapeError

TEXT = "a\nb\n\n\nlast\n"  # 5 lines, lines 3-4 blank


def read(path):
    if path == "../x":
        raise PathEscapeError(path)
    if path != "F.sol":
        raise FileNotFoundError(path)
    return TEXT


def draft(file="F.sol", start=1, end=2):
    return FindingDraft(title="t", severity="low", file=file, line_start=start, line_end=end,
                        description="d", impact="i")


def test_valid_citation_passes():
    assert citation_errors(draft(), read) == []


@pytest.mark.parametrize("d,needle", [
    (draft(file="Nope.sol"), "does not exist"),
    (draft(file="../x"), "does not exist"),
    (draft(start=1, end=400), "has 5 lines"),
    (draft(start=0, end=2), "invalid line range"),
    (draft(start=4, end=2), "invalid line range"),
    (draft(start=3, end=4), "empty"),
])
def test_bad_citations_fail_with_clear_message(d, needle):
    errs = citation_errors(d, read)
    assert len(errs) == 1 and needle in errs[0]
