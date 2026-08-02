"""Specification Family 6 — Retrieval Metrics.

Sprint P3.3.3: executable specifications for the Retrieval Metrics Engine
(`evaluation/retrieval_metrics.py`) and its Independent Validator
(`evaluation/retrieval_metrics_validator.py`).

Three kinds of specification, deliberately separated:

    algebra      metric arithmetic over hand-constructed records, where the
                 expected value is written out by hand rather than computed
    contract     the dependency rule and the report's shape
    corpus       the committed repository authorities, measured end to end

The hand-written expectations matter. A specification that computed its own
expected value would restate the engine's formula and pass whatever that formula
said; `test_chunk_precision_is_matched_over_retrieved` asserts `0.25` because
one of four retrieved chunks was expected, and would fail if the engine ever
divided by something else.

No specification asserts a *retrieval outcome* on the committed corpus — that
the corpus scores 0.1308 micro precision is a fact about Sprint P3.3.1's
Milestone 1A lexical stub, which Milestone 2 is expected to change. Freezing
today's values here would convert a retrieval improvement into a test failure.
What is specified about the corpus is that both derivation paths agree, that the
report is total, and that measuring it changes nothing.

Observational only: every specification reads committed repository state and
writes nothing.
"""

import pytest

from evaluation.retrieval_metrics import (
    RetrievalMetricsError,
    chunk_precision_at_k,
    chunk_recall_at_k,
    classification_metrics,
    compute,
    rate,
    validate_records,
)
from evaluation.retrieval_metrics_validator import compare, flatten, recompute
from scripts.evaluate_retrieval import authority_digests
from scripts.report_retrieval_metrics import evaluation_records


def record(entry_id, expected, observed, classification=None):
    """Build one Retrieval Evaluation record in the Sprint P3.3.2 record shape.

    Counts and derived id lists are computed here so a specification states only
    the two sets it is actually about. `classification` may be overridden to
    construct the inconsistent records the validator exists to detect — the
    engine cannot produce such a record, so a specification must.
    """
    expected_set, observed_set = set(expected), set(observed)
    matched = sorted(expected_set & observed_set)

    if classification is None:
        if observed_set == expected_set:
            classification = "Exact Match"
        elif expected_set < observed_set:
            classification = "Full Coverage"
        elif expected_set & observed_set:
            classification = "Partial Match"
        else:
            classification = "No Match"

    return {
        "id": entry_id,
        "classification": classification,
        "expected_chunk_ids": sorted(expected_set),
        "observed_chunk_ids": sorted(observed_set),
        "matched_chunk_ids": matched,
        "missing_chunk_ids": sorted(expected_set - observed_set),
        "unexpected_chunk_ids": sorted(observed_set - expected_set),
        "expected_count": len(expected_set),
        "observed_count": len(observed_set),
        "matched_count": len(matched),
    }


@pytest.fixture(scope="module")
def records():
    """Retrieval Evaluation records for the committed repository authorities."""
    return evaluation_records()


@pytest.fixture(scope="module")
def metrics(records):
    """`metrics.Report` for the committed repository authorities."""
    return compute(records)


# ---------------------------------------------------------------------------
# Metric algebra
# ---------------------------------------------------------------------------


def test_chunk_precision_is_matched_over_retrieved():
    """Precision@K divides matched by *retrieved*: one of four retrieved was expected."""
    assert chunk_precision_at_k(record("meta_a", ["x"], ["x", "b", "c", "d"])) == 0.25


def test_chunk_recall_is_matched_over_expected():
    """Recall@K divides matched by *expected*: one of two expected was retrieved."""
    assert chunk_recall_at_k(record("meta_a", ["x", "y"], ["x", "b"])) == 0.5


def test_perfect_retrieval_scores_one_on_both_metrics():
    """An Exact Match retrieves every expected chunk and nothing else."""
    evaluation = record("meta_a", ["x", "y"], ["y", "x"])
    assert chunk_precision_at_k(evaluation) == 1.0
    assert chunk_recall_at_k(evaluation) == 1.0


def test_no_match_scores_zero_on_both_metrics():
    """Zero overlap is zero on both metrics regardless of how much was retrieved."""
    evaluation = record("meta_a", ["x"], ["a", "b", "c"])
    assert chunk_precision_at_k(evaluation) == 0.0
    assert chunk_recall_at_k(evaluation) == 0.0


def test_empty_retrieval_yields_zero_precision():
    """The one divide-by-zero either metric can reach, by documented convention.

    Precision over zero retrieved chunks is `0.0`, not an error and not `None`:
    `metrics.Report` is total, every field populated on every path. Recall is
    unaffected — its denominator is guaranteed non-zero by `validate_records`.
    """
    evaluation = record("meta_a", ["x"], [])
    assert chunk_precision_at_k(evaluation) == 0.0
    assert chunk_recall_at_k(evaluation) == 0.0


def test_rate_of_a_zero_denominator_is_zero():
    """`rate` never raises and never returns `None`."""
    assert rate(0, 0) == 0.0
    assert rate(5, 0) == 0.0


def test_classification_rates_are_fractions_of_questions_evaluated():
    """Rates are counts over the question count, in [0.0, 1.0] — not percentages."""
    metrics = classification_metrics(
        [
            record("meta_a", ["x"], ["x"]),
            record("meta_b", ["x"], ["x", "y"]),
            record("meta_c", ["x", "y"], ["x", "z"]),
            record("meta_d", ["x"], ["z"]),
        ]
    )

    assert metrics["questions_evaluated"] == 4
    assert metrics["exact_match_count"] == 1
    assert metrics["exact_match_rate"] == 0.25
    assert metrics["full_coverage_rate"] == 0.25
    assert metrics["partial_match_rate"] == 0.25
    assert metrics["no_match_rate"] == 0.25


def test_every_classification_is_reported_even_at_zero():
    """An absent key and a zero rate are different claims; only the second is true."""
    metrics = classification_metrics([record("meta_a", ["x"], ["x"])])

    assert metrics["exact_match_count"] == 1
    assert metrics["full_coverage_count"] == 0
    assert metrics["partial_match_count"] == 0
    assert metrics["no_match_count"] == 0


def test_hit_rate_counts_questions_with_any_relevant_evidence():
    """Hit Rate: success(q) := |E ∩ O| > 0.

    Four questions, one per category. Exact Match, Full Coverage and Partial
    Match all retrieved at least one expected chunk; No Match retrieved none.
    Three of four succeed.
    """
    report = compute(
        [
            record("meta_a", ["x"], ["x"]),
            record("meta_b", ["x"], ["x", "y"]),
            record("meta_c", ["x", "y"], ["x", "z"]),
            record("meta_d", ["x"], ["z"]),
        ]
    )

    assert report["retrieval"]["hit_count"] == 3
    assert report["retrieval"]["hit_rate"] == 0.75


def test_hit_rate_is_the_complement_of_the_no_match_rate():
    """The second form Repository Decision 1 states, on a corpus where it is exact."""
    report = compute(
        [
            record("meta_a", ["x"], ["x", "y"]),
            record("meta_b", ["x"], ["z"]),
        ]
    )

    assert report["retrieval"]["hit_rate"] == 0.5
    assert report["retrieval"]["hit_rate"] == 1 - report["classification"]["no_match_rate"]


def test_hit_rate_is_zero_when_nothing_relevant_is_retrieved():
    """Every question a No Match means no question returned relevant evidence."""
    report = compute([record("meta_a", ["x"], ["y"]), record("meta_b", ["p"], ["q"])])

    assert report["retrieval"]["hit_count"] == 0
    assert report["retrieval"]["hit_rate"] == 0.0


def test_hit_rate_aggregates_classifications_rather_than_reintersecting():
    """Repository Decision 1: the Metrics layer aggregates the Evaluation layer.

    A record whose stored classification says No Match is counted as a No Match
    even though its chunk sets overlap. The engine is not entitled to overrule
    Sprint P3.3.2's decision by re-deriving it — and the independent validator,
    which derives Hit Rate from the sets instead, is what surfaces the
    disagreement (`test_independent_validator_detects_a_wrong_classification`).
    """
    report = compute([record("meta_a", ["x"], ["x"], classification="No Match")])

    assert report["retrieval"]["hit_count"] == 0
    assert report["retrieval"]["hit_rate"] == 0.0


def test_macro_and_micro_aggregations_differ_when_evidence_is_uneven():
    """The two aggregations answer different questions, and are both reported.

    One question expects four chunks and retrieves one; the other expects one
    and retrieves it. Macro weights the questions equally — (0.25 + 1.0) / 2 =
    0.625. Micro weights the *chunks* — 2 matched of 5 expected = 0.4. Neither
    is a rounding of the other, which is why selecting one without repository
    authority would be a methodological choice presented as a measurement.
    """
    report = compute(
        [
            record("meta_a", ["w", "x", "y", "z"], ["w"]),
            record("meta_b", ["p"], ["p"]),
        ]
    )

    assert report["retrieval"]["chunk_recall_at_k_macro"] == 0.625
    assert report["retrieval"]["chunk_recall_at_k_micro"] == 0.4


# ---------------------------------------------------------------------------
# Input contract
# ---------------------------------------------------------------------------


def test_record_with_no_expected_chunks_is_refused():
    """Recall's denominator. Sprint P3.3.2 cannot produce such a record; the
    metrics layer restates that domain rather than assuming it."""
    evaluation = record("meta_a", [], ["x"])
    with pytest.raises(RetrievalMetricsError, match="has no denominator|expects no chunks"):
        validate_records([evaluation])


def test_record_whose_count_disagrees_with_its_ids_is_refused():
    """A metric computed from a count that contradicts its own id list would be
    arithmetically valid and factually wrong."""
    evaluation = record("meta_a", ["x"], ["x", "y"])
    evaluation["observed_count"] = 5

    with pytest.raises(RetrievalMetricsError, match="observed_count"):
        validate_records([evaluation])


def test_record_with_unknown_classification_is_refused():
    """The engine measures the four ratified categories and no others."""
    evaluation = record("meta_a", ["x"], ["x"], classification="Unexpected Match")
    with pytest.raises(RetrievalMetricsError, match="unknown classification"):
        validate_records([evaluation])


def test_duplicate_record_ids_are_refused():
    """A question measured twice is counted twice in every denominator."""
    with pytest.raises(RetrievalMetricsError, match="Duplicate"):
        validate_records([record("meta_a", ["x"], ["x"]), record("meta_a", ["y"], ["y"])])


def test_missing_required_field_is_refused():
    """Fields are checked before any metric is computed."""
    evaluation = record("meta_a", ["x"], ["x"])
    del evaluation["matched_count"]

    with pytest.raises(RetrievalMetricsError, match="matched_count"):
        validate_records([evaluation])


def test_empty_evaluation_produces_a_total_report():
    """Zero questions yields zero rates, not a raised error or a missing key."""
    report = compute([])

    assert report["classification"]["questions_evaluated"] == 0
    assert report["classification"]["exact_match_rate"] == 0.0
    assert report["retrieval"]["chunk_precision_at_k_macro"] == 0.0
    assert report["retrieval"]["chunk_recall_at_k_micro"] == 0.0
    assert report["per_question"] == []


def imported_roots(module):
    """The set of top-level package names a module imports.

    Parsed from the module's own source rather than matched as text: a docstring
    that *names* a module is not an import of it, and a substring check cannot
    tell the two apart. The AST can.
    """
    import ast

    from pathlib import Path

    tree = ast.parse(Path(module.__file__).read_text(encoding="utf-8"))
    roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".")[0])
    return roots


def test_metrics_engine_imports_no_repository_authority():
    """The dependency rule, enforced structurally rather than asserted.

    The engine must be measurable against any conforming producer of Retrieval
    Evaluation records, which it cannot be if it can reach the Chunk Corpus, the
    Evidence Trace Dataset, the Golden Dataset, or the Retrieval Runtime. An
    allowlist rather than a denylist: a new import of anything not named here
    fails, including one nobody thought to forbid.
    """
    import evaluation.retrieval_metrics as engine

    assert imported_roots(engine) <= {"math", "collections"}


# ---------------------------------------------------------------------------
# Independent derivation (Path A vs Path B)
# ---------------------------------------------------------------------------


def test_independent_validator_agrees_on_synthetic_records():
    """Both paths produce identical published values over constructed records."""
    records = [
        record("meta_a", ["w", "x"], ["w", "y", "z"]),
        record("meta_b", ["p"], ["p", "q"]),
        record("meta_c", ["r"], ["s", "t"]),
    ]

    flattened = flatten(compute(records))
    independent = recompute(records)

    assert flattened == independent


def test_independent_validator_detects_a_wrong_count():
    """The check the engine cannot perform on its own behalf.

    The engine *uses* the stored counts, so a wrong one yields a wrong metric
    consistently; the validator recomputes from the id lists and never reads
    them, which is what lets it notice.

    The report is computed from the clean records first, because the engine's
    own `validate_records` gate refuses a record whose counts contradict its id
    lists (`test_record_whose_count_disagrees_with_its_ids_is_refused`) — the
    defect cannot reach a metric through the engine. This specifies the second,
    independent line of defense: a record corrupted after computation is still
    caught, by a path that never trusted the counts.
    """
    records = [record("meta_a", ["x"], ["x", "y"])]
    report = compute(records)
    records[0]["matched_count"] = 2

    rows = {row["check"]: row for row in compare(report, records)}

    assert rows["record count integrity"]["status"] == "FAIL"


def test_independent_validator_detects_a_wrong_classification():
    """A label disagreeing with its own chunk sets corrupts every rate while
    leaving them internally consistent and summing correctly.

    Hit Rate is where the two paths part company by design: the engine
    aggregates the stored label (Repository Decision 1) and reports 0.0, the
    validator derives success from `|E ∩ O| > 0` and reports 1.0. The
    disagreement is the finding.
    """
    records = [record("meta_a", ["x"], ["x"], classification="No Match")]

    rows = {row["check"]: row for row in compare(compute(records), records)}

    assert rows["record classification integrity"]["status"] == "FAIL"
    assert rows["independent derivation agreement"]["status"] == "FAIL"
    assert "hit_rate" in rows["independent derivation agreement"]["detail"]


def test_independent_validator_detects_a_tampered_report():
    """A report value that no longer follows from the records is caught."""
    records = [record("meta_a", ["x"], ["x", "y"])]
    report = compute(records)
    report["retrieval"]["chunk_precision_at_k_micro"] = 1.0

    rows = {row["check"]: row for row in compare(report, records)}

    assert rows["independent derivation agreement"]["status"] == "FAIL"


def test_independent_validator_detects_reordered_per_question_rows():
    """Record order carries through from the QA Dataset and is part of the contract."""
    records = [record("meta_a", ["x"], ["x"]), record("meta_b", ["y"], ["y"])]
    report = compute(records)
    report["per_question"].reverse()

    rows = {row["check"]: row for row in compare(report, records)}

    assert rows["per-question row integrity"]["status"] == "FAIL"


def test_independent_validator_detects_an_unreported_metric():
    """A metric derived by one path and absent from the other is a coverage failure."""
    records = [record("meta_a", ["x"], ["x"])]
    report = compute(records)
    del report["retrieval"]["chunk_recall_at_k_micro"]

    rows = {row["check"]: row for row in compare(report, records)}

    assert rows["metric coverage"]["status"] == "FAIL"


def test_validator_imports_nothing_from_the_metrics_engine():
    """Path independence, enforced structurally.

    A shared helper, constant, or rounding rule would make a defect in it
    invisible to both paths — the single failure mode two derivations exist to
    exclude. `evaluation` absent from the imported roots is what makes the
    second path independent rather than a second call into the first.
    """
    import evaluation.retrieval_metrics_validator as validator

    assert imported_roots(validator) <= {"collections", "fractions"}


# ---------------------------------------------------------------------------
# Committed repository authorities
# ---------------------------------------------------------------------------


def test_committed_corpus_both_paths_agree(metrics, records):
    """Path A and Path B produce identical values for every metric."""
    assert flatten(metrics) == recompute(records)


def test_committed_corpus_validation_report_is_all_pass(metrics, records):
    """Every Work Package 4 check passes on the committed authorities."""
    rows = compare(metrics, records)

    assert [row["check"] for row in rows] == [
        "metric coverage",
        "independent derivation agreement",
        "record count integrity",
        "record classification integrity",
        "rate denominator integrity",
        "hit rate complement identity",
        "per-question row integrity",
    ]
    assert all(row["status"] == "PASS" for row in rows), rows


def test_committed_corpus_computation_is_deterministic(records, metrics):
    """Repeated computation over the same records yields an identical report."""
    assert compute(records) == metrics


def test_committed_corpus_metrics_are_reproducible(metrics):
    """Re-running the whole pipeline — retrieval, evaluation, metrics — reproduces
    the report exactly."""
    assert compute(evaluation_records()) == metrics


def test_committed_corpus_report_is_total(metrics, records):
    """Every question appears exactly once, and no metric is `None`."""
    assert len(metrics["per_question"]) == len(records)
    assert [row["id"] for row in metrics["per_question"]] == [r["id"] for r in records]
    assert all(value is not None for value in flatten(metrics).values())


def test_committed_corpus_classification_counts_are_exhaustive(metrics):
    """The four counts sum to the questions evaluated."""
    classification = metrics["classification"]
    counted = sum(
        classification[f"{field}_count"]
        for field in ("exact_match", "full_coverage", "partial_match", "no_match")
    )

    assert counted == classification["questions_evaluated"]


def test_committed_corpus_metrics_are_bounded(metrics):
    """Every rate and every metric lies in [0.0, 1.0].

    A value outside the unit interval would mean a numerator and denominator
    that do not describe the same population — the defect an independent
    derivation would agree with if both paths shared the mistake.
    """
    for name, value in flatten(metrics).items():
        if name.endswith("_rate") or "_at_k_" in name:
            assert 0.0 <= value <= 1.0, (name, value)

    for row in metrics["per_question"]:
        assert 0.0 <= row["chunk_precision_at_k"] <= 1.0
        assert 0.0 <= row["chunk_recall_at_k"] <= 1.0


def test_repository_authorities_are_byte_identical(records):
    """Measuring the repository modifies no repository authority."""
    before = authority_digests()

    report = compute(records)
    compare(report, records)

    assert authority_digests() == before
