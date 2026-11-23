"""SQLite trace store: one file per workspace (.agent/runs.db)."""

import sqlite3
import time
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs(
    id TEXT PRIMARY KEY, target TEXT, started_at REAL, status TEXT, cost_usd REAL DEFAULT 0);
CREATE TABLE IF NOT EXISTS model_calls(
    id INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT, node TEXT, model TEXT,
    input_tokens INTEGER, output_tokens INTEGER, cost_usd REAL, started_at REAL);
CREATE TABLE IF NOT EXISTS tool_calls(
    id INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT, node TEXT, tool TEXT,
    args_json TEXT, ok INTEGER, started_at REAL);
CREATE TABLE IF NOT EXISTS findings(run_id TEXT, id TEXT, json TEXT);
CREATE TABLE IF NOT EXISTS gate_results(
    id INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT, gate TEXT,
    passed INTEGER, detail TEXT, attempt INTEGER);
"""


class Store:
    def __init__(self, path: str | Path):
        if str(path) != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(str(path))
        self.db.executescript(SCHEMA)

    def start_run(self, run_id: str, target: str) -> None:
        self.db.execute(
            "INSERT INTO runs(id, target, started_at, status) VALUES (?,?,?,?)",
            (run_id, target, time.time(), "running"),
        )
        self.db.commit()

    def add_model_call(self, run_id, node, model, input_tokens, output_tokens, cost_usd) -> None:
        self.db.execute(
            "INSERT INTO model_calls(run_id, node, model, input_tokens, output_tokens,"
            " cost_usd, started_at) VALUES (?,?,?,?,?,?,?)",
            (run_id, node, model, input_tokens, output_tokens, cost_usd, time.time()),
        )
        self.db.execute(
            "UPDATE runs SET cost_usd = cost_usd + ? WHERE id = ?", (cost_usd, run_id)
        )
        self.db.commit()

    def run_cost(self, run_id: str) -> float:
        row = self.db.execute("SELECT cost_usd FROM runs WHERE id = ?", (run_id,)).fetchone()
        return row[0] if row else 0.0

    def count_model_calls(self, run_id: str) -> int:
        row = self.db.execute(
            "SELECT COUNT(*) FROM model_calls WHERE run_id = ?", (run_id,)
        ).fetchone()
        return row[0]

    def add_tool_call(self, run_id, node, tool, args_json, ok) -> None:
        self.db.execute(
            "INSERT INTO tool_calls(run_id, node, tool, args_json, ok, started_at)"
            " VALUES (?,?,?,?,?,?)",
            (run_id, node, tool, args_json, int(ok), time.time()),
        )
        self.db.commit()
