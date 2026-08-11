"""Two-route hybrid Retrieval Runtime execution against the committed corpus.

Sprint M2.04: the thin orchestrator that composes the repository's two
independently validated retrieval routes and fuses them with Reciprocal Rank
Fusion. It plays the same operational-tooling role `scripts/run_retrieval.py`
plays for the lexical route alone, and **holds no fusion logic of its own** —
every rank, score and ordering rule lives in `sample_rag/fusion.py`.

    Evidence Trace question
              |
              +-----------------------------+
              |                             |
              v                             v
    VectorIndexRuntime.query_text     Retriever.retrieve
    (BGE -> FAISS)                    (BM25)
              |                             |
              v                             v
      ranked chunk ids              ranked chunk ids
              |                             |
              +--------------+--------------+
                             |
                             v
             sample_rag.fusion.reciprocal_rank_fusion
                             |
                             v
                   fused ranked chunk ids

**This module is where the two routes meet, and it is the only place they do.**
`sample_rag/fusion.py` imports neither of them, and neither imports the other —
`tests/test_lexical_bm25.py::test_m203_the_semantic_route_is_untouched_by_the_lexical_one`
and `tests/test_vector_query.py::test_m201c_the_query_path_exposes_no_fusion_or_lexical_surface`
keep both facts structural. Composing them in `scripts/` rather than inside
`sample_rag/` is what preserves that: `docs/architecture.md` §6 bars
`sample_rag/` from importing `scripts/`, and this direction is the permitted
one, already taken by `scripts/run_retrieval.py` and
`scripts/evaluate_retrieval.py`.

**Neither route is modified, re-parameterized or re-implemented here.** The
BM25 statistics, `k1`, `b`, the tokenization contract, the FAISS index, its
identity, the rebuild lifecycle and the embedding provider are all reached
through their existing public entry points and are used exactly as they stand.
This sprint is a consumer, not a repair.

Strictly read-only with respect to repository source: this module loads
committed artifacts and writes none. `VectorIndexRuntime` may write the
**derived** FAISS artifact under `VECTOR_INDEX_ROOT` if none is present or the
persisted one no longer identifies the corpus, which is that module's own RO-09
lifecycle and not an artifact this sprint introduces — the directory is
`.gitignore`d runtime state and the canonical corpus remains the source of
truth. No observed-retrieval artifact is persisted, per the decision
`scripts/run_retrieval.py` recorded at Sprint P3.3.1.

The Evidence Trace Dataset is read here **only** as the repository's list of
questions, exactly as `scripts/run_retrieval.py` reads it. No expectation field
is consulted; comparing observed against expected retrieval is
`scripts/compare_retrieval_routes.py`'s responsibility.
"""

import time

from sample_rag.fusion import DEFAULT_TOP_K, RRF_K, reciprocal_rank_fusion
from sample_rag.retriever import Retriever
from sample_rag.vector_runtime import VectorIndexRuntime
from scripts.build_manifest import load_manifest, validate_manifest
from scripts.run_retrieval import load_canonical_documents, load_corpus, load_questions

# Retrieval depth, held equal for both input routes and for the fused output.
# **An engineering decision of this sprint, and the one that makes the routes
# comparable at all**: `evaluation/retrieval_metrics.py` defines K as the
# observed retrieval size, so measuring one route at depth 5 against another at
# depth 20 would compare two different metrics. It is the repository's existing
# `DEFAULT_TOP_K`, not a value chosen for this sprint, and it is not varied —
# searching over candidate-pool depth is retrieval-quality optimization
# (**M2-15**), which `docs/roadmap.md` §1.1 places at Milestone 2C.
ROUTE_TOP_K = DEFAULT_TOP_K

SEMANTIC_ROUTE = "SEMANTIC"
LEXICAL_ROUTE = "LEXICAL"
FUSED_ROUTE = "RRF"


def load_documents() -> list:
    """Read the Knowledge Manifest's `documents[]`, for the vector runtime.

    Through `validate_manifest(load_manifest())` — the chained gate
    `docs/CHUNK_VALIDATION_PLAN.md` §P7.1 prescribes and every other consumer
    uses — so the manifest reaches `VectorIndexRuntime` the same way it reaches
    `scripts/build_chunks.py`, and no two consumers can disagree about what the
    corpus declares.
    """
    return list(validate_manifest(load_manifest())["documents"])


def canonical_order(chunks: list, canonical_document_ids: set) -> list:
    """Return every corpus chunk id in the repository's canonical tie-break order.

    Sprint P3.7.5's ordering rule below the score — **canonical documents ahead
    of superseded ones, then committed corpus position** — materialized as a
    single sequence, which is the form `sample_rag.fusion.rank_candidates` can
    consume without learning what a document or a manifest is.

    The two levels compose into one total order because the second already is
    one: no two chunks share a committed corpus position. Expressing them as a
    sequence rather than as a comparator is what keeps the fusion primitive a
    pure function of ranked id lists, with the corpus knowledge held here,
    where the corpus is already loaded.

    `sorted` is stable, so ranking only on the canonical designation preserves
    committed corpus position within each group — the positional level is
    inherited rather than restated, and cannot drift from the enumeration it
    describes.
    """
    return [
        chunk["id"]
        for chunk in sorted(
            chunks,
            key=lambda chunk: 0 if chunk["document_id"] in canonical_document_ids else 1,
        )
    ]


def semantic_route(runtime: VectorIndexRuntime, question: str, top_k: int = ROUTE_TOP_K) -> list:
    """Ranked chunk ids from the semantic route, unmodified.

    `VectorIndexRuntime.query_text` is called exactly as Sprint M2.01C left it:
    the same provider embeds query and corpus, no query prefix or instruction
    is applied, and nothing here re-orders, weights, normalizes or filters what
    FAISS returned. This function exists to name the route, not to adjust it.
    """
    return list(runtime.query_text(question, top_k))


def lexical_route(retriever: Retriever, question: str, top_k: int = ROUTE_TOP_K) -> list:
    """Ranked chunk ids from the lexical route, unmodified.

    `Retriever.retrieve(query, filters)` through its frozen signature, reading
    the ranked ids the runtime already records. `diagnostics["retrieved_chunk_ids"]`
    is the same list `scripts/evaluate_retrieval.py` observes, so the lexical
    input to fusion is byte-for-byte the lexical route the repository already
    measures — not a second derivation of it.
    """
    result = retriever.retrieve(question, {"top_k": top_k})

    return list(result.diagnostics["retrieved_chunk_ids"])


def fuse_routes(semantic_ids: list, lexical_ids: list, order: list, top_k: int = ROUTE_TOP_K) -> list:
    """Fuse one question's two ranked id lists.

    Delegated wholly to `sample_rag.fusion.reciprocal_rank_fusion`. The only
    thing this layer contributes is the canonical ordering authority, which is
    a property of the corpus rather than of the fusion arithmetic.
    """
    return reciprocal_rank_fusion(semantic_ids, lexical_ids, RRF_K, top_k, order)


def execute(retriever: Retriever, runtime: VectorIndexRuntime, questions: list, order: list) -> list:
    """Execute both routes and their fusion for every question, in order.

    Returns `(entry_id, {route -> ranked chunk ids})` pairs, carrying all three
    routes rather than the fused one alone: the sprint must be able to say what
    each route contributed, and re-running a route separately to find out would
    let two executions of the same query disagree.

    Each question is independent — neither the retriever nor the runtime
    carries state between queries — so the sequence is reproducible and any
    single question can be re-run in isolation and produce the same result.
    """
    executed = []
    for entry_id, question in questions:
        semantic = semantic_route(runtime, question)
        lexical = lexical_route(retriever, question)
        executed.append(
            (
                entry_id,
                {
                    SEMANTIC_ROUTE: semantic,
                    LEXICAL_ROUTE: lexical,
                    FUSED_ROUTE: fuse_routes(semantic, lexical, order),
                },
            )
        )

    return executed


def measure(retriever: Retriever, runtime: VectorIndexRuntime, questions: list, order: list) -> dict:
    """Time each stage separately, over the whole question set.

    Reported rather than assumed. The point of separating the three timings is
    that the fusion arithmetic and the retrieval it fuses are expected to differ
    by orders of magnitude, and an end-to-end figure alone would not show
    whether that held.

    **Nothing is cached, batched, warmed or otherwise optimized to improve
    these numbers.** The index is resolved before timing begins, so the
    measurement covers query execution rather than the one-time RO-09 lifecycle
    — a rebuild embeds the whole corpus and would otherwise be attributed to
    the first query. That resolution cost is reported separately by `main`.
    """
    timings: dict = {}

    for route, call in (
        (SEMANTIC_ROUTE, lambda question: semantic_route(runtime, question)),
        (LEXICAL_ROUTE, lambda question: lexical_route(retriever, question)),
    ):
        started = time.perf_counter()
        for _, question in questions:
            call(question)
        timings[route] = time.perf_counter() - started

    executed = [
        (semantic_route(runtime, question), lexical_route(retriever, question))
        for _, question in questions
    ]

    started = time.perf_counter()
    for semantic, lexical in executed:
        fuse_routes(semantic, lexical, order)
    timings[FUSED_ROUTE] = time.perf_counter() - started

    started = time.perf_counter()
    for _, question in questions:
        fuse_routes(semantic_route(runtime, question), lexical_route(retriever, question), order)
    timings["END_TO_END"] = time.perf_counter() - started

    count = len(questions)

    return {
        route: {
            "total_ms": round(elapsed * 1000, 3),
            "per_query_ms": round(elapsed * 1000 / count, 3) if count else 0.0,
        }
        for route, elapsed in timings.items()
    }


def summarize(executed: list, route: str, corpus_size: int) -> dict:
    """Describe one route's observed retrieval across an execution.

    The statistics `scripts/run_retrieval.py` `summarize` reports, restricted to
    those computable from chunk ids alone — this layer observes ranked ids, not
    chunk mappings. Descriptive only: no expectation is read, so no statistic
    here can express correctness.
    """
    counts = [len(routes[route]) for _, routes in executed]
    chunk_ids = [chunk_id for _, routes in executed for chunk_id in routes[route]]
    unique = set(chunk_ids)

    return {
        "questions_executed": len(executed),
        "chunks_retrieved": len(chunk_ids),
        "unique_chunks_retrieved": len(unique),
        "average_top_k": round(sum(counts) / len(counts), 2) if executed else 0.0,
        "empty_results": sum(1 for count in counts if count == 0),
        "chunk_reuse": round(len(chunk_ids) / len(unique), 2) if unique else 0.0,
        "corpus_utilization": round(len(unique) / corpus_size, 4) if corpus_size else 0.0,
    }


def route_agreement(executed: list) -> dict:
    """How much the fused result owes to each route, and how much they overlap.

    Not a quality measurement and not presented as one — it describes where the
    fused ids came from, which is what distinguishes "RRF worked" from "RRF
    returned one route's output under a new name".
    """
    shared, from_semantic, from_lexical = [], [], []
    for _, routes in executed:
        semantic = set(routes[SEMANTIC_ROUTE])
        lexical = set(routes[LEXICAL_ROUTE])
        fused = set(routes[FUSED_ROUTE])

        shared.append(len(semantic & lexical))
        from_semantic.append(len(fused & semantic))
        from_lexical.append(len(fused & lexical))

    count = len(executed) or 1

    return {
        "candidate_union_mean": round(
            sum(len(set(routes[SEMANTIC_ROUTE]) | set(routes[LEXICAL_ROUTE])) for _, routes in executed) / count,
            2,
        ),
        "route_overlap_mean": round(sum(shared) / count, 2),
        "questions_with_route_overlap": sum(1 for value in shared if value),
        "fused_from_semantic_mean": round(sum(from_semantic) / count, 2),
        "fused_from_lexical_mean": round(sum(from_lexical) / count, 2),
    }


def report(executed: list, corpus_size: int, timings: dict, resolution_ms: float) -> None:
    """Print per-route observed characteristics, route agreement and timings."""
    for route in (SEMANTIC_ROUTE, LEXICAL_ROUTE, FUSED_ROUTE):
        print(f"\n{route} route — observed retrieval")
        for name, value in summarize(executed, route, corpus_size).items():
            print(f"  {name:<28} {value}")

    print("\nRoute agreement")
    for name, value in route_agreement(executed).items():
        print(f"  {name:<28} {value}")

    print("\nPerformance")
    print(f"  {'index resolution (once)':<28} {round(resolution_ms, 3)} ms")
    for route, values in timings.items():
        print(f"  {route:<28} {values['total_ms']} ms total   {values['per_query_ms']} ms/query")


def main() -> None:
    """Execute the two-route hybrid Retrieval Runtime and report what it did."""
    chunks = load_corpus()
    canonical_ids = load_canonical_documents()
    questions = load_questions()
    order = canonical_order(chunks, canonical_ids)

    retriever = Retriever(chunks, canonical_ids)
    runtime = VectorIndexRuntime(chunks, load_documents())

    started = time.perf_counter()
    runtime.index()
    resolution_ms = (time.perf_counter() - started) * 1000

    executed = execute(retriever, runtime, questions, order)
    timings = measure(retriever, runtime, questions, order)

    print(f"vector index disposition     {runtime.disposition}")
    print(f"RRF k                        {RRF_K}")
    print(f"route top_k                  {ROUTE_TOP_K}")
    report(executed, len(chunks), timings, resolution_ms)


if __name__ == "__main__":
    main()
