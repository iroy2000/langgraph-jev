"""Typed result models returned by Jev.

These hide the underlying ``typesafe-sdk`` response types from users, mapping
the raw API response into a stable, SDK-agnostic representation.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel


class JevDecision(BaseModel):
    """A single typed decision returned for one question.

    Attributes:
        field: The question name this decision answers.
        type: The question type: ``"choice"``, ``"boolean"``, or ``"score"``.
        value: The decided value -- the chosen option (choice), ``0``-``1``
            probability of yes (boolean), or numeric score (score).
        confidence: Model confidence in ``[0, 1]``, when reported. Jev reports
            confidence for Choice and Score answers, not Boolean/Noul answers.
        probabilities: The full probability distribution over options or score
            levels, when reported.
        meets_threshold: Whether this decision met its configured confidence
            threshold, or ``None`` if no threshold was configured for it.
    """

    field: str
    type: Literal["choice", "boolean", "score"]
    value: Any
    confidence: float | None = None
    probabilities: dict[str, float] | None = None
    meets_threshold: bool | None = None


class JevResult(BaseModel):
    """The full set of decisions returned by a single Jev call.

    Attributes:
        model: The model that produced the decisions (e.g. ``"jev-1.13.0"``).
        decisions: Decisions keyed by question name.
        requires_review: ``True`` if any decision fell below its configured
            confidence threshold. Used for LangGraph conditional routing; see
            :func:`~langgraph_jev.routing.route_by_decision`.
        usage: Token usage reported by the API, when available.
    """

    model: str
    decisions: dict[str, JevDecision]
    requires_review: bool = False
    usage: dict[str, int | None] | None = None

    def __getitem__(self, key: str) -> JevDecision:
        return self.decisions[key]

    def __contains__(self, key: object) -> bool:
        return key in self.decisions
