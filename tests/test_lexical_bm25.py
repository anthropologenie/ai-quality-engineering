"""Specifications for the lexical BM25 retrieval route — Sprint M2.03.

Register capability **M2-03** — *"a ranking function replacing plain
distinct-term overlap"* (`docs/DEFERRED_ITEMS_REGISTER.md` §4). The sprint
replaces `sample_rag/retriever.py`'s scorer with genuine BM25 behind the
unchanged `retrieve(query, filters) -> RetrievalResult` contract, so these
specifications are about the *ranking function and its contract*, not about the
retrieval seam, which Sprints P3.3.1 and P3.7.5 already specified and which the
27 CLI, 48 generation and 117 evaluation specifications already exercise
end-to-end.

What this module establishes, and in this order: that the scorer is BM25 rather
than a renamed overlap count; that the tokenization/normalization contract is
the documented one and is applied identically to corpus and query; that the
corpus statistics BM25 needs are derived correctly; that ranking is
deterministic and totally ordered; that the degenerate queries and corpora are
defined rather than accidental; and that the route returns the repository's
**canonical** chunk ids and reaches neither FAISS nor the embedding model.

**BM25 is lexical, and these specifications say so rather than implying
otherwise.** `test_m203_bm25_carries_no_semantic_understanding` presents a
query that is a correct paraphrase of a chunk and shares no term with it, and
asserts the route retrieves nothing — the whole point of keeping the semantic
route (**M2-01** / **M2-02**) separate. No specification here asserts that a
higher BM25 score means a better answer.

**No fusion is specified because none exists.**
`test_m203_the_lexical_route_is_independent_of_the_semantic_route` is what keeps
that structural: Reciprocal Rank Fusion and hybrid ranking are **M2-04**,
reranking is **M2-05**, and a helper added to this module's subject later fails
that specification rather than passing unnoticed.

Scoring is recomputed from the BM25 formula in several specifications below,
independently of `BM25Statistics.score`. That is deliberate: a specification
that called the implementation to compute its own expectation would assert only
that the implementation equals itself.
"""

import ast
import importlib
import inspect
import math
import pathlib

import pytest

from sample_rag.retriever import (
    BM25_B,
    BM25_K1,
    BM25_SCORE_PRECISION,
    DEFAULT_TOP_K,
    EMPTY_RESULT_SCORE,
    LEXICAL_ROUTE,
    LEXICAL_STUB,
    BM25Statistics,
    Retriever,
    tokenize,
)

# ---------------------------------------------------------------------------
# Fixtures and helpers
# ---------------------------------------------------------------------------


def chunk(chunk_id, text, document_id="doc-a", index=0):
    """One chunk mapping, shaped exactly as the committed Chunk Corpus stores them.

    All six contract fields are supplied even though the retriever reads three,
    so a specification exercising ranking is never also exercising a malformed
    corpus (`docs/CHUNK_CONTRACT.md` §17).
    """
    return {
        "id": chunk_id,
        "document_id": document_id,
        "text": text,
        "chunk_index": index,
        "character_start": 0,
        "character_end": len(text),
    }


def corpus(*texts):
    """A synthetic corpus of `texts`, with positional ids and one parent document.

    Ids are `c0`, `c1`, … and are the *only* identity in play — the same
    `chunks[].id` field the committed corpus uses and the semantic route
    returns. Nothing here introduces a second one.
    """
    return [chunk(f"c{position}", text, index=position) for position, text in enumerate(texts)]


def bm25(statistics, query_terms, position, k1=BM25_K1, b=BM25_B):
    """Recompute the BM25 score for one document, from the formula alone.

    The independent oracle for the scoring specifications: written straight from
    `docs/M2.03_Real_BM25_Lexical_Retrieval_Report.md` §5's formula, reading only
    the four corpus statistics, and calling nothing on the implementation's
    scoring path.
    """
    counts = statistics.term_frequencies[position]
    length = statistics.document_lengths[position]
    average = statistics.average_document_length
    normalization = k1 * (1 - b + b * (length / average if average else 0.0))

    total = 0.0
    for term in sorted(query_terms):
        frequency = counts.get(term, 0)
        if frequency:
            document_frequency = statistics.document_frequencies.get(term, 0)
            idf = math.log(
                1
                + (statistics.document_count - document_frequency + 0.5)
                / (document_frequency + 0.5)
            )
            total += idf * frequency * (k1 + 1) / (frequency + normalization)

    return round(total, BM25_SCORE_PRECISION)


@pytest.fixture
def committed(real_chunks):
    """A `Retriever` over the committed Chunk Corpus, with no canonical designation.

    The designation is omitted deliberately: it is a *tie-break* input
    (Sprint P3.7.5) and every specification below that concerns ranking states
    its own expectation about ties. `test_m203_the_canonical_tie_break_is_preserved`
    supplies it explicitly, which is where it belongs.
    """
    return Retriever(real_chunks)


def imported_roots(module):
    """Every top-level package name imported by `module`'s source."""
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
    """Every function, class and assignment target `module` declares.

    What a module *is*, as opposed to what its comments say — the distinction
    `test_m203_the_semantic_route_is_untouched_by_the_lexical_one` depends on.
    """
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


# ---------------------------------------------------------------------------
# 1. Genuine BM25 rather than term overlap
# ---------------------------------------------------------------------------


def test_m203_a_rare_term_outweighs_a_common_one():
    """Inverse document frequency exists — the property overlap counting cannot have.

    Both candidates match exactly **one** distinct query term, so Sprint
    P3.3.1's scorer ranked them equal and resolved the tie by corpus position,
    which here would put the common-term chunk first. BM25 must put the
    rare-term chunk first instead: `beta` occurs in one chunk of five and
    `alpha` in four, so `beta` carries the larger weight.

    Stated as a strict inequality on the scores as well as on the order, so a
    scorer that produced the right sequence for the wrong reason — a
    position-based accident, or an overlap count that happened to differ — still
    fails.
    """
    retriever = Retriever(corpus("alpha", "alpha", "alpha", "alpha", "beta"))

    result = retriever.retrieve("alpha beta", {})
    scores = dict(zip(result.diagnostics["retrieved_chunk_ids"], result.diagnostics["scores"]))

    assert result.diagnostics["retrieved_chunk_ids"][0] == "c4"
    assert scores["c4"] > scores["c0"]
    assert all(terms == ["alpha"] for terms in result.diagnostics["matched_terms"][1:])


def test_m203_term_frequency_within_a_chunk_raises_the_score():
    """`tf` participates — a term occurring twice outscores the same term once.

    Distinct-term overlap is blind to this by construction: both chunks match
    the one query term, so both scored 1. Under BM25 the repeated occurrence
    increases `tf` and therefore the score, and the length penalty cannot cancel
    it here because the two chunks carry the same padding.
    """
    retriever = Retriever(corpus("alpha alpha padding", "alpha padding padding"))

    result = retriever.retrieve("alpha", {})

    assert result.diagnostics["retrieved_chunk_ids"] == ["c0", "c1"]
    assert result.diagnostics["scores"][0] > result.diagnostics["scores"][1]


def test_m203_term_frequency_saturates_rather_than_accumulating_linearly():
    """`k1` saturates `tf` — this is BM25, not a weighted occurrence count.

    The distinguishing property. A linear scorer would give three occurrences
    three times the score of one; BM25's `tf · (k1 + 1) / (tf + k1 · …)` is
    bounded above by `idf · (k1 + 1)` however large `tf` grows, so each further
    occurrence adds less than the one before it. Both halves are asserted — that
    more still means more, and that the *marginal* gain falls — because either
    alone is satisfied by a scorer that is not BM25.

    The three documents are padded to **equal length**, deliberately: varying
    `tf` by lengthening a document would vary `|d| / avgdl` at the same time and
    the comparison would no longer isolate saturation. `df` and `idf` are
    likewise identical across the three, since every one of them carries
    `alpha`.
    """
    statistics = BM25Statistics.from_texts(
        ["alpha pad pad pad", "alpha alpha pad pad", "alpha alpha alpha pad"]
    )
    scores = [statistics.score(["alpha"], position)[0] for position in range(3)]

    assert statistics.document_lengths == (4, 4, 4)
    assert scores[0] < scores[1] < scores[2]
    assert (scores[2] - scores[1]) < (scores[1] - scores[0])

    # The ceiling holds for any document length, because `k1 · (1 − b + b·…)` is
    # strictly positive: no amount of repetition reaches `idf · (k1 + 1)`.
    saturated = BM25Statistics.from_texts(["alpha " * 500, "beta"])

    assert saturated.score(["alpha"], 0)[0] < (
        saturated.inverse_document_frequency("alpha") * (BM25_K1 + 1)
    )


def test_m203_document_length_normalization_penalizes_the_longer_chunk():
    """`b` participates — equal `tf`, and the shorter chunk wins.

    The two chunks carry `alpha` exactly once, so `tf` and `idf` are identical
    and the only term that can separate them is `|d| / avgdl`. A scorer without
    length normalization would tie them and fall through to corpus position,
    which here would produce the same first element by accident; the score
    inequality is what makes the specification about normalization.
    """
    retriever = Retriever(corpus("alpha", "alpha filler filler filler filler filler"))

    result = retriever.retrieve("alpha", {})
    scores = result.diagnostics["scores"]

    assert result.diagnostics["retrieved_chunk_ids"] == ["c0", "c1"]
    assert scores[0] > scores[1]


def test_m203_scores_match_the_documented_formula_on_the_committed_corpus(
    committed, real_chunks
):
    """Every reported score equals the formula recomputed independently.

    Over the committed corpus and a real query, so the agreement is asserted
    against the corpus the repository actually ships rather than a two-chunk
    fixture. `bm25` above reads only the four corpus statistics and reimplements
    the arithmetic, so this is the formula checking the implementation and not
    the implementation checking itself.
    """
    result = committed.retrieve("What cloud platforms have you worked with?", {})
    terms = result.diagnostics["query_terms"]

    # Positions come from the committed corpus, not from the retriever's private
    # copy: the retriever preserves corpus order (`__init__`), so the two agree,
    # and reading the committed collection is what makes this an independent
    # recomputation rather than a look inside the subject.
    positions = {chunk["id"]: position for position, chunk in enumerate(real_chunks)}
    expected = [
        bm25(committed.statistics, terms, positions[chunk_id])
        for chunk_id in result.diagnostics["retrieved_chunk_ids"]
    ]

    assert result.diagnostics["scores"] == expected
    assert result.score == expected[0]


def test_m203_the_score_is_not_a_normalized_fraction(committed):
    """The result-level score is a BM25 score, not the P3.3.1 overlap fraction.

    Sprint P3.3.1 divided the overlap count by the query's distinct-term count,
    which bounded every score in `[0, 1]`. Sprint M2.03 removed that division
    (`retrieve`'s docstring records why: a BM25 score is not a fraction, and any
    scheme for making two routes comparable is **M2-04**'s score fusion). A
    score above 1 is the observable consequence, and it is asserted here so the
    removal is specified rather than incidental.
    """
    result = committed.retrieve("cloud platforms", {})

    assert result.score > 1.0
    assert result.score == max(result.diagnostics["scores"])


# ---------------------------------------------------------------------------
# 2. Tokenization and normalization
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "text, expected",
    [
        pytest.param("Alpha ALPHA aLpHa", ["alpha", "alpha", "alpha"], id="case-folded"),
        pytest.param("alpha, beta; gamma.", ["alpha", "beta", "gamma"], id="punctuation-split"),
        pytest.param("  alpha \t\n beta  ", ["alpha", "beta"], id="whitespace-collapsed"),
        pytest.param("alpha alpha beta", ["alpha", "alpha", "beta"], id="repeats-preserved"),
        pytest.param("CI/CD", ["ci", "cd"], id="slash-is-a-separator"),
        pytest.param("end-to-end", ["end", "to", "end"], id="hyphen-is-a-separator"),
        pytest.param("led 15 engineers", ["led", "15", "engineers"], id="numerics-kept"),
        pytest.param("alpha2beta", ["alpha2beta"], id="alphanumeric-is-one-term"),
        pytest.param("...", [], id="no-alphanumeric-tokenizes-to-nothing"),
        pytest.param("", [], id="empty-text-tokenizes-to-nothing"),
    ],
)
def test_m203_the_tokenization_contract_is_exactly_as_documented(text, expected):
    """`tokenize` — every decision the BM25 contract had to make, stated as a case.

    Enumerated rather than described, because BM25 weights precisely what this
    function emits: a silent change to any row below would change every `tf`,
    every `df` and every document length in the corpus. Order is asserted too —
    the function returns reading order, which is what makes the result a bag
    with positions rather than a set.
    """
    assert tokenize(text) == expected


def test_m203_no_stemming_lemmatization_or_stop_word_removal_is_applied():
    """The absences are the contract, and are asserted rather than assumed.

    `engineer`/`engineering`/`engineers` remain three distinct terms, and the
    common function words survive tokenization. A stemmer, lemmatizer or
    stop-word list would each make the match set depend on a linguistic
    resource this repository does not carry — and none is required by any
    repository authority, which `docs/M2.03_…` §4 records.
    """
    assert tokenize("engineer engineering engineers") == [
        "engineer",
        "engineering",
        "engineers",
    ]
    assert tokenize("the a of and is") == ["the", "a", "of", "and", "is"]


def test_m203_the_same_tokenization_applies_to_corpus_and_query():
    """One contract, both sides — a term cannot exist in a chunk and not in a query.

    Asserted behaviourally rather than by inspecting the call sites: a
    differently-cased, differently-punctuated query retrieves the chunk whose
    text tokenizes to the same terms. Were the corpus lowercased and the query
    not, this returns nothing.
    """
    retriever = Retriever(corpus("Kubernetes, AWS."))

    assert retriever.retrieve("kubernetes aws", {}).diagnostics["retrieved_chunk_ids"] == ["c0"]
    assert retriever.retrieve("KUBERNETES!!! (aws)", {}).diagnostics["retrieved_chunk_ids"] == [
        "c0"
    ]


# ---------------------------------------------------------------------------
# 3. Corpus statistics
# ---------------------------------------------------------------------------


def test_m203_the_corpus_statistics_are_derived_correctly():
    """`N`, `df`, `tf`, `|d|` and `avgdl`, each against a hand-computed value.

    A three-document corpus small enough that every statistic can be stated by
    hand, so the specification records what the numbers *are* rather than that
    they are self-consistent.
    """
    statistics = BM25Statistics.from_texts(
        ["alpha beta", "alpha alpha gamma", "delta"]
    )

    assert statistics.document_count == 3
    assert statistics.document_frequencies == {
        "alpha": 2,
        "beta": 1,
        "gamma": 1,
        "delta": 1,
    }
    assert statistics.term_frequencies[1]["alpha"] == 2
    assert statistics.document_lengths == (2, 3, 1)
    assert statistics.average_document_length == 2.0


def test_m203_document_frequency_counts_documents_not_occurrences():
    """`df` is a document count — three occurrences in one chunk is `df = 1`.

    The distinction BM25's `idf` depends on. A `df` that counted occurrences
    would make a term repeated within a single chunk look corpus-wide and
    collapse its weight, which is the opposite of what repetition means.
    """
    statistics = BM25Statistics.from_texts(["alpha alpha alpha", "beta"])

    assert statistics.document_frequencies["alpha"] == 1
    assert statistics.term_frequencies[0]["alpha"] == 3


def test_m203_inverse_document_frequency_is_strictly_positive_for_every_corpus_term():
    """Every `idf` over the committed corpus is `> 0`, including the commonest term.

    The invariant the Lucene IDF form was chosen for
    (`inverse_document_frequency`'s docstring records the reasoning). The classic
    `ln((N − df + 0.5) / (df + 0.5))` goes negative once a term is carried by
    more than about half the corpus; with 259 chunks drawn from one resume that
    is a routine case, and a negative weight would let a *matching* chunk score
    below zero and collide with `EMPTY_RESULT_SCORE`.

    Asserted over the whole vocabulary rather than a sampled term, and the
    monotonicity is asserted alongside it: rarer must still mean heavier, or a
    positive floor would have been bought at the cost of the weighting.
    """
    statistics = BM25Statistics.from_texts(["a"] * 10 + ["a b"])

    assert all(
        statistics.inverse_document_frequency(term) > 0
        for term in statistics.document_frequencies
    )
    assert statistics.inverse_document_frequency("b") > statistics.inverse_document_frequency("a")


def test_m203_an_unseen_term_has_a_defined_weight_and_contributes_nothing():
    """`df = 0` is total, and never a division by zero — but never scores either.

    The `+ 0.5` in both numerator and denominator makes the unseen term the
    heaviest the corpus can express rather than an error; `score` then skips it
    because its `tf` is zero in every document. Both halves matter: the first
    keeps the function total for a direct caller, the second is why an unknown
    query term cannot manufacture a match.
    """
    statistics = BM25Statistics.from_texts(["alpha"])

    assert statistics.inverse_document_frequency("absent") > 0
    assert statistics.score(["absent"], 0) == (0.0, [])


def test_m203_statistics_are_positional_and_carry_no_chunk_identity():
    """The statistics object holds no id — there is no second chunk identity here.

    Index `i` of `term_frequencies` and `document_lengths` describes the chunk at
    index `i` of the collection, which is the corpus order the retriever already
    treats as authoritative. Asserted structurally over the dataclass's declared
    fields, so a later field named `chunk_id`, `bm25_id` or `lexical_id` fails
    here rather than being noticed in review.
    """
    fields = set(BM25Statistics.__dataclass_fields__)

    assert fields == {
        "document_count",
        "document_frequencies",
        "term_frequencies",
        "document_lengths",
        "average_document_length",
    }
    assert not any("id" in name for name in fields)


def test_m203_the_statistics_are_derived_once_and_describe_the_bound_corpus(real_chunks):
    """One derivation per retriever, over the copy the retriever ranks.

    Both properties in one specification because they are one guarantee: the
    corpus a retriever computed `df` from and the corpus it ranks are the same
    object. A caller mutating its own list afterwards changes neither, so two
    queries against one retriever cannot disagree about `avgdl`.
    """
    mutable = list(real_chunks)
    retriever = Retriever(mutable)

    before = retriever.statistics
    retriever.retrieve("cloud", {})
    mutable.clear()

    assert retriever.statistics is before
    assert retriever.statistics.document_count == len(real_chunks)
    assert retriever.retrieve("cloud", {}).diagnostics["corpus_size"] == len(real_chunks)


# ---------------------------------------------------------------------------
# 4. Ranking direction, determinism and tie-breaking
# ---------------------------------------------------------------------------


def test_m203_ranking_is_by_descending_score(committed):
    """Higher BM25 score first, over the committed corpus and a real query.

    Asserted as a non-increasing sequence over every candidate rather than over
    the top-k slice, so a ranking that is correct within the returned window and
    wrong outside it — which a later `top_k` change would then expose — fails
    now.
    """
    result = committed.retrieve("engineering leadership cloud platforms", {"top_k": 40})
    scores = result.diagnostics["scores"]

    assert len(scores) > 1
    assert scores == sorted(scores, reverse=True)
    assert result.score == scores[0]


def test_m203_equal_scores_are_broken_by_committed_corpus_position():
    """A genuine tie falls through to ascending corpus position, and nothing else.

    The three chunks are identical in text, so they are identical in `tf`, in
    `|d|` and in `df` contribution — the tie is exact, not approximate. The
    surviving order is the Chunk Corpus's own persisted order (Knowledge
    Manifest document order, then `chunk_index`), which is Sprint P3.3.1's
    tie-break unchanged. **No new identity was introduced to break it**: the
    positions are the collection's, and `c0`/`c1`/`c2` are the same
    `chunks[].id` values the semantic route returns.
    """
    retriever = Retriever(corpus("alpha beta", "alpha beta", "alpha beta"))

    result = retriever.retrieve("alpha beta", {})

    assert len(set(result.diagnostics["scores"])) == 1
    assert result.diagnostics["retrieved_chunk_ids"] == ["c0", "c1", "c2"]


def test_m203_the_canonical_tie_break_is_preserved_and_still_sits_between():
    """Sprint P3.7.5's canonical rank still resolves ties, and still only ties.

    Two assertions, because the tie-break has always had two halves. Among
    equal-scoring candidates the canonical document's chunk comes first; and
    when the scores *differ*, canonical designation cannot promote the weaker
    chunk — the designation is a sort rank between score and position, never a
    weight added to a score.
    """
    tied = [chunk("c0", "alpha", "old"), chunk("c1", "alpha", "new", index=1)]
    retriever = Retriever(tied, canonical_document_ids={"new"})

    assert retriever.retrieve("alpha", {}).diagnostics["retrieved_chunk_ids"] == ["c1", "c0"]

    outscored = [
        chunk("c0", "alpha alpha", "old"),
        chunk("c1", "alpha filler filler", "new", index=1),
    ]
    outranked = Retriever(outscored, canonical_document_ids={"new"})

    assert outranked.retrieve("alpha", {}).diagnostics["retrieved_chunk_ids"] == ["c0", "c1"]


def test_m203_the_ordering_is_total_over_the_committed_corpus(committed):
    """No pair of candidates is left unordered — position makes the sort total.

    The property that makes determinism a guarantee rather than an observation:
    ties in score and in canonical rank are possible, ties in corpus position
    are not, so the sort key is injective over the candidate set and the
    surviving order cannot depend on Python's sort implementation.
    """
    candidates = committed.rank_candidates(sorted(tokenize("engineering data quality")))
    keys = [(score, position) for score, position, _, _ in candidates]

    assert len(candidates) > 1
    assert len({position for _, position in keys}) == len(candidates)
    assert keys == sorted(keys, key=lambda key: (-key[0], key[1]))


def test_m203_the_same_query_is_reproducible_across_repeated_runs(committed, real_chunks):
    """Same corpus, same query, same ordered chunk ids — across calls and instances.

    Repeated ten times on one retriever *and* against a freshly constructed one,
    so the guarantee covers both a stateful retriever leaking between calls and
    a construction-order dependency in the statistics. The whole diagnostic
    record is compared, not just the ids, because a reproducible order with a
    drifting score is not determinism.
    """
    first = committed.retrieve("cloud platforms and data quality", {})
    repeats = [committed.retrieve("cloud platforms and data quality", {}) for _ in range(10)]
    rebuilt = Retriever(list(real_chunks)).retrieve("cloud platforms and data quality", {})

    assert all(result.diagnostics == first.diagnostics for result in repeats)
    assert all(result.score == first.score for result in repeats)
    assert rebuilt.diagnostics == first.diagnostics


def test_m203_query_word_order_does_not_change_any_score(committed):
    """A permuted query scores identically — the summation order is canonical.

    `score` sums over `sorted(query_terms)` rather than the caller's order, so
    the floating-point sum is associativity-stable. Without that, two spellings
    of the same query could differ in the last bits, round differently and rank
    differently — determinism that holds per-query but not across equivalent
    queries.
    """
    forward = committed.retrieve("cloud platforms data quality", {})
    reversed_ = committed.retrieve("quality data platforms cloud", {})

    assert forward.diagnostics["scores"] == reversed_.diagnostics["scores"]
    assert forward.diagnostics["retrieved_chunk_ids"] == reversed_.diagnostics["retrieved_chunk_ids"]


# ---------------------------------------------------------------------------
# 5. Query handling — repeats, degenerate queries, degenerate corpora
# ---------------------------------------------------------------------------


def test_m203_a_repeated_query_term_counts_twice():
    """Query-term multiplicity participates, as the reference implementations have it.

    `score` iterates the query's terms rather than its term set (Lucene and
    `rank_bm25` both do), so `"alpha alpha"` weights `alpha` twice. Asserted on
    the score rather than only on the recorded terms, because a scorer that
    recorded multiplicity and then scored the set would pass the weaker check.
    """
    retriever = Retriever(corpus("alpha beta", "beta beta"))

    single = retriever.retrieve("alpha", {})
    doubled = retriever.retrieve("alpha alpha", {})

    assert doubled.diagnostics["query_terms"] == ["alpha", "alpha"]
    assert doubled.diagnostics["scores"][0] == pytest.approx(
        2 * single.diagnostics["scores"][0], rel=1e-9
    )


def test_m203_the_recorded_query_terms_are_the_terms_that_were_scored(committed):
    """`diagnostics["query_terms"]` is the exact scored sequence — sorted, with repeats.

    Sprint P3.3.1 recorded the distinct set; Sprint M2.03 records the bag,
    because under BM25 a repeated term is part of the input to the score the
    same record reports. Asserted against `tokenize` directly, so the record
    cannot drift from the tokenization contract.
    """
    query = "cloud cloud platforms"
    result = committed.retrieve(query, {})

    assert result.diagnostics["query_terms"] == sorted(tokenize(query))
    assert result.diagnostics["query_terms"] == ["cloud", "cloud", "platforms"]


@pytest.mark.parametrize(
    "query",
    [
        pytest.param("", id="empty-string"),
        pytest.param("   ", id="whitespace-only"),
        pytest.param("!!! ??? ...", id="punctuation-only"),
    ],
)
def test_m203_a_query_with_no_terms_retrieves_nothing(committed, query):
    """A query that tokenizes to nothing is a defined no-match, not an error.

    The path the CLI's abstention behaviour depends on — `--question ""` is a
    well-formed argument, and the pipeline handles it through its contracted
    path rather than through a CLI guard (`tests/test_cli.py`
    `test_an_empty_question_is_accepted_and_abstains`). Every contract field
    still carries a deterministic, meaningful value (Architectural AC2).
    """
    result = committed.retrieve(query, {})

    assert result.chunks == []
    assert result.score == EMPTY_RESULT_SCORE
    assert result.retrieval_route == LEXICAL_ROUTE
    assert result.diagnostics["query_terms"] == []
    assert result.diagnostics["candidates_matched"] == 0


def test_m203_unknown_query_terms_retrieve_nothing_and_score_zero(committed):
    """A query sharing no term with the corpus is a no-match, not a weak match.

    `df = 0` gives an unknown term the heaviest weight the corpus can express,
    so a scorer that added its `idf` without checking `tf` would return the
    whole corpus at a uniform score. It returns nothing instead — and this is
    the lexical-disjointness property `docs/P3.6.0_…` §9.6 records the
    abstention path as relying on.
    """
    result = committed.retrieve("zzzz qqqq wwww", {})

    assert result.chunks == []
    assert result.score == EMPTY_RESULT_SCORE
    assert result.diagnostics["query_terms"] == ["qqqq", "wwww", "zzzz"]
    assert result.diagnostics["candidates_matched"] == 0


def test_m203_a_partially_unknown_query_scores_only_its_known_terms():
    """Unknown terms are skipped, not penalized and not imputed.

    The score for `"alpha zzzz"` equals the score for `"alpha"` exactly. A
    scorer that let the unknown term contribute would inflate it; one that
    divided by the query length — Sprint P3.3.1's normalization — would deflate
    it.
    """
    retriever = Retriever(corpus("alpha", "beta"))

    assert retriever.retrieve("alpha zzzz", {}).score == retriever.retrieve("alpha", {}).score


def test_m203_a_single_document_corpus_ranks_and_scores():
    """`N = 1` is a defined corpus, not a degenerate one.

    Worth stating because `idf` is at its most delicate here — `N = df = 1`
    gives `ln(1 + 0.5/1.5)`, small but strictly positive, where the classic IDF
    form would give `ln(0.5/1.5) < 0` and rank the only matching chunk below
    zero. And `avgdl == |d|`, so the length-normalization ratio is exactly 1.
    """
    retriever = Retriever(corpus("alpha beta"))

    result = retriever.retrieve("alpha", {})

    assert result.diagnostics["retrieved_chunk_ids"] == ["c0"]
    assert result.score > 0
    assert retriever.statistics.average_document_length == 2.0


def test_m203_an_empty_corpus_retrieves_nothing_and_defines_its_statistics():
    """A retriever over no chunks answers every query with a defined no-match.

    `avgdl` is `0.0` rather than a division by zero, and `score` treats the
    length ratio as `0.0` on that path — defined so the function is total for a
    direct caller, and unreachable through `rank_candidates`, which has no
    document to score.
    """
    retriever = Retriever([])

    result = retriever.retrieve("alpha", {})

    assert retriever.statistics.document_count == 0
    assert retriever.statistics.average_document_length == 0.0
    assert result.chunks == []
    assert result.score == EMPTY_RESULT_SCORE
    assert result.diagnostics["corpus_size"] == 0


def test_m203_a_chunk_with_no_terms_is_never_a_candidate():
    """A chunk whose text tokenizes to nothing cannot be retrieved.

    `tf` is zero for every term, so it matches nothing — and its zero length
    still lowers `avgdl` for the rest of the corpus, which is correct: it is a
    document in the collection, it just carries no term.
    """
    retriever = Retriever(corpus("alpha", "...", "alpha alpha"))

    result = retriever.retrieve("alpha", {})

    assert result.diagnostics["retrieved_chunk_ids"] == ["c2", "c0"]
    assert retriever.statistics.document_lengths == (1, 0, 2)


def test_m203_top_k_bounds_the_result_without_changing_the_ranking(committed):
    """`top_k` slices an already-total order; `candidates_matched` reports the rest.

    Sprint P3.3.1's behaviour, restated against BM25 scores: the returned window
    is a prefix of the full ranking, and the count of everything that matched is
    recorded rather than discarded.
    """
    full = committed.retrieve("cloud platforms", {"top_k": 100})
    limited = committed.retrieve("cloud platforms", {"top_k": 3})

    assert len(limited.chunks) == 3
    assert limited.diagnostics["retrieved_chunk_ids"] == (
        full.diagnostics["retrieved_chunk_ids"][:3]
    )
    assert limited.diagnostics["candidates_matched"] == full.diagnostics["candidates_matched"]
    assert committed.retrieve("cloud platforms", {}).diagnostics["top_k"] == DEFAULT_TOP_K


# ---------------------------------------------------------------------------
# 6. BM25 is lexical — the boundary the semantic route exists for
# ---------------------------------------------------------------------------


def test_m203_bm25_carries_no_semantic_understanding():
    """A correct paraphrase sharing no term retrieves nothing. That is not a defect.

    The query is a faithful restatement of the chunk's meaning — *supervised
    personnel* for *led a team of engineers* — and overlaps it in no token, so
    BM25, which weights term occurrence and nothing else,
    returns nothing. Recorded as an asserted property rather than a caveat,
    because the repository's reason for keeping a *separate* semantic route
    (**M2-01** / **M2-02**, `sample_rag/vector_runtime.py`) is exactly this
    gap, and **M2-04** is where the two routes are combined.

    The lexical half of the same pair is asserted alongside it: a query that
    *does* share terms retrieves the chunk. Without that, the specification
    would be consistent with a scorer that retrieves nothing at all.
    """
    retriever = Retriever(corpus("Led a team of fifteen engineers", "unrelated filler text"))

    disjoint = retriever.retrieve("supervised personnel", {})

    assert set(tokenize("supervised personnel")).isdisjoint(
        tokenize("Led a team of fifteen engineers")
    )
    assert disjoint.chunks == []
    assert retriever.retrieve("led engineers", {}).diagnostics["retrieved_chunk_ids"] == ["c0"]


def test_m203_a_higher_score_is_a_lexical_claim_and_the_route_says_so(committed):
    """The route reports itself as lexical, on every path.

    `retrieval_route` and `diagnostics["retrieval_method"]` both read `LEXICAL`,
    unchanged by this sprint. The label was not renamed to `BM25`: it names the
    *route* in the approved Hybrid Retrieval architecture — *Structured (SQL) +
    Lexical (BM25) + Semantic (Vector) → RRF* (`docs/roadmap.md` §1.1) — and
    BM25 is the ranking function that route now uses, not a fourth route.
    `diagnostics["sql_filter_applied"]` continues to report the unexercised
    structured branch separately.
    """
    for query in ("cloud platforms", "zzzz qqqq"):
        result = committed.retrieve(query, {})

        assert result.retrieval_route == LEXICAL_ROUTE == "LEXICAL"
        assert result.diagnostics["retrieval_method"] == LEXICAL_ROUTE
        assert result.diagnostics["sql_filter_applied"] is False


def test_m203_the_stub_marker_reports_a_real_ranking_function(committed):
    """`diagnostics["stub"]` is `False` — the marker swapped, the shape did not.

    `docs/MILESTONE_1A.md` build item 4 froze the marker so *"Milestone 2 swaps
    values inside an already-correct shape rather than changing the shape
    itself"*. Sprint M2.03 is that swap for the lexical route. The precedent is
    `Indexer.index(...).stub`, which Sprint M2.01A flipped `True -> False` for
    **M2-01** on the same reasoning (`tests/test_indexer.py`
    `test_1b03_the_index_declares_what_kind_of_vectors_it_holds`) — a marker
    that could only ever say `True` stops being one the moment a real
    implementation exists.
    """
    assert LEXICAL_STUB is False
    assert committed.retrieve("cloud", {}).diagnostics["stub"] is LEXICAL_STUB
    assert committed.retrieve("zzzz", {}).diagnostics["stub"] is LEXICAL_STUB


# ---------------------------------------------------------------------------
# 7. M2-04 preparation invariants — one identity, two independent routes
# ---------------------------------------------------------------------------


def test_m203_the_route_returns_canonical_chunk_ids(committed, real_chunks):
    """Every retrieved id is a committed `chunks[].id` — the repository's only chunk identity.

    The invariant **M2-04** will fuse on: `VectorStore.query(vector, top_k)`
    returns `list[str]` of the same field (`sample_rag/vector_store.py` —
    *"chunk **ids**, matching the identity `docs/CHUNK_CONTRACT.md` §17 makes
    globally unique and the join key `sample_rag/retriever.py` already ranks
    on"*). Asserted as membership in the committed corpus's id set, and as
    identity with the emitted chunk mappings, so a derived or re-hashed id
    fails.
    """
    committed_ids = {chunk["id"] for chunk in real_chunks}
    result = committed.retrieve("cloud platforms engineering", {})

    assert result.diagnostics["retrieved_chunk_ids"]
    assert set(result.diagnostics["retrieved_chunk_ids"]) <= committed_ids
    assert result.diagnostics["retrieved_chunk_ids"] == [chunk["id"] for chunk in result.chunks]


def test_m203_no_second_chunk_identity_is_introduced(committed):
    """No `lexical_chunk_id`, `bm25_id` or `lexical_document_id` exists anywhere.

    Stated over the module's whole source rather than over the diagnostic keys
    alone, so a second identity introduced as a local variable, a helper's
    parameter or a new field fails here. The route emits `chunks[].id` and
    `chunks[].document_id` and nothing else that identifies a chunk.
    """
    import sample_rag.retriever as module

    source = inspect.getsource(module)
    for barred in ("lexical_chunk_id", "bm25_id", "lexical_document_id", "lexical_id"):
        assert barred not in source, f"{barred} would be a second chunk identity"

    identity_keys = {
        key for key in committed.retrieve("cloud", {}).diagnostics if key.endswith("_ids")
    }
    assert identity_keys == {"retrieved_chunk_ids", "document_ids"}


def test_m203_the_lexical_route_is_independent_of_the_semantic_route():
    """M2.03 — the sprint boundary, enforced structurally.

    The mirror of
    `tests/test_vector_query.py::test_m201c_the_query_path_exposes_no_fusion_or_lexical_surface`,
    pointed the other way. The lexical route imports no vector module, no FAISS,
    no embedding library and no model, and declares no fusion, hybrid, rerank or
    query-rewriting helper. **M2-04** is where the two routes meet; a helper
    added here later fails this specification rather than quietly preparing it.
    """
    import sample_rag.retriever as module

    assert imported_roots(module) == {"math", "re", "collections", "dataclasses"}
    assert imported_modules(module) == {"math", "re", "collections", "dataclasses"}

    declared = {
        node.name
        for node in ast.walk(ast.parse(inspect.getsource(module)))
        if isinstance(node, ast.FunctionDef)
    }

    for barred in (
        "rrf",
        "reciprocal_rank_fusion",
        "fuse",
        "fusion",
        "hybrid",
        "rerank",
        "reranking",
        "normalize_scores",
        "expand_query",
        "rewrite_query",
        "embed",
        "query_vector",
        "generate",
    ):
        assert barred not in declared, f"{barred} is out of scope for Sprint M2.03"


def test_m203_the_semantic_route_is_untouched_by_the_lexical_one():
    """Only the architecture's own dependent reaches `retriever`, and BM25 stayed here.

    Stated over the package by glob, mirroring
    `tests/test_vector_index.py::test_m201b_no_other_pipeline_module_imports_faiss`,
    so a module added later is covered without anyone remembering to add it. Two
    directions in one specification.

    **Who may reach the lexical route:** `generator.py` alone, and it did before
    this sprint — `docs/architecture.md` §5 gives `Generator` the dependency
    *Retriever*, and what it imports is the `RetrievalResult` contract, not the
    scorer. An allowlist rather than a denylist, so a vector module reaching the
    lexical route fails here whether or not anyone thought to forbid it.

    **Where BM25 may live:** `retriever.py` alone. A second copy of the ranking
    function in `vector_index.py` or `vector_runtime.py` would be a second
    lexical route, and fusing the two is **M2-04**'s work rather than a thing to
    grow inside the semantic route.

    Stated over **declared names** rather than over raw source text, deliberately.
    A module may legitimately *mention* BM25 in a comment — `generator.py` does,
    to explain why its own stub marker no longer mirrors the retrieval one — and a
    substring check would have made that prose a failure while still missing a
    scorer declared under any other name.
    """
    import sample_rag.retriever

    package_root = pathlib.Path(sample_rag.retriever.__file__).parent

    borrowers, duplicates = [], []
    for path in sorted(package_root.glob("*.py")):
        if path.name == "retriever.py":
            continue

        module = importlib.import_module(f"sample_rag.{path.stem}")
        if "sample_rag.retriever" in imported_modules(module):
            borrowers.append(path.name)
        if any("bm25" in name.lower() for name in declared_names(module)):
            duplicates.append(path.name)

    assert borrowers == ["generator.py"], f"the lexical scorer is reached from: {borrowers}"
    assert duplicates == [], f"BM25 is declared outside the lexical route in: {duplicates}"


def test_m203_no_bm25_dependency_was_added(repository_root):
    """`requirements.txt` is unchanged — BM25 is standard-library arithmetic.

    `math.log` and `collections.Counter` are the whole of it. A BM25 package
    would add a dependency for a formula the repository can state in six lines,
    and `docs/architecture.md` §10's *"minimal dependencies"* decision is
    binding. Asserted rather than described, so adding `rank_bm25` or an
    equivalent later is a visible failure.
    """
    requirements = (repository_root / "requirements.txt").read_text(encoding="utf-8").lower()

    for barred in ("rank_bm25", "rank-bm25", "bm25", "whoosh", "elasticsearch", "lucene"):
        assert barred not in requirements
