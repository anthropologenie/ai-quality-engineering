"""Specification Family 5 — Retrieval Evaluation.

Sprint P3.3.2: executable specifications for the Retrieval Evaluation Engine
(`evaluation/retrieval_evaluation.py`) and its orchestrator
(`scripts/evaluate_retrieval.py`). These encode Work Package 5's validation
obligations — deterministic comparison, stable ordering, referential integrity,
exactly-once classification, and the mutual exclusivity and collective
exhaustiveness of the four categories — as permanent specifications rather than
a one-off execution.

Two kinds of specification, deliberately separated:

    synthetic  the classification algebra, over constructed chunk-id sets
    corpus     the committed repository authorities, evaluated end to end

The synthetic ones can state what the corpus happens not to exercise. The
committed corpus contains no Exact Match at HEAD, and a suite that only observed
the corpus would therefore never specify what an Exact Match *is* — leaving the
category untested precisely because retrieval currently never produces it.

No specification here asserts a retrieval outcome. `test_committed_corpus_*`
asserts that every question is classified exactly once and that the totals
account for all of them; none asserts that a particular question lands in a
particular category, because that is a fact about the current retrieval
implementation, not a property of the evaluation engine — and Sprint P3.3.1's
retriever is explicitly a Milestone 1A lexical stub whose behavior Milestone 2
is expected to change. Freezing today's classifications here would convert a
retrieval improvement into a test failure.

Observational only. Every specification below reads committed repository state
and writes nothing; `test_repository_authorities_are_byte_identical` is the
executable form of the Sprint P3.3.2 Repository Invariant.
"""

import itertools

import pytest

from evaluation.retrieval_evaluation import (
    CLASSIFICATIONS,
    EXACT_MATCH,
    FULL_COVERAGE,
    NO_MATCH,
    PARTIAL_MATCH,
    RetrievalEvaluationError,
    check_classification_totals,
    check_exhaustive_classification,
    check_referential_integrity,
    check_stable_ordering,
    classify,
    evaluate,
    evaluate_entry,
    run_validation_suite,
    summarize,
)
from scripts.evaluate_retrieval import (
    authority_digests,
    index_chunk_documents,
    load_expectations,
    observe,
)
from scripts.run_retrieval import load_corpus


@pytest.fixture(scope="module")
def corpus():
    """The committed Chunk Corpus, loaded through its own validation gate."""
    return load_corpus()


@pytest.fixture(scope="module")
def chunk_documents(corpus):
    """Chunk id to parent document id, over the committed corpus."""
    return index_chunk_documents(corpus)


@pytest.fixture(scope="module")
def expectations():
    """Expected retrieval, in Evidence Trace order."""
    return load_expectations()


@pytest.fixture(scope="module")
def observations(corpus):
    """Observed retrieval, produced by executing the Retrieval Runtime."""
    return observe(corpus)


@pytest.fixture(scope="module")
def evaluations(expectations, observations):
    """The evaluation of the committed corpus."""
    return evaluate(expectations, observations)


# ---------------------------------------------------------------------------
# Classification algebra (synthetic)
# ---------------------------------------------------------------------------


def test_exact_match_requires_set_equality():
    """O == E is Exact Match: every expected chunk, and nothing else."""
    assert classify({"a", "b"}, {"a", "b"}) == EXACT_MATCH


def test_exact_match_ignores_ordering():
    """Set semantics, not list semantics — the Work Package 2 Repository Decision.

    `expected_chunk` is ordered by ascending `chunk_index` and
    `retrieved_chunk_ids` by retrieval ranking; the two orderings are
    intentionally different, so identical membership in a different order is an
    Exact Match and not a disagreement.
    """
    evaluation = evaluate_entry("meta_synthetic", ["a", "b", "c"], ["c", "a", "b"])
    assert evaluation["classification"] == EXACT_MATCH
    assert evaluation["missing_chunk_ids"] == []
    assert evaluation["unexpected_chunk_ids"] == []


def test_full_coverage_is_a_proper_superset():
    """E ⊂ O is Full Coverage: all expected evidence, retrieved alongside noise."""
    assert classify({"a"}, {"a", "b", "c"}) == FULL_COVERAGE


def test_partial_match_has_overlap_and_a_gap():
    """E ∩ O ≠ ∅ with E ⊄ O is Partial Match: some evidence retrieved, some missing."""
    assert classify({"a", "b"}, {"a", "z"}) == PARTIAL_MATCH


def test_no_match_covers_disjoint_retrieval():
    """E ∩ O = ∅ with unrelated chunks retrieved is No Match.

    There is no separate "Unexpected Match" category; zero overlap is
    represented entirely by No Match regardless of what else was retrieved.
    """
    assert classify({"a"}, {"y", "z"}) == NO_MATCH


def test_no_match_covers_empty_retrieval():
    """Empty observed retrieval is the same zero-overlap case as unrelated retrieval."""
    assert classify({"a"}, set()) == NO_MATCH


def test_empty_expectation_is_refused():
    """The one input at which the four categories are not mutually exclusive.

    With `E = ∅` and empty observed retrieval, `O == E` (Exact Match) and
    `E ∩ O = ∅` (No Match) both hold. The Evidence Trace Dataset cannot produce
    such an entry — `scripts/build_evidence_trace.py` refuses to derive one and
    `validate_evidence_trace` rejects it on read — and the engine refuses it too
    rather than resolving the ambiguity by predicate ordering.
    """
    with pytest.raises(RetrievalEvaluationError, match="no expected chunk"):
        evaluate_entry("meta_synthetic", [], [])


def test_classifications_are_mutually_exclusive_and_exhaustive():
    """Every (expected, observed) pair over a fixed universe satisfies exactly one condition.

    Exhaustive over the subset pairs of a three-chunk universe — small enough to
    enumerate completely, large enough to contain every structural relationship
    the four categories distinguish (equality, proper superset, proper subset,
    partial overlap, disjointness, and empty observed retrieval). The conditions
    are restated here from the Work Package 3 definitions rather than imported,
    so the specification would still detect a change to the engine's own
    predicates.

    Expected sets are non-empty, which is the engine's domain and not a
    convenience: at `E = ∅` the Exact Match and No Match conditions are both
    true, so the categories partition every pair the Retrieval Expectation
    Authority can produce but not every pair expressible in Python.
    `test_empty_expectation_is_refused` specifies the boundary itself. Observed
    sets include the empty one — empty retrieval is reachable and is No Match.
    """
    universe = ("a", "b", "c")
    subsets = [
        set(combination)
        for size in range(len(universe) + 1)
        for combination in itertools.combinations(universe, size)
    ]

    for expected in (subset for subset in subsets if subset):
        for observed in subsets:
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
            assert holding == [classify(expected, observed)], (expected, observed, holding)


# ---------------------------------------------------------------------------
# Pairing and record structure (synthetic)
# ---------------------------------------------------------------------------


def test_every_entry_is_evaluated_exactly_once():
    """One evaluation per Evidence Trace entry, in Evidence Trace order."""
    expectations = [("meta_a", ["c1"]), ("meta_b", ["c2"])]
    observations = {"meta_a": ["c1"], "meta_b": ["c9"]}

    evaluations = evaluate(expectations, observations)

    assert [evaluation["id"] for evaluation in evaluations] == ["meta_a", "meta_b"]
    assert all(evaluation["classification"] in CLASSIFICATIONS for evaluation in evaluations)


def test_entry_without_an_observation_is_refused():
    """An unobserved entry is a broken execution, not a No Match.

    Classifying it would report that retrieval found no expected evidence, when
    in fact retrieval was never executed for that question.
    """
    with pytest.raises(RetrievalEvaluationError, match="No RetrievalResult was observed"):
        evaluate([("meta_a", ["c1"])], {})


def test_observation_without_an_entry_is_refused():
    """An observation with no Evidence Trace entry means the runtime ran over
    questions the expectation authority does not contain."""
    with pytest.raises(RetrievalEvaluationError, match="correspond to no Evidence Trace entry"):
        evaluate([("meta_a", ["c1"])], {"meta_a": ["c1"], "meta_b": ["c2"]})


def test_duplicate_entry_ids_are_refused():
    """An id evaluated twice would be counted twice in every aggregate total."""
    with pytest.raises(RetrievalEvaluationError, match="appear more than once"):
        evaluate([("meta_a", ["c1"]), ("meta_a", ["c2"])], {"meta_a": ["c1"]})


def test_evaluation_record_partitions_the_two_sets():
    """Matched, missing and unexpected partition expected ∪ observed with no remainder."""
    evaluation = evaluate_entry("meta_synthetic", ["a", "b"], ["b", "z"])

    assert evaluation["matched_chunk_ids"] == ["b"]
    assert evaluation["missing_chunk_ids"] == ["a"]
    assert evaluation["unexpected_chunk_ids"] == ["z"]
    assert evaluation["expected_count"] == 2
    assert evaluation["observed_count"] == 2
    assert evaluation["matched_count"] == 1


# ---------------------------------------------------------------------------
# Validation checks (synthetic negative cases)
# ---------------------------------------------------------------------------


def test_referential_integrity_rejects_an_unknown_expected_chunk():
    """An expected id absent from the corpus means the authorities have diverged."""
    evaluations = evaluate([("meta_a", ["ghost"])], {"meta_a": ["c1"]})
    with pytest.raises(RetrievalEvaluationError, match="expects chunk ids"):
        check_referential_integrity(evaluations, {"c1"})


def test_referential_integrity_rejects_an_unknown_observed_chunk():
    """An observed id absent from the corpus means retrieval returned a chunk
    the corpus does not contain."""
    evaluations = evaluate([("meta_a", ["c1"])], {"meta_a": ["ghost"]})
    with pytest.raises(RetrievalEvaluationError, match="observed chunk ids"):
        check_referential_integrity(evaluations, {"c1"})


def test_stable_ordering_rejects_an_unsorted_id_list():
    """A record whose id lists are not sorted is not reproducibly serializable."""
    expectations = [("meta_a", ["a", "b"])]
    evaluations = evaluate(expectations, {"meta_a": ["a", "b"]})
    evaluations[0]["observed_chunk_ids"] = ["b", "a"]

    with pytest.raises(RetrievalEvaluationError, match="not in stable order"):
        check_stable_ordering(evaluations, expectations)


def test_stable_ordering_rejects_reordered_evaluations():
    """Evaluation order must follow Evidence Trace order so the two can be read together."""
    expectations = [("meta_a", ["c1"]), ("meta_b", ["c2"])]
    evaluations = evaluate(expectations, {"meta_a": ["c1"], "meta_b": ["c2"]})

    with pytest.raises(RetrievalEvaluationError, match="does not follow Evidence Trace order"):
        check_stable_ordering(list(reversed(evaluations)), expectations)


def test_exhaustive_classification_rejects_a_mislabelled_record():
    """A classification inconsistent with the record's own sets is refused.

    The check re-derives the four conditions from `expected_chunk_ids` and
    `observed_chunk_ids` rather than trusting the stored label, which is what
    lets it catch this.
    """
    evaluations = evaluate([("meta_a", ["c1"])], {"meta_a": ["c1"]})
    evaluations[0]["classification"] = NO_MATCH

    with pytest.raises(RetrievalEvaluationError, match="satisfies the"):
        check_exhaustive_classification(evaluations)


def test_classification_totals_reject_a_summary_that_loses_a_question():
    """Category totals must sum to the question count — exhaustiveness, in aggregate."""
    evaluations = evaluate([("meta_a", ["c1"])], {"meta_a": ["c1"]})
    summary = summarize(evaluations, {"c1": "doc"})
    summary["exact_match"] = 0

    with pytest.raises(RetrievalEvaluationError, match="Classification totals sum to"):
        check_classification_totals(evaluations, summary)


# ---------------------------------------------------------------------------
# Committed repository authorities
# ---------------------------------------------------------------------------


def test_committed_corpus_evaluates_every_evidence_trace_entry(evaluations, expectations):
    """Every Evidence Trace entry is evaluated against exactly one RetrievalResult."""
    assert len(evaluations) == len(expectations)
    assert [evaluation["id"] for evaluation in evaluations] == [
        entry_id for entry_id, _ in expectations
    ]


def test_committed_corpus_classification_is_exhaustive(evaluations, chunk_documents):
    """Every question receives exactly one of the four categories, and the totals
    account for all of them."""
    check_exhaustive_classification(evaluations)

    summary = summarize(evaluations, chunk_documents)
    check_classification_totals(evaluations, summary)
    assert summary["questions_evaluated"] == len(evaluations)


def test_committed_corpus_evaluation_is_deterministic(expectations, observations):
    """Repeated evaluation of identical inputs yields identical evaluations.

    Determinism as the repository defines it elsewhere (tests/conftest.py):
    repeated construction yields equal values — not a frozen literal digest of
    one corpus snapshot.
    """
    assert evaluate(expectations, observations) == evaluate(expectations, observations)


def test_committed_corpus_retrieval_is_deterministic(corpus):
    """Re-executing the Retrieval Runtime observes the same retrieval.

    The evaluation can only be reproducible if its observed input is; this
    specifies the half of reproducibility that lives upstream of the engine.
    """
    assert observe(corpus) == observe(corpus)


def test_committed_corpus_referential_integrity(evaluations, chunk_documents):
    """Every expected and observed chunk id exists in the committed Chunk Corpus."""
    check_referential_integrity(evaluations, set(chunk_documents))


def test_committed_corpus_validation_suite_passes(
    evaluations, expectations, observations, chunk_documents
):
    """The full Work Package 5 validation report is PASS on every check."""
    summary = summarize(evaluations, chunk_documents)
    report = run_validation_suite(
        evaluations, expectations, observations, chunk_documents, summary
    )

    assert [entry["check"] for entry in report] == [
        "determinism",
        "stable ordering",
        "referential integrity",
        "exhaustive classification",
        "classification totals",
    ]
    assert all(entry["status"] == "PASS" for entry in report), report


def test_summary_document_distributions_cover_the_committed_corpus(evaluations, chunk_documents):
    """Both distributions are keyed only by documents the Knowledge Manifest catalogues.

    A distribution key is a `document_id`, which the Chunk Corpus inherits from
    the Knowledge Manifest; a key outside that set would mean the summary is
    describing a document the corpus does not have.
    """
    summary = summarize(evaluations, chunk_documents)
    catalogued = set(chunk_documents.values())

    for field in ("expected_document_distribution", "observed_document_distribution"):
        assert set(summary[field]) <= catalogued
        assert list(summary[field]) == sorted(summary[field])


def test_repository_authorities_are_byte_identical(corpus):
    """The Repository Invariant: evaluation modifies no repository authority.

    Digests are taken around a full evaluation — corpus load, runtime execution,
    comparison, summary and validation — so this specifies the whole path rather
    than the engine alone.
    """
    before = authority_digests()

    expectations = load_expectations()
    observations = observe(corpus)
    chunk_documents = index_chunk_documents(corpus)
    evaluations = evaluate(expectations, observations)
    summary = summarize(evaluations, chunk_documents)
    run_validation_suite(evaluations, expectations, observations, chunk_documents, summary)

    assert authority_digests() == before
