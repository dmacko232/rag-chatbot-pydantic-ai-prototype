"""Evaluation runner: sends questions through the chat use case and measures correctness + precision@10."""

import asyncio
import json
import logging
import sys
from pathlib import Path

import cohere
from sqlmodel import Session

from backend.application.tools.retrieval import (
    CohereRerankStep,
    KeywordSearchStep,
    RetrievalPipeline,
    ThresholdStep,
    VectorSearchStep,
)
from backend.application.tools.sql_query import SQLQueryTool
from backend.application.use_cases.chat import ChatUseCase
from shared.config import get_settings
from shared.db import init_db

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


def load_questions() -> list[dict]:
    path = Path(__file__).parent / "questions.json"
    return json.loads(path.read_text())


async def run_single_question(
    question: dict, chat_use_case: ChatUseCase, retrieval_pipeline: RetrievalPipeline
) -> dict:
    query = question["question"]

    retrieved_chunks = retrieval_pipeline.retrieve(query)
    retrieved_sources = [c.source_file for c in retrieved_chunks[:10]]

    response_text, citations = await chat_use_case.execute(query)

    precision_at_10 = None
    if "expected_source" in question:
        expected = question["expected_source"]
        hits = sum(1 for s in retrieved_sources if s == expected)
        precision_at_10 = hits / min(10, len(retrieved_sources)) if retrieved_sources else 0.0

    contains_expected = None
    if "expected_answer_contains" in question:
        contains_expected = question["expected_answer_contains"].lower() in response_text.lower()

    return {
        "id": question["id"],
        "type": question["type"],
        "question": query,
        "response": response_text[:500],
        "citations": citations,
        "retrieved_sources": retrieved_sources,
        "precision_at_10": precision_at_10,
        "contains_expected": contains_expected,
    }


async def main():
    settings = get_settings()
    engine = init_db(settings)

    questions = load_questions()
    logger.info("Loaded %d eval questions", len(questions))

    with Session(engine) as session:
        cohere_client = cohere.Client(api_key=settings.cohere_api_key)

        retrieval_pipeline = RetrievalPipeline(
            steps=[
                VectorSearchStep(session, cohere_client, settings.cohere_embed_model),
                KeywordSearchStep(session),
                CohereRerankStep(cohere_client, settings.cohere_rerank_model),
                ThresholdStep(settings.reranker_threshold),
            ]
        )
        sql_tool = SQLQueryTool(session)
        chat_use_case = ChatUseCase(retrieval_pipeline=retrieval_pipeline, sql_tool=sql_tool)

        results = []
        for i, q in enumerate(questions):
            logger.info("Running question %d/%d: %s", i + 1, len(questions), q["question"][:60])
            try:
                result = await run_single_question(q, chat_use_case, retrieval_pipeline)
                results.append(result)
            except Exception as e:
                logger.error("Failed on question %d: %s", q["id"], e)
                results.append({"id": q["id"], "error": str(e)})

    output_path = Path(__file__).parent / "results.json"
    output_path.write_text(json.dumps(results, indent=2))
    logger.info("Results written to %s", output_path)

    precision_scores = [r["precision_at_10"] for r in results if r.get("precision_at_10") is not None]
    contains_scores = [r["contains_expected"] for r in results if r.get("contains_expected") is not None]

    if precision_scores:
        avg_precision = sum(precision_scores) / len(precision_scores)
        logger.info("Average Precision@10 (source match): %.2f (%d questions)", avg_precision, len(precision_scores))

    if contains_scores:
        accuracy = sum(contains_scores) / len(contains_scores)
        logger.info("Contains-expected accuracy: %.2f (%d questions)", accuracy, len(contains_scores))


if __name__ == "__main__":
    asyncio.run(main())
