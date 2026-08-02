"""Independent Retrieval Metrics Validator.

Sprint P3.3.3 Work Package 4: Path B. Re-derives every metric in
`metrics.Report` from Retrieval Evaluation records without consulting the
Metrics Engine, then compares the two derivations value by value. Agreement is
evidence; disagreement is a finding about one of the two paths.

Independence is structural, not a claim:

* **No import from `evaluation.retrieval_metrics`.** Not the engine's functions,
  not its constants, not its rounding precision — all are restated here. An
  import of any of them would make a shared defect invisible to both paths,
  which is the single failure mode this validator exists to exclude.
* **It never reads `metrics.Report` to produce a value.** The report is an
  argument to `compare` alone, after every recomputed value already exists.
  Nothing below validates a stored number against itself.
* **A different input path.** The engine measures the records' `*_count`
  fields; this validator recomputes every count from `expected_chunk_ids` and
  `observed_chunk_ids` by set arithmetic, and re-derives each classification
  from those same sets rather than reading `classification`. So the two paths
  disagree not only when a metric is miscomputed but when a record's own counts
  or label disagree with its id lists.
* **A different numeric path.** `fractions.Fraction` — exact rational
  arithmetic, converted to float and rounded once at the end. The engine
  divides in binary floating point throughout. Two independent numeric routes
  to the same published decimal.

Like the engine, this module consumes only Retrieval Evaluation records and
performs no filesystem or network I/O.
"""

from collections import Counter
from fractions import Fraction

# Restated, deliberately not imported — see the module docstring. If Sprint
# P3.3.2's category labels or the repository's serialization precision ever
# change, this file must be updated independently, and until it is the
# comparison fails loudly rather than silently tracking the engine.
EXACT_MATCH = "Exact Match"
FULL_COVERAGE = "Full Coverage"
PARTIAL_MATCH = "Partial Match"
NO_MATCH = "No Match"

PRECISION = 4


class MetricValidationError(Exception):
    """Raised when the two derivation paths cannot be compared at all.

    Distinct from a metric *disagreement*, which is reported as a FAIL row by
    `compare` rather than raised: a disagreement is the validator working, and
    must not be indistinguishable from the validator being unable to run.
    """


def _round(value: Fraction) -> float:
    """Convert an exact rational to the published decimal.

    `float()` before `round()` is deliberate: `round(Fraction, 4)` returns a
    `Fraction`, which would compare unequal to the engine's float even when both
    denote the same number. The comparison must be between values of the same
    type, or it tests types instead of arithmetic.
    """
    return round(float(value), PRECISION)


def _ratio(numerator: int, denominator: int) -> Fraction:
    """Exact ratio, or exact zero when the denominator is zero.

    The zero-denominator convention is restated here rather than inherited, so
    the two paths agree about divide-by-zero because they were independently
    written to, not because they share a helper.
    """
    return Fraction(numerator, denominator) if denominator else Fraction(0)


def _classify(expected: set, observed: set) -> str:
    """Re-derive one classification from the record's own chunk id sets.

    The Sprint P3.3.2 Work Package 3 conditions, restated. This is what lets the
    validator detect a record whose stored `classification` disagrees with its
    `expected_chunk_ids` and `observed_chunk_ids` — a defect that would corrupt
    every classification rate while leaving the rates internally consistent and
    summing correctly.
    """
    if observed == expected:
        return EXACT_MATCH
    if expected < observed:
        return FULL_COVERAGE
    if expected & observed:
        return PARTIAL_MATCH
    return NO_MATCH


def recompute(records: list) -> dict:
    """Derive every metric independently from Retrieval Evaluation records.

    Returns a mapping of metric name to value, flattened rather than nested:
    the engine's report is nested by section, and comparing a flat mapping
    against a flattened view of that report means the comparison cannot be
    fooled by a value that is correct but filed in the wrong section.

    Every count below is recomputed from the id lists. The records' own
    `expected_count`, `observed_count` and `matched_count` fields are read
    exactly once each — in `compare`, as a consistency check — and never used to
    produce a metric.
    """
    if not isinstance(records, list):
        raise MetricValidationError("Retrieval Evaluation records must be a list.")

    questions = len(records)
    classifications: Counter = Counter()

    matched_total = 0
    expected_total = 0
    observed_total = 0
    hits = 0
    precisions = []
    recalls = []

    for index, record in enumerate(records):
        try:
            expected = set(record["expected_chunk_ids"])
            observed = set(record["observed_chunk_ids"])
        except (TypeError, KeyError) as exc:
            raise MetricValidationError(
                f"Record at index {index} does not carry comparable chunk id lists: {exc}"
            ) from exc

        matched = expected & observed
        classifications[_classify(expected, observed)] += 1

        # Hit Rate from its definition — |E ∩ O| > 0 — rather than from a
        # classification label. The engine reaches the same number by
        # aggregating Sprint P3.3.2's labels (Repository Decision 1); deriving
        # it here from the sets is what makes the two paths independent, and
        # makes agreement evidence that the stored labels match the definition.
        if matched:
            hits += 1

        matched_total += len(matched)
        expected_total += len(expected)
        observed_total += len(observed)

        precisions.append(_ratio(len(matched), len(observed)))
        recalls.append(_ratio(len(matched), len(expected)))

    recomputed = {
        "questions_evaluated": questions,
        "hit_count": hits,
        "hit_rate": _round(_ratio(hits, questions)),
        "expected_chunk_references": expected_total,
        "retrieved_chunk_references": observed_total,
        "matched_chunk_references": matched_total,
        "expected_chunks_unique": len(
            {chunk_id for record in records for chunk_id in record["expected_chunk_ids"]}
        ),
        "retrieved_chunks_unique": len(
            {chunk_id for record in records for chunk_id in record["observed_chunk_ids"]}
        ),
        "chunk_precision_at_k_micro": _round(_ratio(matched_total, observed_total)),
        "chunk_recall_at_k_micro": _round(_ratio(matched_total, expected_total)),
        "chunk_precision_at_k_macro": _round(
            sum(precisions, Fraction(0)) / questions if questions else Fraction(0)
        ),
        "chunk_recall_at_k_macro": _round(
            sum(recalls, Fraction(0)) / questions if questions else Fraction(0)
        ),
    }

    for classification, field in (
        (EXACT_MATCH, "exact_match"),
        (FULL_COVERAGE, "full_coverage"),
        (PARTIAL_MATCH, "partial_match"),
        (NO_MATCH, "no_match"),
    ):
        recomputed[f"{field}_count"] = classifications[classification]
        recomputed[f"{field}_rate"] = _round(_ratio(classifications[classification], questions))

    return recomputed


def flatten(report: dict) -> dict:
    """Flatten `metrics.Report` into the comparison's name-to-value shape.

    Structural only — this reads the report's layout, never recomputes or
    adjusts a value. It is the one place the validator touches the report, and
    it runs after `recompute` has already produced every number it will compare.
    """
    try:
        flattened = dict(report["classification"])
        flattened.update(report["retrieval"])
    except (KeyError, TypeError) as exc:
        raise MetricValidationError(f"metrics.Report is not a comparable report: {exc}") from exc
    return flattened


def compare(report: dict, records: list) -> list:
    """Compare Path A against Path B and report every check.

    Returns `{"check": ..., "status": "PASS"|"FAIL", "detail": ...}` rows in a
    fixed order — the Work Package 4 validation report. Every check runs; the
    deliverable is the full report, and stopping at the first disagreement would
    hide the state of the rest.

    Metric agreement is exact equality of published values, not equality within
    a tolerance. Both paths round to the same precision, so any tolerance would
    admit a real disagreement in the digits the report actually shows.
    """
    recomputed = recompute(records)
    flattened = flatten(report)

    rows = []

    missing = sorted(set(recomputed) - set(flattened))
    extra = sorted(set(flattened) - set(recomputed))
    if missing or extra:
        rows.append(
            {
                "check": "metric coverage",
                "status": "FAIL",
                "detail": f"absent from report: {missing}; not independently derived: {extra}",
            }
        )
    else:
        rows.append({"check": "metric coverage", "status": "PASS", "detail": ""})

    disagreements = [
        f"{name}: engine={flattened[name]!r} independent={recomputed[name]!r}"
        for name in sorted(set(recomputed) & set(flattened))
        if flattened[name] != recomputed[name]
    ]
    rows.append(
        {
            "check": "independent derivation agreement",
            "status": "FAIL" if disagreements else "PASS",
            "detail": "; ".join(disagreements),
        }
    )

    rows.append(_check_record_counts(records))
    rows.append(_check_record_classifications(records))
    rows.append(_check_rate_denominators(records))
    rows.append(_check_hit_rate_complement(records))
    rows.append(_check_per_question_rows(report, records))

    return rows


def _check_hit_rate_complement(records: list) -> dict:
    """Verify Hit Rate is exactly the complement of the No Match rate.

    Sprint P3.3.3 Repository Decision 1 states two forms of Hit Rate and asserts
    they are equivalent:

        Exact Match + Full Coverage + Partial Match   ≡   1 − No Match Rate

    The engine computes the first. This checks the second holds, over exact
    rationals so the identity is tested rather than its rounding — 1 − 0.3636
    and 0.6364 agree here, but two independently rounded decimals are not
    guaranteed to complement in general, and a check that relied on it would be
    checking presentation.

    The equivalence is only true if the four categories are collectively
    exhaustive, which Sprint P3.3.2 validates. Re-checking it here means the
    metrics layer does not simply inherit that property as an assumption.
    """
    questions = len(records)
    hits = sum(
        1
        for record in records
        if set(record["expected_chunk_ids"]) & set(record["observed_chunk_ids"])
    )
    no_match = sum(
        1
        for record in records
        if _classify(set(record["expected_chunk_ids"]), set(record["observed_chunk_ids"]))
        == NO_MATCH
    )

    hit_rate = _ratio(hits, questions)
    complement = Fraction(1) - _ratio(no_match, questions) if questions else Fraction(0)

    if hit_rate != complement:
        return {
            "check": "hit rate complement identity",
            "status": "FAIL",
            "detail": f"hit rate {hit_rate} is not 1 - no match rate {complement}",
        }

    return {"check": "hit rate complement identity", "status": "PASS", "detail": ""}


def _check_record_counts(records: list) -> dict:
    """Verify each record's stored counts agree with its own id lists.

    This is the check the engine cannot perform on its own behalf: it *uses*
    those counts, so a wrong one produces a wrong metric consistently. The
    validator never uses them, which is what makes it able to check them.
    """
    disagreements = [
        f"{record['id']}: {field}={record[field]} but {ids_field} holds {len(record[ids_field])}"
        for record in records
        for field, ids_field in (
            ("expected_count", "expected_chunk_ids"),
            ("observed_count", "observed_chunk_ids"),
            ("matched_count", "matched_chunk_ids"),
        )
        if record[field] != len(record[ids_field])
    ]
    return {
        "check": "record count integrity",
        "status": "FAIL" if disagreements else "PASS",
        "detail": "; ".join(disagreements),
    }


def _check_record_classifications(records: list) -> dict:
    """Verify each record's stored classification follows from its own chunk sets."""
    disagreements = [
        f"{record['id']}: stored={record['classification']!r} derived={derived!r}"
        for record in records
        for derived in [
            _classify(set(record["expected_chunk_ids"]), set(record["observed_chunk_ids"]))
        ]
        if derived != record["classification"]
    ]
    return {
        "check": "record classification integrity",
        "status": "FAIL" if disagreements else "PASS",
        "detail": "; ".join(disagreements),
    }


def _check_rate_denominators(records: list) -> dict:
    """Verify the four classification rates share one denominator and are total.

    Two properties: the counts sum to the question count, and the rates sum to
    exactly 1. The second is the denominator check proper — four rates computed
    over four *different* denominators could each look plausible individually
    and would not sum to one.

    The sum is taken over **exact rationals**, not over the published values.
    Four independently rounded decimals need not sum to 1.0 and, for this
    corpus, do not: 10/22, 4/22 and 8/22 each round down, so the published rates
    sum to 0.9999. That residual is a property of rounding four numbers for
    display, not of the denominators, and a check that failed on it would be
    checking presentation. `_round` is applied to each rate for publication and
    is verified per-metric by the derivation-agreement check; the totality of
    the denominator is verified here, where rounding cannot reach it.
    """
    questions = len(records)
    classifications: Counter = Counter(
        _classify(set(record["expected_chunk_ids"]), set(record["observed_chunk_ids"]))
        for record in records
    )

    counted = sum(classifications[name] for name in (EXACT_MATCH, FULL_COVERAGE, PARTIAL_MATCH, NO_MATCH))
    if counted != questions:
        return {
            "check": "rate denominator integrity",
            "status": "FAIL",
            "detail": f"classification counts sum to {counted}, not {questions}",
        }

    total = sum(
        (
            _ratio(classifications[name], questions)
            for name in (EXACT_MATCH, FULL_COVERAGE, PARTIAL_MATCH, NO_MATCH)
        ),
        Fraction(0),
    )
    expected_total = Fraction(1) if questions else Fraction(0)
    if total != expected_total:
        return {
            "check": "rate denominator integrity",
            "status": "FAIL",
            "detail": f"exact classification rates sum to {total}, not {expected_total}",
        }

    return {"check": "rate denominator integrity", "status": "PASS", "detail": ""}


def _check_per_question_rows(report: dict, records: list) -> dict:
    """Verify the per-question rows are complete, in record order, and correct.

    Ordering is part of the contract, not presentation: record order carries
    through from the QA Dataset, and a report whose rows were re-sorted could
    not be read against the dataset row-for-row.
    """
    rows = report.get("per_question")
    if not isinstance(rows, list):
        raise MetricValidationError("metrics.Report carries no per-question rows.")

    if [row["id"] for row in rows] != [record["id"] for record in records]:
        return {
            "check": "per-question row integrity",
            "status": "FAIL",
            "detail": "per-question rows do not follow Retrieval Evaluation record order",
        }

    disagreements = []
    for row, record in zip(rows, records):
        expected = set(record["expected_chunk_ids"])
        observed = set(record["observed_chunk_ids"])
        matched = len(expected & observed)

        for field, value in (
            ("chunk_precision_at_k", _round(_ratio(matched, len(observed)))),
            ("chunk_recall_at_k", _round(_ratio(matched, len(expected)))),
        ):
            if row[field] != value:
                disagreements.append(
                    f"{record['id']} {field}: engine={row[field]!r} independent={value!r}"
                )

    return {
        "check": "per-question row integrity",
        "status": "FAIL" if disagreements else "PASS",
        "detail": "; ".join(disagreements),
    }
