"""Specification Family 4 — Data Quality Validation.

Sprint P3.1.8.1A implements **Phase W1 — Manifest structural gate** from the
approved `docs/DATA_QUALITY_VALIDATION_PLAN.md` §11.2, and nothing else.

W1 is the repository's first executable Manifest specification. Until now the
committed `sample_rag/knowledge_manifest.json` was validated only when
`scripts/build_manifest.py` was run by hand; `docs/MILESTONE_1A.md` build item
1 promised *"one pytest suite"* over the Manifest and the plan's §0 verified
that suite absent at HEAD. This file closes that gap for **structure**. The
freshness/hash half of build item 1 is DQ-1 (phase W3) and is deliberately not
implemented here.

Reuse, not reimplementation (plan §11.1)
----------------------------------------
The gate is `scripts/build_manifest.py`'s own `load_manifest` and
`validate_manifest`, called directly. No structural rule is restated here, no
wrapper is introduced, and no validation logic is duplicated —
`docs/ENGINEERING_TRACEABILITY_REGISTER.md` §5 rates duplication a **High**
drift risk. The `tests/` → `scripts/` import is the one already exercised at
HEAD by tests/test_knowledge_source_failures.py; the repository-root `sys.path`
insertion in the top-level `conftest.py` makes it resolvable. (Plan §16 records
this reuse decision as open item **O-4**; this file is the recording it asks
for.)

Observational only
------------------
`validate_manifest`'s own docstring states it is read-only, performing *"no
mutation, normalization, or copying"*, and `load_manifest` performs *"no
mutation or repair"*. Every specification below is therefore a pure
observation of committed repository state. Nothing here writes, repairs, or
normalizes an artifact, and no specification is permitted to become a repair.

Why there is no synthetic negative case in this file
----------------------------------------------------
Plan §12 requires each DQV **check** to pair a synthetic negative case with a
real-corpus positive one. W1 is not such a check: §11.2 records its failure
classes as "—", and §8.2 assigns *"Manifest structural failures
(missing/mistyped `manifest_version`, `documents`, or a required entry field)"*
to the **Structural Artifact Validation** layer and `ManifestValidationError`,
explicitly **not** to DQV. Constructing malformed manifests here would specify
another layer's failure surface, which §11.3 bars. W1 asserts only that the
committed artifact clears the gate that layer already owns. The synthetic
negative cases arrive with DQ-2 (W2) onward, which are DQV failure classes.

Corpus scale, recorded not glossed (plan §12, §16 O-5)
-------------------------------------------------------
The committed corpus is one document. That does not weaken W1 — a structural
gate is decidable from the artifact alone at any size (§6.1 row 1) — but it is
the reason no specification below counts entries or asserts anything about how
many there are. Per Register §3.5's finding **I-6**, no specification names a
corpus filename.

Scope boundary
--------------
W2 (identifier uniqueness — F-1, gated on the D-2 erratum), W3 (freshness /
hash), W4 (completeness), and W5 (referential integrity) are separate
implementation sprints and are absent from this file by design. F-1 remains
open; no specification below asserts identifier uniqueness.
"""

from scripts.build_manifest import load_manifest, validate_manifest


def test_w1_committed_manifest_passes_the_structural_gate():
    """W1 — `validate_manifest(load_manifest())` succeeds against the committed Manifest.

    The repository's first executable Manifest specification (plan §11.2, W1).
    `validate_manifest` raises `ManifestValidationError` on any structural
    contract violation, so an uncaught call *is* the assertion: the committed
    `sample_rag/knowledge_manifest.json` is readable, is valid JSON, carries
    the contracted `manifest_version` and `documents` fields, and every entry
    carries every required field at its required type.
    """
    validate_manifest(load_manifest())


def test_w1_structural_gate_validates_the_committed_artifact_itself():
    """W1 — the gate returns the object it was given, evidencing what it validated.

    `validate_manifest` is contracted to be read-only and to return *"the exact
    same object on success"* rather than a normalized or repaired copy. Asserting
    identity therefore establishes two things at once: the gate above ran over
    the artifact as committed, not over a reconstruction of it, and the gate
    left it unmodified — the observational property `docs/roadmap.md` §6 requires
    of Layer 1 (plan §7.2: DQV produces no artifact).
    """
    manifest = load_manifest()

    assert validate_manifest(manifest) is manifest


def test_w1_structural_gate_is_repeatable_over_the_committed_manifest():
    """W1 — the gate yields the same verdict and the same manifest on every run.

    A validation layer that reports repository state must report it identically
    when nothing has changed; a gate that passed once and failed next run would
    make every DQV result unfalsifiable. This is a property of the manifest read
    plus the structural gate, and is distinct from the construction determinism
    of `KnowledgeSource.load()` already specified by Specification Family 2
    (plan §6.1 row 10) — nothing about `Document` construction is re-specified
    here.
    """
    first = validate_manifest(load_manifest())
    second = validate_manifest(load_manifest())

    assert first == second
