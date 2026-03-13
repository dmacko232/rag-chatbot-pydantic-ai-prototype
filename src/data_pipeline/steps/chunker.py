import json
import logging

from openai import AsyncAzureOpenAI

from data_pipeline.pipeline import PipelineContext, Step
from shared.config import Settings

logger = logging.getLogger(__name__)

CHUNKING_SYSTEM_PROMPT = """You are a document chunking assistant. You receive a press release that was parsed from HTML (formatting lost). Your job is to split it into meaningful chunks suitable for semantic search, and extract document-level metadata.

Instructions:
- Each chunk should be a coherent, self-contained passage of roughly 200-400 words.
- Split on semantic boundaries (topic shifts, new sections, different subjects).
- For short documents, 1-3 chunks is fine. Don't force splits where none exist.
- For each chunk, also provide a larger "context" version that includes surrounding text for LLM grounding.
- Extract document-level metadata: publication year, business segment, and document type.

Respond with valid JSON matching this schema:
{
  "year": <int or null>,
  "business_segment": "<t_systems|telekom_deutschland|t_mobile_us|deutsche_telekom_group>",
  "document_type": "<financial_report|product_launch|partnership|award|general>",
  "chunks": [
    {
      "content": "<chunk text for retrieval, 200-400 words>",
      "content_for_llm": "<larger context including surrounding text>"
    }
  ]
}"""


class LLMChunkerStep(Step):
    """Use Azure OpenAI to split documents into semantic chunks and extract metadata."""

    def __init__(self, settings: Settings) -> None:
        self._client = AsyncAzureOpenAI(
            api_key=settings.azure_openai_api_key,
            azure_endpoint=settings.azure_openai_endpoint,
            api_version=settings.azure_openai_api_version,
        )
        self._deployment = settings.azure_openai_deployment

    async def run(self, ctx: PipelineContext) -> PipelineContext:
        for i, doc in enumerate(ctx.raw_documents):
            logger.info("Chunking document %d/%d: %s", i + 1, len(ctx.raw_documents), doc["source_file"])
            result = await self._chunk_document(doc["content"])

            doc["year"] = result.get("year")
            doc["business_segment"] = result.get("business_segment", "deutsche_telekom_group")
            doc["document_type"] = result.get("document_type", "general")
            doc["chunks"] = result.get("chunks", [])

        return ctx

    async def _chunk_document(self, content: str) -> dict:
        response = await self._client.chat.completions.create(
            model=self._deployment,
            messages=[
                {"role": "system", "content": CHUNKING_SYSTEM_PROMPT},
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
