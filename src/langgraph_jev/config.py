"""Configuration constants for langgraph-jev.

These mirror the environment variables and defaults used by the underlying
``typesafe-sdk`` client. See https://docs.typesafe.ai/sdk/python/usage for details.
"""

from __future__ import annotations

API_KEY_ENV_VAR = "TYPESAFE_API_KEY"
BASE_URL_ENV_VAR = "TYPESAFE_BASE_URL"
DEFAULT_MODEL_ENV_VAR = "TYPESAFE_DEFAULT_MODEL"
DEFAULT_MODEL = "jev-latest"
