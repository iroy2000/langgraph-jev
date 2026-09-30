"""Tests for JevRunnable: invoke and ainvoke."""

from __future__ import annotations

from typing import Any

from langchain_core.callbacks.base import BaseCallbackHandler

from langgraph_jev import JevRunnable, choice
from tests.conftest import make_client, make_response


class _RecordingHandler(BaseCallbackHandler):
    """Records chain start/end callbacks, to verify Runnable tracing hooks fire."""

    def __init__(self) -> None:
        self.started: list[Any] = []
        self.ended: list[Any] = []

    def on_chain_start(self, serialized: Any, inputs: Any, **kwargs: Any) -> None:
        self.started.append(inputs)

    def on_chain_end(self, outputs: Any, **kwargs: Any) -> None:
        self.ended.append(outputs)


def test_invoke_returns_jev_result() -> None:
    response = make_response(
        {
            "route": {
                "type": "choice",
                "choice": "coding",
                "probabilities": {"coding": 1.0},
                "confidence": 1.0,
            }
        }
    )
    client = make_client(response)
    runnable = JevRunnable(
        questions={"route": choice(["coding", "support", "research"])}, client=client
    )

    result = runnable.invoke({"title": "Customer cannot login"})

    assert result.decisions["route"].value == "coding"


def test_invoke_fires_langchain_callbacks() -> None:
    """JevRunnable must go through _call_with_config so tracing/callbacks work."""
    response = make_response(
        {
            "route": {
                "type": "choice",
                "choice": "coding",
                "probabilities": {"coding": 1.0},
                "confidence": 1.0,
            }
        }
    )
    client = make_client(response)
    runnable = JevRunnable(
        questions={"route": choice(["coding", "support", "research"])}, client=client
    )
    handler = _RecordingHandler()

    runnable.invoke({"title": "Customer cannot login"}, config={"callbacks": [handler]})

    assert len(handler.started) == 1
    assert len(handler.ended) == 1


async def test_ainvoke_returns_jev_result() -> None:
    response = make_response(
        {
            "route": {
                "type": "choice",
                "choice": "support",
                "probabilities": {"support": 1.0},
                "confidence": 1.0,
            }
        }
    )
    client = make_client(response)
    runnable = JevRunnable(
        questions={"route": choice(["coding", "support", "research"])}, client=client
    )

    result = await runnable.ainvoke({"title": "Billing question"})

    assert result.decisions["route"].value == "support"
