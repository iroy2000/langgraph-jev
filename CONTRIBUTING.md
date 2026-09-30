# Contributing to langgraph-jev

Thanks for your interest in contributing!

## Development setup

```bash
git clone https://github.com/langgraph-jev/langgraph-jev.git
cd langgraph-jev
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Running checks

```bash
pytest
ruff check .
mypy src
```

All three must pass before a PR is merged.

## Guidelines

- Keep the public API small (`JevClient`, `JevNode`, `JevRunnable`, `choice`,
  `boolean`, `score`, `route_by_decision`). Avoid exposing internal
  `typesafe-sdk` types directly.
- Tests must not require a real `TYPESAFE_API_KEY`. Inject a fake/mock
  `sync_client`/`async_client` into `JevClient` instead.
- Never log API keys, authorization headers, or raw sensitive user content.
- Do not invent or assume undocumented Jev API behavior. If in doubt, check
  https://docs.typesafe.ai and the `typesafe-sdk` source before changing
  `client.py`.
- Keep the implementation small; avoid turning this into a generic AI
  framework. This package is scoped to Jev + LangGraph/LangChain + typed
  decisions + agent routing.

## Commit messages

Use clear, descriptive commit messages. Reference related issues where
applicable.
