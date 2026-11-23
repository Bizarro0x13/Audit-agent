from agent.baseline import single_agent
from agent.models import Model
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
