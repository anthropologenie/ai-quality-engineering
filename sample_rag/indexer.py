"""The Index stage — `Indexer` and the `Index` it produces.

Sprint 1B.1: implements register capability **1B-03**, the Index Layer's
`Indexer` component.

`docs/architecture.md` §5 freezes the interface — `Indexer.index(chunks:
List[Chunk]) -> Index`, dependency `Chunker`, *"**1B** — deterministic
placeholder vectors"*. `docs/roadmap.md` §1 states what building it settles:
*"That order is Chunking → Indexing → Retrieval; the repository executed
Retrieval (Sprint P3.3.1) while Indexing was never built. Milestone 1B builds
the missing stage."*

Until this module, the ALTM Index stage had no component.
`docs/DEFERRED_ITEMS_REGISTER.md` **1B-03** records it as *"An entire build
item with **no owning sprint**"*, and `docs/altm.md` §12 was qualified at
Sprint P3.7.4 to say the stage was exercised *"only in part"* for exactly this
reason.

Read-only, and structurally so
-------------------------------
`Indexer` is constructed over an already-loaded chunk collection and performs
no filesystem or network I/O at all — the same shape `sample_rag/retriever.py`
adopted, and for the same two reasons: no indexing path can reach a repository
artifact to modify it, and `sample_rag/` stays free of any import from
`scripts/`, the direction `docs/architecture.md` §6 bars.

**No `Index` artifact is persisted.** No repository authority defines one:
`docs/architecture.md` §6's repository structure lists no index file, and §5
describes `Index` as the Indexer's return value rather than an artifact. The
Index is built on demand from the Chunk Corpus, exactly as the `Retriever` is
constructed on demand from it.

On `List[Chunk]` and what the runtime actually carries
-------------------------------------------------------
`docs/architecture.md` §5 names the parameter `List[Chunk]`, the contract
entity `docs/CHUNK_CONTRACT.md` §8 defines. The value that reaches this stage
at runtime is that entity's **serialized form** — the mapping loaded from
`sample_rag/chunks.json` — because `scripts/build_chunks.py` persists chunks
between the Chunk stage and everything downstream.

This module therefore reads `chunk["id"]` and `chunk["text"]`, which is the
convention `sample_rag/retriever.py` already established against the same
collection. It is existing repository practice, not a new interpretation, and
is recorded in the Sprint 1B.1 evidence as an implementation observation.

Criterion **A-5** — *"Zero imports of any embedding, vector-store, or
LLM-evaluation library"* — remains binding throughout Milestone 1B
(`docs/DEFERRED_ITEMS_REGISTER.md` §3 exit condition). This module imports
`dataclasses` and `sample_rag.embedding`, and nothing else. **That is still
true after Sprint M2.01A**: the embedding library is imported by the seam
module alone, and the Index stage reaches it only through
`sample_rag.embedding` — so the A-5 transition is confined to one file rather
than spreading across the Index Layer.

Sprint M2.01A — real embeddings, behind the same interface
------------------------------------------------------------
Register capability **M2-01**. This module changes in exactly one substantive
way: the default `EmbeddingProvider` becomes `BGEEmbeddingProvider`, so the
Index over the committed Chunk Corpus holds real semantic vectors rather than
placeholders. `Indexer.index`'s signature, its coverage guarantee, its purity
and `Index`'s field set are all unchanged — which is what
`docs/MILESTONE_1A.md` criterion A-1 predicted would be possible: *"a stub
implementation can be replaced without changing calling code."*

**No index artifact is introduced by that change.** The paragraph above still
holds: the Index is built on demand and persisted nowhere, and no repository
authority defines an index or embedding artifact. Sprint M2.01A implements a
provider, not a store — `docs/DEFERRED_ITEMS_REGISTER.md` **M2-02** owns
persistence, and `sample_rag/vector_store.py` remains interface-only.
"""

from dataclasses import dataclass, field

from sample_rag.embedding import (
    EMBEDDING_DIMENSION,
    BGEEmbeddingProvider,
)


@dataclass(frozen=True)
class Index:
    """The lookup structure `docs/architecture.md` §5 names as `Indexer`'s output.

    Fields
    ------
    `vectors` — chunk id to vector. Keyed on `chunks[].id`, the
    identity `docs/CHUNK_CONTRACT.md` §17 makes globally unique and derives
    from position, so a chunk's index entry cannot collide with another's.

    `dimension` — the width every vector in `vectors` carries. Recorded rather
    than recomputed on read, so a consumer can assert the shape without
    iterating the collection.

    `stub` — whether this Index holds placeholder values. The marker follows
    the `RetrievalResult` precedent frozen by `docs/MILESTONE_1A.md` build item
    4, whose `diagnostics["stub"] is True` exists so *"the pytest suite [can]
    assert on structure **and** semantics now"*. It is what lets a
    specification state what kind of values this Index holds, rather than
    inferring it from the vectors' provenance.

    It read `True` throughout Milestone 1B and reads `False` from Sprint
    M2.01A, because the default provider now embeds for real. The field is not
    removed: a marker that only ever says one thing cannot distinguish an
    Index built over the stand-in from one built over the model, and both are
    constructible today.

    A mutable `dict` on a frozen dataclass mirrors `RetrievalResult`'s mutable
    containers, recorded as an accepted limitation at
    `docs/DEFERRED_ITEMS_REGISTER.md` **NA-04**. It is the existing repository
    disposition, adopted here rather than diverged from.
    """

    vectors: dict = field(default_factory=dict)
    dimension: int = EMBEDDING_DIMENSION
    stub: bool = False

    def covers(self, chunk_id: str) -> bool:
        """Whether `chunk_id` has a representation in this Index.

        The predicate `docs/MILESTONE_1A.md` build item 2's Index Coverage
        Validation clause is stated against — *"every chunk produced during
        indexing has a deterministic placeholder representation behind the
        `EmbeddingProvider` interface"*. The clause's *coverage* claim is what
        it validates, and coverage is indifferent to what fills the seam: from
        Sprint M2.01A the representation is a real embedding, and the property
        being checked is the one it always was. It is also the predicate which
        `docs/DATA_QUALITY_VALIDATION_PLAN.md` §8.1 names as DQ-7's failure
        condition in its negative form.

        Exposed as a method so the Data Quality Validation layer asserts
        coverage through the Index's own vocabulary rather than reaching into
        `vectors` and restating what membership means.
        """
        return chunk_id in self.vectors


class Indexer:
    """Builds a lookup structure over chunks.

    `docs/architecture.md` §5: `Indexer.index(chunks: List[Chunk]) -> Index`.
    Pure in the sense this repository requires — no filesystem or network I/O
    of its own, no shared mutable state, and a function of its arguments and
    its provider alone.

    The `EmbeddingProvider` is injected, **defaulting to `BGEEmbeddingProvider`
    from Sprint M2.01A** and to the deterministic stand-in before it. That
    substitution is the whole of what this module changed at Milestone 2A, and
    it is what `docs/MILESTONE_1A.md` criterion A-1 meant by *"a stub
    implementation can be replaced without changing calling code"* — register
    **M2-01**'s provider is supplied here, and no calling code changed.

    One consequence is stated rather than left to be discovered: with the real
    provider, `index` loads a model on first use, so it is no longer free and
    no longer offline. `sample_rag/embedding.py` owns that cost and its
    failure mode; this stage does not catch or re-interpret it, because a
    missing model is not an indexing defect.
    """

    def __init__(self, embedding_provider=None):
        self._embedding_provider = embedding_provider or BGEEmbeddingProvider()

    def index(self, chunks: list) -> Index:
        """Build the `Index` over `chunks`.

        Every chunk receives a representation — the coverage property DQ-7
        validates over the committed corpus. No chunk is filtered, sampled, or
        skipped: a chunk absent from the Index is precisely the failure
        `docs/DATA_QUALITY_VALIDATION_PLAN.md` §8.1 defines DQ-7 as detecting,
        so this stage must not be the thing that produces it.

        `dimension` is read from the first vector rather than assumed, so the
        provider in use records *its* width — the property that let Sprint
        M2.01A move from a 16-component placeholder to a 384-component
        embedding without this line changing.

        An empty collection legally yields an empty Index —
        `docs/CHUNK_CONTRACT.md` §11's *"zero or more"* cardinality reaches
        this stage as a corpus that produced no chunks, and that is not a
        failure here any more than it is there. With no vector to measure, the
        width and the `stub` marker are read from the provider's own
        declarations, defensively: `docs/architecture.md` §7 freezes
        `EmbeddingProvider` at a single `embed` method, so neither attribute
        can be required of a provider, and a foreign one that declares neither
        still indexes.
        """
        vectors = {
            chunk["id"]: self._embedding_provider.embed(chunk["text"]) for chunk in chunks
        }

        declared_dimension = getattr(
            self._embedding_provider, "dimension", EMBEDDING_DIMENSION
        )
        dimension = len(next(iter(vectors.values()))) if vectors else declared_dimension

        return Index(
            vectors=vectors,
            dimension=dimension,
            stub=getattr(self._embedding_provider, "placeholder", False),
        )
