# API reference

## Public API

```python
from langgraph_jev import (
    JevClient,
    JevNode,
    JevRunnable,
    choice,
    boolean,
    score,
    route_by_decision,
)
```

That's the full public API. Errors (`JevError` and its subclasses
`JevConfigurationError`, `JevAPIError`, `JevTimeoutError`,
`JevValidationError`) and the result types (`JevDecision`, `JevResult`) are
also exported for type annotations and `except` clauses.

## Core classes

### `JevClient`

Thin wrapper around `typesafe-sdk`'s sync and async clients. Reads
`TYPESAFE_API_KEY` from the environment if `api_key` isn't passed explicitly.
Supports `decide()`/`adecide()`, and can be used as a sync or async context
manager (see [Resource cleanup](quickstart.md#resource-cleanup)).

### `JevNode`

A callable LangGraph node. Takes `questions`, an optional `client`,
`state_key`/`output_key` for scoping graph state, `thresholds` for
per-question confidence gates, and a `low_confidence` policy
(`"allow"` | `"human_review"` | `"error"`).

Raises `ValueError` at construction time if a `thresholds` key doesn't match
any configured question name, and raises `JevValidationError` from
`__call__`/`ainvoke` if `low_confidence="error"` and a decision falls below
its threshold.

### `JevRunnable`

A standard LangChain `Runnable[Any, JevResult]`. Implements `invoke`/`ainvoke`
through LangChain's `_call_with_config`/`_acall_with_config`, so callbacks
(LangSmith tracing, etc.) and `RunnableConfig` behave the same as any other
Runnable in a chain.

## Question builders

### `choice(options, *, instructions=None)`

Selects one option from a fixed set. `options` can be a plain list of names,
or a mapping of name to a rubric description for that option.

### `boolean(*, instructions=None, criteria=None)`

A yes/no judgment (the Jev API's *Noul* primitive). Returns a probability of
"yes" in `[0, 1]` as `value`; `criteria` optionally describes what counts as
`"true"` and `"false"`.

!!! note
    Boolean/Noul answers don't report a separate `confidence` score --
    `value` *is* the probability. Configuring a `thresholds` entry for a
    `boolean()` question has no effect, and `JevNode` emits a `UserWarning`
    if you try.

### `score(levels=None, *, instructions=None)`

Rates the state against an ordered rubric of `levels`. Defaults to a generic
three-level rubric (`["low", "medium", "high"]`) if omitted. Passing an
explicit empty list is not treated the same as omitting `levels` -- it's
passed through as-is and rejected by the API.

## Result types

### `JevDecision`

One answer per question: `field`, `type`, `value`, `confidence` (choice/score
only), `probabilities`, and `meets_threshold`.

### `JevResult`

The full set of decisions from one call: `model`, `decisions` (keyed by
question name, also indexable via `result["field"]`), `requires_review`, and
`usage`.

## Routing helper

### `route_by_decision(result, *, field, routes, fallback)`

Maps a decision's value to a route name. Returns `fallback` if
`result.requires_review` is set or the decision's value has no matching entry
in `routes`.

## Errors

All raised errors are subclasses of `JevError`:

| Exception | Raised when |
| --- | --- |
| `JevConfigurationError` | Client construction fails (e.g. no API key found) |
| `JevValidationError` | A question fails validation, or a threshold gate rejects a low-confidence decision |
| `JevTimeoutError` | The request times out |
| `JevAPIError` | The API returns an error response, or an expected answer is missing from it |
