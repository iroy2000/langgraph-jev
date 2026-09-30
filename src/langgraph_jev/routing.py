"""Deterministic routing based on a Jev decision.

Jev makes the probabilistic decision; your application decides what to do
with it. This helper keeps that boundary explicit and routing logic
deterministic.
"""

from __future__ import annotations

from collections.abc import Mapping

from .models import JevResult


def route_by_decision(
    result: JevResult,
    *,
    field: str,
    routes: Mapping[str, str],
    fallback: str,
) -> str:
    """Map a decision's value to a LangGraph route name.

    If ``result.requires_review`` is set (see
    :class:`~langgraph_jev.node.JevNode`'s ``low_confidence="human_review"``),
    or the decision's value has no matching entry in ``routes``, ``fallback``
    is returned.

    Example:
        ```python
        def route_work(state):
            return route_by_decision(
                state["decision"],
                field="work_type",
                routes={
                    "bug": "coding_agent",
                    "support": "support_agent",
                    "documentation": "documentation_agent",
                },
                fallback="human_review",
            )
        ```
    """
    if result.requires_review:
        return fallback
    decision = result.decisions.get(field)
    if decision is None:
        return fallback
    return routes.get(decision.value, fallback)
