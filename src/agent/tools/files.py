"""Read-only file tools, restricted to the target root.

Rules:
  - every path is resolved against target_root
  - anything that ends up outside target_root is refused with PathEscapeError
  - every call (allowed or refused) writes one row to tool_calls
"""

import json
import re
from pathlib import Path

from agent.store import Store


class PathEscapeError(Exception):
    pass


class FileTools:
    def __init__(self, target_root: str | Path, store: Store, run_id: str, node: str = "analyze"):
        self.root = Path(target_root).resolve()
        self.store = store
        self.run_id = run_id
        self.node = node

    def _safe_path(self, path: str) -> Path:
        """Return the real path inside self.root, or raise PathEscapeError.

        resolve() collapses '..' and follows symlinks, so the check below runs on
        where the path REALLY points. An absolute `path` replaces self.root in the
        join, which is fine: it still has to land inside the root to pass.
        """
        real = (self.root / path).resolve()
        if not real.is_relative_to(self.root):
            raise PathEscapeError(f"{path!r} is outside the target root")
        return real

    def _log(self, tool: str, args: dict, ok: bool) -> None:
        self.store.add_tool_call(self.run_id, self.node, tool, json.dumps(args), ok)

    def read_file(self, path: str) -> str:
        try:
            text = self._safe_path(path).read_text(errors="replace")
        except Exception:
            self._log("read_file", {"path": path}, False)
            raise
        self._log("read_file", {"path": path}, True)
        return text

    def _files(self) -> list[Path]:
        found = []
        for p in self.root.rglob("*"):
            real = p.resolve()
            if real.is_file() and real.is_relative_to(self.root):
                found.append(p)
        return sorted(found)

    def list_files(self) -> list[str]:
        self._log("list_files", {}, True)
        return [str(p.relative_to(self.root)) for p in self._files()]

    def grep(self, pattern: str) -> list[str]:
        try:
            regex = re.compile(pattern)
        except re.error:
            self._log("grep", {"pattern": pattern}, False)
            raise
        hits = []
        for p in self._files():
            rel = str(p.relative_to(self.root))
            for n, line in enumerate(p.read_text(errors="replace").splitlines(), start=1):
                if regex.search(line):
                    hits.append(f"{rel}:{n}: {line}")
        self._log("grep", {"pattern": pattern}, True)
        return hits
