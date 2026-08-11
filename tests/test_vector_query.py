"""Specification Family — semantic query and the vector-index runtime lifecycle.

Sprint M2.01C specifies the **query/protocol completion stage** of register
capability **M2-02**, under Repository Owner rulings **RO-08** (Decision 2) and
**RO-09** (`docs/DEFERRED_ITEMS_REGISTER.md` §4.1, §4.2).

**M2-02 is not discharged by this sprint, and no specification here claims it
is.** `test_m201c_no_component_satisfies_the_vector_store_protocol` at the foot
of this file states the remaining gap — `upsert` — and states it as the reason,
not as an omission.

Scope boundary against the sprints on either side
---------------------------------------------------
`tests/test_indexer.py` specifies the `EmbeddingProvider` seam, the
`VectorStore` **Protocol** and the in-memory `Index`. `tests/test_vector_index.py`
specifies how an `Index` is persisted, identified, reloaded and validated. This
file specifies what happens when a **query vector** meets that artifact, and the
runtime lifecycle RO-09 item 8 places around it.

`sample_rag/vector_store.py` is untouched by this sprint. The Protocol is
frozen, and `test_m201c_the_frozen_protocol_is_unchanged` re-states that from
this sprint's side.

What is deliberately absent
----------------------------
No BM25, no lexical scoring change, no Reciprocal Rank Fusion, no hybrid
ranking, no score fusion, no reranking, no query expansion or rewriting, no
generation, no evaluation tooling and no JobOps. Those are **M2-03**, **M2-04**,
**M2-05**, **M2-06**, **M2-07**, **M2-08** and Milestone 2B, and
`test_m201c_the_query_path_exposes_no_fusion_or_lexical_surface` is what keeps
this sprint on its side of that line.

Behaviour, not artefacts
-------------------------
Following `tests/conftest.py` and the whole 1B / 2A precedent, no specification
here freezes a vector literal, a similarity score, or a FAISS binary digest.
Semantic behaviour is stated as **relative ordering** — the discipline
`tests/test_indexer.py::test_m201_related_text_embeds_nearer_than_unrelated_text`
set at Sprint M2.01A — because a threshold would specify one checkpoint's
calibration rather than the repository's claim.

Where these specifications write
---------------------------------
Every one that persists an artifact writes to `tmp_path`. **Nothing writes to
`VECTOR_INDEX_ROOT`**, the real runtime location, which is derived state under
RO-09 and is not a place a specification may leave residue.
"""

import ast
import inspect
import json
import subprocess

import pytest

from sample_rag.embedding import (
    EMBEDDING_DIMENSION,
    EMBEDDING_MODEL_ID,
    EMBEDDING_MODEL_REVISION,
    PLACEHOLDER_DIMENSION,
    BGEEmbeddingProvider,
    DeterministicEmbeddingProvider,
)
from sample_rag.indexer import Indexer
from sample_rag.vector_index import (
    FAISS_INDEX_FILENAME,
    INDEX_METADATA_FILENAME,
    VECTOR_INDEX_ROOT,
    FaissVectorIndex,
    VectorIndexCompatibilityError,
    identity_for,
)
from sample_rag.vector_runtime import (
    LOADED,
    REBUILT_ABSENT,
    REBUILT_STALE,
    VectorIndexRuntime,
)

# Three chunks whose *placeholder* vectors are unrelated to their meaning — the
# stand-in is a digest. Query semantics, ordering, top-k and the ordinal mapping
# are all properties of FAISS and of the mapping, not of the model, so they are
# specified against the stand-in and cost no checkpoint. The specifications
# whose subject is *meaning* use the real model, and say so.
CHUNKS = [
    {"id": "c0", "text": "alpha"},
    {"id": "c1", "text": "beta"},
    {"id": "c2", "text": "gamma"},
]
DOCUMENTS = [{"id": "d0", "hash": "0" * 64}, {"id": "d1", "hash": "1" * 64}]

# A controlled semantic corpus: three chunks from three plainly different
# subjects, one of them resume-shaped. Wide by construction, for the reason
# Sprint M2.01A gives — a specification should fail on a broken integration,
# not on ordinary model variation.
RESUME_CHUNK = {
    "id": "s0",
    "text": (
        "Led a cross-functional QA team of five engineers, owning test strategy "
        "and stakeholder communication across releases."
    ),
}
WEATHER_CHUNK = {
    "id": "s1",
    "text": "Rainfall in the coastal region peaked during the monsoon season that year.",
}
PIPELINE_CHUNK = {
    "id": "s2",
    "text": "Built ETL data pipelines in Python for warehouse ingestion and reconciliation.",
}
SEMANTIC_CHUNKS = [RESUME_CHUNK, WEATHER_CHUNK, PIPELINE_CHUNK]


def built(chunks=None, documents=None, provider=None):
    """Build a `FaissVectorIndex` over the given material."""
    chunks = CHUNKS if chunks is None else chunks
    documents = DOCUMENTS if documents is None else documents
    provider = provider or DeterministicEmbeddingProvider()

    index = Indexer(provider).index(chunks)

    return FaissVectorIndex.build(index, chunks, documents, provider)


def expected_identity(chunks=None, documents=None, provider=None):
    """The identity the given inputs would produce."""
    chunks = CHUNKS if chunks is None else chunks
    documents = DOCUMENTS if documents is None else documents
    provider = provider or DeterministicEmbeddingProvider()

    return identity_for(Indexer(provider).index(chunks), chunks, documents, provider)


class RecordingProvider:
    """The stand-in, plus a record of every text it was asked to embed.

    Structurally an `EmbeddingProvider`, like every other provider in this
    repository — conformance by shape, per criterion A-1. The record is what
    lets a specification state facts about the *query side* of embedding: how
    many texts were embedded, and exactly what text reached the model.
    """

    dimension = PLACEHOLDER_DIMENSION
    placeholder = True

    def __init__(self, model_id="", revision=""):
        self.embedded = []
        self.model_id = model_id
        self.revision = revision

    def embed(self, text: str) -> list[float]:
        self.embedded.append(text)
        return DeterministicEmbeddingProvider().embed(text)


class NarrowProvider(DeterministicEmbeddingProvider):
    """A provider of a different width, for the dimension-compatibility case."""

    dimension = 8

    def embed(self, text: str) -> list[float]:
        return super().embed(text)[: self.dimension]


# --- the query contract ------------------------------------------------------


def test_m201c_query_returns_the_chunk_id_of_the_nearest_stored_vector():
    """M2-02 / M2.01C — the capability itself, in its smallest form.

    `docs/architecture.md` §7 declares `query(vector, top_k) -> list[str]` and
    `sample_rag/vector_store.py` states what those strings are — *"the ids of
    the `top_k` nearest stored vectors"*. Querying with a vector the index
    itself stores must return that vector's own chunk first: it is its own
    nearest neighbour, and no ranking rule can put anything ahead of it.
    """
    index = built()

    assert index.query(index.reconstruct(1), 1) == ["c1"]


def test_m201c_the_ordinal_mapping_is_the_one_the_identity_records():
    """M2-02 / M2.01C — **ordinal → chunk_id**, at every position.

    FAISS answers with ordinals; the answer only means something because
    `identity.chunk_ids[ordinal]` says which chunk sits there. Asserted for
    every position rather than one, so an off-by-one or a reversed mapping
    fails here instead of surfacing as a plausible-looking wrong retrieval.
    """
    index = built()

    for position, chunk_id in enumerate(index.identity.chunk_ids):
        assert index.query(index.reconstruct(position), 1) == [chunk_id]
        assert index.chunk_id_at(position) == chunk_id


def test_m201c_results_are_ordered_nearest_first():
    """M2-02 / M2.01C — result ordering follows FAISS's own similarity order.

    Stated as an ordering over *measured* similarity rather than against a
    frozen sequence: the query is placed nearer one stored vector than another
    by construction — it **is** one of them — so the vector it equals must rank
    ahead of the rest, and the full result must be a permutation of the corpus
    with that chunk at the head.

    No re-ranking, weighting or fusion is applied to FAISS's order anywhere in
    the path, which is what makes this assertion a statement about the index
    rather than about a scoring function this sprint may not have.
    """
    index = built()

    for position, chunk_id in enumerate(index.identity.chunk_ids):
        results = index.query(index.reconstruct(position), len(CHUNKS))

        assert results[0] == chunk_id
        assert sorted(results) == sorted(chunk["id"] for chunk in CHUNKS)


def test_m201c_top_k_smaller_than_the_corpus_returns_exactly_top_k():
    """M2-02 / M2.01C — top-k selection, under-requesting.

    The ordinary case: fewer results than the index holds, and they are the
    head of the same ordering a larger `top_k` would produce. A `top_k` that
    changed *which* neighbours were returned rather than only *how many* would
    mean the ordering depended on the request.
    """
    index = built()
    vector = index.reconstruct(0)

    assert index.query(vector, 2) == index.query(vector, len(CHUNKS))[:2]
    assert len(index.query(vector, 2)) == 2


def test_m201c_top_k_equal_to_the_corpus_returns_every_chunk_once():
    """M2-02 / M2.01C — top-k selection, exactly saturating.

    Every stored chunk, each exactly once. Duplicate ids here would mean either
    FAISS returned an ordinal twice or the mapping collapsed two positions onto
    one chunk — both silent corruptions of attribution.
    """
    index = built()

    results = index.query(index.reconstruct(0), len(CHUNKS))

    assert len(results) == len(CHUNKS)
    assert len(set(results)) == len(CHUNKS)


def test_m201c_top_k_larger_than_the_corpus_returns_only_what_is_stored():
    """M2-02 / M2.01C — top-k selection, over-requesting.

    FAISS pads a short result with the ordinal `-1`. Those slots must be
    dropped, not mapped: `chunk_ids[-1]` is the *last* chunk in Python, so a
    naive mapping would return it repeatedly as if it were a neighbour. This
    specification is the reason the padding is filtered rather than assumed
    absent.
    """
    index = built()

    results = index.query(index.reconstruct(0), len(CHUNKS) + 50)

    assert len(results) == len(CHUNKS)
    assert set(results) == {chunk["id"] for chunk in CHUNKS}


def test_m201c_a_non_positive_top_k_returns_nothing():
    """M2-02 / M2.01C — `top_k <= 0`.

    *"The ids of the `top_k` nearest"* for zero or fewer is no ids. Answered
    rather than raised, because no repository authority defines an error for
    it and inventing one would add a failure surface the contract does not
    describe; the nearest existing behaviour, `sample_rag/retriever.py`'s
    slice-based top-k, is empty at zero too.

    **An engineering decision, recorded as one** — see
    `docs/M2.01C_Semantic_Query_Foundation_Report.md` §9. It is specified so
    that changing it is a visible decision rather than a silent drift.
    """
    index = built()
    vector = index.reconstruct(0)

    assert index.query(vector, 0) == []
    assert index.query(vector, -1) == []


def test_m201c_an_empty_index_returns_nothing():
    """M2-02 / M2.01C — a corpus that produced no chunks.

    `docs/CHUNK_CONTRACT.md` §11's *"zero or more"* cardinality reaches this
    stage as an index with nothing in it, and `sample_rag/indexer.py` already
    treats that as legal rather than as a failure. Query answers it the same
    way: no stored vectors, therefore no nearest ones.
    """
    provider = DeterministicEmbeddingProvider()
    index = FaissVectorIndex.build(
        Indexer(provider).index([]), [], DOCUMENTS, provider
    )

    assert index.vector_count == 0
    assert index.query([0.0] * PLACEHOLDER_DIMENSION, 5) == []


def test_m201c_a_query_vector_of_the_wrong_width_is_rejected():
    """M2-02 / M2.01C — malformed query dimensionality.

    Raised as `VectorIndexCompatibilityError`, the exception that already means
    *this index does not identify the inputs it is being used for*. `dimension`
    is one of RO-08 Decision 3's eight signals, and a 16-component query against
    a 384-component index is that same incompatibility arriving from the query
    side — so no new exception type is introduced for it.

    Checked before FAISS sees the vector, so the failure names the repository's
    fact rather than surfacing as a third-party assertion.
    """
    index = built()

    with pytest.raises(VectorIndexCompatibilityError, match="components wide"):
        index.query([0.0] * (PLACEHOLDER_DIMENSION + 1), 1)

    with pytest.raises(VectorIndexCompatibilityError):
        index.query([], 1)


def test_m201c_every_result_is_a_chunk_id_the_index_holds():
    """M2-02 / M2.01C — the result is chunk ids, and only chunk ids.

    `list[str]`, every element drawn from `identity.chunk_ids`. A result
    carrying a position, a score, or an id the index does not hold would
    satisfy the annotation while breaking the join `sample_rag/retriever.py`
    already ranks on and `docs/CHUNK_CONTRACT.md` §17 makes unique.
    """
    index = built()

    results = index.query(index.reconstruct(2), len(CHUNKS))

    assert all(isinstance(result, str) for result in results)
    assert set(results) <= set(index.identity.chunk_ids)


def test_m201c_query_exposes_no_similarity_score():
    """M2-02 / M2.01C — scores are deliberately hidden, not merely unused.

    FAISS returns distances alongside ordinals and this path discards them,
    because the frozen return type is `list[str]`. Publishing them would widen
    the contract, and the only consumer a score would have today is the rank
    fusion (**M2-04**) this sprint may not implement.

    Asserted as the absence of any non-string element, which is the observable
    form of the claim.
    """
    index = built()

    results = index.query(index.reconstruct(0), len(CHUNKS))

    assert results == [str(result) for result in results]
    assert not any(isinstance(result, (tuple, list, dict, float)) for result in results)


def test_m201c_query_matches_the_frozen_protocol_declaration():
    """M2-02 / M2.01C — the implementation did not redesign the seam.

    `docs/architecture.md` §7 and `sample_rag/vector_store.py` declare
    `query(self, vector: list[float], top_k: int) -> list[str]`. The
    implementation's signature is compared against the Protocol's own, so a
    renamed parameter or a widened return type fails here — which is the
    property criterion A-1's *"swappable"* rests on, and the reason M2.01C had
    nothing to add to the seam to make the implementation fit.
    """
    from sample_rag.vector_store import VectorStore

    declared = inspect.signature(VectorStore.query)

    for implementation in (FaissVectorIndex.query, VectorIndexRuntime.query):
        assert inspect.signature(implementation) == declared


def test_m201c_a_loaded_index_answers_identically_to_the_one_in_memory(tmp_path):
    """M2-02 / M2.01C — persistence does not change what a query returns.

    The property that makes the artifact worth persisting at all: an index read
    back from disk must be the same retrieval instrument as the one that was
    written. Compared over every stored vector as a query, so a mis-ordered
    load or a shifted mapping fails rather than passing on one lucky case.
    """
    index = built()
    index.save(tmp_path)

    loaded = FaissVectorIndex.load(tmp_path)

    for position in range(len(CHUNKS)):
        vector = index.reconstruct(position)
        assert loaded.query(vector, len(CHUNKS)) == index.query(vector, len(CHUNKS))


# --- the runtime artifact lifecycle (RO-09 item 8) ---------------------------


def test_m201c_a_missing_artifact_is_rebuilt_and_persisted(tmp_path):
    """RO-09 item 8 — **exists-check → rebuild**.

    The artifact is derived and rebuildable (RO-09 items 1–2), so its absence
    is not an error a caller must handle: the canonical corpus is the source of
    truth and can produce it. The rebuild is persisted immediately, because a
    rebuild that stayed in memory would leave the next process to repeat it.
    """
    target = tmp_path / "vector_index"
    runtime = VectorIndexRuntime(CHUNKS, DOCUMENTS, DeterministicEmbeddingProvider(), target)

    index = runtime.index()

    assert runtime.disposition == REBUILT_ABSENT
    assert runtime.rebuild_signals == []
    assert index.vector_count == len(CHUNKS)
    assert sorted(path.name for path in target.iterdir()) == [
        FAISS_INDEX_FILENAME,
        INDEX_METADATA_FILENAME,
    ]


def test_m201c_a_current_artifact_is_loaded_rather_than_rebuilt(tmp_path):
    """RO-09 item 8 — **load**, when compatibility validation passes.

    The case the whole lifecycle exists for. A second runtime over the same
    corpus must reuse what the first wrote, or persistence would buy nothing.
    """
    provider = DeterministicEmbeddingProvider()
    VectorIndexRuntime(CHUNKS, DOCUMENTS, provider, tmp_path).index()

    second = VectorIndexRuntime(CHUNKS, DOCUMENTS, provider, tmp_path)
    index = second.index()

    assert second.disposition == LOADED
    assert second.rebuild_signals == []
    assert index.identity == expected_identity()


def test_m201c_a_chunk_content_change_forces_a_rebuild(tmp_path):
    """RO-09 item 8 — **stale-index detection**, on the RO-08 Decision 1 signal.

    Chunk *content* moved while the chunk ids, the chunk count and every
    document hash stayed identical — the drift no pre-existing repository
    identity could see, and the reason RO-08 Decision 1 was sought. The
    lifecycle must notice and rebuild, naming `chunk_fingerprint` as the cause.
    """
    provider = DeterministicEmbeddingProvider()
    VectorIndexRuntime(CHUNKS, DOCUMENTS, provider, tmp_path).index()

    rechunked = CHUNKS[:2] + [{"id": "c2", "text": "gamma delta"}]
    runtime = VectorIndexRuntime(rechunked, DOCUMENTS, provider, tmp_path)
    index = runtime.index()

    assert runtime.disposition == REBUILT_STALE
    assert runtime.rebuild_signals == ["chunk_fingerprint"]
    assert index.identity == expected_identity(chunks=rechunked)


def test_m201c_a_corpus_change_forces_a_rebuild(tmp_path):
    """RO-09 item 8 — stale detection on the existing document identity model.

    `documents[].hash` is the SHA-256 the Knowledge Manifest already carries and
    DQ-1 already validates; it is consumed here rather than re-derived.
    """
    provider = DeterministicEmbeddingProvider()
    VectorIndexRuntime(CHUNKS, DOCUMENTS, provider, tmp_path).index()

    moved = [{"id": "d0", "hash": "0" * 64}, {"id": "d1", "hash": "2" * 64}]
    runtime = VectorIndexRuntime(CHUNKS, moved, provider, tmp_path)
    runtime.index()

    assert runtime.disposition == REBUILT_STALE
    assert runtime.rebuild_signals == ["document_hashes"]


def test_m201c_an_embedding_model_change_forces_a_rebuild(tmp_path):
    """RO-09 item 8 — stale detection on embedding model identity.

    Vectors produced by a different model are not comparable with the query
    vectors a different model produces, so an index built under one and queried
    under another would return confident nonsense. `model_id` is what sees it.
    """
    VectorIndexRuntime(
        CHUNKS, DOCUMENTS, RecordingProvider(EMBEDDING_MODEL_ID, "r1"), tmp_path
    ).index()

    runtime = VectorIndexRuntime(
        CHUNKS, DOCUMENTS, RecordingProvider("some-other/model", "r1"), tmp_path
    )
    runtime.index()

    assert runtime.disposition == REBUILT_STALE
    assert runtime.rebuild_signals == ["model_id"]


def test_m201c_an_embedding_revision_change_forces_a_rebuild(tmp_path):
    """RO-09 item 8 — stale detection on the pinned checkpoint.

    The signal Sprint M2.01A pinned in code. The same model id at a different
    commit silently produces different vectors, which is exactly why
    `sample_rag/embedding.py` pins the revision rather than the branch.
    """
    VectorIndexRuntime(
        CHUNKS, DOCUMENTS, RecordingProvider(EMBEDDING_MODEL_ID, EMBEDDING_MODEL_REVISION), tmp_path
    ).index()

    runtime = VectorIndexRuntime(
        CHUNKS, DOCUMENTS, RecordingProvider(EMBEDDING_MODEL_ID, "0" * 40), tmp_path
    )
    runtime.index()

    assert runtime.disposition == REBUILT_STALE
    assert runtime.rebuild_signals == ["model_revision"]


def test_m201c_a_dimension_change_forces_a_rebuild(tmp_path):
    """RO-09 item 8 — stale detection on embedding width.

    An index whose vectors are not the width the provider now produces cannot
    be queried at all: `query` rejects a mismatched vector. Detecting the width
    at lifecycle time turns that hard failure into a rebuild.
    """
    VectorIndexRuntime(CHUNKS, DOCUMENTS, DeterministicEmbeddingProvider(), tmp_path).index()

    runtime = VectorIndexRuntime(CHUNKS, DOCUMENTS, NarrowProvider(), tmp_path)
    index = runtime.index()

    assert runtime.disposition == REBUILT_STALE
    assert runtime.rebuild_signals == ["dimension"]
    assert index.identity.dimension == NarrowProvider.dimension


def test_m201c_a_faiss_configuration_change_forces_a_rebuild(tmp_path, monkeypatch):
    """RO-09 item 8 — stale detection on *"relevant FAISS index configuration"*.

    RO-08 Decision 3 names the FAISS configuration as a compatibility signal.
    An artifact recorded under one index type is not interchangeable with one
    built under another, even over identical vectors, so the lifecycle must
    rebuild rather than reuse it.

    The persisted artifact is written under a substituted configuration and the
    runtime then meets it under the real one, which is the direction a
    configuration change actually arrives from.
    """
    import sample_rag.vector_index as module

    monkeypatch.setattr(module, "VECTOR_INDEX_TYPE", "IndexIVFFlat")
    built().save(tmp_path)
    monkeypatch.undo()

    runtime = VectorIndexRuntime(CHUNKS, DOCUMENTS, DeterministicEmbeddingProvider(), tmp_path)
    runtime.index()

    assert runtime.disposition == REBUILT_STALE
    assert runtime.rebuild_signals == ["index_type"]


def test_m201c_a_corrupt_artifact_is_rebuilt_rather_than_raised(tmp_path):
    """RO-09 item 8 — an unusable artifact has the same remedy as a missing one.

    A FAISS binary FAISS refuses, and a metadata file that is not JSON. Both are
    `VectorIndexPersistenceError` at the artifact layer, where they mean *this
    artifact cannot be trusted*; at the lifecycle layer they mean *rebuild*,
    because RO-09 items 1–2 leave nothing to lose by rebuilding.
    """
    provider = DeterministicEmbeddingProvider()
    VectorIndexRuntime(CHUNKS, DOCUMENTS, provider, tmp_path).index()
    (tmp_path / FAISS_INDEX_FILENAME).write_bytes(b"not a faiss index at all")

    runtime = VectorIndexRuntime(CHUNKS, DOCUMENTS, provider, tmp_path)

    assert runtime.index().vector_count == len(CHUNKS)
    assert runtime.disposition == REBUILT_ABSENT

    (tmp_path / INDEX_METADATA_FILENAME).write_text("{ not json", encoding="utf-8")
    second = VectorIndexRuntime(CHUNKS, DOCUMENTS, provider, tmp_path)

    assert second.index().vector_count == len(CHUNKS)
    assert second.disposition == REBUILT_ABSENT


def test_m201c_a_rebuilt_artifact_validates_against_the_corpus_that_forced_it(tmp_path):
    """RO-09 item 8 — rebuilding is a remedy, not a new kind of drift.

    After a stale rebuild the persisted artifact must satisfy the very
    validation that rejected its predecessor, and a third runtime over the same
    corpus must simply load it.
    """
    provider = DeterministicEmbeddingProvider()
    VectorIndexRuntime(CHUNKS, DOCUMENTS, provider, tmp_path).index()

    rechunked = CHUNKS[:2] + [{"id": "c2", "text": "gamma delta"}]
    VectorIndexRuntime(rechunked, DOCUMENTS, provider, tmp_path).index()

    persisted = FaissVectorIndex.load(tmp_path)
    persisted.validate(expected_identity(chunks=rechunked))

    third = VectorIndexRuntime(rechunked, DOCUMENTS, provider, tmp_path)
    third.index()

    assert third.disposition == LOADED


def test_m201c_a_rebuild_preserves_chunk_order_and_the_mapping(tmp_path):
    """RO-09 item 8 — what a rebuild must preserve.

    Chunk order, chunk ids, embedding configuration, index configuration and
    metadata identity. Preserved because the rebuild path calls the same
    `Indexer` and `FaissVectorIndex.build` the first build did, rather than
    reproducing their behaviour — so this specification checks a structural
    property, not a coincidence.
    """
    provider = DeterministicEmbeddingProvider()
    original = VectorIndexRuntime(CHUNKS, DOCUMENTS, provider, tmp_path).index()

    (tmp_path / FAISS_INDEX_FILENAME).unlink()
    rebuilt = VectorIndexRuntime(CHUNKS, DOCUMENTS, provider, tmp_path).index()

    assert rebuilt.identity == original.identity
    assert rebuilt.identity.chunk_ids == tuple(chunk["id"] for chunk in CHUNKS)
    assert [rebuilt.chunk_id_at(i) for i in range(len(CHUNKS))] == [
        original.chunk_id_at(i) for i in range(len(CHUNKS))
    ]


def test_m201c_the_runtime_queries_the_index_it_validated(tmp_path):
    """RO-09 item 8 — **expose the loaded index to the query path**.

    The lifecycle's whole purpose, stated as a retrieval fact: after the corpus
    moves, a query must answer from the *current* corpus. A runtime that queried
    the stale artifact it found on disk would return ids for chunks that no
    longer exist.
    """
    provider = DeterministicEmbeddingProvider()
    VectorIndexRuntime(CHUNKS, DOCUMENTS, provider, tmp_path).index()

    replaced = [{"id": "c9", "text": "omega"}]
    runtime = VectorIndexRuntime(replaced, DOCUMENTS, provider, tmp_path)

    assert runtime.query_text("omega", 3) == ["c9"]
    assert runtime.disposition == REBUILT_STALE


def test_m201c_staleness_is_checked_without_embedding_the_corpus(tmp_path):
    """M2.01C — compatibility validation must not cost what it prevents.

    The expected identity needs the corpus, the provider's declared width and
    the model identity — none of which requires embedding anything. A check
    that embedded the corpus would cost exactly as much as the rebuild it
    exists to avoid, and staleness is checked on every construction.

    Counted through the provider itself, so the claim is about executions
    rather than about elapsed time.
    """
    provider = RecordingProvider(EMBEDDING_MODEL_ID, EMBEDDING_MODEL_REVISION)
    VectorIndexRuntime(CHUNKS, DOCUMENTS, provider, tmp_path).index()
    embedded_during_rebuild = len(provider.embedded)

    second = RecordingProvider(EMBEDDING_MODEL_ID, EMBEDDING_MODEL_REVISION)
    runtime = VectorIndexRuntime(CHUNKS, DOCUMENTS, second, tmp_path)
    runtime.index()

    assert embedded_during_rebuild == len(CHUNKS)
    assert runtime.disposition == LOADED
    assert second.embedded == []


def test_m201c_the_runtime_writes_only_the_two_artifact_files(tmp_path):
    """RO-09 — the derived location holds the artifact and nothing else.

    No cache file, no lock, no log, no second copy. The runtime location must
    not accumulate state the canonical corpus cannot regenerate, or it becomes
    the second source of truth RO-09 item 6 forbids.
    """
    runtime = VectorIndexRuntime(CHUNKS, DOCUMENTS, DeterministicEmbeddingProvider(), tmp_path)
    runtime.index()
    runtime.query_text("alpha", 2)

    assert sorted(path.name for path in tmp_path.rglob("*")) == [
        FAISS_INDEX_FILENAME,
        INDEX_METADATA_FILENAME,
    ]


def test_m201c_the_default_runtime_location_is_the_declared_constant():
    """RO-09 item 9 — the concrete runtime artifact location, owned by M2.01C.

    RO-09 prescribes no path and leaves the choice here. The choice is the
    constant Sprint M2.01B already declared, so the repository has **one**
    runtime location rather than two, and it is derived from the module's own
    path — not from a working directory, an environment variable or a flag —
    which is what makes it deterministic and reproducible for every caller.
    """
    runtime = VectorIndexRuntime(CHUNKS, DOCUMENTS, DeterministicEmbeddingProvider())

    assert runtime.directory == VECTOR_INDEX_ROOT
    assert VECTOR_INDEX_ROOT.name == "vector_index"
    assert VECTOR_INDEX_ROOT.parent.name == "sample_rag"


def test_m201c_the_runtime_artifact_is_not_a_repository_source_artifact(repository_root):
    """RO-09 items 3–5 — generated FAISS artifacts are not committed.

    The ruling states the policy and reserves the ignore rule for this sprint,
    *"once the location exists"*. It now exists, so the rule exists, and this
    specification is what keeps the two agreeing.

    Both halves are asserted: the ignore rule names the runtime **directory**,
    and nothing under that directory is tracked by Git. The trailing separator
    matters — `sample_rag/vector_index.py` is source and is committed; only the
    directory beside it is derived.

    **Tracking, not presence.** *Not committed* is a property of the Git index,
    not of the filesystem. RO-09 item 6 expects a caller to generate the
    artifact in place and says *"a caller who deletes it loses nothing but the
    time to rebuild"*, so the artifact is **allowed** to exist at the runtime
    location RO-09 item 9 fixes — a populated `sample_rag/vector_index/` is a
    correct execution, not a policy breach. This specification therefore asks
    Git what it tracks rather than asking the filesystem what exists.
    Corrected at Sprint **RO-12** from the filesystem-absence assertion it
    originally carried, which stated a stricter property than the policy it
    cites; see `docs/ENGINEERING_TRACEABILITY_REGISTER.md` §3.5 **M2.04-F-1**.
    """
    ignored = (repository_root / ".gitignore").read_text(encoding="utf-8").splitlines()

    assert "sample_rag/vector_index/" in ignored

    tracked = subprocess.run(
        ["git", "ls-files", "--", "sample_rag/vector_index/"],
        cwd=repository_root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )

    assert tracked.stdout == ""


# --- query-side embedding (M2.01A's provider, unchanged) ---------------------


def test_m201c_the_query_is_embedded_by_the_provider_that_built_the_index(tmp_path):
    """M2.01C — one provider, both sides.

    Not merely the same model id: the same object, the one the index's own
    identity records. A query embedded by any other provider would produce a
    vector that is comparable to the stored ones only by coincidence, and
    `docs/architecture.md` §5 places `EmbeddingProvider` as `VectorStore`'s
    dependency for exactly this reason.
    """
    provider = RecordingProvider(EMBEDDING_MODEL_ID, EMBEDDING_MODEL_REVISION)
    runtime = VectorIndexRuntime(CHUNKS, DOCUMENTS, provider, tmp_path)

    runtime.query_text("alpha", 1)

    assert provider.embedded[-1] == "alpha"
    assert runtime.index().identity.model_id == EMBEDDING_MODEL_ID
    assert runtime.index().identity.model_revision == EMBEDDING_MODEL_REVISION


def test_m201c_no_query_prefix_or_transformation_is_applied(tmp_path):
    """M2.01C — the query text reaches the model **verbatim**.

    BGE publishes an asymmetric retrieval prefix for the query side, and
    `sample_rag/embedding.py` records that it is deliberately not applied and
    that **M2-02** / **M2-04** own the question. No repository authority
    establishes one, so none is applied and none is invented here; it is
    reported as an open question instead
    (`docs/M2.01C_Semantic_Query_Foundation_Report.md` §17, finding F-2).

    Specified rather than left implicit, so that adopting a prefix later is a
    deliberate, visible decision — it would change what every query vector *is*
    relative to every stored one.
    """
    provider = RecordingProvider()
    runtime = VectorIndexRuntime(CHUNKS, DOCUMENTS, provider, tmp_path)
    question = "Represent nothing; this text must arrive unchanged."

    runtime.query_text(question, 1)

    assert provider.embedded[-1] == question
    assert provider.embedded[len(CHUNKS):] == [question]


# --- retrieval correctness, against the real model ---------------------------


def test_m201c_a_query_retrieves_the_chunk_that_answers_it(tmp_path):
    """M2-02 / M2.01C — **the capability itself**: semantic retrieval.

    Everything above this specification would hold for the Milestone 1B digest,
    because ordering, top-k and the ordinal mapping are properties of FAISS and
    of the mapping. This is the property that would not: a query that shares no
    vocabulary with the chunk it should retrieve still retrieves it, because
    the vectors carry meaning.

    Stated as **which chunk ranks first** over a controlled three-subject
    corpus, not as a similarity threshold — the discipline
    `tests/test_indexer.py::test_m201_related_text_embeds_nearer_than_unrelated_text`
    established at Sprint M2.01A. The margins are wide by construction, so this
    fails on a broken integration rather than on ordinary model variation.

    **This is a retrieval-correctness check, not an evaluation metric.** It asks
    whether the query path returns what the index says it should. Context
    Precision, Context Recall, Ragas and DeepEval are **M2-07**, **M2-08** and
    **M2-10**, and none of them appears here.
    """
    provider = BGEEmbeddingProvider()
    runtime = VectorIndexRuntime(SEMANTIC_CHUNKS, DOCUMENTS, provider, tmp_path)

    assert runtime.query_text("Who managed a software testing team?", 1) == ["s0"]
    assert runtime.query_text("building data pipelines in python", 1) == ["s2"]
    assert runtime.query_text("heavy seasonal rain near the sea", 1) == ["s1"]


def test_m201c_an_unrelated_query_does_not_retrieve_the_related_chunk_first(tmp_path):
    """M2-02 / M2.01C — the contrast that makes the specification above mean something.

    Without it, "the expected chunk appeared in the results" could be satisfied
    by an index that returns the same order for every query — which is exactly
    what the Milestone 1B stand-in would do for reasons unrelated to meaning.
    Two queries about different subjects must rank different chunks first.
    """
    provider = BGEEmbeddingProvider()
    runtime = VectorIndexRuntime(SEMANTIC_CHUNKS, DOCUMENTS, provider, tmp_path)

    related = runtime.query_text("cross-functional quality assurance leadership", 3)
    unrelated = runtime.query_text("monsoon rainfall on the coast", 3)

    assert related[0] == "s0"
    assert unrelated[0] != related[0]


def test_m201c_the_committed_corpus_answers_a_semantic_query(
    tmp_path, real_chunks, real_manifest_entries, real_chunks_by_id
):
    """M2-02 / M2.01C — the actual Milestone 2A pipeline, once, end to end.

    The committed Chunk Corpus, embedded by `BGEEmbeddingProvider` at the pinned
    revision, persisted to a temporary runtime location, reloaded and queried.
    It is the specification that would catch a real-pipeline failure — a width
    mismatch, a mapping that does not resolve to real chunks, an artifact the
    corpus cannot round-trip — that no synthetic collection would surface.

    The assertions are about **the query path**, not about answer quality: every
    returned id resolves to a real chunk, the requested `top_k` is honoured over
    a 200-plus-chunk corpus, and two queries on different subjects do not
    produce the same ranking. Judging *how good* the retrieval is belongs to
    Ragas (**M2-07**) and is not attempted here.
    """
    provider = BGEEmbeddingProvider()
    runtime = VectorIndexRuntime(real_chunks, real_manifest_entries, provider, tmp_path)

    retrieved = runtime.query_text("quality engineering and test automation experience", 5)

    assert runtime.disposition == REBUILT_ABSENT
    assert len(retrieved) == 5
    assert all(chunk_id in real_chunks_by_id for chunk_id in retrieved)
    assert runtime.index().vector_count == len(real_chunks)

    unrelated = runtime.query_text("monsoon rainfall on the coast", 5)
    assert unrelated != retrieved


# --- determinism -------------------------------------------------------------


def test_m201c_the_same_query_over_the_same_corpus_returns_the_same_order(tmp_path):
    """M2.01C — **semantic/query determinism.** Claimed, and specified.

    Same corpus, same embeddings, same index configuration, same query vector →
    equal ordered results, across two independently built indexes in two
    directories. This is `docs/DOCUMENT_CONTRACT.md` §8.8 item 1's definition of
    determinism — *repeated construction yields equal values* — applied to
    retrieval.

    **Byte identity of the FAISS binary is not claimed here and is not
    asserted**, following Sprint M2.01B's finding F-3 and the determinism
    section of `sample_rag/vector_index.py`. Equal *retrieval* is the repository
    property; equal bytes from a third-party serializer is not.

    Nothing is cached to produce this. The two runtimes share no state, and each
    rebuilds from the corpus in full.
    """
    provider = DeterministicEmbeddingProvider()
    first = VectorIndexRuntime(CHUNKS, DOCUMENTS, provider, tmp_path / "first")
    second = VectorIndexRuntime(CHUNKS, DOCUMENTS, provider, tmp_path / "second")

    vector = first.index().reconstruct(0)

    assert first.query(vector, len(CHUNKS)) == second.query(vector, len(CHUNKS))
    assert first.index().identity == second.index().identity


def test_m201c_metadata_identity_survives_a_rebuild(tmp_path):
    """M2.01C — metadata identity is consistent across the lifecycle.

    The persisted metadata after a rebuild must describe the same index as the
    one held in memory, signal for signal. Read from the file rather than from
    the object, so this compares the artifact with the intent rather than the
    object with itself.
    """
    runtime = VectorIndexRuntime(CHUNKS, DOCUMENTS, DeterministicEmbeddingProvider(), tmp_path)
    identity = runtime.index().identity

    metadata = json.loads((tmp_path / INDEX_METADATA_FILENAME).read_text("utf-8"))

    assert metadata["chunk_ids"] == list(identity.chunk_ids)
    assert metadata["chunk_fingerprint"] == identity.chunk_fingerprint
    assert metadata["vector_count"] == identity.vector_count
    assert metadata["embedding"]["dimension"] == identity.dimension
    assert FaissVectorIndex.load(tmp_path).identity == identity


# --- boundary: M2-02 remains OPEN, and nothing beyond query was built --------


def test_m201c_the_frozen_protocol_is_unchanged():
    """M2.01C — `sample_rag/vector_store.py` was not touched by this sprint.

    RO-08 is explicit that it *"adds, removes, renames and alters no method,
    signature, return type or protocol requirement"*, and RO-09 preserves the
    Protocol in the same words. The seam must therefore still declare exactly
    the two methods `docs/architecture.md` §7 states, and still ship no
    implementation beside them — which
    `tests/test_indexer.py::test_1b02_no_vector_store_implementation_is_shipped`
    asserts and this specification restates from this sprint's side, because
    this is the sprint that had a motive to change it.
    """
    import sample_rag.vector_store as module
    from sample_rag.vector_store import VectorStore

    tree = ast.parse(inspect.getsource(module))
    declared = [node.name for node in tree.body if isinstance(node, ast.ClassDef)]

    assert declared == ["VectorStore"]
    assert sorted(
        name for name in VectorStore.__protocol_attrs__
    ) == ["query", "upsert"]


def test_m201c_no_component_satisfies_the_vector_store_protocol(tmp_path):
    """**M2-02 remains OPEN, and this is the exact remaining gap.**

    `query` is implemented, validated and authorized. `upsert` is not
    implemented, and is not stubbed to manufacture conformance: no repository
    authority states its operational semantics, and the frozen signature
    `upsert(chunk_id: str, vector: list[float]) -> None` carries neither the
    chunk **text** that RO-08 Decision 1's `chunk_fingerprint` is computed from
    nor the document identity that `document_hashes` records — so no
    implementation of it could maintain the identity this artifact's
    compatibility validation is defined over.

    `tests/test_indexer.py::test_1b02_a_partial_store_does_not_satisfy_the_protocol`
    already establishes that half a Protocol is not conformance. This
    specification applies that to the component this sprint delivered, so
    **passing a structural test cannot be mistaken for discharging M2-02**.

    It is expected to change only when the Repository Owner supplies `upsert`
    semantics — see `docs/M2.01C_Semantic_Query_Foundation_Report.md` §16.
    """
    from sample_rag.vector_store import VectorStore

    index = built()
    runtime = VectorIndexRuntime(CHUNKS, DOCUMENTS, DeterministicEmbeddingProvider(), tmp_path)

    assert not isinstance(index, VectorStore)
    assert not isinstance(runtime, VectorStore)
    assert not hasattr(index, "upsert")
    assert not hasattr(runtime, "upsert")


def test_m201c_the_query_path_exposes_no_fusion_or_lexical_surface():
    """M2.01C — the sprint boundary, enforced structurally.

    The retrieval operation this sprint introduces is *query vector → FAISS
    nearest-neighbour search → top-k ordinals → chunk ids*, and nothing beyond
    it. BM25 (**M2-03**), Reciprocal Rank Fusion and hybrid ranking
    (**M2-04**), reranking (**M2-05**), query expansion or rewriting, and
    generation (**M2-06**) are all later capabilities, and *"retrieval"* must
    not be allowed to expand into *"hybrid retrieval"* because one route now
    returns real results.

    Asserted over both query-path modules' own source, so a helper added later
    fails here rather than passing unnoticed.
    """
    import sample_rag.vector_index as index_module
    import sample_rag.vector_runtime as runtime_module

    for module in (index_module, runtime_module):
        declared = {
            node.name
            for node in ast.walk(ast.parse(inspect.getsource(module)))
            if isinstance(node, ast.FunctionDef)
        }

        for barred in (
            "bm25",
            "lexical",
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
            "generate",
            "upsert",
        ):
            assert barred not in declared, f"{barred} is out of scope for Sprint M2.01C"


def test_m201c_the_runtime_reaches_faiss_and_the_model_only_through_their_seams():
    """M2.01C / A-5 — the two standing exceptions did not widen.

    The vector-store library stays confined to `sample_rag/vector_index.py` and
    the embedding library to `sample_rag/embedding.py`; the module added by this
    sprint imports neither directly, and imports nothing from `scripts/` —
    the direction `docs/architecture.md` §6 bars.

    The package-wide glob checks in `tests/test_vector_index.py` and
    `tests/test_indexer.py` already cover this file automatically. This
    specification states the positive form: what the new module *is* allowed to
    reach.
    """
    import sample_rag.vector_runtime as module

    roots = {
        node.module.split(".")[0]
        for node in ast.walk(ast.parse(inspect.getsource(module)))
        if isinstance(node, ast.ImportFrom) and node.module
    } | {
        alias.name.split(".")[0]
        for node in ast.walk(ast.parse(inspect.getsource(module)))
        if isinstance(node, ast.Import)
        for alias in node.names
    }

    assert roots == {"sample_rag"}


def test_m201c_the_index_stage_and_the_seam_still_declare_what_they_did():
    """M2.01C — the components this sprint consumed were not redesigned.

    `EmbeddingProvider` stays a one-method Protocol, `BGEEmbeddingProvider`
    stays the elected checkpoint at the pinned revision, and the Index stage
    still reports the model's own width. Sprint M2.01C fitted a query path
    behind all three without moving any of them, which is the same property
    criterion A-1 asked of Sprint M2.01A.
    """
    from sample_rag.embedding import EmbeddingProvider

    assert sorted(EmbeddingProvider.__protocol_attrs__) == ["embed"]
    assert BGEEmbeddingProvider.dimension == EMBEDDING_DIMENSION
    assert BGEEmbeddingProvider().model_id == EMBEDDING_MODEL_ID
    assert BGEEmbeddingProvider().revision == EMBEDDING_MODEL_REVISION
    assert Indexer(DeterministicEmbeddingProvider()).index([]).dimension == PLACEHOLDER_DIMENSION
