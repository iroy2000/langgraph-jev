# Examples

| File | Demonstrates |
| --- | --- |
| `examples/basic.py` | Minimal `JevClient` usage |
| `examples/langgraph_basic.py` | A minimal LangGraph graph with a `JevNode` |
| `examples/confidence_routing.py` | Thresholds and `low_confidence="human_review"` |
| `examples/work_ticket.py` | Building a `WorkTicket` from Jev's decisions |
| `examples/multi_agent.py` | Full graph: understand -> Jev -> ticket -> routed workers |

All examples read `TYPESAFE_API_KEY` from the environment (or a local `.env`
file, if you installed `langgraph-jev[examples]`) and make real calls to the
Jev API.

## WorkTicket

Jev doesn't generate the `WorkTicket` itself -- it provides the decisions,
and your application code builds the typed contract from them:

```python
decision = state["decision"]

ticket = WorkTicket(
    id="WT-1234",
    type=decision["work_type"].value,
    priority=decision["priority"].value,
    needs_engineer=decision["needs_engineer"].value,
    title=request["title"],
    description=request["description"],
    context={"customerTier": request.get("customerTier")},
    acceptance_criteria=["Identify root cause", "Add regression coverage if appropriate"],
)
```

![Terminal output of examples/work_ticket.py](screenshots/work-ticket-example.png)

See `examples/work_ticket.py` for the full example: an understand step feeds
Jev, Jev's decisions build a `WorkTicket`, and the ticket routes to a coding,
support, or docs worker. `examples/multi_agent.py` wires this into a
complete LangGraph graph with routed worker nodes.
