"""A minimal LangGraph graph with a JevNode.

    START -> understand -> jev -> create_ticket -> router -> {coding, support, documentation}

Uses a mock "understand" step so this runs without any LLM provider. Requires
TYPESAFE_API_KEY to be set in the environment. Run with:

    python examples/langgraph_basic.py
"""

from __future__ import annotations

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from langgraph_jev import JevNode, choice, route_by_decision


class GraphState(TypedDict, total=False):
    request: dict[str, Any]
    decision: Any
    ticket: dict[str, Any]


def understand(state: GraphState) -> dict[str, Any]:
    """Mock "understand" step: in a real graph this might call an LLM to
    normalize a raw ticket/message into structured `request` state."""
    return {"request": state["request"]}


jev = JevNode(
    state_key="request",
    output_key="decision",
    questions={
        "work_type": choice(["bug", "support", "documentation"]),
    },
)


def create_ticket(state: GraphState) -> dict[str, Any]:
    decision = state["decision"]
    return {"ticket": {"type": decision["work_type"].value, **state["request"]}}


def router(state: GraphState) -> str:
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


def coding_agent(state: GraphState) -> dict[str, Any]:
    print("coding_agent handling:", state["ticket"])
    return {}


def support_agent(state: GraphState) -> dict[str, Any]:
    print("support_agent handling:", state["ticket"])
    return {}


def documentation_agent(state: GraphState) -> dict[str, Any]:
    print("documentation_agent handling:", state["ticket"])
    return {}


def human_review(state: GraphState) -> dict[str, Any]:
    print("human_review needed for:", state["ticket"])
    return {}


graph = StateGraph(GraphState)
graph.add_node("understand", understand)
graph.add_node("jev", jev)
graph.add_node("create_ticket", create_ticket)
graph.add_node("coding_agent", coding_agent)
graph.add_node("support_agent", support_agent)
graph.add_node("documentation_agent", documentation_agent)
graph.add_node("human_review", human_review)

graph.add_edge(START, "understand")
graph.add_edge("understand", "jev")
graph.add_edge("jev", "create_ticket")
graph.add_conditional_edges(
    "create_ticket",
    router,
    {
        "coding_agent": "coding_agent",
        "support_agent": "support_agent",
        "documentation_agent": "documentation_agent",
        "human_review": "human_review",
    },
)
graph.add_edge("coding_agent", END)
graph.add_edge("support_agent", END)
graph.add_edge("documentation_agent", END)
graph.add_edge("human_review", END)

app = graph.compile()

if __name__ == "__main__":
    app.invoke(
        {
            "request": {
                "title": "Docs are missing for the new webhook API",
                "description": "There is no documentation page for the new webhook endpoints.",
            }
        }
    )
