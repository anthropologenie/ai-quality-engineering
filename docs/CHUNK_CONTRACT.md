# Chunk Contract

**Repository:** `ai-quality-engineering`
**Status:** Frozen
**Contract Version:** 1.0
**Related documents:** `docs/MILESTONE_1A.md` (Knowledge Manifest contract; Indexing build item), `docs/architecture.md` (Chunker component, Index stage), `docs/glossary.md` (canonical terminology), `datasets/SCHEMA.md` (sibling artifact-representation-contract precedent)

This document defines the canonical Chunk Data Model and freezes the Chunk Contract for `ai-quality-engineering`. It is a design and contract specification only. It contains no implementation code and authorizes no implementation work by itself — see Section 19.

---

## 1. Executive Summary

This document establishes **Chunk** as the repository's second canonical persistent artifact, following the same engineering lifecycle already used for the Knowledge Manifest: Data Model → Contract Freeze → Construction → Serialization → Validation.

A Chunk is the smallest retrievable unit of text produced by splitting a validated Document at the Index stage (`docs/glossary.md` §3). This document defines its six required fields (`id`, `document_id`, `text`, `chunk_index`, `character_start`, `character_end`), freezes their types and invariants, and evaluates ten candidate metadata fields — all of which are explicitly deferred, not silently omitted.

Two decisions carry the most long-term weight: chunk identity is deterministic and derived from position (`document_id` + `chunk_index`), not content, so that duplicate text never collides; and character offsets use Python's half-open slicing convention (`[start, end)`), so `document_text[character_start:character_end] == text` holds as a hard invariant and chunk-coverage validation (already named in `docs/altm.md`) has something precise to check.

No new architecture is introduced. This document extends the existing pipeline (Knowledge → Index → Retrieve → Assemble → Infer → Evaluate) and the existing `Chunker.chunk(doc: Document) -> List[Chunk]` interface already declared in `docs/architecture.md` §7.

---

## 2. Repository Discovery Findings

Per Phase 0, the following was inspected before any design decision was made:

- **No `docs/design/`, ADR directory, or existing Chunk schema document exists.** The repository has never before frozen a field-level schema for `Chunk`, only a glossary definition and an interface signature.
- **Precedent A — embedded contract.** The Knowledge Manifest contract (Sprint P1.2.0) was frozen as a subsection embedded directly inside `docs/MILESTONE_1A.md`, under the build item it belongs to (`docs/MILESTONE_1A.md`, build item 1). It includes a schema table, a "Contract status" freeze statement, and explicit "Contract Change" notes for anything removed from an earlier draft.
- **Precedent B — sibling contract document.** `datasets/golden/`'s representation contract is *not* embedded in `roadmap.md`. It lives in a dedicated sibling file, `datasets/SCHEMA.md`, and `roadmap.md` references it rather than duplicating it. `datasets/SCHEMA.md` explicitly separates "how data is stored" (its own job) from "what the data means" (`datasets/README.md`'s job) and from architecture/roadmap decisions (referenced, not restated).
- **`docs/glossary.md` is the single canonical terminology source.** Every other document is required to reference terms defined there rather than redefine them (`docs/glossary.md` §2, "Cross-reference Philosophy"). `Chunk`, `Chunking`, `Index`, `Document`, and the Chunk-vs-Document distinction are already defined there (§3, §8).
- **`docs/architecture.md` already declares the Chunker interface**: `Chunker.chunk(doc: Document) -> List[Chunk]` (§7), and positions Chunk as the output of the Index stage (§4–5).
- **`docs/MILESTONE_1A.md` build item 2** already anticipates chunk-level validation by name ("resume validation, chunk validation, metadata validation, Index Coverage Validation") but has not yet defined what a Chunk *is* — confirming this sprint is a genuine, not-yet-filled gap rather than a duplication of existing work.
- **`docs/altm.md` line 189** already defines the detection mechanism chunk data will be validated against later: "Chunk coverage check — every span of source text should exist in exactly one chunk with a corresponding vector." This is a strong, pre-existing constraint on how offsets must behave (Section 13).
- **`RetrievalResult` (`docs/MILESTONE_1A.md`, build item 4) already separates query-time state from corpus-time state.** `chunks`, `retrieval_route`, `score`, and `diagnostics` are fields of `RetrievalResult`, not of `Chunk`. This is a repository fact, not a new recommendation, and it directly resolves several of the deferred-metadata questions in Section 15.
- **`VectorStore.upsert(chunk_id: str, vector: list[float])` (`docs/architecture.md` §7) already keys vectors externally by `chunk_id` across the whole corpus**, not per-document. This is a repository fact that constrains chunk identity to be globally unique (Section 10).
- **A genuine open gap was found, not invented**: the runtime `Document` object returned by `KnowledgeSource.load() -> List[Document]` (`docs/architecture.md` §5) has no frozen field-level schema of its own yet, distinct from a Knowledge Manifest `documents[]` entry (which only carries `id`, `source`, `hash`, `indexed` — no text content). This document does not attempt to freeze `Document`'s schema (out of scope), but Section 11 records the dependency this creates for `Chunk.document_id` and, indirectly, for `character_start`/`character_end`.

**Conclusion:** an existing convention was found (Precedent B) and is adopted rather than forked. See Section 18.

---

## 3. Repository Terminology

Per `docs/glossary.md`'s cross-reference philosophy, terms already defined there are used as-is and not redefined here.

**Already defined (repository fact, used as-is):**

| Term | Source |
|---|---|
| Chunk | `docs/glossary.md` §3 — "A single retrievable unit of text produced by splitting a document — the smallest span retrieval operates on." |
| Chunking | `docs/glossary.md` §3 — "The process of splitting a validated document into chunks, performed at the Index stage." |
| Chunk vs. Document | `docs/glossary.md` §8 — Chunk is "a slice of a document," produced at Index; Document is "a full source item... before chunking," consumed at Knowledge. |
| Index (stage and noun) | `docs/glossary.md` §3 |
| Corpus, Knowledge Manifest, Deterministic Pipeline, Stub | `docs/glossary.md` §3, §7 |

**New terminology introduced by this document (explicitly flagged, not silently adopted as fact):**

| Term | Status | Notes |
|---|---|---|
| Chunk Data Model / Chunk Contract | **Recommendation.** | Names the pattern the Knowledge Manifest already used implicitly. Not yet a glossary entry. Should be added to `docs/glossary.md` §3 alongside the existing "Knowledge Manifest" entry if this document is frozen (Section 18). |
| Persistent Canonical Artifact / Runtime Artifact | **Recommendation**, sourced from this sprint's own task framing, not from prior repository documentation. | Useful because it gives a name to a distinction the repository already practices (`RetrievalResult` is query-time/ephemeral; Knowledge Manifest and, by this document, Chunk are corpus-time/persistent) but has not yet named. See Section 5. Recommended for a future glossary addition, not made here. |
| Chunk identity, chunk ordering, offset semantics (as formal terms) | **Recommendation**, scoped to this document only. | Used descriptively; not proposed as new glossary entries — they are attributes of the Chunk Contract, not repository-wide vocabulary. |

No new directory names, document locations, or architectural stage names are introduced (Section 18 explains the one new *file*, which follows an existing pattern rather than inventing one).

---

## 4. Architectural Context

Chunk is the output artifact of the **Index** stage, in the six-stage pipeline already locked in `docs/architecture.md` §4:

```
Knowledge → Index → Retrieve → Assemble → Infer → Evaluate
```

- **Produced by:** the `Chunker` component (`docs/architecture.md` §5), from a validated `Document` (Knowledge stage output).
- **Consumed by:** the `Indexer` component, which builds a lookup structure over chunks, and — indirectly, via `Indexer`/`VectorStore` — the `Retriever`.
- **Not consumed directly by:** `ContextBuilder`, `Generator`, or `EvaluationEngine`. Those operate on `RetrievalResult` (a Retrieve-stage, query-time artifact), not on `Chunk` directly. This boundary is load-bearing for Section 15.

No pipeline stage, component, or interface name is changed or added by this document.

---

## 5. Repository Engineering Principles

This document reuses the lifecycle already applied to the Knowledge Manifest (`docs/MILESTONE_1A.md`, `git log`: P1.2.0 → P1.2.1 → P1.2.2 → P1.3):

```
Canonical Data Model → Contract Freeze → Construction → Serialization → Validation
```

Chunk is classified as a **Persistent Canonical Artifact** (Recommendation, Section 3) under this repository's existing two-track distinction:

| | Persistent Canonical Artifact | Runtime Artifact |
|---|---|---|
| Lifecycle | Data Model → Contract Freeze → Construction → Serialization → Validation | Data Model → Contract Freeze → Construction → Validation |
| Lifetime | Corpus-derived; exists once per corpus generation; version-controlled | Query-derived; exists only for the duration of one request |
| Repository example | Knowledge Manifest (frozen), **Chunk (this document)** | `RetrievalResult` (`docs/MILESTONE_1A.md`, build item 4) |
| Determinism requirement | Identical corpus + identical algorithm ⇒ identical artifact | Identical query + identical corpus/index state ⇒ identical result |

This classification is justified by a repository fact, not asserted from nothing: `RetrievalResult` already exists as a query-time, non-serialized dataclass, structurally distinct from the Knowledge Manifest's corpus-time, serialized-to-disk artifact. Naming the distinction only makes an existing practice explicit.

The following binding principles from `docs/architecture.md` §2 apply directly to this design:

- **Docs before code** — this document exists precisely because Chunk construction (P2.2) must not begin first.
- **Interface-first design** — `Chunker.chunk(doc) -> List[Chunk]` is unchanged; this document defines what `Chunk` *is* without touching the interface signature.
- **Deterministic before probabilistic** — Chunk fields carry no probabilistic content (no scores, no embeddings; see Section 15).
- **Data validation before retrieval** — mirrors the Knowledge Manifest precedent: freeze, then build, then serialize, then validate.

---

## 6. Chunk Data Model

**Entity: `Chunk`**

One `Chunk` represents one contiguous, non-overlapping span of a single parent `Document`'s text.

| Field | Type | Relationship |
|---|---|---|
| `id` | `str` | Identity of this chunk. Globally unique across the entire corpus (Section 10). |
| `document_id` | `str` | Foreign key to the parent document's identity (Section 11). |
| `text` | `str` | The literal chunk content — the substring of the parent document's text at `[character_start, character_end)`. |
| `chunk_index` | `int` | This chunk's zero-based position among all chunks of the same `document_id` (Section 12). |
| `character_start` | `int` | Start offset into the parent document's text (Section 13). |
| `character_end` | `int` | End offset into the parent document's text, exclusive (Section 13). |

Relationships:

- **Chunk → Document**: many-to-one, via `document_id`. Every chunk belongs to exactly one document; a document produces zero or more chunks.
- **Chunk → Chunk (ordering)**: one-to-one successor relationship within a document, via `chunk_index`, forming a total order over a document's chunks (Section 12).
- **Chunk → VectorStore** (future, Milestone 2): referenced externally by `id`, never embeds a vector itself (Section 15).

---

## 7. Chunk Contract

Mirroring the Knowledge Manifest's contract framing (`docs/MILESTONE_1A.md`, build item 1):

> **Contract status (frozen at Sprint P2.1):** the schema in Section 8 defines what a Chunk *is*. How chunks are constructed, serialized, or validated is an implementation concern for P2.2, P2.3, and P2.4 respectively — not defined here.

**Required fields:** `id`, `document_id`, `text`, `chunk_index`, `character_start`, `character_end` — all six, no exceptions (Section 9).

**Optional fields:** none in this frozen contract (Section 9).

**Identity guarantee:** `id` is unique across every chunk in the corpus and deterministic — an identical document, chunked by an identical algorithm, produces identical chunk `id`s (Section 10).

**Ordering guarantee:** for a fixed `document_id`, `chunk_index` values are exactly `0, 1, ..., N-1` with no gaps or duplicates, and ascending `chunk_index` corresponds to ascending `character_start` — i.e., chunk order matches reading order (Section 12).

**Offset guarantee:** `character_start` and `character_end` are zero-based, Unicode-code-point offsets into the parent document's text, using a half-open interval `[character_start, character_end)`, such that `character_end - character_start == len(text)` always holds (Section 13).

**Non-overlap invariant:** for a fixed `document_id`, chunks do not overlap — for any two chunks with `chunk_index = i` and `chunk_index = i+1`, `character_end` of chunk `i` is `<=` `character_start` of chunk `i+1`. Gaps (e.g. stripped separators or whitespace) are permitted; overlap is not.

**Non-empty invariant:** `character_end > character_start` for every chunk — a zero-length chunk is invalid.

**Deterministic artifact contract:** as with the Knowledge Manifest, an identical `Document` processed by an identical chunking algorithm must produce an identical ordered list of `Chunk`s, field-for-field. This is a contractual requirement, not an implementation detail — every conforming implementation of the Chunk Data Model must preserve it.

---

## 8. Field Definitions

| Field | Type | Purpose |
|---|---|---|
| `id` | `str` | Unique identifier for the chunk within the corpus. Deterministic given identical inputs (Section 10). |
| `document_id` | `str` | Identifier of the parent document. Must equal the `id` of the corresponding entry in `knowledge_manifest.json`'s `documents[]` (Section 11). |
| `text` | `str` | The chunk's literal text content. Equal to `document_text[character_start:character_end]` under Python slicing semantics. |
| `chunk_index` | `int` | Zero-based position of this chunk among all chunks belonging to `document_id`, in reading order (Section 12). |
| `character_start` | `int` | Zero-based, inclusive start offset into the parent document's text (Section 13). |
| `character_end` | `int` | Zero-based, exclusive end offset into the parent document's text (Section 13). |

These are the only fields in the contract. See Section 15 for every candidate field considered and explicitly deferred.

---

## 9. Required vs Optional Fields

All six fields in Section 8 are **required**. There are no optional fields in this frozen contract.

This mirrors the Knowledge Manifest precedent, where all four `documents[]` fields (`id`, `source`, `hash`, `indexed`) are required with no optional fields. Minimalism is deliberate: every candidate field beyond the minimum six (Section 15) is either fully deferred (absent from the contract entirely) or not deferred (included as required) — there is no "optional" middle tier in this version of the contract, which avoids the ambiguity of an unused-but-legal field.

**Note on unknown fields:** this contract does not itself state whether an implementation may attach additional, undocumented fields to a `Chunk` instance (e.g., during Construction, before Validation exists). The precedent (`validate_manifest()` in `scripts/build_manifest.py`) only checks that required fields are present and correctly typed — it does not reject unrecognized extra fields. Whether Chunk validation (P2.4) follows this same permissive stance is that sprint's decision, not this one's; it is flagged here so P2.4 does not have to rediscover the question.

---

## 10. Identity Rules

- `id` is a `str`.
- `id` is **unique across the entire corpus** — not merely unique within one document. This is required because `VectorStore.upsert(chunk_id: str, vector: list[float])` (`docs/architecture.md` §7) already keys a single, corpus-wide store by `chunk_id`; a per-document-only identity scheme would silently violate that existing interface's assumptions the moment two documents produced colliding local IDs.
- `id` is **deterministic**: given an identical `Document` and an identical chunking algorithm, `id` is reproduced exactly. This is a Contract requirement (Section 7), not merely a nice-to-have.
- `id` is **derived from position, not content** (`document_id` + `chunk_index`), not from a hash of `text`. Two chunks with identical text (e.g. a repeated boilerplate heading such as "Responsibilities" appearing in two different job descriptions, or even twice in one document) must not collide. See Section 14 for the full alternatives analysis.
- `id` stability is scoped the same way the Knowledge Manifest's determinism is scoped: identical corpus + identical algorithm ⇒ identical IDs. A change to the chunking algorithm (e.g. different boundary rules) is permitted to reassign different `id`s to conceptually-similar chunks — the contract does not promise `id` stability *across* algorithm changes, only *within* a fixed algorithm applied to a fixed corpus.
- This document does not prescribe the derivation mechanism. Section 14 evaluates identity-strategy alternatives at the architectural level only; the concrete derivation is left to Construction (P2.2), exactly as the Knowledge Manifest contract left `documents[].id`'s derivation unspecified until P1.1's implementation.

---

## 11. Parent Relationships

- `document_id` is a **foreign key** from `Chunk` to a document.
- **Cardinality:** one document produces zero or more chunks (1:N). Every chunk belongs to exactly one document.
- `document_id` **must equal** the corresponding entry's `id` field in `knowledge_manifest.json`'s `documents[]` array (`docs/MILESTONE_1A.md`, build item 1) — not the `source` path, not the file hash. This keeps chunk-to-document joins stable even if a document's source path is later renamed, matching the Knowledge Manifest's own existing separation of stable `id` from mutable-in-principle `source`.
- **Referential integrity** (verifying that every `document_id` in a chunk collection actually exists in the Knowledge Manifest) is **not** part of this structural contract. It is a semantic/cross-artifact validation concern, analogous to how `validate_manifest()` today performs only structural checks and no semantic ones. This is deferred to P2.4 (Chunk Validation) or later, consistent with `docs/MILESTONE_1A.md`'s own note that "Semantic validation is a later milestone."
- **Open dependency (discovered, not invented):** the runtime `Document` object (`KnowledgeSource.load() -> List[Document]`) has no frozen field-level schema yet, and is distinct from a Knowledge Manifest entry (which carries no text content). This document assumes — but does not itself freeze — that whatever `Document.id` the Chunker receives at construction time is identical to the corresponding Knowledge Manifest `documents[].id`. Whoever designs `Document`'s own data model (a gap this discovery surfaced, out of scope here) must preserve that equality, or `Chunk.document_id`'s contract in this document breaks silently. This is recorded as a forward dependency, not resolved here.

---

## 12. Ordering Semantics

- `chunk_index` is a zero-based `int`.
- For a fixed `document_id`, the set of `chunk_index` values across all its chunks is exactly `{0, 1, ..., N-1}` for `N` chunks — contiguous, no gaps, no duplicates.
- `chunk_index` order matches ascending `character_start` order — i.e., `chunk_index` reflects reading order, not construction order or any other incidental ordering.
- **Rationale for zero-based:** consistency with Python's own indexing and slicing conventions, which the repository already leans on throughout (`docs/architecture.md`'s stdlib-only principle, `scripts/build_manifest.py`'s use of `path.relative_to`, list-based document ordering). A one-based scheme would require translation at every consumer.
- This guarantee is what makes chunk-coverage validation (`docs/altm.md` line 189, deferred to P2.4) checkable at all: coverage is verified by walking chunks of a document in `chunk_index` order and confirming their offsets tile the document's text without overlap (Section 7's non-overlap invariant, defined above).

---

## 13. Character Offset Semantics

- `character_start` and `character_end` are zero-based, `int`, and refer to **Unicode code point positions** (i.e., Python `str` indexing/slicing semantics) — not byte offsets, not grapheme clusters, not any encoding-specific unit. This follows directly from the "stdlib-only, pure Python" principle already governing this repository (`docs/MILESTONE_1A.md`, Libraries table).
- The interval is **half-open**: `[character_start, character_end)`. `character_end` is exclusive.
- **Reference frame:** offsets are relative to a single, deterministic plain-text extraction of the parent document — whatever text representation the `Chunker` receives as its `Document` input. The exact extraction/normalization method (e.g., how a `.docx` file's paragraphs are joined into one string) is a Knowledge-stage/Document concern and is explicitly **not** defined by this document (Section 16). This document's only requirement of that upstream representation is that it be stable and deterministic for a given document — consistent with the repository's existing deterministic-artifact principle.
- **Hard invariant:** `text == document_text[character_start:character_end]`, and therefore `len(text) == character_end - character_start`, for every chunk. This is the single strongest correctness check available on a Chunk instance, and it is free to verify (no external state needed beyond the chunk itself and the source document text) — a deliberate design goal, not an accident.
- See Section 14 for the inclusive-vs-exclusive alternatives analysis.

---

## 14. Architectural Decision Analysis

### 14.1 Chunk Identity Strategy

- **Alternatives:** (a) random UUID per chunk; (b) sequential integer counter; (c) content hash of `text`; (d) position-derived hash of `(document_id, chunk_index)`.
- **Trade-offs:** (a) is non-deterministic — violates the deterministic-artifact contract outright. (b) is deterministic only if construction order is itself deterministic and global, which couples chunk numbering across unrelated documents for no benefit. (c) breaks under duplicate content — a repeated section heading or boilerplate phrase would collide across documents, corrupting `VectorStore.upsert`'s per-chunk keying. (d) is deterministic, globally unique (given `document_id` is already unique and `chunk_index` is unique within it), and stays stable across re-runs of the same chunking algorithm.
- **Recommendation:** (d), position-derived identity from `(document_id, chunk_index)`.
- **Justification:** matches the Knowledge Manifest's own precedent of deriving `id` from a stable positional/path property (`source`) rather than from content (`hash` is a separate field, reserved for integrity checking, not identity). The concrete derivation mechanism is left to Construction (P2.2), per Section 10.

### 14.2 Parent Document Relationship

- **Alternatives:** (a) embed a full copy of document metadata inside each chunk; (b) reference the parent by `source` path; (c) reference the parent by Knowledge Manifest `id`.
- **Trade-offs:** (a) duplicates data already owned by the Knowledge Manifest and risks silent drift if the document is re-processed. (b) couples chunk records to a path string that the Knowledge Manifest itself treats as non-identity (`docs/MILESTONE_1A.md` already separates `id` from `source`). (c) is a single stable foreign key, consistent with how the Knowledge Manifest already models its own identity.
- **Recommendation:** (c), `document_id` = Knowledge Manifest `documents[].id`.
- **Justification:** reuses an identity scheme the repository has already frozen and validated (P1.2.0–P1.3), rather than inventing a second one for the same underlying document.

### 14.3 Chunk Ordering

- **Alternatives:** (a) one-based indexing; (b) zero-based indexing; (c) no explicit index, ordering implied by list position only.
- **Trade-offs:** (a) requires translation at every Python consumer (`chunks[chunk_index]` would be off by one). (c) makes ordering an accident of whatever container holds the chunks, rather than a property of the chunk itself — a chunk passed individually (e.g. to a test or a log line) would lose its position entirely.
- **Recommendation:** (b), zero-based, carried as an explicit field.
- **Justification:** matches Python/stdlib convention already used throughout the repository; keeps ordering a property of the `Chunk` value itself, not of its container.

### 14.4 Character Offset Semantics — Inclusive vs. Exclusive

- **Alternatives:** (a) inclusive-inclusive (`[start, end]`); (b) inclusive-exclusive / half-open (`[start, end)`).
- **Trade-offs:** (a) requires `len(text) == end - start + 1`, is a well-known source of off-by-one defects, and breaks the clean adjacency property `chunk[i].end == chunk[i+1].start` (it becomes `chunk[i].end + 1 == chunk[i+1].start`). (b) matches Python's own `str` slicing exactly, so `text == document_text[start:end]` is a direct, zero-translation invariant, and adjacent/tiling chunks compare with plain `<=`.
- **Recommendation:** (b), half-open, exclusive end.
- **Justification:** directly serves the chunk-coverage validation already named (not yet implemented) in `docs/altm.md` line 189 — half-open intervals make "does this span exist in exactly one chunk" a simple interval-tiling check, not an off-by-one-prone one. Also consistent with the stdlib-only, Python-idiomatic principle governing the rest of the repository.

### 14.5 Field Typing

- **Alternatives:** (a) loosely-typed structure with no frozen per-field types; (b) explicit per-field types as frozen in this document, with the concrete representation left open to P2.2.
- **Trade-offs:** (a) alone provides no contract to validate against. (b) gives Construction and Validation a concrete, checkable shape without prematurely dictating how P2.2 represents `Chunk` internally — mirroring how the Knowledge Manifest contract fixed field *types* (`documents[].indexed: boolean`) without dictating a representation.
- **Recommendation:** (b).
- **Justification:** keeps this document a Contract, not an implementation, per the sprint's own Data-Model-vs-Contract framing (Section 7).

### 14.6 Required vs. Optional Fields

- **Alternatives:** (a) mark speculative fields (e.g. `heading`) optional now, to avoid a future contract version bump; (b) keep the v1 contract to exactly the minimum six fields, with everything else fully deferred (absent, not optional).
- **Trade-offs:** (a) risks the same problem the Knowledge Manifest explicitly avoided with `created_at` — an unpopulated or inconsistently-populated optional field that erodes the "deterministic, meaningful" guarantee the repository holds retrieval/manifest fields to (`docs/MILESTONE_1A.md`, `RetrievalResult`'s placeholder-value philosophy). (b) keeps the contract small and everything in it meaningful.
- **Recommendation:** (b).
- **Justification:** matches the Knowledge Manifest precedent (all four fields required, zero optional) and the repository's general minimalism principle (`docs/roadmap.md` §6, "Minimal dependencies... added only when a milestone specifically requires them").

---

## 15. Deferred Metadata

Every candidate field named in the sprint scope is evaluated individually. None are included in the v1 contract.

| Field | Decision | Rationale |
|---|---|---|
| `token_count` | **Deferred.** | Tokenization requires choosing a tokenizer, which is a Milestone 2 concern (`docs/MILESTONE_1A.md`: "No embedding library... imported anywhere in the M1A codebase"). A character count masquerading as a token count would be actively misleading rather than merely incomplete. Chunking in M1A is structure-aware (section/field boundaries), not token-budget-driven, so nothing in the current pipeline needs this field yet. |
| `heading` | **Deferred**, but flagged as the strongest near-term candidate. | M1A's primary chunking strategy is explicitly "section/field-based boundaries — resume headers, JD fields like Responsibilities/Requirements" (`docs/MILESTONE_1A.md`, build item 3), so this field is directly relevant to the locked chunking strategy — unlike the Milestone-2-only fields below. It is deferred here only because Construction (P2.2) has not yet decided the concrete shape a "heading" takes for each document type, and freezing a field ahead of that decision risks a contract that doesn't fit the real implementation. Recommend revisiting at P2.2. |
| `section` | **Deferred**, same rationale as `heading`. | See above. |
| `page_number` | **Deferred — out of scope, not just early.** | No document type in the current corpus (`.docx` resume, job descriptions) has a defined pagination concept anywhere in the pipeline. Unlike `heading`/`section`, this is not a near-term candidate. |
| `embedding` | **Deferred — Milestone 2.** | Repository fact, not judgment call: `VectorStore.upsert(chunk_id: str, vector: list[float])` (`docs/architecture.md` §7) already stores vectors *externally*, keyed by `chunk_id`, not embedded on the chunk object. Adding an `embedding` field to `Chunk` would duplicate state the architecture already assigns elsewhere. |
| `embedding_model` | **Deferred — Milestone 2.** | Same reasoning as `embedding`; provenance of a vector belongs with the `EmbeddingProvider`/`VectorStore` boundary, not the corpus-derived `Chunk`. |
| `vector_id` | **Deferred — Milestone 2.** | If ever needed, this is the inverse of `VectorStore.upsert`'s existing `chunk_id` key — `chunk_id` already *is* the join key from the vector store's side; a separate `vector_id` field on `Chunk` would be a redundant, unrequested indirection. |
| `retrieval_score` | **Deferred — belongs to `RetrievalResult`, not `Chunk`.** | Repository fact: `RetrievalResult` (`docs/MILESTONE_1A.md`, build item 4) already carries `score` as a field distinct from `chunks`. A score is query-dependent; `Chunk` is corpus-derived and must stay query-independent to keep its determinism guarantee (Section 7) meaningful — the same chunk retrieved by two different queries cannot have two different scores if the score lives on the chunk itself. |
| `rerank_score` | **Deferred**, same reasoning as `retrieval_score`. | Query-time, not corpus-time. Belongs on a future `RetrievalResult`-adjacent structure, not `Chunk`. |
| `similarity_score` | **Deferred**, same reasoning as `retrieval_score`. | Query-time, not corpus-time. |

The last three rows are the concrete evidence for the Persistent-vs-Runtime-Artifact distinction proposed in Section 5: every deferred scoring field is deferred for the *same* reason (it belongs to query-time `RetrievalResult`, not corpus-time `Chunk`), which is exactly the boundary that distinction names.

---

## 16. Explicit Out-of-Scope Items

Restated from sprint scope, none of which this document designs, decides, or implies a design for:

- Text splitting, recursive chunking, semantic chunking, overlap algorithms
- Tokenization
- Embeddings, embedding models, vector stores (beyond citing their existing interface as evidence — Section 15)
- Lexical indexing implementation, retrieval implementation, context construction, generation
- Serialization implementation (a future container/version-field question is *noted* in Section 19 as a forward dependency for P2.3, not designed here)
- Validation implementation (structural or semantic)
- Document's own field-level data model (noted as an open dependency in Section 11, not resolved here)
- Any implementation code, placeholder classes, or scaffolding

---

## 17. Final Recommended Chunk Contract

Consolidated statement of the frozen v1 Chunk Contract, combining Sections 6–13 into one reference shape.

**Schema:**

| Field | Type | Required | Purpose |
|---|---|---|---|
| `id` | `str` | Yes | Globally unique, deterministic identifier, derived from position (`document_id` + `chunk_index`), not content. |
| `document_id` | `str` | Yes | Foreign key equal to the parent document's `id` in `knowledge_manifest.json`'s `documents[]`. |
| `text` | `str` | Yes | Literal chunk content; equals `document_text[character_start:character_end]`. |
| `chunk_index` | `int` | Yes | Zero-based position among the parent document's chunks, in reading order. |
| `character_start` | `int` | Yes | Zero-based, inclusive, Unicode-code-point start offset into the parent document's text. |
| `character_end` | `int` | Yes | Zero-based, exclusive, Unicode-code-point end offset into the parent document's text. |

**Invariants (all must hold for every conforming Chunk):**

1. `character_end > character_start` (non-empty).
2. `len(text) == character_end - character_start`.
3. `text == document_text[character_start:character_end]` (half-open, Python slicing semantics).
4. For a fixed `document_id`: `chunk_index` values are exactly `0..N-1`, contiguous, no gaps or duplicates.
5. For a fixed `document_id`: ascending `chunk_index` corresponds to ascending `character_start` (reading order preserved).
6. For a fixed `document_id`: chunks do not overlap — `chunk[i].character_end <= chunk[i+1].character_start`.
7. `id` is unique across the entire corpus.
8. Identical `Document` + identical chunking algorithm ⇒ identical `Chunk` sequence, field-for-field (determinism).

**No fields beyond the six above exist in this version of the contract.** Every candidate field evaluated in Section 15 is explicitly deferred, not silently included as optional.

This is the shape P2.2 (Chunk Builder) is expected to construct, P2.3 (Chunk Serialization) is expected to persist, and P2.4 (Chunk Validation) is expected to check.

---

## 18. Repository Impact Assessment

**If and when this document is reviewed and its status changes to Frozen**, the following edits would follow — none of which are made by this document itself:

1. **New file, this document** (`docs/CHUNK_CONTRACT.md`) — follows the existing `datasets/SCHEMA.md` sibling-contract-document precedent (Section 2), rather than embedding this contract inline into the already-dense `docs/MILESTONE_1A.md`, and rather than inventing a new `docs/design/` directory the repository has never used. This is the one new artifact this document itself constitutes.
2. **`docs/MILESTONE_1A.md`, build item 3 (Indexing)** — would gain a short "Contract status: frozen at Sprint P2.1, see `docs/CHUNK_CONTRACT.md`" pointer, mirroring how `docs/architecture.md` §5 already points to `docs/MILESTONE_1A.md` for the Knowledge Manifest's canonical schema ("The canonical schema is defined in `docs/MILESTONE_1A.md`.").
3. **`docs/architecture.md` §5, Chunker row** — would gain a similar one-line pointer to `docs/CHUNK_CONTRACT.md`, matching the existing Knowledge Manifest cross-reference pattern rather than duplicating the schema into the architecture document.
4. **`docs/glossary.md` §3** — would gain a "Chunk Contract" (or similarly named) entry, and, if the Persistent-vs-Runtime-Artifact classification (Section 5) is accepted, a corresponding entry for that distinction — added following the glossary's own rule that new terms are "added here first, then referenced" (`docs/glossary.md` §10).

None of these four edits are performed by this document. `docs/MILESTONE_1A.md` and `docs/architecture.md` are both currently marked Locked/Frozen; editing them is exactly the kind of action this sprint's review-and-freeze gate exists to authorize deliberately, not incidentally.

---

## 19. Readiness Assessment

**P2.2 — Chunk Builder.** Ready to proceed once this document is approved. Construction has a concrete target shape (Section 6, Section 17), an evaluated identity strategy (Section 14.1), and a resolved offset convention (Section 13) to build against. Construction must still decide: the concrete representation, the exact `id`-derivation mechanism, and how `heading`/`section` will eventually be represented once revisited (Section 15) — none of which this document blocks on.

**P2.3 — Chunk Serialization.** Ready to proceed once P2.2 exists, with one open question this document intentionally does not resolve: whether a wrapping container (analogous to the Knowledge Manifest's `manifest_version` + `documents[]` shape) is needed for a persisted chunk collection, and whether that container — not the individual `Chunk` entity — should carry its own schema-version field. Per Section 9's precedent (individual `documents[]`/`facts` entries never carry `schema_version`; only their containers do), this document recommends the same pattern for Chunk, but leaves the container's actual shape to P2.3.

**P2.4 — Chunk Validation.** Ready to proceed once P2.2/P2.3 exist. Structural validation has a precise, checkable contract to validate against (Section 17's invariants, especially the non-overlap and `text == document_text[start:end]` invariants). Semantic/referential validation (does every `document_id` actually exist in the Knowledge Manifest — Section 11) is explicitly named as deferred, not forgotten, matching how `docs/MILESTONE_1A.md` already flags "Semantic validation is a later milestone" for the Knowledge Manifest itself.

---

## 20. Architectural Backlog

This section records known gaps surfaced during this document's discovery and drafting that are deliberately **not** resolved here. Recording them is documentation only — no architecture is proposed or implied for any item below.

**Item: `Document` has no frozen Data Model.**

- **What was discovered:** Repository Discovery (Section 2) found that the runtime `Document` object returned by `KnowledgeSource.load() -> List[Document]` (`docs/architecture.md` §5) has no frozen field-level schema of its own — distinct from a Knowledge Manifest `documents[]` entry, which carries no text content.
- **Why it does not block this Chunk Contract:** This Chunk Contract only assumes that a `Document.id` value seen by the Chunker is identical to the corresponding Knowledge Manifest `documents[].id` (Section 11). That single assumption is sufficient for `Chunk.document_id` to be well-defined; it does not require `Document`'s full field-level schema to be frozen.
- **Why it should still be addressed:** Left undefined, a future implementation of `Document` could silently diverge from this assumption (e.g., adopt a different identifier scheme), which would break `Chunk.document_id`'s contract without any single document flagging the break.
- **Disposition:** Recorded as backlog for a future design sprint — a `Document` Data Model & Contract Freeze, following the same lifecycle already used for the Knowledge Manifest and for this Chunk Contract. Not designed, scoped, or scheduled by this document.

---

*This document is the canonical Chunk Contract for `ai-quality-engineering`, frozen at Sprint P2.1. The Section 18 cross-reference edits to `docs/MILESTONE_1A.md`, `docs/architecture.md`, and `docs/glossary.md` remain a deliberate, separate action, not yet performed. Revise only when a documented contract gap is discovered or Milestone 2 formally supersedes this contract.*
