import pytest

from agent.baseline import single_agent
from agent.models import Model, ModelOutputError
from agent.store import Store
from agent.tools.files import FileTools
from tests.test_graph import FINDINGS, FIXTURE
from tests.test_models import FakeClient, Reply


def test_single_agent_is_one_model_call():
    store = Store(":memory:")
    store.start_run("r", "t")
    client = FakeClient([Reply(FINDINGS)])
    found = single_agent(Model(store, "r", client=client), FileTools(FIXTURE, store, "r"))
    assert client.calls == 1 and [f.id for f in found] == ["F-001"]


def test_single_agent_retries_an_unparseable_reply_with_feedback():
    store = Store(":memory:")
    store.start_run("r", "t")
    client = FakeClient([Reply("There is nothing to report."), Reply(FINDINGS)])
    found = single_agent(Model(store, "r", client=client), FileTools(FIXTURE, store, "r"))
    assert client.calls == 2 and [f.id for f in found] == ["F-001"]
    assert "not valid JSON" in client.requests[1]["messages"][0]["content"]


def test_single_agent_gives_up_loudly_after_the_attempts():
    store = Store(":memory:")
    store.start_run("r", "t")
    client = FakeClient([Reply("nope"), Reply("still nope"), Reply("no")])
    with pytest.raises(ModelOutputError):
        single_agent(Model(store, "r", client=client), FileTools(FIXTURE, store, "r"))
    assert client.calls == 3
