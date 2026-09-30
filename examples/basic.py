"""Minimal JevClient usage -- no LangGraph, no LangChain.

Requires TYPESAFE_API_KEY to be set in the environment. Run with:

    python examples/basic.py
"""

from __future__ import annotations

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from langgraph_jev import JevClient, boolean, choice

client = JevClient()

result = client.decide(
    state={
        "title": "Customer cannot login",
        "description": "Customer receives a 401 when signing in after the last deploy.",
    },
    questions={
        "work_type": choice(["bug", "support", "documentation"]),
        "is_urgent": boolean(instructions="Does this convey urgency or a broken workflow?"),
    },
)

print("model:", result.model)
print("work_type:", result.decisions["work_type"].value, result.decisions["work_type"].confidence)
print("is_urgent:", result.decisions["is_urgent"].value)
