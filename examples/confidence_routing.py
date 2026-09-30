"""Confidence thresholds and low_confidence="human_review".

Requires TYPESAFE_API_KEY to be set in the environment. Run with:

    python examples/confidence_routing.py
"""

from __future__ import annotations

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from langgraph_jev import JevNode, choice


def route_after_jev(state: dict) -> str:
    if state["decision"].requires_review:
        return "human_review"
    return "continue"


jev = JevNode(
    questions={
        "work_type": choice(["bug", "support", "configuration", "documentation"]),
        "priority": choice(["critical", "high", "normal", "low"]),
    },
    thresholds={
        "work_type": 0.85,
        "priority": 0.90,
    },
    low_confidence="human_review",
)

state = {
    "title": "It's kind of slow sometimes?",
    "description": "Not sure if this is a bug or expected. Happens occasionally.",
}

update = jev({"title": state["title"], "description": state["description"]})
decision = update["decision"]

for field, d in decision.decisions.items():
    print(
        f"{field}: value={d.value!r} confidence={d.confidence} meets_threshold={d.meets_threshold}"
    )

print("route:", route_after_jev({"decision": decision}))
