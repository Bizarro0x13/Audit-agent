"""The one place every model call goes through.

Handles: key/model from env, timeout, retry with backoff, structured JSON output,
token + cost counting, a trace row per call, and the per-run cost cap.
"""

import json
import os
import re
import time

from pydantic import TypeAdapter

from agent.store import Store

# USD per million tokens (input, output), from the published price list as of 2026-11-03.
# Haiku 5.5 is priced higher ($0.50 / $2.50) for prompts over 100K tokens; our prompts are
# one file, far below that. Re-check before publishing cost numbers.
PRICES = {
    "claude-haiku-5-5": (0.10, 0.50),
    "claude-sonnet-5-5": (2.00, 10.00),
}
# Unknown model id: assume the Sonnet rate so the cost cap errs on the safe side.
DEFAULT_PRICE = PRICES["claude-sonnet-5-5"]


def price_for(model: str) -> tuple[float, float]:
    """Per-model price. AGENT_PRICE_IN / AGENT_PRICE_OUT override it for every model."""
    default_in, default_out = PRICES.get(model, DEFAULT_PRICE)
    return (
        float(os.environ.get("AGENT_PRICE_IN", default_in)),
        float(os.environ.get("AGENT_PRICE_OUT", default_out)),
    )
RETRY_STATUSES = {429, 500, 502, 503, 529}


class CostCapExceeded(Exception):
    pass


class ModelOutputError(Exception):
    """The model's reply was not valid JSON for the requested schema."""


def _is_retryable(exc: Exception) -> bool:
    return getattr(exc, "status_code", None) in RETRY_STATUSES or isinstance(
        exc, (ConnectionError, TimeoutError)
    )


def _extract_json(text: str) -> str:
    """Pull the JSON out of a reply: a fenced block, or JSON that ends the reply after prose."""
    fenced = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if fenced:
        return fenced.group(1).strip()
    text = text.strip()
    decoder = json.JSONDecoder()
    for i, ch in enumerate(text):
        if ch in "[{":
            try:
                _, end = decoder.raw_decode(text[i:])
            except ValueError:
                continue
            if not text[i + end :].strip():  # valid JSON that runs to the end of the reply
                return text[i:]
    return text


class Model:
    def __init__(self, store: Store, run_id: str, client=None, sleep=time.sleep):
        self.store = store
        self.run_id = run_id
        self.model = os.environ.get("AGENT_MODEL", "claude-sonnet-5-5")
        self.max_usd = float(os.environ.get("AGENT_MAX_USD", "1.00"))
        self.max_retries = 3
        self.sleep = sleep
        if client is None:
            import anthropic  # key is read from ANTHROPIC_API_KEY

            client = anthropic.Anthropic(timeout=60.0, max_retries=0)
        self.client = client

    def call(self, node: str, system: str, user: str, schema=None, model: str | None = None):
        model = model or self.model
        if self.store.run_cost(self.run_id) >= self.max_usd:
            raise CostCapExceeded(f"cap ${self.max_usd:.2f} already reached")
        if schema is not None:
            system += (
                "\n\nReply with JSON only, matching this JSON schema:\n"
                + json.dumps(TypeAdapter(schema).json_schema())
            )
        response = self._send_with_retry(system, user, model)
        usage = response.usage
        price_in, price_out = price_for(model)
        cost = (usage.input_tokens * price_in + usage.output_tokens * price_out) / 1e6
        self.store.add_model_call(
            self.run_id, node, model, usage.input_tokens, usage.output_tokens, cost
        )
        if self.store.run_cost(self.run_id) > self.max_usd:
            raise CostCapExceeded(f"cap ${self.max_usd:.2f} exceeded")
        text = "".join(b.text for b in response.content if getattr(b, "type", "text") == "text")
        if schema is None:
            return text
        try:
            return TypeAdapter(schema).validate_json(_extract_json(text))
        except ValueError as exc:
            raise ModelOutputError(f"{exc}\n--- stop_reason={getattr(response, 'stop_reason', None)}, blocks={[getattr(b, 'type', '?') for b in response.content]}, raw reply (first 300 chars) ---\n{text[:300]}") from exc

    def _send_with_retry(self, system: str, user: str, model: str):
        for attempt in range(self.max_retries + 1):
            try:
                return self.client.messages.create(
                    model=model,
                    max_tokens=4096,
                    system=system,
                    messages=[{"role": "user", "content": user}],
                )
            except Exception as exc:
                if attempt == self.max_retries or not _is_retryable(exc):
                    raise
                self.sleep(2**attempt)  # 1s, 2s, 4s
