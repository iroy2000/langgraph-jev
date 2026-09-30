"""Errors raised by langgraph-jev.

These wrap the underlying ``typesafe-sdk`` exceptions so callers only need to
depend on this package's error hierarchy.
"""

from __future__ import annotations


class JevError(Exception):
    """Base class for all langgraph-jev errors."""


class JevConfigurationError(JevError):
    """Raised when a :class:`~langgraph_jev.client.JevClient` is misconfigured.

    Typically raised when no API key is available, either explicitly or via the
    ``TYPESAFE_API_KEY`` environment variable.
    """


class JevAPIError(JevError):
    """Raised when the Jev API returns an unsuccessful response.

    Attributes:
        status: The HTTP status code, when available.
        request_id: The TypeSafe request id, when available, for support requests.
    """

    def __init__(
        self,
        message: str,
        *,
        status: int | None = None,
        request_id: str | None = None,
    ) -> None:
        if status is not None:
            message = f"{message} (status={status})"
        if request_id is not None:
            message = f"{message} (request_id={request_id})"
        super().__init__(message)
        self.status = status
        self.request_id = request_id


class JevTimeoutError(JevError):
    """Raised when a request to the Jev API times out or fails to connect."""


class JevValidationError(JevError):
    """Raised when a Jev decision or question definition fails validation.

    For example, this is raised when :class:`~langgraph_jev.node.JevNode` is
    configured with ``low_confidence="error"`` and a decision falls below its
    configured confidence threshold, or when a question's fields (e.g.
    ``criteria``) are rejected by the underlying ``typesafe-sdk`` models.
    """
