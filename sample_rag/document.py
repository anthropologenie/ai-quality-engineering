"""The runtime `Document` representation.

Sprint P3.1.3: implements the Knowledge-stage `Document` value
(docs/architecture.md §5, `KnowledgeSource.load() -> List[Document]`;
docs/glossary.md §8) realizing the approved Document Contract
(docs/DOCUMENT_CONTRACT.md §8.7) per the approved Document Construction Plan
(docs/DOCUMENT_CONSTRUCTION_PLAN.md).

Runtime model only. This module defines *what* a `Document` is; *how* one is
created — corpus resolution, identity resolution, text extraction, text
normalization, ordered emission, and the construction error surface — belongs
to Knowledge Source (Construction Plan §6.1, R1–R6) and is deferred to Sprint
P3.1.4. Accordingly this module performs no parsing, loading, extraction,
normalization, validation, or repository interaction, and imports nothing
beyond `dataclasses`.

`Document` is a passive, corpus-derived data value that owns no behavior
(Document Contract Phase 9). Its two fields are exactly those frozen by
Contract §8.7; every candidate field in §8.6 is deferred, not silently
included as optional.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Document:
    """The two fields frozen by docs/DOCUMENT_CONTRACT.md §8.7 — no more, no less.

    Field order matches that section's schema table exactly, following the
    precedent `Chunk` set against docs/CHUNK_CONTRACT.md §8
    (docs/CHUNK_SERIALIZATION_PLAN.md §P1).

    `id` is reused unmodified from the corresponding `knowledge_manifest.json`
    `documents[].id` and is never independently derived (Contract §8.4,
    invariant 1). `text` is the document's full deterministic plain-text
    content — the reference frame `Chunk.character_start`/`character_end` are
    computed against (Contract §8.2; docs/CHUNK_CONTRACT.md §13) — and may be
    empty, which legally produces zero chunks (Contract §8.3, invariant 2).

    Enforcing either invariant is not this class's responsibility: invariant 1's
    equality half is cross-artifact and deferred to the Data Quality Validation
    layer (Contract §8.5; Construction Plan §13.2), and invariant 3
    (determinism) is a property of repeated construction, not of one value
    (Contract §8.8).
    """

    id: str
    text: str
