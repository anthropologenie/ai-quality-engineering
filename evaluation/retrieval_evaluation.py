"""Deterministic Retrieval Evaluation Engine.

Sprint P3.3.2: the repository's first comparison of *observed* retrieval
(`RetrievalResult`, Sprint P3.3.1) against its *expected* retrieval authority
(the Evidence Trace Dataset, Sprint P3.2.4). It answers one question per
evidence entry — which expected chunks were retrieved — and nothing beyond it.

Evaluation only. No metric is computed here: Chunk Precision@K, Chunk Recall@K,
Exact Match Rate, Hit Rate and every ranking statistic belong to Sprint P3.3.3,
and interpretation of any of them to Sprint P3.3.4. Context Precision and
Context Recall are Ragas metrics reserved for Milestone 2
(docs/AI_Quality_Metrics_Reference.md §Layer 3) and belong to neither. The
summaries below are descriptive counts of what was observed, which is what a
metrics layer consumes — not a substitute for one.

Read-only, and structurally so, following the precedent `sample_rag/retriever.py`
set: this module performs no filesystem and no network I/O at all, so no
evaluation path can reach a repository authority to modify it. Loading the
Evidence Trace Dataset and executing the Retrieval Runtime is the caller's
responsibility (`scripts/evaluate_retrieval.py`), which also keeps `evaluation/`
free of any import from `scripts/` and from `sample_rag/` — the same direction
constraint docs/architecture.md §6 draws between the pipeline under test and the
logic that evaluates it.

Placement: `evaluation/` is that separation's evaluation half. docs/architecture.md
§6 assigns one subdirectory per evaluation *tool* (`deepeval/`, `promptfoo/`,
`ragas/`); this engine is tool-agnostic Layer 1 comparison logic — pure stdlib,
no framework — so it belongs to none of them and sits at the layer root instead.
docs/architecture.md §5 records Layer 1 (pytest) as the only evaluation layer
active in Milestone 1A; Ragas (Layer 2) arrives in Milestone 2 and is not
anticipated by any name here.

Comparison frame:

    Evidence Trace expected_chunk  ─┐
                                    ├─> set comparison -> classification
    RetrievalResult retrieved ids  ─┘
"""

from collections import Counter
from collections.abc import Mapping

# The four categories frozen by Sprint P3.3.2 Work Package 3, in the order that
# sprint defines them — strongest agreement first. They are mutually exclusive
# and collectively exhaustive over every possible (expected, observed) pair, a
# property `check_exhaustive_classification` re-derives from the predicates
# rather than trusting this list.
EXACT_MATCH = "Exact Match"
FULL_COVERAGE = "Full Coverage"
PARTIAL_MATCH = "Partial Match"
NO_MATCH = "No Match"

CLASSIFICATIONS = (EXACT_MATCH, FULL_COVERAGE, PARTIAL_MATCH, NO_MATCH)


class RetrievalEvaluationError(Exception):
    """Raised when observed retrieval cannot be evaluated against the Evidence
    Trace Dataset, or when a produced evaluation violates its own invariants.

    A sixth independent, flat exception type, following the repository's
    per-responsibility pattern (`ManifestValidationError`, `ChunkConstructionError`,
    `ChunkSerializationError`, `ChunkValidationError`, `EvidenceTraceError`) — a
    direct `Exception` subclass with no shared validation base class
    (docs/CHUNK_VALIDATION_PLAN.md §P6.2).
    """


def classify(expected: set, observed: set) -> str:
    """Classify one question by set comparison of expected against observed chunks.

    Set semantics, not ordered-list semantics — the Repository Decision of
    Sprint P3.3.2 Work Package 2. `expected_chunk` is ordered ascending by
    `chunk_index` (Sprint P3.2.4 Decision G) while `retrieved_chunk_ids` is
    ordered by retrieval ranking (Sprint P3.3.1). Those orderings are
    intentionally different and comparing them positionally would report a
    disagreement that neither authority asserts. Membership is what is evaluated
    here; ranking is Sprint P3.3.3's.

    The four predicates, evaluated in order of decreasing agreement:

        O == E              Exact Match     exactly the expected chunks
        E ⊂ O               Full Coverage   all expected, plus others
        E ∩ O ≠ ∅ ∧ E ⊄ O   Partial Match   some expected, some missing
        E ∩ O = ∅           No Match        no expected evidence at all

    Order of evaluation is a readability choice, not a semantic one: over this
    function's domain the four conditions are disjoint, so any evaluation order
    yields the same answer. There is no separate "Unexpected Match" category —
    retrieval that returned only unrelated chunks and retrieval that returned
    nothing are both zero-overlap, and No Match represents both.

    Domain: `expected` must be non-empty, which is why `evaluate_entry` refuses
    an empty expectation rather than passing it through. The four conditions are
    mutually exclusive everywhere except at `E = ∅`, where `O == E` and
    `E ∩ O = ∅` both hold for empty observed retrieval and Exact Match and No
    Match would be simultaneously true. That pair is unreachable from the
    Retrieval Expectation Authority — `scripts/build_evidence_trace.py` refuses
    to derive an entry resolving to zero chunks, and `validate_evidence_trace`
    rejects an empty `expected_chunk` on read — so the categories partition the
    real domain exactly, and the engine enforces that domain instead of
    assuming it.
    """
    if observed == expected:
        return EXACT_MATCH
    if expected < observed:
        return FULL_COVERAGE
    if expected & observed:
        return PARTIAL_MATCH
    return NO_MATCH


def evaluate_entry(entry_id: str, expected_chunk_ids: list, observed_chunk_ids: list) -> dict:
    """Evaluate one Evidence Trace entry against one RetrievalResult.

    Every chunk-id collection on the returned record is a sorted list, never a
    set: sets have no order to serialize and no order to compare, so a record
    built from them would be unstable across runs for reasons that have nothing
    to do with retrieval. Sorting by chunk id — not by rank and not by
    `chunk_index` — keeps the record's ordering a property of identity alone,
    which is the only ordering both input authorities agree on.

    Counts are carried alongside the id lists because the aggregate summary and
    Sprint P3.3.3's metrics both need them, and recomputing `len()` at each call
    site is how those two layers would drift apart.

    An empty expectation is refused, not classified: it is the one input at
    which the four categories stop being mutually exclusive (see `classify`),
    and the Evidence Trace Dataset never produces one. Observed retrieval may be
    empty — that is No Match, and a legitimate evaluation.
    """
    expected = set(expected_chunk_ids)
    observed = set(observed_chunk_ids)

    if not expected:
        raise RetrievalEvaluationError(
            f"Evidence Trace entry {entry_id!r} carries no expected chunk; retrieval "
            f"cannot be evaluated against an empty expectation."
        )

    return {
        "id": entry_id,
        "classification": classify(expected, observed),
        "expected_chunk_ids": sorted(expected),
        "observed_chunk_ids": sorted(observed),
        # Retrieved and expected. The evaluation's positive evidence.
        "matched_chunk_ids": sorted(expected & observed),
        # Expected but not retrieved.
        "missing_chunk_ids": sorted(expected - observed),
        # Retrieved but not expected. Recorded, not judged: the Evidence Trace
        # Dataset asserts which chunks carry the answer, never that no other
        # chunk may be retrieved alongside them.
        "unexpected_chunk_ids": sorted(observed - expected),
        "expected_count": len(expected),
        "observed_count": len(observed),
        "matched_count": len(expected & observed),
    }


def evaluate(expectations: list, observations: Mapping) -> list:
    """Evaluate every Evidence Trace entry against exactly one RetrievalResult.

    `expectations` is `(entry_id, expected_chunk_ids)` in Evidence Trace order —
    which is the QA Dataset's own order (Sprint P3.2.4) — and that order is
    preserved exactly. `observations` maps entry id to observed chunk ids.

    The pairing is required to be total and one-to-one in both directions: an
    entry with no observation cannot be evaluated, and an observation with no
    entry means the runtime was executed over questions the expectation
    authority does not contain. Either is a broken execution rather than a
    retrieval finding, so both are refused here instead of being summarized as
    a No Match.
    """
    seen = [entry_id for entry_id, _ in expectations]

    duplicated = sorted({entry_id for entry_id in seen if seen.count(entry_id) > 1})
    if duplicated:
        raise RetrievalEvaluationError(
            f"Evidence Trace entry ids {duplicated} appear more than once; each entry "
            f"must be evaluated exactly once."
        )

    unobserved = [entry_id for entry_id in seen if entry_id not in observations]
    if unobserved:
        raise RetrievalEvaluationError(
            f"No RetrievalResult was observed for Evidence Trace entries {unobserved}."
        )

    unexpected = sorted(set(observations) - set(seen))
    if unexpected:
        raise RetrievalEvaluationError(
            f"RetrievalResults {unexpected} correspond to no Evidence Trace entry."
        )

    return [
        evaluate_entry(entry_id, expected_chunk_ids, observations[entry_id])
        for entry_id, expected_chunk_ids in expectations
    ]


def _distribution(chunk_ids: list, chunk_documents: Mapping) -> dict:
    """Count chunk references per parent document, ordered by document id.

    References, not distinct chunks: a chunk expected by three questions counts
    three times, because the distribution describes how often each document was
    drawn upon across the evaluation, not how much of it was touched. Distinct
    coverage is reported separately as chunk utilization.

    Key order is sorted by document id so the serialized summary is byte-stable
    across runs; `Counter.most_common()` order would be insertion-dependent.
    """
    counts = Counter(chunk_documents[chunk_id] for chunk_id in chunk_ids)
    return {document_id: counts[document_id] for document_id in sorted(counts)}


def summarize(evaluations: list, chunk_documents: Mapping) -> dict:
    """Describe the evaluation in aggregate.

    Descriptive counts only (Sprint P3.3.2 Work Package 4). The classification
    totals below are frequencies, not rates: no total is divided by the question
    count, because Exact Match Rate, Chunk Recall@K and Hit Rate are named
    Sprint P3.3.3 deliverables and computing them here would move that sprint's
    output into this one under a different name.

    The two utilization ratios are the single exception, and are corpus-coverage
    descriptions rather than retrieval metrics: they measure how much of the
    Chunk Corpus each side of the comparison touched, and neither has expected
    and observed on opposite sides of the division. The same ratio over the same
    denominator is already reported by `scripts/run_retrieval.py`'s
    `corpus_utilization` for observed retrieval alone (Sprint P3.3.1).
    """
    corpus_size = len(chunk_documents)
    totals = Counter(evaluation["classification"] for evaluation in evaluations)

    expected_references = [
        chunk_id for evaluation in evaluations for chunk_id in evaluation["expected_chunk_ids"]
    ]
    observed_references = [
        chunk_id for evaluation in evaluations for chunk_id in evaluation["observed_chunk_ids"]
    ]

    expected_chunks = set(expected_references)
    observed_chunks = set(observed_references)
    overlap = expected_chunks & observed_chunks

    return {
        "questions_evaluated": len(evaluations),
        # Classification totals, in the frozen Work Package 3 order. Every
        # category is present even at zero: an absent key and a zero count are
        # different claims, and only the second one is true.
        "exact_match": totals[EXACT_MATCH],
        "full_coverage": totals[FULL_COVERAGE],
        "partial_match": totals[PARTIAL_MATCH],
        "no_match": totals[NO_MATCH],
        "expected_document_distribution": _distribution(expected_references, chunk_documents),
        "observed_document_distribution": _distribution(observed_references, chunk_documents),
        "expected_chunk_references": len(expected_references),
        "observed_chunk_references": len(observed_references),
        "expected_chunks_unique": len(expected_chunks),
        "observed_chunks_unique": len(observed_chunks),
        "corpus_size": corpus_size,
        "expected_chunk_utilization": _ratio(len(expected_chunks), corpus_size),
        "observed_chunk_utilization": _ratio(len(observed_chunks), corpus_size),
        # Distinct chunks that are both expected somewhere and observed
        # somewhere — a corpus-level intersection, deliberately not per-question.
        # A chunk expected by one question and retrieved for a different one
        # counts here and does not count toward that question's matched_count.
        "chunk_overlap_unique": len(overlap),
        "chunk_overlap_references": sum(
            evaluation["matched_count"] for evaluation in evaluations
        ),
        "expected_only_chunks": len(expected_chunks - observed_chunks),
        "observed_only_chunks": len(observed_chunks - expected_chunks),
    }


def _ratio(numerator: int, denominator: int) -> float:
    """Round a coverage fraction to the repository's serialization precision.

    Four places, matching `scripts/run_retrieval.py`'s `corpus_utilization`, so
    the two layers' coverage figures are directly comparable rather than
    differing in the last digit. A zero denominator yields `0.0` rather than
    raising: an empty corpus is a corpus that was zero percent covered.
    """
    return round(numerator / denominator, 4) if denominator else 0.0


def check_deterministic_comparison(expectations: list, observations: Mapping) -> None:
    """Verify that evaluating the same inputs twice produces the same evaluation.

    Re-evaluates rather than re-reading a cached result, which is what makes this
    a check on `evaluate` and not on the caller. `evaluate` reads no clock, no
    environment and no filesystem, and holds no state between calls, so the only
    way this can fail is set iteration leaking into an output — precisely the
    defect `evaluate_entry`'s sorting exists to prevent.
    """
    if evaluate(expectations, observations) != evaluate(expectations, observations):
        raise RetrievalEvaluationError(
            "Evaluation is not deterministic: two evaluations of identical inputs differ."
        )


def check_stable_ordering(evaluations: list, expectations: list) -> None:
    """Verify evaluation order and every id list's internal order.

    Two distinct orderings, both required. Across records: Evidence Trace order,
    preserved exactly, so the evaluation can be read against the dataset
    row-for-row. Within a record: ascending chunk id, so no field's order can
    vary with set iteration.
    """
    ordered = [entry_id for entry_id, _ in expectations]
    produced = [evaluation["id"] for evaluation in evaluations]
    if produced != ordered:
        raise RetrievalEvaluationError(
            "Evaluation order does not follow Evidence Trace order."
        )

    id_fields = (
        "expected_chunk_ids",
        "observed_chunk_ids",
        "matched_chunk_ids",
        "missing_chunk_ids",
        "unexpected_chunk_ids",
    )
    for evaluation in evaluations:
        for field in id_fields:
            if evaluation[field] != sorted(evaluation[field]):
                raise RetrievalEvaluationError(
                    f"Evaluation {evaluation['id']!r} field {field!r} is not in stable order."
                )


def check_referential_integrity(evaluations: list, chunk_ids: set) -> None:
    """Verify every evaluated chunk id exists in the Chunk Corpus.

    Both sides are checked against the same corpus. An expected id absent from
    the corpus would mean the Evidence Trace Dataset and the Chunk Corpus have
    diverged; an observed id absent from it would mean the runtime retrieved
    something the corpus does not contain. Neither is a retrieval finding, and
    an evaluation that silently classified either would be reporting on chunks
    that do not exist.
    """
    for evaluation in evaluations:
        unknown_expected = sorted(set(evaluation["expected_chunk_ids"]) - chunk_ids)
        if unknown_expected:
            raise RetrievalEvaluationError(
                f"Evaluation {evaluation['id']!r} expects chunk ids {unknown_expected}, "
                f"which the Chunk Corpus does not contain."
            )

        unknown_observed = sorted(set(evaluation["observed_chunk_ids"]) - chunk_ids)
        if unknown_observed:
            raise RetrievalEvaluationError(
                f"Evaluation {evaluation['id']!r} observed chunk ids {unknown_observed}, "
                f"which the Chunk Corpus does not contain."
            )


def check_exhaustive_classification(evaluations: list) -> None:
    """Verify every evaluation carries exactly one of the four classifications.

    The predicates are re-derived here from the record's own id lists rather than
    read back off `classification`, so this checks the *categories* — that
    exactly one of the four Work Package 3 conditions holds for every real
    (expected, observed) pair — and not merely that `classify` returned a string
    from a known list. Reading `classification` back would make the check
    tautological: `classify` returns exactly one value by construction, which
    proves nothing about whether the four conditions partition the space.

    An evaluation carrying an empty expectation would satisfy two conditions and
    fail here. `evaluate_entry` refuses to produce one, so this reports the
    violation rather than being the only thing standing between it and a
    summary — two independent guards over the same domain restriction.
    """
    for evaluation in evaluations:
        expected = set(evaluation["expected_chunk_ids"])
        observed = set(evaluation["observed_chunk_ids"])

        holding = [
            name
            for name, predicate in (
                (EXACT_MATCH, observed == expected),
                (FULL_COVERAGE, expected < observed),
                (PARTIAL_MATCH, bool(expected & observed) and not expected <= observed),
                (NO_MATCH, not expected & observed),
            )
            if predicate
        ]

        if len(holding) != 1:
            raise RetrievalEvaluationError(
                f"Evaluation {evaluation['id']!r} satisfies {len(holding)} classification "
                f"conditions ({holding}); the four categories must be mutually exclusive "
                f"and collectively exhaustive."
            )

        if holding[0] != evaluation["classification"]:
            raise RetrievalEvaluationError(
                f"Evaluation {evaluation['id']!r} is classified "
                f"{evaluation['classification']!r} but satisfies the {holding[0]!r} condition."
            )


def check_classification_totals(evaluations: list, summary: Mapping) -> None:
    """Verify the aggregate totals account for every evaluated question exactly once.

    The four category counts must sum to the question count — the aggregate
    restatement of collective exhaustiveness, and the check that would catch a
    summary drifting from the per-question records it describes.
    """
    counted = sum(
        summary[name] for name in ("exact_match", "full_coverage", "partial_match", "no_match")
    )
    if counted != len(evaluations):
        raise RetrievalEvaluationError(
            f"Classification totals sum to {counted} but {len(evaluations)} questions "
            f"were evaluated."
        )
    if summary["questions_evaluated"] != len(evaluations):
        raise RetrievalEvaluationError(
            f"Summary reports {summary['questions_evaluated']} questions evaluated but "
            f"{len(evaluations)} evaluations were produced."
        )


def run_validation_suite(
    evaluations: list, expectations: list, observations: Mapping, chunk_documents: Mapping,
    summary: Mapping,
) -> list:
    """Run every evaluation validation and report each outcome.

    Returns `{"check": ..., "status": "PASS"|"FAIL", "detail": ...}` records in a
    fixed order — the Sprint P3.3.2 Work Package 5 validation report. Unlike the
    repository's artifact validators, which are fail-fast because a malformed
    artifact must not reach a consumer, this deliberately runs every check and
    reports all of them: the deliverable is the full PASS/FAIL report, and
    stopping at the first failure would hide the state of the rest.

    The individual `check_*` functions remain fail-fast and independently
    callable, so a caller that needs a hard gate has one, and a specification can
    exercise any single check against synthetic input.
    """
    checks = (
        ("determinism", check_deterministic_comparison, (expectations, observations)),
        ("stable ordering", check_stable_ordering, (evaluations, expectations)),
        ("referential integrity", check_referential_integrity, (evaluations, set(chunk_documents))),
        ("exhaustive classification", check_exhaustive_classification, (evaluations,)),
        ("classification totals", check_classification_totals, (evaluations, summary)),
    )

    report = []
    for name, check, arguments in checks:
        try:
            check(*arguments)
        except RetrievalEvaluationError as exc:
            report.append({"check": name, "status": "FAIL", "detail": str(exc)})
        else:
            report.append({"check": name, "status": "PASS", "detail": ""})

    return report
