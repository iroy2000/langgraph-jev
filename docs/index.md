# langgraph-jev

`langgraph-jev` is an open-source LangGraph/LangChain integration for
[Jev](https://docs.typesafe.ai/introduction), TypeSafe's typed probabilistic
decision API. `JevNode` wraps it as a decision node you drop into an agent
graph -- it's not an LLM and not an LLM wrapper.

Jev evaluates typed *questions* against *state* and returns typed answers with
probabilities and confidence attached. There's no text generation and nothing
to parse -- your code branches on, sorts by, and routes with the result
directly.

For example, a `work_ticket` graph might run an "understand" step over a
customer request, hand the structured output to a `JevNode` for typed
decisions (work type, priority, whether it needs an engineer), and then route
to a coding, support, or docs worker based on those decisions. See the
[examples](examples.md#workticket) page for the full version of this.

![Terminal output of examples/basic.py](screenshots/basic-example.png)

## Where to go next

- [Quick start](quickstart.md) -- install, set your API key, define your
  first question.
- [API reference](api.md) -- the full public surface: `JevClient`, `JevNode`,
  `JevRunnable`, question builders, errors, and result types.
- [Examples](examples.md) -- runnable scripts covering LangGraph nodes,
  confidence thresholds, and the `WorkTicket` pattern.

## Source

The project lives at
[github.com/iroy2000/langgraph-jev](https://github.com/iroy2000/langgraph-jev).
Issues and pull requests are welcome -- see `CONTRIBUTING.md` in the repo.
