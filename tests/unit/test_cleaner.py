import pytest

from data_pipeline.pipeline import PipelineContext
from data_pipeline.steps.cleaner import CleanerStep


@pytest.mark.asyncio
async def test_removes_cookie_artifact():
    ctx = PipelineContext(
        raw_documents=[
            {"content": "Hello. Sorry, we are not allowed to show you this content due to your cookie settings. World."}
        ]
    )
    result = await CleanerStep().run(ctx)
    assert "cookie" not in result.raw_documents[0]["content"]
    assert "Hello." in result.raw_documents[0]["content"]


@pytest.mark.asyncio
async def test_removes_leading_spaces():
    ctx = PipelineContext(raw_documents=[{"content": "  Hello\n  World"}])
    result = await CleanerStep().run(ctx)
    assert result.raw_documents[0]["content"] == "Hello\nWorld"


@pytest.mark.asyncio
async def test_collapses_blank_lines():
    ctx = PipelineContext(raw_documents=[{"content": "A\n\n\n\nB"}])
    result = await CleanerStep().run(ctx)
    assert result.raw_documents[0]["content"] == "A\n\nB"
