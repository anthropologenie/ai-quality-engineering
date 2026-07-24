"""Unit tests for sample_rag/chunker.py (Sprint P2.2.1).

Verifies observable behavior required by the frozen Chunk Contract
(docs/CHUNK_CONTRACT.md) and the approved Chunk Builder Implementation Plan
(docs/CHUNK_BUILDER_IMPLEMENTATION_PLAN.md), not internal implementation
details. `_Document` below is a local test fixture only — not a production
Document Data Model (out of scope per the Implementation Plan).
"""

from dataclasses import dataclass

import pytest

from sample_rag.chunker import Chunk, ChunkConstructionError, Chunker


@dataclass
class _Document:
    id: str
    text: str


def test_empty_document_produces_no_chunks():
    chunks = Chunker().chunk(_Document(id="doc1", text=""))
    assert chunks == []


def test_single_chunk_for_unstructured_short_text():
    chunks = Chunker().chunk(_Document(id="doc1", text="A single short paragraph."))
    assert len(chunks) == 1
    assert chunks[0].text == "A single short paragraph."
    assert chunks[0].chunk_index == 0
    assert chunks[0].document_id == "doc1"


def test_multiple_chunks_split_on_structural_boundaries():
    text = "Responsibilities\nDid the work.\n\nRequirements\nNeeded the skill."
    chunks = Chunker().chunk(_Document(id="doc1", text=text))
    assert len(chunks) == 2
    assert chunks[0].text == "Responsibilities\nDid the work."
    assert chunks[1].text == "Requirements\nNeeded the skill."


def test_chunk_index_is_zero_based_contiguous_and_matches_reading_order():
    text = "First section.\n\nSecond section.\n\nThird section."
    chunks = Chunker().chunk(_Document(id="doc1", text=text))
    assert [c.chunk_index for c in chunks] == list(range(len(chunks)))
    starts = [c.character_start for c in chunks]
    assert starts == sorted(starts)


def test_offsets_satisfy_the_contract_slice_invariant():
    text = "Alpha section here.\n\nBeta section here.\n\nGamma section here."
    doc = _Document(id="doc1", text=text)
    chunks = Chunker().chunk(doc)
    for chunk in chunks:
        assert chunk.text == text[chunk.character_start : chunk.character_end]
        assert len(chunk.text) == chunk.character_end - chunk.character_start
        assert chunk.character_end > chunk.character_start


def test_chunks_do_not_overlap_and_index_order_matches_offset_order():
    text = "One.\n\nTwo.\n\nThree.\n\nFour."
    chunks = Chunker().chunk(_Document(id="doc1", text=text))
    for i in range(len(chunks) - 1):
        assert chunks[i].character_end <= chunks[i + 1].character_start
        assert chunks[i].chunk_index < chunks[i + 1].chunk_index


def test_fallback_splitting_applies_only_to_oversized_structural_spans():
    oversized_word = "x" * 50
    oversized_span = " ".join(oversized_word for _ in range(30))  # > 1000 chars, no natural break
    text = f"Short section.\n\n{oversized_span}"
    chunks = Chunker().chunk(_Document(id="doc1", text=text))

    assert chunks[0].text == "Short section."
    assert len(chunks) > 2, "oversized span should have been split by the fallback path"
    for chunk in chunks[1:]:
        assert len(chunk.text) <= 1000


def test_default_path_does_not_invoke_fallback_for_normal_sections():
    text = "Responsibilities\nOwned the pipeline end to end.\n\nRequirements\nFive years experience."
    chunks = Chunker().chunk(_Document(id="doc1", text=text))
    assert len(chunks) == 2
    assert all(len(c.text) <= 1000 for c in chunks)


def test_chunk_ids_are_deterministic_across_repeated_construction():
    text = "Section A.\n\nSection B."
    doc = _Document(id="doc1", text=text)
    first_run = Chunker().chunk(doc)
    second_run = Chunker().chunk(doc)
    assert first_run == second_run
    assert [c.id for c in first_run] == [c.id for c in second_run]


def test_chunk_ids_are_unique_within_a_document():
    text = "Section A.\n\nSection B.\n\nSection C."
    chunks = Chunker().chunk(_Document(id="doc1", text=text))
    ids = [c.id for c in chunks]
    assert len(ids) == len(set(ids))


def test_chunk_ids_differ_across_documents_for_identical_text():
    text = "Repeated boilerplate heading."
    chunks_a = Chunker().chunk(_Document(id="doc_a", text=text))
    chunks_b = Chunker().chunk(_Document(id="doc_b", text=text))
    assert chunks_a[0].id != chunks_b[0].id


def test_full_output_is_deterministic_for_identical_input():
    text = "First.\n\nSecond.\n\nThird."
    doc = _Document(id="doc1", text=text)
    assert Chunker().chunk(doc) == Chunker().chunk(doc)


@pytest.mark.parametrize(
    "bad_doc",
    [
        None,
        object(),
        _Document(id=123, text="valid text"),
        _Document(id="doc1", text=None),
    ],
)
def test_invalid_input_raises_chunk_construction_error(bad_doc):
    with pytest.raises(ChunkConstructionError):
        Chunker().chunk(bad_doc)


def test_chunk_dataclass_exposes_exactly_the_contract_fields():
    expected_fields = {
        "id",
        "document_id",
        "text",
        "chunk_index",
        "character_start",
        "character_end",
    }
    assert set(Chunk.__dataclass_fields__) == expected_fields
