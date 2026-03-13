import json
import logging
from dataclasses import dataclass

from pydantic_ai import Agent, RunContext

from backend.application.tools.retrieval import RetrievalPipeline, RetrievedChunk
from backend.application.tools.sql_query import SQLQueryTool

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a helpful assistant specializing in Deutsche Telekom press releases. You answer questions accurately based on the information retrieved from the press release corpus.

Rules:
1. Always cite your sources using inline citations after each statement, formatted as [Source: filename]. When information comes from a specific press release, reference it.
2. Format your responses in clean, well-structured markdown. Use headers, bullet points, and bold text where appropriate.
3. If the retrieved information doesn't contain the answer, say so clearly. Do not hallucinate.
4. For aggregation or counting questions, use the SQL tool to query the Document table.
5. For content questions, use the retrieval tool to find relevant press release chunks.
6. Be concise but thorough. Prefer facts over speculation."""


@dataclass
class ChatDeps:
    retrieval_pipeline: RetrievalPipeline
    sql_tool: SQLQueryTool


chat_agent = Agent(
    "openai:gpt-4o",
    system_prompt=SYSTEM_PROMPT,
    deps_type=ChatDeps,
    retries=1,
)


@chat_agent.tool
async def retrieve_press_releases(ctx: RunContext[ChatDeps], query: str) -> str:
    """Search the press release corpus for relevant content. Use for factual, comparative, or detail questions."""
    chunks = ctx.deps.retrieval_pipeline.retrieve(query)
    if not chunks:
        return "No relevant press releases found for this query."

    results: list[str] = []
    for chunk in chunks:
        results.append(f"[Source: {chunk.source_file} | Score: {chunk.score:.2f}]\n{chunk.content_for_llm}")
    return "\n\n---\n\n".join(results)


@chat_agent.tool
async def query_documents_sql(ctx: RunContext[ChatDeps], sql_query: str) -> str:
    """Run a read-only SQL SELECT query against the Document table. Columns: id, source_file, content, year, business_segment, document_type. Use for counting, filtering, or aggregation questions."""
    return ctx.deps.sql_tool.execute(sql_query)


class ChatUseCase:
    def __init__(self, retrieval_pipeline: RetrievalPipeline, sql_tool: SQLQueryTool) -> None:
        self._deps = ChatDeps(retrieval_pipeline=retrieval_pipeline, sql_tool=sql_tool)

    async def execute(self, user_message: str, history: list[dict] | None = None) -> tuple[str, list[dict]]:
        """Returns (assistant_response, citations)."""
        message_history = []
        if history:
            for msg in history:
                message_history.append({"role": msg["role"], "content": msg["content"]})

        result = await chat_agent.run(user_message, deps=self._deps, message_history=message_history)

        citations = self._extract_citations(result.data)
        return result.data, citations

    async def execute_stream(self, user_message: str, history: list[dict] | None = None):
        """Yields streamed text chunks."""
        message_history = []
        if history:
            for msg in history:
                message_history.append({"role": msg["role"], "content": msg["content"]})

        async with chat_agent.run_stream(user_message, deps=self._deps, message_history=message_history) as result:
            async for chunk in result.stream_text(delta=True):
                yield chunk

    @staticmethod
    def _extract_citations(text: str) -> list[dict]:
        import re

        pattern = r"\[Source:\s*([^\]|]+?)(?:\s*\|[^\]]*?)?\]"
        matches = re.findall(pattern, text)
        seen = set()
        citations = []
        for match in matches:
            filename = match.strip()
            if filename not in seen:
                seen.add(filename)
                citations.append({"source_file": filename})
        return citations
