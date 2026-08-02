"""Retrieval Runtime execution against the committed repository corpus.

Sprint P3.3.1: the thin orchestrator that loads the committed Chunk Corpus,
executes `sample_rag/retriever.py`'s `Retriever` over the questions carried by
the Evidence Trace Dataset, and reports observed runtime characteristics. It
plays the same operational-tooling role `scripts/build_manifest.py`,
`scripts/build_chunks.py`, and `scripts/build_evidence_trace.py` already play,
and holds no retrieval logic of its own.

Strictly read-only, and deliberately so: this module loads repository artifacts
and writes none. Runtime output is materialized in memory as `RetrievalResult`
values and summarized to stdout; no observed-retrieval artifact is persisted,
because none is defined by repository authority and this sprint does not
introduce artifact names (docs/MILESTONE_1A.md Architecture Freeze).

The Evidence Trace Dataset is read here **only** as the repository's list of
questions. No expectation field is consulted, and no comparison of observed
against expected retrieval happens anywhere in this sprint — that is Sprint
P3.3.2's responsibility.
"""

from sample_rag.retriever import Retriever
from scripts.build_chunks import load_chunks, validate_chunks
from scripts.build_evidence_trace import load_evidence_trace, validate_evidence_trace

# The frozen interface takes a filter mapping; an empty one selects the
# retriever's own DEFAULT_TOP_K and exercises no SQL-filter behavior.
DEFAULT_FILTERS: dict = {}


def load_corpus() -> list:
    """Load and structurally validate the committed Chunk Corpus.

    Validation is not re-implemented here: `validate_chunks(load_chunks())` is
    the chained call docs/CHUNK_VALIDATION_PLAN.md §P7.1 prescribes, so the
    runtime consumes the corpus through the same gate every other consumer does.
    """
    return validate_chunks(load_chunks())["chunks"]


def load_questions() -> list:
    """Read the repository's questions, in Evidence Trace order.

    Returns `(entry_id, question)` pairs. Only these two values are read; the
    expectation fields on each entry are deliberately untouched.
    """
    collection = validate_evidence_trace(load_evidence_trace())
    return [(entry["id"], entry["question"]) for entry in collection["evidence_trace"]]


def execute(retriever: Retriever, questions: list, filters: dict = None) -> list:
    """Execute retrieval for every question, in order.

    Returns `(entry_id, RetrievalResult)` pairs. Each call is independent — the
    retriever carries no state between queries — so the sequence is reproducible
    and any single query can be re-run in isolation and produce the same result.
    """
    active = DEFAULT_FILTERS if filters is None else filters
    return [(entry_id, retriever.retrieve(question, active)) for entry_id, question in questions]


def summarize(results: list, corpus_size: int) -> dict:
    """Describe observed runtime behavior across an execution.

    Descriptive runtime observations only — how much was retrieved, how often,
    and from where. Nothing here scores retrieval quality: no expectation is
    read, so no statistic below can express correctness.
    """
    retrieved_counts = [len(result.chunks) for _, result in results]
    chunk_ids = [chunk["id"] for _, result in results for chunk in result.chunks]
    document_ids = {chunk["document_id"] for _, result in results for chunk in result.chunks}
    unique_chunks = set(chunk_ids)

    return {
        "questions_executed": len(results),
        "chunks_retrieved": len(chunk_ids),
        "unique_chunks_retrieved": len(unique_chunks),
        "unique_documents_retrieved": len(document_ids),
        "average_top_k": round(sum(retrieved_counts) / len(retrieved_counts), 2) if results else 0.0,
        "maximum_top_k": max(retrieved_counts) if results else 0,
        "minimum_top_k": min(retrieved_counts) if results else 0,
        "empty_results": sum(1 for count in retrieved_counts if count == 0),
        # Chunk reuse: retrievals per distinct chunk. 1.0 means every retrieval
        # surfaced a different chunk; higher means chunks recur across queries.
        "chunk_reuse": round(len(chunk_ids) / len(unique_chunks), 2) if unique_chunks else 0.0,
        "document_coverage": round(len(document_ids) / 2, 4) if document_ids else 0.0,
        "corpus_utilization": round(len(unique_chunks) / corpus_size, 4) if corpus_size else 0.0,
    }


def main() -> None:
    """Execute the Retrieval Runtime and report observed characteristics."""
    chunks = load_corpus()
    questions = load_questions()
    results = execute(Retriever(chunks), questions)

    statistics = summarize(results, len(chunks))
    for name, value in statistics.items():
        print(f"{name:<28} {value}")


if __name__ == "__main__":
    main()
