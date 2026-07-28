"""Deterministic Document construction from the canonical repository corpus.

Sprint P3.1.4: implements the `Knowledge Source` pipeline component
(docs/architecture.md §5, `KnowledgeSource.load() -> List[Document]`) against
the approved Document Contract (docs/DOCUMENT_CONTRACT.md §8.7) and the
approved Document Construction Plan (docs/DOCUMENT_CONSTRUCTION_PLAN.md).

Construction only: no chunking, no serialization, no independent validation
component, no repository mutation. The Knowledge Manifest is read, never
written — `scripts/build_manifest.py` owns that lifecycle, including
`documents[].indexed` (Construction Plan §6.2).

Execution stages, one responsibility each (Construction Plan §7):

    knowledge_manifest.json -> manifest entries   (discover_manifest_entries)
    manifest entry          -> repository file    (resolve_source_path)
    repository file         -> raw text           (extract_text)
    raw text                -> normalized text    (normalize_text)
    (id, normalized text)   -> Document           (KnowledgeSource.load)

Identity strategy S1 (Construction Plan §9.1): corpus enumeration is driven by
the Manifest, and `Document.id` is *read* from `documents[].id` — never
generated, rewritten, or normalized here. Knowledge Source is a constructor,
not an identifier authority (Contract §8.4, A5).

Extraction is Python-standard-library only — `zipfile` + `xml.etree.ElementTree`
for `.docx` — per the dependency decision recorded at Sprint P3.1.2.
"""

import json
import re
import xml.etree.ElementTree as ET
import zipfile

from collections.abc import Mapping
from pathlib import Path

from sample_rag.document import Document

SAMPLE_RAG_ROOT = Path(__file__).resolve().parent
KNOWLEDGE_MANIFEST_PATH = SAMPLE_RAG_ROOT / "knowledge_manifest.json"

# Mirrors scripts/build_manifest.py's admissibility gate. Held locally rather
# than imported, so that sample_rag/ takes no dependency on scripts/, which
# docs/architecture.md §6 defines as "not pipeline logic" (Construction Plan
# §9.1, the row on which S1 was selected over S2).
SUPPORTED_EXTENSIONS = {".docx", ".md", ".txt"}

DOCX_MAIN_PART = "word/document.xml"
_WORDPROCESSINGML = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
_DOCX_BODY = f"{_WORDPROCESSINGML}body"
_DOCX_PARAGRAPH = f"{_WORDPROCESSINGML}p"
_DOCX_TEXT = f"{_WORDPROCESSINGML}t"

# A .docx paragraph (w:p) is a block-level element. Rendering each block as a
# blank-line-separated plain-text block is what preserves the source's own
# structure in `Document.text` (normalization rule N1, see normalize_text).
PARAGRAPH_SEPARATOR = "\n\n"

_TRAILING_WHITESPACE = re.compile(r"[ \t]+$", re.MULTILINE)
_EXCESS_BLANK_LINES = re.compile(r"\n{3,}")


class DocumentConstructionError(Exception):
    """Raised when Document construction cannot read the corpus or cannot
    produce a value conforming to docs/DOCUMENT_CONTRACT.md §8.7."""


def discover_manifest_entries() -> list[Mapping]:
    """Read the canonical Knowledge Manifest and return its `documents[]` entries.

    Strategy S1 (Construction Plan §9.1): the Manifest — not the filesystem —
    is the corpus enumeration. The artifact is read directly with `json`; no
    identifier is recomputed and nothing is imported from `scripts/`.

    Entry order is preserved exactly as persisted and is never re-sorted (§11.2,
    Task 3). Only the two fields construction consumes (`id`, `source`) are
    checked, and only for admissibility — this is not, and must not grow into,
    a second implementation of `validate_manifest` (Construction Plan §10.1,
    "Validation failures" row).
    """
    try:
        with KNOWLEDGE_MANIFEST_PATH.open("r", encoding="utf-8", newline="") as f:
            raw = f.read()
    except OSError as exc:
        raise DocumentConstructionError(
            f"Unable to read Knowledge Manifest at {KNOWLEDGE_MANIFEST_PATH}: {exc}"
        ) from exc

    try:
        manifest = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise DocumentConstructionError(
            f"Knowledge Manifest at {KNOWLEDGE_MANIFEST_PATH} is not valid JSON: {exc}"
        ) from exc

    if not isinstance(manifest, Mapping):
        raise DocumentConstructionError("Knowledge Manifest must be a JSON object.")

    documents = manifest.get("documents")
    if not isinstance(documents, list):
        raise DocumentConstructionError("Knowledge Manifest field 'documents' must be a list.")

    for index, entry in enumerate(documents):
        if not isinstance(entry, Mapping):
            raise DocumentConstructionError(
                f"Manifest document entry at index {index} must be an object."
            )
        for field in ("id", "source"):
            if not isinstance(entry.get(field), str):
                raise DocumentConstructionError(
                    f"Manifest document entry at index {index} field '{field}' must be a string."
                )

    return documents


def resolve_source_path(source: str) -> Path:
    """Resolve a manifest `documents[].source` to its repository file.

    `source` is stored relative to `sample_rag/` with POSIX separators
    (`scripts/build_manifest.py` `normalize_source_path`), so resolution is a
    deterministic join. Raises when the source escapes the corpus root, when the
    extension is outside the approved set, or when the Manifest names a file the
    corpus does not contain — all Input failures under Construction Plan §10.1.
    """
    relative = Path(source)

    # Corpus-root containment (ADR-P3.1.7.2-F2, accepted Option A). Construction
    # Plan §4.1 defines the corpus root as fixing "which filesystem items are
    # corpus items at all"; the extension gate below enforces one half of that
    # boundary and this enforces the other. It belongs to Construction rather
    # than Data Quality Validation because it is an *intra-artifact* invariant:
    # it reads only the configured corpus root and the single manifest entry
    # being processed, never the corpus as a whole — the criterion Contract §8.5
    # uses to route cross-artifact checks elsewhere.
    #
    # Deliberately a check on the manifest *value* rather than on resolved
    # filesystem state: `SAMPLE_RAG_ROOT / Path(source)` silently discards the
    # root when `source` is absolute, and `..` traverses out of it.
    if relative.is_absolute() or ".." in relative.parts:
        raise DocumentConstructionError(
            f"Manifest source {source!r} escapes the corpus root at {SAMPLE_RAG_ROOT}; "
            f"a corpus item must resolve beneath it."
        )

    path = SAMPLE_RAG_ROOT / relative

    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise DocumentConstructionError(
            f"Unsupported corpus extension {path.suffix!r} for source {source!r}; "
            f"supported extensions are {sorted(SUPPORTED_EXTENSIONS)}."
        )

    if not path.is_file():
        raise DocumentConstructionError(
            f"Manifest source {source!r} does not resolve to a file at {path}."
        )

    return path


def extract_docx_paragraphs(path: Path) -> list[str]:
    """Extract the ordered block-level paragraph texts from a .docx.

    A .docx is an OOXML package: a ZIP container whose body text lives in
    `word/document.xml`. Each `w:p` is one block-level paragraph; its text is
    the in-document-order concatenation of its `w:t` descendants. Traversal is
    document-ordered and therefore deterministic.

    Only `w:t` character content is read. Constructs that carry text through
    other elements (`w:tab`, `w:br`, footnotes, headers, text boxes) are not
    interpreted; none occurs in the current corpus (verified at Sprint P3.1.2).
    A corpus gaining them would reopen extraction fidelity, as that sprint
    recorded.
    """
    try:
        with zipfile.ZipFile(path) as package:
            document_xml = package.read(DOCX_MAIN_PART)
    except (OSError, zipfile.BadZipFile) as exc:
        raise DocumentConstructionError(
            f"Corpus item {path} is not a readable .docx package: {exc}"
        ) from exc
    except KeyError as exc:
        raise DocumentConstructionError(
            f"Corpus item {path} contains no {DOCX_MAIN_PART} part."
        ) from exc

    try:
        body = ET.fromstring(document_xml).find(_DOCX_BODY)
    except ET.ParseError as exc:
        raise DocumentConstructionError(
            f"Corpus item {path} has an unparseable {DOCX_MAIN_PART}: {exc}"
        ) from exc

    if body is None:
        raise DocumentConstructionError(
            f"Corpus item {path} has no document body in {DOCX_MAIN_PART}."
        )

    return [
        "".join(node.text or "" for node in paragraph.iter(_DOCX_TEXT))
        for paragraph in body.iter(_DOCX_PARAGRAPH)
    ]


def extract_text(path: Path) -> str:
    """Extract raw plain text from a resolved corpus file.

    Dispatches on extension across the approved set. `.docx` is unpacked from
    its OOXML container; `.md` and `.txt` are already plain text and are read
    verbatim. Files are opened with `newline=""` so no newline translation
    happens here — newline handling is normalization's responsibility alone,
    which keeps `normalize_text` a total function of the extracted string
    rather than of the platform (Construction Plan §11.1).
    """
    if path.suffix.lower() == ".docx":
        return PARAGRAPH_SEPARATOR.join(extract_docx_paragraphs(path))

    try:
        with path.open("r", encoding="utf-8", newline="") as f:
            return f.read()
    except OSError as exc:
        raise DocumentConstructionError(f"Corpus item {path} is unreadable: {exc}") from exc
    except UnicodeDecodeError as exc:
        raise DocumentConstructionError(
            f"Corpus item {path} is not valid UTF-8 text: {exc}"
        ) from exc


def normalize_text(text: str) -> str:
    """Normalize extracted text to the stable form carried by `Document.text`.

    A fixed, total function of its input: no clock, locale, environment,
    randomness, or filesystem state participates, satisfying Contract §8.7
    invariant 3 as scoped by Construction Plan §11.1.

    Rules, applied in order:

    N1  Block separation (applied during .docx extraction, recorded here for
        completeness): each `w:p` block-level paragraph becomes one text block,
        blocks joined by a blank line. `.md`/`.txt` already carry their own
        block structure and receive no equivalent step.
    N2  Newline normalization: CRLF and lone CR become LF, so identical content
        normalizes identically regardless of how the source encodes line ends.
    N3  Trailing whitespace: spaces and tabs at end of line are removed, so a
        visually blank line is textually blank (and so N4 can see it).
    N4  Blank-line collapsing: runs of three or more newlines collapse to
        exactly two, giving one uniform block separator across all formats.
    N5  Document trimming: leading and trailing whitespace is removed, so the
        value does not vary with an incidental trailing newline.

    N1 and N4 are what make blank lines a meaningful boundary in the output.
    `sample_rag/chunker.py` splits on blank lines as its *primary*
    structure-aware strategy, with recursive-character splitting reserved as a
    fallback that `docs/MILESTONE_1A.md` build item 3 states is "never the
    default path." Joining .docx paragraphs with a single newline instead would
    leave the resume with no blank line anywhere, collapsing it to one 10.5k
    span and making that fallback the only path ever taken — measured at Sprint
    P3.1.2 §8 and confirmed before this rule was chosen. Chunk granularity
    itself remains the Chunker's concern, not this module's.
    """
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    normalized = _TRAILING_WHITESPACE.sub("", normalized)
    normalized = _EXCESS_BLANK_LINES.sub("\n\n", normalized)
    return normalized.strip()


class KnowledgeSource:
    """Exposes the validated corpus to the pipeline as `Document` values.

    `load()` is the component's entire public surface, exactly as declared by
    docs/architecture.md §5. Knowledge Source performs no chunking, indexing,
    retrieval, embedding, or evaluation, and never mutates the repository.
    """

    def load(self) -> list[Document]:
        """Construct one `Document` per Knowledge Manifest entry, in manifest order.

        Ordering is the Manifest's own `documents[]` order, preserved and never
        re-sorted — the option Construction Plan §11.2 records as already
        deterministic, because `scripts/build_manifest.py` `main()` produced it
        through `sorted(...)`. Determinism holds for any manifest content, since
        the same persisted array always yields the same order.

        `Document.id` is read from the entry and passed through unchanged (A5).
        Failures surface as `DocumentConstructionError` on the first violation
        rather than yielding a partially-constructed or non-conforming value
        (Construction Plan §10.1, §10.2).
        """
        documents = []

        for entry in discover_manifest_entries():
            document_id = entry["id"]
            path = resolve_source_path(entry["source"])
            text = normalize_text(extract_text(path))

            documents.append(Document(id=document_id, text=text))

        return documents
