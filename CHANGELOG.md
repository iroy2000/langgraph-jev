# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- Initial release: `JevClient`, `JevNode`, `JevRunnable`.
- Typed question definitions: `choice()`, `boolean()`, `score()`.
- Typed result models: `JevDecision`, `JevResult`.
- Confidence thresholds and `low_confidence` policy (`allow` / `human_review`
  / `error`) on `JevNode`.
- Deterministic routing helper: `route_by_decision()`.
- Synchronous and asynchronous APIs (`decide`/`adecide`, `invoke`/`ainvoke`).
- Examples: `basic.py`, `langgraph_basic.py`, `confidence_routing.py`,
  `work_ticket.py`, `multi_agent.py`.
- `py.typed` marker (the package is PEP 561-typed).
- Sync/async context manager support on `JevClient`.
- `SECURITY.md` with a private vulnerability-reporting policy.

### Fixed

- `JevRunnable.invoke`/`ainvoke` now go through LangChain's
  `_call_with_config`/`_acall_with_config`, so callbacks (e.g. LangSmith
  tracing) and `RunnableConfig` (`tags`, `metadata`, `run_name`) work as
  expected for a LangChain `Runnable`.
- `JevNode` now raises `ValueError` at construction time if a `thresholds`
  key doesn't match any configured question name, instead of silently
  ignoring it.
- `JevNode` warns if a confidence threshold is configured on a `boolean()`
  question, which never reports a confidence score.
- Errors raised while translating typed questions into `typesafe-sdk`
  question objects (e.g. invalid `criteria`) are now wrapped in
  `JevValidationError` instead of leaking a raw `pydantic.ValidationError`.
- A Jev response missing an expected answer now raises a clear
  `JevAPIError` instead of an unhandled `KeyError`.
- `JevAPIError`'s message now includes `status`/`request_id` when present.
- The package version is now defined in exactly one place
  (`langgraph_jev.__version__`), read by `pyproject.toml` via Hatch's
  dynamic versioning, instead of being duplicated across two files.
- Removed the redundant `License :: OSI Approved :: MIT License` classifier
  now that `pyproject.toml` uses the PEP 639 SPDX license expression.
- `score()` no longer falls back to the default three-level rubric when
  called with an explicit empty list (`score([])`); the empty list is now
  passed through and rejected by the API, rather than silently replaced.
- Added `Raises:` sections to the docstrings of `JevClient.__init__`,
  `decide`/`adecide`, and `JevNode.__init__`/`__call__`/`ainvoke`, and
  documented `JevClient`'s context-manager support in the README (it was
  implemented but previously undocumented).
