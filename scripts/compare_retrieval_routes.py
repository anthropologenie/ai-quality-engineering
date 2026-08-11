"""Retrieval-quality comparison across the semantic, lexical and fused routes.

Sprint M2.04, and the sprint's answer to its **second** question. The first —
*does the RRF implementation work correctly?* — is answered by
`tests/test_rrf_fusion.py`. This module answers *does two-route RRF actually
improve the retrieval-quality problem recorded as **M2.03-F-1**?*, and a YES to
the first implies nothing about the second.

**M2.03-F-1**, `docs/ENGINEERING_TRACEABILITY_REGISTER.md`: BM25's length
normalization interacts badly with the corpus's header-sized chunks, and
retrieval quality against the 22 committed expectations fell when the lexical
scorer became BM25. Repository Owner sprint **RO-11** made **M2-04** *"the next
architectural checkpoint for this finding"* while stating equally explicitly
that M2-04 is **NOT a guaranteed remedy**, and that whether fusion improves,
partially recovers or fails to recover the regression *"must be established by
M2-04's own implementation and retrieval-quality evidence"*.

This module is therefore built to be **neutral**. It answers whatever the
measurement says.

What is held fixed, and why that is the whole point
-----------------------------------------------------
* **The benchmark** — the same 22-question Evidence Trace Dataset that exposed
  F-1. Not a new one, not a subset, not a reweighting. No question is removed,
  reworded or excused, and the expectations are read through
  `scripts/evaluate_retrieval.py`'s own `load_expectations`.
* **The metrics** — `evaluation/retrieval_evaluation.py` and
  `evaluation/retrieval_metrics.py`, **both unedited by this sprint**. That is
  the property the metrics engine's own docstring predicted: *"a future BM25,
  vector, or hybrid retriever [can] be measured without touching this file — a
  new retriever changes what the records *say*, not what a record *is*."* This
  sprint is that hybrid retriever, and the claim held a second time.
* **Retrieval depth** — `ROUTE_TOP_K` for every route, so K in Chunk
  Precision@K means the same thing in every column.
* **Both routes** — consumed exactly as they stand. No BM25 parameter, no
  tokenization, no chunking, no embedding, no FAISS configuration and no query
  text is altered to improve a number, and `RRF_K` was fixed from the
  literature before any of this was executed.

The historical baseline is *historical*
-----------------------------------------
Column A is the **distinct-term-overlap** scorer that preceded BM25. It is
**not executed**: Sprint M2.03 replaced it, and `docs/M2.03_…` §13 records the
replacement as the capability **M2-03** itself. Resurrecting, reimplementing or
restoring it to produce a fourth live column would be reintroducing a
superseded implementation to make a comparison look complete, so the recorded
measurements are carried instead, labelled as observations rather than as a
route. Every other column is measured live, here, now.

    Evidence Trace expectations  ─┐
                                  ├─> evaluation.evaluate ─> evaluation.compute
    route's ranked chunk ids     ─┘        (unedited)             (unedited)
"""

from evaluation.retrieval_evaluation import evaluate
from evaluation.retrieval_metrics import compute
from scripts.evaluate_retrieval import (
    authority_digests,
    index_chunk_documents,
    load_expectations,
)
from scripts.run_hybrid_retrieval import (
    FUSED_ROUTE,
    LEXICAL_ROUTE,
    ROUTE_TOP_K,
    SEMANTIC_ROUTE,
    canonical_order,
    execute,
    load_documents,
)
from sample_rag.fusion import RRF_K
from sample_rag.retriever import Retriever
from sample_rag.vector_runtime import VectorIndexRuntime
from scripts.run_retrieval import load_canonical_documents, load_corpus, load_questions

# Sprint M2.03's recorded measurements for the distinct-term-overlap scorer,
# reproduced verbatim from `docs/M2.03_Real_BM25_Lexical_Retrieval_Report.md`
# §11 and `docs/ENGINEERING_TRACEABILITY_REGISTER.md` M2.03-F-1.
#
# **Historical observations, not targets, and not a live route.** They are the
# `43df8f3`-era record of a scorer this repository no longer contains. They are
# carried so the regression F-1 names has a stated magnitude in the same table
# as the routes that might or might not recover it — and for no other purpose.
# Nothing in this sprint is tuned toward them, and reaching them is not a
# success criterion.
HISTORICAL_OVERLAP_BASELINE = {
    "hit_rate": 0.7273,
    "chunk_precision_at_k_micro": 0.1481,
    "chunk_recall_at_k_micro": 0.4324,
    "full_coverage_count": 11,
    "partial_match_count": 5,
    "no_match_count": 6,
}

HISTORICAL_LABEL = "overlap (historical)"

# The comparison's rows. Chunk Recall@K is included because the repository
# already defines and implements it — `evaluation/retrieval_metrics.py`
# `chunk_recall_at_k`, with a denominator `validate_records` guarantees is
# non-zero — so it is an existing metric being read, not one introduced here.
# Context Precision and Context Recall are **M2-10**, reserved for Ragas, and
# appear nowhere.
COMPARISON_ROWS = (
    ("retrieval", "hit_rate", "Hit Rate"),
    ("retrieval", "chunk_precision_at_k_micro", "Chunk Precision@K (micro)"),
    ("retrieval", "chunk_precision_at_k_macro", "Chunk Precision@K (macro)"),
    ("retrieval", "chunk_recall_at_k_micro", "Chunk Recall@K (micro)"),
    ("retrieval", "chunk_recall_at_k_macro", "Chunk Recall@K (macro)"),
    ("retrieval", "hit_count", "Hit count"),
    ("retrieval", "matched_chunk_references", "Matched chunk references"),
    ("retrieval", "retrieved_chunks_unique", "Retrieved chunks (unique)"),
    ("classification", "full_coverage_count", "Full Coverage count"),
    ("classification", "partial_match_count", "Partial Match count"),
    ("classification", "no_match_count", "No Match count"),
    ("classification", "exact_match_count", "Exact Match count"),
)

ROUTES = (SEMANTIC_ROUTE, LEXICAL_ROUTE, FUSED_ROUTE)


def observe_routes() -> tuple:
    """Execute all three routes over the benchmark's questions.

    Returns `(chunks, executed)`. Retrieval is not re-derived per route:
    `scripts/run_hybrid_retrieval.py`'s `execute` produces all three id lists
    from one pass, so the fused column is measured against the very semantic
    and lexical columns it was fused from, rather than against a second
    execution that could differ.
    """
    chunks = load_corpus()
    canonical_ids = load_canonical_documents()

    retriever = Retriever(chunks, canonical_ids)
    runtime = VectorIndexRuntime(chunks, load_documents())

    executed = execute(
        retriever,
        runtime,
        load_questions(),
        canonical_order(chunks, canonical_ids),
    )

    return chunks, executed


def metrics_for(route: str, executed: list, expectations: list, chunk_documents: dict) -> dict:
    """Measure one route through the repository's existing engines.

    `evaluate` then `compute`, both handed this route's observations and
    nothing else — the same two calls `scripts/report_retrieval_metrics.py`
    makes for the lexical route. The engines cannot tell which route produced
    the ids, which is exactly why the three columns are comparable.
    """
    observations = {entry_id: routes[route] for entry_id, routes in executed}

    return compute(evaluate(expectations, observations, chunk_documents))


def per_question_rows(executed: list, expectations: list) -> list:
    """Per-question expected/observed overlap for every route.

    Reported because an aggregate can move for reasons that are not the reason
    it appears to have moved, and a per-question view is what distinguishes
    "fusion recovered questions" from "fusion traded one set of hits for
    another of the same size".
    """
    expected = {entry_id: set(chunk_ids) for entry_id, chunk_ids in expectations}

    rows = []
    for entry_id, routes in executed:
        row = {"id": entry_id, "expected": len(expected[entry_id])}
        for route in ROUTES:
            row[route] = len(expected[entry_id] & set(routes[route]))
        rows.append(row)

    return rows


def deltas(baseline: dict, measured: dict) -> dict:
    """Absolute and relative movement of one metric set against another.

    Both are reported, and neither is interpreted. **No materiality threshold
    is applied**, because no repository authority defines one and inventing one
    after seeing the numbers would be choosing the verdict and then choosing
    the rule that produces it.
    """
    movement = {}
    for name, before in baseline.items():
        after = measured.get(name)
        if after is None:
            continue

        absolute = after - before
        movement[name] = {
            "before": before,
            "after": after,
            "absolute": round(absolute, 4),
            "relative": round(absolute / before, 4) if before else None,
        }

    return movement


def flatten(metrics: dict) -> dict:
    """Collapse a `metrics.Report`'s two sections into one lookup."""
    return {**metrics["retrieval"], **metrics["classification"]}


def report(measured: dict, executed: list, expectations: list) -> None:
    """Print the four-column comparison, the deltas, and the per-question view."""
    print(f"RRF k                {RRF_K}")
    print(f"route top_k          {ROUTE_TOP_K}")
    print(f"questions            {len(executed)}\n")

    header = f"  {'metric':<30}{HISTORICAL_LABEL:>22}"
    for route in ROUTES:
        header += f"{route:>14}"
    print(header)

    flat = {route: flatten(metrics) for route, metrics in measured.items()}
    for section, field, label in COMPARISON_ROWS:
        historical = HISTORICAL_OVERLAP_BASELINE.get(field)
        row = f"  {label:<30}{'—' if historical is None else historical:>22}"
        for route in ROUTES:
            row += f"{flat[route][field]:>14}"
        print(row)

    for reference, title in (
        (HISTORICAL_OVERLAP_BASELINE, "RRF vs the historical overlap baseline"),
        (
            {name: flat[LEXICAL_ROUTE][name] for name in HISTORICAL_OVERLAP_BASELINE},
            "RRF vs BM25 (the route F-1 was raised against)",
        ),
        (
            {name: flat[SEMANTIC_ROUTE][name] for name in HISTORICAL_OVERLAP_BASELINE},
            "RRF vs the semantic route",
        ),
    ):
        print(f"\n{title}")
        for name, movement in deltas(reference, flat[FUSED_ROUTE]).items():
            relative = "—" if movement["relative"] is None else f"{movement['relative']:+.4f}"
            print(
                f"  {name:<30} {movement['before']:>10} -> {movement['after']:<10} "
                f"absolute {movement['absolute']:+.4f}   relative {relative}"
            )

    print("\nPer-question expected-chunk hits")
    print(f"  {'question':<40}{'expected':>10}" + "".join(f"{route:>10}" for route in ROUTES))
    for row in per_question_rows(executed, expectations):
        print(
            f"  {row['id']:<40}{row['expected']:>10}"
            + "".join(f"{row[route]:>10}" for route in ROUTES)
        )


def main() -> None:
    """Measure all three routes against the F-1 benchmark and report neutrally.

    Repository integrity is demonstrated by measurement rather than asserted:
    digests are taken around the whole comparison, exactly as
    `scripts/evaluate_retrieval.py` does. The committed authorities are read;
    none is written.
    """
    before = authority_digests()

    chunks, executed = observe_routes()
    expectations = load_expectations()
    chunk_documents = index_chunk_documents(chunks)

    measured = {
        route: metrics_for(route, executed, expectations, chunk_documents)
        for route in ROUTES
    }

    report(measured, executed, expectations)

    status = "PASS" if authority_digests() == before else "FAIL"
    print(f"\n  {'repository integrity':<30} {status}")


if __name__ == "__main__":
    main()
