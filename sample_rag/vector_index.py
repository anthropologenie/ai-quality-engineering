"""The persistent vector-index artifact — FAISS-backed, identity-validated.

Sprint M2.01B: implements the **persistence/foundation stage** of register
capability **M2-02** (*Vector store implementation*), under authorization
**A6**, the FAISS election of Sprint RO-06 / RO-07, and Repository Owner
ruling **RO-08** (`docs/DEFERRED_ITEMS_REGISTER.md` §4.1).

This module builds, persists, loads and identity-validates a vector index. It
performs **no retrieval of any kind**.

Why this is a new module and not `sample_rag/vector_store.py`
--------------------------------------------------------------
`docs/architecture.md` §7 freezes the `VectorStore` Protocol at two methods —
`upsert(chunk_id, vector) -> None` and `query(vector, top_k) -> list[str]` —
and `tests/test_indexer.py::test_1b02_no_vector_store_implementation_is_shipped`
asserts that `sample_rag/vector_store.py` declares that Protocol **and nothing
else**. **RO-08 Decision 2** stages M2-02 rather than splitting it: this sprint
builds the persistence foundation and **shall not discharge M2-02**, and
Sprint M2.01C supplies `query` and the query-time nearest-neighbour behaviour.

So this module is deliberately **not** a `VectorStore`. It implements no
`query`, and it therefore does not satisfy the Protocol — which
`test_1b02_a_partial_store_does_not_satisfy_the_protocol` already states is
not conformance. RO-08 records that non-conformance as the authorized,
deliberately staged state, not as a contract violation. The seam is left
exactly as frozen, with no implementation shipped beside it.

Criterion A-5 — the vector-store-library transition, recorded
--------------------------------------------------------------
`docs/MILESTONE_1A.md` criterion A-5 — *"Zero imports of any embedding,
vector-store, or LLM-evaluation library anywhere in the codebase"* — has been
binding since Milestone 1A. Its **embedding-library** portion lapsed at Sprint
M2.01A, in `sample_rag/embedding.py` alone
(`docs/DEFERRED_ITEMS_REGISTER.md` §4).

**Sprint M2.01B is the authorized transition point for the vector-store-library
portion**, for M2-02, and this module is where it applies: `import faiss`
below is the repository's second and last standing A-5 exception. The scope is
exactly as narrow as M2.01A's:

    embedding library      -> `sample_rag/embedding.py` only  (M2.01A)
    vector-store library   -> this module only                (M2.01B)
    LLM SDK                -> still barred (M2-06)
    LLM-evaluation library -> still barred (M2-07, M2-08, M3-06)

`tests/test_vector_index.py` holds the AST allowlist for this module and a
glob check that no other `sample_rag/*.py` imports `faiss`, following the
pattern `tests/test_indexer.py` established for the embedding seam. The
package is **`faiss-cpu`**, never `faiss-gpu`: `docs/roadmap.md` §7 places
*"GPU optimization"* out of scope entirely, and `sample_rag/embedding.py`
already fixes embedding execution to CPU for reproducibility.

What identifies an index, and why each field is here
-----------------------------------------------------
**RO-08 Decision 3** fixes the Milestone 2A freshness/compatibility basis and
**bounds it** to eight signals. `VectorIndexIdentity` carries those signals and
no others. Every field has a compatibility purpose:

    document_hashes    -- the corpus changed              (existing manifest identity)
    chunk_ids          -- the chunk set or its order changed
    vector_count       -- the chunk count changed
    chunk_fingerprint  -- chunk *content* changed         (RO-08 Decision 1)
    model_id           -- a different embedding model produced these vectors
    model_revision     -- the same model at a different checkpoint
    dimension          -- the vectors are not the width this index holds
    index_type/metric  -- the FAISS configuration changed

**No timestamp of any kind is recorded, and none may be.** RO-08 Decision 3
bars `created_at`, persisted `documents[].indexed`, last-indexed timestamps
and timestamp-based identity; `docs/MILESTONE_1A.md` build item 1 removed
`created_at` because a timestamp *"would make the manifest non-deterministic
for an identical corpus generated at two different times"*, and ruling **R-02**
removed `documents[].indexed` from the persisted schema. JobOps SQLite
freshness remains Milestone 2B (**1B-06**, reallocated by **RO-06**).

Why `IndexFlatIP`
------------------
Flat, exact, and untrained. There is no clustering, no quantization, no
sampling and no random initialization anywhere in its construction, so an
index built twice from identical vectors holds identical contents — which is
what `docs/architecture.md` §9's determinism discipline requires of a
repository artifact, and what a partitioned or graph index (IVF, HNSW) could
not offer without a trained, seed-dependent structure.

Inner product is chosen because `sample_rag/embedding.py`'s provider returns
**unit-norm** vectors by the published checkpoint's own `Normalize` module, and
for unit-norm vectors inner product is cosine similarity. **Selecting a metric
is an index-construction property, not a retrieval act**: nothing in this
module searches, ranks or returns neighbours.

Determinism — what is claimed, and what is not
------------------------------------------------
Following the precedent `sample_rag/embedding.py` sets for the embedding model:

**Claimed — semantic/index determinism.** Identical chunks, vectors, model
identity and configuration produce an equal `VectorIndexIdentity`, an equal
vector count, and bytewise-equal reconstructed vectors. The metadata file is
byte-identical, because this module serializes it with the repository's own
fixed `json.dumps(..., indent=2) + "\n"` call.

**Not claimed — byte identity of the FAISS binary.** Third-party binary
serialization is not a repository byte-identity contract, and no repository
authority establishes one for it. No specification asserts it.
"""

import hashlib
import json

from dataclasses import dataclass
from pathlib import Path

import faiss
import numpy

# The FAISS configuration this repository builds. Identity-relevant: an index
# built under a different type or metric holds different structure, so both
# participate in compatibility validation (RO-08 Decision 3's *"relevant FAISS
# index configuration / type"*).
VECTOR_INDEX_TYPE = "IndexFlatIP"
VECTOR_INDEX_METRIC = "inner_product"

# The two files that constitute the artifact. Separated because they are
# different kinds of thing: one is FAISS's own binary serialization, which this
# repository does not own the format of, and one is repository metadata in the
# repository's own canonical JSON. Merging them would either embed a binary
# blob in JSON or hide repository identity inside a third-party container.
FAISS_INDEX_FILENAME = "index.faiss"
INDEX_METADATA_FILENAME = "index_metadata.json"

# Container version, on the container rather than on entries — the convention
# `sample_rag/chunks.json` (`schema_version`) and `sample_rag/knowledge_manifest.json`
# (`manifest_version`) both follow, and which `docs/CHUNK_SERIALIZATION_PLAN.md`
# §P7 records as family-scoped rather than repository-wide.
METADATA_SCHEMA_VERSION = "1.0"

# The default location for a built artifact, expressed so callers agree on one
# path rather than each inventing one. **No artifact is committed at Sprint
# M2.01B** — this constant names where one would be written, and every
# specification writes to a temporary directory instead.
VECTOR_INDEX_ROOT = Path(__file__).resolve().parent / "vector_index"


class VectorIndexPersistenceError(Exception):
    """Raised when the persisted artifact cannot be written, read, or trusted.

    Scoped to persistence: a missing directory or file, unreadable or
    unparseable metadata, a FAISS binary FAISS itself refuses, or the two files
    disagreeing about what they hold. **Not** reused for identity mismatch,
    which is `VectorIndexCompatibilityError` and is a different engineering
    fact — the artifact is intact but describes other inputs.

    Two separately-scoped exceptions rather than a hierarchy, following
    `scripts/build_chunks.py`, which carries `ChunkSerializationError` (I/O and
    parse) and `ChunkValidationError` (structure) as independent `Exception`
    subclasses for the same reason, and `sample_rag/embedding.py`'s
    `EmbeddingModelUnavailableError` for the same naming discipline.
    """


class VectorIndexCompatibilityError(Exception):
    """Raised when an index does not identify the inputs it is being used for.

    The stale-index and incompatibility surface. Carries the **names of the
    signals that differ**, so a caller learns which of RO-08 Decision 3's
    signals moved rather than only that something did.
    """


def chunk_fingerprint(chunks) -> str:
    """The **RO-08 Decision 1** index-local chunk-content fingerprint.

    Recorded exactly, because RO-08 requires this sprint to state the algorithm,
    the serialization and the input construction, and explicitly does **not**
    make any of the three repository authority:

    * **Input construction** — the ordered sequence of `(chunk["id"],
      chunk["text"])` pairs, in the order `chunks` is given. Order is part of
      the identity: the same chunks in a different order are a different index,
      because vector position is what maps back to a chunk id.
    * **Serialization** — `json.dumps(pairs, ensure_ascii=False,
      separators=(",", ":"))`, UTF-8 encoded. JSON because it is already the
      repository's serialization mechanism, and because its escaping makes the
      encoding **injective**: no chunk text, whatever separators or newlines it
      contains, can imitate the framing between two chunks. A plain `id:text`
      join could. Compact separators because a digest input is never read by a
      person; `ensure_ascii=False` so the encoded bytes are the text's own
      UTF-8 rather than an escaped transliteration.
    * **Algorithm** — SHA-256, full 64-character hex digest. SHA-256 is the
      repository's only content-hash function (`scripts/build_manifest.py`
      `compute_sha256`, `generate_document_id`; `sample_rag/chunker.py`
      `generate_chunk_id`). The digest is **not truncated**: truncation in this
      repository marks an *identifier* (12 and 16 characters), while
      `documents[].hash` — the existing **content** hash, which this is the
      analogue of — is stored full-width.

    **Scope, per RO-08 Decision 1.** This value lives only in the persisted
    vector-index metadata. It does not modify `sample_rag/chunks.json`, does not
    modify the chunk contract, does not redefine chunk ids, adds no
    corpus-level metadata to the chunk container, amends no part of
    `ADR-0001`, and replaces no part of the document identity model. **It is an
    index-local identity mechanism, not a canonical corpus identity.**

    Why it is needed at all: chunk ids are derived from position —
    `sample_rag/chunker.py` `generate_chunk_id`, *"not from chunk content"* —
    and `documents[].hash` covers source **bytes**, not extracted text
    (`docs/DATA_QUALITY_VALIDATION_PLAN.md` §8.8 item 2). A chunker or
    extraction change can therefore rewrite chunk text while document hashes,
    chunk ids and chunk count all stay identical. This digest is what sees it.
    """
    pairs = [[chunk["id"], chunk["text"]] for chunk in chunks]
    serialized = json.dumps(pairs, ensure_ascii=False, separators=(",", ":"))

    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class VectorIndexIdentity:
    """The signals that decide whether an index may be used for given inputs.

    Exactly **RO-08 Decision 3**'s bounded set, and nothing else. Frozen, like
    `Document`, `Chunk`, `RetrievalResult` and `Index` before it, so a consumer
    cannot rebind a field to make an incompatible index appear current.

    `chunk_ids` and `document_hashes` are tuples rather than lists so the value
    is hashable and comparable as a whole; `document_hashes` holds
    `(document_id, hash)` pairs sorted by id, so two identities built from the
    same manifest in different iteration orders compare equal.
    """

    model_id: str
    model_revision: str
    dimension: int
    index_type: str
    metric: str
    vector_count: int
    chunk_ids: tuple
    chunk_fingerprint: str
    document_hashes: tuple

    def mismatches(self, other) -> list:
        """Return the names of the signals on which `self` and `other` differ.

        A **report rather than a bool**, following every W6 predicate in
        `tests/test_data_quality.py` and for the same reason: a caller that
        learns *which* signal moved can act on it, and a specification can
        assert the precise cause rather than the mere fact of failure.

        Ordered from corpus-level to configuration-level, so the first entry is
        the most upstream cause rather than an arbitrary one.
        """
        differences = []

        for signal in (
            "document_hashes",
            "chunk_ids",
            "vector_count",
            "chunk_fingerprint",
            "model_id",
            "model_revision",
            "dimension",
            "index_type",
            "metric",
        ):
            if getattr(self, signal) != getattr(other, signal):
                differences.append(signal)

        return differences


def identity_for(index, chunks, documents, embedding_provider) -> VectorIndexIdentity:
    """Build the `VectorIndexIdentity` the given inputs would produce.

    The expected-state constructor: a caller computes this from the corpus it
    *intends* to use, then compares it against a loaded artifact's identity.
    Building an index and validating one therefore derive identity through the
    same function, so the two cannot drift apart — the duplication
    `docs/ENGINEERING_TRACEABILITY_REGISTER.md` §5 rates **High** risk.

    `model_id` and `model_revision` are read from the provider **defensively**,
    with `getattr`, exactly as `sample_rag/indexer.py` reads `dimension` and
    `placeholder`. `docs/architecture.md` §7 freezes `EmbeddingProvider` at a
    single `embed` method, so no attribute may be *required* of a provider;
    `BGEEmbeddingProvider` declares both, and a provider that declares neither
    records the empty string rather than failing. This is why identity is
    supplied at build time at all: `Index` carries vectors, a width and a stub
    marker, and **no model identity** — the Index alone cannot say what
    embedded it.

    `documents` is the Knowledge Manifest's `documents[]` — its `id` and `hash`
    fields, the repository's existing document identity model, used rather than
    re-derived.
    """
    return VectorIndexIdentity(
        model_id=getattr(embedding_provider, "model_id", "") or "",
        model_revision=getattr(embedding_provider, "revision", "") or "",
        dimension=index.dimension,
        index_type=VECTOR_INDEX_TYPE,
        metric=VECTOR_INDEX_METRIC,
        vector_count=len(chunks),
        chunk_ids=tuple(chunk["id"] for chunk in chunks),
        chunk_fingerprint=chunk_fingerprint(chunks),
        document_hashes=tuple(
            sorted((document["id"], document["hash"]) for document in documents)
        ),
    )


class FaissVectorIndex:
    """A FAISS index plus the repository identity that says what it holds.

    The minimum lifecycle Sprint M2.01B was briefed to establish, and no more:

        build   -> from an `Index` (`sample_rag/indexer.py`) and its inputs
        save    -> two files in one directory
        load    -> back from that directory, cross-validated
        validate-> against the identity the intended inputs would produce

    There is no `query`, no `search`, no `upsert`. `upsert` is absent because
    this artifact is built whole from a chunk corpus and rebuilt when that
    corpus changes — incremental mutation is a `VectorStore` behaviour whose
    contract Sprint M2.01C completes.
    """

    def __init__(self, faiss_index, identity: VectorIndexIdentity):
        """Wrap an already-built FAISS index and its identity.

        Not the construction path — `build` and `load` are. Direct construction
        exists so those two classmethods share one assembly point.
        """
        self._faiss_index = faiss_index
        self._identity = identity

    @property
    def identity(self) -> VectorIndexIdentity:
        """What this index says it holds."""
        return self._identity

    @property
    def vector_count(self) -> int:
        """How many vectors FAISS actually holds.

        Read from FAISS rather than from the metadata, so a caller can compare
        the two. `load` does exactly that.
        """
        return self._faiss_index.ntotal

    @classmethod
    def build(cls, index, chunks, documents, embedding_provider):
        """Build the FAISS index over `index`'s vectors, in `chunks` order.

        `chunks` fixes the order, and the order is the mapping: FAISS addresses
        vectors by ordinal position, so position *i* holds the vector for
        `chunks[i]["id"]`, which is what `identity.chunk_ids` records and what
        `chunk_id_at` reads back. Taking the order from the chunk collection
        rather than from `index.vectors` keeps it the Chunk Contract's order —
        `docs/CHUNK_CONTRACT.md` §17 invariants 4–5 — rather than a dict's
        insertion order.

        Every chunk must have a vector. A chunk without one is the DQ-7
        coverage failure `docs/DATA_QUALITY_VALIDATION_PLAN.md` §8.1 defines,
        arriving at the persistence stage; it is raised as an incompatibility
        between the Index and the chunks rather than silently indexing a
        shorter corpus than the caller asked for.

        Vectors are converted to `float32`, which is FAISS's storage type. The
        conversion is lossless for values that came from the model: the
        provider's `float` components are widened `float32` to begin with
        (`sample_rag/embedding.py` converts NumPy `float32` to `float` to
        satisfy `docs/architecture.md` §7's `list[float]`).
        """
        missing = [chunk["id"] for chunk in chunks if chunk["id"] not in index.vectors]
        if missing:
            raise VectorIndexCompatibilityError(
                f"chunks have no vector in the supplied Index: {sorted(missing)}"
            )

        identity = identity_for(index, chunks, documents, embedding_provider)
        faiss_index = faiss.IndexFlatIP(identity.dimension)

        if chunks:
            vectors = numpy.array(
                [index.vectors[chunk["id"]] for chunk in chunks], dtype=numpy.float32
            )
            faiss_index.add(vectors)

        return cls(faiss_index, identity)

    def chunk_id_at(self, position: int) -> str:
        """The chunk id whose vector FAISS holds at `position`.

        **The vector → chunk mapping**, in the artifact's own vocabulary rather
        than by reaching into `identity.chunk_ids` — the same reason
        `sample_rag/indexer.py` exposes `Index.covers` instead of publishing
        its `vectors` mapping as the way to ask about coverage.

        This is a mapping lookup by ordinal, not a search: it answers *what is
        stored here*, never *what is nearest to this*.
        """
        return self._identity.chunk_ids[position]

    def validate(self, expected: VectorIndexIdentity) -> None:
        """Raise unless this index identifies exactly the `expected` inputs.

        The stale-index and incompatibility gate. Every RO-08 Decision 3 signal
        participates, and no signal outside that set exists to participate.
        Raising rather than returning follows `scripts/build_chunks.py`'s
        `validate_chunks`, the repository's existing shape for a gate a caller
        must pass before using an artifact.
        """
        differences = self._identity.mismatches(expected)

        if differences:
            raise VectorIndexCompatibilityError(
                "persisted vector index does not match the intended inputs; "
                f"differing signals: {differences}. A rebuild is required."
            )

    def save(self, directory) -> None:
        """Persist the artifact into `directory`, creating it if absent.

        Two files, written in one place:

            index.faiss           FAISS's own serialization of the index
            index_metadata.json   this repository's identity metadata

        The metadata is written with `json.dumps(..., indent=2) + "\\n"` —
        the exact call `scripts/build_chunks.py` `write_chunks` and
        `scripts/build_manifest.py` `write_manifest` use, so the repository has
        one canonical JSON form rather than a second one invented here. That
        fixed call is also why the metadata file is byte-identical across
        rebuilds from identical inputs, while the FAISS binary carries no such
        claim.
        """
        directory = Path(directory)

        try:
            directory.mkdir(parents=True, exist_ok=True)
            faiss.write_index(
                self._faiss_index, str(directory / FAISS_INDEX_FILENAME)
            )
            (directory / INDEX_METADATA_FILENAME).write_text(
                json.dumps(self._metadata_payload(), indent=2) + "\n",
                encoding="utf-8",
            )
        except VectorIndexPersistenceError:
            raise
        except Exception as error:
            raise VectorIndexPersistenceError(
                f"could not persist the vector index to {directory}: {error}"
            ) from error

    def _metadata_payload(self) -> dict:
        """The metadata file's content, in a stable field order.

        `schema_version` first, following both existing repository containers.
        Identity is grouped by what it describes — the embedding, the FAISS
        configuration, the chunk material, the documents — so a reader can see
        what each field is for without consulting this module.
        """
        return {
            "schema_version": METADATA_SCHEMA_VERSION,
            "index_type": self._identity.index_type,
            "metric": self._identity.metric,
            "embedding": {
                "model_id": self._identity.model_id,
                "model_revision": self._identity.model_revision,
                "dimension": self._identity.dimension,
            },
            "vector_count": self._identity.vector_count,
            "chunk_fingerprint": self._identity.chunk_fingerprint,
            "chunk_ids": list(self._identity.chunk_ids),
            "documents": [
                {"id": document_id, "hash": document_hash}
                for document_id, document_hash in self._identity.document_hashes
            ],
        }

    @classmethod
    def load(cls, directory):
        """Load the artifact from `directory`, cross-validating its two files.

        Both files are required. A missing one is reported as a missing
        artifact naming a rebuild, because that is the caller's actual remedy —
        the artifact is derived, and nothing about the repository's committed
        state is lost by rebuilding it.

        **The two files are then checked against each other**, which is the
        consistency guarantee a two-file artifact owes: FAISS's own `ntotal`
        and `d` must agree with the metadata's `vector_count` and `dimension`,
        and the recorded `chunk_ids` must be as long as the index is deep. A
        binary and a metadata file that disagree describe no coherent index,
        and accepting the pair would let position → chunk-id mapping silently
        point at the wrong chunk. That failure is persistence, not
        incompatibility: nothing here is being compared to an intended corpus
        yet.
        """
        directory = Path(directory)
        index_path = directory / FAISS_INDEX_FILENAME
        metadata_path = directory / INDEX_METADATA_FILENAME

        for required in (index_path, metadata_path):
            if not required.is_file():
                raise VectorIndexPersistenceError(
                    f"vector index artifact is incomplete — {required} is missing. "
                    "A rebuild is required."
                )

        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except Exception as error:
            raise VectorIndexPersistenceError(
                f"vector index metadata at {metadata_path} could not be read: {error}"
            ) from error

        try:
            identity = cls._identity_from_metadata(metadata)
        except Exception as error:
            raise VectorIndexPersistenceError(
                f"vector index metadata at {metadata_path} is not well formed: {error}"
            ) from error

        try:
            faiss_index = faiss.read_index(str(index_path))
        except Exception as error:
            raise VectorIndexPersistenceError(
                f"FAISS index at {index_path} could not be read: {error}"
            ) from error

        if faiss_index.ntotal != identity.vector_count:
            raise VectorIndexPersistenceError(
                f"artifact is inconsistent — FAISS holds {faiss_index.ntotal} vectors "
                f"but metadata records {identity.vector_count}. A rebuild is required."
            )

        if faiss_index.d != identity.dimension:
            raise VectorIndexPersistenceError(
                f"artifact is inconsistent — FAISS vectors are {faiss_index.d} wide "
                f"but metadata records {identity.dimension}. A rebuild is required."
            )

        if len(identity.chunk_ids) != identity.vector_count:
            raise VectorIndexPersistenceError(
                f"artifact is inconsistent — metadata maps {len(identity.chunk_ids)} "
                f"chunk ids onto {identity.vector_count} vectors. A rebuild is required."
            )

        return cls(faiss_index, identity)

    @staticmethod
    def _identity_from_metadata(metadata) -> VectorIndexIdentity:
        """Reconstruct the identity value from a loaded metadata mapping.

        Every field is read explicitly rather than splatted, so a metadata file
        missing one fails here — inside `load`'s guarded block, as a
        well-formedness failure — rather than producing an identity with a
        silently defaulted signal that would then compare equal to something.
        """
        embedding = metadata["embedding"]

        return VectorIndexIdentity(
            model_id=embedding["model_id"],
            model_revision=embedding["model_revision"],
            dimension=embedding["dimension"],
            index_type=metadata["index_type"],
            metric=metadata["metric"],
            vector_count=metadata["vector_count"],
            chunk_ids=tuple(metadata["chunk_ids"]),
            chunk_fingerprint=metadata["chunk_fingerprint"],
            document_hashes=tuple(
                (document["id"], document["hash"]) for document in metadata["documents"]
            ),
        )

    def reconstruct(self, position: int) -> list:
        """Return the stored vector at `position`, as `list[float]`.

        Reads a vector **back out of storage by ordinal**, which is what lets a
        specification prove that two independently built indexes hold equal
        contents without claiming byte identity of FAISS's serialization.

        It is not a search and cannot become one: it takes a position, never a
        query vector, and returns one stored vector rather than a ranked
        neighbourhood.
        """
        return [float(component) for component in self._faiss_index.reconstruct(position)]
