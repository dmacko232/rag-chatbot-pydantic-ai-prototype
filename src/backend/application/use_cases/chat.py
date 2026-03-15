import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass

from openai import AsyncAzureOpenAI
from pydantic_ai import Agent, RunContext
from pydantic_ai.messages import ModelRequest, ModelResponse, TextPart, UserPromptPart
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from backend.application.dto import HistoryEntry
from backend.application.tools.retrieval import MetadataFilter, RetrievalService
from backend.application.tools.sql_query import SQLQueryTool
from shared.config import get_settings
from shared.prompts import get_prompt

logger = logging.getLogger(__name__)


@dataclass
class ChatDeps:
    retrieval_service: RetrievalService
    sql_tool: SQLQueryTool


def _build_model() -> OpenAIChatModel:
    settings = get_settings()
    client = AsyncAzureOpenAI(
        api_key=settings.azure_openai_api_key,
        azure_endpoint=settings.azure_openai_endpoint,
        api_version=settings.azure_openai_api_version,
    )
    return OpenAIChatModel(
        settings.azure_openai_deployment,
        provider=OpenAIProvider(openai_client=client),
    )


chat_agent = Agent(
    _build_model(),
    system_prompt=get_prompt("chat_system_prompt"),
    deps_type=ChatDeps,
    retries=1,
)


@chat_agent.tool
async def retrieve_press_releases(
    ctx: RunContext[ChatDeps],
    query: str,
    year: int | None = None,
    business_segment: str | None = None,
    document_type: str | None = None,
) -> str:
    """Search the press release corpus for relevant content. Use for factual, comparative, or detail questions.

    Args:
        query: The search query.
        year: Optional filter by publication year (e.g. 2024).
        business_segment: Optional filter: t_systems, telekom_deutschland, t_mobile_us, deutsche_telekom_group.
        document_type: Optional filter: financial_report, product_launch, partnership, award, general.
    """
    metadata_filter = MetadataFilter(
        year=year,
        business_segment=business_segment,
        document_type=document_type,
    )
    chunks = ctx.deps.retrieval_service.retrieve(query, metadata_filter=metadata_filter)
    if not chunks:
        return "No relevant press releases found for this query."

    results: list[str] = []
    for chunk in chunks:
        meta_parts = [f"Source: {chunk.source_file}", f"Score: {chunk.score:.2f}"]
        if chunk.year:
            meta_parts.append(f"Year: {chunk.year}")
        if chunk.business_segment:
            meta_parts.append(f"Segment: {chunk.business_segment}")
        results.append(f"[{' | '.join(meta_parts)}]\n{chunk.content_for_llm}")
    return "\n\n---\n\n".join(results)


@chat_agent.tool
async def query_documents_sql(ctx: RunContext[ChatDeps], sql_query: str) -> str:
    """Run a read-only SQL SELECT query against the Document table. Columns: id, source_file, content, year, business_segment, document_type. Use for counting, filtering, or aggregation questions."""
    return ctx.deps.sql_tool.execute(sql_query)


class ChatUseCase:
    def __init__(self, retrieval_service: RetrievalService, sql_tool: SQLQueryTool) -> None:
        self._deps = ChatDeps(retrieval_service=retrieval_service, sql_tool=sql_tool)

    async def execute_stream(
        self, message: str, history: list[HistoryEntry] | None = None
    ) -> AsyncIterator[str]:
        message_history = []
        for entry in history or []:
            if entry.role == "user":
                message_history.append(ModelRequest(parts=[UserPromptPart(content=entry.content)]))
            else:
                message_history.append(ModelResponse(parts=[TextPart(content=entry.content)]))

        async with chat_agent.run_stream(message, deps=self._deps, message_history=message_history) as result:
            async for chunk in result.stream_text(delta=True):
                yield chunk
