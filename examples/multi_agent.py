"""Full multi-agent WorkTicket graph.

    USER REQUEST -> Understand (mock) -> JevNode -> WorkTicket (Pydantic)
                 -> {Coding, Support, Docs} Worker

Demonstrates the full architectural pipeline:

    LLM         -> understand
    Jev         -> decide
    Application -> enforce contract
    LangGraph   -> orchestrate
    Worker Agent -> execute

Uses mock workers so this runs without any LLM provider. Requires
TYPESAFE_API_KEY to be set in the environment. Run with:

    python examples/multi_agent.py
"""

from __future__ import annotations

from typing import Any, Literal, TypedDict

from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel

from langgraph_jev import JevNode, boolean, choice, route_by_decision


class WorkTicket(BaseModel):
    id: str
    type: Literal["bug", "support", "configuration", "documentation"]
    priority: Literal["critical", "high", "normal", "low"]
    needs_engineer: bool
    title: str
    description: str
    context: dict


class GraphState(TypedDict, total=False):
    request: dict[str, Any]
    decision: Any
    ticket: WorkTicket


def understand(state: GraphState) -> dict[str, Any]:
    """Mock understand step. Replace with an LLM call in a real system."""
    return {"request": state["request"]}


jev = JevNode(
    state_key="request",
    output_key="decision",
    questions={
        "work_type": choice(["bug", "support", "configuration", "documentation"]),
        "priority": choice(["critical", "high", "normal", "low"]),
        "needs_engineer": boolean(
            instructions="Does this require an engineer rather than support staff?"
        ),
    },
    thresholds={"work_type": 0.7},
    low_confidence="human_review",
)


def build_ticket(state: GraphState) -> dict[str, Any]:
    decision = state["decision"]
    request = state["request"]
    ticket = WorkTicket(
        id="WT-0001",
        type=decision["work_type"].value,
        priority=decision["priority"].value,
        needs_engineer=bool(round(decision["needs_engineer"].value)),
        title=request["title"],
        description=request["description"],
        context={"customerTier": request.get("customerTier")},
    )
    return {"ticket": ticket}


def route_work(state: GraphState) -> str:
    return route_by_decision(
        state["decision"],
        field="work_type",
        routes={
            "bug": "coding_worker",
            "configuration": "coding_worker",
            "support": "support_worker",
            "documentation": "documentation_worker",
        },
        fallback="human_review",
    )


def coding_worker(state: GraphState) -> dict[str, Any]:
    print("[coding_worker]", state["ticket"].model_dump_json())
    return {}


def support_worker(state: GraphState) -> dict[str, Any]:
    print("[support_worker]", state["ticket"].model_dump_json())
    return {}


def documentation_worker(state: GraphState) -> dict[str, Any]:
    print("[documentation_worker]", state["ticket"].model_dump_json())
    return {}


def human_review(state: GraphState) -> dict[str, Any]:
    print("[human_review] low-confidence decision, needs a human:", state["decision"])
    return {}


graph = StateGraph(GraphState)
graph.add_node("understand", understand)
graph.add_node("jev", jev)
graph.add_node("build_ticket", build_ticket)
graph.add_node("coding_worker", coding_worker)
graph.add_node("support_worker", support_worker)
graph.add_node("documentation_worker", documentation_worker)
graph.add_node("human_review", human_review)

graph.add_edge(START, "understand")
graph.add_edge("understand", "jev")
graph.add_edge("jev", "build_ticket")
graph.add_conditional_edges(
    "build_ticket",
    route_work,
    {
        "coding_worker": "coding_worker",
        "support_worker": "support_worker",
        "documentation_worker": "documentation_worker",
        "human_review": "human_review",
    },
)
graph.add_edge("coding_worker", END)
graph.add_edge("support_worker", END)
graph.add_edge("documentation_worker", END)
graph.add_edge("human_review", END)

app = graph.compile()

if __name__ == "__main__":
    app.invoke(
        {
            "request": {
                "title": "Customer cannot login",
                "description": "Customer receives a 401 when signing in after the last deploy.",
                "customerTier": "Enterprise",
            }
        }
    )
