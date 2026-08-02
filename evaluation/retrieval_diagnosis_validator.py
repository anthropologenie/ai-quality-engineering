"""Independent Retrieval Diagnosis Validator.

Sprint P3.3.4 Work Package 8: a second, separately-authored derivation of the
same diagnoses, written against `docs/altm.md` directly rather than against the
Diagnosis Engine. Agreement demonstrates that two independent applications of the
documented rules reach the same conclusion — consistent application of repository
rules, not shared implementation logic.

Independence, and its one deliberate exception
----------------------------------------------
* **No import of `evaluation.retrieval_diagnosis`.** Not its rule-selection, its
  confidence assessment, its constants, or its record shape. Enforced
  structurally by an AST allowlist specification.
* **It never reads the engine's diagnoses to produce one.** They are an argument
  to `compare` alone, after every independent diagnosis already exists.
* **A different derivation path.** The engine reads `chunk_recall_at_k` and
  `chunk_precision_at_k` from the Retrieval Metrics report. This validator
  recomputes both from the evaluation records' chunk id sets and uses its own
  values, consulting the metrics report only to confirm the two agree. So a
  disagreement surfaces not just when a rule is misapplied but when the metrics
  report and the evaluation records have drifted apart.
* **A different rule-selection shape.** The engine returns early from an ordered
  chain; this validator builds the full list of §5 rows whose symptom the
  evidence exhibits and then takes the first in document order. Reaching the same
  answer by enumeration rather than by short-circuit is what makes the ordering
  itself independently verified.

**The exception:** both paths import `evaluation.altm_rules`. That module is a
transcription of `docs/altm.md` §5, not engine logic — it is the *authority*, and
Work Package 8 asks the two implementations to apply the same documented rules.
Two separate transcriptions would test whether they were copied identically, not
whether the rules were applied consistently.
"""

from collections import Counter

from evaluation.altm_rules import FAILURE_LOCALIZATION_MATRIX, REACHABLE_STAGES

# Restated, deliberately not imported from the engine.
COMPLETE = "Complete Evidence"
PARTIAL = "Partial Evidence"
INSUFFICIENT = "Insufficient Evidence"

PRECISION = 4


class DiagnosisValidationError(Exception):
    """Raised when the two derivations cannot be compared at all.

    Distinct from a diagnosis *disagreement*, which `compare` reports as a FAIL
    row: a disagreement is the validator working, and must not be
    indistinguishable from the validator being unable to run.
    """


def _ratio(numerator: int, denominator: int) -> float:
    """Coverage ratio at the repository's published precision, zero-safe."""
    return round(numerator / denominator, PRECISION) if denominator else 0.0


def _matching_rules(
    recall: float, precision: float, expected_documents: list, observed_documents: list
) -> list:
    """Every §5 row whose symptom this evidence exhibits, in document order.

    Enumerated rather than short-circuited. The engine selects by falling through
    an ordered chain; building the complete match list here and taking its first
    element verifies both that the same row is chosen and that `docs/altm.md`
    §5's row order is what chooses it.

    The Knowledge rows are still not considered, and Sprint P3.3.5's document
    identity is why that is now demonstrable rather than assumed:
    ALTM-KNOWLEDGE-1 needs which *version* is current, which no permitted input
    carries; ALTM-KNOWLEDGE-2's documented detection is that re-indexing was
    triggered, and a non-empty `expected_document_ids` shows it was. The
    Assemble/Infer/Post-Process/Evaluate/Final-Answer rows name components this
    repository does not implement.

    Derived independently of the engine's ordered chain: `document_mismatch` is
    computed here from the two document lists rather than read from any
    engine-produced value.
    """
    document_identity = bool(expected_documents) and observed_documents is not None
    document_mismatch = document_identity and not (
        set(expected_documents) & set(observed_documents)
    )

    exhibits = {
        # "Right topic, wrong specific document retrieved" — reachable only once
        # document identity exists (Sprint P3.3.5).
        "ALTM-RETRIEVE-1": recall == 0.0 and document_mismatch,
        # "Missing answer despite evidence existing in the corpus". The premise
        # holds by Sprint P3.3.2's validated referential integrity.
        "ALTM-RETRIEVE-2": recall == 0.0 and not document_mismatch,
        "ALTM-RETRIEVE-3": 0.0 < recall < 1.0,
        "ALTM-RETRIEVE-4": recall == 1.0 and precision < 1.0,
    }

    return [
        rule["rule_id"]
        for rule in FAILURE_LOCALIZATION_MATRIX
        if exhibits.get(rule["rule_id"], False)
    ]


def _confidence(recall: float, expected_documents: list) -> str:
    """Evidence completeness, derived from what the observation itself excludes.

    Restated from `docs/altm.md` §7 (rule out upstream before attributing
    downstream) and §10 Principle 2 (a Knowledge failure makes every downstream
    stage look wrong), not copied from the engine:

    * Full recall means every expected chunk was retrieved, so the corpus held it
      and the index produced it — Knowledge and Index are excluded by the
      observation, leaving nothing upstream unresolved.
    * Partial recall excludes Knowledge and Index for the chunks that *were*
      retrieved but not for those that were not.
    * Zero recall excludes nothing upstream, and ALTM-KNOWLEDGE-2 ("Stale answer
      despite a recent source update") remains equally consistent with the
      observation while being unverifiable from the permitted inputs.

    Sprint P3.3.5 supersedes all three whenever document identity is present: a
    non-empty `expected_document_ids` shows the expected document is in the
    corpus and indexed, which is what the Knowledge check tests, and Sprint
    P3.3.2's validated referential integrity shows its chunks exist, which is
    what the Index check tests. Both upstream stages are then excluded on
    evidence regardless of recall, leaving the Retrieve attribution complete.
    """
    if expected_documents:
        return COMPLETE
    if recall == 0.0:
        return INSUFFICIENT
    if recall < 1.0:
        return PARTIAL
    return COMPLETE


def rederive(records: list, metrics: dict) -> dict:
    """Independently derive every diagnosis from evaluation records and ALTM rules.

    Returns `question id -> (rule_id, stage, confidence)`. A question exhibiting
    no symptom is absent from the mapping, which is how "no diagnosis" is
    represented without inventing a record for it.

    Recall and precision are recomputed here from the records' own chunk id sets.
    The metrics report is not consulted for them — `_check_metric_agreement` reads
    it separately, so this derivation stands on the evaluation records alone.
    """
    if not isinstance(records, list):
        raise DiagnosisValidationError("Retrieval Evaluation records must be a list.")

    derived = {}
    for index, record in enumerate(records):
        try:
            expected = set(record["expected_chunk_ids"])
            observed = set(record["observed_chunk_ids"])
        except (TypeError, KeyError) as exc:
            raise DiagnosisValidationError(
                f"Record at index {index} does not carry comparable chunk id lists: {exc}"
            ) from exc

        matched = expected & observed
        recall = _ratio(len(matched), len(expected))
        precision = _ratio(len(matched), len(observed))

        expected_documents = record.get("expected_document_ids", [])
        observed_documents = record.get("observed_document_ids", [])

        matching = _matching_rules(recall, precision, expected_documents, observed_documents)
        if not matching:
            continue

        rule_id = matching[0]
        stages = [
            rule["stages"] for rule in FAILURE_LOCALIZATION_MATRIX if rule["rule_id"] == rule_id
        ][0]
        reachable = [stage for stage in stages if stage in REACHABLE_STAGES]

        if len(reachable) != 1:
            raise DiagnosisValidationError(
                f"Rule {rule_id!r} does not resolve to exactly one reachable stage."
            )

        derived[record["id"]] = (rule_id, reachable[0], _confidence(recall, expected_documents))

    return derived


def compare(diagnoses: list, records: list, metrics: dict) -> list:
    """Compare the engine's diagnoses against the independent derivation.

    Returns `{"check": ..., "status": "PASS"|"FAIL", "detail": ...}` rows in a
    fixed order — the Work Package 8 validation report. Every check runs; the
    deliverable is the full report, and stopping at the first disagreement would
    hide the state of the rest.
    """
    derived = rederive(records, metrics)
    engine = {d["id"]: (d["rule_id"], d["altm_stage"], d["diagnosis_confidence"]) for d in diagnoses}

    rows = []

    only_engine = sorted(set(engine) - set(derived))
    only_derived = sorted(set(derived) - set(engine))
    rows.append(
        {
            "check": "diagnosis coverage",
            "status": "FAIL" if (only_engine or only_derived) else "PASS",
            "detail": (
                f"diagnosed only by engine: {only_engine}; "
                f"only by independent derivation: {only_derived}"
                if (only_engine or only_derived)
                else ""
            ),
        }
    )

    rows.append(_compare_field(engine, derived, 0, "rule consistency"))
    rows.append(_compare_field(engine, derived, 1, "stage consistency"))
    rows.append(_compare_field(engine, derived, 2, "confidence consistency"))
    rows.append(_check_metric_agreement(records, metrics))
    rows.append(_check_unreachable_stages_absent(diagnoses))
    rows.append(_check_one_diagnosis_per_question(diagnoses, records))
    rows.append(_check_document_identity(records))

    return rows


def _check_document_identity(records: list) -> dict:
    """Verify Sprint P3.3.5's document identity is present, ordered, and coherent.

    Three properties, each guarding a way the enrichment could be wrong rather
    than absent:

    * **Sorted** — the same ordering obligation every id list in an evaluation
      record carries; an unsorted list would make the record's serialization
      depend on set iteration.
    * **Expected non-empty** — every evaluated question expects at least one
      chunk (Sprint P3.3.2's enforced domain), so every question must resolve to
      at least one expected document. An empty list would silently return the
      whole diagnosis layer to its pre-P3.3.5 behaviour, since absent identity is
      exactly what the fallback path keys on.
    * **Overlap implies document overlap** — a question with matched chunks must
      have intersecting document sets, because a matched chunk belongs to a
      document on both sides. This is the check that would catch two independently
      derived lists that do not describe the same retrieval.

    Records predating the enrichment are skipped rather than failed: they are
    diagnosable under the pre-P3.3.5 path, and a specification's synthetic record
    is not a defect in the corpus.
    """
    problems = []

    for record in records:
        if "expected_document_ids" not in record or "observed_document_ids" not in record:
            continue

        expected = record["expected_document_ids"]
        observed = record["observed_document_ids"]

        if expected != sorted(expected) or observed != sorted(observed):
            problems.append(f"{record['id']}: document ids are not in stable order")

        if record["expected_chunk_ids"] and not expected:
            problems.append(f"{record['id']}: expects chunks but resolves to no document")

        if record["matched_chunk_ids"] and not set(expected) & set(observed):
            problems.append(
                f"{record['id']}: has matched chunks but disjoint document sets"
            )

    return {
        "check": "document identity integrity",
        "status": "FAIL" if problems else "PASS",
        "detail": "; ".join(problems),
    }


def _compare_field(engine: dict, derived: dict, position: int, name: str) -> dict:
    """Compare one element of the diagnosis triple across both derivations."""
    disagreements = [
        f"{question}: engine={engine[question][position]!r} "
        f"independent={derived[question][position]!r}"
        for question in sorted(set(engine) & set(derived))
        if engine[question][position] != derived[question][position]
    ]
    return {
        "check": name,
        "status": "FAIL" if disagreements else "PASS",
        "detail": "; ".join(disagreements),
    }


def _check_metric_agreement(records: list, metrics: dict) -> dict:
    """Verify the metrics report agrees with the evaluation records it describes.

    The engine diagnoses from the metrics report's per-question values; this
    validator diagnoses from values recomputed off the records. Both paths are
    only comparable if those two sources agree, so the agreement is checked
    explicitly rather than assumed — and a drift between the two upstream layers
    is reported here rather than surfacing as an unexplained diagnosis mismatch.
    """
    rows = {row["id"]: row for row in metrics.get("per_question", [])}
    disagreements = []

    for record in records:
        row = rows.get(record["id"])
        if row is None:
            disagreements.append(f"{record['id']}: no metric row")
            continue

        expected = set(record["expected_chunk_ids"])
        observed = set(record["observed_chunk_ids"])
        matched = expected & observed

        for field, value in (
            ("chunk_recall_at_k", _ratio(len(matched), len(expected))),
            ("chunk_precision_at_k", _ratio(len(matched), len(observed))),
        ):
            if row[field] != value:
                disagreements.append(
                    f"{record['id']} {field}: metrics={row[field]!r} records={value!r}"
                )

    return {
        "check": "metric/record agreement",
        "status": "FAIL" if disagreements else "PASS",
        "detail": "; ".join(disagreements),
    }


def _check_unreachable_stages_absent(diagnoses: list) -> dict:
    """Verify no diagnosis names a stage this repository does not implement.

    Work Package 5 bars Assemble, Infer, Post-Process, Evaluate and Final Answer
    outright: no generation pipeline exists, so no evidence could support one.
    """
    offending = [
        f"{d['id']}: {d['altm_stage']}"
        for d in diagnoses
        if d["altm_stage"] not in REACHABLE_STAGES
    ]
    return {
        "check": "unreachable stages absent",
        "status": "FAIL" if offending else "PASS",
        "detail": "; ".join(offending),
    }


def _check_one_diagnosis_per_question(diagnoses: list, records: list) -> dict:
    """Verify each question received at most one diagnosis, and none is unknown.

    `docs/altm.md` §10 Principle 1 — one failure has one primary origin — is the
    invariant; a question diagnosed twice would appear twice in every stage count.
    """
    counts = Counter(d["id"] for d in diagnoses)
    known = {record["id"] for record in records}

    problems = [f"{qid}: {n} diagnoses" for qid, n in sorted(counts.items()) if n > 1]
    problems += [f"{qid}: not an evaluated question" for qid in sorted(set(counts) - known)]

    return {
        "check": "one diagnosis per question",
        "status": "FAIL" if problems else "PASS",
        "detail": "; ".join(problems),
    }
