import pytest

from data_pipeline.steps.loader import FileDocumentLoader


@pytest.fixture
def data_dir(tmp_path):
    (tmp_path / "1.txt").write_text("Document one content", encoding="utf-8")
    (tmp_path / "2.txt").write_text("Document two content", encoding="utf-8")
    (tmp_path / "3.txt").write_text("Document three content", encoding="utf-8")
    return tmp_path


@pytest.mark.asyncio
async def test_loads_all_txt_files(data_dir):
    loader = FileDocumentLoader(data_dir=str(data_dir))
    docs = await loader.load()
    assert len(docs) == 3


@pytest.mark.asyncio
async def test_loads_in_numeric_order(data_dir):
    loader = FileDocumentLoader(data_dir=str(data_dir))
    docs = await loader.load()
    assert [d.source_file for d in docs] == ["1.txt", "2.txt", "3.txt"]


@pytest.mark.asyncio
async def test_preserves_content(data_dir):
    loader = FileDocumentLoader(data_dir=str(data_dir))
    docs = await loader.load()
    assert docs[0].content == "Document one content"
    assert docs[1].content == "Document two content"


@pytest.mark.asyncio
async def test_empty_directory(tmp_path):
    loader = FileDocumentLoader(data_dir=str(tmp_path))
    docs = await loader.load()
    assert docs == []


@pytest.mark.asyncio
async def test_ignores_non_txt_files(tmp_path):
    (tmp_path / "1.txt").write_text("valid", encoding="utf-8")
    (tmp_path / "notes.md").write_text("should be ignored", encoding="utf-8")
    (tmp_path / "data.json").write_text("{}", encoding="utf-8")

    loader = FileDocumentLoader(data_dir=str(tmp_path))
    docs = await loader.load()
    assert len(docs) == 1
    assert docs[0].source_file == "1.txt"
