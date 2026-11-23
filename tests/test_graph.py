import json
from pathlib import Path

from agent.graph import build_graph
from agent.models import Model
from agent.store import Store
from agent.tools.files import FileTools
from tests.test_models import FakeClient, Reply

FIXTURE = Path(__file__).parent / "fixtures" / "vault"

PLAN = json.dumps([{"file": "Vault.sol", "bug_class": "reentrancy"},
                   {"file": "../evil.sol", "bug_class": "x"}])
FINDINGS = json.dumps([{
    "title": "Reentrancy in withdraw", "severity": "high", "file": "Vault.sol",
    "line_start": 13, "line_end": 15, "description": "call before update",
    "impact": "attacker drains the vault"}])


def test_graph_end_to_end_with_fake_model(tmp_path):
    store = Store(":memory:")
    store.start_run("r1", str(FIXTURE))
    model = Model(store, "r1", client=FakeClient([Reply(PLAN), Reply(FINDINGS)]),
                  sleep=lambda s: None)
    tools = FileTools(FIXTURE, store, "r1")
    out = tmp_path / "report.md"
    result = build_graph(model, tools, report_path=out).invoke(
        {"run_id": "r1", "target_root": str(FIXTURE)})
    assert [f.id for f in result["findings"]] == ["F-001"]
    assert [a.file for a in result["plan"]] == ["Vault.sol"]  # bad file dropped
    assert "Reentrancy in withdraw" in out.read_text()
    assert store.count_model_calls("r1") == 2


def test_bad_analyst_reply_is_skipped_not_fatal(tmp_path):
    store = Store(":memory:")
    store.start_run("r1", str(FIXTURE))
    model = Model(store, "r1", client=FakeClient([Reply(PLAN), Reply("")]), sleep=lambda s: None)
    tools = FileTools(FIXTURE, store, "r1")
    result = build_graph(model, tools, report_path=tmp_path / "r.md").invoke(
        {"run_id": "r1", "target_root": str(FIXTURE)})
    assert result["findings"] == []
    assert len(result["gate_errors"]) == 1
