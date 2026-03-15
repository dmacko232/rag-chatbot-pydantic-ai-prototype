from abc import ABC, abstractmethod

from data_pipeline.models import ChunkedDocument, RawDocument


class IDocumentLoader(ABC):
    @abstractmethod
    async def load(self) -> list[RawDocument]: ...


class IDocumentCleaner(ABC):
    @abstractmethod
    async def clean(self, documents: list[RawDocument]) -> list[RawDocument]: ...


class IDocumentChunker(ABC):
    @abstractmethod
    async def chunk(self, documents: list[RawDocument]) -> list[ChunkedDocument]: ...


class IChunkEmbedder(ABC):
    @abstractmethod
    async def embed(self, documents: list[ChunkedDocument]) -> list[ChunkedDocument]: ...


class IDocumentIndexer(ABC):
    @abstractmethod
    async def index(self, documents: list[ChunkedDocument]) -> None: ...


class IRaptorSummarizer(ABC):
    @abstractmethod
    async def summarize(self, documents: list[RawDocument]) -> None: ...
