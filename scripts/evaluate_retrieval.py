"""Retrieval Evaluation execution against the committed repository authorities.

Sprint P3.3.2: the thin orchestrator that loads the Chunk Corpus and the
Evidence Trace Dataset, executes the Retrieval Runtime over the dataset's
questions, and evaluates observed retrieval against expected retrieval using
`evaluation/retrieval_evaluation.py`. It plays the same operational-tooling role
`scripts/build_manifest.py`, `scripts/build_chunks.py`,
`scripts/build_evidence_trace.py` and `scripts/run_retrieval.py` already play,
and holds no evaluation logic of its own — every comparison, classification and
validation rule lives in the engine.

Strictly read-only, and deliberately so: this module loads repository artifacts
and writes none. The evaluation is materialized in memory and summarized to
stdout; no evaluation artifact is persisted, because none is defined by
repository authority and this sprint does not introduce artifact names
(docs/MILESTONE_1A.md Architecture Freeze) — the same decision
`scripts/run_retrieval.py` recorded for observed retrieval at Sprint P3.3.1.

Retrieval execution is not reimplemented here: `scripts/run_retrieval.py`'s own
`load_corpus`, `load_questions` and `execute` are called directly, so the
observed retrieval being evaluated is byte-for-byte the retrieval that sprint
produces. Re-deriving it would make the two layers capable of disagreeing about
what the runtime did.
"""

import hashlib

from pathlib import Path

from evaluation.retrieval_evaluation import evaluate, run_validation_suite, summarize
from sample_rag.retriever import Retriever
from scripts.build_evidence_trace import load_evidence_trace, validate_evidence_trace
from scripts.run_retrieval import execute, load_corpus, load_questions

REPOSITORY_ROOT = Path(__file__).resolve().parent.parent

# The frozen authorities this sprint consumes, in the dependency order
# docs/MILESTONE_1A.md establishes. Hashed before and after evaluation to
# demonstrate the Repository Invariant — evaluation is observational, so every
# one of these must be byte-identical across the run.
AUTHORITY_PATHS = (
    REPOSITORY_ROOT / "sample_rag" / "knowledge_manifest.json",
    REPOSITORY_ROOT / "sample_rag" / "chunks.json",
    REPOSITORY_ROOT / "datasets" / "golden" / "resume_facts.json",
    REPOSITORY_ROOT / "datasets" / "golden" / "resume_qa_pairs.json",
    REPOSITORY_ROOT / "datasets" / "golden" / "resume_evidence_trace.json",
)


def authority_digests() -> dict:
    """SHA-256 of every consumed repository authority, keyed by repository-relative path.

    `hashlib` is the repository's established integrity mechanism
    (docs/MILESTONE_1A.md build item 1, freshness validation) and the same digest
    the Knowledge Manifest's own `documents[].hash` carries, so the invariant is
    demonstrated with the mechanism the repository already trusts rather than a
    new one.
    """
    return {
        str(path.relative_to(REPOSITORY_ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in AUTHORITY_PATHS
    }


def load_expectations() -> list:
    """Read expected retrieval from the Retrieval Expectation Authority.

    Returns `(entry_id, expected_chunk_ids)` in Evidence Trace order. The dataset
    passes through `validate_evidence_trace` first — the same gate every other
    consumer uses (docs/CHUNK_VALIDATION_PLAN.md §P7.1's chained-call convention)
    — so no expectation is read out of an unvalidated artifact.

    `expected_chunk` is copied rather than referenced so nothing downstream can
    mutate the loaded dataset in place. Only this field and the entry id are
    read; `expected_answer`, `expected_metrics` and the remaining expectation
    fields belong to layers this sprint does not implement.
    """
    collection = validate_evidence_trace(load_evidence_trace())
    return [
        (entry["id"], list(entry["expected_chunk"]))
        for entry in collection["evidence_trace"]
    ]


def observe(chunks: list) -> dict:
    """Execute the Retrieval Runtime and collect observed chunk ids per question.

    Returns `entry_id -> retrieved chunk ids`, in retrieval-ranking order as the
    runtime produced them. The engine compares by set membership and sorts what
    it records, so ranking order is carried here only because discarding it would
    be this layer editing the runtime's output; nothing in this sprint reads it.
    """
    results = execute(Retriever(chunks), load_questions())
    return {
        entry_id: list(result.diagnostics["retrieved_chunk_ids"])
        for entry_id, result in results
    }


def index_chunk_documents(chunks: list) -> dict:
    """Map every corpus chunk id to its parent document id.

    Serves both the aggregate document distribution and the referential-integrity
    check, whose chunk-id universe is this mapping's key set — so the corpus is
    read once and the two consumers cannot disagree about what it contains.
    """
    return {chunk["id"]: chunk["document_id"] for chunk in chunks}


def report(evaluations: list, summary: dict, validation: list, digests: dict) -> None:
    """Print the evaluation, its aggregate summary, and the validation report."""
    print("Per-question evaluation")
    for evaluation in evaluations:
        print(
            f"  {evaluation['id']:<40} {evaluation['classification']:<14} "
            f"expected={evaluation['expected_count']} "
            f"observed={evaluation['observed_count']} "
            f"matched={evaluation['matched_count']}"
        )

    print("\nAggregate evaluation summary")
    for name, value in summary.items():
        print(f"  {name:<32} {value}")

    print("\nValidation")
    for entry in validation:
        detail = f"  {entry['detail']}" if entry["detail"] else ""
        print(f"  {entry['check']:<32} {entry['status']}{detail}")

    print("\nRepository authority digests")
    for path, digest in digests.items():
        print(f"  {path:<44} {digest}")


def main() -> None:
    """Evaluate observed retrieval against expected retrieval, and validate the evaluation.

    Authority digests are taken before and after the evaluation and compared: the
    Repository Invariant is demonstrated by measurement, not asserted by the
    absence of write calls.
    """
    before = authority_digests()

    chunks = load_corpus()
    chunk_documents = index_chunk_documents(chunks)
    expectations = load_expectations()
    observations = observe(chunks)

    evaluations = evaluate(expectations, observations, chunk_documents)
    summary = summarize(evaluations, chunk_documents)
    validation = run_validation_suite(
        evaluations, expectations, observations, chunk_documents, summary
    )

    after = authority_digests()
    status = "PASS" if after == before else "FAIL"
    validation.append({"check": "repository integrity", "status": status, "detail": ""})

    report(evaluations, summary, validation, after)


if __name__ == "__main__":
    main()
