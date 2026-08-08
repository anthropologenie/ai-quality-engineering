"""The runtime lifecycle around the persistent vector index.

Sprint M2.01C: implements the **query/protocol completion stage** of register
capability **M2-02**, under Repository Owner rulings **RO-08** (Decision 2 —
`query(vector, top_k) -> list[str]` and the query-time nearest-neighbour
behaviour) and **RO-09** (the derived-artifact policy and the lifecycle this
module owns), both at `docs/DEFERRED_ITEMS_REGISTER.md` §4.1 and §4.2.

**M2-02 is not discharged by this sprint.** The `VectorStore` Protocol has two
methods; `upsert`'s operational semantics are not established by any repository
authority, and `sample_rag/vector_index.py`'s module docstring records why the
frozen signature cannot carry them. Query is authorized independently and is
implemented; `upsert` is not invented, not stubbed, and not faked.

What RO-09 assigns to this module
-----------------------------------
RO-09 item 8 lists the lifecycle in order, and this module is that list::

    canonical corpus
          |
          v
    expected identity  ................  identity_for(...), from the corpus
          |
          v
    runtime artifact exists? ---- no --> rebuild -> save
          |
         yes
          |
          v
    load + cross-validate ------- fails -> rebuild -> save   (corrupt / partial)
          |
          v
    compatibility validation ---- stale -> rebuild -> save
          |
        current
          |
          v
    query

**The canonical corpus is the source of truth** (RO-09 item 6). The artifact
below it is derived and rebuildable, so every failure to load or validate one
has the same remedy — rebuild — and none of them is an error a caller must
handle. That is why this module catches `VectorIndexPersistenceError` and
`VectorIndexCompatibilityError` and rebuilds, rather than propagating them: at
this layer they are not failures, they are the *reason* a rebuild is needed.
Both exceptions still reach a caller who uses `sample_rag/vector_index.py`
directly, which is where they mean what they always meant.

Where the artifact lives
-------------------------
`VECTOR_INDEX_ROOT` — `sample_rag/vector_index/`, the constant Sprint M2.01B
named. RO-09 item 9 prescribes no location and leaves it to this sprint;
choosing the path already declared, rather than a second one, is what keeps the
repository with one runtime location instead of two. It is deterministic
(derived from the module's own path, not from a working directory, an
environment variable or a flag), discoverable (one constant, imported by both
modules), and reproducible (a rebuild writes the same two filenames there).

**Nothing under it is committed.** RO-09 items 3–5 make the FAISS binary and
its generated metadata derived runtime state rather than repository source, and
`.gitignore` carries the rule that expresses it — the question RO-09's closing
section explicitly reserved for this sprint, *"once the location exists"*. The
runtime location is therefore **not** a second source of truth: it holds only
what the canonical corpus can regenerate, and a caller who deletes it loses
nothing but the time to rebuild.

Why the corpus is injected rather than loaded here
----------------------------------------------------
`docs/architecture.md` §6 bars `sample_rag/` from importing `scripts/`, and the
Chunk Corpus and Knowledge Manifest are `scripts/build_chunks.py`'s and
`scripts/build_manifest.py`'s artifacts. So this module is **handed** its
chunks and documents, exactly as `sample_rag/retriever.py` is handed chunks and
`FaissVectorIndex.build` is handed both. Loading them here would either cross
that direction or duplicate corpus parsing inside the query layer — the
duplication `docs/ENGINEERING_TRACEABILITY_REGISTER.md` §5 rates **High** risk,
and the reason `scripts/run_retrieval.py` exists as the composition point for
the lexical route.

The rebuild path therefore introduces no corpus-loading architecture of its
own. It reuses `Indexer` for embedding and `FaissVectorIndex.build` for
construction, so a rebuilt artifact is built by the same code that built the
first one and preserves chunk order, chunk ids, embedding configuration, index
configuration and metadata identity by construction rather than by agreement.

Criterion A-5
--------------
This module imports **no** vector-store library and **no** embedding library.
It reaches FAISS only through `sample_rag/vector_index.py` and the model only
through `sample_rag/embedding.py`, so both standing A-5 exceptions stay exactly
one library in exactly one module — which
`tests/test_vector_index.py::test_m201b_no_other_pipeline_module_imports_faiss`
and its embedding counterpart in `tests/test_indexer.py` check by glob, and
therefore already cover this file.
"""

from sample_rag.embedding import BGEEmbeddingProvider
from sample_rag.indexer import Indexer
from sample_rag.vector_index import (
    VECTOR_INDEX_ROOT,
    FaissVectorIndex,
    VectorIndexCompatibilityError,
    VectorIndexPersistenceError,
    identity_for,
)

# What the lifecycle did to reach a usable index. A **report rather than a
# bool**, the shape `VectorIndexIdentity.mismatches` and every W6 predicate in
# `tests/test_data_quality.py` already use: a caller — or a specification —
# that learns *why* an index was rebuilt can act on it, where "an index exists"
# alone says nothing about whether the corpus moved.
LOADED = "loaded"
REBUILT_ABSENT = "rebuilt — no usable artifact was present"
REBUILT_STALE = "rebuilt — the persisted artifact did not match the corpus"


class VectorIndexRuntime:
    """Locates, validates, rebuilds and loads the vector index, then queries it.

    Constructed over an already-loaded corpus, like `Retriever` and `Indexer`
    before it, and read-only with respect to every repository artifact except
    the derived index directory it owns.

    One instance holds one index once it has resolved one — ordinary runtime
    state, the same shape `Retriever` holds its chunk collection in. It is not
    a cache in the sense `docs/DATA_QUALITY_VALIDATION_PLAN.md` §7.5 bars and
    not a test accelerator: nothing is shared between instances, no state
    outlives the object, and a new runtime repeats discovery, validation and
    any rebuild in full. Re-resolving the artifact on every query would reload
    a FAISS binary from disk per query, which is a property of *this* module's
    laziness rather than anything the repository asserts.
    """

    def __init__(self, chunks, documents, embedding_provider=None, directory=None):
        """Bind the runtime to a corpus, a provider and an artifact directory.

        `chunks` is the Chunk Corpus in committed order — that order *is* the
        vector → chunk mapping, per `FaissVectorIndex.build`. `documents` is the
        Knowledge Manifest's `documents[]`, read for `id` and `hash` alone.

        The provider defaults to `BGEEmbeddingProvider`, matching
        `sample_rag/indexer.py`'s own default from Sprint M2.01A, so the runtime
        embeds documents and queries with the repository's elected model unless
        a specification names another. **The same provider instance serves
        both**, which is what makes the query vector commensurable with the
        stored ones rather than merely the same width.

        `directory` defaults to `VECTOR_INDEX_ROOT`. It is a parameter so that a
        specification can point the lifecycle at a temporary directory; it is
        not a configuration surface, and no repository path passes anything else.
        """
        self._chunks = list(chunks)
        self._documents = list(documents)
        self._provider = embedding_provider or BGEEmbeddingProvider()
        self._directory = VECTOR_INDEX_ROOT if directory is None else directory
        self._index = None
        self._disposition = None
        self._rebuild_signals = []

    @property
    def directory(self):
        """Where this runtime reads and writes its derived artifact."""
        return self._directory

    @property
    def disposition(self) -> str:
        """`LOADED`, `REBUILT_ABSENT` or `REBUILT_STALE` — or `None` before use.

        What the lifecycle did, recorded rather than inferred. Without it, a
        rebuild and a load are indistinguishable from outside: both end in a
        usable index, and only one of them means the persisted artifact was
        wrong.
        """
        return self._disposition

    @property
    def rebuild_signals(self) -> list:
        """The identity signals that forced a rebuild, when one was forced.

        Empty unless `disposition` is `REBUILT_STALE`: an absent or unreadable
        artifact has no identity to differ, so nothing can be named for it.
        Carries `VectorIndexIdentity.mismatches`' output unchanged, so the
        vocabulary is the artifact's own.
        """
        return list(self._rebuild_signals)

    def expected_identity(self):
        """The identity the bound corpus and provider *should* produce.

        The intended state every persisted artifact is measured against, built
        through `identity_for` — the same function `FaissVectorIndex.build`
        derives an artifact's own identity from, so the two cannot drift apart.

        **No text is embedded to compute it.** `identity_for` reads only
        `dimension` from the Index, and the width is a property the provider
        declares, so an empty Index carries everything this call needs.
        `Indexer(...).index([])` is used to read it rather than `getattr` here,
        because that stage already owns the defensive read for a provider that
        declares no width (`docs/architecture.md` §7 freezes `EmbeddingProvider`
        at one method), and duplicating it would be a second answer to one
        question.

        The cost matters: staleness is checked on every construction, and a
        check that embedded the corpus would cost exactly as much as the
        rebuild it exists to avoid.
        """
        declared_width = Indexer(self._provider).index([])

        return identity_for(
            declared_width, self._chunks, self._documents, self._provider
        )

    def index(self) -> FaissVectorIndex:
        """Return a `FaissVectorIndex` that identifies the bound corpus.

        The whole of RO-09 item 8, in the order it states, resolved once per
        instance. The returned index has either been loaded and validated, or
        rebuilt from the canonical corpus and persisted — never returned
        unvalidated, and never returned stale.
        """
        if self._index is None:
            self._index = self._resolve()

        return self._index

    def _resolve(self) -> FaissVectorIndex:
        """Discover, validate and if necessary rebuild the artifact.

        Two failure classes, one remedy. `VectorIndexPersistenceError` covers a
        directory that was never written, a half-written pair, an unparseable
        metadata file, a FAISS binary FAISS refuses, and two files that
        disagree with each other. `VectorIndexCompatibilityError` covers an
        intact artifact built over other inputs. **Both are recoverable here
        and only here**, because RO-09 items 1–2 make the artifact derived and
        rebuildable: there is no state to lose and nothing for a caller to
        decide.

        The exceptions are caught by their specific classes rather than by a
        bare `except`, so a genuine defect in this repository's own code — a
        `TypeError`, an `AttributeError` — still surfaces as a defect instead
        of being absorbed into an infinite willingness to rebuild.
        """
        expected = self.expected_identity()

        try:
            candidate = FaissVectorIndex.load(self._directory)
        except VectorIndexPersistenceError:
            self._disposition = REBUILT_ABSENT
            self._rebuild_signals = []
            return self._rebuild()

        differences = candidate.identity.mismatches(expected)
        if differences:
            self._disposition = REBUILT_STALE
            self._rebuild_signals = differences
            return self._rebuild()

        self._disposition = LOADED
        self._rebuild_signals = []
        return candidate

    def _rebuild(self) -> FaissVectorIndex:
        """Build the artifact from the canonical corpus and persist it.

        Embedding, construction and persistence are all the existing stages —
        `Indexer.index`, `FaissVectorIndex.build`, `FaissVectorIndex.save` — so
        a rebuilt index preserves chunk order, chunk ids, embedding
        configuration, index configuration and metadata identity because it is
        produced by the same code as the original, not because this function
        reproduces them.

        It is persisted immediately. A rebuild that stayed in memory would
        leave the next process to rebuild again, which is the cost the artifact
        exists to remove.
        """
        index = Indexer(self._provider).index(self._chunks)
        rebuilt = FaissVectorIndex.build(
            index, self._chunks, self._documents, self._provider
        )
        rebuilt.save(self._directory)

        return rebuilt

    def query(self, vector: list[float], top_k: int) -> list[str]:
        """Return the ids of the `top_k` nearest chunks to `vector`.

        `docs/architecture.md` §7's shape, delegated unchanged to
        `FaissVectorIndex.query`, which owns the nearest-neighbour behaviour and
        the ordinal → chunk-id mapping. This method's own contribution is the
        lifecycle: the index it queries is guaranteed to identify the bound
        corpus, because `index()` resolved it.
        """
        return self.index().query(vector, top_k)

    def query_text(self, text: str, top_k: int) -> list[str]:
        """Embed `text` and return the ids of the `top_k` nearest chunks.

        The query-side entry point, and the whole of the retrieval path this
        sprint introduces::

            text -> EmbeddingProvider.embed -> vector -> query -> chunk ids

        **The same provider embeds the query and the documents.** Not merely
        the same model id: the same object, the one this runtime built the index
        with, so the query vector is produced by the checkpoint and revision the
        index's own identity records.

        **No query prefix, instruction or transformation is applied.** BGE
        publishes an asymmetric retrieval prefix for the query side, and
        `sample_rag/embedding.py` records that it is deliberately not applied
        and that **M2-02** / **M2-04** own the question. No repository authority
        establishes one, applying it would change what a query vector *is*
        relative to every stored vector, and RO-08 and RO-09 authorize no such
        decision. It is reported as an open question rather than taken here —
        `docs/M2.01C_Semantic_Query_Foundation_Report.md` §17, finding F-2.

        There is no lexical route, no structured route and no fusion. A caller
        wanting those is asking for **M2-03**, **M2-04** or **M2-05**, none of
        which this sprint may implement.

        The index is resolved **before** the query is embedded. A rebuild
        embeds the whole corpus, so doing it the other way round would spend an
        embedding on a query that a failed lifecycle might never use, and would
        interleave the query's embedding into the middle of the corpus's.
        """
        index = self.index()

        return index.query(self._provider.embed(text), top_k)
