"""Specification Family 4 — Data Quality Validation.

Sprint P3.1.8.1A implemented **Phase W1 — Manifest structural gate** from the
approved `docs/DATA_QUALITY_VALIDATION_PLAN.md` §11.2. Sprint P3.1.8.1B adds
**Phase W2 — Identifier uniqueness (DQ-2)**, closing finding **F-1**.

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

Why W1 has no synthetic negative case
--------------------------------------
Plan §12 requires each DQV **check** to pair a synthetic negative case with a
real-corpus positive one. W1 is not such a check: §11.2 records its failure
classes as "—", and §8.2 assigns *"Manifest structural failures
(missing/mistyped `manifest_version`, `documents`, or a required entry field)"*
to the **Structural Artifact Validation** layer and `ManifestValidationError`,
explicitly **not** to DQV. Constructing malformed manifests here would specify
another layer's failure surface, which §11.3 bars. W1 asserts only that the
committed artifact clears the gate that layer already owns. The synthetic
negative cases arrive with DQ-2 (W2) onward, which are DQV failure classes.

W2 — the approved uniqueness invariant, and its two predicates
--------------------------------------------------------------
The invariant W2 enforces is **not invented here**. `docs/DOCUMENT_CONTRACT.md`
§8.9 (**Contract Erratum E-1**, approved at Sprint P3.1.8.0B, resolving finding
D-2) records it as binding — *"A corpus in which two `Document` values returned
by one `KnowledgeSource.load()` share an `id` does not conform to this
contract"* — corpus-scoped, inherited from `docs/MILESTONE_1A.md` build item 1,
and enforced here: *"Uniqueness is a cross-artifact, collection-level property
and is enforced by the Data Quality Validation pytest layer."* §8.9 item 5 adds
that a duplicate is **detected** by DQV, not **prevented** by construction, so
no specification below expects `load()` to raise.

Plan §11.2 W2 requires **both** predicates, specified independently:

    A.  `documents[].id` read from the Manifest are pairwise distinct
    B.  `[d.id for d in KnowledgeSource().load()]` are pairwise distinct

§8.9 item 5 and plan §9.2 state that under identity strategy S1 — where
`Document.id` is read from the Manifest and never derived — these *are the same
predicate*. Neither is therefore inferred from the other: specifying both makes
that coincidence **a protected property rather than an assumption**. If a future
sprint changed the identity strategy so the two diverged, one predicate would
fail while the other passed, and the divergence would surface here rather than
silently.

The two predicates are asserted **separately and never compared to each other**.
Asserting agreement *between* the Manifest ids and the loaded ids is referential
integrity — phase W5, and `docs/DOCUMENT_CONTRACT.md` §8.5's still-open
deferral — not W2.

Corpus scale, recorded not glossed (plan §12, §16 O-5)
-------------------------------------------------------
The committed corpus is one document. That does not weaken W1 — a structural
gate is decidable from the artifact alone at any size (§6.1 row 1) — but it is
the reason no specification below counts entries or asserts anything about how
many there are. Per Register §3.5's finding **I-6**, no specification names a
corpus filename.

It does, however, make **W2 vacuously true on the committed corpus**: one id
cannot collide with itself. Plan §12 requires this be stated rather than
glossed. The real-corpus specifications below are therefore *regression
protection for a corpus that will grow*, and they are honest about carrying no
protective force today. **W2's protection comes from its synthetic
specifications**, which present a two-entry corpus sharing one id — the exact
shape Sprint P3.1.7.1 used to reproduce F-1 — and confirm the predicate reports
it. Both the real and the synthetic cases run the same predicate function, so
the synthetic cases genuinely exercise what the real ones assert.

Scope boundary
--------------
W3 (freshness / hash), W4 (completeness), and W5 (referential integrity) are
separate implementation sprints and are absent from this file by design.
"""

import json

from scripts.build_manifest import load_manifest, validate_manifest


def duplicate_ids(ids):
    """Return the ids appearing more than once in `ids`, sorted, without repetition.

    The W2 predicate, expressed exactly once. A helper is introduced here only
    because no repository function satisfies it: `validate_manifest` deliberately
    excludes uniqueness (plan §5.3, and §11.3 bars adding it there), and
    `scripts/build_chunks.py`'s `_validate_collection_invariants` — the only
    existing uniqueness logic in the repository — is private, is shaped for
    `chunks.json` entries (it also requires `document_id`, `chunk_index`, and
    character offsets), and raises `ChunkValidationError`. Calling it with
    manifest entries would fail on a missing key, not report a duplicate id.

    Reporting *which* ids collide rather than returning a bool is what lets one
    predicate serve both the real-corpus and the synthetic specifications: the
    positive case asserts the report is empty, the negative case asserts the
    report names the planted duplicate. A bool would have forced the synthetic
    case to restate the predicate, which is the duplication
    `docs/ENGINEERING_TRACEABILITY_REGISTER.md` §5 rates a **High** drift risk.

    Pure and read-only: it counts, and does not deduplicate, repair, normalize,
    or raise.
    """
    return sorted({identifier for identifier in ids if ids.count(identifier) > 1})


# --- W1: Manifest structural gate ------------------------------------------


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


# --- W2 / DQ-2: identifier uniqueness (F-1) ---------------------------------


def test_dq2_committed_manifest_document_ids_are_pairwise_distinct(real_manifest_entries):
    """W2 predicate A — `documents[].id` in the committed Manifest are pairwise distinct.

    Read from the artifact itself via the `real_manifest_entries` fixture, which
    parses `knowledge_manifest.json` with `json` directly rather than through
    any code path that produced or consumes those values.

    Vacuous on today's one-document corpus (see the module docstring). Its
    protective force is regression cover as the corpus grows; the live check on
    this predicate is the synthetic specification below.
    """
    ids = [entry["id"] for entry in real_manifest_entries]

    assert duplicate_ids(ids) == []


def test_dq2_loaded_document_ids_are_pairwise_distinct(real_documents):
    """W2 predicate B — `[d.id for d in load()]` are pairwise distinct.

    Asserted independently of predicate A, not inferred from it. Under identity
    strategy S1 the two coincide (`docs/DOCUMENT_CONTRACT.md` §8.9 item 5); this
    specification is what makes that coincidence protected rather than assumed.

    This is the predicate Contract Erratum E-1 states in its own terms: two
    `Document` values returned by one `KnowledgeSource.load()` must not share an
    `id`. Vacuous on today's corpus, for the same reason as predicate A.
    """
    ids = [document.id for document in real_documents]

    assert duplicate_ids(ids) == []


def test_dq2_duplicate_manifest_document_ids_are_detected(synthetic_corpus):
    """W2 predicate A, synthetic — a Manifest carrying one id twice is reported.

    Reproduces F-1's recorded shape: two entries sharing `id: "dup"`
    (`docs/ENGINEERING_TRACEABILITY_REGISTER.md` §3.1, independently reproduced
    at Sprint P3.1.7.1). Distinct `source` values, so the only property under
    test is the duplicated identifier.

    The entries are read back from the synthetic artifact the same way the real
    specification reads the committed one, and run through the same predicate —
    so this case exercises the check the real case asserts, not a restatement of
    it. The synthetic Manifest is never validated structurally: `entries()`
    writes `id` and `source` only, and W1's structural gate is not W2's concern.
    """
    synthetic_corpus.entries(("dup", "documents/a.txt"), ("dup", "documents/b.txt"))

    entries = json.loads(synthetic_corpus.manifest_path.read_text(encoding="utf-8"))["documents"]
    ids = [entry["id"] for entry in entries]

    assert duplicate_ids(ids) == ["dup"]


def test_dq2_duplicate_loaded_document_ids_are_detected(synthetic_corpus):
    """W2 predicate B, synthetic — `load()` returning two `Document`s with one id is reported.

    The end state F-1 actually recorded: construction accepts the duplicate
    manifest silently and returns two `Document` values sharing an id, raising
    nothing. Erratum E-1 item 5 confirms this is correct construction behaviour
    — the duplicate is *detected* by Data Quality Validation, not *prevented* by
    `load()` — so this specification asserts the successful load first, then
    reports the collision the load carried through.
    """
    synthetic_corpus.text_file("documents/a.txt", "first document")
    synthetic_corpus.text_file("documents/b.txt", "second document")
    synthetic_corpus.entries(("dup", "documents/a.txt"), ("dup", "documents/b.txt"))

    documents = synthetic_corpus.load()
    ids = [document.id for document in documents]

    assert len(documents) == 2
    assert duplicate_ids(ids) == ["dup"]
