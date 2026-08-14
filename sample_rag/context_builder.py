"""Deterministic Context Assembly — the Assemble stage.

Sprint M2.12: register capability **M2-12** — *"Assemble stage — Context
Builder, `Prompt` artifact"* (`docs/DEFERRED_ITEMS_REGISTER.md` §4), allocated
to **Milestone 2A** by `docs/roadmap.md` §1.1 under Repository Owner ruling
**RO-07**, where it sits between **M2-04** (hybrid retrieval → RRF) and
**M2-06** (DeepSeek generation). That is the seam this module occupies:

    canonical corpus
          |
          v
    M2-04 RRF  (sample_rag/fusion.py)
          |
          v
    ordered canonical chunk ids            list[str]
          |
          v
    resolve()                              <-- this module
          |
          v
    ordered canonical chunk records
          |
          v
    assemble()                             <-- this module
          |
          v
    Prompt                                 generation-ready representation
          |
          v
    M2-06 real generation                  NOT this sprint

The interface is `docs/architecture.md` §5's, implemented exactly as that table
states it — `ContextBuilder.assemble(chunks, query) -> Prompt`, dependency
*Retriever*, responsibility *"Assemble retrieved chunks into a prompt within
budget"*. No signature is refined here. The repository's governance precedent
for refining a §5 interface row is a downstream **contract** amending it
explicitly (`docs/MILESTONE_1A.md` build item 4 over the `Retriever` row,
recorded as D-6 in `docs/GENERATION_CONTRACT.md` §2), which is a Repository
Owner action and not an implementing sprint's.

`resolve` exists because §5's `assemble` takes *chunks* while **M2-04** returns
*ids*: `reciprocal_rank_fusion(...) -> list[str]` is *"`list[str]` of canonical
chunk ids"*. The lookup between them is a named, separately specified step
rather than something hidden inside `assemble`, so that a caller composing
`assemble(resolve(fused_ids), query)` crosses the identity boundary in the open.

What this module is deliberately *not*
---------------------------------------
**It assembles what retrieval produced; it does not decide what retrieval
should have produced.** There is no second ranking mechanism here. The supplied
sequence is consumed in the order it arrives and emitted in that order — no
sort, no reordering, no score of any kind is read, computed or carried. RRF
ordering is a retrieval decision that `sample_rag/fusion.py` already made, and
re-deciding it here would put two rankers in one pipeline.

**No retrieval, of any route.** This module imports nothing from the repository
at all — not `sample_rag.retriever`, not `sample_rag.vector_runtime`, not
`sample_rag.fusion`. It cannot re-run, repair, extend or second-guess a route,
and `tests/test_lexical_bm25.py::test_m203_the_semantic_route_is_untouched_by_the_lexical_one`
holds it to that by glob over the package. **No reranking** (**M2-05**), no
query rewriting, no query expansion, no chunking change (**M2-17**), no
embedding change, no retrieval or prompt optimization (**M2-15**).

**No generation, and no model.** `Prompt` is a representation, not an
invocation: nothing here calls a model, opens a socket, reads an API key or
imports an SDK. **M2-06** is where a model consumes one of these. No evaluation
tool is activated either — Ragas (**M2-07**), DeepEval (**M2-08**) and
Promptfoo (**M3-01**) are untouched, and no faithfulness, groundedness or
hallucination measurement exists here.

**No `GenerationResult`, and no change to one.** `docs/GENERATION_CONTRACT.md`
is frozen at v1.0.0 and approved `Generator.generate(query, retrieval:
RetrievalResult)` at §22/G-2. **Nothing in this module changes that**: the
`Generator` is not touched, not re-signatured, and does not import this module.
§6.2 records the `generate(prompt: Prompt)` shape as *"the Milestone 2 target,
reached when a Context Builder exists"* — this sprint makes the Context Builder
exist; **which sprint changes the Generator's input, and whether it does, is
M2-06 / M2-14 authority and is not decided here.**

Determinism by exclusion
-------------------------
The discipline `docs/MILESTONE_1A.md` build item 1 applied when it removed
`created_at`, `sample_rag/retriever.py` applied when it fixed
`retrieval_time_ms` at 0, and `sample_rag/generator.py` applied to the whole
Generation artifact (`docs/GENERATION_CONTRACT.md` §12). No timestamp, no
measured duration, no random or hash-seed-dependent value, no floating-point
value, and no set or dict iteration order reaching an emitted sequence: every
sequence this module emits is derived positionally from the sequence it was
given. Identical corpus + identical ordered ids + identical query therefore
produce an identical `Prompt`, because the values that could vary are not
constructed.

Read-only, and structurally so: no filesystem I/O, no network I/O, and no
mutation of the corpus or of any chunk mapping it is handed — the same property
`sample_rag/retriever.py` and `sample_rag/generator.py` already hold.
"""

from dataclasses import dataclass

# `docs/architecture.md` §4 gives the Assemble stage the responsibility *"Fit
# within context window without silent truncation"* and the failure mode
# *"Retrieved evidence correct but dropped during assembly"*. Both are
# satisfied here by assembling every supplied chunk and dropping none, which is
# available because **no repository authority states a context budget**:
# §5's *"within budget"* and the glossary's *Context Window* (*"the bounded
# input space available to the generation model"*) name the concept without
# fixing a value, and §5 records *"Context-overflow handling under real token
# budgets"* as the Context Builder's **Future Evolution**. A context window is a
# property of a generation model; **M2-06** connects the first one. Inventing a
# token budget, a model-specific limit or a score-based drop rule now would be
# retrieval-quality policy invented inside context assembly — and a dropped
# chunk is precisely the Assemble-stage failure the architecture names.
CONTEXT_SEPARATOR = "\n\n"


class ContextAssemblyError(Exception):
    """A supplied chunk id does not exist in the corpus this builder was bound to.

    Named and module-level, following `ChunkConstructionError`,
    `DocumentConstructionError` and `VectorIndexCompatibilityError` — the
    repository's existing convention for a failure a caller is expected to be
    able to distinguish.
    """


@dataclass(frozen=True)
class Prompt:
    """The Assemble stage's output artifact — `docs/architecture.md` §4, §5.

    **No repository authority defines this artifact's fields.** `Prompt` is
    named by `docs/architecture.md` §5 and §7 and by `docs/glossary.md`, and
    `docs/GENERATION_CONTRACT.md` §21 excludes it from Milestone 1A by name; no
    committed text anywhere states a field, a schema or a serialization for it.
    The three fields below are therefore an **engineering decision of this
    sprint**, recorded in `docs/M2.12_Context_Builder_Report.md`, and each is
    the smallest thing an existing authority requires to exist:

    - `query` — `docs/architecture.md` §4 gives the Assemble stage the inputs
      *"Ranked chunks, query"* and §5 gives `assemble` the argument. A prompt
      that dropped the request it was assembled for could not be the Infer
      stage's input, whose stated input is the assembled prompt alone.
    - `context` — the assembled evidence itself, which is what *"Build the final
      prompt from retrieved evidence"* produces.
    - `chunk_ids` — the provenance that makes `ALTM-ASSEMBLE-1`'s investigation
      executable: *"Diff the assembled prompt against the retrieved chunk set
      before suspecting the model"* (`evaluation/altm_rules.py`). A diff needs
      identity, and a concatenated string alone carries none. The list is
      positionally aligned with the blocks of `context`, and its ids are the
      repository's canonical `chunks[].id` — the same identity **M2-04** fuses
      on and `docs/CHUNK_CONTRACT.md` §17 makes globally unique. **No second
      identity system is introduced.**

    Nothing else is carried. No score, no rank, no token count, no budget, no
    timestamp, no separator marker and no template — each would be this module
    asserting something no authority asked for, and a score or rank in
    particular would be retrieval's decision re-expressed as though assembly
    had a view on it. `diagnostics`, the open mapping `RetrievalResult` and
    `GenerationResult` both carry, is **deliberately absent**: it exists in
    those artifacts to hold per-request detail a named authority requires, and
    no authority requires any of it here.

    Frozen, and field order is the declaration order above — the convention
    `docs/GENERATION_CONTRACT.md` §13.1 fixed for `GenerationResult` and
    `sample_rag/retriever.py` already used for `RetrievalResult`. Frozen because
    the artifact records what was assembled and no consumer has a reason to
    mutate it. **No serialization is defined**: nothing persists a `Prompt`, and
    `docs/GENERATION_CONTRACT.md` §13.3's reasoning for `GenerationResult` — a
    query-derived artifact that exists for one request — applies unchanged.
    """

    query: str
    context: str
    chunk_ids: list


class ContextBuilder:
    """Assembles ranked retrieval output into a prompt — `docs/architecture.md` §5.

    Bound to a chunk collection at construction, exactly as `Retriever` is, and
    for the same reason: the corpus is a property of the pipeline rather than of
    a query, and resolving ids against a collection passed in per call would let
    two assemblies of one query's results disagree about what the corpus is.

    Stateless across calls beyond that binding. Every value returned is derived
    from the arguments of a single call and the fixed corpus, so two calls with
    equal arguments cannot differ and no call can observe another.

    Owns the ALTM **Assemble** stage (`docs/glossary.md`). It does **not** own
    abstention: `docs/GENERATION_CONTRACT.md` §9.3 gives the empty-evidence
    decision to the `Generator`, and this module makes no outcome decision at
    all (see `assemble`).
    """

    def __init__(self, chunks: list):
        """Bind the builder to an already-loaded, already-validated chunk collection.

        The collection is copied into a private list so a caller's later
        mutation cannot change what this builder resolves against, and so the
        builder has nothing to write back to — the property
        `Retriever.__init__` states in the same words.

        The id index is built once, over the copy, for the same reason
        `Retriever` derives its BM25 statistics once: it is a property of the
        corpus, not of a query.

        **Corpus id uniqueness is not re-validated here.** `sample_rag/chunker.py`
        already raises `ChunkConstructionError` on a duplicate chunk id and
        `docs/CHUNK_CONTRACT.md` §17 makes `Chunk.id` globally unique, so a
        second check in this module would be a second owner of an invariant the
        Chunker holds. Corpus **order** is preserved in `self._chunks` exactly
        as committed, though nothing here ranks on it — this module's output
        order is the caller's supplied order and never the corpus's.
        """
        self._chunks = list(chunks)
        self._by_id = {chunk["id"]: chunk for chunk in self._chunks}

    def resolve(self, chunk_ids) -> list:
        """Resolve ordered canonical chunk ids to their canonical chunk records.

        The bridge between **M2-04**'s output and §5's `assemble(chunks, ...)`:
        `reciprocal_rank_fusion` returns `list[str]`, and this returns the
        chunk records those ids name, **in the supplied order**.

        **Order is preserved exactly, and nothing here can reorder.** The result
        is built by iterating the supplied sequence positionally; there is no
        sort, no key function and no comparison anywhere in this method. `[A, C,
        B]` resolves to `[chunk_A, chunk_C, chunk_B]`, never to corpus order.
        No BM25 score, semantic similarity, RRF score, canonical rank, document
        length, section name or timestamp is read — none of them is even
        reachable from here, because the ranking that used them already
        happened.

        **Each id resolves to exactly its own chunk, or to nothing.** No
        substitution, no nearest match, no fallback lookup and no re-retrieval:
        if an id is not in the corpus this builder was bound to, that is
        `ContextAssemblyError` and not another chunk.

        **Missing ids raise — an engineering decision (no authority defines
        this).** Returning a shorter list would drop evidence silently, which is
        exactly `docs/architecture.md` §4's named Assemble-stage failure
        (*"Retrieved evidence correct but dropped during assembly"*) and what
        its responsibility (*"without silent truncation"*) forbids; substituting
        a chunk would break identity; and emitting a placeholder would put text
        in the context that no corpus chunk supports. Raising is the one
        behaviour that neither drops silently nor invents, and it makes the
        condition visible at the seam where it arises rather than downstream in
        an answer.

        **Duplicate ids are preserved, not collapsed — also an engineering
        decision.** No authority defines duplicate semantics at this seam, and
        **M2-04 cannot produce one**: `rank_candidates` accumulates candidates
        into a mapping keyed by chunk id, so its output is deduplicated by
        construction. A duplicate therefore says something about the caller, and
        collapsing it would silently change the sequence the caller supplied
        into a different one. Preserving it keeps `resolve` a positional,
        length-preserving function of its input — `len(resolve(ids)) ==
        len(ids)` on every non-raising path — which is the property that lets
        `Prompt.chunk_ids` stay aligned with the blocks of `Prompt.context`.

        Reads the corpus; never writes to it. The chunk mappings returned are
        the corpus's own objects, not copies — the same pass-through
        `scripts/cli.py` records for runtime artifacts — and nothing here
        mutates one.
        """
        resolved = []
        for chunk_id in chunk_ids:
            if chunk_id not in self._by_id:
                raise ContextAssemblyError(
                    f"Chunk id {chunk_id!r} is not present in the corpus this "
                    f"ContextBuilder was constructed over."
                )
            resolved.append(self._by_id[chunk_id])

        return resolved

    def assemble(self, chunks, query: str) -> Prompt:
        """Assemble ranked chunks and a query into a `Prompt`.

        `docs/architecture.md` §5's interface, implemented at that signature
        exactly: `ContextBuilder.assemble(chunks, query) -> Prompt`, with
        `chunks` the *ranked chunks* §4 names as the Assemble stage's input.

        **The supplied order is the output order.** Blocks appear in `context`
        in the order `chunks` arrives, and `chunk_ids` records that same order
        positionally. No sort is applied, because there is nothing to reorder:
        the ranking is retrieval's and arrives already made.

        **Every supplied chunk is assembled; none is dropped or truncated.**
        See `CONTEXT_SEPARATOR` for why no budget is applied — no repository
        authority states one, and the model whose context window would define it
        does not exist until **M2-06**.

        **The empty sequence assembles to an empty context** — an engineering
        decision, and the smallest deterministic one: `Prompt` is a total
        function of its inputs here, so no branch, no sentinel text and no
        `None` enters the artifact, and an empty context is exactly true about
        an empty retrieval. **No abstention decision is made or implied.**
        `docs/GENERATION_CONTRACT.md` §9.3 places the empty-evidence outcome in
        the `Generator` (*"produced when the consumed `RetrievalResult` yields
        no evidence the Generator can quote"*) and §20.2 records the abstention
        predicate as the Generator's; moving that judgement into assembly would
        put one decision in two components. Whether an empty retrieval should
        become an abstention remains upstream and downstream of here, never
        here.

        **The context carries chunk text and separators, and nothing else** —
        no label, no numbering, no `[1]`-style citation marker, no document
        heading, no XML or Markdown delimiter, no instruction and no system
        preamble. No authority specifies any of them, and each would be text in
        the prompt that no corpus chunk supports. Attribution is carried by
        `chunk_ids`, in resolvable form, rather than by markup invented here —
        the reasoning `docs/GENERATION_CONTRACT.md` §15 already applied when it
        refused a free-text `citations` field alongside `supporting_evidence`.
        Instruction and system-prompt design is prompt engineering, which is
        **M2-15** and **M2-06**, not the Assemble stage.

        The separator is `CONTEXT_SEPARATOR`, and the assembly is **reversible**
        over any corpus whose chunk texts contain no blank line — the same claim
        `sample_rag/generator.py` makes for `STATEMENT_SEPARATOR`, and one the
        specifications check against the committed corpus rather than assume.
        That is what keeps `ALTM-ASSEMBLE-1`'s diff exact: the assembled prompt
        can be split back into the blocks that went into it.

        Reads the chunk mappings; never writes to one.
        """
        chunks = list(chunks)

        return Prompt(
            query=query,
            context=CONTEXT_SEPARATOR.join(chunk["text"] for chunk in chunks),
            chunk_ids=[chunk["id"] for chunk in chunks],
        )
