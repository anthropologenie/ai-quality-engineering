"""Specifications for the Assemble stage — Sprint M2.12.

Register capability **M2-12** — *"Assemble stage — Context Builder, `Prompt`
artifact"* — allocated to **Milestone 2A** by `docs/roadmap.md` §1.1 under
Repository Owner ruling **RO-07**, between **M2-04** and **M2-06**.

These specifications answer one question: **does the Context Builder assemble
exactly what retrieval produced, in exactly the order retrieval produced it?**
They assert nothing about retrieval quality, answer quality, prompt quality or
whether a fused ranking is a good ranking — none of which is this stage's
property, and the first of which is `sample_rag/fusion.py`'s.

The central negative claim is that **there is no second ranker here**. Most of
this file exists to make that claim falsifiable: orders that contradict corpus
order, that contradict every score-like signal, and that a re-ranking
implementation would silently "fix".

Layout, in order: identity resolution; order preservation; the `Prompt`
artifact; context boundaries; the degenerate and out-of-contract inputs; text
that breaks naive assembly; determinism; the integration over the committed
corpus and the real **M2-04** fused route; and the sprint boundary.
"""

import ast
import importlib
import inspect
import pathlib

import pytest

from sample_rag.context_builder import (
    CONTEXT_SEPARATOR,
    ChunkProvenance,
    ContextAssemblyError,
    ContextBuilder,
    Prompt,
)
from sample_rag.fusion import reciprocal_rank_fusion
from sample_rag.retriever import Retriever
from scripts.run_hybrid_retrieval import canonical_order

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def chunk(chunk_id, text, document_id="doc-a", start=0):
    """One chunk mapping, shaped exactly as the committed Chunk Corpus stores them.

    The same helper `tests/test_generator.py` uses, for the same reason: a
    specification exercising this stage should never also be exercising a
    malformed corpus. Offsets satisfy `docs/CHUNK_CONTRACT.md` §17 invariants 1
    and 2.
    """
    return {
        "id": chunk_id,
        "document_id": document_id,
        "text": text,
        "chunk_index": start,
        "character_start": start,
        "character_end": start + len(text),
    }


def corpus(*pairs):
    """A chunk collection from `(id, text)` pairs, in committed corpus order."""
    return [chunk(chunk_id, text, start=index) for index, (chunk_id, text) in enumerate(pairs)]


def imported_roots(module):
    """Every top-level package name imported by `module`'s source.

    Read from the AST rather than from `sys.modules`, so an import that a test
    run happened to satisfy transitively is not mistaken for one this module
    declares — the convention `tests/test_rrf_fusion.py` established.
    """
    tree = ast.parse(inspect.getsource(module))

    roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            roots.add(node.module.split(".")[0])
    return roots


def declared_names(module):
    """Every function, class, argument and assignment target declared in `module`."""
    tree = ast.parse(inspect.getsource(module))

    names = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            names.add(node.id)
        elif isinstance(node, ast.arg):
            names.add(node.arg)
    return names


@pytest.fixture
def builder():
    """A builder over a five-chunk corpus whose ids and texts are distinguishable."""
    return ContextBuilder(
        corpus(
            ("c0", "alpha text"),
            ("c1", "bravo text"),
            ("c2", "charlie text"),
            ("c3", "delta text"),
            ("c4", "echo text"),
        )
    )


# ---------------------------------------------------------------------------
# 1. Identity resolution — a chunk id resolves to its own chunk, or to nothing
# ---------------------------------------------------------------------------


def test_m212_each_chunk_id_resolves_to_exactly_its_own_chunk(builder):
    """`chunk_A -> text_A`, for every id, with no substitution anywhere.

    Stated over every id in the corpus rather than one, so an implementation
    that resolved the first id correctly and drifted afterwards — an off-by-one
    over a list, a positional lookup mistaken for an identity lookup — fails
    here rather than passing on a lucky example.
    """
    for chunk_id, expected in (
        ("c0", "alpha text"),
        ("c1", "bravo text"),
        ("c2", "charlie text"),
        ("c3", "delta text"),
        ("c4", "echo text"),
    ):
        resolved = builder.resolve([chunk_id])

        assert [record["id"] for record in resolved] == [chunk_id]
        assert [record["text"] for record in resolved] == [expected]


def test_m212_resolution_returns_the_canonical_chunk_record_itself(builder):
    """The record carries the corpus's own fields, not a reconstruction of them.

    `document_id` and the document-frame offsets are what
    `docs/GENERATION_CONTRACT.md` §8.3 requires a citation to be resolvable to,
    and this stage must not strip them on the way past. Asserted on the whole
    mapping, so a builder that returned `{"id": ..., "text": ...}` — enough for
    the context string and not enough for provenance — fails.
    """
    corpus_chunk = chunk("c2", "charlie text", start=2)

    (resolved,) = builder.resolve(["c2"])

    assert resolved == corpus_chunk


def test_m212_no_second_chunk_identity_is_introduced(builder):
    """Ids out are the ids in — the canonical `chunks[].id` and nothing derived.

    `docs/CHUNK_CONTRACT.md` §17 makes `Chunk.id` globally unique, and Sprint
    M2.03 recorded that both retrieval routes already agree on it *"so a later
    fusion sprint has one identity to fuse on rather than two"*. **M2-04**
    introduced no `hybrid_chunk_id`; this stage introduces no `context_id`,
    `block_id` or positional identifier either.
    """
    supplied = ["c3", "c0"]

    prompt = builder.assemble(builder.resolve(supplied), "a query")

    assert prompt.chunk_ids == supplied


# ---------------------------------------------------------------------------
# 2. Order preservation — the supplied ranking is retrieval's decision
# ---------------------------------------------------------------------------


def test_m212_supplied_order_is_preserved_exactly(builder):
    """`[A, C, B]` assembles to `A`, `C`, `B` — the sprint's central invariant.

    The supplied order deliberately contradicts committed corpus order, so an
    implementation that iterated its own corpus and filtered by membership —
    the most natural wrong implementation, and one that would look correct on a
    sorted input — produces `[A, B, C]` and fails.
    """
    prompt = builder.assemble(builder.resolve(["c0", "c2", "c1"]), "a query")

    assert prompt.chunk_ids == ["c0", "c2", "c1"]
    assert prompt.context.split(CONTEXT_SEPARATOR) == [
        "alpha text",
        "charlie text",
        "bravo text",
    ]


def test_m212_a_fully_reversed_order_survives_assembly(builder):
    """Corpus order reversed, and reversed still after assembly.

    The strongest available statement of the same property: every adjacent pair
    is in the opposite order from the corpus, so *any* re-derivation of order
    from the corpus — by position, by `chunk_index`, by offsets, by insertion —
    is visible here.
    """
    reversed_ids = ["c4", "c3", "c2", "c1", "c0"]

    prompt = builder.assemble(builder.resolve(reversed_ids), "a query")

    assert prompt.chunk_ids == reversed_ids
    assert prompt.context.split(CONTEXT_SEPARATOR) == [
        "echo text",
        "delta text",
        "charlie text",
        "bravo text",
        "alpha text",
    ]


def test_m212_order_is_not_re_derived_from_any_ranking_signal():
    """No score, length, section, timestamp or lexical signal reorders anything.

    Each competing signal is loaded *against* the supplied order at once: the
    supplied first chunk is the longest, the last alphabetically, the last in
    corpus order, and the one carrying a later-looking document id and a larger
    offset. Every heuristic a re-ranking implementation might reach for would
    move it, and the specification requires it to stay exactly where retrieval
    put it.

    This is the specification that would fail if a second ranking mechanism
    were ever hidden inside context assembly. RRF ordering is **M2-04**'s
    decision (`sample_rag/fusion.py`), already made before this stage is
    reached.
    """
    chunks = [
        chunk("early", "zzz", document_id="doc-a", start=0),
        chunk("late", "a much longer body of evidence text", document_id="doc-z", start=900),
    ]
    builder = ContextBuilder(chunks)

    prompt = builder.assemble(builder.resolve(["late", "early"]), "a query")

    assert prompt.chunk_ids == ["late", "early"]
    assert prompt.context.split(CONTEXT_SEPARATOR) == [
        "a much longer body of evidence text",
        "zzz",
    ]


def test_m212_resolution_is_positional_and_length_preserving(builder):
    """`len(resolve(ids)) == len(ids)`, position for position.

    The property `Prompt.chunk_ids` alignment rests on: if resolution could
    ever return a different length or a different position for the same input,
    the ids recorded in the artifact would stop describing the blocks of the
    context beside them.
    """
    supplied = ["c1", "c4", "c0", "c3"]

    resolved = builder.resolve(supplied)

    assert len(resolved) == len(supplied)
    assert [record["id"] for record in resolved] == supplied


def test_m212_assembly_applies_no_sort(builder):
    """Structurally: no `sorted`, no `.sort`, no comparison key anywhere.

    Stated over the module's AST rather than over one input, because order
    preservation demonstrated on examples is preservation on those examples. A
    module that cannot sort cannot reorder any input at all — including the ones
    no specification here thought to present.
    """
    import sample_rag.context_builder

    tree = ast.parse(inspect.getsource(sample_rag.context_builder))

    calls = [node.func for node in ast.walk(tree) if isinstance(node, ast.Call)]
    called = {node.id for node in calls if isinstance(node, ast.Name)}
    called |= {node.attr for node in calls if isinstance(node, ast.Attribute)}

    assert "sorted" not in called
    assert "sort" not in called
    assert not any("key" == keyword.arg for node in ast.walk(tree)
                   if isinstance(node, ast.Call) for keyword in node.keywords)


# ---------------------------------------------------------------------------
# 3. The `Prompt` artifact
# ---------------------------------------------------------------------------


def test_m212_prompt_carries_exactly_four_fields(builder):
    """Query, context, chunk ids, provenance — and nothing speculative beside them.

    The first three were an engineering decision of Sprint M2.12, taken when no
    repository authority defined `Prompt`'s fields. **The fourth is not a
    decision of any sprint**: `docs/GENERATION_CONTRACT.md` §24.4, under
    Repository Owner ruling **RO-13**, states the shape as
    `Prompt(query, context, chunk_ids, provenance)` and resolves **U-2**.

    A specification that only checked the four were *present* would not notice
    a fifth arriving; this one names the whole set. In particular no `score`,
    no `rank`, no token count, no budget, no timestamp, no `system_prompt`, no
    `citations` and no `diagnostics` — §24.4 bars each by name, and *"No other
    field is authorized."*
    """
    prompt = builder.assemble(builder.resolve(["c0"]), "a query")

    assert [field for field in prompt.__dataclass_fields__] == [
        "query",
        "context",
        "chunk_ids",
        "provenance",
    ]


def test_m212_prompt_is_frozen(builder):
    """The artifact records what was assembled; no consumer may edit it after.

    The convention `docs/GENERATION_CONTRACT.md` §13.1 fixed for
    `GenerationResult` and `sample_rag/retriever.py` already used for
    `RetrievalResult`.
    """
    prompt = builder.assemble(builder.resolve(["c0"]), "a query")

    with pytest.raises(Exception):
        prompt.context = "rewritten"


def test_m212_the_query_reaches_the_prompt_unchanged(builder):
    """No rewriting, no expansion, no normalization, no tokenization.

    `docs/architecture.md` §4 gives the Assemble stage the query as an input;
    query rewriting and expansion are retrieval-side concerns this repository
    has already excluded (`sample_rag/retriever.py` `tokenize`), and they would
    be no more in scope here.
    """
    query = "  Which  ROLES used C++/Rust?  "

    prompt = builder.assemble(builder.resolve(["c0"]), query)

    assert prompt.query == query


def test_m212_chunk_ids_are_aligned_with_the_context_blocks(builder):
    """`ALTM-ASSEMBLE-1` made executable: the prompt diffs against the chunk set.

    *"Diff the assembled prompt against the retrieved chunk set before
    suspecting the model"* (`evaluation/altm_rules.py`) requires the prompt to
    carry identity, and requires that identity to line up with what the context
    actually contains. Both halves are asserted: the ids are the supplied ones,
    and block *i* is the text of chunk *i*.
    """
    supplied = ["c2", "c0", "c4"]

    prompt = builder.assemble(builder.resolve(supplied), "a query")
    blocks = prompt.context.split(CONTEXT_SEPARATOR)

    assert prompt.chunk_ids == supplied
    assert len(blocks) == len(supplied)
    for block, chunk_id in zip(blocks, supplied):
        assert block == builder.resolve([chunk_id])[0]["text"]


# ---------------------------------------------------------------------------
# 3b. `Prompt.provenance` — RO-13 / `docs/GENERATION_CONTRACT.md` §24.4
#
# The U-2 resolution, added at Sprint M2.06. These specifications state what
# §24.4 authorizes and — at least as importantly — what it bars, because the
# section's operative sentence is *"No other field is authorized."*
# ---------------------------------------------------------------------------


def test_m206_provenance_records_carry_exactly_the_four_authorized_fields(builder):
    """§24.4 — `chunk_id`, `document_id`, `character_start`, `character_end`.

    Named as a whole set in §24.4's own table order, so a fifth field arriving
    is a visible failure rather than a silent contract widening. §24.4 bars by
    name: `token_count`, `context_window`, `token_budget`, `citations`,
    `system_prompt`, `diagnostics`, retrieval scores, BM25 scores, FAISS
    similarity, RRF scores, model configuration, memory and conversation
    history.
    """
    prompt = builder.assemble(builder.resolve(["c0", "c1"]), "a query")

    for record in prompt.provenance:
        assert isinstance(record, ChunkProvenance)
        assert [field for field in record.__dataclass_fields__] == [
            "chunk_id",
            "document_id",
            "character_start",
            "character_end",
        ]


def test_m206_provenance_length_matches_the_assembled_chunk_sequence(builder):
    """One record per assembled chunk — no more, no fewer.

    `provenance`, `chunk_ids` and the blocks of `context` are three views of one
    sequence. A length disagreement between any two of them would mean a
    consumer constructing `SupportingEvidence` from record *i* could not know
    which block it describes, which is the whole property §24.4's ordering
    clause exists to guarantee.
    """
    for supplied in ([], ["c0"], ["c0", "c1"], ["c4", "c3", "c2", "c1", "c0"]):
        prompt = builder.assemble(builder.resolve(supplied), "a query")

        assert len(prompt.provenance) == len(supplied)
        assert len(prompt.provenance) == len(prompt.chunk_ids)


def test_m206_provenance_ordering_matches_chunk_ordering(builder):
    """§24.4 — *"Ordering SHALL correspond to assembled chunk ordering."*

    Exercised on an order that contradicts corpus order in every position, so a
    builder that sorted, re-ranked or fell back to corpus order would fail here
    rather than pass by coincidence. Record *i* describes chunk *i*, whose text
    is block *i*.
    """
    supplied = ["c3", "c0", "c4", "c1"]

    prompt = builder.assemble(builder.resolve(supplied), "a query")
    blocks = prompt.context.split(CONTEXT_SEPARATOR)

    assert [record.chunk_id for record in prompt.provenance] == supplied
    assert [record.chunk_id for record in prompt.provenance] == prompt.chunk_ids
    for record, block in zip(prompt.provenance, blocks):
        assert record.character_end - record.character_start == len(block)


def test_m206_each_provenance_entry_identifies_its_own_canonical_chunk(builder):
    """Every value is the canonical chunk record's own, copied unchanged.

    Not re-derived, not defaulted, not normalized: the four values are read from
    the chunk `resolve` returned, so a provenance entry cannot disagree with the
    corpus about the chunk it names. `chunk_id` is the canonical `chunks[].id`
    **M2-04** fuses on — §24.4: *"not a second identity system"*.
    """
    supplied = ["c2", "c0", "c4"]
    resolved = builder.resolve(supplied)

    prompt = builder.assemble(resolved, "a query")

    for record, source in zip(prompt.provenance, resolved):
        assert record.chunk_id == source["id"]
        assert record.document_id == source["document_id"]
        assert record.character_start == source["character_start"]
        assert record.character_end == source["character_end"]


def test_m206_provenance_carries_the_document_identity_of_its_chunk():
    """§24.4 — `document_id` is *"that chunk's `document_id`"*.

    Stated over a corpus spanning two documents, because a single-document
    corpus cannot distinguish "carries the right document" from "carries the
    only document". This is the identity `docs/GENERATION_CONTRACT.md` §8.3
    requires of `SupportingEvidence.document_id`, and the join key T-2 makes
    traceable to a Knowledge Manifest `documents[]` entry.
    """
    builder = ContextBuilder(
        [
            chunk("a0", "alpha", document_id="doc-a", start=0),
            chunk("b0", "bravo", document_id="doc-b", start=100),
            chunk("a1", "charlie", document_id="doc-a", start=40),
        ]
    )

    prompt = builder.assemble(builder.resolve(["b0", "a1", "a0"]), "a query")

    assert [record.document_id for record in prompt.provenance] == [
        "doc-b",
        "doc-a",
        "doc-a",
    ]


def test_m206_provenance_offsets_are_the_document_frame_offsets():
    """§24.4 — inclusive start, exclusive end, in the document frame.

    `docs/CHUNK_CONTRACT.md` §13's frame, which is the repository's only offset
    coordinate system and the one `SupportingEvidence.character_start` uses. A
    chunk-frame offset would be a second, incompatible system over one corpus.

    Exercised on chunks that do **not** start at zero, because a chunk-frame
    implementation is indistinguishable from a document-frame one when every
    chunk begins at the document's start.
    """
    builder = ContextBuilder(
        [
            chunk("c0", "alpha text", document_id="doc-a", start=400),
            chunk("c1", "bravo", document_id="doc-a", start=900),
        ]
    )

    prompt = builder.assemble(builder.resolve(["c0", "c1"]), "a query")

    assert [(record.character_start, record.character_end) for record in prompt.provenance] == [
        (400, 410),
        (900, 905),
    ]
    for record in prompt.provenance:
        assert record.character_end > record.character_start


def test_m206_chunk_text_is_not_duplicated_into_provenance(builder):
    """§24.4 — *"Chunk text SHALL NOT be duplicated into `provenance`."*

    `Prompt.context` already carries it, and a second copy would be two sources
    of truth for one string. Asserted two ways: no field holds a chunk's text,
    and no field is a string other than the two identities — so a `text`,
    `snippet`, `excerpt` or `preview` field under any name fails here.
    """
    prompt = builder.assemble(builder.resolve(["c0", "c1"]), "a query")
    texts = {record["text"] for record in builder.resolve(["c0", "c1"])}

    for record in prompt.provenance:
        values = [getattr(record, field) for field in record.__dataclass_fields__]
        assert not texts & set(value for value in values if isinstance(value, str))
        assert sum(isinstance(value, str) for value in values) == 2


def test_m206_supporting_evidence_text_is_derivable_from_context_and_provenance(builder):
    """§24.4 — *"`SupportingEvidence.text` remains derivable without it."*

    The claim that justifies omitting chunk text, made executable. `context` is
    the separator-joined block sequence and `character_end - character_start` is
    block *i*'s length (`docs/CHUNK_CONTRACT.md` §17 invariant 3), so a consumer
    holding only the `Prompt` can recover every span's text by arithmetic — with
    no corpus read, which is exactly what G-13/§18 bars it from performing.

    Exercised on text containing the separator itself, because a consumer that
    recovered blocks by splitting on `CONTEXT_SEPARATOR` would be wrong there
    while an offset-driven one stays exact.
    """
    builder = ContextBuilder(
        [
            chunk("c0", "alpha" + CONTEXT_SEPARATOR + "still alpha", start=0),
            chunk("c1", "bravo", start=200),
        ]
    )
    supplied = ["c0", "c1"]

    prompt = builder.assemble(builder.resolve(supplied), "a query")

    cursor = 0
    for record, source in zip(prompt.provenance, builder.resolve(supplied)):
        length = record.character_end - record.character_start
        assert prompt.context[cursor : cursor + length] == source["text"]
        cursor += length + len(CONTEXT_SEPARATOR)
    assert cursor - len(CONTEXT_SEPARATOR) == len(prompt.context)


def test_m206_empty_retrieval_produces_empty_provenance(builder):
    """The degenerate input stays total, and gains no sentinel.

    M2-12's empty-context decision is unchanged: `Prompt` remains a total
    function of its inputs, no branch and no `None` enters the artifact, and
    **no abstention decision is made or implied** — `docs/GENERATION_CONTRACT.md`
    §9.3 places that judgement in the Generator, and §24 does not move it.
    """
    prompt = builder.assemble([], "a query")

    assert prompt.provenance == []
    assert prompt.chunk_ids == []
    assert prompt.context == ""


def test_m206_duplicate_chunk_ids_produce_duplicate_provenance_records(builder):
    """Duplicate handling remains governed by M2-12's existing semantics.

    `resolve` preserves duplicates rather than collapsing them, which is what
    keeps it positional and length-preserving. `provenance` is derived in the
    same pass as `chunk_ids`, so it inherits that behaviour exactly — the
    alternative, a `provenance` that deduplicated while `chunk_ids` did not,
    would break the positional alignment §24.4 requires.

    **M2-04 cannot produce a duplicate** (`rank_candidates` keys candidates by
    chunk id), so this states the seam's behaviour on a caller's sequence rather
    than a fused one.
    """
    supplied = ["c1", "c1", "c0"]

    prompt = builder.assemble(builder.resolve(supplied), "a query")

    assert [record.chunk_id for record in prompt.provenance] == supplied
    assert len(prompt.provenance) == len(prompt.context.split(CONTEXT_SEPARATOR))


def test_m206_a_missing_chunk_id_still_raises_before_any_provenance_exists(builder):
    """Missing-chunk behaviour remains governed by M2-12's existing semantics.

    `resolve` raises `ContextAssemblyError`; no partial `Prompt`, no partial
    provenance and no placeholder record is produced. The M2-12 reasoning is
    unchanged — a shorter list would drop evidence silently, which is
    `docs/architecture.md` §4's named Assemble-stage failure — and §24.4 adds no
    fallback, no substitution and no re-retrieval to it.
    """
    with pytest.raises(ContextAssemblyError):
        builder.assemble(builder.resolve(["c0", "absent", "c1"]), "a query")


def test_m206_provenance_is_deterministic_across_repeated_assembly(builder):
    """Identical corpus + identical ids + identical query ⇒ identical provenance.

    §24.3's **structural determinism** half, which v2.0.0 keeps normative:
    provenance mapping *"SHALL remain deterministic, and byte-identical-checkable
    wherever the implementation permits"*. Nothing here is externally generated,
    so the guarantee applies in full — this is the assembly stage, and no model
    participates in it.
    """
    supplied = ["c3", "c1", "c4"]

    first = builder.assemble(builder.resolve(supplied), "a query")
    second = builder.assemble(builder.resolve(supplied), "a query")

    assert first.provenance == second.provenance
    assert first == second


def test_m206_provenance_records_are_frozen(builder):
    """The record states what was assembled; no consumer may edit it after.

    The same convention `Prompt`, `GenerationResult` and `RetrievalResult`
    already hold. A mutable provenance record would let a consumer rewrite the
    identity its own `SupportingEvidence` is built from, which is precisely the
    traceability G-12 and T-1…T-5 exist to keep recoverable from the artifact.
    """
    prompt = builder.assemble(builder.resolve(["c0"]), "a query")

    with pytest.raises(Exception):
        prompt.provenance[0].chunk_id = "rewritten"


def test_m206_provenance_does_not_alias_the_corpus_chunk_mappings(builder):
    """The record copies four values; it does not hand out the chunk mapping.

    A consumer holding the `Prompt` must not be able to reach the corpus through
    it — G-13/§18 bars the Generator from corpus access, and a provenance entry
    that carried the live chunk dict would have handed that access over the
    boundary rather than through it.
    """
    prompt = builder.assemble(builder.resolve(["c0"]), "a query")
    record = prompt.provenance[0]

    for field in record.__dataclass_fields__:
        assert not isinstance(getattr(record, field), dict)


# ---------------------------------------------------------------------------
# 4. Context boundaries — what the assembled text does and does not contain
# ---------------------------------------------------------------------------


def test_m212_context_carries_chunk_text_and_separators_and_nothing_else(builder):
    """No label, numbering, citation marker, heading, delimiter or instruction.

    No authority specifies any of them, and each would be text in the prompt
    that no corpus chunk supports — the reasoning
    `docs/GENERATION_CONTRACT.md` §15 already applied when it refused a
    free-text `citations` field. Stated as an exact string equality, which is
    the only form that rules out an addition nobody anticipated.
    """
    prompt = builder.assemble(builder.resolve(["c0", "c1"]), "a query")

    assert prompt.context == "alpha text" + CONTEXT_SEPARATOR + "bravo text"


def test_m212_nothing_is_dropped_or_truncated(builder):
    """Every supplied chunk reaches the context, whole.

    `docs/architecture.md` §4 gives the Assemble stage the responsibility *"Fit
    within context window without silent truncation"* and the failure mode
    *"Retrieved evidence correct but dropped during assembly"*. **No repository
    authority states a context budget** — §5 records *"Context-overflow
    handling under real token budgets"* as *Future Evolution*, and the model
    whose window would define one arrives at **M2-06** — so nothing is dropped
    and the arithmetic below is exact.
    """
    supplied = ["c0", "c1", "c2", "c3", "c4"]
    texts = [record["text"] for record in builder.resolve(supplied)]

    prompt = builder.assemble(builder.resolve(supplied), "a query")

    assert len(prompt.chunk_ids) == len(supplied)
    assert len(prompt.context) == sum(len(text) for text in texts) + len(
        CONTEXT_SEPARATOR
    ) * (len(supplied) - 1)
    for text in texts:
        assert text in prompt.context


def test_m212_a_large_context_is_not_truncated():
    """A prompt far past any plausible token budget is still assembled whole.

    The specification that would fail the moment a token heuristic, a
    model-specific limit or a dynamic top-N were introduced without an
    authority defining it.
    """
    chunks = [chunk(f"c{index}", "x" * 50_000, start=index * 50_000) for index in range(20)]
    builder = ContextBuilder(chunks)
    supplied = [record["id"] for record in chunks]

    prompt = builder.assemble(builder.resolve(supplied), "a query")

    assert prompt.chunk_ids == supplied
    assert len(prompt.context) == 20 * 50_000 + len(CONTEXT_SEPARATOR) * 19


def test_m212_assembly_is_reversible_over_the_committed_corpus(real_chunks):
    """The separator cannot occur inside a committed chunk, so the diff is exact.

    `sample_rag/generator.py` makes the same claim for `STATEMENT_SEPARATOR` and
    this checks the corpus property that claim rests on rather than assuming it:
    if a future corpus introduced a chunk containing a blank line, splitting an
    assembled context back into its blocks would stop being sound and this
    specification — not a downstream answer — is where that surfaces.
    """
    assert all(CONTEXT_SEPARATOR not in record["text"] for record in real_chunks)

    builder = ContextBuilder(real_chunks)
    supplied = [record["id"] for record in real_chunks[:10]]

    prompt = builder.assemble(builder.resolve(supplied), "a query")

    assert prompt.context.split(CONTEXT_SEPARATOR) == [
        record["text"] for record in real_chunks[:10]
    ]


# ---------------------------------------------------------------------------
# 5. Degenerate and out-of-contract inputs
# ---------------------------------------------------------------------------


def test_m212_the_empty_retrieval_assembles_to_an_empty_context(builder):
    """`[]` yields a `Prompt` with an empty context, not `None` and not a sentinel.

    An engineering decision, and the smallest deterministic one: no repository
    authority defines an empty-retrieval policy at this seam. An empty context
    is exactly true about an empty retrieval, and it keeps `assemble` total.
    """
    prompt = builder.assemble(builder.resolve([]), "a query")

    assert prompt.query == "a query"
    assert prompt.context == ""
    assert prompt.chunk_ids == []


def test_m212_the_empty_retrieval_makes_no_abstention_decision(builder):
    """Nothing here decides an outcome, and nothing here can express one.

    `docs/GENERATION_CONTRACT.md` §9.3 places the empty-evidence outcome in the
    `Generator` and §20.2 records the abstention predicate as the Generator's.
    The artifact carries no outcome field and the empty context carries no
    abstention text — so an implementation that started deciding here would
    have nowhere to put the decision, which is the point.
    """
    prompt = builder.assemble(builder.resolve([]), "a query")

    assert not hasattr(prompt, "outcome")
    assert prompt.context == ""
    assert "Abstain" not in prompt.context


def test_m212_a_missing_chunk_id_raises_rather_than_dropping_it(builder):
    """An unresolvable id is a named failure, not a shorter list.

    An engineering decision — no authority defines missing-id behaviour at this
    seam. Silently returning fewer chunks is exactly
    `docs/architecture.md` §4's named Assemble-stage failure (*"Retrieved
    evidence correct but dropped during assembly"*), which is why it is not the
    behaviour chosen.
    """
    with pytest.raises(ContextAssemblyError) as raised:
        builder.resolve(["c0", "absent", "c1"])

    assert "absent" in str(raised.value)


def test_m212_a_missing_chunk_id_never_substitutes_another_chunk(builder):
    """No nearest match, no fallback lookup, no re-retrieval, no placeholder.

    The failure surfaces as an exception and produces no `Prompt` at all —
    asserted rather than assumed, because a builder that substituted a chunk
    would produce a perfectly well-formed artifact carrying evidence the query
    never retrieved.
    """
    with pytest.raises(ContextAssemblyError):
        builder.resolve(["absent"])

    with pytest.raises(ContextAssemblyError):
        builder.assemble(builder.resolve(["absent"]), "a query")


def test_m212_duplicate_chunk_ids_are_preserved_rather_than_collapsed(builder):
    """The supplied sequence is not rewritten into a different one.

    An engineering decision, and one **M2-04 cannot exercise**:
    `rank_candidates` accumulates candidates into a mapping keyed by chunk id,
    so a fused result is deduplicated by construction — verified below. A
    duplicate therefore says something about the caller, and collapsing it here
    would silently change the retrieval result the caller supplied.
    """
    supplied = ["c1", "c0", "c1"]

    prompt = builder.assemble(builder.resolve(supplied), "a query")

    assert prompt.chunk_ids == supplied
    assert prompt.context.split(CONTEXT_SEPARATOR) == [
        "bravo text",
        "alpha text",
        "bravo text",
    ]


def test_m212_the_fused_route_cannot_supply_a_duplicate_id():
    """The premise the duplicate decision rests on, checked rather than asserted.

    If **M2-04** could emit a repeated id, the paragraph above would be wrong
    about where duplicates come from. It cannot, and this is where that would
    be discovered.
    """
    fused = reciprocal_rank_fusion(["a", "b", "c"], ["c", "a", "d"], top_k=10)

    assert len(fused) == len(set(fused))


def test_m212_an_empty_corpus_resolves_nothing_and_assembles_nothing():
    """Both degenerate inputs at once, and neither is special-cased."""
    builder = ContextBuilder([])

    assert builder.assemble(builder.resolve([]), "a query").context == ""
    with pytest.raises(ContextAssemblyError):
        builder.resolve(["c0"])


# ---------------------------------------------------------------------------
# 6. Text that breaks naive assembly
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "text",
    [
        "punctuation: commas, semicolons; dashes — and \"quotes\" plus 'apostrophes'",
        "unicode: café naïve résumé — 日本語 — Ελληνικά — עברית — 🚀 emoji",
        "multiline\nsecond line\nthird line",
        "trailing whitespace   ",
        "   leading whitespace",
        "backslash \\ and tab\tand carriage\rreturn",
        "json-looking {\"id\": \"not-a-chunk-id\"} and markup <b>bold</b>",
        "x" * 20_000,
    ],
)
def test_m212_special_text_passes_through_byte_for_byte(text):
    """Chunk text is carried verbatim; assembly is not a formatter.

    No escaping, no stripping, no normalization, no encoding change, no
    collapsing of whitespace and no truncation. A single-chunk context is the
    exact chunk text, which is the strongest form of the claim.
    """
    builder = ContextBuilder([chunk("only", text)])

    prompt = builder.assemble(builder.resolve(["only"]), "a query")

    assert prompt.context == text


def test_m212_a_multiline_chunk_does_not_split_into_two_blocks():
    """Single newlines inside chunk text are content, not boundaries.

    This is why `CONTEXT_SEPARATOR` is a blank line rather than a newline: a
    multiline chunk assembled with `"\\n"` would be indistinguishable from two
    chunks, and `ALTM-ASSEMBLE-1`'s diff would silently mis-attribute evidence.
    """
    builder = ContextBuilder(
        [chunk("a", "line one\nline two"), chunk("b", "line three", start=20)]
    )

    prompt = builder.assemble(builder.resolve(["a", "b"]), "a query")

    assert prompt.context.split(CONTEXT_SEPARATOR) == ["line one\nline two", "line three"]


def test_m212_empty_chunk_text_is_neither_special_cased_nor_rejected():
    """Legal here only because nothing here validates the corpus.

    `sample_rag/chunker.py` raises `ChunkConstructionError` on an empty chunk
    and `docs/CHUNK_CONTRACT.md` §17 invariant 1 forbids one, so the committed
    corpus contains none — this stage therefore neither re-validates the
    invariant the Chunker owns nor invents a behaviour for a chunk the corpus
    cannot hold. Recorded so the absence of handling is a decision rather than
    an oversight.
    """
    builder = ContextBuilder([chunk("a", ""), chunk("b", "body", start=1)])

    prompt = builder.assemble(builder.resolve(["a", "b"]), "a query")

    assert prompt.chunk_ids == ["a", "b"]
    assert prompt.context == CONTEXT_SEPARATOR + "body"


# ---------------------------------------------------------------------------
# 7. Determinism
# ---------------------------------------------------------------------------


def test_m212_identical_inputs_produce_identical_prompts(builder):
    """Same corpus + same ordered ids + same query ⇒ equal artifacts.

    Determinism in the form `docs/CHUNK_CONTRACT.md` §5 states it for runtime
    artifacts, and achieved the way this repository already achieves it — by
    excluding the values that would break it (§12, `docs/MILESTONE_1A.md` build
    item 1's `created_at` removal, `retrieval_time_ms = 0`).
    """
    supplied = ["c3", "c0", "c4"]

    first = builder.assemble(builder.resolve(supplied), "a query")
    second = builder.assemble(builder.resolve(supplied), "a query")

    assert first == second


def test_m212_two_builders_over_one_corpus_agree(real_chunks):
    """No construction-order or instance state reaches the artifact.

    Two independently constructed builders over the same corpus must produce
    equal prompts — the specification that would catch a dict iteration order,
    an insertion counter or a cached value escaping into the output.
    """
    supplied = [record["id"] for record in real_chunks[:8]]

    first = ContextBuilder(real_chunks).assemble(
        ContextBuilder(real_chunks).resolve(supplied), "a query"
    )
    second = ContextBuilder(list(real_chunks)).assemble(
        ContextBuilder(list(real_chunks)).resolve(supplied), "a query"
    )

    assert first == second


def test_m212_the_builder_does_not_mutate_the_corpus_it_was_given(real_chunks):
    """Read-only, structurally — the property `Retriever` and `Generator` hold.

    Both the collection and the chunk mappings inside it are checked: the
    records `resolve` returns are the corpus's own objects, and assembly must
    not write through them.
    """
    before = [dict(record) for record in real_chunks]
    supplied = [record["id"] for record in real_chunks[:5]]

    builder = ContextBuilder(real_chunks)
    builder.assemble(builder.resolve(supplied), "a query")

    assert real_chunks == before


def test_m212_a_caller_mutating_its_list_afterwards_cannot_change_the_builder():
    """The collection is copied at construction, exactly as `Retriever` copies it."""
    chunks = corpus(("c0", "alpha text"))
    builder = ContextBuilder(chunks)

    chunks.clear()

    assert builder.resolve(["c0"])[0]["text"] == "alpha text"


# ---------------------------------------------------------------------------
# 8. Integration over the committed corpus and the real M2-04 fused route
# ---------------------------------------------------------------------------


@pytest.fixture
def committed_fusion(real_chunks):
    """One real fused ranking over the committed corpus.

    The lexical route is run for real and fused against a deliberately
    different id ordering, so the fused sequence is genuinely **M2-04**'s
    output rather than a hand-written list that happens to look like one. No
    embedding model or FAISS index is loaded — the semantic route's *ranking*
    is what fusion consumes, and supplying one directly keeps this
    specification a statement about assembly rather than about retrieval.
    """
    retriever = Retriever(real_chunks)
    lexical = list(
        retriever.retrieve("python engineering experience", {"top_k": 5}).diagnostics[
            "retrieved_chunk_ids"
        ]
    )
    semantic = list(reversed([record["id"] for record in real_chunks[:5]]))
    order = canonical_order(real_chunks, set())

    return reciprocal_rank_fusion(semantic, lexical, top_k=5, order=order)


def test_m212_the_fused_ranking_reaches_the_prompt_unchanged(real_chunks, committed_fusion):
    """M2-04's ordered ids in, the same ordered ids out.

    The end-to-end statement of this sprint's seam over real corpus and real
    fusion output: `ordered canonical chunk ids -> Prompt`, with the ordering
    untouched in between.
    """
    builder = ContextBuilder(real_chunks)

    prompt = builder.assemble(builder.resolve(committed_fusion), "python engineering experience")

    assert prompt.chunk_ids == committed_fusion


def test_m212_every_committed_chunk_id_resolves_to_its_committed_text(
    real_chunks, real_chunks_by_id, committed_fusion
):
    """Canonical ids resolve to canonical text, over the committed corpus.

    Joined against the corpus mapping the suite already maintains rather than
    against the builder's own lookup, so the specification and the
    implementation do not share a source of truth.
    """
    builder = ContextBuilder(real_chunks)

    for record in builder.resolve(committed_fusion):
        assert record["text"] == real_chunks_by_id[record["id"]]["text"]
        assert record["document_id"] == real_chunks_by_id[record["id"]]["document_id"]


def test_m212_the_committed_prompt_is_deterministic(real_chunks, committed_fusion):
    """Two assemblies over the committed corpus produce equal prompts."""
    first = ContextBuilder(real_chunks)
    second = ContextBuilder(real_chunks)

    assert first.assemble(first.resolve(committed_fusion), "q") == second.assemble(
        second.resolve(committed_fusion), "q"
    )


# ---------------------------------------------------------------------------
# 9. The sprint boundary
# ---------------------------------------------------------------------------


def test_m212_the_context_builder_imports_nothing_from_the_pipeline():
    """It assembles what retrieval produced; it cannot reach retrieval to change it.

    An allowlist over the module's declared imports: `dataclasses` alone. A
    module that cannot import `sample_rag.retriever`, `sample_rag.fusion`,
    `sample_rag.vector_runtime` or `sample_rag.vector_index` cannot re-run,
    repair or second-guess a route — and cannot implement one either. It also
    cannot reach `json`, `pathlib`, `os`, `urllib`, `requests` or any SDK, which
    is the structural form of *no filesystem I/O, no network I/O, no model
    invocation*.
    """
    import sample_rag.context_builder

    assert imported_roots(sample_rag.context_builder) == {"dataclasses"}


def test_m212_no_retrieval_generation_or_evaluation_name_is_declared():
    """Nothing named for a capability this sprint must not activate.

    Stated over declared names rather than raw source text, the convention
    `tests/test_lexical_bm25.py` set: the module docstring legitimately
    *mentions* BM25, RRF, DeepSeek and Ragas to record what it does not do, and
    a substring check over source would make that prose a failure while missing
    a scorer declared under any other name.
    """
    import sample_rag.context_builder

    names = {name.lower() for name in declared_names(sample_rag.context_builder)}

    for forbidden in (
        "bm25",
        "rrf",
        "fusion",
        "rerank",
        "embed",
        "vector",
        "faiss",
        "deepseek",
        "ragas",
        "deepeval",
        "promptfoo",
        "generate",
        "token",
        "budget",
        "truncat",
    ):
        assert not any(forbidden in name for name in names), (
            f"context assembly declares a {forbidden!r} name"
        )


def test_m212_the_milestone_1a_generator_does_not_consume_the_prompt():
    """The Milestone 1A quotation `Generator` is untouched — by M2-12 and by M2-06.

    `docs/GENERATION_CONTRACT.md` v1.0.0 remains authoritative for *"the
    historical Milestone 1A deterministic quotation-generator contract"*
    (§24.1), which §22/G-2 approved as `Generator.generate(query, retrieval:
    RetrievalResult)`. RO-13 did **not** withdraw v1.0.0, and this specification
    records that `sample_rag/generator.py` still conforms to it byte for byte.

    **The Milestone 2 model-backed generator is a different module**, governed
    by v2.0.0 (§24) and specified in `tests/test_model_generator.py`. Its
    coexistence with this one, and which of the two is the
    `docs/architecture.md` §5 `Generator` row, is **M2-14** authority — RO-13
    §24.2 kept that row's synchronization open and separate. This specification
    therefore keeps the v1.0.0 component pinned rather than asserting anything
    about the v2 one.
    """
    import sample_rag.generator

    assert "context_builder" not in inspect.getsource(sample_rag.generator)

    parameters = list(
        inspect.signature(sample_rag.generator.Generator.generate).parameters
    )
    assert parameters == ["self", "query", "retrieval"]


def test_m206_the_context_builder_is_reached_only_by_the_model_backed_generator():
    """The seam has exactly one pipeline consumer, and it is the one M2-06 added.

    Stated over the package by glob, mirroring
    `tests/test_vector_index.py::test_m201b_no_other_pipeline_module_imports_faiss`
    and `tests/test_lexical_bm25.py::test_m203_the_semantic_route_is_untouched_by_the_lexical_one`,
    so a module added later is covered without anyone remembering to add it.

    **M2-12 recorded that the Context Builder was reached only by its own
    specifications *"until a consumer exists, which is M2-06"*.** That consumer
    now exists, and this is the same specification narrowed to name it: an
    **allowlist**, so a second consumer arriving fails here whether or not
    anyone thought to forbid it. The property M2-12 was protecting — that
    assembly is not wired into arbitrary pipeline modules — is preserved, not
    relaxed: the count moved from zero to exactly one, and the one is named.

    **No orchestration layer was introduced**, and `scripts/cli.py` is
    unchanged: its chain is still `Retriever.retrieve -> Generator.generate`
    over the Milestone 1A quotation path.
    """
    import sample_rag.context_builder

    package_root = pathlib.Path(sample_rag.context_builder.__file__).parent

    borrowers = []
    for path in sorted(package_root.glob("*.py")):
        if path.name == "context_builder.py":
            continue

        module = importlib.import_module(f"sample_rag.{path.stem}")
        if "context_builder" in inspect.getsource(module):
            borrowers.append(path.name)

    assert borrowers == ["model_generator.py"], (
        f"the context builder is reached from: {borrowers}"
    )


def test_m212_the_prompt_is_a_representation_and_not_an_invocation(builder):
    """A `Prompt` is data. Nothing here calls a model — **M2-06** does that.

    No credential, no endpoint, no client and no callable field: the artifact is
    four plain values, and a consumer must exist elsewhere for it to mean
    anything. **That remains true after M2-06**: the provenance §24.4 added is
    four scalars per chunk, and the module that invokes a provider is a
    different one. `docs/GENERATION_CONTRACT.md` §24.4 bars `system_prompt` and
    model configuration from this artifact by name.
    """
    prompt = builder.assemble(builder.resolve(["c0"]), "a query")

    assert isinstance(prompt, Prompt)
    assert isinstance(prompt.query, str)
    assert isinstance(prompt.context, str)
    assert isinstance(prompt.chunk_ids, list)
    assert all(isinstance(chunk_id, str) for chunk_id in prompt.chunk_ids)
    assert isinstance(prompt.provenance, list)
    assert all(isinstance(record, ChunkProvenance) for record in prompt.provenance)
    assert not any(callable(getattr(prompt, field)) for field in prompt.__dataclass_fields__)
