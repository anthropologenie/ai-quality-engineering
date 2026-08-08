"""Deterministic Retrieval Metrics Engine.

Sprint P3.3.3: computes classical Information Retrieval metrics from the
Retrieval Evaluation records Sprint P3.3.2 produces. It answers one question —
how well did retrieval perform — and expresses no view on why.

Classical IR only, and explicitly not Ragas. `docs/AI_Quality_Metrics_Reference.md`
§Layer 3 names Context Precision and Context Recall as *the* canonical retrieval
metrics, evaluated by Ragas, with "no substitutes at this layer", and §Milestone
Mapping places Layer 3 in Milestone 2 once real embeddings and FAISS exist. The
metrics below are deterministic set-arithmetic measurements over a committed
evaluation; they are not those metrics, do not approximate them, and must not be
reported under their names. The distinction is maintained in the naming itself:
every metric here is prefixed `chunk_` or `classification_`, never `context_`.

Dependency rule (Sprint P3.3.3): this engine consumes **only** Retrieval
Evaluation records. It does not import, read, or reach the Chunk Corpus, the
Evidence Trace Dataset, the Knowledge Manifest, the Golden Dataset, Document
objects, or `RetrievalResult`. Structurally so — this module performs no
filesystem and no network I/O at all, and imports nothing from `sample_rag/`,
`scripts/`, or `evaluation.retrieval_evaluation`. Every value it reports is
derivable from the record fields it is handed, which is what allows a future
BM25, vector, or hybrid retriever to be measured without touching this file:
a new retriever changes what the records *say*, not what a record *is*.

**The BM25 half of that sentence is no longer future, and the claim held.** Sprint
M2.03 replaced the lexical scorer with genuine BM25 (**M2-03**) and this module
was not edited, imported differently or re-specified; only the numbers it reports
moved. Vector and hybrid retrieval remain future — **M2-02**'s query stage exists
but no evaluation record is produced from it, and fusion is **M2-04**.

    evaluation.Record[]  ->  Retrieval Metrics Engine  ->  metrics.Report
"""

import math

from collections import Counter

# The four Sprint P3.3.2 Work Package 3 categories, restated as the label
# strings the records carry. Deliberately not imported from
# `evaluation.retrieval_evaluation`: the dependency rule admits records, not the
# evaluation module, and an import would make this engine unable to measure any
# other conforming producer of evaluation records.
EXACT_MATCH = "Exact Match"
FULL_COVERAGE = "Full Coverage"
PARTIAL_MATCH = "Partial Match"
NO_MATCH = "No Match"

CLASSIFICATIONS = (EXACT_MATCH, FULL_COVERAGE, PARTIAL_MATCH, NO_MATCH)

# Rate field name per classification, in the frozen category order.
RATE_FIELDS = (
    (EXACT_MATCH, "exact_match"),
    (FULL_COVERAGE, "full_coverage"),
    (PARTIAL_MATCH, "partial_match"),
    (NO_MATCH, "no_match"),
)

# Four places, the repository's established serialization precision for
# coverage figures (`scripts/run_retrieval.py` `corpus_utilization`,
# `evaluation/retrieval_evaluation.py` `_ratio`), so metric values here are
# directly comparable with the descriptive ratios those layers already report.
PRECISION = 4

# The record fields this engine reads, and the type each must have. Nothing
# outside this set is consulted; a record carrying additional fields is
# accepted, because a later evaluation layer may record more than this engine
# measures.
REQUIRED_RECORD_FIELDS = {
    "id": str,
    "classification": str,
    "expected_chunk_ids": list,
    "observed_chunk_ids": list,
    "matched_chunk_ids": list,
    "expected_count": int,
    "observed_count": int,
    "matched_count": int,
}


class RetrievalMetricsError(Exception):
    """Raised when Retrieval Evaluation records cannot be measured.

    A seventh independent, flat exception type, following the repository's
    per-responsibility pattern (`ManifestValidationError`, `ChunkConstructionError`,
    `ChunkSerializationError`, `ChunkValidationError`, `EvidenceTraceError`,
    `RetrievalEvaluationError`) — a direct `Exception` subclass with no shared
    validation base class (docs/CHUNK_VALIDATION_PLAN.md §P6.2).
    """


def rate(numerator: int, denominator: int) -> float:
    """A ratio, rounded to the repository's serialization precision.

    A zero denominator yields `0.0` rather than raising or returning `None`.
    Every call site below reaches a zero denominator only in the degenerate case
    its own docstring names, and in each of those the measured quantity is
    genuinely absent rather than unknown — no questions evaluated, or no chunks
    retrieved to be precise about. Returning a number keeps `metrics.Report`
    total: every field is populated on every path, which is the same contract
    `RetrievalResult` holds (docs/MILESTONE_1A.md Architectural AC2).
    """
    return round(exact_ratio(numerator, denominator), PRECISION)


def exact_ratio(numerator: int, denominator: int) -> float:
    """The same ratio, unrounded — the value `rate` publishes a rounding of.

    Macro aggregation sums these rather than the published values, so a mean is
    rounded exactly once, at publication, instead of being a mean of already-
    rounded numbers. Double rounding would make the macro figures depend on
    `PRECISION` in a way that is invisible in the report.
    """
    return numerator / denominator if denominator else 0.0


def validate_records(records: list) -> list:
    """Verify records are measurable before any metric is computed.

    Structural gate, fail-fast, `list -> list` — the same public shape
    `validate_manifest`, `validate_chunks` and `validate_evidence_trace`
    establish, so records reach a metric only through a gate.

    Three classes of check, each guarding a specific way a metric could be
    silently wrong rather than absent:

    * **Field presence and type** — a missing count would make a denominator
      raise; a missing id list would make the independent validator unable to
      re-derive anything.
    * **Count/id agreement** — `expected_count` must equal `len(expected_chunk_ids)`
      and likewise for observed and matched. The two are redundant by
      construction in Sprint P3.3.2's records, and a metric computed from a
      count that disagrees with its own id list would be arithmetically valid
      and factually wrong.
    * **Non-empty expectation** — recall's denominator. Sprint P3.3.2's
      `evaluate_entry` already refuses an empty expectation, so this restates
      that engine's domain rather than widening it; restating it here is what
      lets Chunk Recall@K have a guaranteed non-zero denominator instead of a
      convention.

    Duplicate record ids are refused: a question measured twice is counted twice
    in every denominator.
    """
    if not isinstance(records, list):
        raise RetrievalMetricsError("Retrieval Evaluation records must be a list.")

    seen: set = set()
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise RetrievalMetricsError(f"Record at index {index} must be an object.")

        for field, expected_type in REQUIRED_RECORD_FIELDS.items():
            if field not in record:
                raise RetrievalMetricsError(
                    f"Record at index {index} is missing required field {field!r}."
                )
            if not isinstance(record[field], expected_type):
                raise RetrievalMetricsError(
                    f"Record at index {index} field {field!r} must be of type "
                    f"{expected_type.__name__}."
                )

        if record["classification"] not in CLASSIFICATIONS:
            raise RetrievalMetricsError(
                f"Record {record['id']!r} carries unknown classification "
                f"{record['classification']!r}."
            )

        for count_field, ids_field in (
            ("expected_count", "expected_chunk_ids"),
            ("observed_count", "observed_chunk_ids"),
            ("matched_count", "matched_chunk_ids"),
        ):
            if record[count_field] != len(record[ids_field]):
                raise RetrievalMetricsError(
                    f"Record {record['id']!r} field {count_field!r} is "
                    f"{record[count_field]} but {ids_field!r} holds "
                    f"{len(record[ids_field])} ids."
                )

        if record["expected_count"] == 0:
            raise RetrievalMetricsError(
                f"Record {record['id']!r} expects no chunks; Chunk Recall@K has no "
                f"denominator for it."
            )

        if record["id"] in seen:
            raise RetrievalMetricsError(f"Duplicate Retrieval Evaluation record id {record['id']!r}.")
        seen.add(record["id"])

    return records


def chunk_precision_at_k(record: dict) -> float:
    """Fraction of retrieved chunks that were expected, for one question.

        |E ∩ O| / |O|        matched_count / observed_count

    **K is the observed retrieval size, not a configured constant.** The
    retriever's `top_k` is a runtime filter value carried in
    `RetrievalResult.diagnostics`; Retrieval Evaluation records do not carry it,
    and the dependency rule bars this engine from reading the runtime to find
    out. The denominator is therefore what was actually retrieved, which equals
    the configured `top_k` for every question except one whose corpus offered
    fewer candidates than `top_k`. Recorded as an observation for Sprint P3.3.4
    rather than worked around here.

    Zero retrieved chunks yields `0.0`: no expected chunk was among those
    retrieved, because none was retrieved. This is a convention, not a
    measurement — the alternative reading is that precision is undefined — and
    it is the only zero denominator either metric can reach.
    """
    return rate(record["matched_count"], record["observed_count"])


def chunk_recall_at_k(record: dict) -> float:
    """Fraction of expected chunks that were retrieved, for one question.

        |E ∩ O| / |E|        matched_count / expected_count

    The denominator is guaranteed non-zero by `validate_records`, which inherits
    the domain Sprint P3.3.2's evaluation engine already enforces. "@K" is
    carried in the name because the numerator is bounded by what a top-K
    retrieval could return, not because K appears in the arithmetic.
    """
    return rate(record["matched_count"], record["expected_count"])


def per_question_metrics(records: list) -> list:
    """Per-question metric values, in record order.

    Record order is Retrieval Evaluation order, which is Evidence Trace order,
    which is the QA Dataset's own order — preserved through three layers without
    re-sorting, so a metric row can be read against the dataset row-for-row.

    The classification is carried through rather than recomputed: this engine
    measures classifications, it does not assign them. Re-deriving it here would
    duplicate Sprint P3.3.2's algorithm in a layer that has no authority over it
    — and it is precisely what the independent validator does instead, from a
    position where disagreement is a finding rather than a duplication.
    """
    return [
        {
            "id": record["id"],
            "classification": record["classification"],
            "chunk_precision_at_k": chunk_precision_at_k(record),
            "chunk_recall_at_k": chunk_recall_at_k(record),
        }
        for record in records
    ]


def hit_metrics(records: list) -> dict:
    """Hit Rate — did retrieval return any relevant evidence?

        success(q) := |E ∩ O| > 0

        Hit Rate = successful questions / questions evaluated

    **Computed by aggregating Retrieval Evaluation classifications, not by
    re-performing set intersection** (Sprint P3.3.3 Repository Decision 1). The
    Metrics layer aggregates the Evaluation layer; it does not duplicate its
    logic. Sprint P3.3.2 already decided, validated, and froze which questions
    overlap — No Match is defined as `E ∩ O = ∅` and the four categories are
    validated mutually exclusive and collectively exhaustive — so intersecting
    the sets again here would be a second implementation of that decision,
    free to drift from it.

        Hit Rate = Exact Match + Full Coverage + Partial Match
                 ≡ 1 − No Match Rate

    Both forms are stated by Decision 1 and are the same number. The first is
    computed; the second is verified exactly, over rationals, by the independent
    validator — where the equivalence is a cross-check rather than a restatement.

    This metric is **not** named "Top-k Success Rate". That term is deliberately
    absent from the repository (Decision 1), and no alias is retained.
    """
    totals = Counter(record["classification"] for record in records)
    hits = totals[EXACT_MATCH] + totals[FULL_COVERAGE] + totals[PARTIAL_MATCH]

    return {"hit_count": hits, "hit_rate": rate(hits, len(records))}


def _macro(values: list) -> float:
    """Mean of per-question ratios, rounded once. Empty input yields `0.0`."""
    return round(math.fsum(values) / len(values), PRECISION) if values else 0.0


def classification_metrics(records: list) -> dict:
    """Counts and rates for the four evaluation classifications (Work Package 2).

    Pure aggregation over `record["classification"]`. Every category is present
    even at zero — an absent key and a zero rate are different claims, and only
    the second is true — and the four counts sum to the question count by the
    collective exhaustiveness Sprint P3.3.2 validates.

    Rates are fractions of questions evaluated, in `[0.0, 1.0]`, not percentages.
    A zero-question evaluation yields four zero rates rather than a raised error:
    the report stays total, and `questions_evaluated` already records that
    nothing was measured.
    """
    totals = Counter(record["classification"] for record in records)
    questions = len(records)

    metrics = {"questions_evaluated": questions}
    for classification, field in RATE_FIELDS:
        metrics[f"{field}_count"] = totals[classification]
        metrics[f"{field}_rate"] = rate(totals[classification], questions)
    return metrics


def retrieval_metrics(records: list) -> dict:
    """Classical IR metrics over the evaluation (Work Package 3).

    Both Chunk Precision@K and Chunk Recall@K are reported under **two**
    aggregations, because the repository has ratified neither and they answer
    different questions:

    * **macro** — the mean of the per-question values. Every question counts
      equally regardless of how many chunks it expects.
    * **micro** — summed numerators over summed denominators. Every *chunk*
      counts equally, so questions expecting more evidence weigh more.

    Reporting both is not indecision: they are the two standard aggregations, no
    repository authority selects between them, and selecting one here would make
    a methodological choice on Sprint P3.3.4's behalf while presenting it as a
    measurement. Both are deterministic and both are derivable from records
    alone.

    Macro values are means of the **unrounded** per-question ratios, rounded
    once at publication (see `exact_ratio`). `math.fsum` is used rather than
    `sum` so the accumulation is correctly rounded regardless of record order —
    a mean that shifted in its last digit when questions were reordered would
    not be the stable ordering Sprint P3.3.2 validates.
    """
    questions = len(records)
    per_question = per_question_metrics(records)

    matched = sum(record["matched_count"] for record in records)
    expected = sum(record["expected_count"] for record in records)
    observed = sum(record["observed_count"] for record in records)

    expected_unique = {
        chunk_id for record in records for chunk_id in record["expected_chunk_ids"]
    }
    observed_unique = {
        chunk_id for record in records for chunk_id in record["observed_chunk_ids"]
    }

    return {
        **hit_metrics(records),
        "expected_chunk_references": expected,
        "retrieved_chunk_references": observed,
        "matched_chunk_references": matched,
        "expected_chunks_unique": len(expected_unique),
        "retrieved_chunks_unique": len(observed_unique),
        "chunk_precision_at_k_macro": _macro(
            [exact_ratio(r["matched_count"], r["observed_count"]) for r in records]
        ),
        "chunk_precision_at_k_micro": rate(matched, observed),
        "chunk_recall_at_k_macro": _macro(
            [exact_ratio(r["matched_count"], r["expected_count"]) for r in records]
        ),
        "chunk_recall_at_k_micro": rate(matched, expected),
    }


def compute(records: list) -> dict:
    """Produce `metrics.Report` from Retrieval Evaluation records.

    The engine's single entry point and its output contract. Records are
    validated first, so no metric is ever computed from an unmeasurable record.

    Key order is fixed by construction rather than by input, and every nested
    collection is either in record order or built from a fixed field list, so
    two runs over equal records produce equal reports — and equal serializations.
    """
    validate_records(records)

    return {
        "classification": classification_metrics(records),
        "retrieval": retrieval_metrics(records),
        "per_question": per_question_metrics(records),
    }
