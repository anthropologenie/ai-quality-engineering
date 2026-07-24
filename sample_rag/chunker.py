"""Deterministic, structure-aware Chunk construction.

Sprint P2.2.1: implements the `Chunker` pipeline component
(docs/architecture.md §5, `Chunker.chunk(doc: Document) -> List[Chunk]`)
realizing the frozen Chunk Contract (docs/CHUNK_CONTRACT.md) per the approved
Chunk Builder Implementation Plan (docs/CHUNK_BUILDER_IMPLEMENTATION_PLAN.md).

Construction only: no serialization, no validation, no filesystem or network
I/O. `doc` is assumed to expose `.id: str` and `.text: str` at minimum
(Implementation Plan §1.2, §3.2) — the full Document Data Model is out of
scope here (Chunk Contract §20).

Primary strategy is structure-aware splitting along blank-line (section/
field) boundaries. Recursive-character splitting is a fallback used only for
spans that exceed MAX_STRUCTURAL_CHUNK_CHARACTERS, never the default path
(docs/MILESTONE_1A.md, build item 3).
"""

import hashlib
import re

from dataclasses import dataclass

# Implementation decision permitted by the approved Chunk Builder
# Implementation Plan (Chunk Contract §14.5 leaves representation/thresholds
# open to Construction). A conservative Milestone 1A construction value, not
# a Contract field — subject to empirical tuning during later
# retrieval/token-budget work, not during this sprint.
MAX_STRUCTURAL_CHUNK_CHARACTERS = 1000
_BLANK_LINE_PATTERN = re.compile(r"\n[ \t]*\n[ \t\n]*")


class ChunkConstructionError(Exception):
    """Raised when Chunk construction receives malformed input or produces
    a result that violates the frozen Chunk Contract invariants."""


@dataclass(frozen=True)
class Chunk:
    """The six fields frozen by docs/CHUNK_CONTRACT.md §8 — no more, no less."""

    id: str
    document_id: str
    text: str
    chunk_index: int
    character_start: int
    character_end: int


def _validate_document(doc) -> None:
    """Confirm `doc` exposes the minimal assumed shape: `.id: str`, `.text: str`."""
    document_id = getattr(doc, "id", None)
    if not isinstance(document_id, str):
        raise ChunkConstructionError("doc.id must be a str.")

    text = getattr(doc, "text", None)
    if not isinstance(text, str):
        raise ChunkConstructionError("doc.text must be a str.")


def _strip_span(text: str, start: int, end: int) -> tuple[int, int] | None:
    """Trim leading/trailing whitespace from [start, end), returning None if
    the span is empty after trimming."""
    while start < end and text[start].isspace():
        start += 1
    while end > start and text[end - 1].isspace():
        end -= 1
    if start >= end:
        return None
    return start, end


def detect_structural_boundaries(text: str) -> list[tuple[int, int]]:
    """Split text into non-overlapping, non-empty spans along blank-line
    (section/field) boundaries, in reading order.

    This is the primary chunking strategy (docs/MILESTONE_1A.md, build item
    3): structure-aware splitting, not token- or size-driven splitting.
    """
    if text == "":
        return []

    spans = []
    cursor = 0
    for match in _BLANK_LINE_PATTERN.finditer(text):
        sep_start, sep_end = match.span()
        stripped = _strip_span(text, cursor, sep_start)
        if stripped is not None:
            spans.append(stripped)
        cursor = sep_end

    stripped = _strip_span(text, cursor, len(text))
    if stripped is not None:
        spans.append(stripped)

    return spans


def detect_fallback_boundaries(
    text: str, start: int, end: int, max_chars: int
) -> list[tuple[int, int]]:
    """Recursively split [start, end) into spans no larger than max_chars.

    Fallback only, for structural spans that exceed max_chars — never the
    default path. Prefers splitting on whitespace near the max_chars window;
    falls back to a hard split when no whitespace is available.
    """
    if end - start <= max_chars:
        return [(start, end)]

    split_at = text.rfind(" ", start, start + max_chars)
    if split_at <= start:
        split_at = start + max_chars

    spans = [(start, split_at)]

    next_start = split_at
    while next_start < end and text[next_start].isspace():
        next_start += 1

    if next_start < end:
        spans.extend(detect_fallback_boundaries(text, next_start, end, max_chars))

    return spans


def _collect_spans(text: str) -> list[tuple[int, int]]:
    """Structural spans, with the recursive-character fallback applied only
    to spans that exceed MAX_STRUCTURAL_CHUNK_CHARACTERS."""
    spans = []
    for start, end in detect_structural_boundaries(text):
        if end - start <= MAX_STRUCTURAL_CHUNK_CHARACTERS:
            spans.append((start, end))
        else:
            spans.extend(
                detect_fallback_boundaries(text, start, end, MAX_STRUCTURAL_CHUNK_CHARACTERS)
            )
    return spans


def generate_chunk_id(document_id: str, chunk_index: int) -> str:
    """Deterministic chunk id, derived from position — (document_id,
    chunk_index) — not from chunk content (Chunk Contract §10, §14.1)."""
    digest_input = f"{document_id}:{chunk_index}".encode("utf-8")
    return hashlib.sha256(digest_input).hexdigest()[:16]


def build_chunk(document_id: str, chunk_index: int, start: int, end: int, text: str) -> Chunk:
    """Construct a single Chunk value for a known, already-computed span."""
    return Chunk(
        id=generate_chunk_id(document_id, chunk_index),
        document_id=document_id,
        text=text,
        chunk_index=chunk_index,
        character_start=start,
        character_end=end,
    )


def _check_invariants(chunks: list[Chunk]) -> None:
    """Defensive, construction-time enforcement of the frozen Chunk Contract
    §17 invariants.

    Binding during construction: a violation aborts Chunk construction by
    raising ChunkConstructionError, rather than returning a non-conforming
    result. This is defensive invariant enforcement scoped to the chunks a
    single `chunk()` call just built — it is NOT a replacement for the
    standalone Chunk Validation component planned for Sprint P2.4, which
    validates persisted Chunk collections independently of construction.
    """
    seen_ids = set()
    for index, chunk in enumerate(chunks):
        if chunk.character_end <= chunk.character_start:
            raise ChunkConstructionError(f"Chunk at index {index} is not non-empty.")
        if len(chunk.text) != chunk.character_end - chunk.character_start:
            raise ChunkConstructionError(f"Chunk at index {index} text length does not match offsets.")
        if chunk.chunk_index != index:
            raise ChunkConstructionError(
                f"Chunk at index {index} has chunk_index {chunk.chunk_index}, expected {index}."
            )
        if chunk.id in seen_ids:
            raise ChunkConstructionError(f"Duplicate chunk id {chunk.id!r} detected.")
        seen_ids.add(chunk.id)

    for i in range(len(chunks) - 1):
        if chunks[i].character_end > chunks[i + 1].character_start:
            raise ChunkConstructionError(f"Chunks at index {i} and {i + 1} overlap.")


class Chunker:
    """Splits a validated Document into structurally-bounded Chunks.

    docs/architecture.md §5: `Chunker.chunk(doc: Document) -> List[Chunk]`.
    Pure: no filesystem I/O, no network I/O, no shared mutable state.
    """

    def chunk(self, doc) -> list[Chunk]:
        _validate_document(doc)
        document_id = doc.id
        text = doc.text

        spans = _collect_spans(text)
        chunks = [
            build_chunk(document_id, index, start, end, text[start:end])
            for index, (start, end) in enumerate(spans)
        ]

        _check_invariants(chunks)
        return chunks
