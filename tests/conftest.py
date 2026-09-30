"""Shared test fixtures: a fake Jev transport so tests never need a real API key."""

from __future__ import annotations

import json
from typing import Any

import pytest
from typesafe_sdk import SystemOneResponse

from langgraph_jev import JevClient


def make_response(
    answers: dict[str, dict[str, Any]], *, model: str = "jev-1.13.0"
) -> SystemOneResponse:
    """Build a real ``SystemOneResponse`` from raw answer dicts, without any HTTP call.

    Uses ``model_validate_json`` (matching the SDK's own JSON decode path) so that
    JSON-object-style integer keys (score legends/probabilities) coerce correctly,
    the same way they do when decoding a real HTTP response body.
    """
    payload = {
        "model": model,
        "answers": answers,
        "usage": {"input_tokens": 10, "output_tokens": 5},
    }
    return SystemOneResponse.model_validate_json(json.dumps(payload))


class FakeSyncClient:
    """A fake ``typesafe_sdk.TypeSafeClient`` returning a canned response."""

    def __init__(
        self, response: SystemOneResponse | None = None, *, error: Exception | None = None
    ) -> None:
        self.response = response
        self.error = error
        self.calls: list[tuple[Any, Any]] = []
        self.closed = False

    def system_one(self, state: Any, questions: Any, **kwargs: Any) -> SystemOneResponse:
        self.calls.append((state, questions))
        if self.error is not None:
            raise self.error
        assert self.response is not None
        return self.response

    def close(self) -> None:
        self.closed = True


class FakeAsyncClient:
    """A fake ``typesafe_sdk.AsyncTypeSafeClient`` returning a canned response."""

    def __init__(
        self, response: SystemOneResponse | None = None, *, error: Exception | None = None
    ) -> None:
        self.response = response
        self.error = error
        self.calls: list[tuple[Any, Any]] = []
        self.closed = False

    async def system_one(self, state: Any, questions: Any, **kwargs: Any) -> SystemOneResponse:
        self.calls.append((state, questions))
        if self.error is not None:
            raise self.error
        assert self.response is not None
        return self.response

    async def aclose(self) -> None:
        self.closed = True


def make_client(
    response: SystemOneResponse | None = None, *, error: Exception | None = None
) -> JevClient:
    """Build a JevClient backed entirely by fakes -- no network, no API key required."""
    sync = FakeSyncClient(response, error=error)
    aio = FakeAsyncClient(response, error=error)
    return JevClient(sync_client=sync, async_client=aio)


@pytest.fixture
def work_ticket_answers() -> dict[str, dict[str, Any]]:
    return {
        "work_type": {
            "type": "choice",
            "choice": "bug",
            "probabilities": {"bug": 0.9, "support": 0.1},
            "confidence": 0.8,
        },
        "priority": {
            "type": "choice",
            "choice": "high",
            "probabilities": {"critical": 0.1, "high": 0.6, "normal": 0.2, "low": 0.1},
            "confidence": 0.4,
        },
        "needs_engineer": {
            "type": "noul",
            "noul": 0.95,
        },
    }
