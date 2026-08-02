"""Retrieval Diagnosis execution against the completed upstream layers.

Sprint P3.3.4: the thin orchestrator that obtains the Retrieval Evaluation
records and the Retrieval Metrics report, applies the documented ALTM rules via
`evaluation/retrieval_diagnosis.py`, independently re-derives every diagnosis,
and reports both alongside the repository integrity check. It plays the same
operational-tooling role the repository's other `scripts/` modules play and holds
no diagnostic logic of its own — every rule, stage attribution and confidence
assessment lives in `evaluation/`.

Strictly read-only. No diagnosis artifact is persisted, because none is defined
by repository authority and this sprint introduces no artifact names
(docs/MILESTONE_1A.md Architecture Freeze) — the same decision the retrieval,
evaluation and metrics orchestrators each recorded.

Upstream is re-executed, never re-derived: `scripts/report_retrieval_metrics.py`'s
own `evaluation_records()` and the metrics engine's `compute()` produce the two
inputs, so the diagnosis explains exactly the evaluation and metrics those layers
publish. Where the dependency rule is enforced, and where it is not: the
**Diagnosis Engine** consumes only records, the metrics report, and the ALTM rule
transcription. This orchestrator additionally hashes repository authorities,
which Sprint P3.3.4 permits an orchestration layer for repository verification.
"""

from evaluation.retrieval_diagnosis import diagnose, summarize, validate_diagnoses
from evaluation.retrieval_diagnosis_validator import compare
from evaluation.retrieval_metrics import compute
from scripts.evaluate_retrieval import authority_digests
from scripts.report_retrieval_metrics import evaluation_records


def upstream() -> tuple:
    """Obtain the two completed upstream outputs this sprint diagnoses."""
    records = evaluation_records()
    return records, compute(records)


def report(diagnoses: list, summary: dict, validation: list) -> None:
    """Print the per-question diagnoses, root-cause summary, and validation report."""
    print("Per-question diagnosis")
    for diagnosis in diagnoses:
        print(
            f"  {diagnosis['id']:<40} {diagnosis['rule_id']:<18} "
            f"{diagnosis['altm_stage']:<10} {diagnosis['diagnosis_confidence']:<22} "
            f"recall={diagnosis['chunk_recall_at_k']:<7} "
            f"precision={diagnosis['chunk_precision_at_k']}"
        )

    print("\nDiagnosis Summary")
    print(f"  {'questions evaluated':<32} {summary['questions_evaluated']}")
    print(f"  {'questions diagnosed':<32} {summary['questions_diagnosed']}")
    print(f"  {'questions without symptom':<32} {summary['questions_without_symptom']}")

    print("\nStage Attribution Summary")
    for stage, count in summary["by_stage"].items():
        print(f"  {stage:<32} {count}")

    print("\nDiagnosis Confidence Summary")
    for value, count in summary["by_confidence"].items():
        print(f"  {value:<32} {count}")

    print("\nRule Attribution Summary")
    for rule_id, count in summary["by_rule"].items():
        print(f"  {rule_id:<32} {count}")

    print("\nValidation")
    for entry in validation:
        detail = f"  {entry['detail']}" if entry["detail"] else ""
        print(f"  {entry['check']:<32} {entry['status']}{detail}")


def main() -> None:
    """Diagnose, independently validate, and report.

    Determinism and reproducibility are demonstrated by measurement rather than
    asserted: the engine is run twice over the same inputs, and once more over a
    freshly re-executed upstream. Repository integrity is demonstrated the same
    way, by digests taken around the whole execution.
    """
    before = authority_digests()

    records, metrics = upstream()
    diagnoses = validate_diagnoses(diagnose(records, metrics), records)
    summary = summarize(diagnoses, records)

    validation = compare(diagnoses, records, metrics)
    validation.append(
        {
            "check": "determinism",
            "status": "PASS" if diagnose(records, metrics) == diagnoses else "FAIL",
            "detail": "",
        }
    )

    fresh_records, fresh_metrics = upstream()
    validation.append(
        {
            "check": "reproducibility",
            "status": "PASS" if diagnose(fresh_records, fresh_metrics) == diagnoses else "FAIL",
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

    report(diagnoses, summary, validation)


if __name__ == "__main__":
    main()
