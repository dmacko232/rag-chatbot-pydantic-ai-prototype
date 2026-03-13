import json
import logging

from openai import AsyncAzureOpenAI
from sqlmodel import Session, select

from data_pipeline.pipeline import PipelineContext, Step
from shared.config import Settings
from shared.db import create_db_engine
from shared.models import Chunk, Document

logger = logging.getLogger(__name__)

RAPTOR_SYSTEM_PROMPT = """You are a summarisation assistant. Given a collection of press release excerpts from Deutsche Telekom, produce a set of high-level summary passages that capture the main themes and facts.

These summaries will be used to answer global/abstract questions like:
- "What is Deutsche Telekom's overall strategy?"
- "What sustainability initiatives does Telekom pursue?"
- "How has Telekom's financial performance trended?"

Generate 5-10 summary passages, each 150-300 words, covering distinct themes.

Respond with valid JSON:
{
  "summaries": [
    {"content": "<summary passage>"}
  ]
}"""

RAPTOR_BATCH_SIZE = 20


class RaptorStep(Step):
    """Generate RAPTOR hierarchical summaries for global/abstract questions."""

    def __init__(self, settings: Settings) -> None:
        self._client = AsyncAzureOpenAI(
            api_key=settings.azure_openai_api_key,
            azure_endpoint=settings.azure_openai_endpoint,
            api_version=settings.azure_openai_api_version,
        )
        self._deployment = settings.azure_openai_deployment
        self._engine = create_db_engine(settings)

    async def run(self, ctx: PipelineContext) -> PipelineContext:
        all_excerpts = [doc["content"][:500] for doc in ctx.raw_documents]

        combined = "\n\n---\n\n".join(all_excerpts)
        logger.info("Generating RAPTOR summaries from %d document excerpts", len(all_excerpts))

        response = await self._client.chat.completions.create(
            model=self._deployment,
            messages=[
                {"role": "system", "content": RAPTOR_SYSTEM_PROMPT},
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
            return ctx

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

        return ctx
