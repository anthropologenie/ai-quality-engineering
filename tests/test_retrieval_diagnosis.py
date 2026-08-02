"""Specification Family 7 — Retrieval Diagnosis.

Sprint P3.3.4: executable specifications for the Retrieval Diagnosis Engine
(`evaluation/retrieval_diagnosis.py`), the ALTM rule transcription
(`evaluation/altm_rules.py`), and the Independent Validator
(`evaluation/retrieval_diagnosis_validator.py`).

Four kinds of specification, deliberately separated:

    transcription  the rule table against `docs/altm.md` itself
    rules          rule selection and confidence over constructed evidence
    contract       the dependency rule and the sprint's stage restriction
    corpus         the committed repository authorities, diagnosed end to end

The transcription specifications are the load-bearing ones. Every diagnosis
claims to apply a rule written in `docs/altm.md` §5; if the transcription drifts
from the document, every diagnosis cites text the repository does not contain.
`test_every_rule_symptom_appears_verbatim_in_altm` reads the document and checks.

No specification asserts a *retrieval outcome* on the committed corpus. That
today's evaluation yields ten `ALTM-RETRIEVE-4` diagnoses is a fact about Sprint
P3.3.1's Milestone 1A lexical stub, which Milestone 2 is expected to change;
freezing it would convert a retrieval improvement into a test failure. What is
specified is that every diagnosis cites a documented rule, receives one reachable
stage and one confidence value, and that both derivations agree.

Observational only: every specification reads committed repository state and
writes nothing.
"""

import ast

from pathlib import Path

import pytest

from evaluation.altm_rules import (
    FAILURE_LOCALIZATION_MATRIX,
    LIFECYCLE_STAGES,
    REACHABLE_STAGES,
    RULES_BY_ID,
    reachable_stage,
)
from evaluation.retrieval_diagnosis import (
    CONFIDENCE_VALUES,
    RetrievalDiagnosisError,
    assess_confidence,
    diagnose,
    diagnose_question,
    select_rule,
    summarize,
    validate_diagnoses,
)
from evaluation.retrieval_diagnosis_validator import compare, rederive
from evaluation.retrieval_metrics import compute
from scripts.evaluate_retrieval import authority_digests
from scripts.report_retrieval_metrics import evaluation_records

ALTM_PATH = Path(__file__).resolve().parent.parent / "docs" / "altm.md"

UNREACHABLE_STAGES = ("Assemble", "Infer", "Post-Process", "Evaluate", "Final Answer")


def record(entry_id, expected, observed):
    """Build one Retrieval Evaluation record in the Sprint P3.3.2 record shape."""
    expected_set, observed_set = set(expected), set(observed)
    matched = sorted(expected_set & observed_set)

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
    return evaluation_records()


@pytest.fixture(scope="module")
def metrics(records):
    return compute(records)


@pytest.fixture(scope="module")
def diagnoses(records, metrics):
    return diagnose(records, metrics)


@pytest.fixture(scope="module")
def altm_text():
    return ALTM_PATH.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Rule transcription against docs/altm.md
# ---------------------------------------------------------------------------


def test_every_rule_symptom_appears_verbatim_in_altm(altm_text):
    """Every transcribed symptom is text that `docs/altm.md` actually contains.

    The load-bearing specification of this sprint: a diagnosis cites documented
    prose, so the transcription must not have drifted from the document. Any
    paraphrase, typo, or invented row fails here.
    """
    for rule in FAILURE_LOCALIZATION_MATRIX:
        assert rule["symptom"] in altm_text, rule["rule_id"]


def test_every_rule_component_and_metric_appear_verbatim_in_altm(altm_text):
    """The remaining §5 cells carried on a diagnosis are equally verbatim."""
    for rule in FAILURE_LOCALIZATION_MATRIX:
        assert rule["component"] in altm_text, rule["rule_id"]
        assert rule["metric"] in altm_text, rule["rule_id"]
        assert rule["investigation"] in altm_text, rule["rule_id"]


def test_transcription_covers_every_matrix_row(altm_text):
    """One identifier per documented row — no row omitted, none invented.

    The §5 table's rows are counted from the document itself rather than assumed,
    so a row added to `docs/altm.md` without a corresponding identifier fails.
    """
    lines = altm_text.splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith("| Observed Symptom"))
    rows = 0
    for line in lines[start + 2 :]:
        if not line.startswith("|"):
            break
        rows += 1

    assert rows == len(FAILURE_LOCALIZATION_MATRIX)


def test_rule_ids_are_unique_and_stage_scoped():
    """`ALTM-<STAGE>-<n>`, numbered within the row's first-listed stage."""
    assert len(RULES_BY_ID) == len(FAILURE_LOCALIZATION_MATRIX)

    counters: dict = {}
    for rule in FAILURE_LOCALIZATION_MATRIX:
        stage = rule["stages"][0].upper().replace(" ", "-")
        counters[stage] = counters.get(stage, 0) + 1
        assert rule["rule_id"] == f"ALTM-{stage}-{counters[stage]}", rule["rule_id"]


def test_lifecycle_stages_match_the_documented_eight(altm_text):
    """The eight `docs/altm.md` §3 stages, in document order."""
    assert " → ".join(LIFECYCLE_STAGES) in altm_text
    assert len(LIFECYCLE_STAGES) == 8


def test_reachable_stages_are_the_three_this_repository_implements():
    """Work Package 5: only Knowledge, Index and Retrieve are reachable."""
    assert REACHABLE_STAGES == ("Knowledge", "Index", "Retrieve")
    assert set(REACHABLE_STAGES) <= set(LIFECYCLE_STAGES)
    assert not set(REACHABLE_STAGES) & set(UNREACHABLE_STAGES)


def test_unreachable_rules_resolve_to_no_stage():
    """A rule naming only unreachable stages cannot acquire one.

    `ALTM-INFER-1` names Infer alone; there is no Generator to fail, so asking
    for its reachable stage raises rather than silently returning something.
    """
    with pytest.raises(KeyError):
        reachable_stage("ALTM-INFER-1")


def test_two_stage_rules_resolve_to_their_reachable_stage():
    """"Retrieve or Assemble" resolves to Retrieve — the component that exists."""
    assert reachable_stage("ALTM-RETRIEVE-2") == "Retrieve"
    assert reachable_stage("ALTM-INDEX-1") == "Index"


# ---------------------------------------------------------------------------
# Rule selection and confidence
# ---------------------------------------------------------------------------


def test_zero_recall_selects_the_missing_evidence_rule():
    """No expected chunk retrieved, though the corpus contains it."""
    assert select_rule(recall=0.0, precision=0.0) == "ALTM-RETRIEVE-2"


def test_partial_recall_selects_the_low_recall_rule():
    """Some expected evidence found, some missing."""
    assert select_rule(recall=0.5, precision=0.2) == "ALTM-RETRIEVE-3"


def test_full_recall_with_noise_selects_the_low_precision_rule():
    """Every expected chunk retrieved, alongside chunks that were not expected."""
    assert select_rule(recall=1.0, precision=0.2) == "ALTM-RETRIEVE-4"


def test_perfect_retrieval_selects_no_rule():
    """`docs/altm.md` §5 is a lookup from an observed symptom; absent one, no row applies."""
    assert select_rule(recall=1.0, precision=1.0) is None


def test_recall_takes_precedence_over_precision():
    """§5 row order is the tie-break, not a preference expressed here.

    A zero-recall question is trivially also a low-precision question. "Low
    recall on a known-answerable query" precedes "Low precision on a
    known-answerable query" in the document, and `docs/altm.md` §7 asks whether
    retrieval found the correct evidence before asking anything about noise.
    """
    assert select_rule(recall=0.0, precision=0.0) == "ALTM-RETRIEVE-2"
    assert select_rule(recall=0.25, precision=0.2) == "ALTM-RETRIEVE-3"


def test_full_recall_yields_complete_evidence():
    """The observation itself excludes Knowledge and Index.

    Every expected chunk was retrieved, so the corpus held the evidence and the
    index produced it — `docs/altm.md` §7's upstream exclusion is satisfied by
    the observation, leaving nothing unresolved above Retrieve.
    """
    assert assess_confidence("ALTM-RETRIEVE-4", recall=1.0) == "Complete Evidence"


def test_partial_recall_yields_partial_evidence():
    """Upstream is excluded for the chunks retrieved, not for those missing."""
    assert assess_confidence("ALTM-RETRIEVE-3", recall=0.5) == "Partial Evidence"


def test_zero_recall_yields_insufficient_evidence():
    """Two documented rules match equally and the inputs cannot discriminate.

    `ALTM-KNOWLEDGE-2` ("Stale answer despite a recent source update") is as
    consistent with zero overlap as `ALTM-RETRIEVE-2` is, and its documented
    detection is a freshness check the permitted inputs cannot perform. Work
    Package 6 requires this to be recorded rather than resolved by invented
    reasoning.
    """
    assert assess_confidence("ALTM-RETRIEVE-2", recall=0.0) == "Insufficient Evidence"


def test_every_diagnosis_carries_exactly_one_of_each_required_field():
    """One rule_id, one reachable stage, one confidence — the success criteria."""
    diagnosis = diagnose_question(
        record("meta_a", ["x"], ["x", "y"]),
        {"id": "meta_a", "chunk_recall_at_k": 1.0, "chunk_precision_at_k": 0.5},
    )

    assert diagnosis["rule_id"] in RULES_BY_ID
    assert diagnosis["altm_stage"] in REACHABLE_STAGES
    assert diagnosis["diagnosis_confidence"] in CONFIDENCE_VALUES
    assert diagnosis["documented_rule"] == RULES_BY_ID[diagnosis["rule_id"]]["symptom"]


def test_question_without_symptom_yields_no_diagnosis():
    """Nothing to localize, so no row is applied and no record is invented."""
    assert (
        diagnose_question(
            record("meta_a", ["x"], ["x"]),
            {"id": "meta_a", "chunk_recall_at_k": 1.0, "chunk_precision_at_k": 1.0},
        )
        is None
    )


# ---------------------------------------------------------------------------
# Document identity (Sprint P3.3.5)
# ---------------------------------------------------------------------------


def test_disjoint_documents_select_the_wrong_document_rule():
    """Zero recall with no document overlap is `ALTM-RETRIEVE-1`.

    "Right topic, wrong specific document retrieved" — a §5 row that could not
    fire before document identity existed, because nothing distinguished it from
    "Missing answer despite evidence existing in the corpus".
    """
    assert (
        select_rule(0.0, 0.0, expected_documents=["doc_1"], observed_documents=["doc_2"])
        == "ALTM-RETRIEVE-1"
    )


def test_reached_expected_document_selects_the_missing_evidence_rule():
    """Zero recall while retrieving *from* the expected document is `ALTM-RETRIEVE-2`.

    The right document was reached; its expected chunks were not returned. That
    is the missing-evidence row, not the wrong-document row.
    """
    assert (
        select_rule(0.0, 0.0, expected_documents=["doc_1"], observed_documents=["doc_1", "doc_2"])
        == "ALTM-RETRIEVE-2"
    )


def test_rule_selection_is_unchanged_without_document_identity():
    """Absent identity reproduces the pre-P3.3.5 selection exactly.

    The split is additional resolution, not a changed rule: a record predating
    the enrichment diagnoses as it always did.
    """
    assert select_rule(0.0, 0.0) == "ALTM-RETRIEVE-2"
    assert select_rule(0.0, 0.0, expected_documents=[], observed_documents=[]) == "ALTM-RETRIEVE-2"


def test_document_identity_excludes_the_upstream_stages():
    """A non-empty expected document set yields Complete Evidence at any recall.

    `expected_document_ids` resolves through chunk ids Sprint P3.3.2 validated as
    present in the committed Chunk Corpus, so the expected document is indexed
    and its chunks exist — which is what the Knowledge and Index checks test.
    Both upstream stages are excluded on evidence, so nothing above Retrieve
    remains unresolved.
    """
    assert assess_confidence("ALTM-RETRIEVE-2", 0.0, ["doc_1"]) == "Complete Evidence"
    assert assess_confidence("ALTM-RETRIEVE-1", 0.0, ["doc_1"]) == "Complete Evidence"
    assert assess_confidence("ALTM-RETRIEVE-3", 0.5, ["doc_1"]) == "Complete Evidence"


def test_confidence_is_unchanged_without_document_identity():
    """The pre-P3.3.5 assessments survive intact for records lacking identity."""
    assert assess_confidence("ALTM-RETRIEVE-2", 0.0, []) == "Insufficient Evidence"
    assert assess_confidence("ALTM-RETRIEVE-3", 0.5, []) == "Partial Evidence"
    assert assess_confidence("ALTM-RETRIEVE-4", 1.0, []) == "Complete Evidence"


def test_no_knowledge_rule_becomes_selectable():
    """Document identity activates a Retrieve row, not a Knowledge row.

    `ALTM-KNOWLEDGE-1` needs which *version* is current — the Knowledge Manifest
    encodes that in filenames and the dependency rule bars reading it.
    `ALTM-KNOWLEDGE-2`'s documented detection is that re-indexing was triggered,
    and a non-empty expected document set shows it was, contradicting the row's
    premise rather than leaving it open.
    """
    selections = {
        select_rule(recall, precision, expected, observed)
        for recall, precision in ((0.0, 0.0), (0.5, 0.2), (1.0, 0.2), (1.0, 1.0))
        for expected in (["doc_1"], [])
        for observed in (["doc_1"], ["doc_2"], ["doc_1", "doc_2"], [])
    }

    assert not {rule for rule in selections if rule and rule.startswith("ALTM-KNOWLEDGE")}


def test_diagnosis_carries_the_supporting_document_evidence():
    """The document sets travel with the diagnosis, so the rule split and the
    upstream exclusion are re-derivable from the diagnosis alone."""
    evaluation = record("meta_a", ["x"], ["y"])
    evaluation["expected_document_ids"] = ["doc_1"]
    evaluation["observed_document_ids"] = ["doc_2"]

    diagnosis = diagnose_question(
        evaluation, {"id": "meta_a", "chunk_recall_at_k": 0.0, "chunk_precision_at_k": 0.0}
    )

    assert diagnosis["rule_id"] == "ALTM-RETRIEVE-1"
    assert diagnosis["altm_stage"] == "Retrieve"
    assert diagnosis["diagnosis_confidence"] == "Complete Evidence"
    assert diagnosis["expected_document_ids"] == ["doc_1"]
    assert diagnosis["observed_document_ids"] == ["doc_2"]


def test_independent_validator_agrees_on_the_document_split():
    """Both derivations reach the same rule and confidence from document identity."""
    records = []
    for entry_id, expected, observed, expected_docs, observed_docs in (
        ("meta_a", ["x"], ["y"], ["doc_1"], ["doc_2"]),
        ("meta_b", ["x"], ["y"], ["doc_1"], ["doc_1", "doc_2"]),
        ("meta_c", ["x", "y"], ["x", "z"], ["doc_1"], ["doc_1", "doc_2"]),
    ):
        evaluation = record(entry_id, expected, observed)
        evaluation["expected_document_ids"] = expected_docs
        evaluation["observed_document_ids"] = observed_docs
        records.append(evaluation)

    metrics = compute(records)
    engine = {
        d["id"]: (d["rule_id"], d["altm_stage"], d["diagnosis_confidence"])
        for d in diagnose(records, metrics)
    }

    assert engine == rederive(records, metrics)
    assert engine["meta_a"][0] == "ALTM-RETRIEVE-1"
    assert engine["meta_b"][0] == "ALTM-RETRIEVE-2"


def test_independent_validator_detects_incoherent_document_identity():
    """Matched chunks with disjoint document sets cannot describe one retrieval."""
    evaluation = record("meta_a", ["x"], ["x", "y"])
    evaluation["expected_document_ids"] = ["doc_1"]
    evaluation["observed_document_ids"] = ["doc_2"]
    records = [evaluation]

    rows = {row["check"]: row for row in compare(diagnose(records, compute(records)), records, compute(records))}
    assert rows["document identity integrity"]["status"] == "FAIL"


# ---------------------------------------------------------------------------
# Input contract and dependency rule
# ---------------------------------------------------------------------------


def test_question_without_a_metric_row_is_refused():
    """A question the metrics layer never measured cannot be diagnosed."""
    with pytest.raises(RetrievalDiagnosisError, match="no row for evaluated questions"):
        diagnose([record("meta_a", ["x"], ["y"])], {"per_question": []})


def test_metric_row_without_a_question_is_refused():
    """The two upstream layers must describe the same question set."""
    with pytest.raises(RetrievalDiagnosisError, match="correspond to no Retrieval Evaluation"):
        diagnose(
            [record("meta_a", ["x"], ["y"])],
            {
                "per_question": [
                    {"id": "meta_a", "chunk_recall_at_k": 0.0, "chunk_precision_at_k": 0.0},
                    {"id": "meta_b", "chunk_recall_at_k": 0.0, "chunk_precision_at_k": 0.0},
                ]
            },
        )


def test_diagnosis_naming_an_unreachable_stage_is_refused():
    """Work Package 5, enforced rather than assumed."""
    diagnosis = diagnose_question(
        record("meta_a", ["x"], ["y"]),
        {"id": "meta_a", "chunk_recall_at_k": 0.0, "chunk_precision_at_k": 0.0},
    )
    diagnosis["altm_stage"] = "Infer"

    with pytest.raises(RetrievalDiagnosisError, match="not reachable"):
        validate_diagnoses([diagnosis], [record("meta_a", ["x"], ["y"])])


def test_diagnosis_citing_an_undocumented_rule_is_refused():
    """No diagnostic rule may be introduced outside `docs/altm.md` §5."""
    diagnosis = diagnose_question(
        record("meta_a", ["x"], ["y"]),
        {"id": "meta_a", "chunk_recall_at_k": 0.0, "chunk_precision_at_k": 0.0},
    )
    diagnosis["rule_id"] = "ALTM-RETRIEVE-99"

    with pytest.raises(RetrievalDiagnosisError, match="does not document"):
        validate_diagnoses([diagnosis], [record("meta_a", ["x"], ["y"])])


def imported_roots(module):
    """Top-level package names a module imports, parsed from its own source."""
    tree = ast.parse(Path(module.__file__).read_text(encoding="utf-8"))
    roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".")[0])
    return roots


def imported_modules(module):
    """Fully-qualified module names a module imports."""
    tree = ast.parse(Path(module.__file__).read_text(encoding="utf-8"))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def test_diagnosis_engine_reaches_no_repository_authority():
    """The Sprint P3.3.4 dependency rule, enforced structurally.

    The engine may consume evaluation records, the metrics report, and the ALTM
    rule transcription — nothing else. It cannot import the Chunk Corpus, the
    Evidence Trace Dataset, the Knowledge Manifest, or `RetrievalResult`, and an
    allowlist fails on any import nobody thought to forbid.
    """
    import evaluation.retrieval_diagnosis as engine

    assert imported_roots(engine) <= {"collections", "evaluation"}
    assert imported_modules(engine) <= {"collections", "evaluation.altm_rules"}


def test_rule_transcription_imports_nothing():
    """The authority transcription depends on no code at all."""
    import evaluation.altm_rules as rules

    assert imported_roots(rules) == set()


def test_validator_does_not_import_the_diagnosis_engine():
    """Work Package 8 independence, enforced structurally.

    `evaluation.altm_rules` is shared deliberately — it is the transcribed
    authority both implementations must apply, and two separate transcriptions
    would test copying rather than consistent application. The engine itself is
    not imported.
    """
    import evaluation.retrieval_diagnosis_validator as validator

    assert imported_modules(validator) <= {"collections", "evaluation.altm_rules"}
    assert "evaluation.retrieval_diagnosis" not in imported_modules(validator)


# ---------------------------------------------------------------------------
# Independent derivation
# ---------------------------------------------------------------------------


def test_both_derivations_agree_on_synthetic_evidence():
    """Two independent applications of the same documented rules agree."""
    records = [
        record("meta_a", ["x"], ["x", "y"]),
        record("meta_b", ["x", "y"], ["x", "z"]),
        record("meta_c", ["x"], ["y", "z"]),
        record("meta_d", ["x"], ["x"]),
    ]
    metrics = compute(records)

    engine = {
        d["id"]: (d["rule_id"], d["altm_stage"], d["diagnosis_confidence"])
        for d in diagnose(records, metrics)
    }

    assert engine == rederive(records, metrics)
    assert "meta_d" not in engine


def test_independent_validator_detects_a_wrong_rule():
    """A diagnosis citing the wrong documented row is caught."""
    records = [record("meta_a", ["x"], ["x", "y"])]
    metrics = compute(records)
    diagnoses = diagnose(records, metrics)
    diagnoses[0]["rule_id"] = "ALTM-RETRIEVE-2"

    rows = {row["check"]: row for row in compare(diagnoses, records, metrics)}
    assert rows["rule consistency"]["status"] == "FAIL"


def test_independent_validator_detects_a_wrong_stage():
    """A stage that does not follow from the rule is caught."""
    records = [record("meta_a", ["x"], ["x", "y"])]
    metrics = compute(records)
    diagnoses = diagnose(records, metrics)
    diagnoses[0]["altm_stage"] = "Knowledge"

    rows = {row["check"]: row for row in compare(diagnoses, records, metrics)}
    assert rows["stage consistency"]["status"] == "FAIL"


def test_independent_validator_detects_a_wrong_confidence():
    """An evidence-completeness value that does not follow from recall is caught."""
    records = [record("meta_a", ["x"], ["x", "y"])]
    metrics = compute(records)
    diagnoses = diagnose(records, metrics)
    diagnoses[0]["diagnosis_confidence"] = "Insufficient Evidence"

    rows = {row["check"]: row for row in compare(diagnoses, records, metrics)}
    assert rows["confidence consistency"]["status"] == "FAIL"


def test_independent_validator_detects_a_missing_diagnosis():
    """A question the engine failed to diagnose is caught by coverage."""
    records = [record("meta_a", ["x"], ["x", "y"]), record("meta_b", ["p"], ["q"])]
    metrics = compute(records)
    diagnoses = diagnose(records, metrics)

    rows = {row["check"]: row for row in compare(diagnoses[:1], records, metrics)}
    assert rows["diagnosis coverage"]["status"] == "FAIL"


def test_independent_validator_detects_metric_record_drift():
    """A metrics report that no longer describes its evaluation records is caught.

    The engine diagnoses from the metrics report; this validator diagnoses from
    values recomputed off the records. The two are only comparable if those
    sources agree, so the agreement is checked rather than assumed.
    """
    records = [record("meta_a", ["x"], ["x", "y"])]
    metrics = compute(records)
    metrics["per_question"][0]["chunk_recall_at_k"] = 0.0

    rows = {row["check"]: row for row in compare(diagnose(records, metrics), records, metrics)}
    assert rows["metric/record agreement"]["status"] == "FAIL"


# ---------------------------------------------------------------------------
# Committed repository authorities
# ---------------------------------------------------------------------------


def test_committed_corpus_every_diagnosis_is_well_formed(diagnoses, records):
    """Every diagnosis cites one documented rule, one reachable stage, one confidence."""
    validate_diagnoses(diagnoses, records)

    for diagnosis in diagnoses:
        assert diagnosis["rule_id"] in RULES_BY_ID
        assert diagnosis["altm_stage"] in REACHABLE_STAGES
        assert diagnosis["diagnosis_confidence"] in CONFIDENCE_VALUES


def test_committed_corpus_no_unreachable_stage_is_attributed(diagnoses):
    """No generation pipeline exists, so no generation-stage diagnosis may appear."""
    attributed = {diagnosis["altm_stage"] for diagnosis in diagnoses}
    assert not attributed & set(UNREACHABLE_STAGES)


def test_committed_corpus_validation_report_is_all_pass(diagnoses, records, metrics):
    """Every Work Package 8 check passes on the committed authorities."""
    rows = compare(diagnoses, records, metrics)

    assert [row["check"] for row in rows] == [
        "diagnosis coverage",
        "rule consistency",
        "stage consistency",
        "confidence consistency",
        "metric/record agreement",
        "unreachable stages absent",
        "one diagnosis per question",
        # Sprint P3.3.5. The one existing P3.3.4 specification this sprint
        # changes, and it changes by one appended row: the enrichment added a
        # validation check, so the reported check list grew. No assertion about
        # pre-existing behaviour was weakened or removed.
        "document identity integrity",
    ]
    assert all(row["status"] == "PASS" for row in rows), rows


def test_committed_corpus_diagnosis_is_deterministic(records, metrics, diagnoses):
    """Repeated diagnosis over the same inputs yields identical records."""
    assert diagnose(records, metrics) == diagnoses


def test_committed_corpus_diagnosis_is_reproducible(diagnoses):
    """Re-running the whole pipeline reproduces every diagnosis exactly."""
    fresh = evaluation_records()
    assert diagnose(fresh, compute(fresh)) == diagnoses


def test_committed_corpus_summary_totals_are_exhaustive(diagnoses, records):
    """Stage and confidence counts each account for every diagnosis exactly once."""
    summary = summarize(diagnoses, records)

    assert summary["questions_evaluated"] == len(records)
    assert sum(summary["by_stage"].values()) == len(diagnoses)
    assert sum(summary["by_confidence"].values()) == len(diagnoses)
    assert sum(summary["by_rule"].values()) == len(diagnoses)
    assert (
        summary["questions_diagnosed"] + summary["questions_without_symptom"]
        == summary["questions_evaluated"]
    )


def test_repository_authorities_are_byte_identical(records, metrics):
    """Diagnosing the repository modifies no repository authority."""
    before = authority_digests()

    diagnoses = diagnose(records, metrics)
    summarize(diagnoses, records)
    compare(diagnoses, records, metrics)

    assert authority_digests() == before
