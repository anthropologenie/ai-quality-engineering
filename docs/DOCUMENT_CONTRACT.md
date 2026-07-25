# Document Contract

**Repository:** `ai-quality-engineering`
**Status:** Approved v1.0 (frozen at Sprint P2.5; Independent Review accepted — see `docs/DOCUMENT_CONTRACT_REVIEW.md`, Outcome A; review corrections F1 and F4–F8 applied at Sprint P2.5.1 — see Correction Record)
**Contract Version:** 1.0
**Related documents:** `docs/CHUNK_CONTRACT.md` (frozen v1.0 — records the backlog item this sprint resolves, §20), `docs/architecture.md` (§5 Component Architecture — `KnowledgeSource.load() -> List[Document]`), `docs/MILESTONE_1A.md` (Knowledge Manifest contract; build item 1), `docs/glossary.md` (canonical terminology — §3, §8), `docs/CHUNK_BUILDER_IMPLEMENTATION_PLAN.md` (§1.2 — the minimal `Document` shape Construction already assumed), `sample_rag/chunker.py` (the one existing consumer of a `Document`-shaped input), `sample_rag/knowledge_manifest.json` (current corpus state)

This document performs the Phase 0–11 planning lifecycle for Sprint P2.5 and, per that lifecycle's own Phase 8 instruction for a Contract Freeze sprint, produces the proposed field-level Document Contract. It is a design and planning specification only. It contains no implementation code, defines no `.docx`/text-extraction mechanism, and authorizes no implementation work by itself.

---

## Executive Summary

Phase 0 verification found that `Document` is **already an established architectural concept** in this repository — declared in an interface signature (`docs/architecture.md` §5) and defined in the canonical glossary (`docs/glossary.md` §8) — but has **no frozen field-level contract** of its own. `docs/CHUNK_CONTRACT.md` §20 already discovered and recorded this exact gap as backlog, recommending "a future design sprint — a Document Data Model & Contract Freeze, following the same lifecycle already used for the Knowledge Manifest and for this Chunk Contract." This sprint is that recorded forward dependency, not a newly invented investigation.

Consequently, this sprint follows the **Contract Freeze** path (Phase 4), not an Architecture Investigation — Phases 6–7 (Architectural Alternatives, Decision Rationale) are conditional and correctly do not execute. The repository decision (Phase 8) is a proposed two-field Document Contract (`id`, `text`), reusing the Knowledge Manifest's existing identity scheme rather than inventing a new one, following the identical minimalism discipline `docs/CHUNK_CONTRACT.md` already applied to `Chunk`.

---

## Phase 0 — Repository Architecture Verification (Gate)

**Question:** does the repository already declare a named `Document` type within an architectural interface?

**Finding: Yes.**

- `docs/architecture.md` §5, Knowledge Source row: `KnowledgeSource.load() -> List[Document]` — this is the exact illustrative example given in this sprint's own brief, found verbatim in the repository rather than hypothesized.
- `docs/architecture.md` §5, Chunker row: `Chunker.chunk(doc: Document) -> List[Chunk]` — a second, independent interface reference to the same type.
- `docs/glossary.md` §8, "Chunk vs. Document" table: *"Document — A full source item (one resume, one job description) before chunking... Consumed at the Knowledge stage."* This is a canonical, authoritative definition per the glossary's own cross-reference philosophy (`docs/glossary.md` §2: terms are "added here first, then referenced," never redefined elsewhere).
- `docs/CHUNK_CONTRACT.md` §2 and §20 both independently confirm and rely on `Document`'s architectural existence while explicitly noting its field-level schema was never frozen.

**Determination, per the sprint's own governing instruction:**

- The architectural existence of `Document` has already been established. This is not in question.
- This sprint concerns the field-level contract and responsibilities of an existing architectural concept — not whether the concept should exist.
- This sprint follows the precedent established by the Chunk Contract planning work (`docs/CHUNK_CONTRACT.md`) rather than initiating a new architectural investigation.

**Planning path: Contract Freeze.**

---

## Phase 1 — Repository Evidence Discovery

Every repository location where `Document` appears, explicitly or implicitly. Observation only — no interpretation (interpretation begins at Phase 3).

| Location | What was found |
|---|---|
| `docs/architecture.md` §5 | `KnowledgeSource.load() -> List[Document]`; `Chunker.chunk(doc: Document) -> List[Chunk]`. Knowledge Source's stated responsibility: "Expose validated resume, job description, and JobOps data to the pipeline." |
| `docs/architecture.md` §4 | Knowledge stage: "Establish a trustworthy source corpus... Outputs: Validated document set." |
| `docs/architecture.md` §7 | `Document` is referenced by type but not itself defined as a `Protocol`; only `EmbeddingProvider`, `VectorStore`, `Retriever`, `Generator` are shown as interfaces. |
| `docs/glossary.md` §8 | Canonical "Chunk vs. Document" definition (quoted above). |
| `docs/glossary.md` §3 | "Corpus — The full set of validated source documents (resume, job descriptions, JobOps data) available to the pipeline." |
| `docs/CHUNK_CONTRACT.md` §2, §11, §20 | Records that `Chunk.document_id` assumes, without freezing, that `Document.id` equals the corresponding `knowledge_manifest.json` `documents[].id`. Explicitly flags "Document has no frozen Data Model" as backlog (§20). |
| `docs/CHUNK_CONTRACT.md` §13 | Chunk offsets are "relative to a single, deterministic plain-text extraction of the parent document — whatever text representation the `Chunker` receives as its `Document` input... explicitly not defined by this document." |
| `docs/CHUNK_BUILDER_IMPLEMENTATION_PLAN.md` §1.2, §3.2 | Chunk Construction (P2.2.1) was explicitly planned against "the minimal shape the Chunk Contract itself already assumes: an input exposing `.id: str`... and `.text: str`," and explicitly barred from "implement[ing] a `Document` Data Model, a `.docx` parser, or a `KnowledgeSource`." |
| `docs/CHUNK_BUILDER_IMPLEMENTATION_PLAN.md` §2 | Repository scan: "No `Chunker`, `Document`, or `Chunk` code exists anywhere in the repository... `KnowledgeSource` appears only as prose in `docs/`." No `.docx`/document-parsing library is declared in `requirements.txt`. |
| `sample_rag/chunker.py` | `_validate_document(doc)` checks only `getattr(doc, "id", None)` (must be `str`) and `getattr(doc, "text", None)` (must be `str`) — duck-typed, no `Document` class imported or defined. Module docstring: "`doc` is assumed to expose `.id: str` and `.text: str` at minimum... the full Document Data Model is out of scope here (Chunk Contract §20)." |
| `tests/test_chunker.py` | Defines a local, test-only `_Document` fixture class (not a repository-wide `Document` implementation) exposing exactly `.id` and `.text`, used only to exercise `Chunker`. |
| `scripts/build_manifest.py` | `REQUIRED_DOCUMENT_FIELDS = {"id": str, "source": str, "hash": str, "indexed": bool}` — this is the **Knowledge Manifest catalog entry** schema (`docs/MILESTONE_1A.md` build item 1), a distinct artifact from the runtime `Document` object. It carries no text content. `SUPPORTED_EXTENSIONS = {".docx", ".md", ".txt"}` gates which files are catalogued (hashed and listed). `compute_sha256` opens and reads each catalogued file in binary mode for hashing only — the module never *parses* file content. No text-extraction capability exists anywhere in the repository. |
| `sample_rag/knowledge_manifest.json` | Exactly one catalogued document: `{"id": "3f3797c1134c", "source": "documents/resume/Karthik_SR_Resume_v2_2.docx", "hash": "e06f...", "indexed": false}`. Current repository behavior assumes and exercises a **single-document** corpus. |
| `sample_rag/documents/resume/` | Contains one file, `Karthik_SR_Resume_v2_2.docx`. |
| `sample_rag/documents/jobs/` | Empty — no job description documents exist in the corpus yet. |
| `docs/MILESTONE_1A.md` build item 4 | SQL-filter retrieval ("JobOps structured queries: salary, location, application status, exclusion criteria") is described as querying JobOps SQLite directly — not routed through `Chunker`/`Document`. |
| `docs/altm.md` line ~149 | Knowledge stage table: "Outputs: Validated, current document set... Owning component: Knowledge Source." No `Document` field detail. |
| `requirements.txt` | `pytest`, `deepeval`, `promptfoo`, `ragas`, `pandas`, `python-dotenv`. No `.docx`-parsing, text-extraction, or document-loading library present. |

**Relationship to Chunk:** `Chunk.document_id` is a foreign key that, per `docs/CHUNK_CONTRACT.md` §11, is assumed (not frozen) to equal `Document.id`. This is the sharpest existing dependency on Document's identity.

**Relationship to Knowledge Source:** `Document` is the return type of `KnowledgeSource.load()`. No `KnowledgeSource` implementation exists; the interface itself appears only in `docs/architecture.md` prose.

**Current corpus characteristics:** one document (a `.docx` resume), zero job descriptions, zero JobOps-sourced documents. Repository behavior does not currently exercise or require multi-document handling beyond what `knowledge_manifest.json`'s array shape and `scripts/build_manifest.py`'s `sorted(...)` determinism mechanism already provide in principle.

---

## Phase 2 — Repository Precedent Review

**Does an equivalent domain object already exist?** Partially. The Knowledge Manifest's `documents[]` entry (`id`, `source`, `hash`, `indexed`) is a *catalog* record — metadata about a document, not the document's content. `docs/CHUNK_CONTRACT.md` §2 already drew this exact distinction: the runtime `Document` "is distinct from a Knowledge Manifest `documents[]` entry (which only carries `id`, `source`, `hash`, `indexed` — no text content)." The Manifest entry is not a substitute for a `Document` contract; it is a sibling artifact this contract must stay consistent with (specifically, on `id`).

**Can an existing lifecycle be reused?** Yes. `docs/CHUNK_CONTRACT.md` §5 already names the lifecycle used for both the Knowledge Manifest and Chunk: `Data Model → Contract Freeze → Construction → Serialization → Validation`. `docs/CHUNK_CONTRACT.md` §20 explicitly recommends this same lifecycle for Document. No repository evidence suggests a different lifecycle is warranted.

**Should an existing repository pattern be adapted?** Yes. The Chunk Contract's own methodology (repository discovery before design, minimal required-field set, explicit deferral of every non-evidenced candidate field, no optional-field tier) is directly reusable, applied to a different entity.

**Is a genuinely new pattern required?** No repository evidence supports this. Document's position in the architecture (Knowledge-stage output, Chunker input) is structurally analogous to Chunk's position (Index-stage output, Indexer input) — both are corpus-derived values consumed by exactly one downstream component.

**Conclusion: Adapt.** Reuse the Chunk Contract's lifecycle and methodology; do not reuse the Knowledge Manifest's *entry schema* (it is a different artifact serving a different purpose — catalog metadata, not text content); do not introduce a new pattern.

---

## Phase 3 — Evidence Classification

Repository evidence converted into architectural observations, without proposing solutions.

| Repository Evidence | Evidence Classification |
|---|---|
| `KnowledgeSource.load() -> List[Document]` is declared in `docs/architecture.md` §5 | The repository has committed to `Document` as an architectural type before any implementation of it exists. |
| `Chunker.chunk(doc: Document) -> List[Chunk]` is the only consumer-side reference to `Document` | Exactly one component depends on `Document`'s shape today; that dependency is already narrowed to `.id`/`.text` in practice (`sample_rag/chunker.py`). |
| `docs/CHUNK_CONTRACT.md` §11 assumes `Document.id == knowledge_manifest.json documents[].id` without freezing it | Chunk's own contract already has an unverified dependency on a fact this document must either confirm or leave open. |
| Knowledge Manifest `documents[]` entries carry no text content | Document text is not currently persisted or catalogued anywhere in the repository; it exists only as a hypothetical runtime extraction. |
| No `.docx`-parsing or text-extraction library is declared or used anywhere in the repository | The mechanism that would populate `Document.text` from `Karthik_SR_Resume_v2_2.docx` does not exist. `Document`'s field-level contract can be frozen independently of this mechanism (the Chunk Contract precedent already established this separation — Contract before Construction). |
| `sample_rag/documents/jobs/` is empty; `knowledge_manifest.json` lists one document | Current repository evidence does not yet demonstrate multi-document operational complexity for `Document`, mirroring the identical finding already made for `Chunk` in `docs/adr/ADR-0001-chunk-persistent-representation.md`. |
| SQL-filter retrieval (`docs/MILESTONE_1A.md` build item 4) queries JobOps SQLite directly | JobOps structured data is not currently modeled as, or routed through, `Document` — despite `docs/architecture.md` §5's Knowledge Source responsibility prose naming "JobOps data" alongside resume/job-description text. This is a textual breadth the current implementation does not exercise. |
| `docs/architecture.md` §5 lists Knowledge Source's dependencies as "JobOps SQLite (read-only), **resume file**" and its interface as `KnowledgeSource.load() -> List[Document]`; §4 gives the Knowledge stage inputs "Resume, job descriptions, JobOps SQLite" → outputs "Validated document set"; §10 locks *"Knowledge ingestion operates on the canonical `.docx` corpus"*; `docs/altm.md` line 149 names **Knowledge Source** as the Knowledge stage's Responsible Component | The responsibility of turning a raw source file into `Document.text` is real (the Chunker's input must come from somewhere) and is **already owned by Knowledge Source**. No component named "Loader" appears in §5 because none is required — the responsibility sits inside an existing, named component. What remains undetermined is the extraction *mechanism* and Knowledge Source's internal decomposition, which are Construction concerns, not architectural ones. *(Corrected at Sprint P2.5.1 per `docs/DOCUMENT_CONTRACT_REVIEW.md` Finding F1.)* |
| `docs/CHUNK_BUILDER_IMPLEMENTATION_PLAN.md` §1.2 already bounded Chunk Construction to a minimal `.id`/`.text` assumption and explicitly prohibited it from building a `Document` Data Model | The repository has already practiced, once, the exact separation this sprint is chartered to formalize: a downstream component can be built against an *assumed* minimal Document shape without that shape being frozen — but the assumption itself was never promoted to a contract. |

---

## Phase 4 — Determine Sprint Shape

Per Phase 0's finding (`Document` already architecturally committed) and Phase 2's conclusion (Adapt, not Introduce), this sprint is a **Contract Freeze**, not an Architecture Investigation.

The remaining work, per the sprint's own instruction for this outcome, is to define:

- responsibilities — Phase 5, Phase 9
- field-level contract — Phase 8
- ownership — Phase 9
- lifecycle — Phase 8, Phase 10

This sprint follows the precedent established by `docs/CHUNK_CONTRACT.md` rather than initiating Phases 6–7 (Architectural Alternatives, Decision Rationale), which are conditional on an Architecture Investigation outcome that Phase 0 did not find.

---

## Phase 5 — Problem Statement

Using only the evidence classified in Phase 3, the architectural problem this sprint addresses is narrower than "should Document exist" — it is:

- **Implied but undefined responsibility:** `Chunker.chunk(doc: Document)` has been implemented and committed against an *assumed* shape (`.id`, `.text`) that was never promoted from implementation assumption to frozen contract. This is the same category of gap the Knowledge Manifest and Chunk contracts each closed for their own entities before their respective Construction sprints began.
- **Duplicated-assumption risk:** `docs/CHUNK_CONTRACT.md` §11 depends on `Document.id == knowledge_manifest.json documents[].id` holding true. `sample_rag/chunker.py` independently duck-types the same assumption. Neither location is the authoritative source for this fact; both would silently break if a future `Document` implementation adopted a different identifier scheme.
- **Undefined extraction mechanism (not undefined ownership):** the text-extraction step (`.docx` → plain text) that `Document.text` presupposes is **owned by Knowledge Source** — `docs/architecture.md` §5 names the "resume file" as its dependency and `KnowledgeSource.load() -> List[Document]` as its interface, §10 locks *"Knowledge ingestion operates on the canonical `.docx` corpus"*, and `docs/altm.md` line 149 names Knowledge Source as the Knowledge stage's Responsible Component. What no frozen document addresses is the *mechanism* by which that owner produces `Document.text`, which is a Construction concern. *(Corrected at Sprint P2.5.1 per `docs/DOCUMENT_CONTRACT_REVIEW.md` Finding F1; originally stated as "unclear ownership.")*
- **Lifecycle gap:** `Document` has no defined position in the `Data Model → Contract Freeze → Construction → Serialization → Validation` lifecycle already applied to the Knowledge Manifest and to Chunk. It is currently frozen at none of these stages.
- **Dependency gap:** Chunk's own frozen invariant (`text == document_text[character_start:character_end]`, `docs/CHUNK_CONTRACT.md` §13, §17 invariant 3) is only partially checkable today (per `docs/CHUNK_VALIDATION_PLAN.md` §P1.4) precisely because no `Document` representation exists to check it against.
- **Deferred responsibility:** referential integrity between `Chunk.document_id` and its parent `Document`/Manifest entry has twice been deferred (`docs/CHUNK_CONTRACT.md` §11, `docs/CHUNK_VALIDATION_PLAN.md` §P5) pending a `Document` contract that did not yet exist. This sprint is a precondition for that deferred work eventually being resolvable.

None of the above requires inventing a new architectural concept. All of it requires giving an already-named concept a frozen shape.

---

## Phase 6 — Architectural Alternatives

**Not executed.** Phase 0 determined that `Document` is already an established architectural concept; Phase 4 classified this sprint as a Contract Freeze. Per the sprint's own governing instruction, Phase 6 executes "only if Phase 4 determines that an architectural investigation is required." It was not.

## Phase 7 — Decision Rationale

**Not executed**, for the same reason as Phase 6. No alternatives were evaluated because none were required to be.

---

## Phase 8 — Repository Decision

### 8.1 Repository Definition

`Document` is the Knowledge-stage output of the pipeline: a full source item (one resume, one job description) exposed by `KnowledgeSource.load()`, before chunking (`docs/glossary.md` §8). It is the input to `Chunker.chunk(doc: Document) -> List[Chunk]` (`docs/architecture.md` §5) and is distinct from a `knowledge_manifest.json` `documents[]` catalog entry, which describes a document (`id`, `source`, `hash`, `indexed`) without carrying its text.

### 8.2 Data Model

**Entity: `Document`**

One `Document` represents one full, validated source item's deterministic plain-text content, exposed to the pipeline at the Knowledge stage.

| Field | Type | Relationship |
|---|---|---|
| `id` | `str` | Identity of this document. Must equal the corresponding entry's `id` in `knowledge_manifest.json`'s `documents[]` (Section 8.4). |
| `text` | `str` | The document's full, deterministic plain-text content — the reference frame `Chunk.character_start`/`character_end` are computed against (`docs/CHUNK_CONTRACT.md` §13). |

These are the only fields evidenced as required by an existing, frozen consumer. See Section 8.6 for every candidate field considered and explicitly deferred.

### 8.3 Field-Level Contract

Mirroring `docs/CHUNK_CONTRACT.md` §7's contract framing:

> **Contract status (proposed at Sprint P2.5, pending review):** the schema in Section 8.2 defines what a `Document` *is*. How `Document` instances are constructed — including any `.docx`, Markdown, or plain-text extraction mechanism — is an implementation concern for a future Construction sprint, not defined here.

**Required fields:** `id`, `text` — both, no exceptions.

**Optional fields:** none in this proposed contract (Section 8.6).

**Identity guarantee:** `id` is a `str` and is unique across the corpus, reusing the identity already frozen for `knowledge_manifest.json` `documents[].id` (`docs/MILESTONE_1A.md` build item 1) rather than establishing a second identity scheme for the same underlying document (Section 8.4).

**Content guarantee:** `text` is a `str` representing a single, deterministic plain-text extraction of the source item. Identical source content, extracted by an identical mechanism, must produce identical `text` — this is the same determinism discipline already governing the Knowledge Manifest (`docs/MILESTONE_1A.md` build item 1, "Deterministic artifact contract") and Chunk (`docs/CHUNK_CONTRACT.md` §7). `docs/CHUNK_CONTRACT.md` §13 already depends on this property; this contract makes it an explicit requirement of `Document` itself rather than an assumption borrowed from a downstream consumer.

**Non-empty guarantee:** this contract does not require `text` to be non-empty. `docs/CHUNK_CONTRACT.md` §11 already establishes that "a document produces zero or more chunks" as a legal outcome; an empty `Document.text` is consistent with that existing guarantee, not a new one.

### 8.4 Identity Rules

- `id` is a `str`.
- `id` **must equal** the corresponding entry's `id` field in `knowledge_manifest.json`'s `documents[]` array — not derived independently. This closes the gap `docs/CHUNK_CONTRACT.md` §11 explicitly flagged as an open, unresolved assumption ("this document assumes — but does not itself freeze — that whatever `Document.id` the Chunker receives at construction time is identical to the corresponding Knowledge Manifest `documents[].id`"). This proposed contract resolves that flag by freezing the equality directly, rather than leaving two independent locations (`docs/CHUNK_CONTRACT.md` and `sample_rag/chunker.py`) each assuming it separately.
- This contract does **not** introduce a second, competing identity scheme. The Knowledge Manifest's `documents[].id` generation mechanism (`scripts/build_manifest.py`'s `generate_document_id`, a SHA-256 digest of the normalized source path, truncated) is reused as-is; `Document.id` is not independently derived by this contract.
- **Justification:** identical to `docs/CHUNK_CONTRACT.md` §14.2's own reasoning for `Chunk.document_id`: reusing an already-frozen, already-validated identity scheme is preferred over inventing a second one for the same underlying entity.

### 8.5 Parent Relationships

`Document` has no parent entity in this contract — it is the root of the Knowledge-stage data model (the Knowledge Manifest catalog entry is a sibling artifact describing the same corpus item, not a parent of `Document`; see Section 8.1).

- **Document → Knowledge Manifest entry:** one-to-one, via `id` (Section 8.4). Every `Document` returned by `KnowledgeSource.load()` corresponds to exactly one `knowledge_manifest.json` `documents[]` entry.
- **Document → Chunk:** one-to-many. A `Document` produces zero or more `Chunk`s via `Chunker.chunk(doc)` (`docs/CHUNK_CONTRACT.md` §6).
- **Referential integrity** (verifying that every `Document.id` returned by `KnowledgeSource.load()` actually has a corresponding `knowledge_manifest.json` entry) is **not** part of this structural contract, for the identical reason `docs/CHUNK_CONTRACT.md` §11 already gave for `Chunk.document_id`: it is a semantic/cross-artifact validation concern, not a structural one. Deferred to the same Data Quality Validation pytest layer (`docs/MILESTONE_1A.md` build item 2) already recommended as the home for Chunk's own deferred referential-integrity check (`docs/CHUNK_VALIDATION_PLAN.md` §P5).

### 8.6 Deferred Fields

Every candidate field with repository evidence naming it is evaluated individually, following `docs/CHUNK_CONTRACT.md` §15's own methodology. None are included in the v1 proposed contract.

| Field | Decision | Rationale |
|---|---|---|
| `source` (file path) | **Deferred.** | Already owned by `knowledge_manifest.json` `documents[].source` (`docs/MILESTONE_1A.md` build item 1). No evidenced consumer of `Document` (currently, only `Chunker`) requires the path directly — `Document.id` already provides a stable join key back to the Manifest entry, which carries `source` if needed. Duplicating it on `Document` risks the same drift the Manifest's own `id`/`source` separation was designed to avoid. |
| `hash` | **Deferred.** | Already owned by `knowledge_manifest.json` `documents[].hash`, used for corpus-level freshness/integrity checking (`docs/MILESTONE_1A.md` build item 1). No evidence that any `Document`-level consumer needs a hash independent of the Manifest's existing one. |
| `document_type` / `kind` (e.g., resume, job_description) | **Deferred**, but flagged as the strongest near-term candidate. | `docs/architecture.md` §5 names Knowledge Source's responsibility as exposing "resume, job description, and JobOps data," and `docs/MILESTONE_1A.md` build item 3 describes chunking strategy that differs by document type ("resume headers, JD fields like Responsibilities/Requirements"). However, `sample_rag/chunker.py`'s structural-boundary detection currently operates on `text` content structure alone (blank-line boundaries) and does not branch on an explicit type field — mirroring exactly how `docs/CHUNK_CONTRACT.md` §15 deferred `heading`/`section` as "directly relevant... but... Construction has not yet decided the concrete shape." Recommend revisiting once a real job-description document exists in the corpus (currently, `sample_rag/documents/jobs/` is empty) and Construction has evidence of whether type-specific handling is actually needed. |
| `metadata` (JobOps structured fields — salary, location, application status) | **Deferred — scope boundary, not just timing.** | Repository evidence (`docs/MILESTONE_1A.md` build item 4) shows SQL-filter retrieval already queries JobOps SQLite *directly*, bypassing `Document`/`Chunker` entirely. No repository evidence shows JobOps structured data ever being wrapped as a `Document`. Adding a `metadata` field here would be speculative, not evidenced — see Phase 11, Outstanding Question 3, for the broader unresolved classification question this defers. |
| `character_count` / `length` | **Deferred.** | Fully derivable from `len(text)` at any point by any consumer; no evidence any consumer needs it precomputed and stored. Mirrors the reasoning already applied to similarly-derivable fields in `docs/CHUNK_CONTRACT.md` §15. |

### 8.7 Final Proposed Document Contract

Consolidated statement of the proposed v1 Document Contract.

**Schema:**

| Field | Type | Required | Purpose |
|---|---|---|---|
| `id` | `str` | Yes | Identity, reused unmodified from `knowledge_manifest.json`'s `documents[].id` — not independently derived. |
| `text` | `str` | Yes | Deterministic plain-text extraction of the source item; the reference frame `Chunk` offsets are computed against. |

**Invariants (proposed, all must hold for every conforming Document):**

1. `id` is a `str` and equals the corresponding `knowledge_manifest.json` `documents[].id` entry.
2. `text` is a `str` (may be empty; an empty `Document` legally produces zero chunks, per `docs/CHUNK_CONTRACT.md` §11).
3. Identical source content, extracted by an identical mechanism, produces an identical `text` value (determinism).

**No fields beyond these two exist in this version of the contract.** Every candidate field evaluated in Section 8.6 is explicitly deferred, not silently included as optional.

### 8.8 Recorded Limits of Invariant 3 (Determinism)

*Added at Sprint P2.5.1 per `docs/DOCUMENT_CONTRACT_REVIEW.md` Finding F8. This section records two consequences of invariant 3 that were previously unstated. It does not weaken, alter, or reinterpret the invariant itself — Sections 8.2–8.7 are unchanged.*

1. **Invariant 3 is not checkable from any single artifact.** Determinism is a property of *repeated construction*, not of one `Document` value: verifying it requires comparing the output of two runs over identical source content. It therefore cannot be folded into a future structural Document validator. This is the identical limit already established for Chunk invariant 8 (`docs/CHUNK_CONTRACT.md` §17) and recorded as such by `docs/CHUNK_VALIDATION_PLAN.md` §P1.4 and §P8, and by `docs/CHUNK_SERIALIZATION_PLAN.md` §P5, which route the analogous check to a two-run test/CI strategy rather than to a single-artifact validator.

2. **No existing check detects extracted-text drift.** `knowledge_manifest.json`'s `documents[].hash` is a SHA-256 digest of the **source file's bytes** (`scripts/build_manifest.py`'s `compute_sha256`), not of extracted text. A change to the extraction mechanism can therefore alter `Document.text` for byte-identical source content without any existing freshness or integrity check registering it. Invariant 3 is mechanism-relative by design — matching, and not weaker than, the equivalent scoping in `docs/CHUNK_CONTRACT.md` §10 — but that scoping means the repository currently has no detector for a mechanism change. Recorded here only; no detector is designed, scoped, or required by this contract. It is a Data Quality Validation concern (`docs/MILESTONE_1A.md` build item 2) if a need for one is ever evidenced.

---

## Phase 9 — Repository Boundaries

| Component | Owns | Evidence |
|---|---|---|
| **Knowledge Source** | Producing `Document` instances via `.load()`; owning `knowledge_manifest.json` (the corpus catalog, a sibling artifact to `Document`, not `Document` itself). | `docs/architecture.md` §5 |
| **Document** | No behavior — a passive, corpus-derived data value (`id`, `text`) per Section 8.2. Owns nothing downstream of itself. | This document, Section 8 |
| **Chunk** | Retrievable text spans derived from exactly one `Document`, via `chunk_index`/`character_start`/`character_end`. | `docs/CHUNK_CONTRACT.md` §6 |
| **Text extraction** *(no separate component — owned by Knowledge Source)* | Populating `Document.text` from a raw source file (e.g., `.docx` parsing) belongs to **Knowledge Source**, whose declared dependency is the "resume file" and whose declared output is `List[Document]`. No "Loader" component is warranted or introduced: `docs/architecture.md` §5's table names no such component because none is required, and adding one would create a new first-class architectural concept without repository evidence — the bar `docs/adr/ADR-0001-chunk-persistent-representation.md` already applied and refused to cross. The extraction *mechanism* and Knowledge Source's internal decomposition remain open, and are Construction-planning concerns. | `docs/architecture.md` §5 (interface + "resume file" dependency), §4, §10 (locked: "Knowledge ingestion operates on the canonical `.docx` corpus"); `docs/altm.md` line 149 (Responsible Component: Knowledge Source); `docs/DOCUMENT_CONTRACT_REVIEW.md` Finding F1 |
| **Validator** | Structural validation of a `Document` instance (were one to be built, mirroring `validate_manifest`/`validate_chunks`) is not yet designed — out of scope for this Contract Freeze, consistent with how `docs/CHUNK_CONTRACT.md` deferred Chunk's own validation design to a later sprint (P2.4). Semantic/referential checks (Document.id ↔ Manifest entry) belong to the Data Quality Validation pytest layer (`docs/MILESTONE_1A.md` build item 2), per Section 8.5. | `docs/MILESTONE_1A.md` build item 2; `docs/CHUNK_VALIDATION_PLAN.md` §P5 |
| **Retriever** | Operates on `Chunk`/`RetrievalResult`, not `Document` directly. The SQL-filter stage queries JobOps SQLite directly, independent of `Document` (Phase 3, Phase 11 Q3). | `docs/MILESTONE_1A.md` build item 4 |
| **Generator** | Operates on assembled prompts (`ContextBuilder` output), no relationship to `Document`. | `docs/architecture.md` §5 |

No responsibility above is assigned to more than one component.

---

## Phase 10 — Forward Dependencies

**Work enabled by this contract, once reviewed and frozen:**

- **Document Construction** — implementing `KnowledgeSource` and a concrete text-extraction mechanism (e.g., `.docx` parsing) against the frozen shape in Section 8.2, mirroring how `docs/CHUNK_BUILDER_IMPLEMENTATION_PLAN.md` planned Chunk Construction against `docs/CHUNK_CONTRACT.md`.
- **Full Chunk invariant 3 checkability** — `docs/CHUNK_VALIDATION_PLAN.md` §P1.4 recorded that `text == document_text[character_start:character_end]` is only partially checkable (via `len(text) == character_end - character_start`) because no `Document` representation exists to check the full substring equality against. A real `Document` implementation, built against this contract, unblocks that check.
- **Chunk `document_id` referential integrity** — `docs/CHUNK_CONTRACT.md` §11 and `docs/CHUNK_VALIDATION_PLAN.md` §P5 both deferred this pending a `Document` contract. This document supplies the missing identity guarantee (Section 8.4) that check depends on; the check itself remains a future Data Quality Validation pytest layer responsibility, not implemented here.
- **`docs/CHUNK_CONTRACT.md` §20 backlog item closure** — this document is the design sprint that item called for. Closing it does not require modifying `docs/CHUNK_CONTRACT.md` itself; the backlog item's own text already anticipates being resolved by a separate, later document. A comparable, separate synchronization pass should nonetheless be expected once this document's own status changes: `docs/CHUNK_CONTRACT.md` §18's cross-reference edits **were performed**, at commit `994f7b1` ("docs: synchronize repository with frozen Chunk Contract"), which updated `docs/MILESTONE_1A.md`, `docs/architecture.md`, and `docs/glossary.md`. That pass is not performed by this document. *(Corrected at Sprint P2.5.1 per `docs/DOCUMENT_CONTRACT_REVIEW.md` Finding F5; this passage previously described those edits as not-yet-performed.)*

**Work intentionally deferred (recorded, not scheduled):**

- **Document Serialization** — whether `Document` (or its extracted `text`) needs its own persisted, version-controlled representation (analogous to `chunks.json`), or remains a build-time-only, on-demand extraction with no independent artifact. No repository evidence currently establishes a need for persistence beyond what `knowledge_manifest.json` (catalog) and a future `.docx`-extraction mechanism (on-demand) already provide. If pursued, this would follow the same Contract-before-Serialization sequencing already used for Chunk.
- **Document Validation** — structural validation of a `Document` instance against Section 8.2's contract is not designed here, mirroring how Chunk Validation was a distinct, later sprint (P2.4) built only after Chunk Construction and Serialization existed.
- **`document_type`/`kind` field** — flagged in Section 8.6 as the strongest near-term candidate, deferred pending real evidence from a job-description document actually entering the corpus.
- **Text-extraction mechanism** — *not* an ownership question: Knowledge Source already owns text extraction (Phase 9; `docs/architecture.md` §5, §10; `docs/altm.md` line 149). No new component is warranted, and `docs/architecture.md` §5 requires no edit. What is deferred is the concrete extraction mechanism and Knowledge Source's internal decomposition — Construction-planning concerns, addressed by `docs/DOCUMENT_CONSTRUCTION_PLAN.md`. *(Corrected at Sprint P2.5.1 per `docs/DOCUMENT_CONTRACT_REVIEW.md` Finding F1; previously recorded as "Loader ownership," an architecture-level decision.)*

**Explicitly outside Milestone 1A** (per `docs/MILESTONE_1A.md`'s own Out of Scope list, unaffected by this document): real `.docx` parsing at production quality, multi-document corpus generation at scale, JobOps-as-Document modeling, embeddings, retrieval quality, and generation — none of these are enabled, blocked, or altered by this contract.

---

## Phase 11 — Outstanding Questions

1. **Should `source` or `document_type` be promoted from deferred to required once real job-description documents exist in the corpus?**
   - Why unresolved: `sample_rag/documents/jobs/` is currently empty; no repository evidence yet demonstrates whether `Chunker`'s structural-boundary detection needs type-aware branching in practice.
   - Construction evidence required: yes — first real ingestion of a job-description document.
   - Disposition: intentionally deferred, not a present gap; revisit at Document Construction time if evidence emerges.

2. **Which component owns text-extraction (e.g., `.docx` parsing) — is a new "Loader" component warranted, or does this responsibility belong inside `KnowledgeSource` itself?** — **ANSWERED. Not an architectural gap.** *(Reclassified at Sprint P2.5.1 per `docs/DOCUMENT_CONTRACT_REVIEW.md` Finding F1 and its Phase 5 classification table. Retained rather than deleted, so the question and its resolution stay on the record.)*
   - Answer: the responsibility belongs to **`KnowledgeSource`**. No "Loader" component is warranted, and none is introduced.
   - Evidence: `docs/architecture.md` §5 lists Knowledge Source's dependencies as "JobOps SQLite (read-only), **resume file**" and its interface as `KnowledgeSource.load() -> List[Document]` — no component sits between the raw file and the returned `Document`; §4 gives the Knowledge stage inputs "Resume, job descriptions, JobOps SQLite" → outputs "Validated document set"; §10 **locks** *"Knowledge ingestion operates on the canonical `.docx` corpus"*; `docs/altm.md` line 149 names **Knowledge Source** as the Knowledge stage's Responsible Component. Knowledge-Source-owned code (`scripts/build_manifest.py`) already opens corpus files today.
   - Why the original framing was wrong: the literal premise — that no component *named* "Loader" appears in §5 — is true, but the conclusion that the responsibility is therefore unowned does not follow, and contradicts evidence this document itself cites in Phase 1 (`docs/altm.md` line 149's Responsible Component column).
   - What remains open: the extraction *mechanism* and Knowledge Source's internal decomposition — Construction-planning concerns of the same class `docs/CHUNK_BUILDER_IMPLEMENTATION_PLAN.md` §2.1 resolved for `Chunker` without an ADR. Addressed by `docs/DOCUMENT_CONSTRUCTION_PLAN.md`.
   - Governance consequence: no ADR is required, and `docs/architecture.md` requires no amendment — introducing a "Loader" would create a new first-class architectural concept without repository evidence, the bar `docs/adr/ADR-0001-chunk-persistent-representation.md` already applied and declined to cross.

3. **Does JobOps structured data (SQLite) ever get modeled as a `Document`, or does SQL-filter retrieval permanently bypass `Document`/`Chunk` entirely?**
   - Why unresolved: `docs/architecture.md` §5's Knowledge Source responsibility prose ("resume, job description, and JobOps data") is textually broader than what any frozen interface or current implementation exercises. `docs/MILESTONE_1A.md` build item 4 describes JobOps SQL-filter retrieval as a direct, separate data path.
   - Construction evidence required: no — this is an existing textual ambiguity in an already-locked document (`docs/architecture.md`), not something new evidence would resolve; it requires an explicit scope clarification.
   - Disposition: intentionally not resolved by this contract (Document's schema, Section 8.2, is scoped to text corpus items only — resume and job descriptions — consistent with `docs/glossary.md` §8's own definition). Flagged for a future milestone or documentation clarification, not a blocking issue for Document Construction against text-based sources.
   - Stronger supporting evidence *(added at Sprint P2.5.1 per `docs/DOCUMENT_CONTRACT_REVIEW.md` Finding F7)*: this exclusion is **structural, not merely prose scoping**. `scripts/build_manifest.py` discovers corpus items only beneath `DOCUMENTS_ROOT` and only where the suffix matches `SUPPORTED_EXTENSIONS = {".docx", ".md", ".txt"}`. A JobOps SQLite row therefore cannot obtain a `knowledge_manifest.json` `documents[]` entry, and consequently cannot satisfy Section 8.4's identity requirement that `Document.id` equal such an entry's `id`. The *implemented* Knowledge Manifest already excludes JobOps-as-Document under this contract; the residual ambiguity is confined to `docs/architecture.md` §5's responsibility prose, which is broader than any implemented path.

4. **Should `Document` be classified under the Persistent Canonical Artifact / Runtime Artifact distinction `docs/CHUNK_CONTRACT.md` §5 introduced?**
   - Why unresolved: **not** because the classification lacks canonical status — it has it. `docs/glossary.md` §3 contains a "Persistent Canonical Artifact / Runtime Artifact" entry, added at commit `994f7b1`, so it is a frozen glossary term rather than the recommendation `docs/CHUNK_CONTRACT.md` §3 originally flagged. The question is unresolved because whether `Document` fits either category cleanly depends on the still-open Serialization question (Phase 10). *(Premise corrected at Sprint P2.5.1 per `docs/DOCUMENT_CONTRACT_REVIEW.md` Finding F4; the disposition below is unchanged.)*
   - Construction evidence required: yes — resolving whether `Document` is ever persisted independently of on-demand extraction.
   - Disposition: intentionally deferred; not required to freeze the field-level contract in Section 8.2, exactly as `docs/CHUNK_CONTRACT.md` §19 left Chunk's own container/persistence shape open at contract-freeze time.

None of the above blocked the field-level contract in Phase 8 from being reviewed and frozen. Question 2 is answered and closed (above). Questions 1, 3, and 4 remain forward dependencies for later work, not defects in this document's own scope — a classification the accepted independent review confirmed for each (`docs/DOCUMENT_CONTRACT_REVIEW.md`, Phase 5 classification table: none requires an ADR).

---

## Construction Readiness Review

- [x] Repository Architecture Verification complete — Phase 0
- [x] Repository Evidence Discovery complete — Phase 1
- [x] Repository Precedent Review complete (Adapt) — Phase 2
- [x] Evidence Classification complete — Phase 3
- [x] Sprint Shape determined (Contract Freeze) — Phase 4
- [x] Problem Statement evidence-backed — Phase 5
- [x] Phases 6–7 correctly skipped, with reasoning stated — Phase 6, Phase 7
- [x] Field-level Document Contract proposed — Phase 8
- [x] Repository Boundaries unambiguous — Phase 9
- [x] Forward Dependencies documented — Phase 10
- [x] Outstanding Questions explicitly recorded — Phase 11

**Result: PASS.** No blocking gap was found for this planning sprint itself. Four outstanding questions were recorded (Phase 11), none of which blocked review of the two-field contract (Section 8.7). Following the accepted independent review, Question 2 is **answered and closed** — text extraction is owned by Knowledge Source, no ADR is required, and no architecture-level decision is outstanding. Questions 1, 3, and 4 remain scoped to later work (corpus expansion; a documentation clarification to `docs/architecture.md` §5's prose; Document Serialization) and none requires an ADR (`docs/DOCUMENT_CONTRACT_REVIEW.md`, Phase 5 classification table). *(Corrected at Sprint P2.5.1 per Finding F1; this paragraph previously listed "Loader ownership" as a separate architecture-level decision.)*

---

## Correction Record — Sprint P2.5.1

This document was independently reviewed at the Sprint P2.5 review gate. The review (`docs/DOCUMENT_CONTRACT_REVIEW.md`) returned **Outcome A — APPROVED**: the contract in Sections 8.2–8.7 was approved as written, with no field, type, invariant, deferral, or identity rule requiring revision, and with no additional ADR required before Document Construction Planning.

Sprint P2.5.1 was a documentation-only pass applying that review's findings to this document. **Sections 8.2 through 8.7 — the schema itself — are byte-for-byte unchanged.** Only analysis sections the review found wrong or stale were corrected. This record follows the precedent of `docs/MILESTONE_1A.md` build item 1's own "Contract Change — `created_at` removed" note: a correction is recorded, not silently applied.

| Finding | Correction applied | Locations |
|---|---|---|
| **F1** (material) | The claim that text extraction is unowned is replaced throughout with the review's evidence-backed conclusion: **Knowledge Source owns text extraction**; no "Loader" component is warranted or introduced; what remains open is the extraction mechanism and internal decomposition, a Construction concern. | Phase 3 (evidence row); Phase 5 ("Unclear ownership" → "Undefined extraction mechanism"); Phase 9 (Loader row → Text extraction row); Phase 10 ("Loader ownership" bullet); Phase 11 Q2 (reclassified as **ANSWERED**, retained not deleted); Construction Readiness Review |
| **F4** (accuracy) | Question 4's stated premise corrected: the Persistent Canonical Artifact / Runtime Artifact classification **is** a frozen `docs/glossary.md` §3 entry (added at commit `994f7b1`), not a pending recommendation. Disposition unchanged. | Phase 11 Q4 |
| **F5** (accuracy) | Corrected the claim that `docs/CHUNK_CONTRACT.md` §18's cross-reference edits are unperformed — they were performed at commit `994f7b1`. Added that a comparable synchronization pass should be expected for this document, without performing it. | Phase 10 |
| **F6** (accuracy) | Corrected "the module never opens or parses file content": `compute_sha256` opens and reads every catalogued file in binary mode for hashing. The substantive claim — no text-extraction capability exists — is unchanged and correct. | Phase 1 (evidence row) |
| **F7** (completeness) | Added the stronger evidence the review identified for Question 3: `scripts/build_manifest.py`'s `DOCUMENTS_ROOT`/`SUPPORTED_EXTENSIONS` discovery gate means a JobOps SQLite row cannot obtain a `documents[]` entry and therefore cannot satisfy Section 8.4 — a **structural** exclusion, not merely prose scoping. Disposition unchanged. | Phase 11 Q3 |
| **F8** (completeness) | Recorded two previously unstated consequences of invariant 3: it is not checkable from a single artifact (requires a two-run comparison, as for Chunk invariant 8), and `documents[].hash` covers source bytes rather than extracted text, so no existing check detects extraction-mechanism drift. Added as a new Section 8.8 **adjacent to, and without modifying**, Section 8.7. | New Section 8.8 |
| — | Document status updated to reflect acceptance (header). | Header |

**F2 and F3 are not corrections to this document.** The review classified them as unrecorded consequences requiring an owner, and this sprint's governing brief assigns them to Document Construction Planning, where they are addressed as `docs/DOCUMENT_CONSTRUCTION_PLAN.md` §9 (identity-derivation coupling) and §12 (dependency governance) respectively.

**Not performed by this pass** (recorded, separate, broader work): the repository synchronization described in `docs/DOCUMENT_CONSTRUCTION_PLAN.md` §14.2 items 2–5 — a `docs/glossary.md` "Document Contract" entry, a `docs/architecture.md` §5 pointer, and a `docs/MILESTONE_1A.md` pointer. No file other than this one was modified.

**Residual wording note.** Sections 8.3, 8.6, and 8.7 retain the word "proposed" (e.g. "Contract status (proposed at Sprint P2.5, pending review)", "Final Proposed Document Contract"), which now trails the approved status in the header. This is deliberate: those sections fall inside the byte-for-byte-unchanged schema range and were not touched. Removing the pre-approval phrasing is a separate, purely cosmetic edit for a future pass.

---

## Stop Condition

Per the sprint's own governing instruction, this document ends here.

No `Document` class, loader, `.docx` parser, or any runtime code has been implemented. No filesystem logic, CLI, or tests have been written. `docs/architecture.md`, `docs/CHUNK_CONTRACT.md`, `docs/glossary.md`, and `docs/MILESTONE_1A.md` are unchanged. No commit has been made to any of them.

The contract in Section 8.7 has been reviewed and approved (`docs/DOCUMENT_CONTRACT_REVIEW.md`, Outcome A), and the corrections above have been applied. Construction planning is complete (`docs/DOCUMENT_CONSTRUCTION_PLAN.md`); Document Construction (Sprint P3.1) awaits approval of that plan. *(Sentence updated at Sprint P2.5.1; it previously read "Awaiting review and approval of the proposed contract (Section 8.7) before a Document Construction sprint begins.")*
