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
        return self.client.decide(input, self.questions)

    async def ainvoke(
        self, input: Any, config: RunnableConfig | None = None, **kwargs: Any
    ) -> JevResult:
        return await self.client.adecide(input, self.questions)
