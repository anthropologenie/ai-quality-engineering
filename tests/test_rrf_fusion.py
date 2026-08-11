"""Specifications for two-route Reciprocal Rank Fusion — Sprint M2.04.

Register capability **M2-04**, at its Milestone 2A activation: *"Hybrid
retrieval — semantic and lexical routes, RRF over two routes"*
(`docs/roadmap.md` §1.1, under Repository Owner ruling **RO-07**). The
structured SQL branch is Milestone 2B and is specified nowhere here.

These specifications answer **one** of this sprint's two questions — *does the
RRF implementation work correctly?* The other — *does two-route RRF improve the
retrieval-quality problem recorded as M2.03-F-1?* — is a measurement, not a
specification, and it lives in `scripts/compare_retrieval_routes.py` and
`docs/M2.04_RRF_Fusion_Report.md`. **A passing file here asserts nothing about
retrieval quality**, and no specification below claims that a fused ranking is
a better ranking.

The expected RRF scores are recomputed from the published formula
`RRF(d) = Σ 1 / (k + rank(d))` in the arithmetic specifications, independently
of `sample_rag/fusion.py`. That is deliberate, and is the convention
`tests/test_lexical_bm25.py` set for BM25: a specification that called the
implementation to compute its own expectation would assert only that the
implementation equals itself.

Layout, in order: the arithmetic; the candidate universe; the ordering and its
tie-break; the degenerate inputs; determinism; the integration over the
committed corpus; and the sprint boundary.
"""

import ast
import importlib
import inspect
import pathlib

import pytest

from sample_rag.fusion import (
    DEFAULT_TOP_K,
    RRF_K,
    RRF_SCORE_PRECISION,
    positional_ranks,
    rank_candidates,
    reciprocal_rank_fusion,
)
from scripts.run_hybrid_retrieval import (
    FUSED_ROUTE,
    LEXICAL_ROUTE,
    ROUTE_TOP_K,
    SEMANTIC_ROUTE,
    canonical_order,
    fuse_routes,
    lexical_route,
)

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def imported_roots(module):
    """Every top-level package name imported by `module`'s source.

    The same helper `tests/test_lexical_bm25.py`, `tests/test_indexer.py` and
    `tests/test_vector_index.py` each carry, restated here for the same reason
    they restate it from each other: a specification file that imported its
    boundary check from another specification file would couple two suites that
    are meant to fail independently.
    """
    tree = ast.parse(inspect.getsource(module))

    roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".")[0])
    return roots


def imported_modules(module):
    """Every fully-qualified module name imported by `module`'s source."""
    tree = ast.parse(inspect.getsource(module))

    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def declared_names(module):
    """Every function, class, assignment target and argument `module` declares."""
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


def scores(semantic, lexical, k=RRF_K, order=()):
    """`chunk_id -> fused score`, for specifications that assert arithmetic."""
    return dict(rank_candidates(semantic, lexical, k, order))


# ---------------------------------------------------------------------------
# the arithmetic — `RRF(d) = Σ 1 / (k + rank(d))`
# ---------------------------------------------------------------------------


def test_m204_the_worked_example_scores_and_orders_exactly_as_the_formula_says():
    """M2-04 — the whole contract on one hand-computable example.

    Semantic `[A, B, C]`, lexical `[C, A, D]`, at the module's own `k`. Every
    expected value below is written as the formula's own arithmetic, so this
    specification is an independent statement of what RRF *is*:

        A   semantic rank 1, lexical rank 2   1/(k+1) + 1/(k+2)
        B   semantic rank 2                   1/(k+2)
        C   semantic rank 3, lexical rank 1   1/(k+3) + 1/(k+1)
        D                    lexical rank 3   1/(k+3)

    At `k = 60` that is A ≈ 0.032522, C ≈ 0.032266, B ≈ 0.016129, D ≈ 0.015873,
    so the fused order is **A, C, B, D** — and the two candidates both routes
    found lead the two neither route agreed on, which is the behaviour RRF
    exists to produce.
    """
    semantic = ["A", "B", "C"]
    lexical = ["C", "A", "D"]

    expected = {
        "A": 1 / (RRF_K + 1) + 1 / (RRF_K + 2),
        "B": 1 / (RRF_K + 2),
        "C": 1 / (RRF_K + 3) + 1 / (RRF_K + 1),
        "D": 1 / (RRF_K + 3),
    }

    assert scores(semantic, lexical) == pytest.approx(expected)
    assert [chunk_id for chunk_id, _ in rank_candidates(semantic, lexical)] == ["A", "C", "B", "D"]
    assert reciprocal_rank_fusion(semantic, lexical, top_k=4) == ["A", "C", "B", "D"]


def test_m204_ranks_are_one_based_and_positional():
    """M2-04 — rank 1, not rank 0, and position rather than score.

    A 0-based reading would make the first place worth `1/k` instead of
    `1/(k+1)` — at `k = 60`, 0.016667 against 0.016393. That is a different
    ranking function, not a different spelling of the same one, so the
    specification states the base directly.

    `positional_ranks` is asserted alongside it because it is the only thing
    RRF reads from a route: *where* the route placed a candidate, never how
    strongly it scored it. No BM25 score and no FAISS similarity is an input to
    anything in this module.
    """
    assert positional_ranks(["A", "B", "C"]) == {"A": 1, "B": 2, "C": 3}
    assert scores(["A"], [])["A"] == pytest.approx(1 / (RRF_K + 1))
    assert scores(["A"], [])["A"] != pytest.approx(1 / RRF_K)


def test_m204_rank_one_contributes_more_than_rank_two_which_contributes_more_than_rank_three():
    """M2-04 — the contribution is strictly decreasing in rank.

    `1 / (k + rank)` is strictly decreasing for positive `k`, which is what
    makes a single route's contributions preserve that route's own order, and
    what makes an empty second route degenerate to the first route unchanged
    rather than to an arbitrary permutation of it.
    """
    route = [f"r{rank}" for rank in range(1, 6)]
    measured = scores(route, [])

    contributions = [measured[chunk_id] for chunk_id in route]

    assert contributions == [1 / (RRF_K + rank) for rank in range(1, 6)]
    assert contributions == sorted(contributions, reverse=True)
    assert len(set(contributions)) == len(contributions)


def test_m204_a_candidate_found_by_both_routes_accumulates_both_contributions():
    """M2-04 — the sum is over routes, and both terms are present.

    The shared candidate carries `1/(k+1) + 1/(k+1)`, exactly twice a rank-1
    unilateral contribution — asserted as a sum rather than as a doubling, so
    the specification would still hold if the two ranks differed.
    """
    shared = scores(["A"], ["A"])["A"]

    assert shared == pytest.approx(1 / (RRF_K + 1) + 1 / (RRF_K + 1))
    assert shared == pytest.approx(2 * scores(["A"], [])["A"])


def test_m204_a_candidate_found_by_one_route_carries_only_that_routes_contribution():
    """M2-04 — **no penalty term**, and absence is not a score.

    A candidate the other route never returned is not charged a notional worst
    rank, is not down-weighted, and is not excluded. It carries one
    contribution and competes on it.

    Charging a penalty would make a fused score depend on how deep each route
    was asked to go rather than on where it placed the candidate — and it would
    structurally suppress exactly the paraphrase evidence
    `tests/test_lexical_bm25.py::test_m203_bm25_carries_no_semantic_understanding`
    shows BM25 cannot see and the semantic route can.
    """
    measured = scores(["A", "B"], ["B"])

    assert measured["A"] == pytest.approx(1 / (RRF_K + 1))
    assert measured["B"] == pytest.approx(1 / (RRF_K + 2) + 1 / (RRF_K + 1))
    assert measured["A"] == pytest.approx(scores(["A"], [])["A"])


def test_m204_route_agreement_outranks_a_unilateral_first_place():
    """M2-04 — the behavioural consequence of `k = 60`, stated rather than assumed.

    A candidate placed 5th by *both* routes beats one placed 1st by a single
    route: `2/(k+5) ≈ 0.030769` against `1/(k+1) ≈ 0.016393`. This is the
    property that makes RRF a fusion rather than a concatenation, and it is
    what `RRF_K`'s value buys — at a much smaller `k` a single route's first
    place would dominate instead.

    It is a statement about the ranking function. **It is not a claim that the
    agreed candidate is the better answer**; whether agreement predicts
    relevance on this corpus is measured, not specified.
    """
    semantic = ["s1", "s2", "s3", "s4", "shared"]
    lexical = ["l1", "l2", "l3", "l4", "shared"]

    measured = scores(semantic, lexical)

    assert measured["shared"] == pytest.approx(2 / (RRF_K + 5))
    assert measured["s1"] == pytest.approx(1 / (RRF_K + 1))
    assert measured["shared"] > measured["s1"]
    assert reciprocal_rank_fusion(semantic, lexical, top_k=1) == ["shared"]


# ---------------------------------------------------------------------------
# the candidate universe
# ---------------------------------------------------------------------------


def test_m204_the_candidate_universe_is_the_union_of_both_routes():
    """M2-04 — union, not intersection, and nothing is invented.

    Every id either route returned is eligible; no id that neither returned can
    appear. Both halves matter: an intersection would discard precisely the
    unilateral evidence fusion exists to preserve, and an output id absent from
    both inputs would mean the fusion layer had become a retrieval layer.
    """
    semantic = ["A", "B", "C"]
    lexical = ["C", "D"]

    fused = reciprocal_rank_fusion(semantic, lexical, top_k=99)

    assert set(fused) == {"A", "B", "C", "D"}
    assert len(fused) == 4


def test_m204_disjoint_routes_contribute_every_candidate_and_interleave_by_rank():
    """M2-04 — no shared candidate at all, which is a real case on this corpus.

    With no overlap every candidate carries one contribution, so the fused
    order is the rank-wise interleaving of the two routes: both rank-1s, then
    both rank-2s, and so on. Ties within each pair are broken by the ordering
    rule specified below, not by the arithmetic.
    """
    fused = reciprocal_rank_fusion(["A", "B"], ["C", "D"], top_k=99)

    assert set(fused) == {"A", "B", "C", "D"}
    assert set(fused[:2]) == {"A", "C"}
    assert set(fused[2:]) == {"B", "D"}


def test_m204_unequal_route_lengths_with_partial_overlap_keep_every_candidate():
    """M2-04 — the ordinary case: routes of different depths, partly agreeing.

    The shorter route does not truncate the union, and its candidates are not
    advantaged or disadvantaged by its length — only by where in it they sit.
    """
    semantic = ["A", "B", "C", "D", "E"]
    lexical = ["C", "F"]

    fused = reciprocal_rank_fusion(semantic, lexical, top_k=99)

    assert set(fused) == {"A", "B", "C", "D", "E", "F"}
    assert fused[0] == "C"
    assert fused.index("F") < fused.index("D")


# ---------------------------------------------------------------------------
# ordering and tie-breaking
# ---------------------------------------------------------------------------


def test_m204_tied_scores_are_broken_by_the_canonical_ordering_authority():
    """M2-04 — the tie-break is the repository's existing ordering, supplied as `order`.

    Two candidates each found by one route at the same rank score exactly
    equally — the tie is genuine, not a float artifact. Sprint P3.7.5's rule
    below the score is *canonical documents ahead of superseded ones, then
    committed corpus position*, and `scripts/run_hybrid_retrieval.py`
    materializes those two levels as one sequence. Passing that sequence in
    settles the tie by the repository's own convention.

    **No repository authority governs tie-breaking after fusion** — Sprint
    M2.01C recorded the gap and named M2-04 as where it would become real. This
    is therefore an engineering decision, and the decision is to reuse the
    ordering the repository already has rather than to invent an alphabetical,
    hash-based or insertion-ordered second one. The specification proves it is
    the authority that decides, by flipping the authority and watching the
    result flip with it.
    """
    tied = scores(["A"], ["B"])
    assert tied["A"] == tied["B"]

    assert reciprocal_rank_fusion(["A"], ["B"], top_k=2, order=["B", "A"]) == ["B", "A"]
    assert reciprocal_rank_fusion(["A"], ["B"], top_k=2, order=["A", "B"]) == ["A", "B"]


def test_m204_the_tie_break_never_reorders_candidates_whose_scores_differ():
    """M2-04 — the ordering authority sits *below* the score and cannot cross it.

    The same property `Retriever._canonical_rank` holds for the lexical route:
    a sort rank, never a weight, read only after the score comparison has
    already tied. An ordering authority that could promote a lower-scoring
    candidate would be a weighting scheme wearing a tie-break's name.
    """
    semantic = ["A", "B"]
    lexical = ["A"]

    assert scores(semantic, lexical)["A"] > scores(semantic, lexical)["B"]
    assert reciprocal_rank_fusion(semantic, lexical, top_k=2, order=["B", "A"]) == ["A", "B"]


def test_m204_a_canonical_chunk_wins_a_tie_against_a_superseded_one(
    real_chunks, real_manifest_entries
):
    """M2-04 — P3.7.5 preserved for the fused route, over the real corpus.

    The committed corpus carries two resume versions, and Sprint P3.7.5 exists
    because the default ordering silently preferred the **superseded** one: the
    Knowledge Manifest orders sources alphabetically and `v2_2` sorts before
    `v2_3`. This specification ties a canonical chunk against a superseded one
    and requires the canonical chunk to win — the same outcome P3.7.5 secured
    for the lexical route, now secured for the fused one.

    The tie is constructed by giving each candidate one rank-1 contribution
    from a different route, so the RRF scores are exactly equal and the
    ordering authority is the only thing that can decide.
    """
    canonical_ids = {entry["id"] for entry in real_manifest_entries if entry["canonical"]}
    order = canonical_order(real_chunks, canonical_ids)

    canonical = next(chunk["id"] for chunk in real_chunks if chunk["document_id"] in canonical_ids)
    superseded = next(
        chunk["id"] for chunk in real_chunks if chunk["document_id"] not in canonical_ids
    )

    assert order.index(canonical) < order.index(superseded)

    tied = scores([superseded], [canonical])
    assert tied[superseded] == tied[canonical]

    assert reciprocal_rank_fusion([superseded], [canonical], top_k=2, order=order) == [
        canonical,
        superseded,
    ]


def test_m204_canonical_order_covers_the_corpus_and_keeps_committed_position_within_each_group(
    real_chunks, real_manifest_entries
):
    """M2-04 — the ordering authority is exactly P3.7.5's two levels, and total.

    Every corpus chunk appears exactly once, canonical chunks precede superseded
    ones, and **within each group the committed corpus order is unchanged** —
    the positional level is inherited from a stable sort rather than restated,
    so it cannot drift from the enumeration it describes.

    Totality matters: no two chunks share a position, so the tie-break leaves no
    pair of corpus candidates unordered.
    """
    canonical_ids = {entry["id"] for entry in real_manifest_entries if entry["canonical"]}
    order = canonical_order(real_chunks, canonical_ids)

    assert len(order) == len(real_chunks)
    assert set(order) == {chunk["id"] for chunk in real_chunks}

    committed = [chunk["id"] for chunk in real_chunks]
    groups = {
        True: [chunk["id"] for chunk in real_chunks if chunk["document_id"] in canonical_ids],
        False: [chunk["id"] for chunk in real_chunks if chunk["document_id"] not in canonical_ids],
    }

    assert order == groups[True] + groups[False]
    for group in groups.values():
        assert group == [chunk_id for chunk_id in committed if chunk_id in set(group)]


def test_m204_without_an_ordering_authority_ties_fall_back_to_first_appearance():
    """M2-04 — the fallback level, and the fact that it is a fallback.

    Reachable only for an id the ordering authority does not cover. On the
    fused route it is unreachable, because both routes return ids drawn from
    the committed corpus and `order` is that corpus; it exists so the primitive
    stays total for a direct caller, the same reason `BM25Statistics.score`
    defines an empty-corpus normalization ratio it can never meet through
    `rank_candidates`.

    Ids the authority does cover sort **ahead** of ids it does not, so a
    partially covering authority cannot silently promote an uncovered id.
    """
    assert reciprocal_rank_fusion(["A"], ["B"], top_k=2) == ["A", "B"]
    assert reciprocal_rank_fusion(["B"], ["A"], top_k=2) == ["B", "A"]
    assert reciprocal_rank_fusion(["A"], ["B"], top_k=2, order=["B"]) == ["B", "A"]


# ---------------------------------------------------------------------------
# degenerate inputs — defined rather than accidental
# ---------------------------------------------------------------------------


def test_m204_an_empty_semantic_route_degenerates_to_the_lexical_order():
    """M2-04 — fusing against nothing returns the other route unchanged."""
    assert reciprocal_rank_fusion([], ["C", "A", "B"], top_k=99) == ["C", "A", "B"]


def test_m204_an_empty_lexical_route_degenerates_to_the_semantic_order():
    """M2-04 — the same property, pointed the other way.

    Both are specified rather than one, because a fusion that silently favoured
    a route would pass the first and fail the second.
    """
    assert reciprocal_rank_fusion(["C", "A", "B"], [], top_k=99) == ["C", "A", "B"]


def test_m204_both_routes_empty_returns_no_ids():
    """M2-04 — no candidates, no result, and no exception.

    An empty retrieval is a reachable, meaningful outcome the repository
    already carries — `RetrievalResult` defines an `EMPTY_RESULT_SCORE` path
    and the CLI's abstention path is reached through it — so fusion returns an
    empty list rather than raising.
    """
    assert reciprocal_rank_fusion([], [], top_k=5) == []
    assert rank_candidates([], []) == []


def test_m204_a_duplicate_within_a_route_keeps_its_best_rank_and_contributes_once():
    """M2-04 — duplicate semantics, defined.

    `A` at positions 1 and 3 of one route carries `1/(k+1)` — the best rank —
    and not `1/(k+1) + 1/(k+3)`. Counting it twice would let one route award a
    single candidate two contributions and outweigh the other route, which is
    weighting by another name.

    Neither route emits duplicates today, so this is a definition rather than a
    workaround; it is specified so it stays one.
    """
    measured = scores(["A", "B", "A"], [])

    assert measured["A"] == pytest.approx(1 / (RRF_K + 1))
    assert measured["B"] == pytest.approx(1 / (RRF_K + 2))
    assert reciprocal_rank_fusion(["A", "B", "A"], [], top_k=99) == ["A", "B"]


def test_m204_top_k_of_zero_or_less_returns_no_ids():
    """M2-04 — the guard that slicing would have got wrong.

    `candidates[:top_k]` is correct for `0` and quietly wrong for `-1`, where
    Python's negative-index semantics drop the *last* candidate and return
    everything else — a retrieval depth of minus one returning four chunks.
    Both values are specified because only the second distinguishes a guard
    from a slice.
    """
    semantic, lexical = ["A", "B", "C"], ["C", "D"]

    assert reciprocal_rank_fusion(semantic, lexical, top_k=0) == []
    assert reciprocal_rank_fusion(semantic, lexical, top_k=-1) == []
    assert reciprocal_rank_fusion(semantic, lexical, top_k=-99) == []


def test_m204_top_k_beyond_the_union_returns_the_whole_union_in_fused_order():
    """M2-04 — truncation is all `top_k` does; it never pads.

    The union of `[A, B, C]` and `[C, A, D]` holds four ids, so asking for
    fifty returns four — in fused order, not in either route's order, and with
    no placeholder, repetition or padding to reach the requested depth.
    """
    fused = reciprocal_rank_fusion(["A", "B", "C"], ["C", "A", "D"], top_k=50)

    assert fused == ["A", "C", "B", "D"]
    assert fused == reciprocal_rank_fusion(["A", "B", "C"], ["C", "A", "D"], top_k=4)


def test_m204_top_k_counts_over_the_union_and_can_exceed_either_route():
    """M2-04 — a fused result may be longer than either input.

    Two disjoint routes of three ids each yield six candidates, so a `top_k` of
    six is satisfiable even though neither route alone could satisfy it. `top_k`
    is a depth over the union, not over a route.
    """
    fused = reciprocal_rank_fusion(["A", "B", "C"], ["D", "E", "F"], top_k=6)

    assert len(fused) == 6
    assert len(fused) > len(["A", "B", "C"])


# ---------------------------------------------------------------------------
# determinism
# ---------------------------------------------------------------------------


def test_m204_repeated_identical_execution_produces_the_identical_ranking():
    """M2-04 — determinism is part of the contract, and is measured not asserted.

    Same inputs, same `k`, same `top_k`, same ordering rules → the same ids in
    the same order, every time. Nothing here consults a clock, a hash seed, an
    environment variable or a random source, and the fusion holds no state
    between calls.
    """
    semantic = ["A", "B", "C", "D"]
    lexical = ["C", "A", "E", "B"]

    runs = [reciprocal_rank_fusion(semantic, lexical, top_k=5) for _ in range(10)]

    assert len(set(map(tuple, runs))) == 1
    assert runs[0] == reciprocal_rank_fusion(list(semantic), list(lexical), top_k=5)


def test_m204_equal_rank_multisets_produce_bit_identical_scores():
    """M2-04 — why ranking on the exact score is safe, and rounding is not needed.

    Contributions are accumulated in a fixed route order, so two candidates
    carrying the same multiset of ranks compare **exactly** equal rather than
    nearly so. This is what lets the tie-break be a reachable, testable path
    without the rounding `sample_rag/retriever.py` needs for BM25, whose score
    accumulates over many terms and would otherwise hide real collisions.

    Asserted with `==` on floats deliberately — `pytest.approx` would pass on
    the near-miss this specification exists to rule out.
    """
    assert scores(["A"], ["B"])["A"] == scores(["A"], ["B"])["B"]
    assert scores(["A", "x"], ["y", "A"])["A"] == scores(["B", "y"], ["x", "B"])["B"]


def test_m204_the_fused_ranking_is_a_total_order_over_the_candidates():
    """M2-04 — no pair is left unordered, so no result depends on sort stability.

    Every candidate appears exactly once, and the ordering keys are distinct
    across the universe: with a covering ordering authority, `(score, position)`
    cannot collide because no two chunks share a corpus position.
    """
    semantic = ["A", "B", "C", "D"]
    lexical = ["D", "C", "B", "A"]
    order = ["A", "B", "C", "D"]

    fused = reciprocal_rank_fusion(semantic, lexical, top_k=99, order=order)

    assert sorted(fused) == sorted(set(semantic) | set(lexical))
    assert len(fused) == len(set(fused))


def test_m204_score_precision_is_a_reporting_constant_only():
    """M2-04 — `RRF_SCORE_PRECISION` describes output, and nothing ranks on it.

    Stated because the neighbouring `BM25_SCORE_PRECISION` *is* a ranking
    constant, and the two must not be assumed to mean the same thing.

    Demonstrated on a pair whose scores are genuinely different but **round
    equal** at the reporting precision: two adjacent deep ranks, where
    `1/(k+r) − 1/(k+r+1)` has fallen below `10 ** −RRF_SCORE_PRECISION`. The
    implementation still orders them strictly, which it could not do if it
    ranked on the rounded value. At the retrieval depths this repository
    actually uses the pair is unreachable — it takes ranks in the thousands to
    construct — which is precisely why rounding before ranking would buy
    nothing and could only manufacture ties.
    """
    assert isinstance(RRF_SCORE_PRECISION, int)

    route = [f"d{rank}" for rank in range(1, 2002)]
    measured = scores(route, [])

    near, farther = measured["d2000"], measured["d2001"]

    assert near != farther
    assert round(near, RRF_SCORE_PRECISION) == round(farther, RRF_SCORE_PRECISION)

    ranked = [chunk_id for chunk_id, _ in rank_candidates(route, [])]
    assert ranked.index("d2000") < ranked.index("d2001")
    assert ranked == route


# ---------------------------------------------------------------------------
# integration over the committed corpus
# ---------------------------------------------------------------------------


def test_m204_the_fused_route_returns_canonical_chunk_ids(real_chunks, real_chunks_by_id):
    """M2-04 — one identity in, one identity out.

    Every fused id is an existing `chunks[].id`. **No second chunk identity is
    introduced** — no `hybrid_chunk_id`, `fusion_id` or `retrieval_id` — which
    is what Sprint M2.03 was preparing when it verified that both routes
    already return the same identity *"so a later fusion sprint has one
    identity to fuse on rather than two"*.

    The lexical route is executed for real here; the semantic side is supplied
    as corpus ids so this specification stays about identity rather than about
    the embedding model, which
    `test_m204_the_committed_corpus_answers_a_fused_query` covers.
    """
    from sample_rag.retriever import Retriever

    retriever = Retriever(real_chunks)
    lexical = lexical_route(retriever, "quality engineering and test automation")
    semantic = [chunk["id"] for chunk in real_chunks[:5]]

    fused = fuse_routes(semantic, lexical, canonical_order(real_chunks, set()))

    assert fused
    assert all(chunk_id in real_chunks_by_id for chunk_id in fused)
    assert set(fused) <= set(semantic) | set(lexical)


def test_m204_the_committed_corpus_answers_a_fused_query(
    tmp_path, real_chunks, real_manifest_entries, real_chunks_by_id
):
    """M2-04 — the actual Milestone 2A pipeline, once, end to end.

    The committed Chunk Corpus, embedded by `BGEEmbeddingProvider` at the
    pinned revision and indexed by FAISS, fused with the real BM25 route over a
    real question. It is the specification that would catch an integration
    failure no synthetic pair of id lists could surface — a route returning an
    identity the other does not share, a mapping that resolves to nothing, an
    ordering authority that does not cover the corpus.

    Mirrors `tests/test_vector_query.py::test_m201c_the_committed_corpus_answers_a_semantic_query`,
    one layer up, and makes the same disclaimer: the assertions are about **the
    fused path**, not about answer quality. Whether fusion retrieves *better*
    evidence is measured by `scripts/compare_retrieval_routes.py` and reported
    in `docs/M2.04_RRF_Fusion_Report.md`; judging it belongs to Ragas
    (**M2-07**) and is not attempted here.
    """
    from sample_rag.embedding import BGEEmbeddingProvider
    from sample_rag.retriever import Retriever
    from sample_rag.vector_runtime import VectorIndexRuntime
    from scripts.run_hybrid_retrieval import execute, semantic_route

    canonical_ids = {entry["id"] for entry in real_manifest_entries if entry["canonical"]}
    retriever = Retriever(real_chunks, canonical_ids)
    runtime = VectorIndexRuntime(
        real_chunks, real_manifest_entries, BGEEmbeddingProvider(), tmp_path
    )
    order = canonical_order(real_chunks, canonical_ids)

    question = "What test automation frameworks has the candidate used?"
    semantic = semantic_route(runtime, question)
    lexical = lexical_route(retriever, question)
    fused = fuse_routes(semantic, lexical, order)

    assert len(semantic) == ROUTE_TOP_K
    assert len(fused) == ROUTE_TOP_K
    assert all(chunk_id in real_chunks_by_id for chunk_id in fused)
    assert set(fused) <= set(semantic) | set(lexical)

    executed = execute(retriever, runtime, [("entry", question)], order)
    assert executed[0][1][FUSED_ROUTE] == fused
    assert executed[0][1][SEMANTIC_ROUTE] == semantic
    assert executed[0][1][LEXICAL_ROUTE] == lexical


def test_m204_fusing_the_same_query_twice_returns_the_same_fused_order(
    tmp_path, real_chunks, real_manifest_entries
):
    """M2-04 — end-to-end determinism over the committed corpus.

    Two independent runtimes over two independent index directories, the same
    question, the same fused ids in the same order. Nothing is cached to
    produce this: the runtimes share no state and each resolves its artifact in
    full.
    """
    from sample_rag.embedding import BGEEmbeddingProvider
    from sample_rag.retriever import Retriever
    from scripts.run_hybrid_retrieval import semantic_route
    from sample_rag.vector_runtime import VectorIndexRuntime

    canonical_ids = {entry["id"] for entry in real_manifest_entries if entry["canonical"]}
    order = canonical_order(real_chunks, canonical_ids)
    provider = BGEEmbeddingProvider()
    question = "how did the candidate improve release quality"

    fused = []
    for directory in ("first", "second"):
        runtime = VectorIndexRuntime(
            real_chunks, real_manifest_entries, provider, tmp_path / directory
        )
        retriever = Retriever(real_chunks, canonical_ids)
        fused.append(
            fuse_routes(
                semantic_route(runtime, question), lexical_route(retriever, question), order
            )
        )

    assert fused[0] == fused[1]


def test_m204_fusion_does_not_alter_either_route(real_chunks):
    """M2-04 — the routes are consumed, not modified.

    The id lists handed to fusion are unchanged afterwards, and each route
    returns exactly what it returns when fusion is not involved at all. M2-04
    is a consumer layer; a route whose output depended on whether it was later
    fused would not be independently callable, which
    `docs/DEFERRED_ITEMS_REGISTER.md` records that both routes are.
    """
    from sample_rag.retriever import Retriever

    retriever = Retriever(real_chunks)
    question = "python data pipelines"

    before = lexical_route(retriever, question)
    semantic = [chunk["id"] for chunk in real_chunks[:5]]
    semantic_copy = list(semantic)

    fuse_routes(semantic, before, canonical_order(real_chunks, set()))

    assert semantic == semantic_copy
    assert before == lexical_route(retriever, question)


def test_m204_the_route_depth_is_the_repositorys_existing_default(real_chunks):
    """M2-04 — `top_k` is held equal across all three routes, and is not a new value.

    `evaluation/retrieval_metrics.py` defines K as the **observed retrieval
    size**, so measuring one route at depth 5 against another at depth 20 would
    compare two different metrics under one name. `ROUTE_TOP_K` is
    `sample_rag/retriever.py`'s own `DEFAULT_TOP_K`, restated rather than
    re-chosen, and searching over it is retrieval-quality optimization
    (**M2-15**).
    """
    assert ROUTE_TOP_K == DEFAULT_TOP_K == 5


# ---------------------------------------------------------------------------
# the sprint boundary
# ---------------------------------------------------------------------------


def test_m204_the_fusion_primitive_depends_on_nothing_at_all():
    """M2-04 — the smallest seam the repository permits, enforced structurally.

    `sample_rag/fusion.py` imports **nothing**: not the lexical route, not the
    semantic route, not FAISS, not the embedding library, not `scripts/`, not
    even the standard library. That shape was not chosen for elegance — it is
    what `tests/test_lexical_bm25.py::test_m203_the_semantic_route_is_untouched_by_the_lexical_one`
    requires, since it allows exactly one borrower of the lexical route and it
    is `generator.py`.

    A fusion module that reached into either route could re-parameterize it.
    This one cannot reach anything, so M2-04 is structurally a consumer rather
    than a repair layer, and criterion **A-5**'s two standing exceptions —
    `sentence_transformers` in `sample_rag/embedding.py` and `faiss` in
    `sample_rag/vector_index.py` — did not widen.
    """
    import sample_rag.fusion as module

    assert imported_roots(module) == set()
    assert imported_modules(module) == set()


def test_m204_the_fusion_primitive_declares_no_later_capability():
    """M2-04 — the sprint boundary as an AST allowlist, not as prose.

    The mirror of `tests/test_lexical_bm25.py`'s and `tests/test_vector_query.py`'s
    boundary specifications, now guarding the layer above both. **M2-05**
    reranking, query rewriting and expansion, **M2-06** generation, the
    Milestone 2B SQL/JobOps branch, learned or weighted fusion, score
    normalization and caching are all absent, and a helper added later fails
    here rather than passing unnoticed.

    Stated over declared names — functions, classes, assignments and arguments
    — rather than over raw source text, so a module may legitimately *mention*
    a later capability in a comment to explain why it is absent, which this one
    does throughout.
    """
    import sample_rag.fusion as module

    declared = declared_names(module)

    for barred in (
        "bm25",
        "sql",
        "jobops",
        "structured",
        "rerank",
        "reranking",
        "expand_query",
        "rewrite_query",
        "query_expansion",
        "normalize_scores",
        "normalize",
        "weight",
        "learned",
        "boost",
        "embed",
        "generate",
        "cache",
        "faiss",
        "timestamp",
        "freshness",
        "ragas",
        "deepeval",
        "promptfoo",
        "deepseek",
    ):
        offenders = [name for name in declared if barred in name.lower()]
        assert offenders == [], f"{barred} is out of scope for Sprint M2.04: {offenders}"


def test_m204_fusion_takes_exactly_two_routes():
    """M2-04 — two-route fusion, structurally, so 2B cannot arrive by accident.

    The Milestone 2A activation fuses the semantic and lexical routes; the
    structured SQL branch is Milestone 2B (`docs/roadmap.md` §1.1), and no
    JobOps corpus is connected. The signature takes two **named** routes rather
    than a variadic list, so a third route cannot be added by passing one more
    argument — it requires editing the signature, which fails this
    specification.

    `*args` and `**kwargs` are barred for the same reason: either would make
    the arity a runtime property instead of a declared one.
    """
    for function in (reciprocal_rank_fusion, rank_candidates):
        parameters = inspect.signature(function).parameters

        assert [
            name
            for name, parameter in parameters.items()
            if parameter.kind is not parameter.VAR_KEYWORD
        ][:2] == ["semantic_ids", "lexical_ids"]
        assert not any(
            parameter.kind in (parameter.VAR_POSITIONAL, parameter.VAR_KEYWORD)
            for parameter in parameters.values()
        )

    assert list(inspect.signature(reciprocal_rank_fusion).parameters) == [
        "semantic_ids",
        "lexical_ids",
        "k",
        "top_k",
        "order",
    ]


def test_m204_neither_retrieval_route_imports_the_fusion_layer():
    """M2-04 — fusion sits above the routes, and the dependency points one way.

    Stated over the package by glob, mirroring
    `tests/test_vector_index.py::test_m201b_no_other_pipeline_module_imports_faiss`,
    so a module added later is covered without anyone remembering to add it. If
    a route imported the fusion layer, the two routes would be transitively
    connected and neither would remain independently callable — the property
    `docs/DEFERRED_ITEMS_REGISTER.md` records for both, and the property this
    sprint had to preserve to be a consumer rather than a redesign.
    """
    import sample_rag.fusion

    package_root = pathlib.Path(sample_rag.fusion.__file__).parent

    borrowers = []
    for path in sorted(package_root.glob("*.py")):
        if path.name == "fusion.py":
            continue

        module = importlib.import_module(f"sample_rag.{path.stem}")
        if "sample_rag.fusion" in imported_modules(module):
            borrowers.append(path.name)

    assert borrowers == [], f"the fusion layer is imported by a retrieval route: {borrowers}"


def test_m204_the_sprints_orchestrators_reach_no_later_capability():
    """M2-04 — the composition points import the two routes and nothing beyond them.

    `scripts/run_hybrid_retrieval.py` and `scripts/compare_retrieval_routes.py`
    are where the routes meet, so they are where a later capability would most
    plausibly creep in. Neither reaches an LLM SDK, an evaluation framework, a
    database driver or an HTTP client, and the comparison script reaches the
    evaluation engines **without editing them** — `evaluation/retrieval_evaluation.py`
    and `evaluation/retrieval_metrics.py` are consumed exactly as Sprints
    P3.3.2 and P3.3.3 left them.
    """
    import scripts.compare_retrieval_routes as comparison
    import scripts.run_hybrid_retrieval as orchestrator

    for module in (orchestrator, comparison):
        roots = imported_roots(module)

        assert roots <= {"time", "sample_rag", "scripts", "evaluation"}
        for barred in (
            "sqlite3",
            "faiss",
            "sentence_transformers",
            "torch",
            "requests",
            "httpx",
            "openai",
            "ragas",
            "deepeval",
            "promptfoo",
        ):
            assert barred not in roots, f"{barred} is out of scope for Sprint M2.04"


def test_m204_the_evaluation_engines_were_not_edited_for_this_sprint():
    """M2-04 — the benchmark measures the routes; the routes did not adjust the benchmark.

    `evaluation/retrieval_metrics.py`'s own docstring predicted this sprint:
    *"a future BM25, vector, or hybrid retriever [can] be measured without
    touching this file — a new retriever changes what the records say, not what
    a record is."* This specification holds the engines to it, by requiring
    that they still import nothing that could reach a retrieval route or a
    repository artifact.

    It is what makes the M2.03-F-1 comparison credible: three routes measured
    by one unmodified instrument, which cannot tell which route produced the
    ids it is handed.
    """
    import evaluation.retrieval_evaluation as evaluation_engine
    import evaluation.retrieval_metrics as metrics_engine

    assert imported_roots(evaluation_engine) == {"collections"}
    assert imported_roots(metrics_engine) == {"math", "collections"}

    for engine in (evaluation_engine, metrics_engine):
        assert "sample_rag" not in imported_roots(engine)
        assert "scripts" not in imported_roots(engine)
