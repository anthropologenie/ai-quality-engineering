"""Chunk collection serialization, persistence, and loading.

Sprint P2.3.2: implements the serializer designed by the approved Chunk
Serialization Plan (docs/CHUNK_SERIALIZATION_PLAN.md), realizing the
container recommended by docs/CHUNK_CONTRACT.md §19 and frozen by
docs/adr/ADR-0001-chunk-persistent-representation.md.

Construction only: serializes an already-constructed, already-ordered
`list[Chunk]` (Sprint P2.2, sample_rag/chunker.py) into the canonical
sample_rag/chunks.json artifact, and loads it back as a plain Mapping. No
structural or referential validation (Sprint P2.4), no multi-document
orchestration, and no runtime pipeline logic — mirrors the role
scripts/build_manifest.py already plays for the Knowledge Manifest.
"""

import json
from collections.abc import Mapping
from pathlib import Path

from sample_rag.chunker import Chunk

SAMPLE_RAG_ROOT = Path(__file__).resolve().parent.parent / "sample_rag"
SCHEMA_VERSION = "1.0"
CHUNKS_PATH = SAMPLE_RAG_ROOT / "chunks.json"


class ChunkSerializationError(Exception):
    """Raised when a Chunk collection cannot be persisted to or loaded from disk.

    Scoped exclusively to serialization I/O and JSON parsing failures
    (docs/CHUNK_SERIALIZATION_PLAN.md §P3.5). Not reused for structural or
    referential validation, which belongs to Sprint P2.4.
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
