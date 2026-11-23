from enum import Enum
from typing import Literal

from pydantic import BaseModel


class Severity(str, Enum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"
    info = "info"


class Status(str, Enum):
    proposed = "proposed"
    verified = "verified"
    rejected = "rejected"
    approved = "approved"


class FocusArea(BaseModel):
    file: str
    bug_class: str


class FindingDraft(BaseModel):
    """What the analyst model returns. The graph adds id/status."""

    title: str
    severity: Severity
    file: str
    line_start: int
    line_end: int
    description: str
    impact: str


class Finding(FindingDraft):
    id: str
    status: Status = Status.proposed
    verifier_note: str = ""


class VerifyResult(BaseModel):
    verdict: Literal["verified", "rejected"]
    note: str
