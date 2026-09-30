"""The Jev decision node for LangGraph."""

from __future__ import annotations

import warnings
from collections.abc import Mapping
from typing import Any, Literal

from .client import JevClient
from .errors import JevValidationError
from .models import JevResult
from .questions import Question

LowConfidencePolicy = Literal["allow", "human_review", "error"]


class JevNode:
    """A typed probabilistic decision node, callable from a LangGraph graph.

    ``JevNode`` receives graph state, evaluates the configured ``questions``
    against it via Jev, and returns a state update -- it never replaces the
    entire graph state.

    Example:
        ```python
        from langgraph_jev import JevNode, choice, boolean

        jev = JevNode(
            questions={
                "work_type": choice(["bug", "support", "documentation"]),
                "priority": choice(["critical", "high", "normal", "low"]),
                "needs_engineer": boolean(),
            },
            thresholds={"work_type": 0.85},
            low_confidence="human_review",
        )

        graph.add_node("jev", jev)
        ```
    """

    def __init__(
        self,
        questions: Mapping[str, Question],
        *,
        client: JevClient | None = None,
        state_key: str | None = None,
        output_key: str = "decision",
        thresholds: Mapping[str, float] | None = None,
        low_confidence: LowConfidencePolicy = "allow",
    ) -> None:
        """Configure a Jev decision node.

        Args:
            questions: Typed questions to evaluate, keyed by decision name.
            client: A preconfigured :class:`~langgraph_jev.client.JevClient`.
                A default client (reading ``TYPESAFE_API_KEY``) is created if
                omitted.
            state_key: The graph state field to pass to Jev as its ``state``.
                If ``None`` (the default), the complete graph state is passed.
            output_key: The graph state field the resulting
                :class:`~langgraph_jev.models.JevResult` is written to.
            thresholds: Optional per-question minimum confidence. Decisions
                below their threshold are still returned in full -- never
                silently discarded -- but flip ``result.requires_review``.
            low_confidence: Policy applied when a threshold is not met:
                ``"allow"`` (default) does nothing extra; ``"human_review"``
                exposes ``result.requires_review`` for conditional routing;
                ``"error"`` raises :class:`~langgraph_jev.errors.JevValidationError`.
        """
        self.questions = dict(questions)
        self.client = client or JevClient()
        self.state_key = state_key
        self.output_key = output_key
        self.thresholds = dict(thresholds or {})
        self.low_confidence: LowConfidencePolicy = low_confidence
        for field in self.thresholds:
            question = self.questions.get(field)
            if question is not None and question.type == "boolean":
                warnings.warn(
                    f"A confidence threshold is configured for {field!r}, but it is a "
                    "boolean() question (Jev Noul), which never reports a confidence "
                    "score. This threshold will have no effect.",
                    UserWarning,
                    stacklevel=2,
                )

    def _extract_state(self, graph_state: Mapping[str, Any]) -> Any:
        if self.state_key is None:
            return graph_state
        return graph_state[self.state_key]

    def _apply_thresholds(self, result: JevResult) -> JevResult:
        requires_review = False
        for field, decision in result.decisions.items():
            threshold = self.thresholds.get(field)
            if threshold is None or decision.confidence is None:
                continue
            decision.meets_threshold = decision.confidence >= threshold
            if not decision.meets_threshold:
                requires_review = True
        result.requires_review = requires_review
        if requires_review and self.low_confidence == "error":
            raise JevValidationError(
                "One or more Jev decisions fell below their configured confidence "
                f"threshold: {result.decisions!r}"
            )
        return result

    def __call__(self, state: Mapping[str, Any]) -> dict[str, JevResult]:
        """Evaluate this node's questions against ``state`` synchronously."""
        result = self.client.decide(self._extract_state(state), self.questions)
        return {self.output_key: self._apply_thresholds(result)}

    async def ainvoke(self, state: Mapping[str, Any]) -> dict[str, JevResult]:
        """Evaluate this node's questions against ``state`` asynchronously."""
        result = await self.client.adecide(self._extract_state(state), self.questions)
        return {self.output_key: self._apply_thresholds(result)}
