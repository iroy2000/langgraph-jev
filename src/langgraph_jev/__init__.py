"""langgraph-jev: a native Jev decision node for LangGraph.

Jev is a typed probabilistic decision layer: send state and typed questions,
get back structured answers your code can branch on, sort by, and route with.
This package exposes Jev as a LangGraph node and a LangChain-compatible
runnable, without requiring users to write HTTP plumbing themselves.

    Decision != Execution.
    Jev != Worker Agent.

Jev decides. Your application enforces the contract. LangGraph orchestrates.
Worker agents execute.
"""

from __future__ import annotations

from .client import JevClient
from .errors import (
    JevAPIError,
    JevConfigurationError,
    JevError,
    JevTimeoutError,
    JevValidationError,
)
from .models import JevDecision, JevResult
from .node import JevNode
from .questions import BooleanQuestion, ChoiceQuestion, ScoreQuestion, boolean, choice, score
from .routing import route_by_decision
from .runnable import JevRunnable

__all__ = [
    "JevClient",
    "JevNode",
    "JevRunnable",
    "choice",
    "boolean",
    "score",
    "route_by_decision",
    "JevDecision",
    "JevResult",
    "ChoiceQuestion",
    "BooleanQuestion",
    "ScoreQuestion",
    "JevError",
    "JevConfigurationError",
    "JevAPIError",
    "JevValidationError",
    "JevTimeoutError",
]

__version__ = "0.1.0"
