"""Deterministic lexical Retrieval Runtime.

Sprint P3.3.1: implements the `Retriever` pipeline component
(docs/architecture.md §5) returning the `RetrievalResult` contract frozen by
docs/MILESTONE_1A.md build item 4 and Architectural AC2. This is the
repository's first executable retrieval behavior — it produces *observed*
runtime output only, and expresses no judgement about correctness.

Read-only, and structurally so: `Retriever` is constructed over an
already-loaded chunk collection and performs no filesystem or network I/O at
all, so no retrieval path can reach a repository artifact to modify it. Loading
the committed Chunk Corpus is the caller's responsibility
(`scripts/run_retrieval.py`), which also keeps `sample_rag/` free of any import
from `scripts/` — the direction docs/architecture.md §6 bars, and the same
constraint that already keeps `SUPPORTED_EXTENSIONS` duplicated between
`knowledge_source.py` and `build_manifest.py`
(docs/ENGINEERING_TRACEABILITY_REGISTER.md AH-9).

Retrieval path implemented here, reflecting the current resume-only corpus:

    query -> lexical retrieval -> RetrievalResult

The optional SQL-filter stage that precedes lexical retrieval in the Milestone
1A architecture is not exercised: it filters JobOps-derived structured metadata
(docs/roadmap.md §4), and the corpus contains no such data. Not exercising it
reflects the corpus, and changes no architecture. BM25, embeddings, vector,
hybrid, and reranking are Milestone 2 (docs/MILESTONE_1A.md §174) and are
deliberately absent — the scoring below is plain distinct-term overlap, not a
weighted or saturating ranking function.
"""

import re

from dataclasses import dataclass

# Construction values, not Contract fields. `retrieve()` reads `top_k` from its
# own `filters` argument so the frozen `retrieve(query, filters)` signature is
# preserved exactly rather than grown a third parameter.
DEFAULT_TOP_K = 5
LEXICAL_ROUTE = "LEXICAL"

# Deterministic placeholder values, per docs/MILESTONE_1A.md build item 4's own
# worked example and Architectural AC2 ("deterministic, meaningful placeholder
# values in every field"). `retrieval_time_ms` is fixed at 0 rather than
# measured: a real duration would make repeated runs differ, breaking the
# determinism this sprint exists to demonstrate.
PLACEHOLDER_RETRIEVAL_TIME_MS = 0
EMPTY_RESULT_SCORE = 0.0

_TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


@dataclass(frozen=True)
class RetrievalResult:
    """The four fields frozen by docs/MILESTONE_1A.md build item 4 — no more, no less.

    Field order matches that section's worked example. Every field carries a
    deterministic, meaningful value on every path, including the no-match path
    (Architectural AC2); none is ever `None`.

    `diagnostics` is the contract's own open mapping, and is where this sprint's
    per-query runtime detail lives — `query`, `retrieved_chunk_ids`,
    `document_ids`, per-chunk `scores`, and `ranking`. Carrying them there
    rather than as new top-level fields is what keeps the frozen four-field
    contract unredesigned while still recording everything the runtime observed
    (see the module note in `retrieve`).
    """

    chunks: list
    retrieval_route: str
    score: float
    diagnostics: dict


def tokenize(text: str) -> list[str]:
    """Split text into lowercase alphanumeric terms, in reading order.

    A fixed, total function of its input — no locale, clock, or environment
    participates — which is what makes scoring reproducible across runs and
    machines.
    """
    return _TOKEN_PATTERN.findall(text.lower())


def score_chunk(query_terms: set, chunk_text: str) -> tuple[int, list[str]]:
    """Score one chunk by distinct query-term overlap.

    Deliberately the simplest defensible lexical signal: how many of the query's
    distinct terms appear in the chunk, with no term weighting, no inverse
    document frequency, and no length normalization — none of which may be
    introduced before Milestone 2 (docs/MILESTONE_1A.md §174). Returns the raw
    overlap count and the matched terms, sorted so the diagnostic record is
    itself deterministic.
    """
    chunk_terms = set(tokenize(chunk_text))
    matched = sorted(query_terms & chunk_terms)
    return len(matched), matched


class Retriever:
    """Returns ranked evidence for a query, over a fixed chunk collection.

    docs/architecture.md §5: `Retriever.retrieve(query, filters)`. That table's
    return type still reads `List[Chunk]`; docs/MILESTONE_1A.md build item 4
    supersedes it explicitly — "not a bare `List[Chunk]`" — and is the contract
    implemented here.

    Pure with respect to the repository: no filesystem I/O, no network I/O, no
    mutation of the collection it was given, and no shared mutable state between
    calls.
    """

    def __init__(self, chunks: list):
        """Bind the retriever to an already-loaded, already-validated chunk collection.

        The collection is copied into a private list so that later mutation by a
        caller cannot change what this retriever sees, and so the retriever
        itself has nothing to write back to. Corpus order is preserved exactly
        as committed — it is the tie-break authority used by `rank_candidates`.
        """
        self._chunks = list(chunks)

    def rank_candidates(self, query_terms: set) -> list[tuple]:
        """Score every chunk and order the matches deterministically.

        Ordering is descending score, then ascending committed corpus position.
        The positional tie-break matters: overlap counts collide often on a
        corpus this size, and without it equal-scoring chunks would be ordered
        by whatever `sorted` happened to see first. Anchoring ties to the Chunk
        Corpus's own persisted order — Knowledge Manifest document order, then
        `chunk_index` (Sprint P3.2.2) — makes ranking a property of the
        committed corpus rather than of this function's iteration.

        Chunks with zero overlap are not candidates: retrieving them would be
        recording a match the query has no lexical basis for.
        """
        candidates = []
        for position, chunk in enumerate(self._chunks):
            overlap, matched = score_chunk(query_terms, chunk["text"])
            if overlap:
                candidates.append((overlap, position, chunk, matched))

        candidates.sort(key=lambda candidate: (-candidate[0], candidate[1]))
        return candidates

    def retrieve(self, query: str, filters: dict) -> RetrievalResult:
        """Execute lexical retrieval for one query.

        `filters` is the frozen interface's filter mapping. Only `top_k` is
        honored in this sprint; the SQL-filter stage that would consume the
        remaining keys is not exercised (see module docstring), so any other key
        is reported in `diagnostics["filters_ignored"]` rather than silently
        dropped — an unapplied filter should be visible in the runtime record,
        not invisible.

        Scores are normalized to the fraction of the query's distinct terms a
        chunk matched, so a score is comparable across queries of different
        lengths. The result-level `score` is the top-ranked chunk's normalized
        score, and `EMPTY_RESULT_SCORE` when nothing matched — a deterministic,
        meaningful value on both paths, never `None` (Architectural AC2).

        Returns observed behavior only. Nothing here consults the Evidence Trace
        Dataset, and nothing here expresses whether the retrieval was correct;
        that comparison is Sprint P3.3.2's.
        """
        filters = filters or {}
        top_k = filters.get("top_k", DEFAULT_TOP_K)
        ignored = sorted(key for key in filters if key != "top_k")

        query_terms = set(tokenize(query))
        matched = self.rank_candidates(query_terms)
        candidates = matched[:top_k]

        chunks = [chunk for _, _, chunk, _ in candidates]
        denominator = len(query_terms) or 1
        scores = [round(overlap / denominator, 6) for overlap, _, _, _ in candidates]

        diagnostics = {
            "query": query,
            "query_terms": sorted(query_terms),
            "retrieved_chunk_ids": [chunk["id"] for chunk in chunks],
            "document_ids": [chunk["document_id"] for chunk in chunks],
            "scores": scores,
            "ranking": list(range(1, len(chunks) + 1)),
            "matched_terms": [matched for _, _, _, matched in candidates],
            "retrieval_method": LEXICAL_ROUTE,
            "top_k": top_k,
            "candidates_matched": len(matched),
            "corpus_size": len(self._chunks),
            "sql_filter_applied": False,
            "filters_ignored": ignored,
            "retrieval_time_ms": PLACEHOLDER_RETRIEVAL_TIME_MS,
            "stub": True,
        }

        return RetrievalResult(
            chunks=chunks,
            retrieval_route=LEXICAL_ROUTE,
            score=scores[0] if scores else EMPTY_RESULT_SCORE,
            diagnostics=diagnostics,
        )
