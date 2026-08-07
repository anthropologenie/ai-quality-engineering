"""Specification Family 9 — Cross-Dataset Integrity.

Sprint P3.4.1 Work Package 5: validates the relationships *between* the
committed dataset authorities, which no single-artifact validator can see.

    Knowledge Manifest
            │
            ▼
    Golden Dataset
           ├──────────────┐
           ▼              ▼
    QA Pairs      Evidence Trace Dataset

Each artifact is separately well-formed under `tests/test_golden_dataset.py`,
`tests/test_qa_pairs.py` and `tests/test_evidence_trace_dataset.py`. That is not
sufficient: a QA pair citing `resume_f099` is structurally perfect and
semantically empty, and an Evidence Trace entry expecting a chunk id the corpus
does not contain would be scored as a retrieval failure forever, attributing to
the retriever a defect that lives in the dataset.

Why this belongs here and not in the artifacts' own validators
---------------------------------------------------------------
`scripts/build_evidence_trace.py` states the boundary its own gate observes —
*"Cross-artifact referential integrity … stays out of `validate_evidence_trace()`,
consistent with the boundary `docs/CHUNK_VALIDATION_PLAN.md` §P5 already drew for
`validate_chunks()`: structural checks live with the artifact's build script,
cross-artifact checks belong to the Data Quality Validation layer."* This file is
that layer for the Golden Dataset family, alongside `tests/test_data_quality.py`,
which owns the same responsibility for the Knowledge Manifest and the Document
corpus.

Reuse: the builder's derivation rules are the specification
------------------------------------------------------------
X-8 and X-9 assert the committed Evidence Trace agrees with
`derive_expected_reasoning_type` and `derive_expected_outcome` — the repository's
own shipped rules, imported and called, never restated. X-15 uses
`resolve_fact_chunks`, the same function the builder resolves evidence with.

**Nothing here regenerates the Evidence Trace Dataset.** X-15 asserts *coverage*
(every chunk a cited fact resolves to is present in `expected_chunk`), not
equality with a rebuilt entry, and no derived value is written anywhere. Asserting
a rebuilt dataset equals the committed one would be a specification of the
builder, not of the committed relationships, and the Sprint P3.4.1 Repository
Dependency Rule bars regenerating the artifact.

Directions asserted, and one deliberately not asserted
-------------------------------------------------------
Every reference is required to resolve — QA pair → fact, Evidence Trace entry →
QA pair, entry → document, entry → chunk — and orphan identifiers on the
referring side are refused in every case.

The **onto** direction is not asserted for facts: a committed fact that no QA
pair cites is a legitimate state. `docs/roadmap.md` §2.2's principle is *"one
verified fact → many question forms"*, not *every fact yields a question*; fact
extraction and question authoring are separate passes, and 7 of the 26 committed
facts are currently uncited. Requiring surjectivity would fail the repository for
a state no authority forbids. It *is* asserted for QA pairs, because the builder
guarantees exactly one Evidence Trace entry per pair — there the bijection is a
real invariant, and X-5 holds it.

Alignment to current canonical knowledge, added at Sprint 1B.2A
----------------------------------------------------------------
X-1 … X-16 all resolve a reference to whatever document a fact *names*. None
asks whether the Knowledge Manifest still designates that document canonical, so
a corpus evolution can leave the whole Golden Dataset citing superseded
knowledge with every specification above still green — internally consistent,
externally stale. X-17 closes that gap, and is the only specification here that
reads the Manifest's `canonical` flag. Its semantics follow Repository Owner
ruling **R-01 — Historical Knowledge Semantics** (Sprint 1B.2B): current
canonical knowledge defines repository truth, and historical knowledge is
legitimate evidence only where evaluating it against canonical knowledge is the
question's purpose.

Runtime components are not involved, per Work Package 5. No retriever is
constructed and no retrieval is executed; the only executed repository code is
artifact readers, the Document corpus loader, and the two pure derivation rules
named above.

Observational only. X-n labels are this file's own organizing labels, not
proposed repository terminology.
"""

from scripts.build_evidence_trace import (
    derive_expected_outcome,
    derive_expected_reasoning_type,
    resolve_fact_chunks,
)


# The two `docs/roadmap.md` §2.3 failure categories that evaluate *historical
# knowledge against current canonical knowledge*, per Repository Owner ruling
# **R-01 — Historical Knowledge Semantics**: historical knowledge exists solely
# as evaluation evidence, and the comparison is historical-vs-canonical, not
# version-vs-version. Both are structurally impossible to author against
# canonical knowledge alone — they require historical knowledge to remain
# reachable, which is why `docs/corpus/resume-corpus.md` retains superseded
# resume artifacts. Stated as a subset here rather than imported from
# `tests/test_qa_pairs.py`, whose frozenset is the full seven-category taxonomy:
# what X-17 needs is not the taxonomy but the two categories for which a
# non-canonical parent document is the point.
HISTORICAL_KNOWLEDGE_CATEGORIES = frozenset({"Stale Version", "Contradiction"})


def evidence_fact_ids(qa_pair):
    """The fact ids one QA pair cites: its parent first, then its supporting facts.

    The same evidence set `scripts/build_evidence_trace.py`
    `build_evidence_trace_entry` assembles — `[fact_id, *supporting_fact_ids]` —
    expressed once here so no specification below rebuilds it and they cannot
    drift apart in what they consider a citation.
    """
    return [qa_pair["fact_id"], *qa_pair["supporting_fact_ids"]]


def paired(real_evidence_trace, real_qa_pairs):
    """Zip Evidence Trace entries with their QA pairs, positionally.

    Positional pairing is sound only because X-5 specifies that the two datasets
    have equal length and identical order; every specification using this helper
    therefore depends on X-5, and a break in that ordering fails X-5 first rather
    than producing a silently misaligned comparison here.
    """
    return list(zip(real_evidence_trace, real_qa_pairs, strict=True))


# --- X-1 … X-4: QA Pairs → Golden Dataset ------------------------------------


def test_x1_every_qa_pair_resolves_to_a_committed_fact(real_qa_pairs, real_facts_by_id):
    """X-1 — every `fact_id` resolves to a fact in the Golden Dataset.

    The repository's traceability principle in executable form:
    `datasets/SCHEMA.md` §10, *"every question and Evidence Trace record
    deterministically references exactly one canonical fact ID — no implicit or
    inferred relationships."*

    `build_evidence_trace_entry` refuses an unresolvable citation at build time
    (*"references unknown fact ids"*), but the builder is not run in CI; this is
    the same guarantee made permanent.
    """
    assert real_qa_pairs, "the committed QA Dataset must contain at least one pair"

    unresolved = sorted(
        {
            pair["fact_id"]
            for pair in real_qa_pairs
            if pair["fact_id"] not in real_facts_by_id
        }
    )

    assert unresolved == [], f"QA pairs citing facts the Golden Dataset does not hold: {unresolved}"


def test_x2_every_supporting_fact_reference_resolves(real_qa_pairs, real_facts_by_id):
    """X-2 — every `supporting_fact_ids` entry resolves; no orphan identifiers.

    Supporting facts are what make a question multi-hop:
    `derive_expected_reasoning_type` counts them, and `build_evidence_trace_entry`
    resolves each one to chunks. An unresolvable supporting id would inflate the
    reasoning type while contributing no chunk — an expectation demanding
    multi-hop evidence the corpus was never asked for.

    Reported per pair rather than as a flat set, so a failure names the citing
    question and not only the dangling id.
    """
    orphaned = {
        pair["id"]: [
            fact_id for fact_id in pair["supporting_fact_ids"] if fact_id not in real_facts_by_id
        ]
        for pair in real_qa_pairs
        if any(fact_id not in real_facts_by_id for fact_id in pair["supporting_fact_ids"])
    }

    assert orphaned == {}, f"QA pairs citing unknown supporting facts: {orphaned}"


def test_x3_every_qa_pair_cites_at_least_one_resolvable_fact(real_qa_pairs, real_facts_by_id):
    """X-3 — every QA pair's evidence set is non-empty and fully resolvable.

    The guarantee `scripts/build_evidence_trace.py` states as *"every QA pair
    must trace to accepted repository knowledge"*. A question with no resolvable
    evidence has no ground truth to be scored against, and the builder refuses to
    emit an entry for it.
    """
    for pair in real_qa_pairs:
        cited = evidence_fact_ids(pair)

        assert cited, f"QA pair {pair['id']!r} cites no facts at all"
        assert all(fact_id in real_facts_by_id for fact_id in cited)


def test_x4_every_qa_pair_draws_evidence_from_a_single_document(
    real_qa_pairs, real_facts_by_id
):
    """X-4 — all facts a QA pair cites belong to one document.

    Not a stylistic constraint: `expected_source` is a single document id, and
    `build_evidence_trace_entry` refuses a multi-document evidence set outright
    because *"'expected_source' has no ratified multi-document encoding."* A pair
    spanning two documents is therefore not merely unusual — it is
    unrepresentable, and the Evidence Trace Dataset could not be rebuilt from the
    QA Dataset at all.

    Load-bearing for this corpus specifically: the Knowledge Manifest catalogues
    two resume versions whose text largely overlaps, so a supporting fact taken
    from the wrong version is a realistic authoring error rather than a
    hypothetical one, and it is exactly what this refuses.
    """
    for pair in real_qa_pairs:
        documents = {real_facts_by_id[fact_id]["document_id"] for fact_id in evidence_fact_ids(pair)}

        assert len(documents) == 1, (
            f"QA pair {pair['id']!r} draws evidence from {len(documents)} documents "
            f"({sorted(documents)})"
        )


# --- X-5 … X-9: Evidence Trace → QA Pairs ------------------------------------


def test_x5_the_evidence_trace_pairs_one_to_one_with_the_qa_dataset(
    real_evidence_trace, real_qa_pairs
):
    """X-5 — one entry per QA pair, in the QA Dataset's own order, with `meta_` ids.

    Three claims that are one invariant: `scripts/build_evidence_trace.py`
    `main()` emits exactly one entry per pair and preserves QA order, and
    `build_evidence_trace_entry` names each entry `meta_<qa_id>`. Asserting the
    id sequence establishes all three at once — cardinality, ordering, and the
    naming convention that makes an entry traceable to its question without a
    lookup.

    This is the specification every positional comparison below depends on. It
    also closes orphan detection in both directions: an entry with no QA pair, or
    a pair with no entry, breaks the sequence equality here.

    The `meta_` prefix alone is checked by `validate_evidence_trace`; what is new
    here is *which* question each id resolves to.
    """
    assert [entry["id"] for entry in real_evidence_trace] == [
        f"meta_{pair['id']}" for pair in real_qa_pairs
    ]


def test_x6_every_entry_preserves_its_question_verbatim(real_evidence_trace, real_qa_pairs):
    """X-6 — `question` is copied from the QA pair without alteration.

    Provenance preservation, and directly load-bearing: `scripts/run_retrieval.py`
    `load_questions` reads the question from the *Evidence Trace* entry, so the
    text actually issued to the retriever is this copy. A drifted copy would mean
    the repository evaluates a question the QA Dataset never authored, while
    every report continued to attribute it to that pair.
    """
    for entry, pair in paired(real_evidence_trace, real_qa_pairs):
        assert entry["question"] == pair["question"], (
            f"{entry['id']}: question drifted from QA pair {pair['id']!r}"
        )


def test_x7_every_entry_preserves_its_expected_answer_verbatim(
    real_evidence_trace, real_qa_pairs
):
    """X-7 — `expected_answer` is copied from the QA pair without alteration.

    The ground truth the Generation layer will be scored against in Milestone 2.
    It is carried in two artifacts today and read from the Evidence Trace one, so
    the QA Dataset's authorship of it is a guarantee only while the copies agree.
    """
    for entry, pair in paired(real_evidence_trace, real_qa_pairs):
        assert entry["expected_answer"] == pair["expected_answer"], (
            f"{entry['id']}: expected_answer drifted from QA pair {pair['id']!r}"
        )


def test_x8_every_expected_reasoning_type_follows_the_derivation_rule(
    real_evidence_trace, real_qa_pairs
):
    """X-8 — `expected_reasoning_type` equals `derive_expected_reasoning_type(pair)`.

    The repository's own rule (Decision B), imported and called rather than
    restated: evidence topology decides the reasoning type — `supporting_fact_ids`
    count ≤ 1 is Single-hop, ≥ 2 is Multi-hop.

    Note what this deliberately does *not* assert: agreement with the QA pair's
    `failure_category`. The builder is explicit that the taxonomy label *"labels
    what a question tests, while this field records how many pieces of evidence
    answering it requires"*, and a committed `Multi-hop` failure category on a
    single-support question is therefore not an inconsistency. Asserting the two
    agreed would contradict a stated repository decision.
    """
    for entry, pair in paired(real_evidence_trace, real_qa_pairs):
        assert entry["expected_reasoning_type"] == derive_expected_reasoning_type(pair), (
            f"{entry['id']}: reasoning type disagrees with the evidence topology of "
            f"QA pair {pair['id']!r}"
        )


def test_x9_every_expected_outcome_follows_the_derivation_rule(
    real_evidence_trace, real_qa_pairs
):
    """X-9 — `expected_outcome` equals `derive_expected_outcome(pair)`.

    Decision C's rule, imported and called: `No Answer` is the abstention test
    and the only category yielding `Abstain`; every other category — including
    `False Premise`, whose expected answer corrects the premise from the corpus
    rather than declining — yields `Answer`.

    A drifted outcome would invert what counts as success for that question:
    a question expected to abstain, scored as one that should answer, is a
    hallucination test that rewards hallucinating.
    """
    for entry, pair in paired(real_evidence_trace, real_qa_pairs):
        assert entry["expected_outcome"] == derive_expected_outcome(pair), (
            f"{entry['id']}: outcome disagrees with the failure category of "
            f"QA pair {pair['id']!r}"
        )


# --- X-10 … X-14: Evidence Trace → documents and chunks ----------------------


def test_x10_every_expected_source_is_the_parent_fact_document(
    real_evidence_trace, real_qa_pairs, real_facts_by_id
):
    """X-10 — `expected_source` is the document the cited facts belong to.

    `expected_source` is the repository's canonical document identity
    (`docs/DOCUMENT_CONTRACT.md` §8.4) and the join key `chunk.document_id` and
    the Manifest's `documents[].id` already share. X-4 establishes the citation
    is single-document; this establishes the entry names *that* document.

    With two overlapping resume versions catalogued, an entry naming the wrong
    version would still resolve to real chunks containing similar text — which is
    precisely why this is asserted against the fact's provenance rather than
    merely against the Manifest.
    """
    for entry, pair in paired(real_evidence_trace, real_qa_pairs):
        expected = real_facts_by_id[pair["fact_id"]]["document_id"]

        assert entry["expected_source"] == expected, (
            f"{entry['id']}: expected_source {entry['expected_source']!r} is not the "
            f"document of cited fact {pair['fact_id']!r} ({expected!r})"
        )


def test_x11_every_expected_source_is_catalogued_by_the_manifest(
    real_evidence_trace, real_manifest_entries
):
    """X-11 — every `expected_source` resolves to a Knowledge Manifest entry.

    Closes the provenance chain at the Knowledge Authority, the root of
    `docs/MILESTONE_1A.md`'s dependency order. `build_evidence_trace_entry`
    refuses an uncatalogued document at build time; this makes it permanent.

    Read from the Manifest artifact itself via `real_manifest_entries`, not
    through the corpus loader, so the two sides of the comparison come from
    different code paths.
    """
    catalogued = {entry["id"] for entry in real_manifest_entries}
    unresolved = sorted(
        {
            entry["expected_source"]
            for entry in real_evidence_trace
            if entry["expected_source"] not in catalogued
        }
    )

    assert unresolved == [], f"expected_source values absent from the Manifest: {unresolved}"


def test_x12_every_expected_chunk_exists_in_the_committed_corpus(
    real_evidence_trace, real_chunks_by_id
):
    """X-12 — every `expected_chunk` id resolves to a committed chunk.

    Orphan detection where it costs the most. `evaluation/retrieval_evaluation.py`
    compares expected against observed chunk ids by set membership, so an
    expectation naming a chunk the corpus does not contain can never be matched:
    it depresses recall permanently, and
    `evaluation/retrieval_diagnosis.py` attributes the resulting gap to the
    Retrieve stage — a dataset defect diagnosed as a retriever defect, in every
    report, indefinitely.

    The corpus is read through its own `validate_chunks(load_chunks())` gate (see
    `tests/conftest.py`) and is not otherwise validated here: the Chunk Corpus is
    out of scope for Sprint P3.4.1 and already has committed specifications.
    """
    orphaned = {
        entry["id"]: [
            chunk_id for chunk_id in entry["expected_chunk"] if chunk_id not in real_chunks_by_id
        ]
        for entry in real_evidence_trace
        if any(chunk_id not in real_chunks_by_id for chunk_id in entry["expected_chunk"])
    }

    assert orphaned == {}, f"Evidence Trace entries expecting unknown chunks: {orphaned}"


def test_x13_every_expected_chunk_belongs_to_the_expected_source_document(
    real_evidence_trace, real_chunks_by_id
):
    """X-13 — every expected chunk's `document_id` is the entry's `expected_source`.

    Resolution (X-12) is not enough: a chunk id that exists but belongs to the
    other catalogued resume version would resolve cleanly while pointing the
    expectation at the wrong document. Given two versions with overlapping text,
    such an expectation could even be *satisfied* by retrieval — recording a
    match against evidence the fact was never extracted from.
    """
    for entry in real_evidence_trace:
        foreign = [
            chunk_id
            for chunk_id in entry["expected_chunk"]
            if real_chunks_by_id[chunk_id]["document_id"] != entry["expected_source"]
        ]

        assert foreign == [], (
            f"{entry['id']}: expected chunks {foreign} do not belong to "
            f"{entry['expected_source']!r}"
        )


def test_x14_expected_chunks_are_ordered_by_ascending_chunk_index(
    real_evidence_trace, real_chunks_by_id
):
    """X-14 — `expected_chunk` is in ascending `chunk_index` order.

    Decision G: an entry's chunk order is *"a property of the corpus, not of the
    order its facts happen to be listed in"*, which is what makes two entries
    citing overlapping evidence comparable to each other and to a rebuilt
    dataset. `validate_evidence_trace` enforces that the ids are distinct but
    knows nothing about the corpus, so ordering is only decidable here.

    Retrieval evaluation compares by set membership and is indifferent to this
    order — which is exactly why an unordered `expected_chunk` would never be
    caught downstream.
    """
    for entry in real_evidence_trace:
        indexes = [real_chunks_by_id[chunk_id]["chunk_index"] for chunk_id in entry["expected_chunk"]]

        assert indexes == sorted(indexes), (
            f"{entry['id']}: expected_chunk is not in ascending chunk_index order ({indexes})"
        )


# --- X-15 … X-16: complete provenance chains ---------------------------------


def test_x15_every_cited_fact_is_covered_by_the_expected_chunks(
    real_evidence_trace, real_qa_pairs, real_facts_by_id, real_chunks_by_id, real_documents_by_id
):
    """X-15 — the chunks each cited fact resolves to are all present in `expected_chunk`.

    The complete provenance chain, executed end to end:

        Evidence Trace entry → QA pair → cited fact → parent Document
                             → the chunks spanning that fact's `source_text`
                             → the entry's own `expected_chunk`

    Resolution uses `resolve_fact_chunks` — the builder's own function, against
    the same `Document.text` offset frame `Chunk.character_start`/`character_end`
    are computed in — so this holds the committed expectations to the repository's
    real resolution rule rather than to a restatement of it.

    **Coverage, not equality.** Every chunk a cited fact resolves to must appear;
    the entry may legitimately carry more, because its `expected_chunk` is the
    union over *all* cited facts. Asserting equality would be rebuilding the
    field, which this sprint does not do — and would also fail the moment a
    supporting fact was added, for a dataset that was still perfectly consistent.

    This is the specification that would catch a fact whose `source_text` still
    matched the document but at a different offset than when the dataset was
    built — a re-chunking or a document edit that GD-8's substring check alone
    cannot see.
    """
    for entry, pair in paired(real_evidence_trace, real_qa_pairs):
        expected = set(entry["expected_chunk"])
        document = real_documents_by_id[entry["expected_source"]]
        document_chunks = [
            chunk
            for chunk in real_chunks_by_id.values()
            if chunk["document_id"] == entry["expected_source"]
        ]

        for fact_id in evidence_fact_ids(pair):
            resolved = {
                chunk["id"]
                for chunk in resolve_fact_chunks(
                    real_facts_by_id[fact_id], document.text, document_chunks
                )
            }

            assert resolved, f"{entry['id']}: fact {fact_id!r} resolves to no chunk at all"
            assert resolved <= expected, (
                f"{entry['id']}: fact {fact_id!r} resolves to chunks "
                f"{sorted(resolved - expected)} that expected_chunk omits"
            )


def test_x16_every_cited_fact_is_grounded_in_the_expected_source_document(
    real_evidence_trace, real_qa_pairs, real_facts_by_id, real_documents_by_id
):
    """X-16 — each cited fact's `source_text` is verbatim in the entry's `expected_source`.

    GD-8 grounds every fact in the document *the fact itself names*. This grounds
    it in the document *the Evidence Trace entry names*, which is a different
    claim wherever the two could disagree — and with two overlapping resume
    versions catalogued, they can.

    Together with X-10 the two are consistent today; specified separately, a
    future divergence surfaces as a failure of whichever link actually broke
    rather than as a single opaque one.
    """
    for entry, pair in paired(real_evidence_trace, real_qa_pairs):
        document_text = real_documents_by_id[entry["expected_source"]].text

        for fact_id in evidence_fact_ids(pair):
            assert real_facts_by_id[fact_id]["source_text"] in document_text, (
                f"{entry['id']}: cited fact {fact_id!r} is not grounded in "
                f"{entry['expected_source']!r}"
            )


# --- X-17: Golden Dataset ↔ current canonical knowledge alignment ------------


def test_x17_only_historical_knowledge_questions_cite_a_non_canonical_document(
    real_qa_pairs, real_facts_by_id, real_manifest_entries
):
    """X-17 — a QA pair may cite non-canonical knowledge only to evaluate historical knowledge.

    The specification that makes corpus evolution *detectable* rather than
    silent. Every check above resolves a reference to whatever document the fact
    happens to name; none asks whether that document still carries the Knowledge
    Manifest's canonical designation. So when new canonical knowledge enters the
    corpus, the entire Golden Dataset can go on citing its predecessor while
    every structural specification stays green — the expectations remain
    internally consistent and externally stale, and the drift surfaces only as
    degraded retrieval metrics, which read as a retrieval defect rather than a
    dataset one. That is precisely the Knowledge-stage-mistaken-for-Retrieve-stage
    confusion `docs/altm.md` exists to prevent.

    **Why the invariant is not "every fact is canonical."** Repository Owner
    ruling **R-01 — Historical Knowledge Semantics** retains historical knowledge
    *solely as evaluation evidence*, and `docs/roadmap.md` §2.3's Stale Version
    and Contradiction categories exist to evaluate it: each compares historical
    knowledge against current canonical knowledge, so historical knowledge must
    remain reachable to be compared at all. Requiring universal canonicality
    would make two of the seven taxonomy categories unpopulatable and would fail
    the repository for the state `docs/corpus/resume-corpus.md` deliberately
    maintains.

    The invariant asserted is the conditional one: non-canonical parentage is
    legitimate **exactly** where evaluating historical knowledge is the
    question's purpose. Everywhere else it means the dataset is asserting
    historical knowledge as current repository truth, which R-01 forbids. Stated
    over the QA pair's full evidence set — parent fact and supporting facts alike
    — because a supporting fact silently anchored to superseded knowledge
    corrupts a multi-hop expectation just as completely.

    Canonicality is read from `sample_rag/knowledge_manifest.json` itself, so the
    specification tracks whatever the Repository Owner has designated rather than
    any version string, filename, or literal document id. It requires no
    maintenance at the next corpus evolution: it simply starts failing, naming the
    facts that need re-anchoring.
    """
    canonical_by_id = {entry["id"]: entry["canonical"] for entry in real_manifest_entries}

    misanchored = []
    for pair in real_qa_pairs:
        if pair["failure_category"] in HISTORICAL_KNOWLEDGE_CATEGORIES:
            continue

        for fact_id in evidence_fact_ids(pair):
            document_id = real_facts_by_id[fact_id]["document_id"]
            if not canonical_by_id[document_id]:
                misanchored.append(f"{pair['id']} → {fact_id} → {document_id}")

    assert misanchored == [], (
        "QA pairs outside the historical-knowledge categories citing facts anchored to "
        f"non-canonical knowledge; the Golden Dataset has drifted from current canonical "
        f"knowledge and needs re-anchoring: {sorted(set(misanchored))}"
    )
