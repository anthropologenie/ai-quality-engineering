"""Retrieval Metrics execution against the committed repository authorities.

Sprint P3.3.3: the thin orchestrator that produces Retrieval Evaluation records,
computes `metrics.Report` from them, independently re-derives every metric, and
reports both together with the repository integrity check. It plays the same
operational-tooling role `scripts/build_manifest.py`, `scripts/build_chunks.py`,
`scripts/build_evidence_trace.py`, `scripts/run_retrieval.py` and
`scripts/evaluate_retrieval.py` already play, and holds no metric logic of its
own — every definition, computation and comparison lives in `evaluation/`.

Strictly read-only. This module loads repository artifacts and writes none; no
metrics artifact is persisted, because none is defined by repository authority
and this sprint does not introduce artifact names (docs/MILESTONE_1A.md
Architecture Freeze) — the same decision `scripts/run_retrieval.py` recorded for
observed retrieval and `scripts/evaluate_retrieval.py` for the evaluation.

Where the dependency rule is enforced, and where it is not: the **Metrics
Engine** consumes only Retrieval Evaluation records, and its module imports
nothing that could reach an authority. This orchestrator does touch authorities
— it must, to produce the records at all, and to hash them — which Sprint
P3.3.3 permits an orchestrator solely for integrity verification and for
obtaining its input. It hands the engine records and nothing else.
"""

from evaluation.retrieval_metrics import compute
from evaluation.retrieval_metrics_validator import compare
from evaluation.retrieval_evaluation import evaluate
from scripts.evaluate_retrieval import authority_digests, load_expectations, observe
from scripts.run_retrieval import load_corpus

# Report field order. Fixed here rather than derived from the report's keys so
# the printed layout is a property of this module and cannot silently change
# when the engine gains a field — a new metric appears in the engine's report
# and is caught by the validator's `metric coverage` check, not quietly printed.
CLASSIFICATION_ROWS = (
    ("questions_evaluated", "Questions evaluated"),
    ("exact_match_count", "Exact Match count"),
    ("exact_match_rate", "Exact Match rate"),
    ("full_coverage_count", "Full Coverage count"),
    ("full_coverage_rate", "Full Coverage rate"),
    ("partial_match_count", "Partial Match count"),
    ("partial_match_rate", "Partial Match rate"),
    ("no_match_count", "No Match count"),
    ("no_match_rate", "No Match rate"),
)

RETRIEVAL_ROWS = (
    ("hit_count", "Hit count"),
    ("hit_rate", "Hit Rate"),
    ("expected_chunk_references", "Expected chunk references"),
    ("expected_chunks_unique", "Expected chunks (unique)"),
    ("retrieved_chunk_references", "Retrieved chunk references"),
    ("retrieved_chunks_unique", "Retrieved chunks (unique)"),
    ("matched_chunk_references", "Matched chunk references"),
    ("chunk_precision_at_k_macro", "Chunk Precision@K (macro)"),
    ("chunk_precision_at_k_micro", "Chunk Precision@K (micro)"),
    ("chunk_recall_at_k_macro", "Chunk Recall@K (macro)"),
    ("chunk_recall_at_k_micro", "Chunk Recall@K (micro)"),
)


def evaluation_records() -> list:
    """Produce the Retrieval Evaluation records this sprint measures.

    Sprint P3.3.2's evaluation is re-executed rather than re-derived: its own
    `load_expectations`, `observe` and `evaluate` are called directly, so the
    records measured here are the records that layer produces. Recomputing them
    would make the metrics layer capable of disagreeing with the evaluation
    layer about what was evaluated.
    """
    chunks = load_corpus()
    return evaluate(load_expectations(), observe(chunks))


def report(metrics: dict, validation: list) -> None:
    """Print the classification summary, retrieval summary, and validation report."""
    print("Classification Summary")
    for field, label in CLASSIFICATION_ROWS:
        print(f"  {label:<32} {metrics['classification'][field]}")

    print("\nRetrieval Summary")
    for field, label in RETRIEVAL_ROWS:
        print(f"  {label:<32} {metrics['retrieval'][field]}")

    print("\nPer-question metrics")
    for row in metrics["per_question"]:
        print(
            f"  {row['id']:<40} {row['classification']:<14} "
            f"precision={row['chunk_precision_at_k']:<8} "
            f"recall={row['chunk_recall_at_k']}"
        )

    print("\nValidation")
    for entry in validation:
        detail = f"  {entry['detail']}" if entry["detail"] else ""
        print(f"  {entry['check']:<36} {entry['status']}{detail}")


def main() -> None:
    """Compute, independently validate, and report Retrieval Metrics.

    Determinism is demonstrated by measurement rather than asserted: the engine
    is run twice over the same records and the two reports compared. Repository
    integrity is demonstrated the same way, by digests taken around the whole
    execution.
    """
    before = authority_digests()

    records = evaluation_records()
    metrics = compute(records)

    validation = compare(metrics, records)
    validation.append(
        {
            "check": "deterministic computation",
            "status": "PASS" if compute(records) == metrics else "FAIL",
            "detail": "",
        }
    )
    validation.append(
        {
            "check": "reproducibility",
            "status": "PASS" if compute(evaluation_records()) == metrics else "FAIL",
            "detail": "",
        }
    )
    validation.append(
        {
            "check": "repository integrity",
            "status": "PASS" if authority_digests() == before else "FAIL",
            "detail": "",
        }
    )

    report(metrics, validation)


if __name__ == "__main__":
    main()
