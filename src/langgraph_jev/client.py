"""Thin client for the Jev API, built on the official ``typesafe-sdk`` package.

This module intentionally does not reimplement HTTP transport, retries, or
authentication -- ``typesafe-sdk`` already provides a maintained, typed client
for the documented TypeSafe API (https://docs.typesafe.ai/api). We wrap it to
translate our typed :mod:`langgraph_jev.questions` and
:mod:`langgraph_jev.models` to and from the SDK's own types, and to map its
exceptions onto this package's error hierarchy.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from typesafe_sdk import (
    AsyncTypeSafeClient,
    SystemOneResponse,
    TypeSafeAPIConnectionError,
    TypeSafeAPIError,
    TypeSafeClient,
    TypeSafeError,
)

from .config import DEFAULT_MODEL
from .errors import JevAPIError, JevConfigurationError, JevError, JevTimeoutError
from .models import JevDecision, JevResult
from .questions import Question


class JevClient:
    """A synchronous/asynchronous client for the Jev decision API.

    Reads the ``TYPESAFE_API_KEY`` environment variable by default; pass
    ``api_key`` to configure it explicitly. Never log or expose the API key.

    Example:
        ```python
        from langgraph_jev import JevClient, choice

        client = JevClient()
        result = client.decide(
            state={"title": "Customer cannot login"},
            questions={"work_type": choice(["bug", "support", "docs"])},
        )
        ```
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        *,
        sync_client: TypeSafeClient | None = None,
        async_client: AsyncTypeSafeClient | None = None,
        **kwargs: Any,
    ) -> None:
        """Create a Jev client.

        Args:
            api_key: Explicit API key. Falls back to ``TYPESAFE_API_KEY``.
            model: Jev model to use. Defaults to ``"jev-latest"``.
            base_url: Override the API root, e.g. to route through a gateway.
            sync_client: Inject a preconfigured ``typesafe_sdk.TypeSafeClient``
                (primarily for tests).
            async_client: Inject a preconfigured
                ``typesafe_sdk.AsyncTypeSafeClient`` (primarily for tests).
            **kwargs: Additional keyword arguments forwarded to the underlying
                ``typesafe_sdk`` clients (e.g. ``retry``, ``timeout``).
        """
        self.model = model or DEFAULT_MODEL
        try:
            self._sync = sync_client or TypeSafeClient(
                api_key=api_key, base_url=base_url, model=self.model, **kwargs
            )
            self._async = async_client or AsyncTypeSafeClient(
                api_key=api_key, base_url=base_url, model=self.model, **kwargs
            )
        except TypeSafeError as exc:
            raise JevConfigurationError(str(exc)) from exc

    def decide(self, state: Any, questions: Mapping[str, Question]) -> JevResult:
        """Evaluate ``questions`` against ``state`` synchronously."""
        try:
            response = self._sync.system_one(
                state, {key: q.to_sdk() for key, q in questions.items()}
            )
        except TypeSafeAPIConnectionError as exc:
            raise JevTimeoutError(str(exc)) from exc
        except TypeSafeAPIError as exc:
            raise JevAPIError(str(exc), status=exc.status, request_id=exc.request_id) from exc
        except TypeSafeError as exc:
            raise JevError(str(exc)) from exc
        return _to_result(response, questions)

    async def adecide(self, state: Any, questions: Mapping[str, Question]) -> JevResult:
        """Evaluate ``questions`` against ``state`` asynchronously."""
        try:
            response = await self._async.system_one(
                state, {key: q.to_sdk() for key, q in questions.items()}
            )
        except TypeSafeAPIConnectionError as exc:
            raise JevTimeoutError(str(exc)) from exc
        except TypeSafeAPIError as exc:
            raise JevAPIError(str(exc), status=exc.status, request_id=exc.request_id) from exc
        except TypeSafeError as exc:
            raise JevError(str(exc)) from exc
        return _to_result(response, questions)

    def close(self) -> None:
        """Release the underlying synchronous HTTP client's resources."""
        self._sync.close()

    async def aclose(self) -> None:
        """Release the underlying asynchronous HTTP client's resources."""
        await self._async.aclose()


def _to_result(response: SystemOneResponse, questions: Mapping[str, Question]) -> JevResult:
    decisions: dict[str, JevDecision] = {}
    for key, question in questions.items():
        if question.type == "boolean":
            noul_answer = response.nouls[key]
            decisions[key] = JevDecision(field=key, type="boolean", value=noul_answer.noul)
        elif question.type == "choice":
            choice_answer = response.choices[key]
            decisions[key] = JevDecision(
                field=key,
                type="choice",
                value=choice_answer.choice,
                confidence=choice_answer.confidence,
                probabilities=dict(choice_answer.probabilities),
            )
        else:
            score_answer = response.scores[key]
            decisions[key] = JevDecision(
                field=key,
                type="score",
                value=score_answer.score,
                confidence=score_answer.confidence,
                probabilities={
                    str(level): value for level, value in score_answer.probabilities.items()
                },
            )
    usage = {
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
    }
    return JevResult(model=response.model, decisions=decisions, usage=usage)
