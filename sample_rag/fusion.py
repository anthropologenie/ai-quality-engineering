"""Reciprocal Rank Fusion over two independently ranked retrieval routes.

Sprint M2.04: the Milestone 2A activation of register capability **M2-04**,
under Repository Owner ruling **RO-07 — Milestone 2 Execution Sequencing**
(`docs/DEFERRED_ITEMS_REGISTER.md` §2, `docs/roadmap.md` §1.1). RO-07's
clarification is explicit that **M2-04 is one capability, staged rather than
split**: Milestone 2A *"exercises the semantic and lexical retrieval routes"*,
and Milestone 2B *"activates the structured SQL branch and completes the
architecture"*. This module is the 2A half, and only that half.

    canonical corpus
          |
          +----------------------------+
          |                            |
          v                            v
    BGE -> FAISS                     BM25
    semantic route                   lexical route
    (sample_rag/vector_runtime.py)   (sample_rag/retriever.py)
          |                            |
          v                            v
    ranked chunk ids             ranked chunk ids
          |                            |
          +-------------+--------------+
                        |
                        v
                       RRF                      <-- this module
                        |
                        v
              fused ranked chunk ids

What this module is deliberately *not*
---------------------------------------
**It consumes the two routes; it does not repair them.** No BM25 parameter,
no BM25 tokenization, no FAISS index, no embedding provider and no chunk is
touched by anything here — this module imports nothing at all beyond the
repository's own package boundary, and in particular imports neither
`sample_rag.retriever` nor `sample_rag.vector_runtime`. It cannot:
`tests/test_lexical_bm25.py::test_m203_the_semantic_route_is_untouched_by_the_lexical_one`
allows exactly one borrower of the lexical route, and it is `generator.py`.
That constraint is what fixed this module's shape — **a pure function over two
ranked id lists** — rather than a retrieval object that reaches into either
route. The seam is the smallest one the repository permits, and the repository
chose it before this sprint did.

**No third route.** The structured/SQL branch is Milestone 2B and no JobOps
corpus is connected; the signature below takes exactly two named routes, so
three-route fusion is not something a caller can reach by passing one more
argument. **No reranking** (**M2-05**), **no query rewriting or expansion**,
**no learned or weighted fusion**, **no LLM reranking**, **no generation**.

**No score fusion.** RRF is defined on *positional ranks* and this module reads
nothing else: a BM25 score and a FAISS inner product are quantities on
incomparable scales, and any scheme for making them comparable is the score
normalization `sample_rag/retriever.py` deliberately removed at Sprint M2.03.
Neither route's score reaches this module — the lexical route's scores stay in
its own `diagnostics`, and `VectorStore.query(vector, top_k) -> list[str]`
never exposed one at all (`docs/M2.01C_…` §13: *"the frozen return type is
`list[str]`"*).

**No second chunk identity.** Every id in, and every id out, is the
repository's canonical `chunks[].id` — the identity
`docs/CHUNK_CONTRACT.md` §17 makes globally unique, the one
`VectorStore.query` returns, and the one `Retriever` ranks on. Sprint M2.03
recorded that the two routes already agreed on it *"so a later fusion sprint
has one identity to fuse on rather than two"*. This module is that sprint, and
it introduces no `hybrid_chunk_id`, `fusion_id` or `retrieval_id`.

The RRF contract
-----------------
Documented here because **no repository authority states it**. `k`, the
tie-break below and the duplicate semantics are **engineering decisions of this
sprint**, recorded in `docs/M2.04_RRF_Fusion_Report.md`, and are not Repository
Owner authority — the same standing `sample_rag/retriever.py` records for `k1`,
`b` and its IDF variant.

    RRF(d) = SUM over routes r containing d of   1 / (k + rank_r(d))

    rank_r(d) is 1-based and positional: the first id a route returns has
    rank 1, the second rank 2, and so on.

* **Two routes, exactly.** Not a variadic list — see above.
* **Candidate universe** — the **union** of the ids appearing in either route.
  A candidate found by only one route keeps that route's single contribution
  and is fully eligible for the fused result; a candidate found by both
  accumulates both. Nothing is discarded for being unilateral, which is the
  property that lets the semantic route recover paraphrased evidence BM25
  cannot see (`tests/test_lexical_bm25.py::test_m203_bm25_carries_no_semantic_understanding`).
* **No penalty term.** An id missing from a route contributes nothing from it;
  it is not charged a notional worst rank. Charging one would be a weighting
  scheme, and would make the fused score depend on how deep each route was
  asked to go rather than on where it placed the candidate.
* **Duplicates within a route** — the **first** (best) occurrence fixes that
  route's rank and later occurrences contribute nothing. Neither route emits
  duplicates today, so this is a definition rather than a workaround; it is
  defined this way because counting an id twice would let one route award a
  single candidate two contributions and outweigh the other route, which is
  weighting by another name.
* **Ranking is on the exact score**, not a rounded one. This is the opposite of
  the decision `sample_rag/retriever.py` records for BM25, and deliberately so:
  BM25 rounds to `BM25_SCORE_PRECISION` because its score accumulates over many
  terms, where float noise would *hide* real collisions and make the tie-break
  an unreachable path. An RRF score is a sum of at most two unit fractions
  taken in a fixed order, so equal inputs produce bit-identical sums and ties
  are already exactly reachable. Rounding first could only *manufacture* ties
  between candidates whose scores genuinely differ.
* **Ties** — see `rank_candidates`.
* **`top_k`** — see `reciprocal_rank_fusion`.
* **Output identity** — `list[str]` of canonical chunk ids, the shape
  `docs/architecture.md` §7 already fixes for the semantic route.
"""

# The RRF constant. **Engineering decision, not repository authority** — no
# committed authority in this repository states a value, which this sprint's
# Phase 1 discovery verified by inspection of `docs/architecture.md`,
# `docs/roadmap.md` and `docs/DEFERRED_ITEMS_REGISTER.md`.
#
# 60 is the value introduced with the method itself — Cormack, Clarke &
# Buettcher, *Reciprocal Rank Fusion outperforms Condorcet and individual Rank
# Learning Methods* (SIGIR 2009) — and the value Elasticsearch and the wider
# literature carry as their default. It is chosen for the same reason
# `sample_rag/retriever.py` chose the conventional `k1 = 1.2` and `b = 0.75`:
# the ranking this module produces is then the one a reader who knows RRF
# expects, and any future retuning is a visible change to a named constant.
#
# It is **not tuned against the 22-question Evidence Trace benchmark**, and was
# fixed before that benchmark was executed. Tuning a retrieval parameter
# against the expectations it is measured by is register capability **M2-15**,
# which `docs/roadmap.md` §1.1 places at Milestone 2C precisely because it
# needs a quality signal (**M2-07**, Ragas) that does not exist yet.
#
# What it does: k damps the influence of top ranks. A large k flattens the
# difference between rank 1 and rank 2, so agreement between the routes matters
# more than either route's own confidence; a small k lets a single route's
# first place dominate. At k = 60 a rank-1 hit is worth 1/61 and a rank-5 hit
# 1/65 — a 6% spread across the retrieval depth below, so two routes agreeing
# anywhere in their top 5 outranks either route's unilateral first place.
RRF_K = 60

# Retrieval depth for the fused route, matching `sample_rag/retriever.py`'s
# `DEFAULT_TOP_K` exactly. Restated rather than imported: this module may not
# import the lexical route (see the module docstring), the same constraint that
# already keeps `SUPPORTED_EXTENSIONS` duplicated between
# `sample_rag/knowledge_source.py` and `scripts/build_manifest.py`
# (`docs/ENGINEERING_TRACEABILITY_REGISTER.md` AH-9). Holding the two equal is
# what makes Chunk Precision@K comparable across the routes, since K is the
# observed retrieval size (`evaluation/retrieval_metrics.py`).
DEFAULT_TOP_K = 5

# Reporting precision for a fused score, the repository's established
# serialization precision for retrieval scores (`BM25_SCORE_PRECISION`) and for
# metric values (`evaluation/retrieval_metrics.py` `PRECISION` is 4 for
# ratios). **Nothing ranks on this value** — see the module docstring. It
# exists so a diagnostic record can print a score without a caller inventing a
# format.
RRF_SCORE_PRECISION = 6


def positional_ranks(chunk_ids) -> dict:
    """Map each id to its 1-based position in one route's ranked output.

    The whole of what RRF reads from a route: *where* the route placed a
    candidate, never how strongly it scored it.

    First occurrence wins. `dict.setdefault` states that directly rather than
    letting it fall out of iteration order, so a duplicated id keeps its best
    rank instead of silently being demoted to its last one — the duplicate
    semantics the module docstring fixes.

    Ranks are 1-based because RRF is defined on ranks, not on offsets: at
    `k = 60` the difference between a 0-based and a 1-based first place is
    1/60 against 1/61, which is a different ranking function, not a different
    spelling of the same one.
    """
    ranks: dict = {}
    for position, chunk_id in enumerate(chunk_ids, start=1):
        ranks.setdefault(chunk_id, position)

    return ranks


def rank_candidates(semantic_ids, lexical_ids, k: float = RRF_K, order=()) -> list[tuple]:
    """Score the union of both routes' ids and order it deterministically.

    Returns `(chunk_id, score)` pairs, best first — the scored ordering
    `reciprocal_rank_fusion` truncates. It is a separate function for the same
    reason `Retriever.rank_candidates` is: a ranking is only explainable
    against the scores that produced it, and a specification that can read them
    can recompute the order independently of this module.

    Three ordering levels, total over the candidate universe:

    1. **RRF score, descending.**

    2. **The canonical ordering authority `order`**, by position. This is the
       tie-break's substance, and `order` is how the repository's existing
       convention reaches a function that may not read the corpus. Sprint
       P3.7.5 fixed the lexical route's ordering as *score, then canonical
       documents ahead of superseded ones, then committed corpus position*;
       the last two levels of that rule are a **total order over corpus
       chunks**, so a caller can express them as a single sequence and
       `scripts/run_hybrid_retrieval.py` does. Passing the corpus ordering in
       preserves P3.7.5 for the fused route exactly, without this module
       learning what a document, a manifest or a canonical designation is.

       **No repository authority governs tie-breaking after fusion** — Sprint
       M2.01C recorded precisely this gap, noting that the vector route has no
       stated tie-break and that the question *"would become a real question
       the moment a second route's results are fused with these (M2-04)"*
       (`docs/M2.01C_Semantic_Query_Foundation_Report.md` §17). So this level
       is an **engineering decision**, and the decision is to reuse the
       ordering the repository already has rather than invent a second one.
       No alphabetical, hash-based, insertion-ordered or random tie-break is
       used anywhere here.

    3. **First appearance across the routes**, scanning the semantic route then
       the lexical one. Reachable only for an id that `order` does not cover,
       and such ids sort *after* every id it does. On the fused route this
       level is unreachable, because both routes return ids drawn from the
       committed corpus and `order` is that corpus. It exists to keep the
       function total for a direct caller — the same reason
       `BM25Statistics.score` defines the empty-corpus normalization ratio it
       can never meet through `rank_candidates` — and it is what makes the
       hand-computable specifications below able to use bare ids without
       supplying a corpus.

    An empty route contributes no ranks and therefore no candidates, so fusing
    against one degenerates to the other route's own order: `1 / (k + rank)` is
    strictly decreasing in `rank`, so a single route's contributions preserve
    that route's ordering exactly. Both empty yields no candidates at all.

    `k` is a parameter so specifications can use small hand-computable values;
    it is documented as positive and is not validated, exactly as
    `BM25Statistics.score` does not validate `k1` or `b`. No repository path
    passes anything but `RRF_K`.
    """
    semantic = positional_ranks(semantic_ids)
    lexical = positional_ranks(lexical_ids)

    appearance: dict = {}
    for chunk_id in list(semantic_ids) + list(lexical_ids):
        appearance.setdefault(chunk_id, len(appearance))

    authority = {chunk_id: position for position, chunk_id in enumerate(order)}
    outside = len(authority)

    candidates = []
    for chunk_id, first_seen in appearance.items():
        # Accumulated in a fixed route order, which is what makes two
        # candidates carrying the same multiset of ranks compare exactly equal
        # rather than nearly so — the property the module docstring relies on
        # when it declines to round before ranking.
        score = 0.0
        if chunk_id in semantic:
            score += 1 / (k + semantic[chunk_id])
        if chunk_id in lexical:
            score += 1 / (k + lexical[chunk_id])

        candidates.append((chunk_id, score, authority.get(chunk_id, outside), first_seen))

    candidates.sort(key=lambda candidate: (-candidate[1], candidate[2], candidate[3]))

    return [(chunk_id, score) for chunk_id, score, _, _ in candidates]


def reciprocal_rank_fusion(
    semantic_ids,
    lexical_ids,
    k: float = RRF_K,
    top_k: int = DEFAULT_TOP_K,
    order=(),
) -> list[str]:
    """Fuse two ranked id lists into one, and return the best `top_k` ids.

    The module's entry point, and `list[str]` of canonical chunk ids — the same
    shape `docs/architecture.md` §7 fixes for `VectorStore.query`, so the fused
    route and the semantic route return the same kind of thing.

    **`top_k` counts over the union**, not over either route. A fused result
    can therefore be longer than either input, and asking for more than the
    union holds returns the whole union in fused order rather than padding it:
    truncation is the only thing `top_k` does.

    **`top_k <= 0` returns no ids**, and is guarded explicitly rather than left
    to slicing. `candidates[:top_k]` would be correct for `0` and quietly wrong
    for `-1`, where Python's negative-index semantics would drop the *last*
    candidate and return everything else — a retrieval depth of minus one
    returning four chunks. The guard makes the degenerate input mean the one
    thing it can defensibly mean.
    """
    if top_k <= 0:
        return []

    fused = rank_candidates(semantic_ids, lexical_ids, k, order)

    return [chunk_id for chunk_id, _ in fused[:top_k]]
