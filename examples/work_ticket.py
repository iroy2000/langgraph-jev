"""The flagship WorkTicket example.

Demonstrates the core architectural thesis of this package:

    Jev does NOT generate the entire WorkTicket.
    Jev provides decisions. Application code constructs the canonical WorkTicket.

Requires TYPESAFE_API_KEY to be set in the environment. Run with:

    python examples/work_ticket.py
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from langgraph_jev import JevNode, boolean, choice


class WorkTicket(BaseModel):
    id: str
    type: Literal["bug", "support", "configuration", "documentation"]
    priority: Literal["critical", "high", "normal", "low"]
    needs_engineer: bool
    title: str
    description: str
    context: dict
    acceptance_criteria: list[str]


jev = JevNode(
    questions={
        "work_type": choice(["bug", "support", "configuration", "documentation"]),
        "priority": choice(["critical", "high", "normal", "low"]),
        "needs_engineer": boolean(
            instructions="Does resolving this require an engineer (vs. support staff)?"
        ),
    }
)

request = {
    "title": "Customer cannot login",
    "description": "Customer receives a 401 when signing in after the last deploy.",
    "customerTier": "Enterprise",
    "product": "core-api",
}

update = jev(request)
decision = update["decision"]

# Jev decides. Application code enforces the typed contract.
ticket = WorkTicket(
    id="WT-1234",
    type=decision["work_type"].value,
    priority=decision["priority"].value,
    needs_engineer=bool(round(decision["needs_engineer"].value)),
    title=request["title"],
    description=request["description"],
    context={
        "customerTier": request.get("customerTier"),
        "product": request.get("product"),
    },
    acceptance_criteria=[
        "Identify root cause",
        "Determine affected workflow",
        "Add regression coverage if appropriate",
    ],
)

print(ticket.model_dump_json(indent=2))
