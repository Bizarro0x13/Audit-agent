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

# USD per million tokens (input, output). Check current pricing; override with env vars.
DEFAULT_PRICE = (3.0, 15.0)
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
    fenced = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    return (fenced.group(1) if fenced else text).strip()


class Model:
    def __init__(self, store: Store, run_id: str, client=None, sleep=time.sleep):
        self.store = store
        self.run_id = run_id
        self.model = os.environ.get("AGENT_MODEL", "claude-sonnet-5-5")
        self.max_usd = float(os.environ.get("AGENT_MAX_USD", "1.00"))
        self.price_in = float(os.environ.get("AGENT_PRICE_IN", DEFAULT_PRICE[0]))
        self.price_out = float(os.environ.get("AGENT_PRICE_OUT", DEFAULT_PRICE[1]))
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
        cost = (usage.input_tokens * self.price_in + usage.output_tokens * self.price_out) / 1e6
        self.store.add_model_call(
            self.run_id, node, model, usage.input_tokens, usage.output_tokens, cost
        )
        if self.store.run_cost(self.run_id) > self.max_usd:
            raise CostCapExceeded(f"cap ${self.max_usd:.2f} exceeded")
        text = response.content[0].text
        if schema is None:
            return text
        try:
            return TypeAdapter(schema).validate_json(_extract_json(text))
        except ValueError as exc:
            raise ModelOutputError(str(exc)) from exc

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
