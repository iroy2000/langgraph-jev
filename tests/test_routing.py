"""Tests for route_by_decision."""

from __future__ import annotations

from langgraph_jev import route_by_decision
from langgraph_jev.models import JevDecision, JevResult


def _result(**decisions: JevDecision) -> JevResult:
    return JevResult(model="jev-1.13.0", decisions=decisions)


def test_normal_route() -> None:
    result = _result(work_type=JevDecision(field="work_type", type="choice", value="bug"))

    route = route_by_decision(
        result,
        field="work_type",
        routes={"bug": "coding_agent", "support": "support_agent"},
        fallback="human_review",
    )

    assert route == "coding_agent"


def test_unknown_decision_value_falls_back() -> None:
    result = _result(work_type=JevDecision(field="work_type", type="choice", value="unmapped"))

    route = route_by_decision(
        result,
        field="work_type",
        routes={"bug": "coding_agent"},
        fallback="human_review",
    )

    assert route == "human_review"


def test_missing_field_falls_back() -> None:
    result = _result(other=JevDecision(field="other", type="choice", value="x"))

    route = route_by_decision(
        result,
        field="work_type",
        routes={"bug": "coding_agent"},
        fallback="human_review",
    )

    assert route == "human_review"


def test_requires_review_forces_fallback_even_with_matching_route() -> None:
    result = _result(work_type=JevDecision(field="work_type", type="choice", value="bug"))
    result.requires_review = True

    route = route_by_decision(
        result,
        field="work_type",
        routes={"bug": "coding_agent"},
        fallback="human_review",
    )

    assert route == "human_review"
