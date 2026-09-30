# Build `langgraph-jev`

## Objective

Build an open-source Python package that provides a native **Jev decision node for LangGraph**, plus a LangChain-compatible runnable interface.

The core idea:

> **Jev is a typed probabilistic decision node inside an agent graph.**

The package should make it easy to plug Jev into LangGraph workflows without users needing to write HTTP/API plumbing themselves.

The flagship example should demonstrate:

```text
User / Jira Ticket
        │
        ▼
   Understand Agent
        │
        ▼
     Jev Node
        │
        ├── work_type
        ├── priority
        └── needs_engineer
        │
        ▼
    WorkTicket
        │
   ┌────┼────┐
   ▼    ▼    ▼
 Coding Support Docs
 Agent   Agent Agent
```

---

# 1. Package Name

Use:

```text
langgraph-jev
```

Python import:

```python
import langgraph_jev
```

Primary classes:

```python
from langgraph_jev import JevNode, JevClient
```

Also expose:

```python
from langgraph_jev import choice, boolean, score
```

If package naming conflicts exist on PyPI, investigate before changing the name.

---

# 2. Repository Structure

Create:

```text
langgraph-jev/
│
├── pyproject.toml
├── README.md
├── LICENSE
├── CONTRIBUTING.md
├── CHANGELOG.md
├── .gitignore
│
├── src/
│   └── langgraph_jev/
│       ├── __init__.py
│       ├── client.py
│       ├── node.py
│       ├── runnable.py
│       ├── questions.py
│       ├── models.py
│       ├── errors.py
│       ├── config.py
│       └── routing.py
│
├── tests/
│   ├── test_client.py
│   ├── test_questions.py
│   ├── test_node.py
│   ├── test_runnable.py
│   └── test_routing.py
│
└── examples/
    ├── basic.py
    ├── langgraph_basic.py
    ├── confidence_routing.py
    ├── work_ticket.py
    └── multi_agent.py
```

Use modern Python typing.

Target Python 3.11+ unless there is a strong reason to support 3.10.

---

# 3. Dependencies

Keep the core dependency footprint small.

Required:

```text
langgraph
langchain-core
httpx
pydantic
```

Do NOT require the full `langchain` package unless necessary.

Use `httpx.AsyncClient` for HTTP.

Support synchronous and asynchronous usage where practical.

Optional dependencies should be clearly separated.

---

# 4. Configuration

Support API key through environment variable:

```bash
TYPESAFE_API_KEY=...
```

Allow explicit configuration:

```python
client = JevClient(api_key="...")
```

Environment configuration should be preferred for examples.

Never log the API key.

Do not commit secrets.

---

# 5. JevClient

Implement a thin HTTP client around the documented TypeSafe Jev API.

Do NOT reverse engineer undocumented behavior.

Keep the HTTP implementation isolated inside:

```text
src/langgraph_jev/client.py
```

Example:

```python
from langgraph_jev import JevClient

client = JevClient()

result = client.decide(
    state={"title": "Customer cannot login", "description": "Customer receives a 401"},
    questions={...},
)
```

Also provide:

```python
await client.adecide(...)
```

The exact endpoint/request/response format should follow the current official Jev API documentation.

Do not hard-code assumptions about undocumented response fields.

---

# 6. Question Definitions

Create a simple typed question API.

At minimum support:

### Choice

```python
choice(["bug", "support", "documentation"])
```

### Boolean / Noul

```python
boolean()
```

### Score

```python
score()
```

Design these as Pydantic models or equivalent typed definitions.

Example:

```python
questions = {
    "work_type": choice(["bug", "support", "configuration", "documentation"]),
    "priority": choice(["critical", "high", "normal", "low"]),
    "needs_engineer": boolean(),
}
```

The question abstraction should remain extensible so additional Jev question types can be added later.

---

# 7. Response Models

Create strongly typed response models.

Conceptually:

```python
class JevDecision(BaseModel):
    value: Any
    probability: float | None = None
    confidence: float | None = None
```

And:

```python
class JevResult(BaseModel):
    decisions: dict[str, JevDecision]
```

Do not invent fields if the actual Jev API does not provide them.

Map the real API response into a stable SDK representation.

The SDK should hide API-specific response details from users.

---

# 8. JevNode

This is the most important class.

Implement:

```python
class JevNode: ...
```

Example:

```python
from langgraph_jev import JevNode, choice, boolean

jev = JevNode(
    questions={
        "work_type": choice(["bug", "support", "documentation"]),
        "priority": choice(["critical", "high", "normal", "low"]),
        "needs_engineer": boolean(),
    }
)
```

The node must be callable by LangGraph.

The node receives graph state.

For example:

```python
result = jev(state)
```

or whatever LangGraph-compatible callable design is appropriate.

The default behavior should be:

```text
Graph State
    ↓
JevNode
    ↓
JevResult
    ↓
Graph State
```

---

# 9. State Input Mapping

Allow users to specify which state field should be passed to Jev.

Example:

```python
jev = JevNode(state_key="structured_request", output_key="decision", questions={...})
```

Input:

```python
state = {"structured_request": {"title": "...", "description": "...", "customerTier": "Enterprise"}}
```

Output:

```python
{"decision": {...}}
```

Default:

```python
state_key = None
```

If `None`, pass the complete state.

---

# 10. Output Mapping

Allow:

```python
output_key = "decision"
```

Default:

```text
decision
```

The node should return a state update rather than replacing the entire LangGraph state.

Example:

```python
{"decision": JevResult(...)}
```

---

# 11. Confidence Thresholds

Implement optional confidence thresholds.

Example:

```python
jev = JevNode(
    questions={"work_type": choice([...]), "priority": choice([...])},
    thresholds={"work_type": 0.85, "priority": 0.90},
)
```

The node should expose whether decisions meet the configured threshold.

Do NOT silently discard low-confidence decisions.

Expose the original decision plus confidence information.

---

# 12. Low Confidence Handling

Support a configurable policy.

Example:

```python
jev = JevNode(..., low_confidence="human_review")
```

Possible modes:

```text
"allow"
"human_review"
"error"
```

Default:

```text
"allow"
```

If using `human_review`, the node should expose enough information for LangGraph conditional routing.

Example:

```python
def route_after_jev(state):

    if state["decision"].requires_review:
        return "human_review"

    return "continue"
```

Do not make assumptions about how a user's human-review workflow works.

---

# 13. Routing Helper

Provide an optional helper:

```python
from langgraph_jev import route_by_decision
```

Example:

```python
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

Keep routing deterministic.

Jev makes the probabilistic decision.

The application decides what to do with that decision.

This separation is important.

---

# 14. LangChain Runnable

Implement a LangChain-compatible abstraction.

Example:

```python
from langgraph_jev import JevRunnable

jev = JevRunnable(questions={"work_type": choice(["bug", "support", "documentation"])})

result = jev.invoke({"title": "Customer cannot login"})
```

Support:

```python
invoke()
ainvoke()
```

If practical, support batching later, but do not block MVP on it.

---

# 15. LangGraph Example

Create:

```text
examples/langgraph_basic.py
```

Example architecture:

```text
START
  ↓
understand
  ↓
jev
  ↓
create_ticket
  ↓
router
  ├── coding_agent
  ├── support_agent
  └── documentation_agent
```

Use a simple mock worker in the example.

Do not require OpenAI, Anthropic, or another model provider just to run the basic Jev example.

---

# 16. WorkTicket Example

This is the flagship example.

Create:

```text
examples/work_ticket.py
```

Define:

```python
class WorkTicket(BaseModel):
    id: str

    type: Literal["bug", "support", "configuration", "documentation"]

    priority: Literal["critical", "high", "normal", "low"]

    needs_engineer: bool

    title: str
    description: str

    context: dict

    acceptance_criteria: list[str]
```

Important:

**Jev does NOT generate the entire WorkTicket.**

Jev provides decisions.

Application code constructs the canonical WorkTicket.

Example:

```python
decision = state["decision"]

ticket = WorkTicket(
    id="WT-1234",
    type=decision["work_type"].value,
    priority=decision["priority"].value,
    needs_engineer=decision["needs_engineer"].value,
    title=request["title"],
    description=request["description"],
    context={"customerTier": request.get("customerTier"), "product": request.get("product")},
    acceptance_criteria=[
        "Identify root cause",
        "Determine affected workflow",
        "Add regression coverage if appropriate",
    ],
)
```

This distinction should be emphasized in the README.

---

# 17. Full WorkTicket Graph

The example should demonstrate:

```text
                    USER REQUEST
                         │
                         ▼
                ┌─────────────────┐
                │ Understand Node │
                │      LLM        │
                └────────┬────────┘
                         │
                         ▼
                   ┌───────────┐
                   │  JevNode  │
                   │           │
                   │ Decisions │
                   └─────┬─────┘
                         │
                         ▼
                ┌─────────────────┐
                │  WorkTicket     │
                │   Pydantic      │
                └────────┬────────┘
                         │
              ┌──────────┼──────────┐
              ▼          ▼          ▼
           Coding     Support      Docs
           Worker      Worker      Worker
```

This demonstrates the architectural thesis:

```text
LLM
→ understand

Jev
→ decide

Application
→ enforce contract

LangGraph
→ orchestrate

Worker Agent
→ execute
```

---

# 18. README

The README should immediately answer:

### What is this?

> `langgraph-jev` is an open-source LangGraph/LangChain integration that exposes Jev as a typed probabilistic decision node.

### Why?

Explain:

```text
Traditional agent:

Input → LLM → decide → execute

This package:

Input → understand → Jev decision → typed contract → execute
```

### Installation

```bash
pip install langgraph-jev
```

### Quick Start

Show the smallest possible example:

```python
from langgraph_jev import JevNode, choice

jev = JevNode(questions={"route": choice(["coding", "support", "research"])})
```

### LangGraph

Show:

```python
graph.add_node("jev", jev)
```

### Confidence Routing

Show:

```python
thresholds = {"route": 0.85}
```

### WorkTicket

Show the complete example.

---

# 19. README Architecture Diagram

Include:

```text
┌──────────────────────────────┐
│       User / Application     │
└──────────────┬───────────────┘
               │
               ▼
        ┌──────────────┐
        │ Understand   │
        │    Agent     │
        └──────┬───────┘
               │
               ▼
        ┌──────────────┐
        │    JevNode   │
        │              │
        │ Typed        │
        │ Decisions    │
        └──────┬───────┘
               │
               ▼
        ┌──────────────┐
        │ WorkTicket   │
        │   Contract   │
        └──────┬───────┘
               │
       ┌───────┼───────┐
       ▼       ▼       ▼
     Agent   Agent   Agent
```

---

# 20. Testing

Tests must not require a real TypeSafe API key.

Create a fake/mock Jev transport.

Test:

### Questions

* choice serialization
* boolean serialization
* score serialization
* validation

### Client

* request construction
* response parsing
* timeout
* HTTP errors
* malformed response

### JevNode

* state input
* output key
* complete state
* async execution
* error propagation
* threshold handling

### Routing

* normal route
* unknown decision
* fallback
* low confidence

### LangChain

* invoke
* ainvoke

---

# 21. Error Handling

Define explicit errors:

```python
JevError
JevConfigurationError
JevAPIError
JevValidationError
JevTimeoutError
```

Never expose API secrets in exceptions.

Include HTTP status and safe diagnostic information where appropriate.

---

# 22. Logging

Use Python logging.

Do not log:

* API keys
* raw sensitive user content by default
* authorization headers

Provide optional debug logging.

---

# 23. Type Safety

Use:

```python
from typing import TypedDict, Literal
```

and/or Pydantic.

Run:

```text
mypy
```

or another static type checker.

The public API should have complete type annotations.

---

# 24. Code Quality

Use:

```text
ruff
pytest
mypy
```

Configure them in `pyproject.toml`.

Use clean, idiomatic Python.

Keep the implementation small.

Do not over-engineer.

---

# 25. Documentation Philosophy

Do NOT describe Jev as an LLM.

Do NOT describe this package as an LLM wrapper.

Use this terminology:

> Jev is a typed probabilistic decision layer.

And:

> `JevNode` is a decision primitive that can be composed into an agent graph.

The README should emphasize that:

```text
Decision ≠ Execution
```

and:

```text
Jev ≠ Worker Agent
```

---

# 26. Important API Design Principle

Keep the public API extremely small.

Target:

```python
from langgraph_jev import (
    JevClient,
    JevNode,
    JevRunnable,
    choice,
    boolean,
    score,
)
```

A developer should be able to understand the package in under five minutes.

Avoid exposing internal HTTP models unless necessary.

---

# 27. Future Features

Do NOT implement these in MVP, but design the architecture so they are possible:

### Future

* streaming
* batch decisions
* caching
* LangSmith tracing
* OpenTelemetry
* middleware
* custom transports
* retries with exponential backoff
* decision evaluation datasets
* decision replay
* visual LangGraph Studio integration
* JavaScript/TypeScript implementation
* additional Jev question types

---

# 28. Example Future API

Keep this possible:

```python
jev = JevNode(
    questions={"category": choice([...]), "priority": choice([...]), "requires_human": boolean()},
    thresholds={"category": 0.85, "priority": 0.90},
)
```

And:

```python
graph.add_node("decision", jev)
```

The goal is that this feels like a native LangGraph node.

---

# 29. Deliverables

The implementation is complete when all of the following exist:

* [ ] Git repository
* [ ] `pyproject.toml`
* [ ] Package under `src/langgraph_jev`
* [ ] `JevClient`
* [ ] `JevNode`
* [ ] `JevRunnable`
* [ ] typed question definitions
* [ ] typed result models
* [ ] confidence handling
* [ ] routing helper
* [ ] synchronous API
* [ ] asynchronous API
* [ ] unit tests
* [ ] mocked API tests
* [ ] LangGraph example
* [ ] WorkTicket example
* [ ] multi-agent example
* [ ] README
* [ ] architecture diagram
* [ ] CONTRIBUTING.md
* [ ] CHANGELOG.md
* [ ] Ruff configuration
* [ ] pytest configuration
* [ ] type checking
* [ ] no secrets committed

---

# 30. Development Order

Implement in this order:

### Step 1

Repository/package scaffolding.

### Step 2

Question models.

### Step 3

Jev API client.

### Step 4

Response models.

### Step 5

`JevNode`.

### Step 6

Unit tests.

### Step 7

Confidence/threshold handling.

### Step 8

Routing helper.

### Step 9

LangChain Runnable.

### Step 10

LangGraph example.

### Step 11

WorkTicket example.

### Step 12

Documentation.

### Step 13

Run:

```bash
pytest
ruff check .
mypy src
```

Fix all issues.

---

# 31. Critical Constraint

Do not invent the Jev API.

Before implementing `JevClient`:

1. Inspect the current official TypeSafe/Jev API documentation.
2. Identify the current authentication mechanism.
3. Identify the actual request schema.
4. Identify the actual response schema.
5. Implement against the documented API.
6. Add a mock transport so tests don't depend on the live API.

If the API documentation differs from assumptions in this specification, **the official API documentation wins**.

---

# 32. Final Product Goal

When someone sees this:

```python
jev = JevNode(
    questions={
        "work_type": choice(["bug", "support", "docs"]),
        "priority": choice(["high", "normal", "low"]),
        "needs_engineer": boolean(),
    }
)

graph.add_node("jev", jev)
```

they should immediately understand:

> "This is a decision node I can plug into my LangGraph."

That is the product.

Do not turn this into a generic AI framework.

Keep it focused:

**Jev + LangGraph/LangChain + typed decisions + agent routing.**

