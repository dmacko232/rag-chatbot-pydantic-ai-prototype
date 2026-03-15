import asyncio
import json
import logging

from openai import AsyncAzureOpenAI

from data_pipeline.interfaces import IDocumentChunker
from data_pipeline.models import ChunkData, ChunkedDocument, RawDocument
from shared.config import Settings
from shared.prompts import get_prompt

logger = logging.getLogger(__name__)


class FixedSizeChunker(IDocumentChunker):
    """Split documents into fixed-size character chunks with overlap."""

    def __init__(self, chunk_size: int = 2000, overlap: int = 200) -> None:
        self._chunk_size = chunk_size
        self._overlap = overlap

    async def chunk(self, documents: list[RawDocument]) -> list[ChunkedDocument]:
        results: list[ChunkedDocument] = []

        for doc in documents:
            text = doc.content
            chunks: list[ChunkData] = []
            start = 0

            while start < len(text):
                end = start + self._chunk_size
                chunk_text = text[start:end]

                context_start = max(0, start - self._overlap)
                context_end = min(len(text), end + self._overlap)
                context_text = text[context_start:context_end]

                chunks.append(ChunkData(content=chunk_text, content_for_llm=context_text))
                start += self._chunk_size - self._overlap

            results.append(
                ChunkedDocument(
                    source_file=doc.source_file,
                    content=doc.content,
                    chunks=chunks,
                )
            )

        return results


class LLMDocumentChunker(IDocumentChunker):
    """Use Azure OpenAI to split documents into semantic chunks and extract metadata."""

    def __init__(self, settings: Settings, concurrency: int = 5) -> None:
        self._client = AsyncAzureOpenAI(
            api_key=settings.azure_openai_api_key,
            azure_endpoint=settings.azure_openai_endpoint,
            api_version=settings.azure_openai_api_version,
            max_retries=10,
        )
        self._deployment = settings.azure_openai_deployment
        self._semaphore = asyncio.Semaphore(concurrency)

    async def chunk(self, documents: list[RawDocument]) -> list[ChunkedDocument]:
        system_prompt = get_prompt("chunking_system_prompt")
        total = len(documents)

        async def _process(idx: int, doc: RawDocument) -> ChunkedDocument:
            async with self._semaphore:
                logger.info("Chunking document %d/%d: %s", idx + 1, total, doc.source_file)
                parsed = await self._call_llm(system_prompt, doc.content)

            chunks = [
                ChunkData(
                    content=c["content"],
                    content_for_llm=c.get("content_for_llm", c["content"]),
                )
                for c in parsed.get("chunks", [])
            ]

            return ChunkedDocument(
                source_file=doc.source_file,
                content=doc.content,
                year=parsed.get("year"),
                business_segment=parsed.get("business_segment", "deutsche_telekom_group"),
                document_type=parsed.get("document_type", "general"),
                chunks=chunks,
            )

        results = await asyncio.gather(*[_process(i, doc) for i, doc in enumerate(documents)])
        return list(results)

    async def _call_llm(self, system_prompt: str, content: str) -> dict:
        response = await self._client.chat.completions.create(
            model=self._deployment,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content},
            ],
            temperature=0.0,
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content or "{}"
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            logger.error("Failed to parse LLM chunking response")
            return {"chunks": [{"content": content, "content_for_llm": content}]}
