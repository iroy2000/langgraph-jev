"""Tests for JevClient: request construction, response parsing, and error mapping."""

from __future__ import annotations

import httpx2
import pytest
from typesafe_sdk import TypeSafeAPIConnectionError, TypeSafeAuthenticationError, TypeSafeError

from langgraph_jev import boolean, choice, score
from langgraph_jev.errors import JevAPIError, JevError, JevTimeoutError, JevValidationError
from tests.conftest import FakeAsyncClient, FakeSyncClient, make_client, make_response


def test_decide_maps_choice_and_boolean_answers() -> None:
    response = make_response(
        {
            "work_type": {
                "type": "choice",
                "choice": "bug",
                "probabilities": {"bug": 0.9, "support": 0.1},
                "confidence": 0.8,
            },
            "needs_engineer": {"type": "noul", "noul": 0.95},
        }
    )
    client = make_client(response)

    result = client.decide(
        state={"title": "Cannot login"},
        questions={
            "work_type": choice(["bug", "support"]),
            "needs_engineer": boolean(),
        },
    )

    assert result.model == "jev-1.13.0"
    assert result.decisions["work_type"].value == "bug"
    assert result.decisions["work_type"].confidence == 0.8
    assert result.decisions["work_type"].probabilities == {"bug": 0.9, "support": 0.1}
    assert result.decisions["needs_engineer"].value == 0.95
    assert result.decisions["needs_engineer"].confidence is None
    assert result.usage == {"input_tokens": 10, "output_tokens": 5}


def test_decide_maps_score_answers_with_string_keyed_probabilities() -> None:
    response = make_response(
        {
            "frustration": {
                "type": "score",
                "score": 1.4,
                "legend": {"0": "calm", "1": "frustrated", "2": "angry"},
                "probabilities": {"0": 0.1, "1": 0.5, "2": 0.4},
                "confidence": 0.6,
            }
        }
    )
    client = make_client(response)

    result = client.decide(
        state="text", questions={"frustration": score(["calm", "frustrated", "angry"])}
    )

    decision = result.decisions["frustration"]
    assert decision.value == 1.4
    assert decision.confidence == 0.6
    assert decision.probabilities == {"0": 0.1, "1": 0.5, "2": 0.4}


def test_decide_passes_sdk_questions_to_underlying_client() -> None:
    response = make_response({"is_bug": {"type": "noul", "noul": 1.0}})
    sync = FakeSyncClient(response)
    from langgraph_jev import JevClient

    client = JevClient(sync_client=sync, async_client=FakeAsyncClient(response))

    client.decide(state="hello", questions={"is_bug": boolean(instructions="Is this a bug?")})

    ((state, questions),) = sync.calls
    assert state == "hello"
    assert questions["is_bug"].instructions == "Is this a bug?"


def test_decide_maps_api_error() -> None:
    headers = httpx2.Headers({})
    api_error = TypeSafeAuthenticationError(401, {"error": "bad key"}, headers)
    client = make_client(error=api_error)

    with pytest.raises(JevAPIError) as excinfo:
        client.decide(state="x", questions={"q": boolean()})

    assert excinfo.value.status == 401


def test_decide_maps_connection_error_to_timeout() -> None:
    client = make_client(error=TypeSafeAPIConnectionError("connect failed"))

    with pytest.raises(JevTimeoutError):
        client.decide(state="x", questions={"q": boolean()})


def test_decide_maps_generic_sdk_error() -> None:
    client = make_client(error=TypeSafeError("boom"))

    with pytest.raises(JevError):
        client.decide(state="x", questions={"q": boolean()})


async def test_adecide_maps_choice_answers() -> None:
    response = make_response(
        {
            "work_type": {
                "type": "choice",
                "choice": "bug",
                "probabilities": {"bug": 1.0},
                "confidence": 1.0,
            }
        }
    )
    client = make_client(response)

    result = await client.adecide(state="x", questions={"work_type": choice(["bug"])})

    assert result.decisions["work_type"].value == "bug"


async def test_adecide_maps_api_error() -> None:
    headers = httpx2.Headers({})
    api_error = TypeSafeAuthenticationError(401, {"error": "bad key"}, headers)
    client = make_client(error=api_error)

    with pytest.raises(JevAPIError):
        await client.adecide(state="x", questions={"q": boolean()})


def test_decide_raises_clear_error_when_response_missing_answer() -> None:
    response = make_response({})
    client = make_client(response)

    with pytest.raises(JevAPIError, match="is_bug"):
        client.decide(state="x", questions={"is_bug": boolean()})


def test_invalid_noul_criteria_raises_jev_validation_error() -> None:
    client = make_client(make_response({}))

    with pytest.raises(JevValidationError):
        client.decide(
            state="x",
            questions={"is_bug": boolean(criteria={"unexpected_key": "nope"})},
        )


def test_context_manager_closes_sync_client() -> None:
    sync = FakeSyncClient(make_response({}))
    from langgraph_jev import JevClient

    client = JevClient(sync_client=sync, async_client=FakeAsyncClient(make_response({})))
    with client:
        pass

    assert sync.closed is True


async def test_async_context_manager_closes_async_client() -> None:
    aio = FakeAsyncClient(make_response({}))
    from langgraph_jev import JevClient

    client = JevClient(sync_client=FakeSyncClient(make_response({})), async_client=aio)
    async with client:
        pass

    assert aio.closed is True


def test_configuration_error_wraps_sdk_error(monkeypatch: pytest.MonkeyPatch) -> None:
    from langgraph_jev import JevClient
    from langgraph_jev import client as client_module
    from langgraph_jev.errors import JevConfigurationError

    def _raise(*args: object, **kwargs: object) -> None:
        raise TypeSafeError("missing api key")

    monkeypatch.setattr(client_module, "TypeSafeClient", _raise)

    with pytest.raises(JevConfigurationError):
        JevClient()
