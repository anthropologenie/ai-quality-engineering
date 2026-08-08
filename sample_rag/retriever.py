"""Deterministic lexical Retrieval Runtime — BM25 ranking.

Sprint P3.3.1: implements the `Retriever` pipeline component
(docs/architecture.md §5) returning the `RetrievalResult` contract frozen by
docs/MILESTONE_1A.md build item 4 and Architectural AC2. This is the
repository's first executable retrieval behavior — it produces *observed*
runtime output only, and expresses no judgement about correctness.

Sprint M2.03: replaces the distinct-term-overlap scorer with genuine **BM25**,
register capability **M2-03** — *"a ranking function replacing plain
distinct-term overlap"* (docs/DEFERRED_ITEMS_REGISTER.md §4). The seam is
unchanged: the same module, the same `retrieve(query, filters) -> RetrievalResult`
contract, the same `tokenize` contract, the same canonical chunk identity, and
the same three-level deterministic ordering. **No lexical Protocol was
introduced**, because no repository authority defines one — docs/architecture.md
§5 names one retrieval component and §7's Protocol sketch declares no lexical
seam beside `Retriever`. `BM25Statistics` below is a data structure holding
corpus statistics, not an injectable interface: nothing constructs a `Retriever`
around an alternative one, and no caller can substitute one.

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

    query -> BM25 lexical retrieval -> RetrievalResult

The optional SQL-filter stage that precedes lexical retrieval in the Milestone
1A architecture is not exercised: it filters JobOps-derived structured metadata
(docs/roadmap.md §4), and the corpus contains no such data. Not exercising it
reflects the corpus, and changes no architecture.

What this module is still deliberately *not*
---------------------------------------------
**This is the lexical route alone.** BM25 is a lexical ranking function: it
scores term occurrence, weighted by rarity and saturated against document
length. It has no notion of meaning, so a query that shares no term with a
chunk scores nothing here however close the two are semantically. The semantic
route (`sample_rag/vector_runtime.py`, **M2-01**/**M2-02**) is what carries
meaning, and the two are **not** combined by this module. Reciprocal Rank
Fusion and hybrid ranking (**M2-04**), reranking (**M2-05**), query rewriting
or expansion, and generation (**M2-06**) are later capabilities and are absent:
this module imports nothing from the vector route, reads no embedding, and
emits no fused score. What it establishes for M2-04 is that the lexical route
returns the repository's **canonical chunk ids** — `chunks[].id`, the same
identity `VectorStore.query(vector, top_k) -> list[str]` returns — so a later
fusion sprint has one identity to fuse on rather than two.

The BM25 contract
------------------
Documented here because no repository authority states it; the parameter values
and the IDF variant below are **engineering decisions of this sprint**, recorded
in `docs/M2.03_Real_BM25_Lexical_Retrieval_Report.md`, not Repository Owner
authority.

    score(q, d) = Σ           idf(t) · ────────── tf(t,d) · (k1 + 1) ──────────
                  t ∈ q                tf(t,d) + k1 · (1 − b + b · |d| / avgdl)

    idf(t) = ln( 1 + (N − df(t) + 0.5) / (df(t) + 0.5) )

where `t` ranges over the query's terms **with multiplicity**, `tf(t,d)` is the
number of occurrences of `t` in chunk `d`, `df(t)` the number of chunks
containing `t`, `N` the chunk count, `|d|` the chunk's token count, and `avgdl`
the mean token count over the corpus.
"""

import math
import re

from collections import Counter
from dataclasses import dataclass, field

# Construction values, not Contract fields. `retrieve()` reads `top_k` from its
# own `filters` argument so the frozen `retrieve(query, filters)` signature is
# preserved exactly rather than grown a third parameter.
DEFAULT_TOP_K = 5
LEXICAL_ROUTE = "LEXICAL"

# BM25 parameters. **Engineering decision, not repository authority** — no
# committed authority in this repository states a value for either, which
# Sprint M2.03's Phase 0 discovery verified by inspection. These are the
# conventional defaults of the Okapi BM25 literature (Robertson & Zaragoza,
# *The Probabilistic Relevance Framework*, §3.3) and of Lucene's own
# `BM25Similarity`, so the ranking this module produces is the one a reader who
# knows BM25 expects, and any future retuning is a visible change to a named
# constant rather than a rediscovery of what the code meant.
#
#   k1 — term-frequency saturation. Higher values let repeated occurrences keep
#        contributing; k1 = 0 would reduce BM25 to presence-only weighting.
#   b  — length normalization. b = 1 normalizes fully by document length,
#        b = 0 not at all.
BM25_K1 = 1.2
BM25_B = 0.75

# Scores are rounded to this many decimal places, and **ranked on the rounded
# value**. Two reasons, both about determinism rather than presentation: the
# ranked order is then explained by the very numbers `diagnostics["scores"]`
# records, and the tie-break below becomes a reachable, testable path rather
# than a theoretical one that float noise would hide.
BM25_SCORE_PRECISION = 6

# Deterministic placeholder values, per docs/MILESTONE_1A.md build item 4's own
# worked example and Architectural AC2 ("deterministic, meaningful placeholder
# values in every field"). `retrieval_time_ms` is fixed at 0 rather than
# measured: a real duration would make repeated runs differ, breaking the
# determinism this sprint exists to demonstrate.
PLACEHOLDER_RETRIEVAL_TIME_MS = 0
EMPTY_RESULT_SCORE = 0.0

# docs/MILESTONE_1A.md build item 4 froze `diagnostics["stub"]` as a *marker* —
# placeholder values exist so the suite can assert semantics now, so that
# "Milestone 2 swaps values inside an already-correct shape rather than changing
# the shape itself". Sprint M2.03 is that swap for the lexical route, and the
# marker reports it: the ranking function is real. The precedent is
# `Indexer.index(...).stub`, which Sprint M2.01A flipped `True -> False` for
# **M2-01** on exactly this reasoning (`tests/test_indexer.py`
# `test_1b03_the_index_declares_what_kind_of_vectors_it_holds`). The route is
# still not the *hybrid* retrieval docs/architecture.md §9 places at Milestone 2
# — that is **M2-04**, and `diagnostics["sql_filter_applied"]` continues to
# report the unexercised structured branch separately.
LEXICAL_STUB = False

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

    **The tokenization/normalization contract, unchanged by Sprint M2.03**, and
    unchanged deliberately: it is the repository's existing convention, and the
    *same* function is applied to corpus chunks and to queries, so no term can
    match in one and not the other. Stated exhaustively, because BM25 weights
    what this function emits:

    - **Case** — folded to lowercase before matching, so `Python` and `python`
      are one term.
    - **Punctuation and whitespace** — every character outside `[a-z0-9]` is a
      separator and is discarded, never a term and never part of one. `CI/CD`
      is two terms; `end-to-end` is three.
    - **Empty tokens** — not representable: the pattern matches one or more
      characters, so no zero-length term can reach the scorer, and text with no
      alphanumeric character tokenizes to the empty list.
    - **Repeated terms** — preserved. The list is a bag, not a set, in reading
      order, which is what gives BM25 its `tf` and its document lengths.
    - **Numeric terms** — kept, and weighted like any other term. `15` in
      "15 engineers" is a term; no numeric parsing, rounding or unit handling
      happens anywhere.

    **Nothing else is applied**, and the absence is the contract: no stemming,
    no lemmatization, no stop-word removal, no synonym or acronym expansion, no
    fuzzy or edit-distance matching, no spelling correction, and no query
    rewriting. No repository authority requires any of them, each would make the
    match set depend on a linguistic resource this repository does not carry,
    and query rewriting and expansion are explicitly out of scope for this
    sprint.
    """
    return _TOKEN_PATTERN.findall(text.lower())


@dataclass(frozen=True)
class BM25Statistics:
    """The corpus statistics BM25 needs, derived once from a chunk collection.

    A **data structure, not a seam.** It is built by `from_texts` from the text
    of the chunks a `Retriever` was handed, held privately by that retriever,
    and never injected, subclassed or substituted — Sprint M2.03 introduced no
    `LexicalProvider` or `BM25Index` Protocol, because no repository authority
    defines one and inventing one to mirror `EmbeddingProvider` and
    `VectorStore` would add an abstraction nothing varies behind. It is a
    separate object rather than four private attributes only so the statistics
    can be specified directly, which is what `tests/test_lexical_bm25.py` does.

    Every quantity BM25 requires is here or derivable from here: the document
    count `N`, per-term document frequency `df`, per-document term frequencies
    `tf`, per-document length `|d|`, and the corpus mean length `avgdl`.

    Positional, exactly like the corpus it is built from: index `i` of
    `term_frequencies` and `document_lengths` describes the chunk at index `i`
    of the collection. That is why this object carries **no chunk ids** — it
    introduces no second identity for a chunk, and the ranked output's identity
    comes from the chunk mappings themselves (`chunks[].id`). Frozen because it
    records what the corpus is; a retriever that could restate its own corpus
    statistics mid-run would not be reproducible.
    """

    document_count: int
    document_frequencies: dict = field(default_factory=dict)
    term_frequencies: tuple = ()
    document_lengths: tuple = ()
    average_document_length: float = 0.0

    @classmethod
    def from_texts(cls, texts) -> "BM25Statistics":
        """Derive the statistics from document texts, in the order given.

        One pass, `tokenize` applied to each text exactly once — so the terms
        BM25 weights are literally the terms the tokenization contract emits,
        with no second, drifting copy of that rule.
        """
        term_frequencies = tuple(Counter(tokenize(text)) for text in texts)
        document_lengths = tuple(sum(counts.values()) for counts in term_frequencies)

        document_frequencies: dict = {}
        for counts in term_frequencies:
            for term in counts:
                document_frequencies[term] = document_frequencies.get(term, 0) + 1

        count = len(term_frequencies)

        return cls(
            document_count=count,
            document_frequencies=document_frequencies,
            term_frequencies=term_frequencies,
            document_lengths=document_lengths,
            average_document_length=(sum(document_lengths) / count) if count else 0.0,
        )

    def inverse_document_frequency(self, term: str) -> float:
        """Return `ln(1 + (N - df + 0.5) / (df + 0.5))` for `term`.

        The **non-negative** BM25 IDF — Lucene's `BM25Similarity` form, and the
        one this sprint elected over the classic
        `ln((N - df + 0.5) / (df + 0.5))`. The reason is a repository invariant,
        not taste. The classic form goes negative for any term carried by more
        than about half the corpus, which on a 259-chunk single-resume corpus is
        a routine occurrence, not a pathological one; a matching chunk could
        then score below zero. Two committed behaviours depend on that not
        happening: `EMPTY_RESULT_SCORE` is `0.0` and Architectural AC2 requires
        `score` to be *meaningful* on both paths, and the CLI's abstention path
        is reached by lexical disjointness (`docs/P3.6.0_…` §9.6). With this
        form every `idf` is strictly positive, so *matched* and *scored above
        zero* are the same statement and neither behaviour can be reached by
        arithmetic accident.

        An unseen term has `df = 0`, which yields the largest weight the corpus
        can express and is never a division by zero — but it can never
        contribute, because `tf` is `0` for every document and `score` skips it.
        """
        frequency = self.document_frequencies.get(term, 0)
        return math.log(1 + (self.document_count - frequency + 0.5) / (frequency + 0.5))

    def score(self, query_terms, position: int, k1: float = BM25_K1, b: float = BM25_B):
        """Score the document at `position` against `query_terms`.

        Returns `(score, matched_terms)` — the score rounded to
        `BM25_SCORE_PRECISION`, and the **distinct** query terms the document
        contains, sorted, so the diagnostic record is itself deterministic.

        `query_terms` is a sequence, and **multiplicity counts**: a term
        appearing twice in the query contributes its weight twice. That is the
        formulation of the reference implementations (Lucene, `rank_bm25`),
        which iterate the query's terms rather than its term set, and dropping
        it would silently make "python python" identical to "python".

        Summation runs over `sorted(query_terms)` rather than the caller's
        order, so the floating-point sum is associativity-stable: two queries
        with the same terms in a different word order produce the *same* score,
        rather than two values that differ in the last bits and rank
        differently. Ordering a query's terms changes nothing about which
        documents match, so nothing is lost by fixing the order.

        A term absent from the document contributes nothing at all — `tf` is
        zero, so the numerator is zero — and is skipped rather than added, which
        is why an all-unknown query yields exactly `0.0` and not a sum of zeros
        that rounding has to rescue.

        When `average_document_length` is `0.0` the corpus holds no term at all,
        so the length-normalization ratio is taken as `0.0`: every document has
        the corpus mean length, trivially. That path is unreachable through
        `rank_candidates` — a corpus with no terms produces no candidates — and
        is defined here so the function is total for a direct caller.
        """
        counts = self.term_frequencies[position]
        length = self.document_lengths[position]
        average = self.average_document_length
        ratio = (length / average) if average else 0.0
        normalization = k1 * (1 - b + b * ratio)

        total = 0.0
        for term in sorted(query_terms):
            frequency = counts.get(term, 0)
            if frequency:
                total += (
                    self.inverse_document_frequency(term)
                    * frequency
                    * (k1 + 1)
                    / (frequency + normalization)
                )

        matched = sorted(term for term in set(query_terms) if counts.get(term, 0))
        return round(total, BM25_SCORE_PRECISION), matched


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

    def __init__(self, chunks: list, canonical_document_ids: set = None):
        """Bind the retriever to an already-loaded, already-validated chunk collection.

        The collection is copied into a private list so that later mutation by a
        caller cannot change what this retriever sees, and so the retriever
        itself has nothing to write back to. Corpus order is preserved exactly
        as committed — it is the tie-break authority used by `rank_candidates`.

        `canonical_document_ids` carries the Knowledge Manifest's canonical
        designation (Sprint P3.7.5). It is *passed in* rather than read, because
        `docs/architecture.md` §6 bars `sample_rag/` from importing `scripts/`,
        and the Manifest is `scripts/build_manifest.py`'s artifact — the same
        constraint that already keeps this module free of any `scripts/` import.
        Defaulting to the empty set means an omitted designation reproduces
        pre-P3.7.5 ordering exactly, so the parameter is additive rather than
        behaviour-changing on its own.

        Sprint M2.03 derives the BM25 corpus statistics here, once per
        retriever, over the copied collection. Once, because they are a property
        of the corpus and not of a query — deriving them per call would make
        every query pay for the corpus and would let two queries against one
        retriever disagree about `avgdl`. Over the *copy*, so the statistics
        cannot be invalidated by a caller mutating the list afterwards: the
        corpus a retriever ranks and the corpus it computed `df` from are the
        same object by construction.
        """
        self._chunks = list(chunks)
        self._canonical_document_ids = frozenset(canonical_document_ids or ())
        self._statistics = BM25Statistics.from_texts(chunk["text"] for chunk in self._chunks)

    @property
    def statistics(self) -> BM25Statistics:
        """The BM25 corpus statistics this retriever ranks with.

        Read-only, and frozen, so exposing it cannot become a way to retune a
        live retriever. It is exposed at all because a score is only explainable
        against the corpus statistics that produced it, and a caller — or a
        specification — that can read `df` and `avgdl` can recompute any score
        this module reports.
        """
        return self._statistics

    def rank_candidates(self, query_terms) -> list[tuple]:
        """Score every chunk and order the matches deterministically.

        Ordering is descending BM25 score, then canonical documents ahead of
        superseded ones, then ascending committed corpus position. **All three
        levels are Sprint P3.3.1's and P3.7.5's, unchanged**; Sprint M2.03
        replaced only what the first level compares. No new tie-break was
        invented, and in particular no second chunk identity was introduced to
        break one.

        The canonical term sits *between* score and position and touches
        neither. It cannot change which chunks are candidates, cannot change any
        chunk's score, and cannot reorder two chunks whose scores differ — it
        selects only among candidates the lexical scorer already ranked equal,
        where the prior behaviour was to take whichever document the Manifest
        happened to list first. That default silently preferred the superseded
        resume version, because the Manifest orders sources alphabetically and
        `v2_2` sorts before `v2_3`.

        The positional tie-break remains, and remains last. BM25 scores collide
        far less often than overlap counts did, but they still collide exactly —
        two chunks of equal length carrying the same query terms the same number
        of times score identically, and duplicated text across resume versions
        makes that a real case on this corpus rather than a hypothetical one.
        Anchoring the final tie to the Chunk Corpus's own persisted order —
        Knowledge Manifest document order, then `chunk_index` (Sprint P3.2.2) —
        keeps ranking a property of the committed corpus rather than of this
        function's iteration, and makes it total: no two chunks share a
        position, so no pair of candidates is left unordered.

        Chunks carrying no query term are not candidates: retrieving them would
        be recording a match the query has no lexical basis for. Candidacy is
        tested on the matched terms rather than on the score, so it states that
        rule directly instead of inferring it from arithmetic — though with
        `inverse_document_frequency` strictly positive the two agree, and
        `tests/test_lexical_bm25.py` asserts they do.
        """
        candidates = []
        for position, chunk in enumerate(self._chunks):
            score, matched = self._statistics.score(query_terms, position)
            if matched:
                candidates.append((score, position, chunk, matched))

        candidates.sort(
            key=lambda candidate: (
                -candidate[0],
                self._canonical_rank(candidate[2]),
                candidate[1],
            )
        )
        return candidates

    def _canonical_rank(self, chunk: dict) -> int:
        """Return 0 for a chunk of a canonical document, 1 otherwise.

        A sort rank, not a score: it is never combined with, added to, or
        compared against a retrieval score, and it is read only after the score
        comparison above has already tied. Returning a fixed small integer
        rather than a weight is what makes that structural instead of
        conventional — there is no magnitude here to leak into ranking.
        """
        return 0 if chunk["document_id"] in self._canonical_document_ids else 1

    def retrieve(self, query: str, filters: dict) -> RetrievalResult:
        """Execute lexical BM25 retrieval for one query.

        `filters` is the frozen interface's filter mapping. Only `top_k` is
        honored in this sprint; the SQL-filter stage that would consume the
        remaining keys is not exercised (see module docstring), so any other key
        is reported in `diagnostics["filters_ignored"]` rather than silently
        dropped — an unapplied filter should be visible in the runtime record,
        not invisible.

        Scores are **BM25 scores, and are not normalized**. Sprint P3.3.1
        divided its overlap count by the query's distinct-term count to make a
        score comparable across queries; Sprint M2.03 removed that division
        deliberately. A BM25 score is not a fraction of anything and has no
        upper bound, so dividing by the query length would produce a number that
        looks like a proportion and is not one — and any *scheme* for making two
        routes' scores comparable is score fusion, which belongs to **M2-04**
        and not here. The result-level `score` is therefore the top-ranked
        chunk's BM25 score, and `EMPTY_RESULT_SCORE` when nothing matched — a
        deterministic, meaningful value on both paths, never `None`
        (Architectural AC2).

        `diagnostics["query_terms"]` is the exact term sequence BM25 scored:
        sorted, and **with multiplicity**, where Sprint P3.3.1 recorded the
        distinct set. It changed because the runtime record should be the input
        to the score it reports, and under BM25 a repeated query term is part of
        that input. `bm25_k1`, `bm25_b` and `average_document_length` join it
        for the same reason — with `corpus_size` and `scores` already present,
        the record now carries everything needed to recompute any score in it.

        Returns observed behavior only. Nothing here consults the Evidence Trace
        Dataset, and nothing here expresses whether the retrieval was correct;
        that comparison is Sprint P3.3.2's.
        """
        filters = filters or {}
        top_k = filters.get("top_k", DEFAULT_TOP_K)
        ignored = sorted(key for key in filters if key != "top_k")

        query_terms = sorted(tokenize(query))
        matched = self.rank_candidates(query_terms)
        candidates = matched[:top_k]

        chunks = [chunk for _, _, chunk, _ in candidates]
        scores = [score for score, _, _, _ in candidates]

        diagnostics = {
            "query": query,
            "query_terms": query_terms,
            "retrieved_chunk_ids": [chunk["id"] for chunk in chunks],
            "document_ids": [chunk["document_id"] for chunk in chunks],
            "scores": scores,
            "ranking": list(range(1, len(chunks) + 1)),
            "matched_terms": [matched for _, _, _, matched in candidates],
            "retrieval_method": LEXICAL_ROUTE,
            "bm25_k1": BM25_K1,
            "bm25_b": BM25_B,
            "average_document_length": self._statistics.average_document_length,
            "top_k": top_k,
            "candidates_matched": len(matched),
            "corpus_size": len(self._chunks),
            "sql_filter_applied": False,
            "filters_ignored": ignored,
            "retrieval_time_ms": PLACEHOLDER_RETRIEVAL_TIME_MS,
            "stub": LEXICAL_STUB,
        }

        return RetrievalResult(
            chunks=chunks,
            retrieval_route=LEXICAL_ROUTE,
            score=scores[0] if scores else EMPTY_RESULT_SCORE,
            diagnostics=diagnostics,
        )
