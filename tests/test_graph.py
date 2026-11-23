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
    result = build_graph(model, tools, store, report_path=out).invoke(
        {"run_id": "r1", "target_root": str(FIXTURE)})
    assert [f.id for f in result["findings"]] == ["F-001"]
    assert [a.file for a in result["plan"]] == ["Vault.sol"]  # bad file dropped
    assert "Reentrancy in withdraw" in out.read_text()
    assert store.count_model_calls("r1") == 2


def bad_citation(end):
    return json.dumps([{
        "title": "Reentrancy", "severity": "high", "file": "Vault.sol", "line_start": 13,
        "line_end": end, "description": "d", "impact": "i"}])


def run(script, tmp_path):
    store = Store(":memory:")
    store.start_run("r1", str(FIXTURE))
    client = FakeClient(script)
    model = Model(store, "r1", client=client, sleep=lambda s: None)
    tools = FileTools(FIXTURE, store, "r1")
    result = build_graph(model, tools, store, report_path=tmp_path / "r.md").invoke(
        {"run_id": "r1", "target_root": str(FIXTURE)})
    return result, store, client


def test_retry_after_bad_citation_passes_with_feedback(tmp_path):
    result, store, client = run([Reply(PLAN), Reply(bad_citation(400)), Reply(FINDINGS)], tmp_path)
    assert [f.id for f in result["findings"]] == ["F-001"]
    assert client.calls == 3
    retry_prompt = client.requests[2]["messages"][0]["content"]
    assert "has 18 lines" in retry_prompt  # the gate error was fed back to the analyst
    rows = store.db.execute("SELECT gate, passed, attempt FROM gate_results ORDER BY id").fetchall()
    assert rows == [("citation", 0, 1), ("citation", 1, 2)]


def test_gives_up_after_three_attempts(tmp_path):
    bad = Reply(bad_citation(400))
    result, _store, client = run([Reply(PLAN), bad, bad, bad], tmp_path)
    assert result["findings"] == []
    assert client.calls == 4  # plan + 3 analyze attempts, no more
    assert "dropped after 3 attempts" in result["gate_errors"][0]


def test_unparseable_reply_counts_as_schema_failure_and_retries(tmp_path):
    result, store, _ = run([Reply(PLAN), Reply(""), Reply(FINDINGS)], tmp_path)
    assert len(result["findings"]) == 1
    rows = store.db.execute("SELECT gate, passed FROM gate_results ORDER BY id").fetchall()
    assert rows[0] == ("schema", 0)
