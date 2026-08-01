"""Evidence Trace Dataset derivation, serialization, persistence, and validation.

Sprint P3.2.4: materializes the Evidence Trace Dataset — the repository's
Retrieval Expectation Authority — from already-validated repository artifacts,
implementing the Repository Owner decisions ratified at Sprint P3.2.3-R.

The canonical schema is repository authority and is not defined here: the
container comes from `datasets/SCHEMA.md` §8 (`schema_version` + `evidence_trace[]`)
and the eight entry fields from `docs/roadmap.md` §2.4, reused verbatim in
repository snake_case (§P3.2.3-R Decision F). No field is added or removed.

This module follows the one-file-per-artifact-family convention `scripts/build_manifest.py`
(Knowledge Manifest) and `scripts/build_chunks.py` (Chunk Corpus) already
establish: derivation, assembly, serialization, and structural validation live
together, composed by a thin `main()`.

Derivation only. Every value is read from an existing validated artifact or
computed from one by a fixed rule — nothing is inferred, scored, or authored
here. Inputs, and the only inputs permitted:

    knowledge_manifest.json  -> document identity            (Sprint 1A.1)
    KnowledgeSource.load()   -> Document text, the offset frame (Sprint P3.1.4)
    resume_facts.json        -> verified fact source_text     (Sprint 1A.1 P4)
    resume_qa_pairs.json     -> the entry-per-QA-pair driver   (Sprint 1A.1 P4)
    chunks.json              -> the committed Chunk Corpus     (Sprint P3.2.2)

Cross-artifact referential integrity (every `expected_chunk` id exists in the
Chunk Corpus; every `expected_source` exists in the Knowledge Manifest) stays
out of `validate_evidence_trace()`, consistent with the boundary
`docs/CHUNK_VALIDATION_PLAN.md` §P5 already drew for `validate_chunks()`:
structural checks live with the artifact's build script, cross-artifact checks
belong to the Data Quality Validation layer (`docs/MILESTONE_1A.md` build item 2).
"""

import json
from collections.abc import Mapping
from pathlib import Path

from sample_rag.knowledge_source import KnowledgeSource

REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
GOLDEN_ROOT = REPOSITORY_ROOT / "datasets" / "golden"
SAMPLE_RAG_ROOT = REPOSITORY_ROOT / "sample_rag"

SCHEMA_VERSION = "1.0"
FACTS_PATH = GOLDEN_ROOT / "resume_facts.json"
QA_PAIRS_PATH = GOLDEN_ROOT / "resume_qa_pairs.json"
CHUNKS_PATH = SAMPLE_RAG_ROOT / "chunks.json"
EVIDENCE_TRACE_PATH = GOLDEN_ROOT / "resume_evidence_trace.json"

# docs/roadmap.md §2.4, in that table's own row order. Fixed and identical for
# every entry: metric applicability does not vary by question type in Milestone
# 1A (Sprint P3.2.3-R Decision E). `docs/AI_Quality_Metrics_Reference.md` maps a
# sixth metric (Hallucination Rate) to the Generation layer; §2.4 is the Evidence
# Trace field's authority and does not list it, so it is not materialized here.
CANONICAL_METRICS = [
    "Faithfulness",
    "Groundedness",
    "Context Recall",
    "Context Precision",
    "Answer Relevancy",
]

# docs/roadmap.md §2.4 value domains, restricted to what Milestone 1A resolves.
# "Aggregation" (reasoning type) and "Clarify" (outcome) are outside this
# milestone and are never emitted (Decisions B, C).
SINGLE_HOP = "Single-hop"
MULTI_HOP = "Multi-hop"
OUTCOME_ANSWER = "Answer"
OUTCOME_ABSTAIN = "Abstain"

# The one failure_category the QA Dataset uses to mark a question the corpus
# cannot answer; docs/roadmap.md §2.3 defines it as the abstention test.
NO_ANSWER_CATEGORY = "No Answer"

REQUIRED_ENTRY_FIELDS = {
    "id": str,
    "question": str,
    "expected_answer": str,
    "expected_source": str,
    "expected_chunk": list,
    "expected_reasoning_type": str,
    "expected_metrics": list,
    "expected_outcome": str,
}


class EvidenceTraceError(Exception):
    """Raised when the Evidence Trace Dataset cannot be derived from, or read
    back out of, the repository's validated artifacts.

    A fifth independent, flat exception type, following the repository's
    existing per-responsibility pattern (`ManifestValidationError`,
    `ChunkConstructionError`, `ChunkSerializationError`, `ChunkValidationError`)
    — a direct `Exception` subclass with no shared validation base class
    (docs/CHUNK_VALIDATION_PLAN.md §P6.2).
    """


def load_json(path: Path) -> Mapping:
    """Read and parse one validated repository artifact.

    No structural validation and no repair: each input artifact is already
    governed by its own contract and validator.
    """
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise EvidenceTraceError(f"Unable to read {path}: {exc}") from exc

    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise EvidenceTraceError(f"{path} is not valid JSON: {exc}") from exc


def index_chunks_by_document(chunks: list) -> dict:
    """Group the Chunk Corpus by `document_id`, ascending by `chunk_index`.

    The sort is what makes Decision G's ordering a property of this index rather
    than of each call site; the Chunk Corpus is already persisted in this order
    (Sprint P3.2.2), so the sort confirms it rather than repairing it.
    """
    grouped: dict = {}
    for chunk in chunks:
        grouped.setdefault(chunk["document_id"], []).append(chunk)
    for entries in grouped.values():
        entries.sort(key=lambda chunk: chunk["chunk_index"])
    return grouped


def resolve_fact_chunks(fact: Mapping, document_text: str, document_chunks: list) -> list:
    """Resolve the chunks that carry one verified fact's `source_text`.

    Resolution is by character-offset intersection against the parent Document —
    the same reference frame `Chunk.character_start`/`character_end` are computed
    in (docs/CHUNK_CONTRACT.md §13) — not by text matching against chunk bodies.
    That is what makes a fact split across a chunk boundary resolve to every
    chunk it spans rather than to none, without inspecting chunk text at all.

    Returns chunks in ascending `chunk_index` order, inherited from the index.
    """
    source_text = fact["source_text"]
    start = document_text.find(source_text)
    if start < 0:
        raise EvidenceTraceError(
            f"Fact {fact['id']!r} source_text is not present in document "
            f"{fact['document_id']!r}; the Golden Dataset and the Document corpus "
            f"have diverged."
        )

    end = start + len(source_text)
    return [
        chunk
        for chunk in document_chunks
        if chunk["character_end"] > start and chunk["character_start"] < end
    ]


def derive_expected_reasoning_type(qa_pair: Mapping) -> str:
    """Reasoning type, derived from evidence topology (Decision B).

    `supporting_fact_ids` count <= 1 is Single-hop, >= 2 is Multi-hop — zero
    supporting facts included, explicitly. The QA Dataset's own
    `failure_category` is deliberately *not* consulted: it labels what a question
    tests, while this field records how many pieces of evidence answering it
    requires. Aggregation is not inferred.
    """
    return MULTI_HOP if len(qa_pair["supporting_fact_ids"]) >= 2 else SINGLE_HOP


def derive_expected_outcome(qa_pair: Mapping) -> str:
    """Expected outcome, derived from the QA Dataset's failure taxonomy (Decision C).

    "No Answer" is the abstention test (docs/roadmap.md §2.3) and is the only
    category yielding Abstain. Every other category — including False Premise,
    whose expected answer corrects the premise from the corpus rather than
    declining — yields Answer. Clarify is outside Milestone 1A and is never
    emitted.
    """
    if qa_pair["failure_category"] == NO_ANSWER_CATEGORY:
        return OUTCOME_ABSTAIN
    return OUTCOME_ANSWER


def build_evidence_trace_entry(
    qa_pair: Mapping, facts: Mapping, documents: Mapping, chunks_by_document: Mapping
) -> dict:
    """Derive one Evidence Trace entry from one QA pair.

    Evidence is the parent fact plus its supporting facts, in the QA pair's own
    order; the chunks they resolve to are de-duplicated and re-sorted ascending
    by `chunk_index` (Decision G), so an entry's chunk order is a property of the
    corpus, not of the order its facts happen to be listed in.

    `expected_source` is the parent document's `id` — the repository's canonical
    document identity (docs/DOCUMENT_CONTRACT.md §8.4) and the join key
    `chunk.document_id` and `knowledge_manifest.json` `documents[].id` already
    share. A single entry drawing evidence from more than one document has no
    ratified encoding for this field, so it is refused rather than guessed.
    """
    fact_ids = [qa_pair["fact_id"], *qa_pair["supporting_fact_ids"]]

    missing = [fact_id for fact_id in fact_ids if fact_id not in facts]
    if missing:
        raise EvidenceTraceError(
            f"QA pair {qa_pair['id']!r} references unknown fact ids {missing}."
        )

    document_ids = {facts[fact_id]["document_id"] for fact_id in fact_ids}
    if len(document_ids) != 1:
        raise EvidenceTraceError(
            f"QA pair {qa_pair['id']!r} draws evidence from {len(document_ids)} "
            f"documents ({sorted(document_ids)}); 'expected_source' has no "
            f"ratified multi-document encoding."
        )

    document_id = document_ids.pop()
    if document_id not in documents:
        raise EvidenceTraceError(
            f"QA pair {qa_pair['id']!r} references document {document_id!r}, "
            f"which the Knowledge Manifest does not catalogue."
        )

    document_chunks = chunks_by_document.get(document_id, [])
    resolved: dict = {}
    for fact_id in fact_ids:
        for chunk in resolve_fact_chunks(
            facts[fact_id], documents[document_id].text, document_chunks
        ):
            resolved[chunk["id"]] = chunk

    expected_chunk = [
        chunk["id"] for chunk in sorted(resolved.values(), key=lambda c: c["chunk_index"])
    ]
    if not expected_chunk:
        raise EvidenceTraceError(
            f"QA pair {qa_pair['id']!r} resolved to zero chunks; every QA pair "
            f"must trace to accepted repository knowledge."
        )

    return {
        "id": f"meta_{qa_pair['id']}",
        "question": qa_pair["question"],
        "expected_answer": qa_pair["expected_answer"],
        "expected_source": document_id,
        "expected_chunk": expected_chunk,
        # Deferred to Milestone 2 (Decision A): the field exists on every entry
        # and is null. No route is inferred — BM25, Vector, and Hybrid are all
        # Milestone 2 capabilities, and SQL is the JobOps structured route, which
        # this resume-only corpus does not exercise.
        "expected_retrieval_route": None,
        "expected_reasoning_type": derive_expected_reasoning_type(qa_pair),
        "expected_metrics": list(CANONICAL_METRICS),
        "expected_outcome": derive_expected_outcome(qa_pair),
    }


def assemble_evidence_trace(entries: list) -> dict:
    """Wrap derived entries in the container frozen by `datasets/SCHEMA.md` §8.

    Pure transformation: preserves input ordering exactly — which is the QA
    Dataset's own order — and performs no filesystem I/O, sorting, or validation.
    """
    return {
        "schema_version": SCHEMA_VERSION,
        "evidence_trace": list(entries),
    }


def write_evidence_trace(collection: dict) -> None:
    """Deterministically serialize the dataset to its canonical artifact.

    Reuses the repository's established serialization convention exactly (see
    `write_manifest`, `write_chunks`): UTF-8, 2-space indentation,
    insertion-order keys, trailing newline. No validation or recomputation.
    """
    serialized = json.dumps(collection, indent=2) + "\n"
    try:
        EVIDENCE_TRACE_PATH.write_text(serialized, encoding="utf-8")
    except OSError as exc:
        raise EvidenceTraceError(
            f"Unable to write Evidence Trace Dataset to {EVIDENCE_TRACE_PATH}: {exc}"
        ) from exc


def load_evidence_trace() -> Mapping:
    """Read and parse the canonical persisted Evidence Trace Dataset."""
    return load_json(EVIDENCE_TRACE_PATH)


def _validate_representation(collection: Mapping) -> list:
    """Container structural gate — must succeed before any entry is inspected."""
    for field in ("schema_version", "evidence_trace"):
        if field not in collection:
            raise EvidenceTraceError(
                f"Evidence Trace Dataset is missing required field {field!r}."
            )

    schema_version = collection["schema_version"]
    if not isinstance(schema_version, str):
        raise EvidenceTraceError("Field 'schema_version' must be a string.")
    if schema_version != SCHEMA_VERSION:
        raise EvidenceTraceError(
            f"Field 'schema_version' must equal {SCHEMA_VERSION!r}, got {schema_version!r}."
        )

    entries = collection["evidence_trace"]
    if not isinstance(entries, list):
        raise EvidenceTraceError("Field 'evidence_trace' must be a list.")

    return entries


def _validate_entry(entry: Mapping, index: int) -> None:
    """Field and value-domain invariants for one Evidence Trace entry.

    Checks the canonical schema exactly: the eight `docs/roadmap.md` §2.4 fields
    plus the `datasets/SCHEMA.md` §6 identifier, no more and no fewer, with each
    ratified value domain enforced.
    """
    if not isinstance(entry, Mapping):
        raise EvidenceTraceError(f"Entry at index {index} must be an object.")

    expected_fields = set(REQUIRED_ENTRY_FIELDS) | {"expected_retrieval_route"}
    unexpected = sorted(set(entry) - expected_fields)
    if unexpected:
        raise EvidenceTraceError(
            f"Entry at index {index} carries non-canonical fields {unexpected}."
        )

    for field, expected_type in REQUIRED_ENTRY_FIELDS.items():
        if field not in entry:
            raise EvidenceTraceError(
                f"Entry at index {index} is missing required field {field!r}."
            )
        if not isinstance(entry[field], expected_type):
            raise EvidenceTraceError(
                f"Entry at index {index} field {field!r} must be of type "
                f"{expected_type.__name__}."
            )

    if "expected_retrieval_route" not in entry:
        raise EvidenceTraceError(
            f"Entry at index {index} is missing required field 'expected_retrieval_route'."
        )
    if entry["expected_retrieval_route"] is not None:
        raise EvidenceTraceError(
            f"Entry at index {index} field 'expected_retrieval_route' must be null "
            f"until Milestone 2."
        )

    if not entry["id"].startswith("meta_"):
        raise EvidenceTraceError(
            f"Entry at index {index} id {entry['id']!r} does not follow the "
            f"'meta_<qa_id>' convention."
        )

    if not entry["expected_chunk"]:
        raise EvidenceTraceError(f"Entry at index {index} has no expected chunk.")
    if not all(isinstance(chunk_id, str) for chunk_id in entry["expected_chunk"]):
        raise EvidenceTraceError(
            f"Entry at index {index} field 'expected_chunk' must contain chunk id strings."
        )
    if len(set(entry["expected_chunk"])) != len(entry["expected_chunk"]):
        raise EvidenceTraceError(
            f"Entry at index {index} repeats a chunk id in 'expected_chunk'."
        )

    if entry["expected_reasoning_type"] not in (SINGLE_HOP, MULTI_HOP):
        raise EvidenceTraceError(
            f"Entry at index {index} reasoning type "
            f"{entry['expected_reasoning_type']!r} is outside the Milestone 1A domain."
        )

    if entry["expected_outcome"] not in (OUTCOME_ANSWER, OUTCOME_ABSTAIN):
        raise EvidenceTraceError(
            f"Entry at index {index} outcome {entry['expected_outcome']!r} is "
            f"outside the Milestone 1A domain."
        )

    if entry["expected_metrics"] != CANONICAL_METRICS:
        raise EvidenceTraceError(
            f"Entry at index {index} field 'expected_metrics' must be the canonical "
            f"docs/roadmap.md §2.4 list."
        )


def _validate_collection_invariants(entries: list) -> None:
    """Cross-entry invariants: dataset-wide identifier uniqueness."""
    seen: set = set()
    for entry in entries:
        if entry["id"] in seen:
            raise EvidenceTraceError(f"Duplicate Evidence Trace id {entry['id']!r}.")
        seen.add(entry["id"])


def validate_evidence_trace(collection: Mapping) -> Mapping:
    """Verify `collection` against the canonical Evidence Trace schema.

    Read-only, fail-fast, `Mapping -> Mapping` — the same public shape and
    behavior `validate_manifest()` and `validate_chunks()` already establish, so
    this validates a persisted dataset, a test fixture, or a synthetic malformed
    collection alike. Structural scope only: cross-artifact referential integrity
    against the QA Dataset and Chunk Corpus belongs to the Data Quality
    Validation layer (docs/CHUNK_VALIDATION_PLAN.md §P5).
    """
    entries = _validate_representation(collection)

    for index, entry in enumerate(entries):
        _validate_entry(entry, index)

    _validate_collection_invariants(entries)

    return collection


def main() -> None:
    """Derive, persist, and structurally validate the Evidence Trace Dataset.

    Thin orchestrator, mirroring `scripts/build_manifest.py` and
    `scripts/build_chunks.py` `main()`. Entry order is the QA Dataset's own
    order, preserved and never re-sorted, so the QA Dataset remains the single
    authority over which questions exist and in what sequence.
    """
    facts = {fact["id"]: fact for fact in load_json(FACTS_PATH)["facts"]}
    qa_pairs = load_json(QA_PAIRS_PATH)["qa_pairs"]
    chunks_by_document = index_chunks_by_document(load_json(CHUNKS_PATH)["chunks"])
    documents = {document.id: document for document in KnowledgeSource().load()}

    entries = [
        build_evidence_trace_entry(qa_pair, facts, documents, chunks_by_document)
        for qa_pair in qa_pairs
    ]

    write_evidence_trace(assemble_evidence_trace(entries))
    validate_evidence_trace(load_evidence_trace())


if __name__ == "__main__":
    main()
