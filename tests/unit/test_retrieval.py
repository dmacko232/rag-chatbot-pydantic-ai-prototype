from unittest.mock import MagicMock

from backend.application.tools.retrieval import HybridSearch, RetrievedChunk, ScoreFilter


def _make_chunk(score: float, chunk_id: int = 1) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=chunk_id, content="test", content_for_llm="test", score=score, source_file="0.txt", document_id=1
    )


# --- ScoreFilter tests ---


def test_score_filter_removes_below_threshold():
    sf = ScoreFilter(threshold=0.3)
    candidates = [_make_chunk(0.1), _make_chunk(0.5), _make_chunk(0.3), _make_chunk(0.29)]
    result = sf.filter(candidates)
    assert len(result) == 2
    assert all(c.score >= 0.3 for c in result)


def test_score_filter_empty_list():
    sf = ScoreFilter(threshold=0.3)
    assert sf.filter([]) == []


def test_score_filter_keeps_all_above():
    sf = ScoreFilter(threshold=0.1)
    candidates = [_make_chunk(0.5), _make_chunk(0.8), _make_chunk(0.3)]
    result = sf.filter(candidates)
    assert len(result) == 3


def test_score_filter_removes_all_below():
    sf = ScoreFilter(threshold=0.9)
    candidates = [_make_chunk(0.1), _make_chunk(0.5), _make_chunk(0.3)]
    result = sf.filter(candidates)
    assert len(result) == 0


# --- RRF tests ---


def test_rrf_equal_alpha_ranks_both_sources():
    hs = HybridSearch.__new__(HybridSearch)
    hs._rrf_k = 60
    hs._rrf_alpha = 0.5
    hs._rrf_top_n = 10

    vec = [_make_chunk(0.9, chunk_id=1), _make_chunk(0.8, chunk_id=2)]
    bm25 = [_make_chunk(0.5, chunk_id=2), _make_chunk(0.4, chunk_id=3)]

    result = hs._reciprocal_rank_fusion(vec, bm25)

    assert len(result) == 3
    ids = [c.chunk_id for c in result]
    assert ids[0] == 2, "chunk 2 appears in both lists so should rank first"
    assert set(ids) == {1, 2, 3}


def test_rrf_vector_only_alpha_1():
    hs = HybridSearch.__new__(HybridSearch)
    hs._rrf_k = 60
    hs._rrf_alpha = 1.0
    hs._rrf_top_n = 10

    vec = [_make_chunk(0.9, chunk_id=1), _make_chunk(0.8, chunk_id=2)]
    bm25 = [_make_chunk(0.5, chunk_id=3)]

    result = hs._reciprocal_rank_fusion(vec, bm25)

    ids = [c.chunk_id for c in result]
    assert ids[0] == 1, "alpha=1.0 means vector rank dominates"
    assert ids[1] == 2


def test_rrf_bm25_only_alpha_0():
    hs = HybridSearch.__new__(HybridSearch)
    hs._rrf_k = 60
    hs._rrf_alpha = 0.0
    hs._rrf_top_n = 10

    vec = [_make_chunk(0.9, chunk_id=1)]
    bm25 = [_make_chunk(0.5, chunk_id=2), _make_chunk(0.4, chunk_id=3)]

    result = hs._reciprocal_rank_fusion(vec, bm25)

    ids = [c.chunk_id for c in result]
    assert ids[0] == 2, "alpha=0.0 means BM25 rank dominates"
    assert ids[1] == 3


def test_rrf_respects_top_n():
    hs = HybridSearch.__new__(HybridSearch)
    hs._rrf_k = 60
    hs._rrf_alpha = 0.5
    hs._rrf_top_n = 2

    vec = [_make_chunk(0.9, chunk_id=i) for i in range(5)]
    bm25 = [_make_chunk(0.5, chunk_id=i) for i in range(5, 10)]

    result = hs._reciprocal_rank_fusion(vec, bm25)
    assert len(result) == 2


def test_rrf_empty_inputs():
    hs = HybridSearch.__new__(HybridSearch)
    hs._rrf_k = 60
    hs._rrf_alpha = 0.5
    hs._rrf_top_n = 10

    assert hs._reciprocal_rank_fusion([], []) == []
    assert len(hs._reciprocal_rank_fusion([_make_chunk(0.9, chunk_id=1)], [])) == 1
    assert len(hs._reciprocal_rank_fusion([], [_make_chunk(0.5, chunk_id=1)])) == 1
