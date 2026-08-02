"""Deterministic Retrieval Diagnosis Engine.

Sprint P3.3.4: applies the documented ALTM rules in `docs/altm.md` to the
completed Retrieval Evaluation records and Retrieval Metrics report, and
explains the retrieval behaviour those layers measured. It is the last
analytical layer of Milestone 1A.

Explanation only. Nothing here computes a metric, re-runs retrieval, re-derives
an evaluation, or recommends a change. Every diagnosis is the application of one
prose rule already written in `docs/altm.md` §5 to evidence already committed
upstream — never a judgement invented in this file.

Inputs, and the only inputs permitted:

    Retrieval Evaluation records   (Sprint P3.3.2)
    Retrieval Metrics report       (Sprint P3.3.3)
    evaluation/altm_rules.py       (docs/altm.md §5, transcribed)

Structurally read-only: this module performs no filesystem and no network I/O,
and imports nothing from `sample_rag/`, `scripts/`, or the evaluation and
metrics engines — only the rule transcription. It cannot reach `RetrievalResult`,
the Chunk Corpus, the Evidence Trace Dataset, or the Knowledge Manifest, which is
the Sprint P3.3.4 dependency rule enforced rather than asserted.

What this engine cannot see, and why it matters
-----------------------------------------------
Retrieval Evaluation records carry chunk identity only — no document identity
(the limitation Sprint P3.3.3 recorded when deferring Document Recall). The
Knowledge-stage rules ALTM-KNOWLEDGE-1 and ALTM-KNOWLEDGE-2 both turn on *which
document version* was returned, and their documented detection metric is a
freshness check against the source. Neither is derivable from the permitted
inputs, so neither can ever fire here. That is recorded in every affected
diagnosis through `diagnosis_confidence`, not worked around — see
`assess_confidence`.
"""

from collections import Counter

from evaluation.altm_rules import REACHABLE_STAGES, RULES_BY_ID, reachable_stage

# Sprint P3.3.4 Work Package 6. Evidence completeness only: whether the
# repository holds enough committed evidence to support one diagnosis uniquely.
# Explicitly not a probability, a statistical confidence, a model confidence, or
# a heuristic certainty — no such quantity is computed anywhere in this sprint.
COMPLETE_EVIDENCE = "Complete Evidence"
PARTIAL_EVIDENCE = "Partial Evidence"
INSUFFICIENT_EVIDENCE = "Insufficient Evidence"

CONFIDENCE_VALUES = (COMPLETE_EVIDENCE, PARTIAL_EVIDENCE, INSUFFICIENT_EVIDENCE)

# The classification Sprint P3.3.2 assigns when retrieval returned exactly the
# expected chunks. Such a question exhibits no failure, so ALTM has nothing to
# localize for it and no diagnosis is emitted (`docs/altm.md` §5 is a lookup from
# an *observed symptom*; absent a symptom there is no row to apply).
EXACT_MATCH = "Exact Match"


class RetrievalDiagnosisError(Exception):
    """Raised when upstream outputs cannot be diagnosed.

    An eighth independent, flat exception type, following the repository's
    per-responsibility pattern (`ManifestValidationError`, `ChunkConstructionError`,
    `ChunkSerializationError`, `ChunkValidationError`, `EvidenceTraceError`,
    `RetrievalEvaluationError`, `RetrievalMetricsError`) — a direct `Exception`
    subclass with no shared validation base class (docs/CHUNK_VALIDATION_PLAN.md
    §P6.2).
    """


def select_rule(recall: float, precision: float) -> str:
    """Select the one `docs/altm.md` §5 rule whose symptom the evidence exhibits.

    Three reachable symptoms, evaluated in §5's own top-to-bottom row order —
    which is also `docs/altm.md` §7's order, where the workflow asks whether
    retrieval *found* the correct evidence before asking anything about noise:

        recall == 0    ALTM-RETRIEVE-2  "Missing answer despite evidence
                                         existing in the corpus"
        recall <  1    ALTM-RETRIEVE-3  "Low recall on a known-answerable query"
        precision < 1  ALTM-RETRIEVE-4  "Low precision on a known-answerable query"

    The premise of ALTM-RETRIEVE-2 — that the evidence exists in the corpus — is
    not assumed: Sprint P3.3.2 validated referential integrity, so every expected
    chunk id is present in the committed Chunk Corpus. The row's symptom is
    therefore satisfied in full, not merely matched on its recall half.

    Order is a documented property, not a preference. A question with zero recall
    is also, trivially, a low-precision question; taking §5's row order as the
    tie-break makes the selection a fact about the document rather than about
    this function. `docs/altm.md` §10 Principle 1 — one failure has one primary
    origin — is why exactly one rule is returned rather than every rule that
    matches.

    Returns `None` when neither recall nor precision is deficient: retrieval
    exhibited no symptom, and §5 has no row for the absence of one.
    """
    if recall == 0.0:
        return "ALTM-RETRIEVE-2"
    if recall < 1.0:
        return "ALTM-RETRIEVE-3"
    if precision < 1.0:
        return "ALTM-RETRIEVE-4"
    return None


def assess_confidence(rule_id: str, recall: float) -> str:
    """Assess how completely repository evidence supports the selected diagnosis.

    `docs/altm.md` §7 requires an upstream stage to be ruled out before a
    downstream one is attributed, and §10 Principle 2 warns that a Knowledge-stage
    failure makes every downstream stage look wrong. Whether this engine can
    perform that upstream exclusion is what the three values record:

    * **Complete Evidence** — every expected chunk was retrieved (`recall == 1`).
      The corpus therefore contained the evidence, indexing produced it, and
      retrieval found it: the Knowledge and Index checks are satisfied *by the
      observation itself*, so the remaining precision symptom is attributable to
      Retrieve with nothing upstream left to exclude.

    * **Partial Evidence** — some expected chunks were retrieved and some were
      not (`0 < recall < 1`). The retrieved ones demonstrate the corpus and index
      are sound for that question, so ALTM-RETRIEVE-3 is uniquely selected; the
      missing ones cannot be attributed further, because distinguishing a ranking
      cutoff from a stale document requires document identity the permitted
      inputs do not carry.

    * **Insufficient Evidence** — no expected chunk was retrieved (`recall == 0`).
      Two documented rules match the observation equally: ALTM-RETRIEVE-2
      (Retrieve) and ALTM-KNOWLEDGE-2, "Stale answer despite a recent source
      update" (Knowledge), whose freshness check this engine cannot run. The
      permitted inputs cannot discriminate between them, so the evidence does not
      uniquely support one diagnosis. Work Package 6 requires this to be recorded
      rather than resolved by invented reasoning, and it is: the rule selected
      remains the one §5's row order yields, and the confidence field states that
      the evidence does not exclude the alternative.

    This is evidence completeness, not likelihood. No value here expresses how
    probable a diagnosis is.
    """
    if rule_id == "ALTM-RETRIEVE-2":
        return INSUFFICIENT_EVIDENCE
    if recall < 1.0:
        return PARTIAL_EVIDENCE
    return COMPLETE_EVIDENCE


def diagnose_question(evaluation: dict, metric_row: dict) -> dict:
    """Produce at most one diagnosis for one evaluated question.

    Returns `None` for a question exhibiting no symptom. Every diagnosis returned
    carries exactly one `rule_id`, exactly one reachable `altm_stage`, and exactly
    one `diagnosis_confidence`, alongside the evaluation and metric evidence that
    selected them — so a reader can re-derive the diagnosis from the record
    without consulting this code, which is what makes it traceable back to
    repository authorities rather than to an implementation.

    The rule's own documented text travels with the diagnosis. Carrying the
    `documented_rule` and `documented_metric` verbatim is what lets a reviewer
    check the application against `docs/altm.md` §5 directly; a bare `rule_id`
    would require trusting that this engine read the row correctly.
    """
    recall = metric_row["chunk_recall_at_k"]
    precision = metric_row["chunk_precision_at_k"]

    rule_id = select_rule(recall, precision)
    if rule_id is None:
        return None

    rule = RULES_BY_ID[rule_id]

    return {
        "id": evaluation["id"],
        "rule_id": rule_id,
        "documented_rule": rule["symptom"],
        "documented_metric": rule["metric"],
        "documented_investigation": rule["investigation"],
        "responsible_component": rule["component"],
        "altm_stage": reachable_stage(rule_id),
        "diagnosis_confidence": assess_confidence(rule_id, recall),
        # Supporting evaluation evidence (Sprint P3.3.2).
        "classification": evaluation["classification"],
        "expected_count": evaluation["expected_count"],
        "observed_count": evaluation["observed_count"],
        "matched_count": evaluation["matched_count"],
        # Supporting metric evidence (Sprint P3.3.3). Named as the deterministic
        # Milestone 1A measurements they are — the rule's own documented metric
        # is Context Precision / Context Recall, which are Ragas metrics reserved
        # for Milestone 2 and are NOT computed anywhere in this repository. The
        # documented metric is carried above; these are the evidence actually
        # available, and the two are deliberately not conflated.
        "chunk_recall_at_k": recall,
        "chunk_precision_at_k": precision,
    }


def diagnose(records: list, metrics: dict) -> list:
    """Diagnose every evaluated question, in Retrieval Evaluation record order.

    Record order carries through from the QA Dataset via the Evidence Trace
    Dataset and the evaluation, so a diagnosis can be read against any upstream
    artifact row-for-row.

    The metrics report is joined to the records by question id, and the join is
    required to be total: a question with no metric row cannot be diagnosed, and
    a metric row with no evaluation record means the two upstream layers describe
    different question sets. Either is a broken pipeline rather than a diagnostic
    finding, so both are refused.

    Questions exhibiting no symptom yield no diagnosis and are counted in the
    summary instead — `docs/altm.md` §5 is a lookup from an observed symptom, and
    inventing a row for its absence would be creating a rule.
    """
    rows = _index_metric_rows(records, metrics)

    diagnoses = []
    for record in records:
        diagnosis = diagnose_question(record, rows[record["id"]])
        if diagnosis is not None:
            diagnoses.append(diagnosis)
    return diagnoses


def _index_metric_rows(records: list, metrics: dict) -> dict:
    """Join the metrics report's per-question rows to the evaluation records."""
    if not isinstance(metrics, dict) or "per_question" not in metrics:
        raise RetrievalDiagnosisError(
            "Retrieval Metrics report carries no per-question rows to diagnose."
        )

    rows = {row["id"]: row for row in metrics["per_question"]}

    missing = [record["id"] for record in records if record["id"] not in rows]
    if missing:
        raise RetrievalDiagnosisError(
            f"Retrieval Metrics report has no row for evaluated questions {missing}."
        )

    extra = sorted(set(rows) - {record["id"] for record in records})
    if extra:
        raise RetrievalDiagnosisError(
            f"Retrieval Metrics rows {extra} correspond to no Retrieval Evaluation record."
        )

    return rows


def summarize(diagnoses: list, records: list) -> dict:
    """Root-cause summary: stage counts, confidence counts, and recurring patterns.

    Descriptive only (Work Package 7). Nothing below ranks a finding by severity,
    proposes a change, or evaluates whether the diagnosed behaviour is acceptable.

    Every reachable stage and every confidence value appears even at zero: an
    absent key and a zero count are different claims, and a stage that was never
    attributed is itself a finding — the one this evaluation's Knowledge count
    records.
    """
    stages = Counter(diagnosis["altm_stage"] for diagnosis in diagnoses)
    confidences = Counter(diagnosis["diagnosis_confidence"] for diagnosis in diagnoses)
    rules = Counter(diagnosis["rule_id"] for diagnosis in diagnoses)

    return {
        "questions_evaluated": len(records),
        "questions_diagnosed": len(diagnoses),
        "questions_without_symptom": len(records) - len(diagnoses),
        "by_stage": {stage: stages[stage] for stage in REACHABLE_STAGES},
        "by_confidence": {value: confidences[value] for value in CONFIDENCE_VALUES},
        "by_rule": {rule_id: rules[rule_id] for rule_id in sorted(rules)},
    }


def validate_diagnoses(diagnoses: list, records: list) -> list:
    """Verify every diagnosis satisfies the Sprint P3.3.4 invariants.

    Structural gate, fail-fast, `list -> list` — the same public shape the
    repository's other validators establish. Four invariants, one per success
    criterion: exactly one documented rule, exactly one reachable stage, exactly
    one confidence value, and one diagnosis per question at most.
    """
    seen: set = set()
    known = {record["id"] for record in records}

    for index, diagnosis in enumerate(diagnoses):
        if diagnosis["rule_id"] not in RULES_BY_ID:
            raise RetrievalDiagnosisError(
                f"Diagnosis at index {index} cites rule {diagnosis['rule_id']!r}, "
                f"which docs/altm.md §5 does not document."
            )

        if diagnosis["altm_stage"] not in REACHABLE_STAGES:
            raise RetrievalDiagnosisError(
                f"Diagnosis {diagnosis['id']!r} attributes to stage "
                f"{diagnosis['altm_stage']!r}, which is not reachable in this repository."
            )

        if diagnosis["altm_stage"] not in RULES_BY_ID[diagnosis["rule_id"]]["stages"]:
            raise RetrievalDiagnosisError(
                f"Diagnosis {diagnosis['id']!r} attributes rule {diagnosis['rule_id']!r} "
                f"to stage {diagnosis['altm_stage']!r}, which that rule does not name."
            )

        if diagnosis["diagnosis_confidence"] not in CONFIDENCE_VALUES:
            raise RetrievalDiagnosisError(
                f"Diagnosis {diagnosis['id']!r} carries confidence "
                f"{diagnosis['diagnosis_confidence']!r}, which is not a permitted value."
            )

        if diagnosis["documented_rule"] != RULES_BY_ID[diagnosis["rule_id"]]["symptom"]:
            raise RetrievalDiagnosisError(
                f"Diagnosis {diagnosis['id']!r} carries rule text that does not match "
                f"docs/altm.md §5 row {diagnosis['rule_id']!r}."
            )

        if diagnosis["id"] not in known:
            raise RetrievalDiagnosisError(
                f"Diagnosis {diagnosis['id']!r} corresponds to no evaluated question."
            )

        if diagnosis["id"] in seen:
            raise RetrievalDiagnosisError(
                f"Question {diagnosis['id']!r} received more than one diagnosis."
            )
        seen.add(diagnosis["id"])

    return diagnoses
