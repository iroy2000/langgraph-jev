# Security Policy

## Reporting a vulnerability

If you discover a security vulnerability in `langgraph-jev` (for example, a
way the library could leak an API key, credentials, or other sensitive
state), please **do not** open a public GitHub issue.

Instead, report it privately via [GitHub Security Advisories](https://github.com/iroy2000/langgraph-jev/security/advisories/new)
for this repository. We'll acknowledge the report, investigate, and publish
a fix and advisory once a patch is available.

## Scope

This package wraps the official `typesafe-sdk` client and never implements
its own HTTP transport or credential storage. Vulnerabilities in the
underlying TypeSafe/Jev API or the `typesafe-sdk` package itself should be
reported directly to TypeSafe at https://docs.typesafe.ai.

## Supported versions

As a pre-1.0 project, only the latest published release is supported with
security fixes.
