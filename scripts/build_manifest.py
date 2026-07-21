"""Corpus discovery and metadata extraction (Sprint 1A.1, P1.1).

Discovers supported documents under sample_rag/documents/, normalizes their
paths, computes content hashes, and builds in-memory document entries. This
is the first stage of the Knowledge Manifest Generator — manifest assembly,
serialization, and validation are later milestones (see docs/MILESTONE_1A.md).
"""

import hashlib
from pathlib import Path

SAMPLE_RAG_ROOT = Path(__file__).resolve().parent.parent / "sample_rag"
DOCUMENTS_ROOT = SAMPLE_RAG_ROOT / "documents"
SUPPORTED_EXTENSIONS = {".docx", ".md", ".txt"}
HASH_CHUNK_SIZE = 8192


def discover_documents(documents_root: Path) -> list[Path]:
    """Find supported documents under documents_root.

    Skips hidden directories, dot-prefixed files, and __pycache__ directories.
    """
    discovered = []
    for path in documents_root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        if any(part.startswith(".") or part == "__pycache__" for part in path.relative_to(documents_root).parts):
            continue
        discovered.append(path)
    return discovered


def normalize_source_path(path: Path, sample_rag_root: Path) -> str:
    """Return path relative to sample_rag/ using POSIX separators."""
    return path.relative_to(sample_rag_root).as_posix()


def compute_sha256(path: Path) -> str:
    """Compute the lowercase hex SHA-256 digest of a file's contents."""
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(HASH_CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()


def generate_document_id(source: str) -> str:
    """Generate the deterministic document ID for a normalized source path."""
    return hashlib.sha256(source.encode("utf-8")).hexdigest()[:12]


def build_document_entry(document_id: str, source: str, file_hash: str) -> dict:
    """Build a single in-memory document entry matching the documented schema."""
    return {
        "id": document_id,
        "source": source,
        "hash": file_hash,
        "indexed": False,
    }


def main() -> None:
    discovered_paths = discover_documents(DOCUMENTS_ROOT)
    normalized_sources = sorted(
        normalize_source_path(path, SAMPLE_RAG_ROOT) for path in discovered_paths
    )

    entries = []
    for source in normalized_sources:
        absolute_path = SAMPLE_RAG_ROOT / source
        file_hash = compute_sha256(absolute_path)
        document_id = generate_document_id(source)
        entries.append(build_document_entry(document_id, source, file_hash))

    for entry in entries:
        print(entry)


if __name__ == "__main__":
    main()
