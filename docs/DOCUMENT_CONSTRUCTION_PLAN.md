# Document Construction — Implementation Plan

**Repository:** `ai-quality-engineering`
**Status:** Planning (Construction Readiness Review — Sprint P3.0)
**Related documents:** `docs/DOCUMENT_CONTRACT.md` (approved v1.0 — the only source of `Document` field/invariant truth), `docs/DOCUMENT_CONTRACT_REVIEW.md` (accepted independent review — Outcome A; findings F1–F8), `docs/architecture.md` (§2 Principles, §5 Component Architecture, §6 Repository Structure, §10 Architectural Decisions), `docs/roadmap.md` (§6 Repository Principles, §7 Scope Freeze), `docs/MILESTONE_1A.md` (build items 1–3, 6; Libraries; Acceptance Criteria), `docs/CHUNK_BUILDER_IMPLEMENTATION_PLAN.md` (the repository's reference Construction-planning precedent), `docs/CHUNK_VALIDATION_PLAN.md` (§P5 coupling precedent, §P1.4 capability-limit precedent), `scripts/build_manifest.py` (the repository's only implemented deterministic-artifact builder), `sample_rag/chunker.py` (the one existing consumer of a `Document`-shaped input)

This document plans **how** Sprint P3.1 will construct `Document` instances conforming to the approved Document Contract. It does not define what a `Document` is (`docs/DOCUMENT_CONTRACT.md`'s job, unchanged here), does not reopen architectural ownership (settled by `docs/DOCUMENT_CONTRACT_REVIEW.md`), selects no parser or dependency, and authorizes no implementation work by itself. It is a planning artifact only.

---

## Terminology Note

No new repository-wide terminology is introduced. "Construction," "extraction," "corpus item," and "resolution" are used descriptively in the sense `docs/DOCUMENT_CONTRACT.md` and `docs/CHUNK_BUILDER_IMPLEMENTATION_PLAN.md` already use them. "Identity Strategy S1/S2/S3" (§9) is this document's own working labelling for organizing an evaluation, not a proposed glossary entry — exactly as `docs/CHUNK_VALIDATION_PLAN.md` treated "Layer 1/2/3" and `docs/CHUNK_SERIALIZATION_PLAN.md` treated "container."

The component name is **Knowledge Source**, with the frozen interface `KnowledgeSource.load() -> List[Document]` (`docs/architecture.md` §5). This plan does not introduce "Loader," "DocumentBuilder," or any second name for that component.

---

## P0 — Planning Precondition Verification

Verified against repository state at commit `74d4ba3` ("docs(document): add Document Contract and independent architectural review"), the most recent commit on `main`.

### P0.1 Repository State

| Precondition | Status | Evidence |
|---|---|---|
| Document Contract has been approved | ✅ Satisfied | `docs/DOCUMENT_CONTRACT_REVIEW.md`, "OUTCOME A — APPROVED": *"The proposed Document Contract (§8.7) is approved as written — no field, type, invariant, deferral, or identity rule requires revision."* Committed at `74d4ba3`. `docs/DOCUMENT_CONTRACT.md`'s header records the approved status (`Approved v1.0`, `Contract Version: 1.0`) following Sprint P2.5.1. |
| Independent Review has been accepted | ✅ Satisfied | `docs/DOCUMENT_CONTRACT_REVIEW.md` is committed to `main` at `74d4ba3`; this sprint's own governing brief records its acceptance. |
| No unresolved architectural decisions remain | ✅ Satisfied | Review, "Answer to the Governance Question": **NO** — no additional ADR required before Document Construction Planning. Outstanding Questions 1, 3, and 4 are classified as planning/documentation work, none blocking (Review, Phase 5 deliverable table). |
| Repository architecture has not materially changed since the approved review | ✅ Satisfied | `git log` shows exactly one commit since the review's evidence base was gathered — `74d4ba3`, which adds `docs/DOCUMENT_CONTRACT.md` and `docs/DOCUMENT_CONTRACT_REVIEW.md` and modifies nothing else. `docs/architecture.md`, `docs/roadmap.md`, `docs/MILESTONE_1A.md`, and `docs/glossary.md` are unchanged since `994f7b1`. |

### P0.2 Repository Consistency — Review Finding F1

**This precondition is satisfied.**

`docs/DOCUMENT_CONTRACT.md` has incorporated the accepted Independent Review's findings. Sprint P2.5.1 applied Finding F1 (material) and Findings F4–F8 (accuracy/completeness) directly to that document, and recorded the pass in its own Correction Record section. The Document Contract's schema (Sections 8.2–8.7) was verified byte-for-byte unchanged by that pass; only the analysis sections the review found wrong or stale were corrected.

**No conflicting architectural conclusion regarding F1 remains in the repository.** `docs/DOCUMENT_CONTRACT.md` and `docs/DOCUMENT_CONTRACT_REVIEW.md` now state the same conclusion, on the same evidence:

> **Text extraction is owned by Knowledge Source.** No "Loader" component is warranted, exists, or is introduced. What remains open is the extraction *mechanism* and Knowledge Source's internal decomposition — Construction-planning concerns, not architectural ones.

Supporting evidence, cited identically by both documents:

> `docs/architecture.md` §5 — Knowledge Source · Dependencies: *"JobOps SQLite (read-only), **resume file**"* · Interface: `KnowledgeSource.load() -> List[Document]`
> `docs/architecture.md` §4 — Knowledge stage · Inputs: *"Resume, job descriptions, JobOps SQLite"* → Outputs: *"Validated document set"*
> `docs/architecture.md` §10 (**locked**) — *"**Knowledge ingestion operates on the canonical `.docx` corpus.**"*
> `docs/altm.md` line 149 — Knowledge · Responsible Component (per `architecture.md`): **Knowledge Source**

Where the corrected conclusion now appears in `docs/DOCUMENT_CONTRACT.md`:

| Location | Current state |
|---|---|
| Phase 3, evidence-classification row | States the responsibility is *"already owned by Knowledge Source"*, citing `architecture.md` §5/§4/§10 and `altm.md` line 149 |
| Phase 5 | Restated as *"Undefined extraction mechanism (not undefined ownership)"* |
| Phase 9, Repository Boundaries | Row restated as *"Text extraction (no separate component — owned by Knowledge Source)"* |
| Phase 10, deferred work | Restated as *"Text-extraction mechanism"*, explicitly *"not an ownership question"* |
| Phase 11, Outstanding Question 2 | Marked **ANSWERED. Not an architectural gap.** — retained rather than deleted, with answer, evidence, and governance consequence on the record |
| Construction Readiness Review | Records Question 2 as answered and closed; no architecture-level decision outstanding |

**Planning proceeds using the corrected Document Contract** as its authoritative input. `docs/DOCUMENT_CONTRACT_REVIEW.md` remains the repository's historical record of why the correction was made and the authority under which the contract was approved (Outcome A); it is no longer needed to resolve a live conflict, because none exists.

### P0.3 Additional consistency observations (recorded, non-blocking)

| Observation | Status |
|---|---|
| `docs/DOCUMENT_CONTRACT.md`'s header reads *"Approved v1.0"* / *"Contract Version: 1.0"*, matching the accepted review's Outcome A. | Consistent. Applied at Sprint P2.5.1. |
| Review findings **F4–F8** are applied to `docs/DOCUMENT_CONTRACT.md`. | Consistent. F5's substance (the `docs/CHUNK_CONTRACT.md` §18 sync edits *were* performed at commit `994f7b1`) is also carried in §14 as the expectation that a comparable `Document` sync pass will be required. F8's substance is recorded both in that document's new Section 8.8 and in §11.3 of this plan. |
| Review findings **F2** and **F3** are carried by this plan as §9 and §12 respectively — the review classified them as unrecorded consequences needing an owner, not as corrections to the contract. | Satisfied by this document. |
| Sections 8.3, 8.6, and 8.7 of `docs/DOCUMENT_CONTRACT.md` retain pre-approval phrasing (the word "proposed") because they fall inside the byte-for-byte-unchanged schema range that Sprint P2.5.1 was required not to touch. | Cosmetic only, and disclosed in that document's own Correction Record. No architectural or contractual ambiguity: the header, the Correction Record, and the review all state the approved status. Not a planning input. |

### P0.4 Precondition verdict

**Repository preconditions are satisfied.** Repository consistency has been verified: `docs/DOCUMENT_CONTRACT.md`, `docs/DOCUMENT_CONTRACT_REVIEW.md`, and this plan agree on Finding F1 and on every other accepted finding. Planning proceeds using the corrected Document Contract as its authoritative input, with no supersession, override, or unreconciled deviation in force.

---

## 1. Purpose

Document Construction Planning exists to remove implementation ambiguity from the last unimplemented stage of the Milestone 1A build-time pipeline, without reopening any decision the repository has already settled.

`Document` is the only entity in the repository that has a frozen contract, a declared architectural producer, and a real downstream consumer — but **no construction path at all**. The concrete consequence is verifiable, not theoretical:

- `sample_rag/chunker.py` is implemented and tested, but its only exercised input is `_Document`, a local test fixture in `tests/test_chunker.py` explicitly labelled *"not a production Document Data Model."*
- `scripts/build_chunks.py` implements serialization (`write_chunks`) and validation (`validate_chunks`), yet **`sample_rag/chunks.json` does not exist** — because nothing in the repository can turn `sample_rag/documents/resume/Karthik_SR_Resume_v2_2.docx` into a `Document` to chunk.
- `docs/CHUNK_VALIDATION_PLAN.md` §P1.4 records Chunk invariant 3 as only half-checkable, and §P5 defers `document_id` referential integrity, both for the same reason: no `Document` representation exists.

This plan's purpose is to define — with repository evidence, at planning altitude — how that gap is closed deterministically, so Sprint P3.1 can implement it without rediscovering questions already answered.

---

## 2. Objective

Produce an implementation-ready construction plan that:

1. preserves the approved Document Contract (`docs/DOCUMENT_CONTRACT.md` §8.7) exactly as frozen;
2. preserves repository architecture (`docs/architecture.md` §5's `KnowledgeSource.load() -> List[Document]`, §6's directory boundaries, §10's locked decisions);
3. incorporates accepted review findings F1 (§P0.2), F2 (§9), F3 (§12), and F5/F8 (§14, §11);
4. defines construction responsibilities, workflow, lifecycle, error surface, and determinism requirements;
5. classifies every remaining implementation decision in a Decision Register (§15) so none is resolved by accident during Construction.

The objective is **translation**, not design: every architectural input is already fixed, and this document's job is to make the implementation unambiguous within those fixed bounds.

---

## 3. Scope

### Included

- Construction inputs and outputs (§4)
- Inherited architectural assumptions, restated as binding constraints (§5)
- Implementation-level construction responsibilities and non-responsibilities (§6)
- Construction data flow (§7) and construction lifecycle (§8), documented separately
- Identity strategy evaluation against the approved `Document.id` invariant, without selection (§9)
- Expected failure categories and the repository's established exception pattern (§10)
- Determinism requirements derived from the contract and repository principles (§11)
- Dependency governance and the prerequisite governance process (§12)
- Validation readiness preconditions (§13)
- Repository impact and expected synchronization (§14)
- Decision Register for every deferred implementation decision (§15)
- Implementation inputs (§16) and objective construction-readiness exit criteria (§17)

### Not Included

- Any change to the approved Document Contract's fields, types, invariants, or deferrals
- Any reopening of architectural ownership (settled — §P0.2)
- Any new ADR, architectural concept, component, glossary term, or directory
- Parser selection, dependency selection, or any recommendation of either (§12)
- `.docx` extraction algorithm design
- Implementation code, scaffolding, placeholder classes, or tests
- Document Serialization design (`docs/DOCUMENT_CONTRACT.md` Phase 10 — deferred, and unresolved by design)
- Document Validation design (§13 states its preconditions only)
- `KnowledgeSource`'s JobOps SQLite path — outside `Document` per the contract's own scoping (`docs/DOCUMENT_CONTRACT.md` §8.1, Outstanding Question 3)
- Multi-document corpus generation, retrieval, indexing, CLI orchestration

---

## 4. Inputs / Outputs

### 4.1 Construction Inputs

| Input | Repository location / source | Notes |
|---|---|---|
| Canonical corpus item(s) | `sample_rag/documents/**` — currently exactly one file, `documents/resume/Karthik_SR_Resume_v2_2.docx` | `docs/architecture.md` §10 (locked): *"Resume corpus stored as versioned `.docx` … Knowledge ingestion operates on the canonical `.docx` corpus."* `sample_rag/documents/jobs/` is currently empty. |
| Knowledge Manifest | `sample_rag/knowledge_manifest.json` (`manifest_version`, `documents[].{id,source,hash,indexed}`) | Frozen contract: `docs/MILESTONE_1A.md` build item 1. Owned by Knowledge Source (`docs/architecture.md` §5). Whether it is a *runtime* input of `load()` is the open question evaluated in §9. |
| Approved Document Contract | `docs/DOCUMENT_CONTRACT.md` §8.7 | Two required fields (`id`, `text`), three invariants. The only source of `Document` truth. |
| Supported-extension gate | `scripts/build_manifest.py` `SUPPORTED_EXTENSIONS = {".docx", ".md", ".txt"}`, `DOCUMENTS_ROOT` | Defines which filesystem items are corpus items at all; a corpus item outside this gate has no Manifest entry and therefore cannot satisfy the contract's invariant 1. |

### 4.2 Construction Outputs

| Output | Shape | Notes |
|---|---|---|
| `Document` values | `id: str`, `text: str` | Exactly the two approved fields — no additional field, optional or otherwise (`docs/DOCUMENT_CONTRACT.md` §8.6, §8.7). |
| `KnowledgeSource.load() -> List[Document]` | An ordered list | Signature is fixed by `docs/architecture.md` §5 and is not restated, extended, or narrowed by this plan. List ordering must be deterministic — see §11.2. |
| Construction error surface | One dedicated exception type | See §10. |

### 4.3 Explicit Non-Outputs

- **No persisted `Document` artifact.** Whether `Document` (or its extracted text) is ever serialized is deferred and unresolved (`docs/DOCUMENT_CONTRACT.md` Phase 10, Outstanding Question 4). Construction produces in-memory values only, mirroring how `sample_rag/chunker.py` produced in-memory `Chunk`s at P2.2 with persistence arriving only at P2.3.
- **No `chunks.json`.** Producing it requires wiring Construction to `Chunker` and `scripts/build_chunks.py` — orchestration, deferred (§14, §15).
- **No manifest generation or mutation.** `scripts/build_manifest.py` owns that lifecycle; `documents[].indexed` is not flipped by Document Construction.

---

## 5. Construction Assumptions

These are **inherited constraints**, already established by approved repository artifacts. Sprint P3.1 must build within them; it must not re-derive, re-litigate, or silently relax any of them.

| # | Inherited constraint | Source |
|---|---|---|
| A1 | The Knowledge Manifest exists, is frozen, is implemented, and is the corpus catalog. | `docs/MILESTONE_1A.md` build item 1; `scripts/build_manifest.py`; `sample_rag/knowledge_manifest.json` |
| A2 | The Document Contract is approved: required fields are exactly `id: str` and `text: str`; there are no optional fields; every candidate field in §8.6 is deferred, not silently includable. | `docs/DOCUMENT_CONTRACT.md` §8.7; `docs/DOCUMENT_CONTRACT_REVIEW.md` Outcome A |
| A3 | **Knowledge Source owns Document construction, including text extraction.** No new component may be introduced for it. | `docs/architecture.md` §5 (interface + "resume file" dependency), §4, §10 (locked ingestion decision); `docs/altm.md` line 149; `docs/DOCUMENT_CONTRACT.md` Phase 9 and Phase 11 Q2 (as corrected at Sprint P2.5.1); `docs/DOCUMENT_CONTRACT_REVIEW.md` F1 |
| A4 | The resume corpus is canonical as versioned `.docx`; PDF is an external export artifact outside the pipeline. | `docs/architecture.md` §10 (locked) |
| A5 | `Document.id` **must equal** the corresponding `knowledge_manifest.json` `documents[].id`. It is not independently derived, and no second identity scheme may be introduced. | `docs/DOCUMENT_CONTRACT.md` §8.4, invariant 1 |
| A6 | Construction must be deterministic: identical source content extracted by an identical mechanism yields identical `text`. | `docs/DOCUMENT_CONTRACT.md` §8.7 invariant 3; `docs/architecture.md` §2 ("Deterministic before probabilistic") |
| A7 | `text` may be empty. An empty `Document` is legal and produces zero chunks. | `docs/DOCUMENT_CONTRACT.md` §8.3 ("Non-empty guarantee" — deliberately not required), invariant 2; `docs/CHUNK_CONTRACT.md` §11 |
| A8 | Referential integrity (`Document.id` ↔ Manifest entry) is **not** part of the structural contract; it belongs to the Data Quality Validation pytest layer. | `docs/DOCUMENT_CONTRACT.md` §8.5; `docs/CHUNK_VALIDATION_PLAN.md` §P5; `docs/MILESTONE_1A.md` build item 2 |
| A9 | The interface is `KnowledgeSource.load() -> List[Document]`, unchanged. | `docs/architecture.md` §5 |
| A10 | `sample_rag/` holds pipeline logic; `scripts/` is explicitly *"not pipeline logic."* | `docs/architecture.md` §6 |
| A11 | Milestone 1A is stdlib + pytest; new dependencies require a recorded scope decision. | `docs/roadmap.md` §6, §7; `docs/architecture.md` §10; `docs/CHUNK_BUILDER_IMPLEMENTATION_PLAN.md` §1.4 |
| A12 | `Document` has no parent entity; the Manifest entry is a sibling artifact, and `Document` → `Chunk` is one-to-many. | `docs/DOCUMENT_CONTRACT.md` §8.5 |

---

## 6. Construction Responsibilities

Implementation responsibilities only. Architectural ownership (A3) is inherited, not redefined.

### 6.1 Responsibilities

| # | Responsibility | Constraint it satisfies |
|---|---|---|
| R1 | **Corpus item resolution** — determine which corpus items exist and are eligible to become `Document` values. | A1, A4; `scripts/build_manifest.py`'s `DOCUMENTS_ROOT`/`SUPPORTED_EXTENSIONS` gate |
| R2 | **Identity resolution** — obtain, for each corpus item, the `id` that equals its Manifest `documents[].id`. | A5; strategy evaluated but not selected in §9 |
| R3 | **Text extraction** — produce a single deterministic plain-text `str` for each corpus item. | A3, A6; mechanism deferred (§12, §15) |
| R4 | **Document assembly** — construct the two-field value, and nothing more. | A2 |
| R5 | **Ordered emission** — return a `List[Document]` whose order is deterministic across runs. | A9, A6; see §11.2 |
| R6 | **Failure surfacing** — raise a defined construction error rather than returning a malformed or partially-constructed `Document`, or leaking an unrelated internal exception. | §10; precedent `sample_rag/chunker.py` `ChunkConstructionError` |

### 6.2 Explicit Non-Responsibilities

Construction must **not**:

- **Chunk.** `Chunker.chunk(doc)` (`sample_rag/chunker.py`) is a separate, already-implemented component.
- **Serialize.** No `Document` persistence exists or is designed (§4.3).
- **Validate as a component.** Structural Document Validation is a later sprint (§13), mirroring how `docs/CHUNK_CONTRACT.md` deferred Chunk Validation to P2.4. A defensive construction-time self-check is permitted (§8, stage 5) exactly as `chunker.py`'s `_check_invariants()` is permitted — and, like it, is **not** a substitute for that later component.
- **Check referential integrity.** A8. Note the nuance in §9: one identity strategy produces referential consistency as a *byproduct*; that byproduct must not be presented, documented, or relied upon as the deferred validation check.
- **Generate, mutate, or repair the Knowledge Manifest.** `scripts/build_manifest.py` owns that lifecycle, including `documents[].indexed`.
- **Model JobOps SQLite data as a `Document`.** `docs/DOCUMENT_CONTRACT.md` §8.1 scopes `Document` to text corpus items; a SQLite row cannot obtain a Manifest entry under `scripts/build_manifest.py`'s discovery gate and therefore cannot satisfy A5 (`docs/DOCUMENT_CONTRACT_REVIEW.md` F7).
- **Introduce a second identity scheme**, a `source`/`hash`/`document_type`/`metadata`/`character_count` field, or any optional-field tier. A2, A5.
- **Import any embedding, vector-store, or LLM-evaluation library.** `docs/MILESTONE_1A.md` Architectural Acceptance Criteria — a blanket M1A constraint applying to every component.

---

## 7. Construction Workflow

**Data flow.** What moves, and in what shape. (Engineering progression is documented separately in §8.)

```text
sample_rag/documents/**            sample_rag/knowledge_manifest.json
  (canonical .docx corpus item)      (documents[].id, .source)
            │                                    │
            │                                    │
            ▼                                    ▼
   ┌─────────────────────┐              ┌─────────────────────┐
   │  Text extraction    │              │ Identity resolution │
   │  (deterministic)    │              │   (§9 — deferred)   │
   └─────────────────────┘              └─────────────────────┘
            │                                    │
            │  text: str                         │  id: str
            └──────────────┬─────────────────────┘
                           ▼
                  ┌─────────────────┐
                  │    Document     │   id: str, text: str
                  │  (two fields)   │
                  └─────────────────┘
                           │
                           ▼
                  List[Document]  ── deterministic order (§11.2)
                           │
                           ▼
             KnowledgeSource.load() returns
                           │
                           ▼
              Chunker.chunk(doc) -> List[Chunk]     (existing consumer,
                                                     unchanged)
```

Notes on the flow, all evidence-bound:

- The two upstream arms are **independent**: extraction depends only on the corpus item's content; identity depends only on the item's normalized source path (directly, or via the Manifest). This independence is what makes §9's strategies interchangeable without touching R3.
- The dashed relationship `Document` → Manifest entry is **one-to-one via `id`** (`docs/DOCUMENT_CONTRACT.md` §8.5), and `Document` → `Chunk` is **one-to-many**.
- Nothing flows back. Construction writes nothing and mutates nothing (§6.2).

---

## 8. Construction Lifecycle

**Engineering progression.** The order in which construction work becomes valid — distinct from §7's data movement.

```text
Inputs Ready
   │   corpus item present under sample_rag/documents/**;
   │   knowledge_manifest.json present and structurally valid;
   │   extraction capability available (§12 governance satisfied)
   ▼
Construction Begins
   │   1. input admissibility check  → raises on malformed input (§10.1)
   │   2. corpus item resolution (R1)
   │   3. identity resolution (R2)
   │   4. text extraction (R3)
   ▼
Document Produced
   │   5. assembly (R4) + optional defensive self-check against
   │      DOCUMENT_CONTRACT §8.7 invariants 1–2
   ▼
Construction Complete
   │   6. deterministic ordered emission (R5)
   │   ordered List[Document] returned; no artifact written
   ▼
Ready for Validation
       preconditions in §13 satisfied
```

**Stage-boundary discipline (inherited precedent).** `scripts/build_manifest.py` keeps `assemble_manifest` (pure) separate from `write_manifest`/`load_manifest` (I/O) and from `validate_manifest` (checking), *even though one could call another*. `docs/CHUNK_BUILDER_IMPLEMENTATION_PLAN.md` §3.7 adopted the same split for `Chunker`. Document Construction should preserve it: the pure assembly step (stage 5) must remain separable from the I/O-bearing steps (stages 2–4), so that a `Document` can be constructed in a test from an already-extracted string without touching the filesystem.

**Departure from the `Chunker` precedent, stated explicitly.** `Chunker.chunk()` is a pure function with no I/O (`docs/CHUNK_BUILDER_IMPLEMENTATION_PLAN.md` §3.7, §4.5). `KnowledgeSource.load()` **cannot** be — its declared dependency is a file (`docs/architecture.md` §5). This is not a deviation from repository convention; it is the reason `build_manifest.py`'s pure/I/O split exists and is the closer precedent for this component.

---

## 9. Identity Strategy (Review Finding F2)

**The invariant to preserve (A5, not reopened):** `Document.id` is a `str` equal to the corresponding `knowledge_manifest.json` `documents[].id` — *"not derived independently"*, and *"this contract does not introduce a second, competing identity scheme"* (`docs/DOCUMENT_CONTRACT.md` §8.4).

**Why this needs a recorded evaluation.** The Manifest's ids are produced by `generate_document_id(source) = sha256(normalized_source_path)[:12]` in **`scripts/build_manifest.py:74-76`** — a module that `docs/architecture.md` §6 defines as *"not pipeline logic."* Any `Document` producer living in `sample_rag/` must therefore obtain that value across a directory boundary the repository has drawn deliberately. `docs/DOCUMENT_CONTRACT_REVIEW.md` F2 recorded this consequence; no phase of the contract does. It is a **planning-level** decision, not an architectural one, and the repository has resolved a directly analogous coupling question inside a planning sprint before (`docs/CHUNK_VALIDATION_PLAN.md` §P5.3, which declined a cross-script dependency as *"new coupling that this sprint's evidence does not yet require introducing"*).

### 9.1 Strategies

| | **S1 — Read the Manifest artifact** | **S2 — Reuse the derivation function** | **S3 — Re-implement the derivation** |
|---|---|---|---|
| Mechanism | `load_manifest()` (+ optionally `validate_manifest()`), then take `documents[].id` and `.source` as the corpus enumeration | `from scripts.build_manifest import generate_document_id`, applied to the normalized source path | A local copy of the same SHA-256/truncation logic inside `sample_rag/` |
| `sample_rag/` → `scripts/` import | None | **Yes** | None |
| Source of corpus enumeration | The Manifest | The filesystem (`discover_documents`-equivalent logic) | The filesystem |
| Drift risk if the id algorithm changes | None — ids are read, never recomputed | None — one implementation | **High** — two implementations must be changed together, with nothing enforcing it |
| Runtime coupling to a persisted artifact | **Yes** — `load()` fails if `knowledge_manifest.json` is missing or stale | No | No |
| Behaviour when the corpus and the Manifest disagree | A file present on disk but absent from the Manifest is simply not loaded (silent narrowing) | The file is loaded and receives a well-formed id with no Manifest entry (silent widening) | Same as S2 |
| Relationship to A8 (deferred referential integrity) | Produces referential consistency **as a byproduct** — must not be documented or relied upon as the deferred check | Neutral | Neutral |
| Repository precedent | `validate_chunks(load_chunks())` chaining; Manifest is already the *"single canonical description of what the corpus is"* (`docs/MILESTONE_1A.md` build item 1) | No precedent for a `sample_rag/` → `scripts/` import anywhere in the repository | Repository has no duplicated-logic precedent; `docs/CHUNK_CONTRACT.md` §14.2 rejected duplication for the analogous case |
| Tension with `docs/architecture.md` §6 | None | **Direct** — imports pipeline behaviour from a directory defined as not pipeline logic | None |

### 9.2 Cross-cutting observations

- **All three satisfy the contract.** Invariant 1 constrains the *value*, not the derivation path. This is why §9 is an evaluation, not an architectural question — a point `docs/DOCUMENT_CONTRACT_REVIEW.md` F2 makes explicitly.
- **S1 and S2/S3 differ in what "the corpus" means at runtime** — the Manifest under S1, the filesystem under S2/S3. `docs/MILESTONE_1A.md` build item 1 calls the Manifest *"the single canonical description of what the corpus is,"* and `docs/MILESTONE_1A.md` Architectural Acceptance Criteria require it to be *"the sole source of truth that freshness/hash validation checks against."* That evidence bears on the choice but does not settle it, because those statements are scoped to corpus description and freshness validation, not to `load()`'s enumeration path.
- **Silent-narrowing vs. silent-widening (§9.1, row 7) is the sharpest practical difference** and should drive P3.1's decision more than import aesthetics: each mode fails differently when corpus and Manifest drift, and P3.1 must state which failure mode it is choosing and whether it surfaces (§10.1) rather than passes silently.
- **A fourth option — changing where `generate_document_id` lives — is out of scope.** Moving it would edit `scripts/build_manifest.py`, a shipped implementation whose Manifest lifecycle is frozen and validated (P1.2.0–P1.3). Nothing in this sprint's evidence requires it.

### 9.3 Disposition

**No strategy is selected.** Selection belongs to Sprint P3.1 (Construction), which must record its choice, its rationale, and the drift/failure mode it accepts. Registered in §15.

---

## 10. Error Handling

No implementation is required here. This section defines the expected failure surface and inherits the repository's established exception pattern.

### 10.1 Failure categories

| Category | Example conditions | Expected disposition |
|---|---|---|
| **Input failures** | Corpus item missing or unreadable; unsupported extension; `knowledge_manifest.json` missing, unparseable, or structurally invalid (S1 only, §9); no Manifest entry for a discovered corpus item (S2/S3, §9) | Raise. These are I/O and admissibility errors — a legitimate error surface here, unlike `Chunker`, which has none because it performs no I/O (`docs/CHUNK_BUILDER_IMPLEMENTATION_PLAN.md` §4.5) |
| **Construction failures** | Extraction yields a non-`str`; identity resolution yields a non-`str` or no value; a corpus item resolves to more than one candidate id | Raise. Never return a partially-constructed or type-violating `Document` |
| **Contract-conformance failures** | A constructed value violates `docs/DOCUMENT_CONTRACT.md` §8.7 invariant 1 or 2 | Raise, if a defensive self-check is implemented (§8, stage 5). Precedent: `sample_rag/chunker.py` `_check_invariants()` aborts construction rather than returning a non-conforming result |
| **Determinism failures** | Two runs over identical source content produce different `text` or different list ordering | **Not** a runtime raise. Determinism is a property of *repeated* execution and is checkable only by two-run comparison — a test/CI concern, exactly as `docs/CHUNK_VALIDATION_PLAN.md` §P1.4 and §P8 concluded for Chunk invariant 8 (§11.3) |
| **Validation failures** | Structural validation of a `Document` against the contract, performed independently of construction | Out of scope for Construction — a later sprint's responsibility (§13) |

**Explicitly not an error:** an empty `text` (A7). It is a legal `Document` that legally produces zero chunks.

### 10.2 Exception pattern (inherited, not decided here)

The repository's established pattern is **flat, independent exception types — one per responsibility, each a direct `Exception` subclass, with no shared base class**:

| Exception | Module |
|---|---|
| `ManifestValidationError` | `scripts/build_manifest.py` |
| `ChunkConstructionError` | `sample_rag/chunker.py` |
| `ChunkSerializationError` | `scripts/build_chunks.py` |
| `ChunkValidationError` | `scripts/build_chunks.py` |

`docs/CHUNK_VALIDATION_PLAN.md` §P6.2 examined and confirmed this pattern deliberately, declining to invent a shared hierarchy. Document Construction should follow it: **one new, dedicated, direct `Exception` subclass, scoped to construction**, raised **fail-fast** on the first violation (matching `validate_manifest`, `_check_invariants`, and `validate_chunks` alike). The concrete type name is an allowed implementation decision (§15), as `docs/CHUNK_BUILDER_IMPLEMENTATION_PLAN.md` §1.3 treated it for `Chunker`.

---

## 11. Determinism Requirements

### 11.1 The contract requirement (inherited)

> *"Identical source content, extracted by an identical mechanism, produces an identical `text` value."* — `docs/DOCUMENT_CONTRACT.md` §8.7 invariant 3

Practical construction consequences:

- No wall-clock, timestamp, or elapsed-time dependence. Direct precedent: the Knowledge Manifest **removed** `created_at` specifically because it broke determinism (`docs/MILESTONE_1A.md` build item 1, "Contract Change").
- No dependence on OS-dependent iteration order. Direct precedent: `scripts/build_manifest.py` `main()` wraps `discover_documents`' `rglob` output in `sorted(...)` for exactly this reason.
- No dependence on locale, environment, randomness, or machine-specific state.
- Text normalization (whitespace, line endings, paragraph joining) must be a fixed, total function of the source content — not conditional on anything outside it.

### 11.2 Derived requirement — deterministic list ordering

`KnowledgeSource.load()` returns a `List[Document]` (A9). The Document Contract is scoped to a single `Document` and states no collection-level ordering invariant — so this is a **construction-level requirement derived from repository principle, explicitly not a contract term** and not an amendment to §8.7:

- `docs/architecture.md` §2: *"Deterministic before probabilistic."*
- `scripts/build_manifest.py` `main()`: `sorted(normalize_source_path(...) for ...)` — the repository's existing answer to this exact class of non-determinism.
- `docs/CHUNK_CONTRACT.md` §7 required *"an identical ordered list of `Chunk`s"* for the analogous collection.

**Non-binding recommendation** (in the style of `docs/CHUNK_BUILDER_IMPLEMENTATION_PLAN.md` §3.4): order by normalized source path, ascending, following `build_manifest.py`'s precedent — or, under strategy S1 (§9), by the Manifest's own `documents[]` order, which is already deterministic because it was produced by that same `sorted(...)`. P3.1 may choose either with justification; it may not leave ordering to filesystem iteration order.

### 11.3 What determinism does *not* give, recorded (Review Finding F8)

- Invariant 3 is **mechanism-relative**. A change of extraction mechanism may legitimately change `text` for unchanged source content. This matches, and does not weaken, the analogous scoping already accepted for Chunk (`docs/CHUNK_CONTRACT.md` §10, §17 invariant 8).
- It is **not checkable from a single artifact**. Verification requires a two-run comparison — a test/CI strategy, matching `docs/CHUNK_VALIDATION_PLAN.md` §P1.4/§P8 and `docs/CHUNK_SERIALIZATION_PLAN.md` §P5.
- `documents[].hash` is a SHA-256 of the **source file's bytes** (`scripts/build_manifest.py` `compute_sha256`), not of extracted text. Existing freshness checking therefore cannot detect extracted-text drift caused by a mechanism change. This is **recorded, not resolved** — it is a Data Quality Validation concern (`docs/MILESTONE_1A.md` build item 2), registered in §15.

---

## 12. Dependency Governance (Review Finding F3)

**This section names no parser, library, module, or approach, and expresses no preference among them.** It documents the governance that must be satisfied before Sprint P3.1 may resolve the extraction mechanism at all.

### 12.1 Repository dependency governance (current state, verified)

| Rule | Source |
|---|---|
| *"**Minimal dependencies.** Milestone 1A is Python stdlib + pytest only. Dependencies are added only when a milestone specifically requires them."* | `docs/roadmap.md` §6 (locked principle) |
| *"Deferred intentionally, not forgotten — do not add these without a deliberate scope decision **recorded in this document**."* | `docs/roadmap.md` §7 (Scope Freeze) |
| *"Minimal dependencies — Milestone 1A must be provable without external services or paid APIs."* | `docs/architecture.md` §10 (locked) |
| Libraries table is stdlib-only (`pytest`, `abc`/`typing.Protocol`, `sqlite3`, `hashlib`, `argparse`, `logging`, `dataclasses`); *"No embedding library, vector store, LLM SDK, or evaluation-tool dependency is **imported** anywhere in the M1A codebase."* | `docs/MILESTONE_1A.md` |
| Prohibited for a construction sprint: *"Add a new external dependency without a recorded scope decision (`docs/roadmap.md` §6)."* | `docs/CHUNK_BUILDER_IMPLEMENTATION_PLAN.md` §1.4 |

**Verified factual nuance.** `requirements.txt` already declares `pytest`, `deepeval`, `promptfoo`, `ragas`, `pandas`, `python-dotenv`. Repository scan confirms none of the non-`pytest` entries is imported by any module. The binding M1A constraint is therefore on **imports in Milestone 1A code**, while `requirements.txt` carries forward-looking declarations. P3.1 must not read the presence of unused declarations as precedent for adding an imported dependency.

### 12.2 Why this is the trigger point

Text extraction is the first Milestone 1A capability that **may** require something outside the stdlib. It is genuinely open in both directions: the stdlib is capable of reading the container formats named in `SUPPORTED_EXTENSIONS`, and external options exist. This plan takes no position on which branch is correct — that determination is precisely what governance exists to make, on the record.

### 12.3 Prerequisite governance process

Before Sprint P3.1 may import any non-stdlib module for extraction:

1. **Determine whether a non-stdlib dependency is required at all.** If extraction is achieved with the stdlib, no scope decision is triggered and §12 imposes no further step.
2. **If one is required, record a Dependency Governance Decision in `docs/roadmap.md` §7** — the venue `docs/roadmap.md` §7 itself designates (*"a deliberate scope decision recorded in this document"*). Not an ADR: `docs/adr/ADR-0001` established that ADRs are reserved for architectural-boundary questions, and dependency selection is neither an architectural boundary nor a responsibility question (`docs/DOCUMENT_CONTRACT_REVIEW.md`, Outcome-B constraints).
3. **Update `requirements.txt` and `docs/MILESTONE_1A.md`'s Libraries table** only after (2), so the "stdlib-only" statement never becomes silently false.
4. **Construction may then proceed** against the recorded decision.

### 12.4 Dependency evaluation expectations (criteria only — no candidates, no scoring)

Any future Dependency Governance Decision should evaluate at least:

- **Determinism** — does the mechanism produce byte-identical text for identical input across runs, machines, and versions (A6)?
- **Necessity** — is the capability genuinely unavailable from the stdlib for the formats in `SUPPORTED_EXTENSIONS`?
- **Scope conformance** — does it stay inside `docs/roadmap.md` §7's Scope Freeze and `docs/architecture.md` §11's Out of Scope list, and outside the embedding/vector-store/LLM-evaluation classes M1A bars from import?
- **Testability** — can extraction be exercised without network access or external services (`docs/MILESTONE_1A.md` Functional Acceptance Criteria)?
- **Reversibility** — how coupled would the pipeline become, and how contained is a later swap?
- **Maintenance and licensing** — ordinary supply-chain diligence.

### 12.5 Relationship to the future Dependency Governance Decision

This plan is **implementation-neutral by construction**: nothing in §4–§11 or §13–§17 presumes either branch. §9's identity strategies, §10's error categories, §11's determinism requirements, and §13's validation preconditions all hold unchanged whichever way the mechanism question is settled. Registered in §15.

---

## 13. Validation Readiness

Document Validation is **not designed here** (§3). This section states only what must be true before it can begin — mirroring how `docs/CHUNK_CONTRACT.md` §19 stated P2.4's preconditions without designing P2.4.

### 13.1 Preconditions

| # | Precondition | Why |
|---|---|---|
| V1 | Document Construction (P3.1) is implemented and produces conforming `Document` values from the real corpus. | Validation checks produced artifacts; `docs/CHUNK_VALIDATION_PLAN.md` was written only after Construction and Serialization existed |
| V2 | The **persistence question is settled** — is `Document` ever serialized (as `chunks.json` is), or does it remain a build-time, in-memory value? | `docs/CHUNK_VALIDATION_PLAN.md` validates a *persisted* collection. `docs/DOCUMENT_CONTRACT.md` Phase 10 and Outstanding Question 4 leave this open. Validation's entire shape — what it consumes — depends on the answer |
| V3 | The identity strategy (§9) is chosen and recorded. | Determines whether the Manifest is already a runtime input, which bears on where the deferred referential-integrity check can cheaply live |
| V4 | The determinism verification approach (§11.3) is decided as a test/CI strategy. | It is not a single-artifact check and cannot be folded into a structural validator |

### 13.2 Checkability of the approved invariants (recorded, so a later sprint need not rediscover it)

| Contract §8.7 invariant | Checkable by a structural Document validator? |
|---|---|
| 1 — `id` is a `str` **and equals** the Manifest `documents[].id` | **Partially.** The type half is structural. The equality half is cross-artifact/semantic and is deferred by A8 to the Data Quality Validation pytest layer — the same disposition and the same home `docs/CHUNK_VALIDATION_PLAN.md` §P5 chose for `Chunk.document_id` |
| 2 — `text` is a `str` (may be empty) | **Yes** — a plain field/type check, directly analogous to `validate_manifest`'s per-field checks |
| 3 — determinism | **No** — a property of repeated construction, not of one value (§11.3) |

### 13.3 What this plan unblocks downstream

Once Construction exists, two long-standing deferrals become resolvable — neither by this plan, and neither by P3.1:

- `docs/CHUNK_VALIDATION_PLAN.md` §P1.4 — Chunk invariant 3 (`text == document_text[character_start:character_end]`) becomes fully checkable, since a `Document` representation to check against will exist.
- `docs/CHUNK_CONTRACT.md` §11 / `docs/CHUNK_VALIDATION_PLAN.md` §P5 — `Chunk.document_id` referential integrity gains a defined join key contract on both sides.

---

## 14. Repository Impact

### 14.1 Affected components

| Component | Impact |
|---|---|
| **Knowledge Source** | Receives its first implementation. Its interface (`docs/architecture.md` §5) is unchanged. Its ownership of text extraction is inherited, not newly assigned (A3, §P0.2) |
| **Chunker** (`sample_rag/chunker.py`) | Unmodified, but gains a real input for the first time. Today its only exercised input is `tests/test_chunker.py`'s local `_Document` fixture. Its duck-typed `_validate_document` (checks `.id: str`, `.text: str`) is exactly satisfied by the approved contract — no change required or permitted |
| **Chunk Serialization / Validation** (`scripts/build_chunks.py`) | Unmodified. `sample_rag/chunks.json` **does not currently exist**; producing it becomes possible for the first time, but requires orchestration that is out of this sprint's scope (§15) |
| **Knowledge Manifest** (`scripts/build_manifest.py`, `sample_rag/knowledge_manifest.json`) | Unmodified. Becomes either a runtime input or the identity source, depending on §9's outcome. `documents[].indexed` remains owned by the Manifest lifecycle, not flipped by Construction |
| **Data Quality Validation layer** (`docs/MILESTONE_1A.md` build item 2) | Not built by this work, but two deferred checks become implementable (§13.3) |
| **CLI** (`docs/MILESTONE_1A.md` build item 6) | Unaffected here. End-to-end `Knowledge → Indexer → …` wiring remains a later build item |

### 14.2 Expected repository synchronization

Repository precedent for a post-freeze synchronization pass is commit `994f7b1` ("docs: synchronize repository with frozen Chunk Contract"), which added cross-references to `docs/MILESTONE_1A.md`, `docs/architecture.md`, and `docs/glossary.md`. A comparable pass applies to `Document`.

**Completed:**

- **`docs/DOCUMENT_CONTRACT.md` — accepted review corrections F1 and F4–F8 applied, and header status updated to `Approved v1.0` / `Contract Version: 1.0`.** Performed at Sprint P2.5.1, with the pass recorded in that document's own Correction Record and its schema (§8.2–§8.7) verified byte-for-byte unchanged. The repository no longer carries two answers on F1 (§P0.2).

**Remaining:**

1. **`docs/glossary.md` §3** — a `Document Contract` entry, alongside the existing `Chunk Contract` entry, per the glossary's own rule that terms are *"added here first, then referenced"* (§10).
2. **`docs/architecture.md` §5, Knowledge Source row** — a one-line pointer to `docs/DOCUMENT_CONTRACT.md`, matching the existing `**Chunk.**` and `**Knowledge Manifest.**` pointer pattern. A pointer is not a decision change, so `docs/architecture.md` §13's stability rule is respected.
3. **`docs/MILESTONE_1A.md`** — a "Contract status" pointer under the Knowledge build item, mirroring build item 3's existing Chunk pointer.
4. **`docs/roadmap.md` §7** — only if §12.3 step 2 is triggered.

None of the remaining edits is performed by this document, and none blocks Sprint P3.1: each is a cross-reference pointer, not a decision.

### 14.3 Implementation implications

- **Module placement.** `docs/architecture.md` §6 designates `sample_rag/` for pipeline components and `scripts/` as *"not pipeline logic"*; `docs/CHUNK_BUILDER_IMPLEMENTATION_PLAN.md` §2.1 applied that reasoning to place `sample_rag/chunker.py`. The same reasoning applies to Knowledge Source. Concrete placement and file naming remain P3.1's decision (§15).
- **Import root is already solved.** `conftest.py` inserts the repository root into `sys.path`; `tests/test_chunker.py` already imports `sample_rag.chunker` successfully. No new test-infrastructure work is implied.
- **Corpus scale.** The corpus is one `.docx`; `sample_rag/documents/jobs/` is empty. Construction against the current corpus yields exactly one `Document`. `docs/MILESTONE_1A.md` Functional Acceptance Criterion 1 requires chunking *"the resume and at least one job description"* — so corpus expansion is a separate prerequisite for that criterion, not for Construction itself. It is also the evidence trigger for revisiting `document_type` (`docs/DOCUMENT_CONTRACT.md` Outstanding Question 1).

---

## 15. Deferred Decisions — Decision Register

Every implementation decision this plan deliberately does not make. Nothing below may be resolved implicitly during Construction; each requires an explicit, recorded choice at its stated venue.

| Decision | Deferred To | Reason |
|---|---|---|
| Parser / extraction dependency selection | Dependency Governance Decision (`docs/roadmap.md` §7) | First candidate external dependency in Milestone 1A; governed by `docs/roadmap.md` §6–§7 and out of this plan's scope by instruction (§12) |
| Whether a non-stdlib dependency is required at all | Sprint P3.1, gated by §12.3 step 1 | Both branches remain open; determining it is the trigger, not the outcome, of governance |
| Extraction mechanism and text-normalization rules | Sprint P3.1 (Construction) | Architectural ownership already established (A3); mechanism is an implementation concern, bounded by A6 |
| Identity strategy S1 / S2 / S3 | Sprint P3.1 (Construction) | All three satisfy invariant 1; the trade-off is coupling and drift/failure mode, not contract conformance (§9, Review F2) |
| Corpus-and-Manifest disagreement behaviour (silent narrowing vs. widening vs. raise) | Sprint P3.1 (Construction) | Follows directly from the identity strategy; must be stated, not inherited by accident (§9.2, §10.1) |
| Module organisation, file location, and naming | Sprint P3.1 (Construction) | Implementation concern; `docs/architecture.md` §6 and `docs/CHUNK_BUILDER_IMPLEMENTATION_PLAN.md` §2.1 supply the reasoning method (§14.3) |
| Construction exception type name | Sprint P3.1 (Construction) | Pattern is inherited and fixed (§10.2); the name is an allowed decision, as it was for `ChunkConstructionError` |
| `List[Document]` ordering key | Sprint P3.1 (Construction) | Determinism is required (§11.2); the concrete key is a bounded implementation choice with a stated recommendation |
| Whether a defensive construction-time self-check is implemented | Sprint P3.1 (Construction) | Permitted and precedented (`chunker.py` `_check_invariants()`), not mandated; never a substitute for Document Validation |
| Document persistence / serialization | Future Document Serialization sprint | Unresolved by the approved contract (`docs/DOCUMENT_CONTRACT.md` Phase 10, Outstanding Question 4); blocks Validation's shape (V2) |
| Document Validation design | Future Document Validation sprint | Preconditions only are stated here (§13); mirrors Chunk's Contract → Construction → Serialization → Validation sequencing |
| `Document.id` ↔ Manifest referential-integrity check | Data Quality Validation pytest layer (`docs/MILESTONE_1A.md` build item 2) | Deferred by the approved contract itself (A8, §8.5) and by `docs/CHUNK_VALIDATION_PLAN.md` §P5 for the analogous Chunk check |
| Extracted-text drift detection (Manifest `hash` covers source bytes only) | Data Quality Validation layer / future milestone | Recorded by Review F8 (§11.3); no repository evidence yet establishes a need |
| Determinism verification strategy (two-run comparison) | Future test/CI design | Not a single-artifact check (§11.3); same disposition as `docs/CHUNK_SERIALIZATION_PLAN.md` §P5 and `docs/CHUNK_VALIDATION_PLAN.md` §P8 |
| Build orchestration / CLI wiring (Document → Chunker → `chunks.json`) | `docs/MILESTONE_1A.md` build item 6 | Out of scope; already recorded as a forward dependency by `docs/CHUNK_VALIDATION_PLAN.md` §P8 |
| `document_type` / `source` field promotion | Revisit at corpus expansion | Deferred by the approved contract (§8.6, Outstanding Question 1) pending a real job-description document; `sample_rag/documents/jobs/` is empty |
| JobOps-as-`Document` classification | Future milestone / documentation clarification | Outstanding Question 3; structurally excluded today by the Manifest discovery gate (Review F7) |
| Performance / optimisation of extraction | Future milestone | No supporting evidence; `docs/MILESTONE_1A.md` Out of Scope explicitly bars *"Performance optimization of any kind"* |

---

## 16. Implementation Inputs

Sprint P3.1 shall consume exactly these artifacts. Anything not listed is not an input to Construction.

| Input | Role |
|---|---|
| `docs/DOCUMENT_CONTRACT.md` (approved v1.0, corrected at Sprint P2.5.1) | The authoritative and only source of `Document` field/invariant truth — §8.2, §8.3, §8.4, §8.5, §8.6, §8.7, plus §8.8's recorded determinism limits. Read directly; it now incorporates every accepted review finding |
| `docs/DOCUMENT_CONTRACT_REVIEW.md` (accepted) | Historical record: the approval authority (Outcome A) and the reasoning behind findings F1 and F4–F8. Also the originating text for F2 (§9) and F3 (§12), which it assigned to Construction Planning rather than to the contract |
| `docs/DOCUMENT_CONSTRUCTION_PLAN.md` (this document) | Construction boundaries, responsibilities, workflow, lifecycle, error surface, determinism, governance, Decision Register |
| `sample_rag/knowledge_manifest.json` + `docs/MILESTONE_1A.md` build item 1 | The corpus catalog and its frozen contract; the source of `Document.id` |
| `docs/architecture.md` | §2 principles, §5 component/interface, §6 directory boundaries, §10 locked decisions |
| `docs/roadmap.md` | §6 dependency principles, §7 Scope Freeze — the governance venue for §12.3 |
| `docs/MILESTONE_1A.md` | Libraries table, Acceptance Criteria, Out of Scope, build items 1–3 and 6 |
| `docs/CHUNK_BUILDER_IMPLEMENTATION_PLAN.md` | Reference Construction-planning precedent — boundaries, discovery, interface planning, readiness-review structure |
| `scripts/build_manifest.py` | Reference implementation for a deterministic artifact builder: pure/I-O separation, `sorted(...)` determinism, flat exception type, `generate_document_id` (§9) |
| `sample_rag/chunker.py`, `tests/test_chunker.py` | The downstream consumer's actual expectations of a `Document`, and the existing unit-test style |

---

## 17. Construction Readiness Checklist

Objective exit criteria for this planning sprint.

**Preconditions**
- [x] Repository state preconditions verified — §P0.1
- [x] Repository consistency explicitly verified against Review Finding F1 — §P0.2
- [x] F1 reconciled in the repository itself: `docs/DOCUMENT_CONTRACT.md` incorporates the accepted findings, and no conflicting architectural conclusion remains — §P0.2
- [x] Additional consistency observations recorded, all currently true — §P0.3

**Planning content**
- [x] Purpose, objective, and scope (included / not included) defined — §1, §2, §3
- [x] Construction inputs, outputs, and explicit non-outputs documented — §4
- [x] Inherited architectural assumptions enumerated as binding constraints (A1–A12) — §5
- [x] Construction responsibilities and non-responsibilities defined at implementation level only — §6
- [x] Construction workflow (data flow) documented — §7
- [x] Construction lifecycle (engineering progression) documented **separately** from data flow — §8
- [x] Identity strategy evaluated with trade-offs, **no strategy selected** (Review F2) — §9
- [x] Failure categories and inherited exception pattern documented — §10
- [x] Determinism requirements documented, including the derived list-ordering requirement and its recorded limits (Review F8) — §11
- [x] Dependency governance documented independently of implementation, **no parser or dependency named or recommended** (Review F3) — §12
- [x] Validation readiness preconditions and invariant checkability recorded — §13
- [x] Repository impact, synchronization expectations, and implementation implications documented — §14
- [x] Every deferred implementation decision classified in a Decision Register — §15
- [x] Implementation inputs enumerated — §16

**Governance**
- [x] Approved Document Contract preserved unchanged — no field, type, invariant, or deferral altered
- [x] No architectural ownership reopened; no new component, ADR, glossary term, or directory introduced
- [x] No parser selected, no dependency introduced, no implementation code written

**Result: PASS**, pending review. All planning preconditions are satisfied, with no deviation in force: `docs/DOCUMENT_CONTRACT.md` incorporates accepted review corrections F1 and F4–F8 (Sprint P2.5.1), the repository carries a single, consistent architectural conclusion on text-extraction ownership, and this plan takes the corrected Document Contract directly as its authoritative input (§P0.2, §P0.4). The remaining synchronization items (§14.2) are cross-reference pointers that block nothing.

Sprint P3.1 (Document Construction) may begin upon approval of this plan, subject to §12.3's governance gate if — and only if — a non-stdlib dependency proves necessary.

---

## 18. Explicitly Out of Scope

This document does not, and must not be read to:

- redesign or amend the approved Document Contract, or add/remove/re-type any field, invariant, or deferral;
- reopen architectural ownership of text extraction (settled — §P0.2, A3);
- introduce any new architecture, component, interface, pipeline stage, glossary term, or directory;
- create or imply the need for a new ADR;
- select, name, rank, or recommend a parser, extraction approach, or any dependency;
- introduce a dependency, or modify `requirements.txt`;
- implement construction code, tests, scaffolding, or placeholder classes;
- modify any runtime module (`sample_rag/chunker.py`, `scripts/build_manifest.py`, `scripts/build_chunks.py`) or any repository artifact;
- design Document Serialization or Document Validation;
- resolve Outstanding Questions 1, 3, or 4 from `docs/DOCUMENT_CONTRACT.md`.

---

## 19. Success Criteria

| Criterion | Where satisfied |
|---|---|
| Approved Document Contract translated into an implementation-ready construction plan | §4–§11, §13, §16, §17 |
| Accepted review findings incorporated without reopening approved architectural decisions | F1 → §P0.2, §5 (A3); F2 → §9; F3 → §12; F5 → §14.2; F8 → §11.3 |
| Planning preconditions verified | §P0.1, §P0.4 |
| Repository consistency explicitly confirmed — verified against the corrected `docs/DOCUMENT_CONTRACT.md`, with no conflicting conclusion remaining and nothing assumed | §P0.2, §P0.3, §P0.4 |
| Construction assumptions documented as inherited constraints | §5 (A1–A12) |
| Construction workflow and construction lifecycle documented **separately** | §7 (data flow) and §8 (engineering progression) |
| Dependency governance recorded independently from implementation | §12 — governance, process, and evaluation criteria only; no candidate named |
| Deferred implementation decisions classified in a Decision Register | §15 |
| Implementation inputs documented | §16 |
| Construction readiness objectively demonstrated | §17 |
| Repository ready to begin deterministic Document Construction | §17 Result |

---

## Stop Condition

Per the sprint's own governing instruction, this document ends here.

No construction code has been written. No Python module has been created or modified. No dependency has been added, selected, or recommended. `docs/DOCUMENT_CONTRACT.md`, `docs/DOCUMENT_CONTRACT_REVIEW.md`, `docs/architecture.md`, `docs/roadmap.md`, `docs/MILESTONE_1A.md`, and `docs/glossary.md` are unchanged, and no commit has been made to any of them.

Awaiting review and approval before Sprint P3.1 (Document Construction) begins.
