import json
import logging

from openai import AsyncAzureOpenAI
from sqlmodel import Session

from data_pipeline.interfaces import IRaptorSummarizer
from data_pipeline.models import RawDocument
from shared.config import Settings
from shared.db import create_db_engine
from shared.models import Chunk, Document
from shared.prompts import get_prompt

logger = logging.getLogger(__name__)


class LLMRaptorSummarizer(IRaptorSummarizer):
    def __init__(self, settings: Settings) -> None:
        self._client = AsyncAzureOpenAI(
            api_key=settings.azure_openai_api_key,
            azure_endpoint=settings.azure_openai_endpoint,
            api_version=settings.azure_openai_api_version,
        )
        self._deployment = settings.azure_openai_deployment
        self._engine = create_db_engine(settings)

    async def summarize(self, documents: list[RawDocument]) -> None:
        excerpts = [doc.content[:500] for doc in documents]
        combined = "\n\n---\n\n".join(excerpts)
        logger.info("Generating RAPTOR summaries from %d document excerpts", len(excerpts))

        system_prompt = get_prompt("raptor_system_prompt")
        response = await self._client.chat.completions.create(
            model=self._deployment,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": combined},
            ],
            temperature=0.2,
            response_format={"type": "json_object"},
        )

        raw = response.choices[0].message.content or '{"summaries": []}'
        try:
            result = json.loads(raw)
        except json.JSONDecodeError:
            logger.error("Failed to parse RAPTOR response")
            return

        summaries = result.get("summaries", [])
        logger.info("Generated %d RAPTOR summaries", len(summaries))

        with Session(self._engine) as session:
            raptor_doc = Document(
                source_file="_raptor_summaries",
                content="RAPTOR hierarchical summaries",
                document_type="general",
            )
            session.add(raptor_doc)
            session.flush()

            for i, summary in enumerate(summaries):
                chunk = Chunk(
                    document_id=raptor_doc.id,
                    content=summary["content"],
                    content_for_llm=summary["content"],
                    chunk_index=i,
                    is_raptor_summary=True,
                )
                session.add(chunk)

            session.commit()
