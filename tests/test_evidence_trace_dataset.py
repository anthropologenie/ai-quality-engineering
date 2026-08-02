"""Specification Family 8 — Evidence Trace Dataset Authority.

Sprint P3.4.1 (`docs/MILESTONE_1A.md` build item 9): promotes the Evidence Trace
Dataset's existing structural validation into permanent committed
specifications.

The validation itself is **not written here**. `scripts/build_evidence_trace.py`
already ships `validate_evidence_trace()` — a read-only, fail-fast
`Mapping -> Mapping` gate implementing the canonical schema from
`docs/roadmap.md` §2.4 and `datasets/SCHEMA.md` §8 — and Sprint P3.4.1's Existing
Validation Policy requires promotion, not redesign. Every specification below
either runs that gate over committed state or holds it to one of its own failure
classes. No structural rule is restated, and no wrapper is introduced.

The gap this closes
--------------------
The gate has three consumers at HEAD — `scripts/run_retrieval.py`
`load_questions`, `scripts/evaluate_retrieval.py` `load_expectations`, and the
builder's own `main()` — and, until this file, **no test**. Nothing ran it unless
a script was run by hand, and nothing anywhere exercised its failure surface, so
a regression in the gate itself would have surfaced as a *passing* validation of
a malformed dataset. The positive specifications close the first half; the
synthetic ones close the second.

Why the synthetic cases are the substantial half
-------------------------------------------------
The committed dataset is valid, so running the gate over it can only ever
demonstrate the accepting direction. It cannot demonstrate that the gate
*rejects* anything — a gate whose body had been deleted would pass ET-1 through
ET-3 exactly as it passes them today. The parameterized cases below therefore
present one deliberately malformed collection per failure class the gate
implements, covering all three of its internal stages (`_validate_representation`,
`_validate_entry`, `_validate_collection_invariants`).

Every synthetic collection is constructed in memory from a minimal valid
baseline. Nothing under `datasets/` is read, written, copied, or monkeypatched by
any synthetic case, and `valid_entry()` below is a test fixture, not a second
implementation of the builder's derivation — it fabricates the smallest object
the gate accepts, and derives nothing.

Scope boundary
---------------
Structural validation only, which is the boundary
`scripts/build_evidence_trace.py`'s own docstring draws and
`docs/CHUNK_VALIDATION_PLAN.md` §P5 established: *"structural checks live with
the artifact's build script, cross-artifact checks belong to the Data Quality
Validation layer."* Whether an `expected_chunk` id exists in the Chunk Corpus,
whether `expected_source` is catalogued, and whether an entry's expectations
agree with its parent QA pair are referential claims owned by
`tests/test_cross_dataset_integrity.py` and are deliberately absent here.

Nothing below re-asserts a rule the gate already enforces — entry field types,
the null `expected_retrieval_route`, the canonical `expected_metrics` list, the
`meta_` id convention and dataset-wide id uniqueness are all checked *by the
gate*, and ET-1 runs the gate. Restating them as separate assertions over
committed state would be the duplication `docs/ENGINEERING_TRACEABILITY_REGISTER.md`
§5 rates a **High** drift risk.

Observational only, per the Sprint P3.4.1 Repository Dependency Rule: the
committed dataset is verified exactly as stored, and no specification runs the
builder or regenerates the artifact. ET-n labels are this file's own organizing
labels, not proposed repository terminology.
"""

import json

import pytest

from scripts.build_evidence_trace import (
    CANONICAL_METRICS,
    EVIDENCE_TRACE_PATH,
    OUTCOME_ANSWER,
    SCHEMA_VERSION,
    SINGLE_HOP,
    EvidenceTraceError,
    load_evidence_trace,
    validate_evidence_trace,
)


def valid_entry(**overrides):
    """The smallest entry `validate_evidence_trace` accepts, with fields overridden.

    A baseline for the synthetic cases, so each one differs from a valid entry in
    exactly the single respect under test — otherwise a case could pass for a
    reason other than the failure class it names. Values are literals: this
    fabricates a minimal object and derives nothing from any repository artifact.
    """
    entry = {
        "id": "meta_qa_synthetic_lexical_01",
        "question": "a synthetic question",
        "expected_answer": "a synthetic answer",
        "expected_source": "synthetic-document",
        "expected_chunk": ["synthetic-chunk"],
        "expected_retrieval_route": None,
        "expected_reasoning_type": SINGLE_HOP,
        "expected_metrics": list(CANONICAL_METRICS),
        "expected_outcome": OUTCOME_ANSWER,
    }
    entry.update(overrides)
    return entry


def collection(*entries):
    """Wrap synthetic entries in a valid container."""
    return {"schema_version": SCHEMA_VERSION, "evidence_trace": list(entries)}


# --- ET-1 … ET-3: the gate over committed state ------------------------------


def test_et1_committed_dataset_passes_the_structural_gate(real_evidence_trace_collection):
    """ET-1 — `validate_evidence_trace` succeeds against the committed dataset.

    The gate raises `EvidenceTraceError` on any structural violation, so an
    uncaught call *is* the assertion: the container carries `schema_version` at
    the canonical value and an `evidence_trace` list, and every entry carries
    exactly the nine canonical fields at their required types, with a `meta_`
    id, a non-empty duplicate-free `expected_chunk`, a null
    `expected_retrieval_route`, the canonical `expected_metrics` list, and a
    reasoning type and outcome inside the Milestone 1A value domains — with
    dataset-wide id uniqueness on top.

    Every one of those rules is enforced here by running the shipped gate, not
    by restating it.
    """
    validate_evidence_trace(real_evidence_trace_collection)


def test_et2_the_gate_validates_the_committed_artifact_itself(real_evidence_trace_collection):
    """ET-2 — the gate returns the object it was given.

    The gate is contracted `Mapping -> Mapping`, returning the same collection
    rather than a normalized or repaired copy. Asserting identity establishes
    two things at once: ET-1 ran over the artifact as committed rather than over
    a reconstruction of it, and the gate left it unmodified — the observational
    property `docs/roadmap.md` §6 requires of this layer. The same evidence
    `tests/test_data_quality.py` W1 records for the Knowledge Manifest gate.
    """
    assert validate_evidence_trace(real_evidence_trace_collection) is real_evidence_trace_collection


def test_et3_the_gate_is_repeatable_over_the_committed_dataset():
    """ET-3 — the gate yields the same verdict and the same dataset on every run.

    A validation layer that reported repository state differently when nothing
    had changed would make every downstream evaluation unfalsifiable. Reads the
    artifact twice through `load_evidence_trace`, so both the read and the gate
    are covered.
    """
    first = validate_evidence_trace(load_evidence_trace())
    second = validate_evidence_trace(load_evidence_trace())

    assert first == second


# --- ET-4: the gate's container failure surface (synthetic) ------------------


@pytest.mark.parametrize(
    "malformed, expected_message",
    [
        pytest.param({"evidence_trace": []}, "schema_version", id="missing-schema-version"),
        pytest.param(
            {"schema_version": SCHEMA_VERSION}, "evidence_trace", id="missing-evidence-trace"
        ),
        pytest.param(
            {"schema_version": 1.0, "evidence_trace": []}, "string", id="non-string-version"
        ),
        pytest.param(
            {"schema_version": "2.0", "evidence_trace": []}, "2.0", id="unratified-version"
        ),
        pytest.param(
            {"schema_version": SCHEMA_VERSION, "evidence_trace": {}}, "list", id="non-list-entries"
        ),
    ],
)
def test_et4_the_gate_rejects_a_malformed_container(malformed, expected_message):
    """ET-4, synthetic — `_validate_representation`'s failure classes are all detected.

    The container gate must run to completion before any entry is inspected, so
    each of its five rejections is exercised independently. The unratified
    version case is the one that matters most in practice: `datasets/SCHEMA.md`
    §2 requires a structural change to bump `schema_version`, which is worth
    nothing unless a consumer refuses the bumped artifact rather than reading it
    under the old assumptions.

    The raised message is required to name the offending field or value —
    a rejection that does not say what was wrong leaves the next engineer to
    bisect the artifact by hand.
    """
    with pytest.raises(EvidenceTraceError) as raised:
        validate_evidence_trace(malformed)

    assert expected_message in str(raised.value)


# --- ET-5: the gate's entry failure surface (synthetic) ----------------------


@pytest.mark.parametrize(
    "entry, expected_message",
    [
        pytest.param(
            valid_entry(unexpected_field="x"), "non-canonical", id="extra-field"
        ),
        pytest.param(
            {k: v for k, v in valid_entry().items() if k != "question"},
            "question",
            id="missing-field",
        ),
        pytest.param(valid_entry(expected_chunk="not-a-list"), "type", id="mistyped-field"),
        pytest.param(
            {k: v for k, v in valid_entry().items() if k != "expected_retrieval_route"},
            "expected_retrieval_route",
            id="missing-retrieval-route",
        ),
        pytest.param(
            valid_entry(expected_retrieval_route="BM25"), "null", id="non-null-retrieval-route"
        ),
        pytest.param(valid_entry(id="qa_synthetic"), "meta_", id="non-meta-id"),
        pytest.param(valid_entry(expected_chunk=[]), "no expected chunk", id="empty-chunk-list"),
        pytest.param(
            valid_entry(expected_chunk=["c", "c"]), "repeats", id="repeated-chunk-id"
        ),
        pytest.param(
            valid_entry(expected_chunk=[1]), "chunk id strings", id="non-string-chunk-id"
        ),
        pytest.param(
            valid_entry(expected_reasoning_type="Aggregation"),
            "Milestone 1A domain",
            id="out-of-domain-reasoning-type",
        ),
        pytest.param(
            valid_entry(expected_outcome="Clarify"),
            "Milestone 1A domain",
            id="out-of-domain-outcome",
        ),
        pytest.param(
            valid_entry(expected_metrics=["Faithfulness"]),
            "expected_metrics",
            id="non-canonical-metrics",
        ),
        pytest.param("not-an-object", "must be an object", id="non-object-entry"),
    ],
)
def test_et5_the_gate_rejects_a_malformed_entry(entry, expected_message):
    """ET-5, synthetic — `_validate_entry`'s failure classes are all detected.

    One case per rule the gate implements, each differing from `valid_entry()`
    in exactly one respect. Three are worth naming for what they protect:

    *Extra field.* The gate refuses fields it does not know, which is what keeps
    `docs/roadmap.md` §2.4's schema closed. An additive-only check would let a
    future sprint attach an unratified expectation field that no consumer reads
    and no authority defines.

    *Non-null retrieval route.* `expected_retrieval_route` is null until
    Milestone 2 (Decision A). Rejecting a populated route is what stops a route
    expectation being smuggled into a milestone whose retrieval layer is a
    documented lexical stub.

    *Out-of-domain reasoning type and outcome.* `Aggregation` and `Clarify` are
    real values in `docs/roadmap.md` §2.4's vocabulary that Milestone 1A
    explicitly does not resolve (Decisions B and C) — so these cases confirm the
    gate enforces the *milestone's* restriction of the domain, not merely the
    domain.
    """
    with pytest.raises(EvidenceTraceError) as raised:
        validate_evidence_trace(collection(entry))

    assert expected_message in str(raised.value)


def test_et5_the_gate_rejects_a_duplicate_entry_identifier():
    """ET-5, synthetic — `_validate_collection_invariants` detects a duplicate id.

    The gate's only cross-entry rule, and the one that cannot be reached by
    inspecting a single entry. Both entries are individually valid and differ
    only in a field that is not the id, so the collection is rejected for its
    collection-level property alone.

    Load-bearing downstream: `scripts/evaluate_retrieval.py` `observe` keys
    observed retrieval by entry id, so a duplicate would silently discard one
    question's observation and evaluate the other's twice.
    """
    with pytest.raises(EvidenceTraceError) as raised:
        validate_evidence_trace(
            collection(valid_entry(), valid_entry(question="a different question"))
        )

    assert "Duplicate" in str(raised.value)


def test_et5_the_gate_accepts_the_synthetic_baseline():
    """ET-5, synthetic — `valid_entry()` is accepted as it stands.

    The control for every case above. Without it, a baseline that was itself
    malformed would make all thirteen rejection cases pass for the wrong reason,
    and the suite would report a failure surface it had never actually exercised.
    """
    assert validate_evidence_trace(collection(valid_entry()))["evidence_trace"]


# --- ET-6: deterministic ordering and representation -------------------------


def test_et6_the_dataset_reads_identically_on_every_load(real_evidence_trace_collection):
    """ET-6 — repeated reads yield equal collections, in equal order.

    Entry order is the QA Dataset's own order, preserved by
    `scripts/build_evidence_trace.py` `main()` and never re-sorted, and it is the
    order `scripts/run_retrieval.py` executes questions in and
    `scripts/evaluate_retrieval.py` reports them in. Equality of parsed lists is
    order-sensitive, so this specifies sequence as well as content. That this
    order *matches* the QA Dataset's is the cross-dataset suite's claim.
    """
    assert load_evidence_trace() == real_evidence_trace_collection


def test_et6_the_committed_artifact_is_in_canonical_serialized_form(
    real_evidence_trace_collection,
):
    """ET-6 — the artifact is byte-identical to its builder's serialization.

    The expression is `write_evidence_trace`'s own — `json.dumps(collection,
    indent=2) + "\\n"`, UTF-8, insertion-order keys — so this asserts the
    committed file is exactly what the repository's serializer emits for the
    collection it holds. Unlike the hand-authored Golden Dataset artifacts, this
    one is builder-produced, so no `ensure_ascii` deviation applies; the artifact
    contains no non-ASCII characters, so the parameter is not exercised either
    way.

    Round-trips the *loaded committed collection*. It does not re-derive the
    dataset from facts, QA pairs and chunks — the Sprint P3.4.1 Repository
    Dependency Rule bars regenerating this artifact, and a re-derivation would
    also make this a specification of the builder rather than of the dataset.
    """
    serialized = json.dumps(real_evidence_trace_collection, indent=2) + "\n"

    assert serialized == EVIDENCE_TRACE_PATH.read_text(encoding="utf-8")
