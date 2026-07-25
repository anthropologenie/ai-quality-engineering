"""Chunk collection serialization, persistence, and loading.

Sprint P2.3.2: implements the serializer designed by the approved Chunk
Serialization Plan (docs/CHUNK_SERIALIZATION_PLAN.md), realizing the
container recommended by docs/CHUNK_CONTRACT.md §19 and frozen by
docs/adr/ADR-0001-chunk-persistent-representation.md.

Construction only: serializes an already-constructed, already-ordered
`list[Chunk]` (Sprint P2.2, sample_rag/chunker.py) into the canonical
sample_rag/chunks.json artifact, and loads it back as a plain Mapping. No
multi-document orchestration and no runtime pipeline logic — mirrors the
role scripts/build_manifest.py already plays for the Knowledge Manifest.

Sprint P2.4.1: implements the structural validator designed by the approved
Chunk Validation Plan (docs/CHUNK_VALIDATION_PLAN.md), realizing the
Representation / Entity / Collection layers over an already-loaded Chunk
collection Mapping. Read-only: validation never touches the filesystem and
accepts any already-loaded, mapping-like collection. Referential integrity
against knowledge_manifest.json and any check requiring Document text are
explicitly deferred (docs/CHUNK_VALIDATION_PLAN.md §P5, §P1.4).
"""

import json
from collections.abc import Mapping
from pathlib import Path

from sample_rag.chunker import Chunk

SAMPLE_RAG_ROOT = Path(__file__).resolve().parent.parent / "sample_rag"
SCHEMA_VERSION = "1.0"
CHUNKS_PATH = SAMPLE_RAG_ROOT / "chunks.json"
REQUIRED_CHUNK_FIELDS = {
    "id": str,
    "document_id": str,
    "text": str,
    "chunk_index": int,
    "character_start": int,
    "character_end": int,
}


class ChunkSerializationError(Exception):
    """Raised when a Chunk collection cannot be persisted to or loaded from disk.

    Scoped exclusively to serialization I/O and JSON parsing failures
    (docs/CHUNK_SERIALIZATION_PLAN.md §P3.5). Not reused for structural or
    referential validation, which belongs to Sprint P2.4.
    """


class ChunkValidationError(Exception):
    """Raised when a persisted Chunk collection fails to conform to the
    frozen Chunk Contract (docs/CHUNK_CONTRACT.md) or its serialized
    container shape (docs/CHUNK_SERIALIZATION_PLAN.md).

    Independent of ChunkConstructionError (sample_rag/chunker.py) and
    ChunkSerializationError (above) — a direct Exception subclass, not part
    of a shared validation hierarchy (docs/CHUNK_VALIDATION_PLAN.md §P6.2).
    """


def serialize_chunk(chunk: Chunk) -> dict:
    """Serialize a single Chunk into a plain, JSON-serializable mapping.

    Direct field-by-field mapping in docs/CHUNK_CONTRACT.md §8 order. No
    value transformation, no validation, no enrichment.
    """
    return {
        "id": chunk.id,
        "document_id": chunk.document_id,
        "text": chunk.text,
        "chunk_index": chunk.chunk_index,
        "character_start": chunk.character_start,
        "character_end": chunk.character_end,
    }


def assemble_chunk_collection(chunks: list[Chunk]) -> dict:
    """Assemble the in-memory Chunk collection from an ordered list of Chunks.

    Pure transformation: wraps the serialized chunks in the frozen container
    (`schema_version` + `chunks[]`), preserving input ordering exactly.
    Performs no filesystem I/O, sorting, or invariant re-checking.
    """
    return {
        "schema_version": SCHEMA_VERSION,
        "chunks": [serialize_chunk(chunk) for chunk in chunks],
    }


def write_chunks(collection: dict) -> None:
    """Deterministically serialize the assembled collection to the canonical artifact.

    Persists `collection` to sample_rag/chunks.json exactly as received:
    UTF-8 encoding, 2-space JSON indentation, insertion-order keys (no
    sorting), and a trailing newline. Performs no validation, recomputation,
    or structural transformation.
    """
    serialized = json.dumps(collection, indent=2) + "\n"
    try:
        CHUNKS_PATH.write_text(serialized, encoding="utf-8")
    except OSError as exc:
        raise ChunkSerializationError(
            f"Unable to write chunk collection to {CHUNKS_PATH}: {exc}"
        ) from exc


def load_chunks() -> Mapping:
    """Read and parse the canonical persisted Chunk collection.

    Reads sample_rag/chunks.json and parses it as JSON. Performs no
    structural contract validation and no mutation or repair. Any failure to
    read or parse the artifact surfaces as ChunkSerializationError.
    """
    try:
        raw = CHUNKS_PATH.read_text(encoding="utf-8")
    except OSError as exc:
        raise ChunkSerializationError(
            f"Unable to read chunk collection at {CHUNKS_PATH}: {exc}"
        ) from exc

    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ChunkSerializationError(
            f"Chunk collection at {CHUNKS_PATH} is not valid JSON: {exc}"
        ) from exc


def _validate_representation(collection: Mapping) -> list:
    """Layer: Serialized Representation. Container structural gate — must
    succeed before any chunk entry is inspected (docs/CHUNK_SERIALIZATION_PLAN.md
    §P2.1; docs/CHUNK_VALIDATION_PLAN.md §P4, Layer 3). Returns the `chunks`
    list on success.
    """
    if "schema_version" not in collection:
        raise ChunkValidationError("Chunk collection is missing required field 'schema_version'.")
    if "chunks" not in collection:
        raise ChunkValidationError("Chunk collection is missing required field 'chunks'.")

    schema_version = collection["schema_version"]
    if not isinstance(schema_version, str):
        raise ChunkValidationError("Chunk collection field 'schema_version' must be a string.")
    if schema_version != SCHEMA_VERSION:
        raise ChunkValidationError(
            f"Chunk collection field 'schema_version' must equal {SCHEMA_VERSION!r}, "
            f"got {schema_version!r}."
        )

    chunks = collection["chunks"]
    if not isinstance(chunks, list):
        raise ChunkValidationError("Chunk collection field 'chunks' must be a list.")

    return chunks


def _validate_chunk_entry(entry: Mapping, index: int) -> None:
    """Layer: Entity. Field and Relational invariants for one chunk entry
    (docs/CHUNK_CONTRACT.md §8, §17 invariants 1-2; docs/CHUNK_VALIDATION_PLAN.md
    §P4, Layer 1). No collection-scoped logic belongs here.
    """
    if not isinstance(entry, Mapping):
        raise ChunkValidationError(f"Chunk entry at index {index} must be an object.")

    for field, expected_type in REQUIRED_CHUNK_FIELDS.items():
        if field not in entry:
            raise ChunkValidationError(
                f"Chunk entry at index {index} is missing required field '{field}'."
            )
        value = entry[field]
        if not isinstance(value, expected_type):
            raise ChunkValidationError(
                f"Chunk entry at index {index} field '{field}' must be of type "
                f"{expected_type.__name__}."
            )

    character_start = entry["character_start"]
    character_end = entry["character_end"]
    text = entry["text"]

    if character_end <= character_start:
        raise ChunkValidationError(
            f"Chunk entry at index {index} is not non-empty: character_end "
            f"({character_end}) must be greater than character_start ({character_start})."
        )
    if len(text) != character_end - character_start:
        raise ChunkValidationError(
            f"Chunk entry at index {index} field 'text' length ({len(text)}) does not "
            f"match character_end - character_start ({character_end - character_start})."
        )


def _validate_collection_invariants(entries: list) -> None:
    """Layer: Collection. Cross-chunk invariants — corpus-wide id uniqueness
    and, per document_id, contiguous chunk_index ordering and non-overlap
    (docs/CHUNK_CONTRACT.md §17 invariants 4-7; docs/CHUNK_VALIDATION_PLAN.md
    §P4, Layer 2). Referential integrity against knowledge_manifest.json is
    explicitly out of scope (docs/CHUNK_VALIDATION_PLAN.md §P5).
    """
    seen_ids = set()
    for entry in entries:
        chunk_id = entry["id"]
        if chunk_id in seen_ids:
            raise ChunkValidationError(f"Duplicate chunk id {chunk_id!r} detected.")
        seen_ids.add(chunk_id)

    by_document: dict = {}
    for entry in entries:
        by_document.setdefault(entry["document_id"], []).append(entry)

    for document_id, document_entries in by_document.items():
        ordered = sorted(document_entries, key=lambda e: e["chunk_index"])

        expected_indices = list(range(len(ordered)))
        actual_indices = [e["chunk_index"] for e in ordered]
        if actual_indices != expected_indices:
            raise ChunkValidationError(
                f"Chunk indices for document_id {document_id!r} are not contiguous "
                f"from 0..N-1: got {actual_indices}."
            )

        for i in range(len(ordered) - 1):
            current, following = ordered[i], ordered[i + 1]
            if current["character_start"] > following["character_start"]:
                raise ChunkValidationError(
                    f"Chunk order for document_id {document_id!r} does not match "
                    f"ascending character_start at chunk_index {following['chunk_index']}."
                )
            if current["character_end"] > following["character_start"]:
                raise ChunkValidationError(
                    f"Chunks at chunk_index {current['chunk_index']} and "
                    f"{following['chunk_index']} overlap for document_id {document_id!r}."
                )


def validate_chunks(collection: Mapping) -> Mapping:
    """Verify that `collection` conforms to the frozen Chunk Contract
    (docs/CHUNK_CONTRACT.md §17) and the persisted container shape
    (docs/CHUNK_SERIALIZATION_PLAN.md §P2.1).

    Read-only: performs no mutation, normalization, or copying. Returns the
    exact same object on success. Raises ChunkValidationError on the first
    violation encountered, in Representation -> Entity -> Collection order
    (docs/CHUNK_VALIDATION_PLAN.md §P4.1), so this function never depends on
    filesystem I/O and can validate persisted collections, test fixtures, or
    synthetic malformed collections alike.
    """
    chunks = _validate_representation(collection)

    for index, entry in enumerate(chunks):
        _validate_chunk_entry(entry, index)

    _validate_collection_invariants(chunks)

    return collection
