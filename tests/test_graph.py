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
OK = json.dumps({"verdict": "verified", "note": "no guard before the call"})
FINDINGS = json.dumps([{
    "title": "Reentrancy in withdraw", "severity": "high", "file": "Vault.sol",
    "line_start": 13, "line_end": 15, "description": "call before update",
    "impact": "attacker drains the vault"}])


def test_graph_end_to_end_with_fake_model(tmp_path):
    store = Store(":memory:")
    store.start_run("r1", str(FIXTURE))
    model = Model(store, "r1", client=FakeClient([Reply(PLAN), Reply(FINDINGS), Reply(OK)]),
                  sleep=lambda s: None)
    tools = FileTools(FIXTURE, store, "r1")
    out = tmp_path / "report.md"
    result = build_graph(model, tools, store, lambda f: "y", report_path=out).invoke(
        {"run_id": "r1", "target_root": str(FIXTURE)})
    assert [f.id for f in result["findings"]] == ["F-001"]
    assert [a.file for a in result["plan"]] == ["Vault.sol"]  # bad file dropped
    assert "Reentrancy in withdraw" in out.read_text()
    assert store.count_model_calls("r1") == 3


def bad_citation(end):
    return json.dumps([{
        "title": "Reentrancy", "severity": "high", "file": "Vault.sol", "line_start": 13,
        "line_end": end, "description": "d", "impact": "i"}])


def run(script, tmp_path, ask=lambda f: "y"):
    store = Store(":memory:")
    store.start_run("r1", str(FIXTURE))
    client = FakeClient(script)
    model = Model(store, "r1", client=client, sleep=lambda s: None)
    tools = FileTools(FIXTURE, store, "r1")
    result = build_graph(model, tools, store, ask, report_path=tmp_path / "r.md").invoke(
        {"run_id": "r1", "target_root": str(FIXTURE)})
    return result, store, client


def test_retry_after_bad_citation_passes_with_feedback(tmp_path):
    result, store, client = run([Reply(PLAN), Reply(bad_citation(400)), Reply(FINDINGS), Reply(OK)], tmp_path)
    assert [f.id for f in result["findings"]] == ["F-001"]
    assert client.calls == 4
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
    result, store, _ = run([Reply(PLAN), Reply(""), Reply(FINDINGS), Reply(OK)], tmp_path)
    assert len(result["findings"]) == 1
    rows = store.db.execute("SELECT gate, passed FROM gate_results ORDER BY id").fetchall()
    assert rows[0] == ("schema", 0)


def test_verifier_prompt_is_isolated_from_analyst(tmp_path):
    from agent.nodes.analyze import SYSTEM as ANALYST_SYSTEM

    _, _, client = run([Reply(PLAN), Reply(FINDINGS), Reply(OK)], tmp_path)
    v = client.requests[2]
    assert "REFUTE" in v["system"]
    assert ANALYST_SYSTEM not in v["system"]  # analyst instructions never reach the verifier
    user = v["messages"][0]["content"]
    assert "attacker drains the vault" in user  # the claim itself
    assert "Focus: check" not in user  # not the analyst's task prompt
    assert len(v["messages"]) == 1  # no conversation history carried over


def test_rejected_finding_kept_in_db_but_not_in_report(tmp_path):
    rejected = json.dumps({"verdict": "rejected", "note": "guard exists"})
    result, store, _ = run([Reply(PLAN), Reply(FINDINGS), Reply(rejected)], tmp_path)
    assert result["findings"][0].status.value == "rejected"
    assert "Reentrancy in withdraw" not in (tmp_path / "r.md").read_text()
    row = store.db.execute("SELECT json FROM findings").fetchone()
    assert '"rejected"' in row[0]


def test_unusable_verifier_reply_leaves_finding_unverified(tmp_path):
    result, _, client = run(
        [Reply(PLAN), Reply(FINDINGS), Reply("x"), Reply("y")], tmp_path, ask=lambda f: "s"
    )
    f = result["findings"][0]
    assert f.status.value == "proposed" and "unusable" in f.verifier_note
    assert client.calls == 4  # plan, analyze, verify + exactly one verify retry


def test_verifier_retries_once_after_unusable_reply(tmp_path):
    result, _, _ = run(
        [Reply(PLAN), Reply(FINDINGS), Reply("oops"), Reply(OK)], tmp_path, ask=lambda f: "s"
    )
    assert result["findings"][0].status.value == "verified"


def test_only_approved_findings_reach_the_report(tmp_path):
    result, store, _ = run([Reply(PLAN), Reply(FINDINGS), Reply(OK)], tmp_path, ask=lambda f: "n")
    assert result["approved_ids"] == []
    assert "Reentrancy in withdraw" not in (tmp_path / "r.md").read_text()
    assert "No approved findings" in (tmp_path / "r.md").read_text()
    assert '"rejected"' in store.db.execute("SELECT json FROM findings").fetchone()[0]


def test_skip_leaves_finding_out_of_report_but_unchanged(tmp_path):
    result, _, _ = run([Reply(PLAN), Reply(FINDINGS), Reply(OK)], tmp_path, ask=lambda f: "s")
    assert result["approved_ids"] == []
    assert result["findings"][0].status.value == "verified"


def test_yes_approves_and_is_reported_with_status(tmp_path):
    result, _, _ = run([Reply(PLAN), Reply(FINDINGS), Reply(OK)], tmp_path)
    assert result["approved_ids"] == ["F-001"]
    assert "status: approved" in (tmp_path / "r.md").read_text()


def test_verifier_rejected_findings_are_never_shown_to_the_human(tmp_path):
    shown = []
    rejected = json.dumps({"verdict": "rejected", "note": "guard exists"})
    run([Reply(PLAN), Reply(FINDINGS), Reply(rejected)], tmp_path, ask=lambda f: shown.append(f) or "y")
    assert shown == []


def test_graph_without_verifier_skips_the_verify_call(tmp_path):
    store = Store(":memory:")
    store.start_run("r1", str(FIXTURE))
    client = FakeClient([Reply(PLAN), Reply(FINDINGS)])
    model = Model(store, "r1", client=client, sleep=lambda s: None)
    result = build_graph(model, FileTools(FIXTURE, store, "r1"), store, lambda f: "y",
                         report_path=tmp_path / "r.md", verify=False).invoke(
        {"run_id": "r1", "target_root": str(FIXTURE)})
    assert client.calls == 2 and result["approved_ids"] == ["F-001"]
