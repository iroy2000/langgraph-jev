"""Tests for JevNode: state input/output mapping, thresholds, async execution."""

from __future__ import annotations

import pytest

from langgraph_jev import JevNode, boolean, choice
from langgraph_jev.errors import JevValidationError
from tests.conftest import make_client, make_response


def _client_for(answers: dict) -> object:
    return make_client(make_response(answers))


def test_complete_state_passed_by_default() -> None:
    client = _client_for({"is_bug": {"type": "noul", "noul": 1.0}})
    node = JevNode(questions={"is_bug": boolean()}, client=client)

    update = node({"title": "x", "description": "y"})

    ((state, _),) = client._sync.calls
    assert state == {"title": "x", "description": "y"}
    assert "decision" in update


def test_state_key_scopes_input() -> None:
    client = _client_for({"is_bug": {"type": "noul", "noul": 1.0}})
    node = JevNode(questions={"is_bug": boolean()}, client=client, state_key="structured_request")

    node({"structured_request": {"title": "x"}, "other": "ignored"})

    ((state, _),) = client._sync.calls
    assert state == {"title": "x"}


def test_output_key_is_configurable() -> None:
    client = _client_for({"is_bug": {"type": "noul", "noul": 1.0}})
    node = JevNode(questions={"is_bug": boolean()}, client=client, output_key="jev_decision")

    update = node({})

    assert set(update.keys()) == {"jev_decision"}
    assert update["jev_decision"].decisions["is_bug"].value == 1.0


def test_returns_state_update_not_full_state_replacement() -> None:
    client = _client_for({"is_bug": {"type": "noul", "noul": 1.0}})
    node = JevNode(questions={"is_bug": boolean()}, client=client)

    update = node({"title": "unchanged"})

    assert update == {"decision": update["decision"]}
    assert "title" not in update


async def test_ainvoke_executes_asynchronously() -> None:
    client = _client_for({"is_bug": {"type": "noul", "noul": 1.0}})
    node = JevNode(questions={"is_bug": boolean()}, client=client)

    update = await node.ainvoke({})

    assert update["decision"].decisions["is_bug"].value == 1.0
    assert len(client._async.calls) == 1


def test_threshold_allow_does_not_raise() -> None:
    client = _client_for(
        {
            "work_type": {
                "type": "choice",
                "choice": "bug",
                "probabilities": {"bug": 0.5, "support": 0.5},
                "confidence": 0.1,
            }
        }
    )
    node = JevNode(
        questions={"work_type": choice(["bug", "support"])},
        client=client,
        thresholds={"work_type": 0.9},
        low_confidence="allow",
    )

    update = node({})

    assert update["decision"].requires_review is True
    assert update["decision"].decisions["work_type"].meets_threshold is False
    assert update["decision"].decisions["work_type"].value == "bug"  # never discarded


def test_threshold_human_review_exposes_requires_review() -> None:
    client = _client_for(
        {
            "work_type": {
                "type": "choice",
                "choice": "bug",
                "probabilities": {"bug": 0.5, "support": 0.5},
                "confidence": 0.1,
            }
        }
    )
    node = JevNode(
        questions={"work_type": choice(["bug", "support"])},
        client=client,
        thresholds={"work_type": 0.9},
        low_confidence="human_review",
    )

    update = node({})

    def route_after_jev(state: dict) -> str:
        if state["decision"].requires_review:
            return "human_review"
        return "continue"

    assert route_after_jev(update) == "human_review"


def test_threshold_error_raises() -> None:
    client = _client_for(
        {
            "work_type": {
                "type": "choice",
                "choice": "bug",
                "probabilities": {"bug": 0.5, "support": 0.5},
                "confidence": 0.1,
            }
        }
    )
    node = JevNode(
        questions={"work_type": choice(["bug", "support"])},
        client=client,
        thresholds={"work_type": 0.9},
        low_confidence="error",
    )

    with pytest.raises(JevValidationError):
        node({})


def test_decision_meeting_threshold_does_not_require_review() -> None:
    client = _client_for(
        {
            "work_type": {
                "type": "choice",
                "choice": "bug",
                "probabilities": {"bug": 0.95, "support": 0.05},
                "confidence": 0.95,
            }
        }
    )
    node = JevNode(
        questions={"work_type": choice(["bug", "support"])},
        client=client,
        thresholds={"work_type": 0.9},
    )

    update = node({})

    assert update["decision"].requires_review is False
    assert update["decision"].decisions["work_type"].meets_threshold is True


def test_threshold_on_boolean_question_warns() -> None:
    client = _client_for({"is_bug": {"type": "noul", "noul": 1.0}})

    with pytest.warns(UserWarning, match="boolean"):
        JevNode(
            questions={"is_bug": boolean()},
            client=client,
            thresholds={"is_bug": 0.9},
        )


def test_threshold_on_unknown_field_raises() -> None:
    client = _client_for(
        {
            "work_type": {
                "type": "choice",
                "choice": "bug",
                "probabilities": {"bug": 1.0},
                "confidence": 1.0,
            }
        }
    )

    with pytest.raises(ValueError, match="wrok_type"):
        JevNode(
            questions={"work_type": choice(["bug", "support"])},
            client=client,
            thresholds={"wrok_type": 0.9},
        )
