"""A LangChain-compatible Runnable wrapper around Jev decisions."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from langchain_core.runnables import Runnable, RunnableConfig

from .client import JevClient
from .models import JevResult
from .questions import Question


class JevRunnable(Runnable[Any, JevResult]):
    """Evaluate Jev questions as a standard LangChain ``Runnable``.

    Implements ``invoke``/``ainvoke`` via :meth:`Runnable._call_with_config` /
    :meth:`Runnable._acall_with_config` so that LangChain callbacks (e.g.
    LangSmith tracing) and ``RunnableConfig`` (``tags``, ``metadata``,
    ``run_name``) behave the same as any other Runnable in a chain.

    Example:
        ```python
        from langgraph_jev import JevRunnable, choice

        jev = JevRunnable(questions={"route": choice(["coding", "support", "research"])})
        result = jev.invoke({"title": "Customer cannot login"})
        ```
    """

    def __init__(
        self, questions: Mapping[str, Question], *, client: JevClient | None = None
    ) -> None:
        self.questions = dict(questions)
        self.client = client or JevClient()

    def invoke(self, input: Any, config: RunnableConfig | None = None, **kwargs: Any) -> JevResult:
        return self._call_with_config(
            lambda inner: self.client.decide(inner, self.questions),
            input,
            config,
            run_type="chain",
        )

    async def ainvoke(
        self, input: Any, config: RunnableConfig | None = None, **kwargs: Any
    ) -> JevResult:
        async def _decide(inner: Any) -> JevResult:
            return await self.client.adecide(inner, self.questions)

        return await self._acall_with_config(_decide, input, config, run_type="chain")
