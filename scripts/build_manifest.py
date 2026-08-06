"""Corpus discovery, metadata extraction, manifest assembly, serialization, and validation.

Sprint 1A.1, P1.1: discovers supported documents under sample_rag/documents/,
normalizes their paths, computes content hashes, and builds in-memory document
entries.

Sprint 1A.1, P1.2.1: assembles those document entries into the in-memory
Knowledge Manifest defined by the frozen contract in docs/MILESTONE_1A.md.

Sprint 1A.1, P1.2.2: deterministically serializes the assembled manifest to
the canonical sample_rag/knowledge_manifest.json artifact.

Sprint 1A.1, P1.3: loads the persisted artifact and validates it against the
frozen structural contract. Loading and validation are separate
responsibilities — validation never touches the filesystem and accepts any
already-loaded, mapping-like manifest. Semantic validation is a later
milestone.
"""

import json
import hashlib
from collections.abc import Mapping
from pathlib import Path

SAMPLE_RAG_ROOT = Path(__file__).resolve().parent.parent / "sample_rag"
DOCUMENTS_ROOT = SAMPLE_RAG_ROOT / "documents"
SUPPORTED_EXTENSIONS = {".docx", ".md", ".txt"}
HASH_CHUNK_SIZE = 8192
MANIFEST_VERSION = "1.0"
KNOWLEDGE_MANIFEST_PATH = SAMPLE_RAG_ROOT / "knowledge_manifest.json"
REQUIRED_DOCUMENT_FIELDS = {
    "id": str,
    "source": str,
    "hash": str,
    "indexed": bool,
    "canonical": bool,
}

# Canonical document designation — Repository Owner decision RO-01.
# First declared at Sprint P3.7.5 (v2.3); redesignated to v3.0 by the approved
# RO-01 decision executed as Milestone 1B's first engineering activity. v2.2 and
# v2.3 remain historical corpus artifacts, catalogued with canonical: false.
# (docs/P3.7.3_Repository_Owner_Constitutional_Decision.md §3.4, §4.4 R-RO-01;
#  docs/P3.7.6_Milestone_1A_Closure_and_Frozen_Baseline.md, appended erratum.)
#
# A Repository Owner corpus-composition decision, declared explicitly rather
# than derived: docs/MILESTONE_1A.md build item 1 keeps *filenames* authoritative
# for document versioning, so parsing `v2_2`/`v2_3` here would have this module
# infer an approval decision from a version string. Approval and version are
# different properties — a corpus with no versions at all would still need one
# document designated canonical — and only the Repository Owner may set it.
#
# Membership is by normalized source path, the same identity `generate_document_id`
# hashes, so designation and document identity cannot disagree.
CANONICAL_SOURCES = frozenset({"documents/resume/Karthik_SR_Resume_v3_0.docx"})


class ManifestValidationError(Exception):
    """Raised when a Knowledge Manifest cannot be loaded or fails structural validation."""


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


def is_canonical(source: str) -> bool:
    """Return whether `source` is a canonical document.

    A total function of the normalized source path and the declared
    `CANONICAL_SOURCES` set — no filesystem access, no filename parsing, no
    ordering dependence — so the designation is reproducible for any corpus.
    A source absent from the declaration is superseded, which makes the default
    for an undesignated corpus "nothing is canonical" rather than a guess.
    """
    return source in CANONICAL_SOURCES


def build_document_entry(document_id: str, source: str, file_hash: str, canonical: bool) -> dict:
    """Build a single in-memory document entry matching the documented schema.

    `canonical` is appended last, after the four fields Sprint 1A.1 froze, so
    existing key order is preserved byte-for-byte and only the new field's
    presence distinguishes this entry from its predecessor.
    """
    return {
        "id": document_id,
        "source": source,
        "hash": file_hash,
        "indexed": False,
        "canonical": canonical,
    }


def assemble_manifest(document_entries: list[dict]) -> dict:
    """Assemble the in-memory Knowledge Manifest from document entries.

    Pure transformation: wraps the document entries produced by corpus
    discovery (P1.1) in the frozen manifest contract (`manifest_version` +
    `documents[]`), preserving entry values and ordering exactly as received.
    Performs no filesystem I/O, serialization, or validation.
    """
    return {
        "manifest_version": MANIFEST_VERSION,
        "documents": list(document_entries),
    }


def write_manifest(manifest: dict) -> None:
    """Deterministically serialize the assembled manifest to the canonical artifact.

    Persists `manifest` to sample_rag/knowledge_manifest.json exactly as
    received: UTF-8 encoding, 2-space JSON indentation, insertion-order keys
    (no sorting), and a trailing newline. Performs no validation,
    recomputation, or structural transformation.
    """
    serialized = json.dumps(manifest, indent=2) + "\n"
    KNOWLEDGE_MANIFEST_PATH.write_text(serialized, encoding="utf-8")


def load_manifest() -> Mapping:
    """Read and parse the canonical persisted Knowledge Manifest.

    Reads sample_rag/knowledge_manifest.json and parses it as JSON. Performs
    no structural contract validation and no mutation or repair. Any failure
    to read or parse the artifact surfaces as ManifestValidationError.
    """
    try:
        raw = KNOWLEDGE_MANIFEST_PATH.read_text(encoding="utf-8")
    except OSError as exc:
        raise ManifestValidationError(
            f"Unable to read manifest at {KNOWLEDGE_MANIFEST_PATH}: {exc}"
        ) from exc

    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ManifestValidationError(
            f"Manifest at {KNOWLEDGE_MANIFEST_PATH} is not valid JSON: {exc}"
        ) from exc


def validate_manifest(manifest: Mapping) -> Mapping:
    """Verify that `manifest` conforms to the frozen Knowledge Manifest structural contract.

    Read-only: performs no mutation, normalization, or copying. Returns the
    exact same object on success. Raises ManifestValidationError on any
    structural contract violation, so this function never depends on
    filesystem I/O and can validate persisted manifests, test fixtures, or
    synthetic malformed manifests alike.
    """
    if "manifest_version" not in manifest:
        raise ManifestValidationError("Manifest is missing required field 'manifest_version'.")
    if "documents" not in manifest:
        raise ManifestValidationError("Manifest is missing required field 'documents'.")

    manifest_version = manifest["manifest_version"]
    if not isinstance(manifest_version, str):
        raise ManifestValidationError("Manifest field 'manifest_version' must be a string.")
    if manifest_version != MANIFEST_VERSION:
        raise ManifestValidationError(
            f"Manifest field 'manifest_version' must equal {MANIFEST_VERSION!r}, "
            f"got {manifest_version!r}."
        )

    documents = manifest["documents"]
    if not isinstance(documents, list):
        raise ManifestValidationError("Manifest field 'documents' must be a list.")

    for index, entry in enumerate(documents):
        if not isinstance(entry, Mapping):
            raise ManifestValidationError(f"Document entry at index {index} must be an object.")
        for field, expected_type in REQUIRED_DOCUMENT_FIELDS.items():
            if field not in entry:
                raise ManifestValidationError(
                    f"Document entry at index {index} is missing required field '{field}'."
                )
            value = entry[field]
            if not isinstance(value, expected_type):
                raise ManifestValidationError(
                    f"Document entry at index {index} field '{field}' must be of type "
                    f"{expected_type.__name__}."
                )

    return manifest


def load_canonical_document_ids() -> set:
    """Return the document ids the persisted Manifest designates canonical.

    Reads the Manifest through the same `validate_manifest(load_manifest())`
    gate every other consumer uses, so a structurally invalid Manifest cannot
    reach retrieval as a silently empty canonical set. Returns ids rather than
    sources because `chunks[].document_id` is what retrieval joins on.

    An empty set is a meaningful, non-exceptional result: it means no document
    is designated, and retrieval tie-breaking then falls through to committed
    corpus order exactly as it did before Sprint P3.7.5.
    """
    manifest = validate_manifest(load_manifest())
    return {entry["id"] for entry in manifest["documents"] if entry["canonical"]}


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
        entries.append(build_document_entry(document_id, source, file_hash, is_canonical(source)))

    manifest = assemble_manifest(entries)
    write_manifest(manifest)


if __name__ == "__main__":
    main()
