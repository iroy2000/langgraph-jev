# Quick start

## Installation

```bash
pip install langgraph-jev
```

Set your API key (never commit it):

```bash
export TYPESAFE_API_KEY=...
```

The examples in `examples/` also support a project-local `.env` file (already
covered by `.gitignore`) via optional `python-dotenv` support:

```bash
pip install "langgraph-jev[examples]"
echo "TYPESAFE_API_KEY=..." > .env
python examples/basic.py
```

## Define a node

```python
from langgraph_jev import JevNode, choice

jev = JevNode(
    questions={
        "route": choice(["coding", "support", "research"]),
    }
)
```

Running `examples/basic.py` against a real state produces typed decisions
with confidence scores, not free text:

![Terminal output of examples/basic.py](screenshots/basic-example.png)

## Resource cleanup

`JevClient` (and anything built on it, like `JevNode`/`JevRunnable`) opens
underlying HTTP clients on construction. Close it when you're done, or use
it as a context manager:

```python
from langgraph_jev import JevClient, choice

with JevClient() as client:
    result = client.decide(state={"title": "..."}, questions={"route": choice(["a", "b"])})

# or, in async code:
async with JevClient() as client:
    result = await client.adecide(state={"title": "..."}, questions={"route": choice(["a", "b"])})
```

If you construct a long-lived `JevNode`/`JevRunnable` (e.g. one per graph,
reused across requests), there's no need to close it per-call -- call
`client.close()`/`await client.aclose()` once when your application shuts
down.

## Adding it to a LangGraph graph

`JevNode` is directly callable by LangGraph -- it receives graph state and
returns a state update (not a replacement of the whole state):

```python
graph.add_node("jev", jev)
```

By default the entire graph state is passed to Jev as `state`. Use
`state_key`/`output_key` to scope input and output:

```python
jev = JevNode(
    state_key="structured_request",
    output_key="decision",
    questions={...},
)
```

## Confidence routing

Choice and Score answers include a `confidence` score derived from the
response's probability distribution (see
[Confidence](https://docs.typesafe.ai/confidence)). Configure thresholds and
a policy for what happens below them:

```python
jev = JevNode(
    questions={
        "work_type": choice(["bug", "support", "configuration", "documentation"]),
        "priority": choice(["critical", "high", "normal", "low"]),
    },
    thresholds={"work_type": 0.85, "priority": 0.90},
    low_confidence="human_review",  # "allow" (default) | "human_review" | "error"
)


def route_after_jev(state):
    if state["decision"].requires_review:
        return "human_review"
    return "continue"
```

Low-confidence decisions are never silently discarded -- the full decision
and its confidence are always available on the result.

## Routing helper

```python
from langgraph_jev import route_by_decision


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

Jev makes the probabilistic decision; your application code decides what to
do with it. Routing stays deterministic.

## Using it as a LangChain Runnable

```python
from langgraph_jev import JevRunnable, choice

jev = JevRunnable(questions={"route": choice(["coding", "support", "research"])})
result = jev.invoke({"title": "Customer cannot login"})
```

Supports both `invoke()` and `ainvoke()`, and goes through LangChain's
standard callback/tracing machinery (`RunnableConfig`, LangSmith, etc.).
