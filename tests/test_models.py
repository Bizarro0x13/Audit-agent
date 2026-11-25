import pytest
from pydantic import BaseModel

from agent.models import CostCapExceeded, Model, ModelOutputError, price_for
from agent.store import Store


class Usage:
    def __init__(self, i, o):
        self.input_tokens, self.output_tokens = i, o


class Reply:
    def __init__(self, text, i=1000, o=1000):
        self.content = [type("B", (), {"text": text})()]
        self.usage = Usage(i, o)


class RateLimited(Exception):
    status_code = 429


class FakeClient:
    """Plays back a list of replies/exceptions; no network."""

    def __init__(self, script):
        self.script = list(script)
        self.calls = 0
        self.requests = []
        self.messages = self

    def create(self, **kwargs):
        self.calls += 1
        self.requests.append(kwargs)
        item = self.script.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def make(script, monkeypatch, max_usd="1.00"):
    monkeypatch.setenv("AGENT_MAX_USD", max_usd)
    store = Store(":memory:")
    store.start_run("r1", "t")
    client = FakeClient(script)
    return Model(store, "r1", client=client, sleep=lambda s: None), store, client


def test_row_written_per_call(monkeypatch):
    m, store, _ = make([Reply("hi"), Reply("yo")], monkeypatch)
    m.call("plan", "s", "u")
    m.call("analyze", "s", "u")
    assert store.count_model_calls("r1") == 2
    assert store.run_cost("r1") > 0


def test_retry_on_429(monkeypatch):
    m, store, client = make([RateLimited(), RateLimited(), Reply("ok")], monkeypatch)
    assert m.call("plan", "s", "u") == "ok"
    assert client.calls == 3
    assert store.count_model_calls("r1") == 1


def test_gives_up_after_max_retries(monkeypatch):
    m, _, client = make([RateLimited()] * 4, monkeypatch)
    with pytest.raises(RateLimited):
        m.call("plan", "s", "u")
    assert client.calls == 4


def test_non_retryable_error_not_retried(monkeypatch):
    m, _, client = make([ValueError("bad")], monkeypatch)
    with pytest.raises(ValueError):
        m.call("plan", "s", "u")
    assert client.calls == 1


def test_cost_cap_raises(monkeypatch):
    monkeypatch.setenv("AGENT_PRICE_IN", "3")
    monkeypatch.setenv("AGENT_PRICE_OUT", "15")
    # each call costs (1000*3 + 1000*15)/1e6 = $0.018; cap $0.03 -> second call exceeds
    m, _, _ = make([Reply("a"), Reply("b"), Reply("c")], monkeypatch, max_usd="0.03")
    m.call("plan", "s", "u")
    with pytest.raises(CostCapExceeded):
        m.call("plan", "s", "u")


def test_cap_blocks_next_call_before_sending(monkeypatch):
    m, _, client = make([Reply("a")], monkeypatch, max_usd="0.01")
    with pytest.raises(CostCapExceeded):
        m.call("plan", "s", "u")
    with pytest.raises(CostCapExceeded):
        m.call("plan", "s", "u")
    assert client.calls == 1


class Item(BaseModel):
    name: str


def test_structured_output_parses_fenced_json(monkeypatch):
    m, _, _ = make([Reply('```json\n[{"name": "a"}]\n```')], monkeypatch)
    assert m.call("plan", "s", "u", schema=list[Item]) == [Item(name="a")]


def test_structured_output_invalid_raises(monkeypatch):
    m, _, _ = make([Reply('[{"nope": 1}]')], monkeypatch)
    with pytest.raises(ModelOutputError):
        m.call("plan", "s", "u", schema=list[Item])


def test_ignores_non_text_blocks(monkeypatch):
    reply = Reply("answer")
    thinking = type("T", (), {"type": "thinking"})()
    text = type("B", (), {"type": "text", "text": "answer"})()
    reply.content = [thinking, text]
    m, _, _ = make([reply], monkeypatch)
    assert m.call("plan", "s", "u") == "answer"


def test_structured_output_after_prose(monkeypatch):
    reply = 'The claim is wrong because of the guard.\n\n{"name": "a"}'
    m, _, _ = make([Reply(reply)], monkeypatch)
    assert m.call("verify", "s", "u", schema=Item) == Item(name="a")


def test_price_is_per_model_and_env_overrides(monkeypatch):
    monkeypatch.delenv("AGENT_PRICE_IN", raising=False)
    monkeypatch.delenv("AGENT_PRICE_OUT", raising=False)
    assert price_for("claude-haiku-5-5") == (0.10, 0.50)
    assert price_for("claude-sonnet-5-5") == (2.00, 10.00)
    assert price_for("some-unknown-model") == (2.00, 10.00)  # safe default: the higher rate
    monkeypatch.setenv("AGENT_PRICE_IN", "1")
    monkeypatch.setenv("AGENT_PRICE_OUT", "2")
    assert price_for("claude-haiku-5-5") == (1.0, 2.0)


def test_cost_uses_the_price_of_the_model_called(monkeypatch):
    monkeypatch.delenv("AGENT_PRICE_IN", raising=False)
    monkeypatch.delenv("AGENT_PRICE_OUT", raising=False)
    m, store, _ = make([Reply("a"), Reply("b")], monkeypatch)
    m.call("plan", "s", "u", model="claude-haiku-5-5")   # 1000 in, 1000 out
    cheap = store.run_cost("r1")
    m.call("analyze", "s", "u", model="claude-sonnet-5-5")
    assert cheap == pytest.approx((1000 * 0.10 + 1000 * 0.50) / 1e6)
    assert store.run_cost("r1") - cheap == pytest.approx((1000 * 2.0 + 1000 * 10.0) / 1e6)
