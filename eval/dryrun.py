"""Fake model client for `run_eval.py --dry-run`: exercises the whole harness offline.

It is NOT a model. It reads the prompt the real nodes build, and answers in the JSON shapes
they expect: a plan over the listed files, findings that sit on the truth ranges (so the
scoring path sees hits), an occasional finding on a safe control (so the false-positive path
sees one), and a "verified" verdict. Numbers produced with it say nothing about accuracy.
"""

import json
import re
import zlib


class _Block:
    type = "text"

    def __init__(self, text: str):
        self.text = text


class _Usage:
    def __init__(self, i: int, o: int):
        self.input_tokens, self.output_tokens = i, o


class _Reply:
    stop_reason = "end_turn"

    def __init__(self, text: str, i: int, o: int):
        self.content = [_Block(text)]
        self.usage = _Usage(i, o)


class DryRunClient:
    def __init__(self, truth_ranges: dict[str, list[tuple[int, int]]], safe_files: set[str]):
        self.truth_ranges = truth_ranges
        self.safe_files = safe_files
        self.messages = self
        self.calls = 0

    def create(self, model, max_tokens, system, messages):
        self.calls += 1
        user = messages[0]["content"]
        if "You plan a code review" in system:
            files = re.findall(r"^(\S+\.sol) \(\d+ chars\)$", user, re.MULTILINE)
            text = json.dumps([{"file": f, "bug_class": "logic errors"} for f in files[:8]])
        elif "skeptical reviewer" in system:
            text = json.dumps({"verdict": "verified", "note": "dry run"})
        else:
            text = json.dumps(self._findings(user))
        return _Reply(text, max(1, len(system + user) // 4), max(1, len(text) // 4))

    def _findings(self, user: str) -> list[dict]:
        out = []
        for f in re.findall(r"<file path='([^']+)'>", user):
            if f in self.truth_ranges:
                a, b = self.truth_ranges[f][0]
                out.append(self._draft(f, a, b, "dry-run finding on a labeled range"))
            elif f in self.safe_files and zlib.crc32(f.encode()) % 2:
                out.append(self._draft(f, 1, 2, "dry-run finding on a safe control"))
        return out

    @staticmethod
    def _draft(file: str, a: int, b: int, title: str) -> dict:
        return {"title": title, "severity": "medium", "file": file, "line_start": a,
                "line_end": b, "description": "dry run", "impact": "dry run"}
