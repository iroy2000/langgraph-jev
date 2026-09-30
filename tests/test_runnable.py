"""Tests for JevRunnable: invoke and ainvoke."""

from __future__ import annotations

from langgraph_jev import JevRunnable, choice
from tests.conftest import make_client, make_response


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
