"""Specification Family 4 — Data Quality Validation.

Sprint P3.1.8.1A implemented **Phase W1 — Manifest structural gate** from the
approved `docs/DATA_QUALITY_VALIDATION_PLAN.md` §11.2. Sprint P3.1.8.1B added
**Phase W2 — Identifier uniqueness (DQ-2)**, closing finding **F-1**. Sprint
P3.1.8.1C added **Phase W3 — Freshness / integrity (DQ-1)**. Sprint P3.1.8.1D
added **Phase W4 — Completeness, Case A (DQ-3)**. Sprint P3.1.8.1E added
**Phase W5 — Referential integrity (DQ-4)**. **Sprint 1B.1 (Corpus Integrity)
adds Phase W6's unblocked half — DQ-5 (chunk validity) and DQ-6 (chunk
referential integrity)**, register capabilities **1B-08** and **1B-09**.

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
That protection is measured rather than asserted:
`docs/ENGINEERING_TRACEABILITY_REGISTER.md` §6 records mutants **M20** (a
derived `Document.id`), **M21** (a duplicated `Document`), and **M22** (a
truncated enumeration) as **KILLED** by the DQ-4 specifications below.

The synthetic specification below is consequently **not** a negative case. That
deviation from plan §13's synthetic-negative criterion is an owner-approved
governance deviation, and `docs/ENGINEERING_TRACEABILITY_REGISTER.md` §3.7
(**P3.1.8.2-D1**) — not this docstring — is its authoritative record: it holds
the determination, its reasoning, its scope, and its approval. Retained here as
implementation context only: no synthetic corpus can manufacture a DQ-4
violation without fabricating a state `load()` cannot produce, so the
specification exercises the correspondence over a three-document corpus
instead — the scale the committed corpus cannot supply, and precisely what O-5
means by *"synthetic cases carry the protection"*.

**One-to-one is DQ-4's cardinality, not a restatement of DQ-2.** Plan §9.1
records §8.5's one-to-one relationship as *"the cardinality DQ-4 asserts"*. A
duplicate `documents[].id` would break that cardinality *and* violate DQ-2, so
both checks would fail together — which is correct, and is why the plan
specifies them as separate claims under separate phases. W5 asserts cardinality;
it does not assert uniqueness, and ownership of F-1 stays with W2.

Scope boundary
--------------
W1–W5 complete the DQ-1 … DQ-4 checks planned for Sprint P3.1.8.1. **Sprint
1B.1 adds W6's chunk-dependent half** — DQ-5 (register **1B-08**) and DQ-6
(register **1B-09**) — whose recorded blocker has cleared: `sample_rag/chunks.json`
did not exist when plan §11.2 scoped W6 and does exist now.

**DQ-7 remains blocked** on the Index Layer and an `EmbeddingProvider`
implementation (plan §8.1, §16 open item O-6), which are register **1B-10**,
**1B-03** and **1B-01**. It is absent from this file for that reason, not by
oversight, and Sprint 1B.1 does not implement it.

W6 and the single-artifact validator (plan §6.1 rows 5 and 7)
--------------------------------------------------------------
`scripts/build_chunks.py`'s `validate_chunks` already owns everything decidable
from `chunks.json` alone: the container, the six field types, invariants 1, 2,
4, 5, 6 and 7. Plan §6.1 assigns that to **Structural Artifact Validation**
(row 5), and §6.2 resolves the collision with DQV explicitly — *"Row 7 vs.
`validate_chunks()` → DQV. `docs/CHUNK_VALIDATION_PLAN.md` §P5 explicitly
declined 'a fifth layer inside `validate_chunks()` itself'."*

W6 therefore restates none of it. DQ-5 calls the existing gate rather than
reimplementing it, and adds only what the gate does not decide: that the
committed collection carries **exactly** the contract's six fields (§17 —
*"No fields beyond the six above exist in this version of the contract"*), and
that each `id` is the **derived** value §17 specifies rather than merely a
unique one. DQ-6 is cross-artifact by construction (plan §6.1 row 7) and could
not live in a single-artifact validator at all.

What W6 protects that nothing protected before
-----------------------------------------------
A Manifest cataloguing a document the chunk collection does not cover was
undetectable at HEAD: `validate_chunks` cannot see the Manifest, and no DQV
check read `chunks.json`. Corpus expansion made that reachable in practice.
`test_dq6_every_manifest_document_is_represented_in_the_chunk_collection` is
the specification that closes it.
"""

import json

import pytest

from scripts.build_chunks import (
    REQUIRED_CHUNK_FIELDS,
    ChunkValidationError,
    load_chunks,
    validate_chunks,
)
from scripts.build_manifest import (
    DOCUMENTS_ROOT,
    SAMPLE_RAG_ROOT,
    compute_sha256,
    discover_documents,
    load_manifest,
    normalize_source_path,
    validate_manifest,
)

from sample_rag.chunker import generate_chunk_id
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

    Deliberately **not** a negative case, under the owner-approved governance
    deviation whose authoritative record is
    `docs/ENGINEERING_TRACEABILITY_REGISTER.md` §3.7 (**P3.1.8.2-D1**). A
    `Document.id` without a Manifest entry cannot be produced by `load()` under
    strategy S1, so manufacturing one would require fabricating a state the
    repository cannot reach.

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


# --- W6 predicates ----------------------------------------------------------
#
# Each returns a *report* rather than a bool, for the reason `duplicate_ids`
# states: one predicate then serves both the real-corpus specification (assert
# the report is empty) and the synthetic negative (assert the report names the
# planted defect). A bool would force the synthetic case to restate the
# predicate — the duplication `docs/ENGINEERING_TRACEABILITY_REGISTER.md` §5
# rates a **High** drift risk.
#
# All five are pure, read-only, and total functions of their arguments: no
# filesystem access, no iteration-order dependence (every report is sorted),
# no clock, no environment. Plan §7.5.


def chunks_with_unexpected_fields(entries):
    """Return `(chunk_index_position, sorted_actual_fields)` for entries whose
    field set is not exactly the Chunk Contract's six.

    `docs/CHUNK_CONTRACT.md` §17 — *"**No fields beyond the six above exist in
    this version of the contract.** Every candidate field evaluated in Section
    15 is explicitly deferred, not silently included as optional."*

    `validate_chunks` cannot make this claim: `_validate_chunk_entry` iterates
    `REQUIRED_CHUNK_FIELDS` and checks presence and type, so it detects a
    *missing* field and is silent about an *extra* one. The deferral in §15 is
    what makes the difference load-bearing — a field appearing here would be a
    deferred candidate arriving without the governance §15 requires.

    The expected set is read from `REQUIRED_CHUNK_FIELDS` rather than written
    out, so this predicate cannot drift from the validator's own notion of the
    contract's fields.
    """
    expected = set(REQUIRED_CHUNK_FIELDS)
    return [
        (position, sorted(entry))
        for position, entry in enumerate(entries)
        if set(entry) != expected
    ]


def misderived_chunk_ids(entries):
    """Return `(stored_id, expected_id)` for entries whose `id` is not the
    contract's positional derivation.

    `docs/CHUNK_CONTRACT.md` §17 — *"`id` … Globally unique, deterministic
    identifier, **derived from position (`document_id` + `chunk_index`), not
    content**"* (§10, §14.1).

    This is not invariant 7 restated. `validate_chunks`'
    `_validate_collection_invariants` asserts ids are pairwise *distinct*;
    distinctness is satisfied by any injective function, including a
    content-derived digest — which is precisely what §17 rules out. Uniqueness
    and derivation are different guarantees, and only one of them was enforced
    at HEAD.

    `generate_chunk_id` is called rather than reproduced. Reimplementing
    `sha256(f"{document_id}:{chunk_index}")[:16]` here would make the
    specification agree with a *copy* of the rule instead of the rule, and
    would survive a change to the real one.
    """
    return [
        (entry["id"], generate_chunk_id(entry["document_id"], entry["chunk_index"]))
        for entry in entries
        if entry["id"] != generate_chunk_id(entry["document_id"], entry["chunk_index"])
    ]


def orphaned_chunk_document_ids(entries, known_document_ids):
    """Return the `document_id` values in `entries` absent from `known_document_ids`.

    The foreign-key direction `docs/CHUNK_CONTRACT.md` §11 freezes —
    *"`document_id` **must equal** the corresponding entry's `id` field in
    `knowledge_manifest.json`'s `documents[]` array"* — and which §11 then
    defers by name: *"Referential integrity … is **not** part of this
    structural contract … deferred to P2.4 (Chunk Validation) or later."* Plan
    §6.1 row 7 is where "or later" landed.

    Sorted, so the report does not depend on set iteration order (plan §7.5).
    """
    return sorted({entry["document_id"] for entry in entries} - set(known_document_ids))


def unchunked_document_ids(entries, documents):
    """Return the ids of documents that have chunkable text and no chunks.

    The Manifest → chunks direction. This is the condition that was
    undetectable at HEAD, and it is deliberately **not** stated as *"every
    document has at least one chunk"*, because that would contradict the
    cardinality `docs/CHUNK_CONTRACT.md` §11 freezes — *"one document produces
    **zero** or more chunks (1:N)"* — and plan §8.2, which classifies empty
    `Document.text` as *"**Not a failure at all** — legal, and legally produces
    zero chunks."*

    The guard is therefore `text.strip()`. Plan §8.2 words the legal-zero case
    as *empty* text; the Chunker's actual zero-chunk condition is slightly
    wider — `detect_structural_boundaries` returns `[]` for any text with no
    non-whitespace run, because `_strip_span` discards whitespace-only spans,
    and invariant 1 (*non-empty*) is what forces that. Using `.strip()` keeps
    this predicate from reporting a whitespace-only document as a defect. The
    widening is recorded rather than assumed — see the Sprint 1B.1 evidence
    report, Engineering Findings.

    This does not re-specify the Chunker. It asserts no chunk count, no
    boundary, and no span; only that a document with chunkable content is
    represented at all.
    """
    chunked = {entry["document_id"] for entry in entries}
    return sorted(
        document.id
        for document in documents
        if document.text.strip() and document.id not in chunked
    )


def reconstruction_failures(entries, documents_by_id):
    """Return `(chunk_id, stored_text, reconstructed_text)` for entries whose
    text is not the span its offsets name in the parent document.

    **Chunk invariant 3 in full form** — `docs/CHUNK_CONTRACT.md` §17:
    *"`text == document_text[character_start:character_end]` (half-open, Python
    slicing semantics)"*. Plan §8.1 names exactly this as DQ-6's second half,
    and §6.1 row 7 assigns *"Chunk invariant 3's full substring form"* to DQV.

    `validate_chunks` enforces only invariant 2, `len(text) == end - start`.
    That is the form decidable without the parent document, and it is strictly
    weaker: a chunk carrying the *right length* of the *wrong* text satisfies
    it. Closing that gap requires the document text, which is a second
    artifact — which is why the contract deferred it and why it lands here.

    Offsets are Unicode code points (§17), and Python string slicing is
    code-point indexed, so the comparison is the contract's semantics directly.
    Chunks whose `document_id` does not resolve are skipped, not reported: that
    is `orphaned_chunk_document_ids`' claim, and reporting it twice would make
    one defect fail two specifications for two different stated reasons.
    """
    failures = []
    for entry in entries:
        document = documents_by_id.get(entry["document_id"])
        if document is None:
            continue
        reconstructed = document.text[entry["character_start"] : entry["character_end"]]
        if entry["text"] != reconstructed:
            failures.append((entry["id"], entry["text"], reconstructed))
    return failures


def chunk_entry(document_id, chunk_index, text, character_start):
    """Build one contract-shaped chunk entry for a synthetic collection.

    A fixture helper, not a second Chunker: `id` comes from `generate_chunk_id`
    and offsets are supplied by the caller, so a synthetic entry is well-formed
    by default and each negative case perturbs exactly one property.
    """
    return {
        "id": generate_chunk_id(document_id, chunk_index),
        "document_id": document_id,
        "text": text,
        "chunk_index": chunk_index,
        "character_start": character_start,
        "character_end": character_start + len(text),
    }


# --- W6 / DQ-5: chunk validity as a corpus property -------------------------


def test_dq5_committed_chunk_collection_passes_the_contract_gate(real_chunk_collection):
    """W6 / DQ-5 — `validate_chunks(load_chunks())` succeeds against the committed collection.

    The chunk counterpart of W1, and it closes the same class of gap. Until
    now the committed `sample_rag/chunks.json` was validated only when
    `scripts/build_chunks.py` `main()` was run by hand, or incidentally by
    `scripts/run_retrieval.py` at runtime. No specification asserted that the
    *artifact in the repository* conforms to the Chunk Contract, so a
    hand-edited or partially-regenerated collection could sit committed and
    green.

    `real_chunk_collection` is deliberately the **unvalidated** fixture. The
    existing `real_chunks` fixture chains `validate_chunks(load_chunks())`
    itself; using it here would make this specification assert a property its
    own fixture had already guaranteed — the trap `tests/conftest.py` records
    for `real_evidence_trace_collection`.

    Reuse, not reimplementation (plan §11.1): the gate is called, not restated.
    `validate_chunks` raises `ChunkValidationError` on the first violation in
    Representation → Entity → Collection order, so a failure here names the
    offending entry and the invariant it broke.

    This is corpus-scoped in the sense plan §8.1 distinguishes: the claim is
    about the committed corpus's chunk collection, not about an arbitrary
    collection the validator happens to be handed.
    """
    assert validate_chunks(real_chunk_collection) is real_chunk_collection


def test_dq5_committed_chunks_carry_exactly_the_six_contract_fields(real_chunk_collection):
    """W6 / DQ-5 — no committed chunk carries a field the contract does not define.

    `docs/CHUNK_CONTRACT.md` §17's closing clause, which no code enforces:
    *"No fields beyond the six above exist in this version of the contract.
    Every candidate field evaluated in Section 15 is explicitly deferred, not
    silently included as optional."*

    The guard is not decoration. §15 defers real candidates — an embedding
    reference among them — and Milestone 1B builds the Index Layer that would
    want one (register **1B-01**, **1B-03**, **1B-04**). This specification is
    what makes such a field arrive through the contract rather than through a
    serializer.

    Were `chunks[]` ever empty, the assertion below would pass vacuously; the
    non-empty guard makes that visible rather than silent.
    """
    entries = real_chunk_collection["chunks"]

    assert entries, "the committed chunk collection must contain at least one chunk"

    assert chunks_with_unexpected_fields(entries) == [], (
        "chunks carrying fields outside the Chunk Contract's six: "
        f"{chunks_with_unexpected_fields(entries)}"
    )


def test_dq5_committed_chunk_ids_are_derived_from_position(real_chunk_collection):
    """W6 / DQ-5 — every committed `id` is the positional derivation §17 specifies.

    `docs/CHUNK_CONTRACT.md` §17: *"derived from position (`document_id` +
    `chunk_index`), **not content**"*.

    Distinct from invariant 7, which `validate_chunks` already enforces:
    uniqueness is satisfied by any injective id function, so a collection whose
    ids were content digests would pass the existing gate and violate the
    contract. `misderived_chunk_ids`' docstring carries the full reasoning.

    No literal id is frozen here. The specification compares two computed
    values, exactly as DQ-1 compares two computed hashes — plan §12,
    *"Behaviour, not artefacts"*.
    """
    entries = real_chunk_collection["chunks"]

    assert entries, "the committed chunk collection must contain at least one chunk"

    assert misderived_chunk_ids(entries) == [], (
        f"chunk ids not derived from (document_id, chunk_index): {misderived_chunk_ids(entries)}"
    )


def test_dq5_an_extra_field_on_a_chunk_is_detected():
    """W6 / DQ-5, synthetic — a chunk carrying a seventh field is reported.

    The negative case plan §12 requires. It cannot be taken from the real
    corpus, which is correct by construction: `serialize_chunk` writes the six
    fields explicitly, so the committed artifact can only acquire a seventh by
    hand-editing or by a future serializer change — which is exactly the drift
    this check exists to catch.

    `embedding` is not an arbitrary choice: `docs/CHUNK_CONTRACT.md` §15
    evaluates and defers a vector representation, and Milestone 1B's Index
    Layer is the work that would introduce one.
    """
    entry = chunk_entry("doc-a", 0, "alpha", 0)
    entry["embedding"] = [0.0, 1.0]

    report = chunks_with_unexpected_fields([entry])

    assert report == [
        (
            0,
            [
                "character_end",
                "character_start",
                "chunk_index",
                "document_id",
                "embedding",
                "id",
                "text",
            ],
        )
    ]


def test_dq5_a_missing_field_on_a_chunk_is_detected():
    """W6 / DQ-5, synthetic — a chunk missing a contract field is reported.

    The other direction of the same predicate. `validate_chunks` also detects
    this, and detecting it twice is deliberate rather than redundant: the two
    layers make different claims, and the predicate here must be shown to be
    an equality over the field set rather than a one-sided superset test. A
    predicate that only caught extras would silently pass a truncated chunk.
    """
    entry = chunk_entry("doc-a", 0, "alpha", 0)
    del entry["character_end"]

    report = chunks_with_unexpected_fields([entry])

    assert report == [
        (0, ["character_start", "chunk_index", "document_id", "id", "text"])
    ]


def test_dq5_a_content_derived_chunk_id_is_detected():
    """W6 / DQ-5, synthetic — an id derived from content rather than position is reported.

    The mutant §17 rules out by name, and the one the existing gate cannot see:
    the collection below has unique ids, contiguous indices, and valid offsets,
    so `validate_chunks` accepts it. Only the derivation check rejects it.
    """
    first = chunk_entry("doc-a", 0, "alpha", 0)
    second = chunk_entry("doc-a", 1, "beta", 6)
    second["id"] = "0123456789abcdef"

    assert validate_chunks({"schema_version": "1.0", "chunks": [first, second]}) is not None

    report = misderived_chunk_ids([first, second])

    assert report == [("0123456789abcdef", generate_chunk_id("doc-a", 1))]


def test_dq5_a_structurally_invalid_collection_is_refused_by_the_gate():
    """W6 / DQ-5, synthetic — the gate this check delegates to actually rejects.

    Guards the delegation itself. `test_dq5_committed_chunk_collection_passes_the_contract_gate`
    asserts a call succeeds; on its own that is compatible with a validator
    that never rejects anything. This specification shows the gate has teeth,
    so the passing assertion carries information.

    Not a restatement of `validate_chunks`' own specifications: one violation
    is presented, not the taxonomy. The Chunk Validation suite owns coverage of
    the validator; this owns the claim that DQ-5's delegation is meaningful.
    """
    entry = chunk_entry("doc-a", 0, "alpha", 0)
    entry["character_end"] = entry["character_start"]

    with pytest.raises(ChunkValidationError):
        validate_chunks({"schema_version": "1.0", "chunks": [entry]})


# --- W6 / DQ-6: chunk referential integrity ---------------------------------


def test_dq6_every_committed_chunk_resolves_to_a_manifest_entry(
    real_chunks, real_manifest_entries
):
    """W6 / DQ-6 — no committed chunk is an orphan against the Knowledge Manifest.

    `docs/CHUNK_CONTRACT.md` §11's foreign key, checked in the narrowing
    direction: every `chunks[].document_id` names a `documents[].id` that
    exists. Plan §6.1 row 7 assigns it to DQV because it is *"two artifacts by
    definition"* — `validate_chunks` cannot see the Manifest at all.

    The Manifest side is read from `real_manifest_entries`, which parses the
    artifact with `json` directly, so the comparison is against the committed
    artifact rather than against a code path that also produced it.
    """
    manifested_ids = {entry["id"] for entry in real_manifest_entries}

    assert real_chunks, "the committed chunk collection must contain at least one chunk"

    assert orphaned_chunk_document_ids(real_chunks, manifested_ids) == [], (
        "chunk document_id values with no Manifest entry: "
        f"{orphaned_chunk_document_ids(real_chunks, manifested_ids)}"
    )


def test_dq6_every_committed_chunk_resolves_to_a_loaded_document(real_chunks, real_documents):
    """W6 / DQ-6 — every committed chunk resolves to a `Document` from `load()`.

    Plan §6.1 row 7 names both targets — *"`Chunk.document_id` ↔
    **Manifest/`Document`**"* — and both are specified, for the reason plan
    §11.2 W2 gives for specifying two coinciding predicates: under identity
    strategy S1 the two sets coincide, and specifying both makes the
    coincidence a protected property rather than an assumption.

    The distinction is not hypothetical here. DQ-4 guarantees `Document` →
    Manifest; nothing guarantees that a chunk keyed to a manifested id is
    keyed to a document `load()` actually produced, which is what the Chunk
    Layer consumes.
    """
    loaded_ids = {document.id for document in real_documents}

    assert real_chunks, "the committed chunk collection must contain at least one chunk"

    assert orphaned_chunk_document_ids(real_chunks, loaded_ids) == [], (
        "chunk document_id values with no loaded Document: "
        f"{orphaned_chunk_document_ids(real_chunks, loaded_ids)}"
    )


def test_dq6_every_manifest_document_is_represented_in_the_chunk_collection(
    real_chunks, real_documents
):
    """W6 / DQ-6 — no catalogued document with chunkable text is missing from the collection.

    **The condition that was undetectable at HEAD.** A Manifest entry the chunk
    collection does not cover breaks no structural invariant: `validate_chunks`
    cannot see the Manifest, `validate_manifest` cannot see the chunks, and
    every DQ-1 … DQ-4 check passes over a manifest whose documents were never
    chunked. The repository could carry a stale `chunks.json` against a current
    Manifest and report a fully green suite.

    Stated as *documents with chunkable text*, not *all documents*, because
    `docs/CHUNK_CONTRACT.md` §11 fixes the cardinality at *"zero or more"* and
    plan §8.2 rules empty `Document.text` *"not a failure at all."*
    `unchunked_document_ids`' docstring carries the exact predicate and why it
    uses `.strip()`.

    No chunk count, boundary, or span is asserted. Chunking behaviour belongs
    to the Chunker and its own suite; this is a coverage claim only.
    """
    assert real_documents, "the committed corpus must contain at least one document"

    assert unchunked_document_ids(real_chunks, real_documents) == [], (
        "catalogued documents with chunkable text and no chunks: "
        f"{unchunked_document_ids(real_chunks, real_documents)}"
    )


def test_dq6_every_committed_chunk_text_equals_its_source_document_span(
    real_chunks, real_documents_by_id
):
    """W6 / DQ-6 — Chunk invariant 3 in full form, against the real corpus.

    `docs/CHUNK_CONTRACT.md` §17 invariant 3 — *"`text ==
    document_text[character_start:character_end]`"* — the reconstruction
    guarantee the repository has carried as a contract statement since Sprint
    P2.1 with nothing enforcing it end to end.

    `validate_chunks` enforces invariant 2 only, `len(text) == end - start`,
    which is what a single artifact can decide. Invariant 3 is strictly
    stronger and needs the parent document: a chunk with correct length and
    wrong content satisfies invariant 2 and violates the contract. That gap is
    the substance of this specification.

    What this protects concretely: it ties the chunk collection to the *bytes
    currently in the corpus*, through extraction and N1–N5 normalization. If a
    source document were edited and the collection not rebuilt, DQ-1 would
    catch the hash drift and this check would independently catch every chunk
    whose text no longer reconstructs — the two failures naming the same cause
    from opposite ends.

    No literal text is frozen. Both sides are computed from committed state,
    per plan §12's *"behaviour, not artefacts."*
    """
    assert real_chunks, "the committed chunk collection must contain at least one chunk"

    failures = reconstruction_failures(real_chunks, real_documents_by_id)

    assert failures == [], (
        f"chunks whose text does not reconstruct from its document span: "
        f"{[chunk_id for chunk_id, _, _ in failures]}"
    )


def test_dq6_an_orphaned_chunk_is_detected():
    """W6 / DQ-6, synthetic — a chunk keyed to an unknown document is reported.

    The negative case for the foreign-key direction. It cannot arise from the
    real corpus: `scripts/build_chunks.py` `main()` chunks the documents
    `load()` emits, so every `document_id` it writes is manifested by
    construction. The check exists for the collection that was *not* produced
    that way — hand-edited, partially regenerated, or carried across a Manifest
    change.
    """
    entries = [
        chunk_entry("doc-present", 0, "alpha", 0),
        chunk_entry("doc-absent", 0, "beta", 0),
    ]

    assert orphaned_chunk_document_ids(entries, {"doc-present"}) == ["doc-absent"]


def test_dq6_a_manifest_document_absent_from_the_chunk_collection_is_detected():
    """W6 / DQ-6, synthetic — a catalogued, chunkable document with no chunks is reported.

    The negative case for **the exact condition that motivated this sprint**:
    the Manifest advanced, the chunk collection did not, and nothing noticed.

    `_Document` below is a two-attribute stand-in, not a fixture corpus. The
    predicate consumes only `.id` and `.text` — the same minimal shape
    `sample_rag/chunker.py` `_validate_document` assumes — so a synthetic
    corpus would add a filesystem round trip without adding a claim.
    """

    class _Document:
        def __init__(self, id, text):
            self.id = id
            self.text = text

    documents = [_Document("doc-chunked", "alpha"), _Document("doc-stale", "beta")]
    entries = [chunk_entry("doc-chunked", 0, "alpha", 0)]

    assert unchunked_document_ids(entries, documents) == ["doc-stale"]


def test_dq6_a_document_with_no_chunkable_text_is_not_reported():
    """W6 / DQ-6, synthetic — a blank document with zero chunks is legal, not a defect.

    The complement of the case above, and the reason
    `unchunked_document_ids` guards on `text.strip()` rather than on presence.
    Plan §8.2 classifies empty `Document.text` as *"**Not a failure at all** —
    legal, and legally produces zero chunks"*, and `docs/CHUNK_CONTRACT.md`
    §11 fixes the cardinality at *"zero or more."*

    Both the empty and the whitespace-only case are presented, because the
    Chunker treats them identically — `detect_structural_boundaries` returns
    `[]` for either — while plan §8.2 words only the first. Specifying both is
    what keeps this check from reporting a legal corpus as broken.
    """

    class _Document:
        def __init__(self, id, text):
            self.id = id
            self.text = text

    documents = [_Document("doc-empty", ""), _Document("doc-blank", "   \n\t  ")]

    assert unchunked_document_ids([], documents) == []


def test_dq6_a_chunk_whose_text_does_not_reconstruct_is_detected():
    """W6 / DQ-6, synthetic — right length, wrong content, and invariant 3 catches it.

    The mutant that separates invariant 3 from invariant 2. `"beta"` and
    `"gamm"` are both four characters, so `len(text) == end - start` holds and
    `validate_chunks` accepts the entry — asserted below, so the distinction is
    demonstrated rather than claimed. Only reconstruction against the parent
    document rejects it.
    """

    class _Document:
        def __init__(self, id, text):
            self.id = id
            self.text = text

    document = _Document("doc-a", "alpha beta gamma")
    entry = chunk_entry("doc-a", 0, "beta", 6)
    entry["text"] = "gamm"

    assert validate_chunks({"schema_version": "1.0", "chunks": [entry]}) is not None

    failures = reconstruction_failures([entry], {"doc-a": document})

    assert failures == [(entry["id"], "gamm", "beta")]


def test_dq6_reconstruction_skips_chunks_whose_document_does_not_resolve():
    """W6 / DQ-6, synthetic — an orphan is reported once, by the check that owns it.

    Boundary between two predicates. An orphaned chunk has no parent document
    to reconstruct against; treating that as a reconstruction failure would
    make one defect fail two specifications for two different stated reasons,
    and would leave a reader unable to tell which claim the corpus actually
    broke.

    `orphaned_chunk_document_ids` owns that defect. This specification fixes
    the division so a later change cannot quietly blur it.
    """
    entry = chunk_entry("doc-absent", 0, "alpha", 0)

    assert reconstruction_failures([entry], {}) == []
    assert orphaned_chunk_document_ids([entry], set()) == ["doc-absent"]
