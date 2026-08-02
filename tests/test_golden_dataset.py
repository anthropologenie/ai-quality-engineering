"""Specification Family 6 — Golden Dataset Authority.

Sprint P3.4.1 (`docs/MILESTONE_1A.md` build item 9, *"pytest suite run against
both datasets"*): promotes the Golden Dataset validation the repository has so
far performed at build time and by hand into permanent committed
specifications.

Until now `datasets/golden/resume_facts.json` was checked only as a side effect
of running `scripts/build_evidence_trace.py`, which reads it, and by the manual
grounding pass performed during Sprints P3.2.0/P3.2.1. Neither survives into a
future sprint: the builder is not run in CI, and a manual pass validates one
snapshot on one day. Every check below runs on every test run instead.

The load-bearing specification
-------------------------------
**GD-8** — every fact's `source_text` is a verbatim substring of its parent
`Document.text`, loaded through `KnowledgeSource().load()` — is the repository's
primary grounding guarantee and the reason this suite exists. Everything the
repository asserts downstream about retrieval, evaluation, metrics and diagnosis
is anchored to it: the Evidence Trace Dataset resolves a fact to chunks by
locating `source_text` inside the parent document's character frame
(`scripts/build_evidence_trace.py` `resolve_fact_chunks`), so a fact whose
`source_text` is a paraphrase rather than a quotation would silently produce
expected-chunk sets describing text the corpus does not contain — and every
metric computed against those expectations would be measuring a fiction.

GD-9 states the property that makes that resolution *unambiguous*, which GD-8
alone does not: `resolve_fact_chunks` uses `str.find`, which returns the **first**
occurrence. A `source_text` appearing twice in one document would resolve to the
first span silently, so uniqueness of occurrence is load-bearing in its own
right and is specified separately.

Reuse, not reimplementation
----------------------------
GD-10 asserts the repository's *own* existing detector agrees with GD-8:
`resolve_fact_chunks` raises `EvidenceTraceError` on exactly this divergence
(*"the Golden Dataset and the Document corpus have diverged"*). GD-8 states the
guarantee in the sprint's own terms and GD-10 holds the shipped detector to it —
they are two mechanisms, not one assertion written twice, and GD-11 exercises
the detector's negative direction, which the committed dataset (correctly) never
can.

Artifacts are read through `scripts/build_evidence_trace.py`'s `load_json` and
`FACTS_PATH`. No path, reader, or validation rule is re-implemented here.

What this suite does not own
-----------------------------
Resolution of the *references* facts carry — a `document_id` reaching the
Knowledge Manifest is asserted here as the fact record's own provenance
completeness (GD-6, GD-7), but QA-pair-to-fact and Evidence-Trace-to-fact
resolution belong to `tests/test_cross_dataset_integrity.py`. The Knowledge
Manifest itself is already specified by `tests/test_data_quality.py` (W1–W5)
and nothing here re-validates it.

Record schema — why the field list is frozen here
--------------------------------------------------
`datasets/SCHEMA.md` §8 fixes the *container* (`schema_version` + `facts[]`) and
deliberately leaves the per-record schema undefined, to be *"specified alongside
the first implementation of each artifact type."* That implementation shipped in
Sprint 1A.1 P4 and has never had an executable specification. GD-2 is it: the
seven fields the committed artifact carries, frozen so that a field silently
added, removed, or retyped in a later sprint fails here rather than surfacing as
a `KeyError` inside the Evidence Trace builder.

Corpus scale, recorded not glossed
-----------------------------------
The committed Golden Dataset holds 26 facts drawn from 2 catalogued documents.
No specification below asserts those counts — they are a fact about one dataset
snapshot, not a contract — but every specification quantifies over a set the
suite first asserts is non-empty, so none can pass vacuously.

Observational only. Every specification reads committed repository state and
writes nothing. Nothing here regenerates the Golden Dataset, runs a builder, or
repairs a record: per the Sprint P3.4.1 Repository Dependency Rule, the dataset
is verified exactly as stored.

GD-n labels are this file's own organizing labels for evidence, not proposed
repository terminology — the convention `docs/DATA_QUALITY_VALIDATION_PLAN.md`
§1 established for its own DQ-n and W-n labels.
"""

import json

import pytest

from scripts.build_evidence_trace import (
    FACTS_PATH,
    EvidenceTraceError,
    load_json,
    resolve_fact_chunks,
)

# `datasets/SCHEMA.md` §2 — every artifact under `datasets/golden/` carries this
# version, and a structural change must bump it rather than change shape under it.
SCHEMA_VERSION = "1.0"

# `datasets/SCHEMA.md` §3 / §6 — the three canonical sources, and the prefix every
# derived identifier carries. Only `resume` is populated at HEAD (§9); the other
# two are schema-valid empty stubs awaiting their source data, so the domain is
# stated in full and membership is what is asserted.
CANONICAL_SOURCES = frozenset({"resume", "job", "jobops"})

# The record schema `datasets/SCHEMA.md` §8 deferred to first implementation,
# frozen here. All seven are strings; none is optional.
CANONICAL_FACT_FIELDS = (
    "id",
    "source",
    "document_id",
    "document_source",
    "section",
    "fact",
    "source_text",
)


def duplicates(values):
    """Return the values appearing more than once, sorted, without repetition.

    The same shape as `tests/test_data_quality.py`'s `duplicate_ids`, and for the
    same reason: reporting *which* values collide rather than a bool is what lets
    one predicate serve a positive assertion and name the offender on failure.
    It is redefined rather than imported because that helper belongs to the
    Knowledge Manifest suite's W2 predicate; sharing it would couple two
    specification families whose subjects are unrelated.

    Pure and read-only: it counts, and does not deduplicate, repair, or raise.
    """
    values = list(values)
    return sorted({value for value in values if values.count(value) > 1})


# --- GD-1 … GD-2: container and record schema -------------------------------


def test_gd1_container_matches_the_schema_contract(real_facts_collection):
    """GD-1 — the container is `datasets/SCHEMA.md` §8's facts container, at §2's version.

    `{"schema_version": "1.0", "facts": []}`, and nothing else at the top level.
    The version is asserted rather than merely read: §2 requires a structural
    change to increment it, so an unchanged version alongside a changed shape is
    precisely the silent drift this specification exists to refuse.
    """
    assert set(real_facts_collection) == {"schema_version", "facts"}
    assert real_facts_collection["schema_version"] == SCHEMA_VERSION
    assert isinstance(real_facts_collection["facts"], list)


def test_gd2_every_fact_carries_exactly_the_canonical_fields(real_facts):
    """GD-2 — every record carries the seven canonical fields, each a string.

    Both directions: no field missing and no field added. A record that grew an
    eighth field would pass a missing-fields-only check while silently
    introducing a schema the repository has never ratified.

    The guard is not decoration — an empty dataset would satisfy the loop
    vacuously.
    """
    assert real_facts, "the committed Golden Dataset must contain at least one fact"

    for fact in real_facts:
        assert set(fact) == set(CANONICAL_FACT_FIELDS), (
            f"fact {fact.get('id')!r} fields {sorted(fact)} != {sorted(CANONICAL_FACT_FIELDS)}"
        )

        for field in CANONICAL_FACT_FIELDS:
            assert isinstance(fact[field], str), (
                f"fact {fact['id']!r} field {field!r} must be a string"
            )


def test_gd2_no_canonical_field_is_empty_or_whitespace(real_facts):
    """GD-2 — no required field is present-but-empty.

    A field carrying `""` satisfies every type check above while carrying no
    information. `source_text` is the one that matters most: the empty string is
    a substring of every document, so an empty `source_text` would pass GD-8's
    grounding check and resolve, through `resolve_fact_chunks`, to whichever
    chunk happens to contain offset zero.
    """
    for fact in real_facts:
        for field in CANONICAL_FACT_FIELDS:
            assert fact[field].strip(), (
                f"fact {fact['id']!r} field {field!r} is empty or whitespace only"
            )


# --- GD-3 … GD-5: identity ---------------------------------------------------


def test_gd3_fact_identifiers_are_pairwise_distinct(real_facts):
    """GD-3 — no two facts share an `id`.

    Duplicate detection at the dataset's identity level. Unlike the Knowledge
    Manifest's DQ-2, this is **not** vacuous on committed state: the dataset
    holds many facts, so the predicate quantifies over real collisions it could
    find. `scripts/build_evidence_trace.py` `main()` keys facts by `id` into a
    dict — a duplicate would not raise there, it would silently discard the
    earlier record and re-point every QA pair referencing it.
    """
    assert duplicates([fact["id"] for fact in real_facts]) == []


def test_gd4_fact_identifiers_follow_the_source_prefixed_convention(real_facts):
    """GD-4 — each `id` is `<source>_f<serial>`, per `datasets/SCHEMA.md` §6.

    §6 makes the source prefix carry provenance: *"preventing collisions across
    sources and making provenance recoverable from the ID alone without a
    lookup."* That guarantee holds only if the prefix agrees with the record's
    own `source` field, which is what is asserted — the id is checked against
    the record, not against a hardcoded literal, so this specification stays
    correct when the `job` and `jobops` sources populate.
    """
    for fact in real_facts:
        prefix = f"{fact['source']}_f"

        assert fact["id"].startswith(prefix), (
            f"fact id {fact['id']!r} does not carry its own source prefix {prefix!r}"
        )
        assert fact["id"][len(prefix):].isdigit(), (
            f"fact id {fact['id']!r} does not end in a numeric serial"
        )


def test_gd5_every_fact_declares_a_canonical_source(real_facts):
    """GD-5 — `source` is one of `datasets/SCHEMA.md` §3's three canonical sources."""
    for fact in real_facts:
        assert fact["source"] in CANONICAL_SOURCES, (
            f"fact {fact['id']!r} declares non-canonical source {fact['source']!r}"
        )


# --- GD-6 … GD-7: provenance completeness ------------------------------------


def test_gd6_every_fact_document_id_is_catalogued_by_the_manifest(
    real_facts, real_manifest_entries
):
    """GD-6 — every `document_id` resolves to a Knowledge Manifest entry.

    Provenance completeness in the direction that matters: a fact whose parent
    document the Manifest does not catalogue is a fact the repository cannot
    trace to a source file, and `scripts/build_evidence_trace.py`
    `build_evidence_trace_entry` refuses exactly this state at build time
    (*"references document …, which the Knowledge Manifest does not catalogue"*).

    The Manifest side is read from the artifact itself via
    `real_manifest_entries`, not through the code path that produced these
    values.

    The opposite direction is deliberately not asserted. A catalogued document
    from which no fact has been extracted is a legitimate corpus state — fact
    extraction is not required to be exhaustive — so asserting it would invent an
    invariant no repository authority states.
    """
    catalogued = {entry["id"] for entry in real_manifest_entries}
    unresolved = sorted(
        {fact["document_id"] for fact in real_facts if fact["document_id"] not in catalogued}
    )

    assert unresolved == [], f"fact document_ids absent from the Knowledge Manifest: {unresolved}"


def test_gd7_fact_document_source_agrees_with_the_manifest_entry(
    real_facts, real_manifest_entries
):
    """GD-7 — `document_source` equals the Manifest `source` for that `document_id`.

    Each fact carries provenance twice — once as identity (`document_id`) and
    once as a path (`document_source`) — and nothing in the repository keeps them
    in step. Only `document_id` is used downstream: the Evidence Trace builder
    joins on it and never reads `document_source`. A stale `document_source`
    would therefore never fail a build, and would misattribute the fact to a
    reader consulting the dataset directly.
    """
    source_by_id = {entry["id"]: entry["source"] for entry in real_manifest_entries}

    for fact in real_facts:
        assert fact["document_source"] == source_by_id[fact["document_id"]], (
            f"fact {fact['id']!r} document_source {fact['document_source']!r} disagrees with "
            f"the Manifest entry for {fact['document_id']!r}"
        )


# --- GD-8 … GD-11: grounding, the load-bearing guarantee ---------------------


def test_gd8_every_fact_source_text_is_verbatim_in_its_parent_document(
    real_facts, real_documents_by_id
):
    """GD-8 — `source_text` is a verbatim substring of `Document.text`.

    The repository's primary grounding guarantee, and the Sprint P3.4.1
    load-bearing specification. Document text is obtained through
    `KnowledgeSource().load()` — the same mechanism every other consumer uses, so
    what is verified is the text the repository actually reads, not a
    re-extraction of the source file.

    `source_text` is the *quotation*; `fact` is the repository's own restatement
    of it and is deliberately **not** checked against the document. Only the
    quotation is required to be verbatim, which is what makes character-offset
    chunk resolution possible at all.

    Verified previously by hand during Sprints P3.2.0/P3.2.1; permanent from
    here.
    """
    assert real_facts, "the committed Golden Dataset must contain at least one fact"

    ungrounded = [
        fact["id"]
        for fact in real_facts
        if fact["source_text"] not in real_documents_by_id[fact["document_id"]].text
    ]

    assert ungrounded == [], (
        f"facts whose source_text is not verbatim in its parent document: {ungrounded}"
    )


def test_gd9_every_fact_source_text_occurs_exactly_once(real_facts, real_documents_by_id):
    """GD-9 — `source_text` appears exactly once in its parent document.

    What makes GD-8's guarantee *usable*. `resolve_fact_chunks` locates the fact
    with `document_text.find(source_text)`, which returns the first occurrence
    and reports nothing about later ones; a `source_text` occurring twice would
    resolve to the first span silently, and the resulting `expected_chunk` set
    would describe a different passage than the fact was extracted from.

    A repeated occurrence is not a schema error — the text would still be
    verbatim, and GD-8 would still pass. It is specified separately because it is
    a distinct failure mode with a distinct consequence.
    """
    for fact in real_facts:
        occurrences = real_documents_by_id[fact["document_id"]].text.count(fact["source_text"])

        assert occurrences == 1, (
            f"fact {fact['id']!r} source_text occurs {occurrences} times in document "
            f"{fact['document_id']!r}; offset resolution would be ambiguous"
        )


def test_gd10_the_existing_grounding_detector_reports_no_divergence(
    real_facts, real_documents_by_id
):
    """GD-10 — `resolve_fact_chunks` raises for no committed fact.

    The repository's own shipped detector, held to GD-8's guarantee. It raises
    `EvidenceTraceError` on precisely this divergence — *"the Golden Dataset and
    the Document corpus have diverged"* — so an uncaught call over every fact is
    the assertion.

    This is not GD-8 restated. GD-8 states the guarantee directly; this runs the
    code path that *depends* on it, so if the detector's own resolution rule ever
    changed, the two would disagree here rather than silently.

    An empty chunk list is passed deliberately: the detector's grounding check
    runs before any chunk is inspected, and chunk resolution itself is
    cross-dataset work owned by `tests/test_cross_dataset_integrity.py`. The
    Chunk Corpus is out of scope for this sprint and is not read here.
    """
    for fact in real_facts:
        resolve_fact_chunks(fact, real_documents_by_id[fact["document_id"]].text, [])


def test_gd11_the_grounding_detector_reports_a_diverged_fact():
    """GD-11, synthetic — a `source_text` absent from the document is detected.

    GD-8's failure direction, which the committed dataset cannot exercise because
    it is (correctly) grounded. The fact is synthetic and the document text is a
    literal: nothing under `datasets/` or `sample_rag/` is read, written, or
    monkeypatched.

    The raised error is required to name the offending fact, per the fail-fast
    convention `docs/DATA_QUALITY_VALIDATION_PLAN.md` §8.4 sets — a detector that
    reports *that* the dataset diverged without reporting *where* leaves the next
    engineer to bisect 26 records by hand.
    """
    diverged = {
        "id": "resume_f999",
        "document_id": "synthetic-document",
        "source_text": "a sentence the document does not contain",
    }

    with pytest.raises(EvidenceTraceError) as raised:
        resolve_fact_chunks(diverged, "the document's actual text", [])

    assert "resume_f999" in str(raised.value)


# --- GD-12 … GD-13: logical consistency and determinism ----------------------


def test_gd12_no_two_facts_quote_the_same_source_text(real_facts):
    """GD-12 — `source_text` values are pairwise distinct.

    Content-level duplicate detection, distinct from GD-3's identity-level check:
    two facts with different ids quoting the same passage are the same fact
    recorded twice. Downstream they would resolve to the same chunks, so a QA
    pair citing both as separate evidence would appear multi-hop while drawing on
    a single passage — inflating `expected_reasoning_type` without adding
    evidence.
    """
    assert duplicates([fact["source_text"] for fact in real_facts]) == []


def test_gd12_no_two_facts_state_the_same_claim(real_facts):
    """GD-12 — `fact` restatements are pairwise distinct.

    The other half of content-level duplication. Two facts quoting different
    passages but restating them identically are indistinguishable to any
    consumer reading `fact` rather than `source_text`, including the manual
    review pass `docs/MILESTONE_1A.md` build item 10 requires.
    """
    assert duplicates([fact["fact"] for fact in real_facts]) == []


def test_gd13_the_dataset_reads_identically_on_every_load(real_facts_collection):
    """GD-13 — repeated reads of the committed artifact yield equal collections.

    A dataset authority that reported different content on successive reads would
    make every downstream evaluation unfalsifiable. This is a property of the
    artifact plus its reader, and is deliberately weaker than a byte-level claim
    — that is the next specification's subject.
    """
    assert load_json(FACTS_PATH) == real_facts_collection


def test_gd13_the_committed_artifact_is_in_canonical_serialized_form(real_facts_collection):
    """GD-13 — the artifact is byte-identical to its canonical serialization.

    Freezes representation, not content: 2-space indentation, insertion-order
    keys, one trailing newline — the convention `scripts/build_manifest.py`,
    `scripts/build_chunks.py` and `scripts/build_evidence_trace.py` all serialize
    with. A record reordered or reformatted in place is drift in an artifact
    `docs/MILESTONE_1A.md` treats as frozen, and without this specification it
    would be invisible to every other check here.

    **One documented difference from the builder-produced artifacts**: the Golden
    Dataset is hand-authored and predates that convention, and it carries literal
    en and em dashes rather than `\\uXXXX` escapes — `ensure_ascii=False`. That is
    stated rather than normalized, because normalizing it would mean modifying a
    repository authority, which this sprint must not do.

    Round-trips the *loaded committed collection*; it does not rebuild the
    dataset from its sources.
    """
    serialized = json.dumps(real_facts_collection, indent=2, ensure_ascii=False) + "\n"

    assert serialized == FACTS_PATH.read_text(encoding="utf-8")
