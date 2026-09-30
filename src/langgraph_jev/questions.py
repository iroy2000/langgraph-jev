"""Typed question definitions for Jev.

These wrap the three TypeSafe/Jev question primitives -- Choice, Noul, and
Score -- in a small, stable public API. See https://docs.typesafe.ai/primitives
for the underlying concepts.

``boolean()`` is this package's name for what the Jev API calls a *Noul*
question (a yes/no judgment that returns the probability the answer is yes).
We use the more familiar name at the public API boundary while mapping
directly onto ``typesafe_sdk.Noul`` when building requests.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Literal, cast

from pydantic import BaseModel
from typesafe_sdk import Choice as _SdkChoice
from typesafe_sdk import Noul as _SdkNoul
from typesafe_sdk import NoulCriteria as _SdkNoulCriteria
from typesafe_sdk import Question as _SdkQuestion
from typesafe_sdk import Score as _SdkScore

JevInstructions = Any
"""A question's instructions: a string, or structured JSON (object/array)."""


class ChoiceQuestion(BaseModel):
    """Selects one option from a fixed set of labeled options."""

    type: Literal["choice"] = "choice"
    criteria: dict[str, Any]
    instructions: JevInstructions | None = None

    def to_sdk(self) -> _SdkQuestion:
        return _SdkChoice(instructions=self.instructions, criteria=self.criteria)


class BooleanQuestion(BaseModel):
    """A yes/no judgment. Maps onto the Jev API's Noul primitive."""

    type: Literal["boolean"] = "boolean"
    criteria: dict[str, Any] | None = None
    instructions: JevInstructions | None = None

    def to_sdk(self) -> _SdkQuestion:
        criteria = cast(_SdkNoulCriteria, self.criteria) if self.criteria is not None else None
        return _SdkNoul(instructions=self.instructions, criteria=criteria)


class ScoreQuestion(BaseModel):
    """Rates the state against an ordered rubric of levels."""

    type: Literal["score"] = "score"
    criteria: list[Any]
    instructions: JevInstructions | None = None

    def to_sdk(self) -> _SdkQuestion:
        return _SdkScore(instructions=self.instructions, criteria=self.criteria)


Question = ChoiceQuestion | BooleanQuestion | ScoreQuestion
"""Any typed langgraph-jev question definition."""


def choice(
    options: Sequence[str] | Mapping[str, Any],
    *,
    instructions: JevInstructions | None = None,
) -> ChoiceQuestion:
    """Define a Choice question: select one option from ``options``.

    ``options`` may be a plain sequence of option names, or a mapping of
    option name to a rubric description for that option.
    """
    criteria = (
        dict(options) if isinstance(options, Mapping) else {option: None for option in options}
    )
    return ChoiceQuestion(criteria=criteria, instructions=instructions)


def boolean(
    *,
    instructions: JevInstructions | None = None,
    criteria: Mapping[str, Any] | None = None,
) -> BooleanQuestion:
    """Define a yes/no question (a Jev Noul question).

    ``criteria`` optionally describes what a "true" and "false" answer mean,
    via the keys ``"true"`` and ``"false"``.
    """
    return BooleanQuestion(
        instructions=instructions,
        criteria=dict(criteria) if criteria is not None else None,
    )


def score(
    levels: Sequence[Any] | None = None,
    *,
    instructions: JevInstructions | None = None,
) -> ScoreQuestion:
    """Define a Score question: rate the state against ordered ``levels``.

    ``levels`` is an ordered list of rubric descriptions, one per score level
    starting at zero. Defaults to a generic three-level rubric if omitted.
    """
    return ScoreQuestion(
        criteria=list(levels) if levels is not None else ["low", "medium", "high"],
        instructions=instructions,
    )
