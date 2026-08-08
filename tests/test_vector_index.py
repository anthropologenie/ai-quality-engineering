"""Specification Family — the persistent vector-index artifact.

Sprint M2.01B specifies the **persistence/foundation stage** of register
capability **M2-02**, under Repository Owner ruling **RO-08**
(`docs/DEFERRED_ITEMS_REGISTER.md` §4.1).

**M2-02 is not discharged by this sprint**, and no specification here claims it
is. RO-08 Decision 2 stages the capability: `query(vector, top_k) -> list[str]`
and query-time nearest-neighbour behaviour belong to Sprint M2.01C, and
`test_m201b_the_artifact_exposes_no_retrieval_surface` below is what keeps this
sprint on its side of that line.

Scope boundary against the Index stage
---------------------------------------
`tests/test_indexer.py` specifies the `EmbeddingProvider` seam, the
`VectorStore` **Protocol**, and the in-memory `Index`. This file specifies what
happens to an `Index` **after** it exists: how it is persisted, identified,
reloaded and validated. Nothing here re-specifies the Protocol, and
`sample_rag/vector_store.py` is untouched by this sprint — `test_1b02_*` in
that file continues to assert it ships no implementation, and continues to pass.

Behaviour, not artefacts
-------------------------
Following `tests/conftest.py` and the whole 1B/2A precedent, no specification
here freezes a vector literal, a FAISS binary digest, or a corpus fact. The
fingerprint's *algorithm and serialization* are pinned — RO-08 Decision 1
requires this sprint to state them exactly — but they are pinned by
independently recomputing the documented construction, in the manner DQ-1
*"compares two computed values"* rather than asserting a stored digest.

Criterion A-5, structurally
----------------------------
`docs/MILESTONE_1A.md` criterion A-5's **vector-store-library** portion lapses
at this sprint, for M2-02, in `sample_rag/vector_index.py` alone. The two
specifications at the foot of this file enforce that boundary the same way
`tests/test_indexer.py` enforces the embedding seam's: an AST allowlist on the
one authorized module, and a glob check that no other `sample_rag/*.py`
imports the library. The AST helpers are duplicated from that file rather than
shared, which is the precedent `tests/test_generator.py` and `tests/test_cli.py`
already set — each specification family carries its own allowlist.
"""

import ast
import hashlib
import inspect
import json

from dataclasses import replace

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
    METADATA_SCHEMA_VERSION,
    VECTOR_INDEX_METRIC,
    VECTOR_INDEX_TYPE,
    FaissVectorIndex,
    VectorIndexCompatibilityError,
    VectorIndexIdentity,
    VectorIndexPersistenceError,
    chunk_fingerprint,
    identity_for,
)


def imported_roots(module):
    """The top-level package of every import in `module`'s source."""
    tree = ast.parse(inspect.getsource(module))

    roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".")[0])
    return roots


def chunk(chunk_id, text):
    """A minimal chunk in the serialized form the Index stage receives.

    Only `id` and `text` are read by the Index stage and by the fingerprint, so
    only those are supplied — the convention `tests/test_indexer.py` established
    against the same collection.
    """
    return {"id": chunk_id, "text": text}


def document(document_id, document_hash):
    """A minimal Knowledge Manifest entry.

    Only `id` and `hash` participate in index identity. Supplying `source` and
    `canonical` would imply the artifact depends on fields it never reads.
    """
    return {"id": document_id, "hash": document_hash}


CHUNKS = [chunk("c0", "alpha"), chunk("c1", "beta"), chunk("c2", "gamma")]
DOCUMENTS = [document("d0", "0" * 64), document("d1", "1" * 64)]


def built(chunks=None, documents=None, provider=None):
    """Build a `FaissVectorIndex` over the given material.

    The deterministic stand-in is the default provider, deliberately: these
    specifications are about **persistence and identity**, which are
    model-agnostic, and the stand-in needs no checkpoint. The real model is
    exercised by `test_m201b_the_committed_corpus_persists_under_the_real_model`,
    which is the one specification here whose subject is the real pipeline.
    """
    chunks = CHUNKS if chunks is None else chunks
    documents = DOCUMENTS if documents is None else documents
    provider = provider or DeterministicEmbeddingProvider()

    index = Indexer(provider).index(chunks)

    return FaissVectorIndex.build(index, chunks, documents, provider), index


def expected_identity(chunks=None, documents=None, provider=None):
    """The identity the given inputs would produce — the intended state."""
    chunks = CHUNKS if chunks is None else chunks
    documents = DOCUMENTS if documents is None else documents
    provider = provider or DeterministicEmbeddingProvider()

    return identity_for(Indexer(provider).index(chunks), chunks, documents, provider)


# --- the persistence contract -----------------------------------------------


def test_m201b_build_produces_a_faiss_index_over_every_chunk():
    """M2-02 / M2.01B — every chunk's vector reaches the persisted index.

    The coverage property DQ-7 asserts of the in-memory Index, carried one
    stage further: an index that silently held fewer vectors than the corpus
    has chunks would map positions onto the wrong chunk ids.
    """
    index, _ = built()

    assert index.vector_count == len(CHUNKS)
    assert index.identity.vector_count == len(CHUNKS)
    assert index.identity.chunk_ids == ("c0", "c1", "c2")


def test_m201b_build_rejects_a_chunk_with_no_vector():
    """M2-02 / M2.01B — an incomplete Index cannot be persisted quietly.

    `docs/DATA_QUALITY_VALIDATION_PLAN.md` §8.1 defines a chunk lacking a
    representation as DQ-7's failure. If it reaches persistence, the artifact
    must refuse rather than build a shorter index whose positions no longer
    correspond to the caller's chunk order.
    """
    provider = DeterministicEmbeddingProvider()
    partial = Indexer(provider).index(CHUNKS[:2])

    with pytest.raises(VectorIndexCompatibilityError):
        FaissVectorIndex.build(partial, CHUNKS, DOCUMENTS, provider)


def test_m201b_the_faiss_configuration_is_flat_inner_product():
    """M2-02 / M2.01B — the elected FAISS configuration, recorded in identity.

    `IndexFlatIP` is exact and untrained: no clustering, quantization, sampling
    or random initialization, so two builds over identical vectors hold
    identical contents. Inner product is cosine for the unit-norm vectors
    `sample_rag/embedding.py` produces.

    Pinned because it is **identity-relevant** — RO-08 Decision 3 names
    *"relevant FAISS index configuration / type"* as a compatibility signal, so
    a change to it must be a visible decision rather than a silent one.
    """
    index, _ = built()

    assert VECTOR_INDEX_TYPE == "IndexFlatIP"
    assert VECTOR_INDEX_METRIC == "inner_product"
    assert index.identity.index_type == VECTOR_INDEX_TYPE
    assert index.identity.metric == VECTOR_INDEX_METRIC


def test_m201b_the_artifact_is_two_files_in_one_directory(tmp_path):
    """M2-02 / M2.01B — what the persisted artifact actually is.

    A FAISS binary this repository does not own the format of, and repository
    metadata in the repository's own canonical JSON. Two files because they are
    two kinds of thing; one directory because they are one artifact.
    """
    index, _ = built()

    index.save(tmp_path)

    assert sorted(path.name for path in tmp_path.iterdir()) == [
        FAISS_INDEX_FILENAME,
        INDEX_METADATA_FILENAME,
    ]


def test_m201b_the_metadata_records_the_identity_and_the_mapping(tmp_path):
    """M2-02 / M2.01B — what the metadata file contains.

    Every RO-08 Decision 3 signal, plus the ordered `chunk_ids` that *is* the
    vector → chunk mapping. `schema_version` sits on the container, the
    convention `sample_rag/chunks.json` and `sample_rag/knowledge_manifest.json`
    both follow.
    """
    index, _ = built()
    index.save(tmp_path)

    metadata = json.loads((tmp_path / INDEX_METADATA_FILENAME).read_text("utf-8"))

    assert metadata["schema_version"] == METADATA_SCHEMA_VERSION
    assert metadata["index_type"] == VECTOR_INDEX_TYPE
    assert metadata["metric"] == VECTOR_INDEX_METRIC
    assert metadata["embedding"]["dimension"] == PLACEHOLDER_DIMENSION
    assert metadata["vector_count"] == len(CHUNKS)
    assert metadata["chunk_ids"] == ["c0", "c1", "c2"]
    assert metadata["documents"] == [
        {"id": "d0", "hash": "0" * 64},
        {"id": "d1", "hash": "1" * 64},
    ]
    assert len(metadata["chunk_fingerprint"]) == 64


def test_m201b_the_metadata_records_no_timestamp_of_any_kind(tmp_path):
    """M2-02 / M2.01B / RO-08 Decision 3 — no timestamp may enter the artifact.

    RO-08 Decision 3 bars `created_at`, persisted `documents[].indexed`,
    last-indexed timestamps and timestamp-based identity. `docs/MILESTONE_1A.md`
    build item 1 removed `created_at` because a timestamp *"would make the
    manifest non-deterministic for an identical corpus generated at two
    different times"*, and ruling **R-02** removed `documents[].indexed` from
    the persisted schema.

    Asserted over the serialized text, so a timestamp nested anywhere in the
    payload fails here rather than only a top-level one.
    """
    index, _ = built()
    index.save(tmp_path)

    serialized = (tmp_path / INDEX_METADATA_FILENAME).read_text("utf-8")

    for barred in ("created_at", "indexed", "timestamp", "last_indexed", "generated_at"):
        assert barred not in serialized


def test_m201b_the_mapping_answers_which_chunk_a_position_holds():
    """M2-02 / M2.01B — the vector → source/chunk mapping.

    FAISS addresses vectors by ordinal, so the mapping is what makes a stored
    vector attributable to a chunk at all. Asked through the artifact's own
    vocabulary rather than by reaching into the identity, the same reason
    `sample_rag/indexer.py` exposes `Index.covers`.
    """
    index, _ = built()

    assert [index.chunk_id_at(position) for position in range(3)] == ["c0", "c1", "c2"]


def test_m201b_the_mapping_follows_chunk_order_not_dict_order():
    """M2-02 / M2.01B — position order is the Chunk Contract's order.

    `docs/CHUNK_CONTRACT.md` §17 invariants 4–5 fix chunk order; `Index.vectors`
    is a mapping whose order is an implementation accident. Building from a
    reversed collection must produce a reversed mapping, which it cannot if the
    order were taken from the Index.
    """
    reversed_chunks = list(reversed(CHUNKS))

    index, _ = built(chunks=reversed_chunks)

    assert index.identity.chunk_ids == ("c2", "c1", "c0")
    assert index.chunk_id_at(0) == "c2"


# --- RO-08 Decision 1: the index-local chunk-content fingerprint -------------


def test_m201b_the_fingerprint_is_sha256_over_the_documented_serialization():
    """RO-08 Decision 1 — the exact algorithm and serialization, pinned.

    RO-08 requires this sprint to **record** the algorithm, serialization and
    input construction, and explicitly makes none of the three repository
    authority. This specification is that record in executable form.

    The expected value is recomputed here **independently** — a literal
    `json.dumps` and `hashlib.sha256` written out in the specification — rather
    than by calling the module under test, following DQ-1's discipline of
    *"comparing two computed values"* instead of asserting a stored digest.
    """
    pairs = [["c0", "alpha"], ["c1", "beta"], ["c2", "gamma"]]
    serialized = json.dumps(pairs, ensure_ascii=False, separators=(",", ":"))
    expected = hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    assert chunk_fingerprint(CHUNKS) == expected
    assert len(expected) == 64


def test_m201b_the_fingerprint_sees_content_change_at_a_stable_chunk_id():
    """RO-08 Decision 1 — **the gap the fingerprint exists to close.**

    `sample_rag/chunker.py` derives chunk ids from position, *"not from chunk
    content"*, and `documents[].hash` covers source **bytes**, not extracted
    text (`docs/DATA_QUALITY_VALIDATION_PLAN.md` §8.8 item 2). A chunker or
    extraction change can therefore rewrite chunk text while the document hash,
    the chunk ids and the chunk count all stay identical.

    Everything except the text is held constant here, so this specification
    fails if the fingerprint ever stops depending on chunk content — which is
    the only reason RO-08 Decision 1 was sought.
    """
    original = [chunk("c0", "alpha")]
    rechunked = [chunk("c0", "alpha beta")]

    assert chunk_fingerprint(original) != chunk_fingerprint(rechunked)


def test_m201b_the_fingerprint_depends_on_chunk_order():
    """RO-08 Decision 1 — the *ordered* sequence, as the ruling states.

    Order is part of the identity because position is the mapping. The same
    chunks in a different order are a different index, and must fingerprint
    differently.
    """
    assert chunk_fingerprint(CHUNKS) != chunk_fingerprint(list(reversed(CHUNKS)))


def test_m201b_the_fingerprint_framing_cannot_be_imitated_by_chunk_text():
    """RO-08 Decision 1 — why the serialization is JSON and not a joined string.

    A naive `f"{id}:{text}"` join collapses these two distinct corpora onto one
    digest: `("a", "b")` and `("a:b", "")` both render as `a:b`. JSON's escaping
    makes the encoding injective, so no chunk text — whatever separators or
    newlines it contains — can imitate the framing between two chunks.

    This is the specification behind the serialization choice; without it the
    choice would be a comment rather than a property.
    """
    innocuous = [chunk("a", "b")]
    colliding = [chunk("a:b", "")]

    assert chunk_fingerprint(innocuous) != chunk_fingerprint(colliding)


def test_m201b_the_fingerprint_is_deterministic_across_calls():
    """RO-08 Decision 1 — repeated construction yields equal values.

    `docs/DOCUMENT_CONTRACT.md` §8.8 item 1's definition of determinism, applied
    to the fingerprint. A digest that varied between calls would make every
    compatibility check unreliable.
    """
    assert chunk_fingerprint(CHUNKS) == chunk_fingerprint(CHUNKS)


def test_m201b_the_fingerprint_does_not_touch_the_committed_chunk_corpus():
    """RO-08 Decision 1 — the fingerprint is **index-local**, enforced.

    The ruling bars it from modifying `sample_rag/chunks.json`, the chunk
    contract, chunk ids, or the chunk container's metadata. The structural half
    of that is asserted here: the module computes the digest from chunks it is
    handed and writes nothing outside the index artifact — it names no path
    into the committed chunk corpus and imports no chunk serializer.

    Asserted over **executable** string constants, with docstrings excluded:
    this module cites `sample_rag/chunks.json` in prose repeatedly, and a naive
    source-text search would fail on its own documentation rather than on
    behaviour.
    """
    import sample_rag.vector_index as module

    tree = ast.parse(inspect.getsource(module))

    docstrings = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef)):
            docstring = ast.get_docstring(node, clean=False)
            if docstring is not None:
                docstrings.add(docstring)

    executable_strings = [
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and node.value not in docstrings
    ]

    assert not [text for text in executable_strings if "chunks.json" in text]
    assert "chunker" not in {name.split(".")[-1] for name in imported_roots(module)}
    assert "scripts" not in imported_roots(module)


# --- persistence and loading ------------------------------------------------


def test_m201b_an_index_round_trips_through_disk(tmp_path):
    """M2-02 / M2.01B — save then load returns the same index.

    Identity, vector count and stored contents all survive. Contents are
    compared by reading vectors back out by ordinal, not by comparing files —
    see the determinism specifications below for why that distinction matters.
    """
    index, _ = built()
    index.save(tmp_path)

    loaded = FaissVectorIndex.load(tmp_path)

    assert loaded.identity == index.identity
    assert loaded.vector_count == index.vector_count
    assert [loaded.reconstruct(i) for i in range(3)] == [
        index.reconstruct(i) for i in range(3)
    ]


def test_m201b_save_creates_the_directory_it_is_given(tmp_path):
    """M2-02 / M2.01B — persistence does not require the caller to pre-create it."""
    index, _ = built()
    target = tmp_path / "nested" / "vector_index"

    index.save(target)

    assert (target / FAISS_INDEX_FILENAME).is_file()
    assert (target / INDEX_METADATA_FILENAME).is_file()


# --- CASES A–I: compatibility and staleness ---------------------------------


def test_m201b_case_a_identical_source_state_validates(tmp_path):
    """CASE A — same corpus, chunks, model, revision, dimension, configuration.

    The positive case every other case is measured against. `mismatches` is
    empty and `validate` does not raise.
    """
    index, _ = built()
    index.save(tmp_path)

    loaded = FaissVectorIndex.load(tmp_path)

    assert loaded.identity.mismatches(expected_identity()) == []
    loaded.validate(expected_identity())


def test_m201b_case_b_a_corpus_change_is_detected(tmp_path):
    """CASE B — a document's content hash moved; the index is stale.

    The existing document identity model, used rather than re-derived:
    `documents[].hash` is the SHA-256 the Knowledge Manifest already carries and
    DQ-1 already validates.
    """
    index, _ = built()
    index.save(tmp_path)
    loaded = FaissVectorIndex.load(tmp_path)

    changed_corpus = [document("d0", "0" * 64), document("d1", "2" * 64)]

    assert loaded.identity.mismatches(expected_identity(documents=changed_corpus)) == [
        "document_hashes"
    ]
    with pytest.raises(VectorIndexCompatibilityError):
        loaded.validate(expected_identity(documents=changed_corpus))


def test_m201b_case_c_a_chunk_content_change_is_detected(tmp_path):
    """CASE C — **the case RO-08 Decision 1 was sought for.**

    Chunk *content* changed while the chunk ids, the chunk count and every
    document hash stayed identical — the drift no pre-existing repository
    identity could see. The fingerprint is the only differing signal, which is
    exactly the claim: without it, this index would validate as current and be
    silently wrong.
    """
    index, _ = built()
    index.save(tmp_path)
    loaded = FaissVectorIndex.load(tmp_path)

    rechunked = [chunk("c0", "alpha"), chunk("c1", "beta"), chunk("c2", "gamma delta")]

    assert loaded.identity.mismatches(expected_identity(chunks=rechunked)) == [
        "chunk_fingerprint"
    ]
    with pytest.raises(VectorIndexCompatibilityError):
        loaded.validate(expected_identity(chunks=rechunked))


def test_m201b_case_c_a_chunk_set_change_is_detected(tmp_path):
    """CASE C, second form — the chunk *set* changed, not only its content.

    A removed chunk moves the chunk-id set, the count and the fingerprint at
    once. Specified alongside the content-only case so the two are not confused:
    the set change was always detectable, the content change was not.
    """
    index, _ = built()
    index.save(tmp_path)
    loaded = FaissVectorIndex.load(tmp_path)

    fewer = CHUNKS[:2]

    assert loaded.identity.mismatches(expected_identity(chunks=fewer)) == [
        "chunk_ids",
        "vector_count",
        "chunk_fingerprint",
    ]


def test_m201b_case_d_an_embedding_model_change_is_rejected(tmp_path):
    """CASE D — a different model produced the vectors this index would serve.

    The identity is read from the provider itself, defensively, the way
    `sample_rag/indexer.py` reads `dimension` and `placeholder` — so a
    substituted provider is detected without the frozen `EmbeddingProvider`
    Protocol growing a field.
    """

    class OtherModelProvider:
        dimension = PLACEHOLDER_DIMENSION
        model_id = "some-other/model"
        revision = EMBEDDING_MODEL_REVISION

        def embed(self, text: str) -> list:
            return DeterministicEmbeddingProvider().embed(text)

    index, _ = built(provider=_named_provider())
    index.save(tmp_path)
    loaded = FaissVectorIndex.load(tmp_path)

    other = expected_identity(provider=OtherModelProvider())

    assert loaded.identity.mismatches(other) == ["model_id"]
    with pytest.raises(VectorIndexCompatibilityError):
        loaded.validate(other)


def test_m201b_case_e_an_embedding_revision_change_is_rejected(tmp_path):
    """CASE E — same model, different checkpoint.

    The signal M2.01A pinned in code and this sprint carries into the artifact.
    A revision change silently alters every vector, so an index built under the
    old checkpoint cannot be reused under the new one.
    """
    index, _ = built(provider=_named_provider())
    index.save(tmp_path)
    loaded = FaissVectorIndex.load(tmp_path)

    moved = replace(loaded.identity, model_revision="0" * 40)

    assert loaded.identity.mismatches(moved) == ["model_revision"]
    with pytest.raises(VectorIndexCompatibilityError):
        loaded.validate(moved)


def test_m201b_case_f_a_dimension_change_is_rejected(tmp_path):
    """CASE F — the vectors are not the width this index holds."""
    index, _ = built()
    index.save(tmp_path)
    loaded = FaissVectorIndex.load(tmp_path)

    widened = replace(loaded.identity, dimension=EMBEDDING_DIMENSION)

    assert loaded.identity.mismatches(widened) == ["dimension"]
    with pytest.raises(VectorIndexCompatibilityError):
        loaded.validate(widened)


def test_m201b_case_g_a_faiss_configuration_change_is_rejected(tmp_path):
    """CASE G — the FAISS index type or metric moved.

    RO-08 Decision 3 names *"relevant FAISS index configuration / type"* as a
    compatibility signal. Both participate: an index built flat under inner
    product is not interchangeable with one built under another structure or
    another metric, even over identical vectors.
    """
    index, _ = built()
    index.save(tmp_path)
    loaded = FaissVectorIndex.load(tmp_path)

    assert loaded.identity.mismatches(
        replace(loaded.identity, index_type="IndexIVFFlat")
    ) == ["index_type"]
    assert loaded.identity.mismatches(replace(loaded.identity, metric="l2")) == ["metric"]

    with pytest.raises(VectorIndexCompatibilityError):
        loaded.validate(replace(loaded.identity, index_type="IndexIVFFlat"))


def test_m201b_case_h_a_missing_artifact_fails_naming_a_rebuild(tmp_path):
    """CASE H — the artifact or half of it is absent.

    Both files are required, and the failure says what the caller's remedy is.
    The artifact is derived, so a rebuild loses nothing — but a silent empty
    index would lose the fact that it was never built.
    """
    with pytest.raises(VectorIndexPersistenceError, match="rebuild"):
        FaissVectorIndex.load(tmp_path / "never-built")

    index, _ = built()
    index.save(tmp_path)
    (tmp_path / INDEX_METADATA_FILENAME).unlink()

    with pytest.raises(VectorIndexPersistenceError, match="rebuild"):
        FaissVectorIndex.load(tmp_path)


def test_m201b_case_i_a_corrupt_faiss_binary_fails_rather_than_loading(tmp_path):
    """CASE I — FAISS's own file is not a FAISS index.

    Raised as persistence rather than propagated, so the caller sees *the
    artifact is unusable* instead of a third-party error whose origin is
    ambiguous — the discipline `sample_rag/embedding.py`'s
    `EmbeddingModelUnavailableError` set for model loading.
    """
    index, _ = built()
    index.save(tmp_path)
    (tmp_path / FAISS_INDEX_FILENAME).write_bytes(b"not a faiss index at all")

    with pytest.raises(VectorIndexPersistenceError):
        FaissVectorIndex.load(tmp_path)


def test_m201b_case_i_corrupt_metadata_fails_rather_than_loading(tmp_path):
    """CASE I — the metadata is unparseable, or is missing a signal.

    Two distinct corruptions. The second matters most: metadata missing a field
    must fail, not produce an identity with a defaulted signal that would then
    compare equal to something it should not.
    """
    index, _ = built()
    index.save(tmp_path)
    (tmp_path / INDEX_METADATA_FILENAME).write_text("{ not json", encoding="utf-8")

    with pytest.raises(VectorIndexPersistenceError):
        FaissVectorIndex.load(tmp_path)

    index.save(tmp_path)
    payload = json.loads((tmp_path / INDEX_METADATA_FILENAME).read_text("utf-8"))
    del payload["chunk_fingerprint"]
    (tmp_path / INDEX_METADATA_FILENAME).write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(VectorIndexPersistenceError):
        FaissVectorIndex.load(tmp_path)


def test_m201b_case_i_files_that_disagree_with_each_other_fail(tmp_path):
    """CASE I — the two files describe different indexes.

    The consistency guarantee a two-file artifact owes. A metadata file
    claiming more vectors than FAISS holds would make `chunk_id_at` attribute
    stored vectors to the wrong chunks — a silent mis-mapping, which is the
    failure mode this check exists to prevent.

    Persistence, not incompatibility: nothing is being compared to an intended
    corpus yet, the artifact is simply not coherent.
    """
    index, _ = built()
    index.save(tmp_path)

    payload = json.loads((tmp_path / INDEX_METADATA_FILENAME).read_text("utf-8"))
    payload["vector_count"] = payload["vector_count"] + 1
    payload["chunk_ids"] = payload["chunk_ids"] + ["c3"]
    (tmp_path / INDEX_METADATA_FILENAME).write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(VectorIndexPersistenceError, match="inconsistent"):
        FaissVectorIndex.load(tmp_path)


def test_m201b_compatibility_reports_every_differing_signal_at_once(tmp_path):
    """M2-02 / M2.01B — the report is complete, not first-failure.

    A caller repairing a stale index should see everything that moved. Ordered
    from corpus-level to configuration-level so the first entry is the most
    upstream cause.
    """
    index, _ = built()
    index.save(tmp_path)
    loaded = FaissVectorIndex.load(tmp_path)

    unrelated = replace(
        loaded.identity,
        document_hashes=(("d9", "9" * 64),),
        chunk_fingerprint="0" * 64,
        metric="l2",
    )

    assert loaded.identity.mismatches(unrelated) == [
        "document_hashes",
        "chunk_fingerprint",
        "metric",
    ]


# --- rebuild / regeneration semantics ---------------------------------------


def test_m201b_rebuilding_from_identical_inputs_is_semantically_deterministic(tmp_path):
    """M2.01B — **claim A: semantic/index determinism.** Required.

    Same chunks, same vectors, same model identity, same configuration must
    produce an equal identity and equal stored contents. Contents are compared
    by reading each vector back out by ordinal, which is the honest way to
    compare two indexes without asserting anything about FAISS's file format.

    This is the property `docs/architecture.md` §9's determinism discipline
    requires of a repository artifact, stated for a binary one.
    """
    first, _ = built()
    second, _ = built()

    assert first.identity == second.identity
    assert first.vector_count == second.vector_count
    assert [first.reconstruct(i) for i in range(3)] == [
        second.reconstruct(i) for i in range(3)
    ]


def test_m201b_the_metadata_file_is_byte_identical_across_rebuilds(tmp_path):
    """M2.01B — **claim A, for the file this repository does own.**

    The metadata is serialized with `json.dumps(..., indent=2) + "\\n"`, the
    exact call `scripts/build_chunks.py` and `scripts/build_manifest.py` use, so
    byte identity here is a repository property and is claimed.

    **No equivalent claim is made for `index.faiss`.** Third-party binary
    serialization is not a repository byte-identity contract, and no repository
    authority establishes one for it — see the module docstring's determinism
    section. No specification in this file asserts it.
    """
    first_directory = tmp_path / "first"
    second_directory = tmp_path / "second"

    built()[0].save(first_directory)
    built()[0].save(second_directory)

    assert (first_directory / INDEX_METADATA_FILENAME).read_bytes() == (
        second_directory / INDEX_METADATA_FILENAME
    ).read_bytes()


def test_m201b_a_rebuilt_index_validates_against_the_original_inputs(tmp_path):
    """M2.01B — the full lifecycle, end to end.

    build → persist → load → validate → rebuild → validate. The rebuilt
    artifact is accepted for the same inputs, which is what makes rebuilding a
    remedy for staleness rather than a new kind of drift.
    """
    built()[0].save(tmp_path)
    loaded = FaissVectorIndex.load(tmp_path)
    loaded.validate(expected_identity())

    built()[0].save(tmp_path)
    rebuilt = FaissVectorIndex.load(tmp_path)

    rebuilt.validate(expected_identity())
    assert rebuilt.identity == loaded.identity


# --- the real model, over the committed corpus ------------------------------


def test_m201b_the_committed_corpus_persists_under_the_real_model(
    tmp_path, real_chunks, real_manifest_entries
):
    """M2-02 / M2.01B — the actual Milestone 2A pipeline, once, end to end.

    Every other specification here uses the deterministic stand-in, because
    persistence and identity are model-agnostic and the stand-in needs no
    checkpoint. This one exercises what the repository will actually build:
    the committed Chunk Corpus, embedded by `BGEEmbeddingProvider` at the pinned
    revision, persisted, reloaded and validated.

    It is the specification that would catch a real-pipeline failure — a width
    mismatch, a provider whose identity is not readable, a corpus the artifact
    cannot represent — that no synthetic collection would surface.
    """
    provider = BGEEmbeddingProvider()
    index = Indexer(provider).index(real_chunks)

    vector_index = FaissVectorIndex.build(
        index, real_chunks, real_manifest_entries, provider
    )
    vector_index.save(tmp_path)
    loaded = FaissVectorIndex.load(tmp_path)

    assert loaded.identity.model_id == EMBEDDING_MODEL_ID
    assert loaded.identity.model_revision == EMBEDDING_MODEL_REVISION
    assert loaded.identity.dimension == EMBEDDING_DIMENSION
    assert loaded.vector_count == len(real_chunks)
    assert loaded.chunk_id_at(0) == real_chunks[0]["id"]

    loaded.validate(
        identity_for(index, real_chunks, real_manifest_entries, provider)
    )


# --- boundary: no retrieval, and A-5 -----------------------------------------


def test_m201b_the_artifact_exposes_no_retrieval_surface():
    """M2.01B — the sprint boundary, enforced structurally.

    RO-08 Decision 2 stages M2-02: `query(vector, top_k) -> list[str]` and
    query-time nearest-neighbour behaviour belong to Sprint M2.01C. This
    specification is what keeps M2.01B on its side of that line — a search
    method added here fails, rather than passing unnoticed because no other
    specification looks.

    Asserted over the module's own source, so it covers functions as well as
    methods.
    """
    import sample_rag.vector_index as module

    tree = ast.parse(inspect.getsource(module))

    declared = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            declared.add(node.name)

    for barred in (
        "query",
        "search",
        "similarity_search",
        "nearest",
        "nearest_neighbours",
        "knn",
        "top_k",
        "retrieve",
        "rank",
        "upsert",
    ):
        assert barred not in declared, f"{barred} is out of scope for Sprint M2.01B"


def test_m201b_the_vector_store_protocol_is_not_implemented_here():
    """M2.01B / RO-08 Decision 2 — the staged state, asserted rather than assumed.

    The persistence component is deliberately **not** a `VectorStore`: it has no
    `query`, and `tests/test_indexer.py::test_1b02_a_partial_store_does_not_satisfy_the_protocol`
    already establishes that a partial implementation is not conformance.

    RO-08 records that non-conformance as authorized and deliberate. This
    specification pins it, so the day M2.01C supplies `query` is a visible
    change here rather than a silent one — and so nothing in this sprint can be
    mistaken for discharging M2-02.
    """
    from sample_rag.vector_store import VectorStore

    index, _ = built()

    assert not isinstance(index, VectorStore)


def test_m201b_the_vector_index_module_imports_faiss_and_nothing_more():
    """M2.01B / A-5 — the vector-store transition, bounded to one library.

    `docs/MILESTONE_1A.md` criterion A-5's vector-store-library portion lapses
    at this sprint, for **M2-02**, in this module alone. The allowlist admits
    `faiss` — and `numpy`, which FAISS's Python API requires to hand it vectors,
    and which is neither an embedding, vector-store, nor evaluation library.

    Still an allowlist, and that is the point: an LLM SDK (**M2-06**) or an
    evaluation tool (**M2-07**, **M2-08**, **M3-06**) imported here fails,
    because the exception granted was for one library and this is what makes
    "one" checkable. It mirrors
    `tests/test_indexer.py::test_m201_the_embedding_seam_imports_the_embedding_library_and_nothing_more`.
    """
    import sample_rag.vector_index as module

    assert imported_roots(module) <= {
        "dataclasses",
        "hashlib",
        "json",
        "pathlib",
        "faiss",
        "numpy",
    }


def test_m201b_no_other_pipeline_module_imports_faiss():
    """M2.01B / A-5 — the exception did not leak past the persistence component.

    Mirrors
    `tests/test_indexer.py::test_m201_no_other_pipeline_module_imports_the_embedding_library`.
    Stated over the package by glob rather than module by module, so a module
    added later is covered without anyone remembering to add it here.
    """
    import importlib
    import pathlib

    import sample_rag.vector_index

    package_root = pathlib.Path(sample_rag.vector_index.__file__).parent

    offenders = []
    for path in sorted(package_root.glob("*.py")):
        if path.name == "vector_index.py":
            continue

        module = importlib.import_module(f"sample_rag.{path.stem}")
        if "faiss" in imported_roots(module):
            offenders.append(path.name)

    assert offenders == [], f"FAISS imported outside the persistence component: {offenders}"


def _named_provider():
    """A deterministic provider that also declares model identity.

    The stand-in declares no `model_id` or `revision` — it stands in for no
    model. CASE D and CASE E are about identity *changing*, so they need a
    provider that has one without needing a checkpoint on disk.
    """

    class NamedProvider:
        dimension = PLACEHOLDER_DIMENSION
        model_id = EMBEDDING_MODEL_ID
        revision = EMBEDDING_MODEL_REVISION

        def embed(self, text: str) -> list:
            return DeterministicEmbeddingProvider().embed(text)

    return NamedProvider()
