from backend.application.tools.retrieval import RetrievedChunk, ThresholdStep


def _make_chunk(score: float) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=1, content="test", content_for_llm="test", score=score, source_file="0.txt", document_id=1
    )


def test_threshold_filters_below():
    step = ThresholdStep(threshold=0.3)
    candidates = [_make_chunk(0.1), _make_chunk(0.5), _make_chunk(0.3), _make_chunk(0.29)]
    result = step.execute("query", candidates)
    assert len(result) == 2
    assert all(c.score >= 0.3 for c in result)


def test_threshold_empty_list():
    step = ThresholdStep(threshold=0.3)
    assert step.execute("query", []) == []
