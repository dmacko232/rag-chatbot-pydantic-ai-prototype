import pytest

from data_pipeline.steps.cleaner import RegexDocumentCleaner
from data_pipeline.models import RawDocument


@pytest.fixture
def cleaner():
    return RegexDocumentCleaner()


@pytest.mark.asyncio
async def test_removes_cookie_artifact(cleaner):
    docs = [
        RawDocument(
            source_file="1.txt",
            content="Hello. Sorry, we are not allowed to show you this content due to your cookie settings. World.",
        )
    ]
    result = await cleaner.clean(docs)
    assert "cookie" not in result[0].content
    assert "Hello." in result[0].content


@pytest.mark.asyncio
async def test_removes_leading_spaces(cleaner):
    docs = [RawDocument(source_file="1.txt", content="  Hello\n  World")]
    result = await cleaner.clean(docs)
    assert result[0].content == "Hello\nWorld"


@pytest.mark.asyncio
async def test_collapses_blank_lines(cleaner):
    docs = [RawDocument(source_file="1.txt", content="A\n\n\n\nB")]
    result = await cleaner.clean(docs)
    assert result[0].content == "A\n\nB"


@pytest.mark.asyncio
async def test_returns_new_objects(cleaner):
    original = RawDocument(source_file="1.txt", content="  text  ")
    result = await cleaner.clean([original])
    assert result[0] is not original
    assert result[0].content == "text"


@pytest.mark.asyncio
async def test_empty_list(cleaner):
    result = await cleaner.clean([])
    assert result == []
