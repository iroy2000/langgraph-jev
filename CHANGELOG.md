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
