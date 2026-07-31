"""Specification Family 4 — Data Quality Validation.

Sprint P3.1.8.1A implemented **Phase W1 — Manifest structural gate** from the
approved `docs/DATA_QUALITY_VALIDATION_PLAN.md` §11.2. Sprint P3.1.8.1B added
**Phase W2 — Identifier uniqueness (DQ-2)**, closing finding **F-1**. Sprint
P3.1.8.1C added **Phase W3 — Freshness / integrity (DQ-1)**. Sprint P3.1.8.1D
added **Phase W4 — Completeness, Case A (DQ-3)**. Sprint P3.1.8.1E adds
**Phase W5 — Referential integrity (DQ-4)**.

W1 is the repository's first executable Manifest specification. Until now the
committed `sample_rag/knowledge_manifest.json` was validated only when
`scripts/build_manifest.py` was run by hand; `docs/MILESTONE_1A.md` build item
1 promised *"one pytest suite"* over the Manifest and the plan's §0 verified
that suite absent at HEAD. W1 closed that gap for **structure**; **W3 closes
its other half** — the *"hash comparison against the manifest"* build item 1
names literally, owed since Sprint P1.2.0 and never built.

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

W3 — what a hash comparison does and does not detect
-----------------------------------------------------
W3 asserts, for every Manifest entry, that `compute_sha256` of the file at
`documents[].source` equals the catalogued `documents[].hash`. This is DQ-1:
*"A catalogued `documents[].hash` no longer matches the SHA-256 of the file at
`documents[].source`"* (plan §8.1).

**The bound, stated explicitly because it is an implementation requirement and
not a footnote** (plan §11.2 W3, §9.1; `docs/DOCUMENT_CONTRACT.md` §8.8 item 2):

    `documents[].hash` is a SHA-256 digest of the SOURCE FILE'S BYTES, not of
    extracted text. W3 therefore detects SOURCE-BYTE DRIFT ONLY.

    W3 does NOT detect extraction-mechanism drift. If the `.docx` extraction
    mechanism changes so that `Document.text` changes while the underlying
    source file remains byte-identical, every specification below still passes.
    Nothing here is evidence about `Document.text`.

§8.8 item 2 records that consequence and is explicit that *"no detector is
designed, scoped, or required by this contract"* for mechanism drift. No
specification below invents one; the gap is documented, not closed. Reading
these specifications as a guarantee about `Document.text` is precisely the
over-reading plan §9.1 warns of.

Corpus scale — W3 differs from W2 here
---------------------------------------
W2's uniqueness predicate is vacuous on a one-document corpus. **W3's is not.**
A single entry carrying a real catalogued digest and a real file on disk is a
complete DQ-1 comparison, so the real-corpus specification below has full
protective force today — it would fail the moment the corpus file changed
without the Manifest being rebuilt. The synthetic specification is not
compensating for a vacuous real case here, as it is for W2; it exists because
plan §12 requires the negative direction to be exercised, and the committed
corpus is (correctly) fresh and so can never demonstrate detection.

No specification below freezes a digest. Plan §12 requires DQ-1 to *"compare
two computed values"* rather than assert a literal hash, because a digest is a
fact about one corpus snapshot; the synthetic case therefore computes its
expected hash with the same function under test rather than hardcoding one.

W4 — completeness in one direction only, and why
-------------------------------------------------
W4 enumerates `sample_rag/documents/**` filtered by `SUPPORTED_EXTENSIONS`,
`sorted(...)`, and asserts every such file has a `documents[]` entry, comparing
on `normalize_source_path`'s normalized form (plan §11.2 W4). This is DQ-3:
*"A corpus file exists beneath `sample_rag/documents/**` with an approved
extension but has no `documents[]` entry — the Case A silent-narrowing blind
spot"* (plan §8.1).

**The narrowing direction ONLY.** Plan §8.3 is explicit that the opposite
direction — a Manifest entry whose file is absent — must **not** be asserted
here:

    "Under Construction's accepted asymmetry (`docs/DOCUMENT_CONSTRUCTION_PLAN.md`
    §20.3), the opposite direction — a Manifest entry whose file is absent —
    already raises at Construction time. DQV must therefore assert only the
    narrowing direction (file present, entry absent); asserting the other
    direction would duplicate a Construction responsibility and violate §6's
    single-owner rule."

That direction is Case B, and it is already specified — `resolve_source_path`
raises, and `tests/test_knowledge_source_failures.py`'s
`test_case_b_manifest_entry_without_a_corpus_file_raises` covers it. Adding it
here would be literal duplication, not defence in depth. Nothing below asserts
it.

Case A is the asymmetric half Construction deliberately left open:
`docs/DOCUMENT_CONSTRUCTION_PLAN.md` §20.3 records that under strategy S1 the
Manifest — not the filesystem — is the corpus enumeration, so *"a file present
but unmanifested is silently excluded (detecting it needs the corpus/Manifest
diff deferred to Data Quality Validation)"*. W4 is that deferred detector. It
reports the divergence; it does not change Construction's behaviour, which
remains correct and unmodified.

Corpus scale — W4 is not vacuous
---------------------------------
Plan §16 open item **O-5** names **DQ-2 and DQ-4** as the checks made vacuously
true by the one-document corpus. **DQ-3 is deliberately not among them**, and
the enumeration bears that out: `sample_rag/documents/**` yields one supported
file today, so the real-corpus specification below quantifies over a non-empty
set and every element of it is genuinely compared against the Manifest. It
would fail the moment a supported file were added to the corpus without the
Manifest being rebuilt — which is precisely the Case A blind spot.

What the committed corpus *cannot* show is the failure itself: the Manifest is
currently complete, so detection can only be exercised synthetically. That is
the sole reason a synthetic specification exists here, and it is a different
reason from W2's, where the real-corpus case carries no force at all.

Per Register §3.5's finding **I-6**, no specification below names a corpus
filename; the enumeration is computed, never hardcoded.

W5 — referential integrity, and the guarantee that makes it tautological today
------------------------------------------------------------------------------
W5 asserts every `Document.id` returned by `load()` has a corresponding
`documents[]` entry, and that the correspondence is one-to-one (plan §11.2 W5;
`docs/DOCUMENT_CONTRACT.md` §8.5: *"Every `Document` returned by
`KnowledgeSource.load()` corresponds to exactly one `knowledge_manifest.json`
`documents[]` entry"*). This is DQ-4, the check §8.5 deferred to this layer as
*"a semantic/cross-artifact validation concern, not a structural one"*, and it
closes A8's deferral for the `Document` side.

**Why DQ-4's failure state cannot arise from the committed implementation.**
`sample_rag/knowledge_source.py` `load()` iterates `discover_manifest_entries()`
and, per identity strategy S1, reads `document_id = entry["id"]` and passes it
through unchanged — *"`Document.id` is read from the entry and passed through
unchanged (A5)"* — appending exactly one `Document` per entry. A `Document.id`
with no corresponding entry is therefore not merely improbable: it is
unreachable through normal repository execution, at **any** corpus size. This is
a structural guarantee of S1, and it is distinct from plan §16 open item
**O-5**, which records DQ-4 as vacuous for a different reason — the corpus holds
one document.

Both limits are real and neither is glossed:

    O-5 (scale)      one document, so the correspondence is trivially small
    S1 (structure)   the failure state cannot be produced by `load()` at all

**What the specifications below are therefore worth.** They are regression
protection, not live detection. They hold `load()` to strategy S1: were a future
sprint to derive `Document.id` rather than read it (strategies S2/S3, which
`docs/DOCUMENT_CONSTRUCTION_PLAN.md` §9.1 records as the rejected alternatives),
or to drop or duplicate entries while constructing, these specifications fail.
That is the protection the mutation pass measures, and it is the only honest
claim available — no synthetic corpus can manufacture a DQ-4 violation without
fabricating a state the repository cannot produce, and fabricating one would
specify a fiction rather than repository behaviour.

Consequently the synthetic specification below does **not** attempt a negative
case. It exercises the correspondence over a three-document corpus, which is the
scale the committed corpus cannot supply — precisely what O-5 means by
*"synthetic cases carry the protection"*. Plan §12's negative-case examples name
a duplicate id, a stale hash, and an unmanifested file — DQ-1, DQ-2, DQ-3 — and
pointedly do not name DQ-4.

**One-to-one is DQ-4's cardinality, not a restatement of DQ-2.** Plan §9.1
records §8.5's one-to-one relationship as *"the cardinality DQ-4 asserts"*. A
duplicate `documents[].id` would break that cardinality *and* violate DQ-2, so
both checks would fail together — which is correct, and is why the plan
specifies them as separate claims under separate phases. W5 asserts cardinality;
it does not assert uniqueness, and ownership of F-1 stays with W2.

Scope boundary
--------------
W1–W5 complete the DQ-1 … DQ-4 checks planned for Sprint P3.1.8.1. DQ-5, DQ-6,
and DQ-7 remain **blocked** on artifacts that do not exist at HEAD —
`sample_rag/chunks.json`, the Index Layer, and an `EmbeddingProvider`
implementation (plan §8.1, §11.2 W6, §16 open item O-6) — and are absent from
this file for that reason, not by oversight.
"""

import json

from scripts.build_manifest import (
    DOCUMENTS_ROOT,
    SAMPLE_RAG_ROOT,
    compute_sha256,
    discover_documents,
    load_manifest,
    normalize_source_path,
    validate_manifest,
)

from sample_rag.knowledge_source import resolve_source_path


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


# --- W3 / DQ-1: freshness / integrity ---------------------------------------


def test_dq1_every_committed_entry_hash_matches_its_source_file(real_manifest_entries):
    """W3 — every `documents[].hash` equals the SHA-256 of the file it catalogues.

    The check `docs/MILESTONE_1A.md` build item 1 promised — *"one pytest suite
    running hash comparison against the manifest"* — and Architectural AC 3's
    requirement that the Manifest be *"the sole source of truth that
    freshness/hash validation checks against"*.

    Two computed values are compared: the digest `compute_sha256` produces now,
    against the digest the Manifest catalogued when it was built. No literal
    digest appears here (plan §12). The source is resolved with Construction's
    own `resolve_source_path`, so the bytes hashed are the bytes
    `KnowledgeSource.load()` would read for this entry, not a path this
    specification re-derived.

    Source bytes only: a passing run says the catalogued files are unchanged on
    disk. It says nothing about `Document.text` — see the module docstring and
    `docs/DOCUMENT_CONTRACT.md` §8.8 item 2.

    Fail-fast within the test, naming the offending entry, per plan §8.4.
    """
    assert real_manifest_entries, "the committed Manifest must catalogue at least one document"

    for entry in real_manifest_entries:
        computed = compute_sha256(resolve_source_path(entry["source"]))

        assert computed == entry["hash"], (
            f"{entry['source']}: catalogued hash {entry['hash']} != computed {computed}"
        )


def test_dq1_source_file_changed_after_cataloguing_is_detected(synthetic_corpus):
    """W3, synthetic — a corpus file edited after cataloguing is reported as stale.

    DQ-1's actual failure mode, reproduced rather than simulated: the Manifest
    catalogues the file's true digest, the file is then edited, and the
    catalogued digest no longer describes it. The committed corpus is correctly
    fresh and so can never exercise this direction, which is why plan §12
    requires a synthetic negative case.

    The expected hash is computed by the same function under test rather than
    hardcoded, per plan §12 — a literal digest would freeze a fact about one
    snapshot. The manifest is written with all four contracted entry fields so
    the only property under test is freshness, not structure.
    """
    source = "documents/a.txt"
    path = synthetic_corpus.text_file(source, "content as catalogued")
    catalogued = compute_sha256(path)
    synthetic_corpus.manifest(
        {
            "manifest_version": "1.0",
            "documents": [
                {"id": "a", "source": source, "hash": catalogued, "indexed": False}
            ],
        }
    )

    synthetic_corpus.text_file(source, "content after an uncatalogued edit")

    entry = json.loads(synthetic_corpus.manifest_path.read_text(encoding="utf-8"))["documents"][0]
    computed = compute_sha256(resolve_source_path(entry["source"]))

    assert computed != entry["hash"]


# --- W4 / DQ-3: completeness, Case A ----------------------------------------


def test_dq3_every_committed_corpus_file_has_a_manifest_entry(real_manifest_entries):
    """W4 — every supported file under `sample_rag/documents/**` is catalogued.

    The Case A detector `docs/DOCUMENT_CONSTRUCTION_PLAN.md` §20.3 deferred to
    this layer: under strategy S1 the Manifest is the corpus enumeration, so a
    supported file present on disk but absent from `documents[]` is silently
    excluded by `load()` and nothing currently registers it.

    Enumeration reuses `discover_documents` — which applies the
    `SUPPORTED_EXTENSIONS` filter and skips hidden and `__pycache__` paths — and
    `normalize_source_path`, so the comparison is against the same normalized
    form `documents[].source` was written in. Neither is reimplemented here, and
    no filename is hardcoded (Register §3.5, I-6).

    Narrowing direction only. A Manifest entry whose file is absent is Case B,
    which raises at Construction and is specified in
    tests/test_knowledge_source_failures.py; asserting it here would duplicate a
    Construction responsibility (plan §8.3, §6).

    The guard is not decoration: were the enumeration ever empty, the assertion
    below would pass vacuously.
    """
    enumerated = sorted(
        normalize_source_path(path, SAMPLE_RAG_ROOT)
        for path in discover_documents(DOCUMENTS_ROOT)
    )
    manifested = {entry["source"] for entry in real_manifest_entries}

    assert enumerated, "the committed corpus must contain at least one supported document"

    unmanifested = [source for source in enumerated if source not in manifested]

    assert unmanifested == [], (
        f"corpus files present but absent from the Manifest: {unmanifested}"
    )


def test_dq3_corpus_file_absent_from_the_manifest_is_detected(synthetic_corpus):
    """W4, synthetic — a supported corpus file with no `documents[]` entry is reported.

    Case A's failure mode, which the committed corpus cannot exhibit because its
    Manifest is complete. Two supported files are placed in the corpus and only
    one is catalogued; the enumeration must report the other.

    A third file carries an extension outside `SUPPORTED_EXTENSIONS`. W4
    enumerates *"filtered by `SUPPORTED_EXTENSIONS`"* (plan §11.2 W4), so it must
    **not** be reported: Construction's `resolve_source_path` rejects that
    extension outright, meaning the file is not a corpus item at all and flagging
    it would be a DQ-3 false positive. Asserting the exact list, rather than
    merely that it is non-empty, is what holds both halves — the file that must
    be reported and the file that must not.

    `discover_documents` and `normalize_source_path` take their roots as
    arguments, so this specification passes the synthetic root directly — no
    module constant is monkeypatched for W4, and the functions under test are
    the committed ones.

    The unmanifested file is reported by its normalized source, not merely
    counted, so a failure names the offending file (plan §8.4).
    """
    synthetic_corpus.text_file("documents/catalogued.txt", "catalogued")
    synthetic_corpus.text_file("documents/unmanifested.txt", "present but never catalogued")
    synthetic_corpus.binary_file("documents/notes.pdf", b"outside SUPPORTED_EXTENSIONS")
    synthetic_corpus.entries(("a", "documents/catalogued.txt"))

    entries = json.loads(synthetic_corpus.manifest_path.read_text(encoding="utf-8"))["documents"]
    enumerated = sorted(
        normalize_source_path(path, synthetic_corpus.root)
        for path in discover_documents(synthetic_corpus.root / "documents")
    )
    manifested = {entry["source"] for entry in entries}

    unmanifested = [source for source in enumerated if source not in manifested]

    assert unmanifested == ["documents/unmanifested.txt"]


# --- W5 / DQ-4: referential integrity ---------------------------------------


def test_dq4_every_loaded_document_id_has_a_manifest_entry(real_documents, real_manifest_entries):
    """W5 — every `Document.id` from `load()` corresponds to a `documents[]` entry.

    DQ-4 as plan §8.1 states it: *"A `Document.id` returned by `load()` has no
    corresponding `documents[]` entry."* `docs/DOCUMENT_CONTRACT.md` §8.5
    deferred exactly this check to this layer; A8 recorded the same deferral.

    The two sides are read independently — `load()` for the `Document` side, and
    the `real_manifest_entries` fixture, which parses the artifact with `json`
    directly, for the Manifest side — so the comparison is against the committed
    artifact rather than against the code path that produced the values.

    Tautological on the committed implementation: S1 reads `Document.id` from the
    entry, so this cannot fail today at any corpus size. It is regression
    protection against an identity strategy that derived ids instead. See the
    module docstring.
    """
    assert real_documents, "the committed corpus must yield at least one Document"

    manifested_ids = {entry["id"] for entry in real_manifest_entries}
    unreferenced = [document.id for document in real_documents if document.id not in manifested_ids]

    assert unreferenced == [], (
        f"Document ids with no corresponding Manifest entry: {unreferenced}"
    )


def test_dq4_document_to_manifest_entry_correspondence_is_one_to_one(
    real_documents, real_manifest_entries
):
    """W5 — the `Document` ↔ Manifest entry correspondence is one-to-one.

    The cardinality `docs/DOCUMENT_CONTRACT.md` §8.5 freezes — *"Every `Document`
    returned by `KnowledgeSource.load()` corresponds to exactly one
    `knowledge_manifest.json` `documents[]` entry"* — and which plan §9.1 names
    as *"the cardinality DQ-4 asserts"*.

    Both directions are checked, because one alone does not establish a
    bijection: each `Document` must match exactly one entry, and the two
    collections must be the same size, so no entry is left uncorresponded.

    This is not DQ-2 restated. A duplicate `documents[].id` would break this
    cardinality and independently violate DQ-2; both would fail, correctly.
    Uniqueness remains W2's claim and F-1 remains W2's finding.
    """
    for document in real_documents:
        matching = [entry for entry in real_manifest_entries if entry["id"] == document.id]

        assert len(matching) == 1, (
            f"Document id {document.id!r} matched {len(matching)} Manifest entries, expected 1"
        )

    assert len(real_documents) == len(real_manifest_entries)


def test_dq4_correspondence_holds_across_a_multi_document_corpus(synthetic_corpus):
    """W5, synthetic — the correspondence holds over a corpus larger than one document.

    The committed corpus holds one document, which plan §16 open item **O-5**
    records as making DQ-4 vacuously true; O-5 states the protection comes from
    synthetic cases. This is that case: three documents, three entries, checked
    for the same correspondence the real specifications assert.

    Deliberately **not** a negative case. A `Document.id` without a Manifest
    entry cannot be produced by `load()` under strategy S1 — see the module
    docstring — so manufacturing one would require fabricating a state the
    repository cannot reach. Plan §12's negative-case examples name a duplicate
    id, a stale hash, and an unmanifested file; DQ-4 is not among them.

    What this specification does add over the real ones is scale: with three
    entries, a `load()` that dropped, duplicated, or reordered a `Document` would
    break the correspondence here while a one-document corpus could not reveal
    it.
    """
    synthetic_corpus.text_file("documents/a.txt", "alpha")
    synthetic_corpus.text_file("documents/b.txt", "beta")
    synthetic_corpus.text_file("documents/c.txt", "gamma")
    synthetic_corpus.entries(
        ("id-a", "documents/a.txt"),
        ("id-b", "documents/b.txt"),
        ("id-c", "documents/c.txt"),
    )

    documents = synthetic_corpus.load()
    entries = json.loads(synthetic_corpus.manifest_path.read_text(encoding="utf-8"))["documents"]
    manifested_ids = {entry["id"] for entry in entries}

    assert [document.id for document in documents if document.id not in manifested_ids] == []

    for document in documents:
        assert len([entry for entry in entries if entry["id"] == document.id]) == 1

    assert len(documents) == len(entries)
