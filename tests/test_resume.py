import sqlite3
from pathlib import Path

import pytest
from langgraph.checkpoint.sqlite import SqliteSaver

from agent.graph import build_graph
from agent.models import Model
from agent.store import Store
from agent.tools.files import FileTools
from tests.test_graph import FINDINGS, OK, PLAN
from tests.test_models import FakeClient, Reply

FIXTURE = Path(__file__).parent / "fixtures" / "vault"
CONFIG = {"configurable": {"thread_id": "r1"}}


class Crash(Exception):
    pass


def make(db_path, script, **kw):
    """Build a fresh graph on the on-disk db (as a new process would)."""
    store = Store(db_path)
    if store.get_run("r1") is None:
        store.start_run("r1", str(FIXTURE))
    client = FakeClient(script)
    model = Model(store, "r1", client=client, sleep=lambda s: None)
    saver = SqliteSaver(sqlite3.connect(db_path, check_same_thread=False))
    graph = build_graph(model, FileTools(FIXTURE, store, "r1"), store, lambda f: "y",
                        report_path=Path(db_path).with_name("report.md"), checkpointer=saver, **kw)
    return graph, store, client


def test_crash_then_resume_does_not_repeat_finished_calls(tmp_path):
    db = str(tmp_path / "runs.db")
    start = {"run_id": "r1", "target_root": str(FIXTURE)}

    # process 1: plan and analyze succeed, the verify call crashes
    graph, store, client = make(db, [Reply(PLAN), Reply(FINDINGS), Crash("boom")])
    with pytest.raises(Crash):
        graph.invoke(start, CONFIG)
    assert client.calls == 3 and store.count_model_calls("r1") == 2

    # process 2: brand-new objects, same db file; only verify is left to do
    graph, store, client = make(db, [Reply(OK)])
    result = graph.invoke(None, CONFIG)
    assert client.calls == 1  # plan and analyze were NOT repeated
    assert store.count_model_calls("r1") == 3  # 2 before + 1 after
    assert result["approved_ids"] == ["F-001"]
    assert "Reentrancy in withdraw" in (tmp_path / "report.md").read_text()


def test_stop_after_analyze_then_resume(tmp_path):
    db = str(tmp_path / "runs.db")
    graph, _store, client = make(db, [Reply(PLAN), Reply(FINDINGS)], interrupt_after=["analyze"])
    graph.invoke({"run_id": "r1", "target_root": str(FIXTURE)}, CONFIG)
    assert client.calls == 2 and not (tmp_path / "report.md").exists()
    graph, _store, client = make(db, [Reply(OK)])
    graph.invoke(None, CONFIG)
    assert client.calls == 1 and (tmp_path / "report.md").exists()


def test_cost_carries_across_resume(tmp_path):
    db = str(tmp_path / "runs.db")
    graph, store, _ = make(db, [Reply(PLAN), Reply(FINDINGS), Crash("boom")])
    with pytest.raises(Crash):
        graph.invoke({"run_id": "r1", "target_root": str(FIXTURE)}, CONFIG)
    spent = store.run_cost("r1")
    _, store2, _ = make(db, [])
    assert store2.run_cost("r1") == spent > 0
