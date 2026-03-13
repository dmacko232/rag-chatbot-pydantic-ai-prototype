import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class PipelineContext:
    """Mutable state passed through the pipeline."""

    raw_documents: list[dict[str, Any]] = field(default_factory=list)
    documents: list[Any] = field(default_factory=list)
    chunks: list[Any] = field(default_factory=list)
    extras: dict[str, Any] = field(default_factory=dict)


class Step(ABC):
    @property
    def name(self) -> str:
        return self.__class__.__name__

    @abstractmethod
    async def run(self, ctx: PipelineContext) -> PipelineContext:
        ...


class Pipeline:
    def __init__(self, steps: list[Step]) -> None:
        self._steps = steps

    async def run(self, ctx: PipelineContext | None = None) -> PipelineContext:
        ctx = ctx or PipelineContext()
        for step in self._steps:
            logger.info("Running step: %s", step.name)
            ctx = await step.run(ctx)
            logger.info("Completed step: %s", step.name)
        return ctx
