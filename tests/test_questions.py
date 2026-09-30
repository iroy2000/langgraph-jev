"""Tests for typed question definitions."""

from __future__ import annotations

from typesafe_sdk import Choice as SdkChoice
from typesafe_sdk import Noul as SdkNoul
from typesafe_sdk import Score as SdkScore

from langgraph_jev import boolean, choice, score
from langgraph_jev.questions import BooleanQuestion, ChoiceQuestion, ScoreQuestion


def test_choice_from_sequence() -> None:
    q = choice(["bug", "support", "docs"])
    assert isinstance(q, ChoiceQuestion)
    assert q.criteria == {"bug": None, "support": None, "docs": None}
    sdk = q.to_sdk()
    assert isinstance(sdk, SdkChoice)


def test_choice_from_mapping_with_rubric() -> None:
    q = choice({"billing": "Payment issues", "technical": "Bugs"})
    assert q.criteria == {"billing": "Payment issues", "technical": "Bugs"}


def test_choice_serialization_round_trip() -> None:
    q = choice(["a", "b"], instructions="Pick one")
    sdk = q.to_sdk()
    dumped = sdk.model_dump()
    assert dumped["type"] == "choice"
    assert dumped["criteria"] == {"a": None, "b": None}
    assert dumped["instructions"] == "Pick one"


def test_boolean_default() -> None:
    q = boolean()
    assert isinstance(q, BooleanQuestion)
    assert q.criteria is None
    sdk = q.to_sdk()
    assert isinstance(sdk, SdkNoul)


def test_boolean_with_criteria() -> None:
    q = boolean(
        instructions="Is this urgent?", criteria={"true": "Time sensitive", "false": "Not urgent"}
    )
    dumped = q.to_sdk().model_dump()
    assert dumped["type"] == "noul"
    assert dumped["criteria"] == {"true": "Time sensitive", "false": "Not urgent"}


def test_score_default_levels() -> None:
    q = score()
    assert isinstance(q, ScoreQuestion)
    assert q.criteria == ["low", "medium", "high"]
    sdk = q.to_sdk()
    assert isinstance(sdk, SdkScore)


def test_score_explicit_empty_levels_is_not_silently_replaced_by_default() -> None:
    """An explicitly empty list is a caller mistake, not a request for the default.

    Regression test: score() previously used a falsy check (`if levels`), which
    treated `score([])` identically to `score()`, silently masking the caller's
    (invalid) input behind an unrelated 3-level default.
    """
    q = score([])
    assert q.criteria == []


def test_boolean_explicit_empty_criteria_preserved() -> None:
    q = boolean(criteria={})
    assert q.criteria == {}


def test_score_with_custom_levels() -> None:
    q = score(["calm", "frustrated", "angry"], instructions="Rate frustration")
    dumped = q.to_sdk().model_dump()
    assert dumped["criteria"] == ["calm", "frustrated", "angry"]
    assert dumped["instructions"] == "Rate frustration"


def test_choice_rejects_none_instructions_key_but_allows_none_value() -> None:
    q = choice(["a", "b"])
    dumped = q.to_sdk().model_dump()
    # instructions is omitted from the wire form when unset
    assert "instructions" not in dumped
