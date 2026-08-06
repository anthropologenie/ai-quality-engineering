# Data Quality Validation — Architecture and Implementation Plan

**Repository:** `ai-quality-engineering`
**Status:** Design proposal — Sprint P3.1.8.0 (Data Quality Validation Design). **Not approved. No implementation authorized by this document.**
**Sprint:** P3.1.8.0 — Milestone 1A, Final Knowledge Layer Gate
**Verified against:** HEAD `68a412fbe1b31dc42a901ed8800fcc64fcf64b9b`, working tree clean, 95 specifications passing (§0)
**Related documents:** `docs/DOCUMENT_CONTRACT.md` (approved v1.0 — the only source of `Document` field/invariant truth), `docs/DOCUMENT_CONSTRUCTION_PLAN.md` (executed — construction boundaries, §13 validation readiness, §20 resolved decisions), `docs/ENGINEERING_TRACEABILITY_REGISTER.md` (the authoritative record of F-1, D-2, and every open observation), `docs/adr/ADR-P3.1.7.2-F2-corpus-root-containment.md` (accepted — the repository's only ruling on the Construction/Data Quality Validation boundary), `docs/CHUNK_VALIDATION_PLAN.md` (§P0.1 structural-validation precedent, §P5 referential-integrity deferral, §P9 open placement question), `docs/CHUNK_CONTRACT.md` (§11, §17), `docs/MILESTONE_1A.md` (build items 1–3, Acceptance Criteria, Definition of Done), `docs/roadmap.md` (§5 four-layer evaluation strategy, §6 principles, §7 Scope Freeze), `docs/architecture.md` (§4, §5, §6, §10), `docs/altm.md` (Knowledge and Index failure modes), `docs/glossary.md` (Evaluation vs. Validation), `docs/P3.1.7.1_Decision_Gate_Report_Evidence_Verification.md`, `docs/P3.1.7_Independent_Implementation_Review_ClaudeCode.md`, `docs/P3.1.7_Independent_Implementation_Review_Codex.md`, `docs/P3.1.5_Construction_Validation_Evidence_Report.md`

This document performs **Architecture and Planning only**. It defines the architectural responsibilities, ownership boundaries, execution model, validation lifecycle, implementation strategy, and specification strategy for the Data Quality Validation layer. It implements no runtime validation, creates no executable specification, modifies no contract, plan, register, or ADR, and authorizes no implementation work by itself.

Where this document reaches a conclusion the repository has not already recorded, it presents that conclusion as a **recommendation**, not a decision — per the standing governance rule established at Sprint P3.1.7.1 and carried in `docs/ENGINEERING_TRACEABILITY_REGISTER.md` §2: *"architectural disposition is not the implementing agent's decision. An implementing agent presents options and a recommendation; a recommendation is not a decision."*

---

## Terminology Note

No new repository-wide terminology is introduced. "Validation," "invariant," "structural," "corpus," and "collection" are used in the sense `docs/glossary.md`, `scripts/build_manifest.py`'s `validate_manifest`, and `docs/CHUNK_VALIDATION_PLAN.md` already use them. "Layer" follows `docs/roadmap.md` §5's existing four-layer evaluation vocabulary. The failure-class labels **DQ-1 … DQ-7** (§8) and the phase labels **W1 … W6** (§11) are this document's own working labels for organizing evidence, not proposed glossary entries — exactly as `docs/CHUNK_VALIDATION_PLAN.md` treated "Layer 1/2/3" and `docs/DOCUMENT_CONSTRUCTION_PLAN.md` treated "Identity Strategy S1/S2/S3."

The layer name is **Data Quality Validation**, abbreviated **DQV** below. It is the layer `docs/MILESTONE_1A.md` build item 2 names and `docs/roadmap.md` §5 calls Layer 1. This document introduces no second name and no new component.

---

## 0. Repository Verification

Performed independently at the start of this sprint. No previous sprint report or chat history was used as evidence.

| Check | Command | Result |
|---|---|---|
| Working tree | `git status` | ✅ `On branch main` · `nothing to commit, working tree clean` |
| HEAD | `git rev-parse HEAD` | ✅ `68a412fbe1b31dc42a901ed8800fcc64fcf64b9b` |
| Unstaged changes | `git diff --stat` | ✅ empty |
| Staged changes | `git diff --cached --stat` | ✅ empty |
| Test suite | `python3 -m pytest -q` | ✅ `95 passed in 0.77s` |
| HEAD commit subject | `git log --oneline -1` | ✅ `docs(knowledge): synchronize construction documentation after assurance remediation` |

**Verdict: the repository matches the expected baseline exactly.** Expected HEAD, actual HEAD, commit subject, clean tree, and a passing suite all agree. No local modification exists. Planning proceeds.

Corpus state at this baseline, verified directly (relevant to every scope judgement below):

- `sample_rag/knowledge_manifest.json` contains exactly **one** `documents[]` entry: `id: "3f3797c1134c"`, `source: "documents/resume/Karthik_SR_Resume_v2_2.docx"`.
- `sample_rag/documents/jobs/` is empty.
- **`sample_rag/chunks.json` does not exist.** Chunk Serialization (`scripts/build_chunks.py` `write_chunks`) is implemented but has never been run against a real `Document`.
- `tests/` contains four specification files (`test_chunker.py`, `test_document_contract.py`, `test_knowledge_source_construction.py`, `test_knowledge_source_failures.py`). **No manifest-validation, freshness, or data-quality specification exists anywhere in the repository.**

---

## 1. Purpose

Data Quality Validation is the last unbuilt layer of the Milestone 1A Knowledge stage, and the last remaining work item in Milestone 1A's Final Knowledge Layer Gate.

Its purpose is fixed by repository evidence, not chosen here:

> **Layer 1 — Data Quality.** *Is the corpus itself trustworthy? Freshness, completeness, hashing, duplicate detection, chunk validity.* Tool: **PyTest**. *Pure data engineering. No LLM call. Runs before any retrieval exists.*
> — `docs/roadmap.md` §5

> **Validation** — *Checking the inputs to the pipeline are trustworthy before anything is built on them (Layer 1 — Data Quality). Is what establishes that the corpus is trustworthy in the first place.*
> — `docs/glossary.md`, "Evaluation vs. Validation"

> **Knowledge validation before retrieval.** *Data quality is checked before it is trusted as a retrieval source.*
> — `docs/roadmap.md` §6 (locked principle)

The concrete gap is verifiable, not theoretical. Three separate frozen artifacts have each deferred a check to this layer and none has been built:

- `docs/DOCUMENT_CONTRACT.md` §8.5 defers `Document.id` ↔ Manifest referential integrity to *"the same Data Quality Validation pytest layer (`docs/MILESTONE_1A.md` build item 2)."*
- `docs/CHUNK_VALIDATION_PLAN.md` §P5 defers `Chunk.document_id` referential integrity to the same named venue.
- `docs/MILESTONE_1A.md` build item 1 states the Knowledge Manifest is *"Validated by: one pytest suite running hash comparison against the manifest"* — **that suite does not exist** (§0).

Additionally, `docs/ENGINEERING_TRACEABILITY_REGISTER.md` §3.1 carries **F-1** (duplicate manifest identifiers accepted silently), CONFIRMED and independently reproduced, deferred to this sprint family and upheld twice.

This document's purpose is to define — with repository evidence, at architectural altitude — the responsibilities, boundaries, lifecycle, and implementation strategy of that layer, so that Sprint P3.1.8.1 can implement it without rediscovering a question this sprint should have answered.

---

## 2. Scope

### 2.1 Included

- Repository Evidence Inventory of every finding that belongs to Data Quality Validation (§4)
- Architectural layer responsibilities and boundary analysis (§5)
- Responsibility matrix assigning each responsibility type to exactly one layer (§6)
- Validation lifecycle, execution model, and validation pipeline (§7)
- Failure taxonomy and reporting model (§8)
- Contract analysis, focused on F-1 and D-2 (§9)
- Governance recommendation resolving D-2 (§10)
- Implementation roadmap, runtime architecture, and validation components (§11)
- Executable specification strategy (§12)
- Acceptance criteria (§13) and completion gate (§14)
- Implementation readiness assessment (§15), Design Decision Gate summary (§16), implementation baseline recommendation (§17)

### 2.2 Not included

- Any runtime validation implementation, module, function, or scaffolding
- Any executable specification or pytest test
- Any modification to `docs/DOCUMENT_CONTRACT.md`, `docs/DOCUMENT_CONSTRUCTION_PLAN.md`, `docs/ENGINEERING_TRACEABILITY_REGISTER.md`, or any ADR
- Creation of an ADR, an erratum, a glossary term, a component, or a directory
- Any commit or tag
- Chunk Layer, Index Layer, Retrieval Layer, or Evaluation Layer work
- Re-opening any decision recorded in `docs/DOCUMENT_CONTRACT.md`, `docs/DOCUMENT_CONSTRUCTION_PLAN.md` §20, or `ADR-P3.1.7.2-F2`
- Document Serialization design, and Document *structural* Validation design (§5.4 explains why the latter is a distinct, still-blocked concern)

---

## 3. Architectural Principles

Inherited constraints. Sprint P3.1.8.1 builds within these; it does not re-derive, re-litigate, or silently relax any of them. Each is quoted or cited from an approved repository artifact.

| # | Inherited constraint | Source |
|---|---|---|
| **P1** | DQV answers one question: *is the corpus itself trustworthy?* Its subject matter is Freshness, completeness, hashing, duplicate detection, chunk validity. | `docs/roadmap.md` §5 (Layer 1) |
| **P2** | DQV is **pytest**. *"Pure Python, pure pytest, no external model calls."* | `docs/MILESTONE_1A.md` build item 2 |
| **P3** | DQV runs **before** anything is built on the corpus — before retrieval exists. | `docs/roadmap.md` §5, §6 |
| **P4** | DQV owns **cross-artifact and collection-level** properties. Verbatim, from the repository's only accepted ruling on this boundary: *"Data Quality Validation remains responsible for cross-artifact repository properties such as duplicate identifiers, uniqueness, completeness, and consistency."* | `ADR-P3.1.7.2-F2`, accepted rationale |
| **P5** | Construction owns **intra-artifact** checks — those decidable from the configured corpus root plus the single manifest entry being processed, requiring no corpus-wide analysis. | `ADR-P3.1.7.2-F2`, accepted rationale; `docs/DOCUMENT_CONTRACT.md` §8.5 |
| **P6** | DQV introduces **no new validation subsystem**. Manifest precedent: *"No separate validation subsystem — this stays a file plus a check."* | `docs/MILESTONE_1A.md` build item 1 |
| **P7** | DQV must be deterministic. *"Deterministic before probabilistic."* No clock, locale, randomness, network, or machine-specific state. | `docs/architecture.md` §2; `docs/MILESTONE_1A.md` Functional AC 3 |
| **P8** | DQV is **read-only**. It repairs nothing, regenerates nothing, and mutates no repository artifact. Precedent: `validate_manifest` and `validate_chunks` both *"perform no mutation, normalization, or copying"* and return the same object. | `scripts/build_manifest.py` `validate_manifest`; `scripts/build_chunks.py` `validate_chunks` |
| **P9** | Milestone 1A is **stdlib + pytest only**. A new dependency requires a scope decision recorded in `docs/roadmap.md` §7 before it is imported. | `docs/roadmap.md` §6, §7; `docs/architecture.md` §10; `docs/DOCUMENT_CONSTRUCTION_PLAN.md` §12.3 |
| **P10** | DQV must not reopen or duplicate Construction. `Document` construction, corpus-root containment, normalization N1–N5, identity strategy S1, and ordering are settled and specified. | `docs/DOCUMENT_CONSTRUCTION_PLAN.md` §20.3, §20.4; `ADR-P3.1.7.2-F2` |
| **P11** | A check must enforce a **stated** invariant, never invent one. *"Reconcile with F-1 … before implementing a uniqueness check, so the check enforces a stated invariant rather than inventing one."* | `docs/ENGINEERING_TRACEABILITY_REGISTER.md` §3.5, D-2 |
| **P12** | Contract change is permitted only through an explicit, approved, documented route: *"All public contracts remain unchanged throughout Milestone 1A implementation unless a documented contract gap is discovered and explicitly approved."* | `docs/MILESTONE_1A.md`, Definition of Done |

---

## 4. Repository Evidence Inventory

**Deliverable 2.** Every repository finding, deferral, or recorded observation that naturally belongs to Data Quality Validation. Nothing below is a new work item; every row already exists in the repository with a disposition. Each row states its origin sprint, repository evidence, current disposition, architectural owner, and why Construction does not own it.

### 4.1 Findings with an explicit DQV disposition

| ID | Finding | Origin | Repository evidence | Current disposition | Architectural owner | Why Construction does not own it |
|---|---|---|---|---|---|---|
| **F-1** | Duplicate manifest identifiers accepted silently — a manifest with two entries sharing `id: "dup"` returns two `Document`s sharing that id, no exception | Sprint P3.1.5 (Construction Validation) | `docs/ENGINEERING_TRACEABILITY_REGISTER.md` §3.1 (**CONFIRMED**, independently reproduced at P3.1.7.1); `sample_rag/knowledge_source.py` `load()` — no uniqueness check across entries; `docs/P3.1.5_Construction_Validation_Evidence_Report.md` §13 | **Open.** DEFERRED to Sprint P3.1.8 (Data Quality Validation) — upheld at P3.1.7.1, unchanged at P3.1.7.2 | **DQV** | Uniqueness is a **collection-level, cross-artifact** property: it is undecidable from one manifest entry, requiring the whole `documents[]` array. That is exactly the criterion `ADR-P3.1.7.2-F2` used to keep containment in Construction *and* to route "duplicate identifiers, uniqueness" to DQV — the ADR names them verbatim. `docs/DOCUMENT_CONTRACT.md` §8.5 routes such checks to DQV; uniqueness is not among §8.7's three invariants |
| **D-2** | `docs/DOCUMENT_CONTRACT.md` §8.3 states `id` *"is unique across the corpus"*; §8.7's invariants omit uniqueness. The implementation follows the weaker reading | Sprint P3.1.7 (Independent Implementation Review — Claude Code, **MAJOR**) | `docs/ENGINEERING_TRACEABILITY_REGISTER.md` §3.5; `docs/DOCUMENT_CONTRACT.md` §8.3 vs. §8.7; `docs/P3.1.7.1_Decision_Gate_Report_Evidence_Verification.md` (Independently Verified; Future Sprint — P3.1.8, with F-1) | **Open.** *"Reconcile **with F-1** at Sprint P3.1.8, before implementing a uniqueness check, so the check enforces a stated invariant rather than inventing one"* | **DQV (analysis) → repository owner (decision)** | It is a **documentation/governance** defect in a frozen contract, not a construction defect. Construction cannot resolve it: `sample_rag/knowledge_source.py` correctly implements §8.7's three invariants, and no code change would make the contract self-consistent. Resolved by §9–§10 of this document |
| **A8 / §8.5** | `Document.id` ↔ `knowledge_manifest.json` `documents[]` referential integrity | Sprint P2.5 (Document Contract Freeze) | `docs/DOCUMENT_CONTRACT.md` §8.5: *"not part of this structural contract … Deferred to the same Data Quality Validation pytest layer"*; `docs/DOCUMENT_CONSTRUCTION_PLAN.md` §5 (A8), §15 | **Open.** Deferred by the approved contract itself | **DQV** | The contract classifies it as *"a semantic/cross-artifact validation concern, not a structural one."* It requires both the constructed `Document` set and the Manifest — two artifacts — so it fails P5's intra-artifact test |
| **§P5** | `Chunk.document_id` referential integrity against `knowledge_manifest.json` | Sprint P2.1 (Chunk Contract §11), re-deferred at Sprint P2.4.0 | `docs/CHUNK_CONTRACT.md` §11; `docs/CHUNK_VALIDATION_PLAN.md` §P5: *"repository evidence points to the Data Quality Validation pytest layer … as its home … not a fifth layer inside `validate_chunks()` itself"* | **Open, and additionally blocked** — `sample_rag/chunks.json` does not exist (§0) | **DQV** | `validate_chunks()`'s scope is a single persisted artifact. Folding a cross-artifact check into it *"would collapse a distinction the repository has already made deliberately"* and would introduce a cross-script dependency the repository has no equivalent of |
| **§P1.4** | Chunk invariant 3, full form — `text == document_text[character_start:character_end]` — is only half-checkable (`len(text) == character_end - character_start`) | Sprint P2.4.0 (Chunk Validation Planning) | `docs/CHUNK_VALIDATION_PLAN.md` §P1.4, §P3 (*"Not classified as a validation rule"*), §P8; `docs/DOCUMENT_CONSTRUCTION_PLAN.md` §13.3 | **Open, and additionally blocked** — requires both a `Document` and `chunks.json` | **DQV** | It is cross-artifact by construction: it compares a Chunk's text against a `Document`'s text. `validate_chunks()` cannot see a `Document`; Construction cannot see a Chunk |
| **§8.8.2 / F8** | Extracted-text drift: `documents[].hash` is a SHA-256 of the **source file's bytes**, not of extracted text, so a change to the extraction mechanism can alter `Document.text` for byte-identical source content with no existing check registering it | Sprint P2.5.1 (Contract Review Finding F8) | `docs/DOCUMENT_CONTRACT.md` §8.8 item 2; `docs/DOCUMENT_CONSTRUCTION_PLAN.md` §11.3, §15; `scripts/build_manifest.py` `compute_sha256` | **Open, recorded not resolved.** *"It is a Data Quality Validation concern … if a need for one is ever evidenced"* | **DQV** | The contract states it is *"recorded here only; no detector is designed, scoped, or required."* Detecting mechanism drift requires comparing across runs and artifacts; it is not a property of one construction |
| **Case A** | Corpus-and-Manifest disagreement, narrowing direction: a corpus file present on disk but absent from the Manifest is **silently excluded** by `load()` | Sprint P3.1 (Construction), recorded at Sprint P3.1.7.2 | `docs/DOCUMENT_CONSTRUCTION_PLAN.md` §20.3: *"a file present but unmanifested is silently excluded (**detecting it needs the corpus/Manifest diff deferred to Data Quality Validation**)"*; §9.1 row 7 | **Closed as a Construction decision; the detector is deferred to DQV** | **DQV** | Construction deliberately chose silent narrowing under strategy S1 and specified it. Detecting the divergence requires enumerating the filesystem **and** the Manifest — a corpus-wide, cross-artifact comparison, failing P5 |
| **Build item 1 check** | *"Validated by: one pytest suite running hash comparison against the manifest"* — the freshness/integrity suite promised by the Knowledge Manifest contract | Sprint P1.2.0 (Manifest Contract Freeze) | `docs/MILESTONE_1A.md` build item 1; `docs/MILESTONE_1A.md` Architectural AC 3 (*"sole source of truth that freshness/hash validation checks against"*); `docs/altm.md` Knowledge failure mode (*"Detection: Content hash mismatch … Layer 1 (Data Quality, pytest)"*); **verified absent from `tests/` at HEAD** | **Open — owed since Sprint P1.2.0, never built** | **DQV** | It is a corpus-wide comparison of catalogued hashes against filesystem content. `validate_manifest`'s own docstring scopes it to structure only, with no filesystem I/O; its design property is that it *"never depends on filesystem I/O"* |
| **Build item 2 — Index Coverage Validation** | *"Every chunk produced during indexing has a deterministic placeholder representation behind the `EmbeddingProvider` interface"* | Sprint P0 (Milestone definition) | `docs/MILESTONE_1A.md` build item 2; `docs/altm.md` Index failure mode (*"Chunk coverage check … Layer 1 (Data Quality, pytest)"*) | **Open, and blocked** — no Index Layer, no `EmbeddingProvider` implementation, no `chunks.json` exists | **DQV** | Named as a DQV responsibility by the milestone document itself. Structurally unavailable to Construction, which produces no chunks and no vectors |

### 4.2 Observations recorded as DQV **candidates**, with no current evidence of need

Listed so P3.1.8.1 does not treat them as scope, and so they are not lost.

| ID | Observation | Origin | Repository evidence | Current disposition | Architectural owner |
|---|---|---|---|---|---|
| **F-2-sym** | Containment reads the manifest value, so a corpus file that is a **symlink** pointing outside the corpus root is not detected | Sprint P3.1.7.2 (`ADR-P3.1.7.2-F2`) | `docs/ENGINEERING_TRACEABILITY_REGISTER.md` §3.5; ADR "Deliberately not done" | **Deliberate boundary of an accepted ADR.** *"Candidate for Data Quality Validation if evidence ever emerges; none exists today"* | **DQV (candidate only — not scheduled)** |
| **Drift detector** | The concrete detector for §8.8.2 extracted-text drift | Sprint P2.5.1 | `docs/DOCUMENT_CONSTRUCTION_PLAN.md` §15 | **Still deferred.** *"No repository evidence yet establishes a need"* | **DQV (candidate only — not scheduled)** |

### 4.3 Open observations that do **not** belong to DQV

Recorded to close the inventory. The sprint brief requires every remaining deferred finding to have an assigned owner; these have one, and it is not DQV.

| ID | Observation | Assigned owner | Evidence for the assignment |
|---|---|---|---|
| **I-6** | `test_b6` hardcodes the corpus filename `Karthik_SR_Resume_v2_2.docx` | **Executable Specification Suite** — re-verify at corpus expansion | `docs/ENGINEERING_TRACEABILITY_REGISTER.md` §3.5; a specification-hygiene item about a test fixture, not a corpus property |
| **I-7** | `test_a15`'s allowlist tracks CPython-synthesized dataclass members (3.13+; suite runs on 3.12) | **Executable Specification Suite** — re-verify at the next CPython upgrade | `docs/ENGINEERING_TRACEABILITY_REGISTER.md` §3.5; a toolchain-version item |
| **A-3** | `discover_manifest_entries` performs admissibility checks bounded only by a docstring | **Construction** — re-inspect if that function grows | `docs/ENGINEERING_TRACEABILITY_REGISTER.md` §3.5; the function is Construction-owned runtime code |
| **P3.1.7-ARCH-01** | JobOps-as-`Document` classification unresolved (Contract Outstanding Question 3) | **Future milestone / documentation clarification** — intentionally deferred | `docs/DOCUMENT_CONTRACT.md` Phase 11 Q3; structurally excluded today by the manifest discovery gate. `docs/P3.1.7.1_Decision_Gate_Report_Evidence_Verification.md` carries it as *"Revisit only if DQV needs the JobOps boundary"* — §5.5 records that P3.1.8.1 does **not** need it |
| **V2 / Q4** | Document persistence / serialization; and the `Persistent Canonical Artifact / Runtime Artifact` classification of `Document` | **Future Document Serialization sprint** | `docs/DOCUMENT_CONTRACT.md` Phase 10, Outstanding Question 4; `docs/DOCUMENT_CONSTRUCTION_PLAN.md` §13.1 V2, §15. §5.4 establishes that this does **not** block DQV |
| **Determinism verification** | Two-run / cross-process comparison of `Document.text` | **Executable Specification Suite — already closed** | `docs/DOCUMENT_CONSTRUCTION_PLAN.md` §20.3: *"Closed — Two-run and cross-process comparison, committed as executable specifications at Sprint P3.1.6."* DQV must **not** duplicate it |
| **Q1** | `document_type` / `source` field promotion | **Future contract revision** — revisit at corpus expansion | `docs/DOCUMENT_CONTRACT.md` §8.6, Outstanding Question 1; `sample_rag/documents/jobs/` is still empty |
| **A-1 duplication** | `SUPPORTED_EXTENSIONS` deliberately duplicated across `sample_rag/` and `scripts/` | **Closed** — accepted trade-off, now enforced by specification AH-9 | `docs/ENGINEERING_TRACEABILITY_REGISTER.md` §3.3, §5 |
| **F-2** | Corpus-root containment | **Closed** — Construction, by `ADR-P3.1.7.2-F2` | `docs/ENGINEERING_TRACEABILITY_REGISTER.md` §3.2 |

**Inventory completeness statement.** Every row in `docs/ENGINEERING_TRACEABILITY_REGISTER.md` §3.5 ("Open findings and observations") appears above with an assigned owner: F-1 (§4.1), D-2 (§4.1), F-2-sym (§4.2), I-6, I-7, A-3, P3.1.7-ARCH-01 (§4.3). Every "Still deferred" row in `docs/DOCUMENT_CONSTRUCTION_PLAN.md` §20.3 likewise appears: persistence, Document Validation design, referential integrity, drift detection, orchestration, `document_type`, JobOps, performance. No finding was created, and none was left unowned.

---

## 5. Boundary Analysis

**Deliverable 3.** Where each layer's authority begins and ends, and why.

### 5.1 The repository's decision criterion, already accepted

The repository has ruled on the Construction/DQV boundary exactly once, and the ruling supplies a reusable criterion rather than a one-off answer. From `ADR-P3.1.7.2-F2`, the accepted rationale as recorded at approval:

> *Corpus-root containment is an **intra-artifact** construction invariant. The check depends only upon the configured corpus root and the manifest entry currently being processed. **It requires no corpus-wide analysis** and therefore belongs to Construction rather than Data Quality Validation.*
>
> ***Data Quality Validation remains responsible for cross-artifact repository properties such as duplicate identifiers, uniqueness, completeness, and consistency.***

This yields a single, mechanical test, which this document applies uniformly and invents nothing beyond:

> **The Corpus-Wide Analysis Test.** If a check is decidable from the single entry (or single value) currently being processed plus fixed configuration, it belongs to **Construction**. If deciding it requires more than one entry, more than one artifact, or the corpus as a whole, it belongs to **Data Quality Validation**.

The same criterion is independently stated by `docs/DOCUMENT_CONTRACT.md` §8.5, which routes referential integrity to DQV *"for the identical reason `docs/CHUNK_CONTRACT.md` §11 already gave … it is a semantic/cross-artifact validation concern, not a structural one."* Two independent frozen artifacts agree; this is **evidence**, not inference.

### 5.2 The layer model

The sprint brief sketches three layers. Repository evidence shows **four**, because a distinct structural-validation layer already exists in the repository as shipped code. Recording it is evidence, not invention: `docs/CHUNK_VALIDATION_PLAN.md` §P0.1 draws this exact distinction, citing `docs/MILESTONE_1A.md` build item 2 as separating *"**structural** validation (this function, embedded in the artifact's own assemble/serialize/validate module) from **Data Quality Validation** (… a distinct pytest suite, Layer 1)."*

```text
        ┌───────────────────────────────────────────────────────────┐
        │  CONSTRUCTION                                             │
        │  sample_rag/knowledge_source.py, sample_rag/chunker.py    │
        │  Intra-artifact, single-entry, on the runtime path.       │
        │  PREVENTS. Raises before a bad value is ever returned.    │
        └───────────────────────────────────────────────────────────┘
                                   ↓
        ┌───────────────────────────────────────────────────────────┐
        │  STRUCTURAL ARTIFACT VALIDATION                           │
        │  scripts/build_manifest.py  validate_manifest()           │
        │  scripts/build_chunks.py    validate_chunks()             │
        │  One persisted artifact, in isolation. No filesystem I/O. │
        │  Shape, types, and that artifact's own collection rules.  │
        └───────────────────────────────────────────────────────────┘
                                   ↓
        ┌───────────────────────────────────────────────────────────┐
        │  DATA QUALITY VALIDATION            ← this plan           │
        │  pytest, Layer 1. Read-only. Off the runtime path.        │
        │  Corpus-wide and cross-artifact. Freshness, completeness, │
        │  hashing, duplicate detection, referential integrity.     │
        │  DETECTS. Establishes that the corpus is trustworthy.     │
        └───────────────────────────────────────────────────────────┘
                                   ↓
        ┌───────────────────────────────────────────────────────────┐
        │  FUTURE EVALUATION  (Layers 2–4, roadmap §5)              │
        │  Retrieval quality (Ragas) · Generation quality (DeepEval)│
        │  · Regression (Promptfoo).  Assumes the corpus is already │
        │  trustworthy. Out of scope for Milestone 1A.              │
        └───────────────────────────────────────────────────────────┘
```

The Construction ↔ DQV distinction is **prevention vs. detection**, stated verbatim by `ADR-P3.1.7.2-F2`: *"Prevention rather than detection. Construction is the only layer on the runtime path. Data Quality Validation would detect the condition after the fact."*

The DQV ↔ Future Evaluation distinction is stated verbatim by `docs/glossary.md`: Evaluation *"assumes the corpus is already trustworthy"*; Validation *"is what establishes that the corpus is trustworthy in the first place."*

### 5.3 Why the Structural Artifact Validation layer is **not** DQV, and must not absorb DQV work

This matters, because `validate_manifest()` is the nearest existing thing to a duplicate-id check and a naive implementation would put F-1 there. Three independent pieces of repository evidence forbid it:

1. **It is not on the runtime path.** `sample_rag/knowledge_source.py` imports nothing from `scripts/`; `KnowledgeSource.load()` never calls `validate_manifest()`. `ADR-P3.1.7.2-F2` rejected Option C on precisely this ground: *"it would not protect the runtime path at all."*
2. **`docs/architecture.md` §6 defines `scripts/` as "not pipeline logic."** The same clause that made strategy S2 unavailable to Construction (`docs/DOCUMENT_CONSTRUCTION_PLAN.md` §9.1) applies here.
3. **`validate_manifest`'s own scope excludes it.** Its docstring states it *"never depends on filesystem I/O"*, and `docs/CHUNK_VALIDATION_PLAN.md` §P0.1 records as repository fact that it *"does not check `documents[].id` uniqueness, despite `id` being a repository-wide identity field."* That is a scoping fact about the precedent, not an oversight to be corrected opportunistically.

**Consequence, stated so P3.1.8.1 cannot resolve it by accident:** the F-1 uniqueness check belongs in the DQV pytest layer, **not** in `validate_manifest()`. This assignment does not forbid `validate_manifest()` from ever gaining a uniqueness check — but no repository evidence calls for one, changing it would edit a shipped, frozen Manifest lifecycle (`docs/DOCUMENT_CONSTRUCTION_PLAN.md` §9.2 declined an analogous edit for exactly this reason), and doing so would create a second owner for one responsibility, which §6 forbids.

### 5.4 Is DQV blocked by the unresolved persistence question (V2)? — **No.**

This is the sharpest architectural risk to this sprint, because `docs/DOCUMENT_CONSTRUCTION_PLAN.md` §13.1 lists as precondition **V2**: *"The persistence question is settled — is `Document` ever serialized … Validation's entire shape — what it consumes — depends on the answer."* That precondition is **still open** (§20.3: *"Document persistence / serialization — Still deferred"*). If V2 blocked DQV, this sprint would have to stop.

It does not, because §13 is scoped to **Document Validation**, a different thing from **Data Quality Validation**:

| | **Document Validation** (§13, blocked) | **Data Quality Validation** (this plan, not blocked) |
|---|---|---|
| What it is | A structural validator for a `Document`, *"mirroring `validate_manifest`/`validate_chunks`"* | The Layer 1 pytest suite named by `docs/MILESTONE_1A.md` build item 2 |
| Where named | `docs/DOCUMENT_CONTRACT.md` Phase 9 ("Validator" row), Phase 10 ("Document Validation — … not designed here"); `docs/DOCUMENT_CONSTRUCTION_PLAN.md` §13 | `docs/MILESTONE_1A.md` build item 2; `docs/roadmap.md` §5 Layer 1; `docs/glossary.md` |
| What it consumes | A **persisted artifact** — hence V2 | The Manifest, the corpus filesystem, and `KnowledgeSource.load()`'s **in-memory** return value |
| Why V2 binds / does not bind | `docs/CHUNK_VALIDATION_PLAN.md` *"validates a persisted collection"*; with no `Document` artifact, there is nothing to point such a validator at | pytest can call `load()` directly. This is not a hypothesis — `tests/test_knowledge_source_construction.py` and `tests/conftest.py`'s `real_documents` fixture already do exactly this at HEAD |

The same document already draws this line itself: `docs/DOCUMENT_CONTRACT.md` Phase 9's "Validator" row separates *"Structural validation of a `Document` instance … not yet designed"* from *"Semantic/referential checks (Document.id ↔ Manifest entry) belong to the Data Quality Validation pytest layer."* One row, two owners, two schedules.

**Recorded consequence.** DQV consumes `Document` values as a **runtime input**, never as an artifact. It therefore produces no artifact and asserts nothing about persistence. If a future sprint settles V2 affirmatively, DQV's inputs are unaffected — an additional structural validator would simply join the Structural Artifact Validation layer. **Inference, clearly labelled:** this classification is this document's reading of two frozen artifacts, not a quotation from either. It is the only reading under which `docs/MILESTONE_1A.md` build item 2 (a shipped milestone requirement) is not indefinitely blocked by an admittedly-open question (`docs/DOCUMENT_CONTRACT.md` Outstanding Question 4) — and §16 records it as the single classification the repository owner should confirm.

### 5.5 Boundaries that are **not** in question

Recorded so P3.1.8.1 does not reopen them.

| Boundary | Status | Evidence |
|---|---|---|
| Corpus-root containment | **Construction.** Closed | `ADR-P3.1.7.2-F2`, accepted |
| Text extraction ownership | **Knowledge Source.** Closed | `docs/DOCUMENT_CONTRACT.md` Phase 9, Phase 11 Q2 (ANSWERED); `docs/DOCUMENT_CONTRACT_REVIEW.md` F1 |
| Identity derivation | **Manifest.** `Document.id` is read, never derived (S1) | `docs/DOCUMENT_CONSTRUCTION_PLAN.md` §20.3; `sample_rag/knowledge_source.py` `load()` |
| Determinism verification | **Executable Specification Suite.** Closed | `docs/DOCUMENT_CONSTRUCTION_PLAN.md` §20.3 |
| Manifest generation and `documents[].indexed` | **`scripts/build_manifest.py`.** DQV reads, never writes | `docs/DOCUMENT_CONSTRUCTION_PLAN.md` §6.2; P8 |
| JobOps-as-`Document` | **Structurally excluded today.** DQV does not need it | `docs/DOCUMENT_CONTRACT.md` Phase 11 Q3 (F7 structural exclusion); a JobOps row cannot obtain a `documents[]` entry, so no DQV check can reach one |

---

## 6. Responsibility Matrix

**Deliverable 4.** Every responsibility type named by the sprint brief, assigned to **exactly one** architectural layer. Each assignment states its evidence and the criterion (§5.1) that produced it.

### 6.1 The matrix

| # | Responsibility type | Owning layer | Criterion | Evidence |
|---|---|---|---|---|
| 1 | **Single-artifact validation** — structural shape and types of one persisted artifact, in isolation, without filesystem I/O | **Structural Artifact Validation** | Decidable from the artifact alone; no corpus-wide analysis, no second artifact | `scripts/build_manifest.py` `validate_manifest`; `scripts/build_chunks.py` `validate_chunks`; `docs/CHUNK_VALIDATION_PLAN.md` §P0.1, §P2.1 |
| 2 | **Single-entry admissibility** — corpus-root containment, extension gate, entry field types at construction time | **Construction** | Intra-artifact: configured root + the one entry being processed | `ADR-P3.1.7.2-F2` (accepted); `sample_rag/knowledge_source.py` `resolve_source_path`, `discover_manifest_entries`; `docs/DOCUMENT_CONSTRUCTION_PLAN.md` §10.1 |
| 3 | **Cross-artifact validation** — any property requiring two or more artifacts to decide | **Data Quality Validation** | Fails the corpus-wide analysis test | `ADR-P3.1.7.2-F2` accepted rationale (verbatim: *"cross-artifact repository properties"*); `docs/DOCUMENT_CONTRACT.md` §8.5; `docs/CHUNK_VALIDATION_PLAN.md` §P5 |
| 4 | **Corpus consistency** — catalogued hash vs. file content (freshness/integrity); corpus filesystem vs. Manifest enumeration (Case A) | **Data Quality Validation** | Requires the corpus as a whole plus the Manifest | `docs/MILESTONE_1A.md` build item 1 (*"one pytest suite running hash comparison against the manifest"*), Architectural AC 3; `docs/roadmap.md` §5 (*"Freshness … hashing"*); `docs/altm.md` Knowledge failure mode (*"Layer 1 (Data Quality, pytest)"*); `docs/DOCUMENT_CONSTRUCTION_PLAN.md` §20.3 (Case A) |
| 5 | **Collection integrity — within one persisted artifact** — e.g. `Chunk.id` uniqueness across `chunks.json`; per-`document_id` index contiguity and non-overlap | **Structural Artifact Validation** | Decidable from that one artifact | `docs/CHUNK_VALIDATION_PLAN.md` §P3 (Collection Invariants), §P4 (Layer 2); implemented at `scripts/build_chunks.py` `_validate_collection_invariants` |
| 6 | **Collection integrity — across the corpus** — `documents[].id` uniqueness, and equivalently `Document.id` uniqueness across `load()` (**F-1**) | **Data Quality Validation** | Requires every manifest entry; undecidable from one | `ADR-P3.1.7.2-F2` accepted rationale (verbatim: *"duplicate identifiers, uniqueness"*); `docs/roadmap.md` §5 (verbatim: *"duplicate detection"*); `docs/ENGINEERING_TRACEABILITY_REGISTER.md` §3.1; §5.3 above (why not `validate_manifest`) |
| 7 | **Referential integrity** — `Document.id` ↔ Manifest entry; `Chunk.document_id` ↔ Manifest/`Document`; Chunk invariant 3's full substring form | **Data Quality Validation** | Two artifacts by definition | `docs/DOCUMENT_CONTRACT.md` §8.5; `docs/CHUNK_CONTRACT.md` §11; `docs/CHUNK_VALIDATION_PLAN.md` §P5, §P1.4; `docs/DOCUMENT_CONSTRUCTION_PLAN.md` §5 (A8), §13.3, §15 |
| 8 | **Validation reporting** — how DQV outcomes are surfaced | **Data Quality Validation** | It reports on its own findings; no separate subsystem exists or is warranted | `docs/MILESTONE_1A.md` build item 2 (*"Pure Python, pure pytest"*), build item 1 (*"No separate validation subsystem — this stays a file plus a check"*); reporting model specified in §8.4 |
| 9 | **Index coverage** — every chunk has a deterministic placeholder representation behind `EmbeddingProvider` | **Data Quality Validation** (blocked — no Index Layer) | Named as DQV by the milestone document; spans chunks and vectors | `docs/MILESTONE_1A.md` build item 2; `docs/altm.md` Index failure mode (*"Layer 1 (Data Quality, pytest)"*) |
| 10 | **Determinism verification** — repeated construction yields identical values | **Executable Specification Suite** | Not a property of any artifact; a property of repeated execution | `docs/DOCUMENT_CONTRACT.md` §8.8 item 1; `docs/DOCUMENT_CONSTRUCTION_PLAN.md` §11.3, §20.3 (**Closed** at Sprint P3.1.6) |
| 11 | **Evaluation correctness** — scoring pipeline output against the Golden Dataset | **Future Evaluation** | Assumes the corpus is already trustworthy | `docs/glossary.md` Evaluation vs. Validation; `docs/roadmap.md` §5 Layers 2–4 |
| 12 | **Retrieval quality** — Context Precision / Context Recall | **Future Evaluation** (Layer 2, Ragas) | *"Assumes the corpus itself is current — a stale corpus is a Layer 1 failure, not a Layer 2 one"* | `docs/roadmap.md` §5; `docs/MILESTONE_1A.md` Out of Scope (Ragas; retrieval quality optimization) |
| 13 | **LLM answer quality** — Faithfulness, Groundedness, Hallucination Rate | **Future Evaluation** (Layer 3, DeepEval) | *"A model can be 100% faithful to a stale document"* | `docs/roadmap.md` §5; `docs/MILESTONE_1A.md` Out of Scope (DeepEval; real LLM generation) |

### 6.2 No-overlap verification

The sprint requires no overlap, no ambiguity, no duplicated ownership. Each potential collision is resolved explicitly:

| Potential collision | Resolution | Authority |
|---|---|---|
| Rows 5 and 6 both say "collection integrity" | Split on scope: **within one persisted artifact** → Structural (row 5); **across the corpus / across artifacts** → DQV (row 6). This is the corpus-wide analysis test applied literally | §5.1 |
| Row 6 vs. `validate_manifest()` | DQV. `validate_manifest` is off the runtime path, lives in a directory defined as not pipeline logic, and has never had a cross-entry check | §5.3 |
| Row 2 vs. row 3 (containment could be called cross-artifact) | Construction. The accepted ADR ruled it intra-artifact and implemented it there. Not reopened | `ADR-P3.1.7.2-F2` |
| Row 7 vs. `validate_chunks()` | DQV. `docs/CHUNK_VALIDATION_PLAN.md` §P5 explicitly declined *"a fifth layer inside `validate_chunks()` itself"* | §P5 |
| Row 10 vs. DQV | Executable Specification Suite, **already closed**. DQV must not add a second determinism check | `docs/DOCUMENT_CONSTRUCTION_PLAN.md` §20.3 |
| Row 4 (Case A narrowing) vs. Construction | DQV. Construction's silent-narrowing behaviour is a **closed, specified decision**; only the *detector* is deferred, and detecting it requires the corpus/Manifest diff | `docs/DOCUMENT_CONSTRUCTION_PLAN.md` §20.3 |
| DQV vs. Future Evaluation | The glossary draws this line: Validation establishes trust; Evaluation assumes it | `docs/glossary.md` |

**Result:** thirteen responsibility types, thirteen single owners, seven collisions explicitly resolved against named repository authority. No responsibility is assigned to two layers, and none is unassigned.

---

## 7. Validation Architecture

**Deliverable 5.** The complete validation lifecycle.

### 7.1 Execution timing

DQV executes **after Construction and before the Chunk Layer trusts the corpus** — `docs/roadmap.md` §6: *"Knowledge validation before retrieval. Data quality is checked before it is trusted as a retrieval source."*

It is **off the runtime path**. `KnowledgeSource.load()` does not call it, and must not: DQV is a pytest suite (P2), and `docs/architecture.md` §6 keeps *"Pipeline logic (`sample_rag/`) … separate from the logic that evaluates it (`evaluation/`, `tests/`) so that the system under test and the test harness cannot be silently coupled."* DQV detects; Construction prevents (§5.2).

Invocation is therefore `python3 -m pytest` — the same command that constitutes `docs/MILESTONE_1A.md` Functional AC 4 (*"Full pytest suite passes"*). DQV adds no new entry point, no CLI, and no orchestration (P6).

### 7.2 Inputs and outputs

| Inputs | Nature | Source |
|---|---|---|
| `sample_rag/knowledge_manifest.json` | Persisted artifact, read-only | `docs/MILESTONE_1A.md` build item 1 |
| `sample_rag/documents/**` | Corpus filesystem, read-only | `docs/architecture.md` §10 (locked) |
| `KnowledgeSource().load()` → `List[Document]` | **In-memory runtime value**, not an artifact | `docs/architecture.md` §5; `sample_rag/knowledge_source.py`; §5.4 |
| *(future, blocked)* `sample_rag/chunks.json` | Persisted artifact — **does not exist at HEAD** | `docs/CHUNK_SERIALIZATION_PLAN.md`; §0 |

| Outputs | Nature |
|---|---|
| pytest pass/fail per check | The report. See §8.4 |
| **No repository artifact** | DQV writes nothing, repairs nothing, regenerates nothing (P8) |
| **No mutation of `documents[].indexed`** | Owned by the Manifest lifecycle (§5.5) |

**"Validated Corpus" is a state, not a file.** No `validated_corpus.json` exists or is proposed. The corpus is validated exactly when the DQV suite passes against it. This is stated explicitly so P3.1.8.1 does not invent an artifact — the same discipline `docs/DOCUMENT_CONSTRUCTION_PLAN.md` §4.3 applied when it recorded "No persisted `Document` artifact" as an explicit non-output.

### 7.3 Validation pipeline

```text
   ┌──────────────────────────────┐        ┌──────────────────────────────┐
   │  Knowledge Manifest          │        │  Corpus filesystem           │
   │  sample_rag/                 │        │  sample_rag/documents/**     │
   │  knowledge_manifest.json     │        │  (canonical .docx corpus)    │
   └──────────────┬───────────────┘        └──────────────┬───────────────┘
                  │                                        │
                  │  ── owned by scripts/build_manifest.py ──
                  │                                        │
                  ▼                                        ▼
   ╔══════════════════════════════════════════════════════════════════════╗
   ║  CONSTRUCTION — sample_rag/knowledge_source.py                       ║
   ║  discover_manifest_entries → resolve_source_path → extract_text      ║
   ║  → normalize_text (N1–N5) → Document(id, text)                       ║
   ║  Intra-artifact checks only. Raises DocumentConstructionError.       ║
   ╚══════════════════════════════════════════════════════════════════════╝
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │  Constructed Documents        │
                    │  List[Document], in memory,   │
                    │  manifest order, no artifact  │
                    └───────────────┬───────────────┘
                                    │
                                    ▼
   ╔══════════════════════════════════════════════════════════════════════╗
   ║  DATA QUALITY VALIDATION — pytest, Layer 1, read-only     ← P3.1.8.1 ║
   ║                                                                      ║
   ║   Stage 1  Manifest structural gate    (reuse validate_manifest)     ║
   ║   Stage 2  Collection integrity        DQ-2  ← F-1                   ║
   ║   Stage 3  Corpus consistency          DQ-1, DQ-3                    ║
   ║   Stage 4  Referential integrity       DQ-4                          ║
   ║   Stage 5  Chunk-dependent checks      DQ-5, DQ-6, DQ-7  (BLOCKED)   ║
   ╚══════════════════════════════════════════════════════════════════════╝
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │  Validated Corpus             │
                    │  A STATE, not an artifact:    │
                    │  "the DQV suite passes"       │
                    └───────────────┬───────────────┘
                                    │
                                    ▼
   ╔══════════════════════════════════════════════════════════════════════╗
   ║  CHUNK LAYER — sample_rag/chunker.py (implemented, unmodified)       ║
   ║  Chunker.chunk(doc) -> List[Chunk] → scripts/build_chunks.py         ║
   ╚══════════════════════════════════════════════════════════════════════╝
```

### 7.4 Transitions and ownership

| Transition | What moves | Owner | Evidence |
|---|---|---|---|
| Corpus files → Knowledge Manifest | Discovery, hashing, id generation, serialization | **`scripts/build_manifest.py`** | `docs/MILESTONE_1A.md` build item 1; `docs/DOCUMENT_CONSTRUCTION_PLAN.md` §6.2 (Construction must not generate, mutate, or repair the Manifest) |
| Manifest + corpus files → `List[Document]` | Enumeration (S1), resolution, extraction, N1–N5 normalization, assembly | **Knowledge Source (Construction)** | `docs/architecture.md` §5; `docs/DOCUMENT_CONSTRUCTION_PLAN.md` §7, §20.3 |
| `List[Document]` → Validated Corpus | Corpus-wide and cross-artifact assertion. **Adds no value, transforms nothing** — the `Document` values that enter are the values that leave | **Data Quality Validation** | P8; `docs/roadmap.md` §5, §6 |
| Validated Corpus → Chunks | Structure-aware chunking against `Document.text` | **Chunker (Index stage)** | `docs/architecture.md` §5; `docs/MILESTONE_1A.md` build item 3 |
| Chunks → `chunks.json` → validated collection | Serialization, then single-artifact structural validation | **`scripts/build_chunks.py`** | `docs/CHUNK_SERIALIZATION_PLAN.md`; `docs/CHUNK_VALIDATION_PLAN.md` §P2.1 |

**The transition that does not exist.** There is no arrow from DQV back to Construction, to the Manifest, or to the corpus. DQV never repairs. This mirrors `docs/DOCUMENT_CONSTRUCTION_PLAN.md` §7's own note — *"Nothing flows back"* — applied one layer later.

### 7.5 Determinism of the validation layer itself

Every DQV check must be a total function of (Manifest, corpus bytes, `load()` output). No clock, locale, environment, randomness, network, or iteration-order dependence (P7). Two concrete consequences, each with direct repository precedent:

- Any filesystem enumeration DQV performs must be `sorted(...)`, for the same reason `scripts/build_manifest.py` `main()` sorts `discover_documents`' `rglob` output.
- Failure messages must not embed absolute paths that vary by machine, or the specification becomes environment-coupled. Precedent: `tests/conftest.py`'s specifications assert behaviour, not machine state, and deliberately avoid freezing implementation artefacts such as SHA-256 digests of one corpus snapshot.

---

## 8. Failure Taxonomy

Every class below traces to a named repository source. None is invented. `docs/roadmap.md` §5's Layer 1 responsibility line — *"Freshness, completeness, hashing, duplicate detection, chunk validity"* — supplies five of the seven directly.

### 8.1 The taxonomy

| ID | Failure class | What it detects | Repository source | Status at P3.1.8.1 |
|---|---|---|---|---|
| **DQ-1** | **Freshness / integrity failure** | A catalogued `documents[].hash` no longer matches the SHA-256 of the file at `documents[].source` | `docs/roadmap.md` §5 (*"Freshness … hashing"*); `docs/MILESTONE_1A.md` build item 1, Architectural AC 3; `docs/altm.md` Knowledge failure mode | **In scope** |
| **DQ-2** | **Duplicate-identifier failure** | Two `documents[]` entries share an `id`; equivalently, two `Document`s from one `load()` share an `id` (**F-1**) | `docs/roadmap.md` §5 (*"duplicate detection"*); `ADR-P3.1.7.2-F2` (*"duplicate identifiers, uniqueness"*); Register §3.1 | **In scope — gated on the D-2 erratum (§10)** |
| **DQ-3** | **Completeness failure** | A corpus file exists beneath `sample_rag/documents/**` with an approved extension but has no `documents[]` entry — the Case A silent-narrowing blind spot | `docs/roadmap.md` §5 (*"completeness"*); `docs/DOCUMENT_CONSTRUCTION_PLAN.md` §20.3, §9.1 row 7 | **In scope** |
| **DQ-4** | **Referential-integrity failure** | A `Document.id` returned by `load()` has no corresponding `documents[]` entry | `docs/DOCUMENT_CONTRACT.md` §8.5; `docs/DOCUMENT_CONSTRUCTION_PLAN.md` A8, §13.2 | **In scope** |
| **DQ-5** | **Chunk validity failure** | A persisted chunk collection violates the Chunk Contract as a *corpus* property (as opposed to `validate_chunks()`'s single-artifact scope) | `docs/roadmap.md` §5 (*"chunk validity"*) | **Blocked** — no `chunks.json` (§0) |
| **DQ-6** | **Chunk referential-integrity failure** | A `Chunk.document_id` has no corresponding Manifest entry / `Document`; and Chunk invariant 3's full form, `text == document_text[character_start:character_end]` | `docs/CHUNK_CONTRACT.md` §11, §17 inv. 3; `docs/CHUNK_VALIDATION_PLAN.md` §P5, §P1.4 | **Blocked** — no `chunks.json` |
| **DQ-7** | **Index-coverage failure** | A chunk lacks a deterministic placeholder representation behind `EmbeddingProvider` | `docs/MILESTONE_1A.md` build item 2; `docs/altm.md` Index failure mode | **Blocked** — no Index Layer, no `EmbeddingProvider` implementation |

### 8.2 Explicitly **not** DQV failure classes

| Not a DQV class | Owner | Evidence |
|---|---|---|
| Construction input failures (unreadable corpus item, unsupported extension, escaping source, malformed Manifest entry) | Construction — `DocumentConstructionError` | `docs/DOCUMENT_CONSTRUCTION_PLAN.md` §10.1; `ADR-P3.1.7.2-F2` |
| Manifest structural failures (missing/mistyped `manifest_version`, `documents`, or a required entry field) | Structural Artifact Validation — `ManifestValidationError` | `scripts/build_manifest.py` `validate_manifest` |
| Chunk structural/representation failures | Structural Artifact Validation — `ChunkValidationError` | `scripts/build_chunks.py` `validate_chunks` |
| Determinism failures | Executable Specification Suite (closed) | `docs/DOCUMENT_CONSTRUCTION_PLAN.md` §20.3 |
| **Blank `Document.text`** — empty, or containing no non-whitespace character | **Not a failure at all** — legal, and legally produces zero chunks | `docs/DOCUMENT_CONTRACT.md` §8.3 (Non-empty guarantee deliberately absent), invariant 2; `docs/CHUNK_CONTRACT.md` §11 (*"zero or more"*) |
| Retrieval, generation, or regression failures | Future Evaluation, Layers 2–4 | `docs/roadmap.md` §5 |

**Wording synchronized at Sprint 1B.1.** This row previously read *"Empty `Document.text`"*. Implementing DQ-6's Manifest-side coverage check required stating the zero-chunk condition exactly, and the Chunker's condition is slightly wider than *empty*: `sample_rag/chunker.py` `detect_structural_boundaries` returns `[]` for **any** text with no non-whitespace run, because `_strip_span` discards whitespace-only spans — which `docs/CHUNK_CONTRACT.md` §17 invariant 1 (*non-empty*) requires it to do.

**This is a wording synchronization, not a scope change.** The row's classification is unchanged — still *not* a DQV failure class, still owned by nobody as a failure, still resting on the same two contract citations. No validation rule is added, no acceptance criterion in §13 or §14 is altered, and no failure class in §8.1 gains or loses a case. The row is widened to describe the behaviour the repository already had; had it been read literally, a whitespace-only corpus document would have been reported as a defect against legal repository state.

### 8.3 A note on DQ-3, so it is not implemented as a false positive

DQ-3 asserts corpus/Manifest agreement. Under Construction's accepted asymmetry (`docs/DOCUMENT_CONSTRUCTION_PLAN.md` §20.3), the **opposite** direction — a Manifest entry whose file is absent — already **raises** at Construction time. DQV must therefore assert only the narrowing direction (file present, entry absent); asserting the other direction would duplicate a Construction responsibility and violate §6's single-owner rule.

### 8.4 Reporting model

The reporting model is fixed by DQV being a pytest suite (P2), and it **diverges deliberately** from the repository's `validate_*` fail-fast precedent. The divergence is stated rather than inherited by accident:

| Property | `validate_manifest` / `validate_chunks` | DQV |
|---|---|---|
| Granularity | One function, fail-fast on the first violation | One test per check family; pytest reports **every** failing family in one run |
| Mechanism | Raises a dedicated `Exception` subclass | pytest assertion |
| Why the difference | A validator is called by a build script that must stop | A diagnostic layer's value is a complete picture of corpus health; pytest's native batch reporting supplies it at zero cost |
| What is preserved | Read-only, no repair, no mutation (P8); deterministic (P7); one clear message naming the offending entry | Identical |

**Within a single test, fail-fast still applies** — the first failing assertion ends that test, matching the precedent's discipline at the granularity where it makes sense.

**No new exception type is introduced.** The repository's flat exception pattern (`docs/DOCUMENT_CONSTRUCTION_PLAN.md` §10.2) exists for *raising* components; DQV asserts rather than raises, so no `DataQualityValidationError` is warranted. Introducing one would create a repository-wide concept without evidence — the bar `ADR-0001` set and declined to cross. **Recommendation, not a decision** (§16, open item O-3).

---

## 9. Contract Analysis

**Phase 4.** Every contract statement bearing on Data Quality Validation, reviewed for whether architectural clarification is required before runtime implementation.

### 9.1 Statement-by-statement review

| Contract statement | Bearing on DQV | Clarification required before implementation? |
|---|---|---|
| §8.2 — `Document` is `id: str`, `text: str` | Fixes what DQV may assert about a `Document` | **No.** Frozen and approved |
| §8.3 — *"`id` is a `str` and **is unique across the corpus**, reusing the identity already frozen for `knowledge_manifest.json` `documents[].id`"* | The **only** contract statement of uniqueness. It is the invariant a DQ-2 check would enforce | **YES — this is D-2.** See §9.2 |
| §8.3 — Content guarantee (determinism) | Already specified by the suite; DQV must not duplicate | **No.** Closed (§6.1 row 10) |
| §8.3 — Non-empty guarantee deliberately absent | Empty `text` is legal; DQV must not assert non-emptiness | **No.** Explicit in the contract |
| §8.4 — `id` **must equal** the Manifest `documents[].id`; no second identity scheme | Under S1, `Document.id` *is* the manifest value, read unchanged | **No.** Frozen; implemented and specified |
| §8.5 — Referential integrity *"is **not** part of this structural contract … Deferred to the … Data Quality Validation pytest layer"* | Directly assigns DQ-4 to DQV | **No.** The deferral is explicit and its venue is named |
| §8.5 — `Document` → Manifest entry is one-to-one via `id`; `Document` → `Chunk` is one-to-many | The cardinality DQ-4 asserts | **No.** Frozen |
| §8.7 — Invariants 1–3, *"all must hold for **every conforming Document**"* | Per-instance scope. **Uniqueness is absent** | **YES — this is D-2.** See §9.2 |
| §8.8 item 1 — invariant 3 is not checkable from a single artifact | Keeps determinism out of DQV | **No.** Recorded and closed |
| §8.8 item 2 — `documents[].hash` covers source **bytes**, not extracted text | Bounds what DQ-1 can claim: it detects *source* drift, never *extraction-mechanism* drift | **No** — but it must be **stated in the DQ-1 check's own documentation**, or DQ-1 will be over-read as a guarantee about `Document.text`. Recorded as an implementation requirement (§11, W3) |
| `docs/MILESTONE_1A.md` build item 1 — `documents[].id`: *"**Unique** identifier for the document within the manifest"* | An **independent** statement of uniqueness, in the Manifest contract, at manifest scope | **No** — and it is the decisive evidence for §10's recommended direction |
| `docs/CHUNK_CONTRACT.md` §11 / §17 inv. 3 | DQ-6, blocked pending `chunks.json` | **No.** Blocked, not ambiguous |

**Result: exactly one contract statement pair requires clarification before runtime implementation — §8.3 vs. §8.7 (D-2).** Every other statement is either frozen and unambiguous, or explicitly deferred to a named venue.

### 9.2 D-2 — the inconsistency, stated precisely

**The two statements, quoted:**

> §8.3, Identity guarantee: *"`id` is a `str` and **is unique across the corpus**, reusing the identity already frozen for `knowledge_manifest.json` `documents[].id` … rather than establishing a second identity scheme for the same underlying document."*

> §8.7, Invariants — *"proposed, **all must hold for every conforming Document**"*:
> 1. *"`id` is a `str` and equals the corresponding `knowledge_manifest.json` `documents[].id` entry."*
> 2. *"`text` is a `str` (may be empty …)."*
> 3. *"Identical source content, extracted by an identical mechanism, produces an identical `text` value (determinism)."*
>
> *"**No fields beyond these two exist in this version of the contract.**"*

**The inconsistency:** §8.3 asserts a guarantee that §8.7 — the contract's own consolidated, authoritative invariant list — does not encode. `docs/P3.1.7_Independent_Implementation_Review_ClaudeCode.md` (D-2, MAJOR) states the consequence: *"The contract simultaneously guarantees and does not guarantee uniqueness; both the implementation and F-1's deferral rely on the weaker reading. Any future consumer keying by `Document.id` may rely on the stronger one."* Independently verified at Sprint P3.1.7.1.

**Why it blocks P3.1.8.1 specifically.** `docs/ENGINEERING_TRACEABILITY_REGISTER.md` §3.5 states the requirement directly: reconcile *"before implementing a uniqueness check, so the check enforces a stated invariant rather than inventing one"* (P11). A DQ-2 check written today would have to pick a reading, and picking silently is exactly what the register forbids.

**A structural observation that bears on the resolution — and is evidence, not preference.** §8.7's invariants are introduced as holding *"for every conforming Document"* — a **per-instance** scope. Uniqueness is not a property of any single `Document`; it is undecidable from one. It therefore cannot be added to §8.7 as "invariant 4" without changing the stated scope of that list. This is the same structural limit §8.8 item 1 already records for invariant 3 (*"not checkable from any single artifact"*), and the same limit `docs/CHUNK_VALIDATION_PLAN.md` §P0.2 identified when it classified Chunk invariant 7 (`id` unique across the corpus) as a **Collection** invariant rather than a Field or Relational one.

**A second observation, from the implementation.** Under identity strategy S1, `sample_rag/knowledge_source.py` `load()` reads `entry["id"]` and passes it through unchanged. Therefore *`Document.id` uniqueness across `load()`* and *`documents[].id` uniqueness across the Manifest* are the **same predicate** on the current implementation — a duplicate `Document.id` is possible if and only if the Manifest contains a duplicate `documents[].id`. This is what makes the eventual check mechanical once D-2 is resolved, and it is why §10 recommends the direction it does.

---

## 10. Governance Recommendation for D-2

**Deliverable 9.** The sprint brief requires a recommendation with justification, and explicitly instructs that an ADR must not be assumed. This section evaluates the available mechanisms against repository evidence and recommends one. It creates nothing.

### 10.1 Identified inconsistency

Restated for the record: `docs/DOCUMENT_CONTRACT.md` §8.3 states `Document.id` *"is unique across the corpus"*; §8.7 — the contract's consolidated invariant list, declared complete (*"No fields beyond these two exist in this version of the contract"*) — omits uniqueness. The runtime implementation follows the weaker reading. Verified independently at Sprint P3.1.7.1; recorded at `docs/ENGINEERING_TRACEABILITY_REGISTER.md` §3.5.

### 10.2 Mechanisms evaluated

| Mechanism | Assessment | Repository evidence |
|---|---|---|
| **(a) Narrowly scoped contract erratum** to `docs/DOCUMENT_CONTRACT.md` | **RECOMMENDED.** The defect is *within one document's own text*, and the contract is the artifact that must state the invariant a DQ-2 check enforces | `docs/MILESTONE_1A.md` Definition of Done authorizes exactly this route: *"All public contracts remain unchanged … **unless a documented contract gap is discovered and explicitly approved**."* D-2 is a documented, independently verified contract gap. `docs/DOCUMENT_CONSTRUCTION_PLAN.md` §20.2 already names this mechanism by name for the analogous §8.2 wording question: *"a separate governance action (**a contract erratum**)."* `docs/P3.1.7_Independent_Implementation_Review_ClaudeCode.md` D-2 recommends the same: *"Reconcile in a contract erratum … **Do not resolve it silently in code**"* |
| **(b) An ADR** establishing the authoritative interpretation | **NOT RECOMMENDED — and not required.** An ADR answers an architectural-boundary or ownership question. D-2's ownership question is **already answered**: `ADR-P3.1.7.2-F2`'s accepted rationale assigns *"duplicate identifiers, uniqueness"* to Data Quality Validation, verbatim. Writing an ADR would re-decide a decision the repository owner has already made | `docs/DOCUMENT_CONSTRUCTION_PLAN.md` §12.3 step 2: *"Not an ADR: `docs/adr/ADR-0001` established that ADRs are reserved for **architectural-boundary questions**."* `docs/DOCUMENT_CONTRACT_REVIEW.md` classified none of the contract's Outstanding Questions as requiring an ADR. `ADR-P3.1.7.2-F2` exists because a boundary was *genuinely disputed* between two independent reviews — D-2 is not disputed; both reviews and the Decision Gate agree on what it is and where it goes |
| **(c) A `docs/roadmap.md` §7 scope decision** | **NOT APPLICABLE.** That venue is designated for **dependency and scope** decisions | `docs/roadmap.md` §7; `docs/DOCUMENT_CONSTRUCTION_PLAN.md` §12.3 step 2. No dependency or scope change is involved |
| **(d) A row in `docs/ENGINEERING_TRACEABILITY_REGISTER.md`** | **NOT SUFFICIENT ALONE.** The register is explicitly **retrospective**: *"Entries are added only after a disposition has been established."* It records the resolution; it cannot *be* the resolution | Register §1.2, §8 |
| **(e) Resolve it in the DQV implementation** | **REJECTED.** Directly contrary to P11 and to the review's instruction not to resolve it silently in code | Register §3.5; review D-2 |
| **(f) Leave it, and have DQ-2 cite §8.3 as-is** | **REJECTED.** It leaves P3.1.8.1 enforcing a guarantee the contract's own authoritative invariant list contradicts — precisely the ambiguity the sprint brief requires P3.1.8.1 not to inherit | Register §3.5; sprint brief, Phase 4 |

### 10.3 Recommendation

> **A narrowly scoped contract erratum to `docs/DOCUMENT_CONTRACT.md`, authored and approved by the repository owner as a standalone governance pass, before any DQ-2 uniqueness check is implemented. No ADR is required.**

**Recommended shape of that erratum** (its content is the owner's decision; this is the evidence-supported direction, per the standing rule that a recommendation is not a decision):

1. **Resolve in favour of the manifest-derived reading.** Record that `Document.id` uniqueness is **inherited from the Knowledge Manifest**, whose own frozen contract already states it — `docs/MILESTONE_1A.md` build item 1: *"`documents[].id` — **Unique** identifier for the document within the manifest."* This is not a new guarantee; it is the guarantee §8.3 was already pointing at when it said *"reusing the identity already frozen for `knowledge_manifest.json` `documents[].id` … rather than establishing a second identity scheme."*
2. **Record that uniqueness is corpus-scoped, not instance-scoped**, and therefore correctly absent from §8.7's per-instance invariant list — resolving the apparent contradiction as a **scope** distinction rather than a disagreement (§9.2).
3. **Record the enforcement owner explicitly: Data Quality Validation**, citing `docs/DOCUMENT_CONTRACT.md` §8.5 and `ADR-P3.1.7.2-F2`'s accepted rationale. After the erratum, DQ-2 enforces a stated invariant (P11 satisfied).
4. **Follow the §8.8 precedent for form.** Sprint P2.5.1 added §8.8 *"adjacent to, and without modifying, Section 8.7"*, keeping §8.2–§8.7 byte-for-byte frozen, and recorded the pass in a Correction Record. An erratum in the same shape resolves D-2 while preserving the frozen schema range — the repository's established way of recording a correction rather than silently applying one (`docs/MILESTONE_1A.md` build item 1's *"Contract Change — `created_at` removed"* note is the original precedent).

**Why direction (1) rather than promoting uniqueness to a fourth §8.7 invariant:**

| | Manifest-derived (recommended) | Promote to §8.7 invariant 4 |
|---|---|---|
| Scope coherence | Preserves §8.7's stated per-instance scope | Breaks it — uniqueness is undecidable from one `Document` (§9.2) |
| Frozen range | §8.2–§8.7 stay byte-for-byte unchanged, as at P2.5.1 | Edits the deliberately frozen schema range |
| Consistency with §8.4 | Reinforces *"no second identity scheme"* — uniqueness comes from where identity comes from | Creates a `Document`-level guarantee independent of its source |
| Consistency with the accepted ADR | Matches *"cross-artifact repository properties such as duplicate identifiers, uniqueness"* → DQV | Implies a per-`Document` structural invariant, pulling uniqueness toward Construction |
| Implementation consequence | DQ-2 asserts manifest uniqueness; `Document.id` uniqueness follows as a theorem under S1 (§9.2) | Would imply Construction should raise on a duplicate — reopening a closed layer, contrary to P10 |
| Repository precedent | `docs/CHUNK_VALIDATION_PLAN.md` §P0.2/§P3 classify corpus-wide `id` uniqueness as a **Collection** invariant, never a Field one | No precedent |

### 10.4 Supporting repository evidence, consolidated

- `docs/MILESTONE_1A.md`, Definition of Done — authorizes a documented, explicitly approved contract change (the governance route).
- `docs/MILESTONE_1A.md` build item 1 — `documents[].id` is already contractually *"Unique … within the manifest"* (the substance).
- `docs/DOCUMENT_CONTRACT.md` §8.4 — identity is reused from the Manifest, not independently derived (why the manifest-derived reading is the natural one).
- `docs/DOCUMENT_CONTRACT.md` §8.5 — cross-artifact/semantic checks belong to DQV (the enforcement owner).
- `docs/DOCUMENT_CONTRACT.md` §8.8 + Correction Record — the precedent for an adjacent, non-destructive contract addition (the form).
- `ADR-P3.1.7.2-F2`, accepted rationale — *"duplicate identifiers, uniqueness"* → DQV (why no new ADR is needed).
- `docs/DOCUMENT_CONSTRUCTION_PLAN.md` §12.3 step 2 — ADRs are reserved for architectural-boundary questions (why an ADR is the wrong instrument).
- `docs/DOCUMENT_CONSTRUCTION_PLAN.md` §20.2 — names "a contract erratum" as the correct mechanism for an analogous contract-wording question.
- `docs/P3.1.7_Independent_Implementation_Review_ClaudeCode.md` D-2 — independently recommends a contract erratum and forbids silent code resolution.
- `docs/ENGINEERING_TRACEABILITY_REGISTER.md` §3.5 — reconcile before implementing the check.
- `scripts/build_manifest.py` `validate_manifest` — performs **no** uniqueness check today, so nothing in the repository currently enforces the Manifest's own stated uniqueness. The erratum makes explicit which layer will.

### 10.5 Implementation impact

| If the erratum lands as recommended | Consequence for Sprint P3.1.8.1 |
|---|---|
| Uniqueness is a **stated, corpus-scoped, manifest-derived** invariant | DQ-2 becomes mechanical: assert `documents[].id` values are pairwise distinct, and assert the same of `[d.id for d in load()]`. Both enforce a stated invariant (P11 satisfied) |
| §8.7 remains per-instance and byte-for-byte frozen | No contract re-freeze, no re-review of the schema, no impact on `sample_rag/document.py` or the 95 existing specifications |
| F-1 gains an approved behaviour to specify | `tests/conftest.py`'s standing note (*"The suite excludes only F-1 … it is not yet approved repository behaviour"*) and Register §7's *"Not specified, deliberately: identifier uniqueness (F-1 — not yet approved behaviour)"* both become closable **by P3.1.8.1**, in their own venues |
| Construction is untouched | P10 preserved. `sample_rag/knowledge_source.py` needs no change: a duplicate id is detected by DQV, not prevented by `load()` — consistent with the prevention/detection split (§5.2) |
| **If the owner instead chooses invariant 4** | P3.1.8.1's scope changes materially: uniqueness would become a per-`Document` structural invariant, likely reopening Construction and the frozen schema range. **This is why the erratum must precede implementation, not accompany it** |

---

## 11. Implementation Roadmap

**Phase 5.** The strategy Sprint P3.1.8.1 executes. Written so implementation is largely mechanical.

### 11.1 Runtime architecture

**There is no new runtime component.** DQV adds no module to `sample_rag/`, no function to `scripts/`, no CLI, and no exception type (§8.4). It is a pytest suite that reads existing artifacts and calls the existing public interface. This follows P6 and `docs/MILESTONE_1A.md` build item 1's *"No separate validation subsystem — this stays a file plus a check."*

**Placement — and the resolution of a recorded open question.** `docs/CHUNK_VALIDATION_PLAN.md` §P9 left open *"Whether the Data Quality Validation pytest layer … should itself live under `tests/` or a new `scripts/` entry point."* Repository evidence now answers it directly:

> `docs/architecture.md` §6 — **`tests/`** · *"pytest suite — **primarily Layer 1 (Data Quality) validation in Milestone 1A**."*

`evaluation/` is excluded by the same table: it holds *"one subdirectory per evaluation tool — `deepeval/`, `promptfoo/`, `ragas/`"*, and DQV uses none of the three (P2, and `docs/MILESTONE_1A.md` Out of Scope bars all three). A `scripts/` entry point is excluded because `scripts/` is *"not pipeline logic"* and, more directly, because §P9's question was about where a **pytest** layer lives. **Recommended:** `tests/test_data_quality.py`, alongside the existing four specification files. File naming and internal organisation are bounded implementation decisions for P3.1.8.1, exactly as `docs/DOCUMENT_CONSTRUCTION_PLAN.md` §15 treated *"Module organisation, file location, and naming."*

**Dependencies:** stdlib + pytest only (`json`, `hashlib`, `pathlib`, `collections`). No governance gate is triggered (P9; `docs/DOCUMENT_CONSTRUCTION_PLAN.md` §12.3 step 1 closes on the stdlib branch, as it did for Construction — Register §3.4, G-5).

**Reuse, not reimplementation.** DQV should call `scripts/build_manifest.py`'s `load_manifest`, `validate_manifest`, `compute_sha256`, and `normalize_source_path` rather than reimplementing them. This is available to `tests/` — `docs/architecture.md` §6's barrier separates `sample_rag/` (pipeline) from `scripts/`; it does not bar the test harness from importing either, and `conftest.py` already inserts the repository root on `sys.path`. **This is the reason DQV can do what Construction could not**: strategy S2 was rejected for Construction solely because a `sample_rag/` → `scripts/` import crosses the pipeline boundary (`docs/DOCUMENT_CONSTRUCTION_PLAN.md` §9.1). DQV is not pipeline code, so that objection does not apply — and reuse avoids the `SUPPORTED_EXTENSIONS`-style duplication Register §5 records as a **High** drift risk. *(Inference, labelled: no repository artifact states this explicitly; it follows from §6's directory responsibilities. Recorded as open item **O-4** in §16.)*

### 11.2 Implementation phases

| Phase | Work | Failure classes | Depends on | Gate |
|---|---|---|---|---|
| **W0** | **Governance.** The D-2 contract erratum is authored and approved (§10). Not P3.1.8.1's work to decide — its work to *wait for* | — | Repository owner | **Blocking for W2 only.** W1, W3–W5 may proceed without it |
| **W1** | **Manifest structural gate.** A specification asserting `validate_manifest(load_manifest())` succeeds against the committed Manifest. Closes the *"Validated by: one pytest suite"* gap for structure | — | Nothing | The repository's first-ever manifest specification |
| **W2** | **Collection integrity — F-1.** Assert `documents[].id` values are pairwise distinct; assert `[d.id for d in load()]` are pairwise distinct. Both predicates, since §9.2 shows they coincide under S1 — specifying both makes the coincidence a protected property rather than an assumption | **DQ-2** | **W0** | F-1 closable in the register |
| **W3** | **Freshness / integrity.** For each entry, assert `compute_sha256(resolved source) == documents[].hash`. Must document, in the test's own docstring, that this covers **source bytes only** and cannot detect extraction-mechanism drift (§8.8 item 2, §9.1) | **DQ-1** | Nothing | Closes `docs/MILESTONE_1A.md` build item 1's hash-comparison requirement and Architectural AC 3 |
| **W4** | **Completeness — Case A.** Enumerate `sample_rag/documents/**` filtered by `SUPPORTED_EXTENSIONS`, `sorted(...)`; assert every such file has a `documents[]` entry, comparing on `normalize_source_path`'s normalized form. Narrowing direction only (§8.3) | **DQ-3** | Nothing | Closes the Case A detector deferred by Construction Plan §20.3 |
| **W5** | **Referential integrity.** Assert every `Document.id` from `load()` has a corresponding `documents[]` entry, and that the correspondence is one-to-one (`docs/DOCUMENT_CONTRACT.md` §8.5) | **DQ-4** | Nothing | Closes A8 / §8.5's deferral for the `Document` side |
| **W6** | **Chunk-dependent checks — OUT OF SCOPE for P3.1.8.1** | DQ-5, DQ-6, DQ-7 | `chunks.json`, Index Layer, `EmbeddingProvider` — **none exists at HEAD** | Deferred to the Chunk/Index layers with owner recorded (§4.1) |

**Sequencing note.** W1 and W3–W5 depend on nothing and can be implemented immediately upon approval. Only **W2 is gated on the D-2 erratum**. If the owner wishes to begin P3.1.8.1 before the erratum is authored, P3.1.8.1 can deliver W1, W3, W4, W5 in full and land W2 in a follow-on pass — **but the sprint would then not close F-1**, which is its principal chartered finding. **Recommendation: author the erratum first.**

### 11.3 What P3.1.8.1 must not do

- Modify `sample_rag/knowledge_source.py`, `sample_rag/document.py`, `sample_rag/chunker.py`, `scripts/build_manifest.py`, or `scripts/build_chunks.py` (P8, P10)
- Add a uniqueness check to `validate_manifest()` (§5.3)
- Introduce a `DataQualityValidationError` or any new exception type (§8.4)
- Produce a `validated_corpus.json` or any DQV artifact (§7.2)
- Re-specify determinism, containment, normalization, ordering, or the failure surface — all already specified by the 95-specification suite (§6.1 row 10, §5.5)
- Assert a non-empty `Document.text` (§8.2)
- Resolve D-2 in code (P11, §10.2(e))
- Begin Chunk, Index, or Retrieval Layer work

---

## 12. Specification Strategy

DQV *is* specifications — there is no separate implementation to specify. The strategy therefore governs how the checks themselves are written, and it inherits the discipline the Knowledge Layer earned at Sprints P3.1.6–P3.1.7.2.

| Principle | Requirement for P3.1.8.1 | Precedent |
|---|---|---|
| **Claim-to-specification mapping** | Every check maps to exactly one named repository claim (a DQ-class, a contract section, or a register finding) and is recorded in `docs/ENGINEERING_TRACEABILITY_REGISTER.md` §7 | Register §7's existing A1–A16 / B2–B10 / AH-1…AH-9 mapping |
| **Behaviour, not artefacts** | No specification freezes a SHA-256 digest of one corpus snapshot, an absolute path, or a file count as a constant. DQ-1 compares two computed values; it does not assert a literal hash | `tests/conftest.py`: *"no specification here asserts a literal SHA-256 digest of `Document.text`, because a digest is a fact about one corpus snapshot"* |
| **Adequacy is measured, not asserted** | Sprint P3.1.8.1 must run a mutation pass over any code its checks protect and record the result. Register §6 exists precisely because *"an adequacy claim about a specification suite requires measurement"* | Register §4 (Recorded divergence), §6 (Standing caution: *"a surviving mutant is evidence of a blind spot; a killed mutant is not proof of adequacy"*) |
| **Synthetic + real corpus** | Each check is exercised against a **synthetic** corpus (the negative case — a duplicate id, a stale hash, an unmanifested file) and against the **real** committed corpus (the positive case) | `tests/conftest.py`'s `SyntheticCorpus`, `synthetic_corpus`, `real_manifest_entries`, `real_documents` fixtures — all already exist and are directly reusable |
| **No intentionally failing specification** | Every DQV check must pass at HEAD against the committed corpus. If a check would fail, that is a corpus or contract finding to disposition, not a red test to commit | `tests/conftest.py`: *"No intentionally failing specification exists"* |
| **Corpus-scale honesty** | The corpus is one document (§0). A uniqueness check over a one-entry manifest is vacuously true on the real corpus — so DQ-2's real protection comes from its **synthetic** duplicate case. This must be stated in the specification, not glossed | Register §6's equivalent-mutant analysis, which distinguished genuine blind spots from corpus artefacts (`body.iter` → `findall`: *"Equivalent mutant on the current corpus"*) |
| **I-6 caution** | Do not hardcode `Karthik_SR_Resume_v2_2.docx`. Register §3.5 already carries I-6 for this exact defect in an existing specification; a new layer must not repeat it | Register §3.5, I-6 |

---

## 13. Acceptance Criteria

Sprint P3.1.8.1 is acceptable when **all** of the following hold. Each is objectively checkable.

**Governance**
- [ ] The D-2 contract erratum exists, is approved by the repository owner, and is cited by the DQ-2 check (§10)
- [ ] No ADR was created, and none was needed (§10.2(b))
- [ ] `docs/ENGINEERING_TRACEABILITY_REGISTER.md` records F-1's closure and D-2's resolution, **after** the disposition was established (Register §1.2, §8)

**Implementation**
- [ ] DQ-1 through DQ-4 are implemented as pytest specifications; DQ-5 through DQ-7 are recorded as blocked with their blockers named (§8.1)
- [ ] No file under `sample_rag/` or `scripts/` was modified (§11.3)
- [ ] No new artifact is produced by the suite (§7.2)
- [ ] No new exception type, component, glossary term, directory, or dependency was introduced (§8.4, §11.1, P9)
- [ ] The suite is stdlib + pytest only; `requirements.txt` is unchanged (P9)

**Behaviour**
- [ ] Each check has a synthetic negative case **and** a real-corpus positive case (§12)
- [ ] Every check is deterministic: repeated runs and independent processes agree (P7)
- [ ] The full suite passes at HEAD: 95 existing specifications plus the new DQV specifications, with **zero** pre-existing specifications modified or skipped
- [ ] No specification asserts a literal digest, absolute path, or hardcoded corpus filename (§12)

**Evidence**
- [ ] A mutation pass over the checks is executed and its results recorded, with equivalent mutants distinguished from genuine survivors (§12; Register §6)
- [ ] Every new specification is mapped to a named claim in the register's §7 table (§12)

---

## 14. Completion Criteria — Design Completion Gate

**This sprint (P3.1.8.0)** is complete when all nine deliverables exist, the D-2 governance recommendation is justified against repository evidence, and every deferred finding has an assigned architectural owner. Assessed in §15–§16.

**Sprint P3.1.8.1** is complete — and with it the Milestone 1A Knowledge Layer — when:

1. Every §13 acceptance criterion is checked.
2. **F-1 is closed** in `docs/ENGINEERING_TRACEABILITY_REGISTER.md` §3.1, with the change that closed it — the last open finding raised against the Knowledge Layer.
3. **D-2 is closed** in §3.5, with the erratum that resolved it.
4. `docs/MILESTONE_1A.md` build item 1's *"Validated by: one pytest suite running hash comparison against the manifest"* is satisfied for the first time since Sprint P1.2.0, and Architectural AC 3 (*"`knowledge_manifest.json` … is the sole source of truth that freshness/hash validation checks against"*) is demonstrated rather than asserted.
5. The remaining DQV responsibilities (DQ-5, DQ-6, DQ-7) are recorded as **owned by DQV and blocked on the Chunk/Index layers**, so no future sprint rediscovers their ownership.
6. `tests/conftest.py`'s standing note that F-1 is *"not yet approved repository behaviour"* is updated in its own venue, mirroring how the F-2 note was updated at Sprint P3.1.7.2.

---

## 15. Implementation Readiness Assessment

**Deliverable 6.**

| Dimension | Assessment | Evidence |
|---|---|---|
| **Architectural responsibilities** | **Complete.** Thirteen responsibility types, thirteen single owners, seven potential collisions explicitly resolved | §6 |
| **Runtime boundaries** | **Unambiguous.** The Construction/DQV boundary follows a single accepted criterion (§5.1) applied uniformly; the DQV/Structural-Validation and DQV/Evaluation boundaries each rest on a quoted repository statement | §5.1, §5.3, §5.2 |
| **Deferred-finding ownership** | **Complete.** Every row of Register §3.5 and every "Still deferred" row of Construction Plan §20.3 has an assigned owner | §4.1, §4.2, §4.3 |
| **Contract clarity** | **One gap, identified and routed.** D-2 is the sole contract statement requiring clarification before implementation; a governance mechanism is recommended with evidence | §9.1, §10 |
| **Input availability** | **Available.** The Manifest, the corpus, and `load()` all exist and are exercised by the current suite. `chunks.json` does not exist — and every check that needs it is explicitly out of scope | §0, §7.2, §11.2 W6 |
| **Dependency governance** | **Not triggered.** stdlib + pytest only | P9, §11.1 |
| **Specification infrastructure** | **Already in place.** `SyntheticCorpus`, `synthetic_corpus`, `real_manifest_entries`, `real_documents` fixtures exist at HEAD and cover the negative and positive cases DQV needs | `tests/conftest.py` |
| **Corpus scale** | **A recorded limitation, not a blocker.** One document means DQ-2 and DQ-4 are vacuously true on the real corpus; synthetic cases carry the protection, and §12 requires this to be stated in the specifications rather than glossed | §0, §12 |
| **Blocking dependency on unresolved architecture** | **One, with a defined resolution path: D-2.** No other check depends on an open architectural question | §10, §16 |

**Verdict: READY, conditional on the D-2 erratum.** Sprint P3.1.8.1 can implement W1 and W3–W5 immediately upon approval, and W2 upon the erratum's approval.

---

## 16. Design Decision Gate Summary

**Deliverable 7.** Assessed against the four gate questions in the sprint brief, followed by every uncertainty this sprint could not close, recorded explicitly rather than resolved by assumption.

| Gate question | Answer | Basis |
|---|---|---|
| Are architectural responsibilities complete? | **Yes** | §6 — every responsibility type named by the brief is assigned to exactly one layer, each with cited evidence |
| Are runtime boundaries unambiguous? | **Yes** | §5 — one accepted criterion, applied uniformly; every collision resolved against named authority |
| Does every deferred finding have an assigned owner? | **Yes** | §4 — with an explicit completeness statement reconciling against Register §3.5 and Construction Plan §20.3 |
| Does any implementation depend on an unresolved architectural question? | **Yes — exactly one: D-2**, and only the DQ-2 check depends on it | §9.2, §11.2 W2 |

### 16.1 Recorded uncertainties

Recorded, not resolved. Each states its impact and what would close it.

| ID | Uncertainty | Impact on P3.1.8.1 | Closed by |
|---|---|---|---|
| **O-1** | **D-2 is unresolved.** The contract does not consistently state whether `Document.id` uniqueness is guaranteed | **Blocks W2 (DQ-2 / F-1) only.** W1, W3–W5 unaffected | The repository owner authoring/approving the erratum recommended in §10.3. **This is the one item that must close before P3.1.8.1 can complete its chartered purpose** |
| **O-2** | **The four-layer model** (§5.2) records a *Structural Artifact Validation* layer that repository evidence demonstrates in code but no document names as an architectural layer | None on the checks themselves. It affects how §6's matrix is read | Owner confirmation that recording the existing layer is acceptable, or an instruction to fold it into the three-layer sketch. **Inference, labelled as such** |
| **O-3** | **No `DataQualityValidationError`.** §8.4 recommends assertions over a new exception type, by analogy to `ADR-0001`'s evidence bar | Low. Reversible; affects only the checks' internal style | P3.1.8.1 recording the choice explicitly, as `docs/DOCUMENT_CONSTRUCTION_PLAN.md` §15 required for `DocumentConstructionError`'s name |
| **O-4** | **`tests/` → `scripts/` import for reuse** (§11.1) is not explicitly sanctioned by any repository artifact; it follows from `docs/architecture.md` §6's directory responsibilities | Low, but it determines whether DQV reuses `compute_sha256`/`normalize_source_path` or duplicates them — and Register §5 rates duplication a **High** drift risk | P3.1.8.1 recording the choice with rationale. **Inference, labelled as such** |
| **O-5** | **Corpus scale.** With one document, DQ-2 and DQ-4 are vacuously true on the real corpus | Bounded and disclosed. Protection comes from synthetic cases; §12 requires the limitation to be stated in the specifications | Corpus expansion — which is also the trigger for Contract Outstanding Question 1 and for re-verifying I-6 |
| **O-6** | **DQ-5, DQ-6, DQ-7 are unimplementable** — `chunks.json`, the Index Layer, and `EmbeddingProvider` do not exist | None. Explicitly out of scope, with owner and blocker recorded | The Chunk and Index layers. Ownership is settled now so it is not rediscovered later. **Owning milestone: Milestone 1B** — recorded at Sprint P3.7.4 |

> **O-5 and O-6 — owning milestone recorded, Sprint P3.7.4.** Added under authorization **A7** of `docs/P3.7.3_Repository_Owner_Constitutional_Decision.md`. **Ownership is unchanged (DQV), and the recorded blockers are unchanged.** This adds the milestone in which each item is scheduled, and nothing else.
>
> | Item | Owning milestone | Register id | Status of the recorded blocker |
> |---|---|---|---|
> | **O-5** — DQ-2 and DQ-4 vacuously true at corpus scale 1 | Milestone 1B | **1B-13** | Unchanged. Trigger is corpus expansion, which is register **1B-05** / **1B-06** |
> | **O-6 / DQ-5** — chunk validity as a corpus property | Milestone 1B | **1B-08** | **Cleared.** `chunks.json` did not exist when W6 was scoped; it exists at commit `180dcdc`, digest `323723b4fe82`. The check remains unimplemented |
> | **O-6 / DQ-6** — chunk referential integrity, incl. Chunk invariant 3's full form | Milestone 1B | **1B-09** | **Cleared**, same artifact. The check remains unimplemented |
> | **O-6 / DQ-7** — index coverage | Milestone 1B | **1B-10** | **Not cleared.** The Index Layer and `EmbeddingProvider` still do not exist; both are register **1B-01** / **1B-03**, in the same milestone |
>
> Canonical authority for all four: `docs/DEFERRED_ITEMS_REGISTER.md`. §8.1, §11.2 W6 and §13 of this plan are unchanged.

> **O-6 — closed at Sprint 1B.2.** Appended, leaving the P3.7.4 note above intact: that note recorded the status accurately when written, and this records what changed since.
>
> | Item | Register id | Status |
> |---|---|---|
> | **O-6 / DQ-5** — chunk validity as a corpus property | **1B-08** | ✅ **Implemented** at Sprint 1B.1, commit `f4544bf` — `tests/test_data_quality.py` |
> | **O-6 / DQ-6** — chunk referential integrity, incl. Chunk invariant 3's full form | **1B-09** | ✅ **Implemented** at Sprint 1B.1, commit `f4544bf` — `tests/test_data_quality.py` |
> | **O-6 / DQ-7** — index coverage | **1B-10** | ✅ **Implemented** at Sprint 1B.2. Its recorded blocker — *"the Index Layer and `EmbeddingProvider` still do not exist"* — cleared in the same sprint at register **1B-03** (`sample_rag/indexer.py`) and **1B-01** (`sample_rag/embedding.py`) |
>
> **O-6 is discharged: no DQV failure class in §8.1 remains unimplemented.** O-5 (**1B-13**) is unaffected by this note and remains as the P3.7.4 note records it.
>
> §8.1's *Status at P3.1.8.1* column, §11.2's W6 row and §13 are **not** amended: each is explicitly scoped to Sprint P3.1.8.1 and states that sprint's position accurately.

**Gate verdict: PASS with one blocking governance item (O-1).** The architecture is complete and the boundaries are unambiguous. Sprint P3.1.8.1 must not begin the DQ-2 uniqueness check until the D-2 erratum is approved; the remaining work is unblocked. **Implementation may begin only after repository owner approval** of this plan and of the §10 governance recommendation.

---

## 17. Implementation Baseline Recommendation

**Deliverable 8.** A recommendation only. No commit, tag, or history change is created by this document.

**Recommendation: adopt commit `68a412fbe1b31dc42a901ed8800fcc64fcf64b9b` as the implementation baseline for Sprint P3.1.8.1 — plus the approved D-2 erratum commit, which should land on top of it before any DQ-2 work begins.**

**Why this commit qualifies:**

| Criterion | Evidence at `68a412f` |
|---|---|
| Independently verified | §0 — clean tree, matching HEAD, 95 passing specifications, verified this sprint from the repository, not from a report |
| Construction is complete and closed | `docs/DOCUMENT_CONSTRUCTION_PLAN.md` §20.3 — every decision deferred to Sprint P3.1 is closed |
| The disputed boundary is settled | `ADR-P3.1.7.2-F2` accepted; F-2 closed; the accepted rationale supplies the criterion this plan reuses (§5.1) |
| Assurance is measured, not asserted | Register §6 — mutation baseline recorded, equivalent mutants distinguished, 100% line coverage on both Knowledge Layer runtime modules |
| The engineering record is durable | `docs/ENGINEERING_TRACEABILITY_REGISTER.md` exists and holds every finding, disposition, and claim-to-specification mapping |
| Specification infrastructure is reusable | `tests/conftest.py`'s synthetic and real-corpus fixtures already cover the cases DQV needs (§12) |
| One open finding remains, and it is this sprint family's charter | F-1, with D-2 attached — precisely what P3.1.8.1 exists to close |

**Why the erratum commit must precede DQ-2:** implementing a uniqueness check against an unresolved contract would enforce an invented invariant, which P11 and Register §3.5 both forbid, and would leave P3.1.8.1 inheriting the ambiguity the sprint brief requires it not to inherit.

**Not recommended, and not performed:** creating a tag. The repository has no tagging precedent — baselines are identified by commit SHA throughout (`5b903db`, `994f7b1`, `8839802`, `74d4ba3` are all cited by SHA in existing artifacts). Introducing tagging would be a new repository practice without evidence.

---

## 18. Explicitly Out of Scope

This document does not, and must not be read to:

- implement runtime validation, create any executable specification, or write any pytest test;
- create a validation module, modify runtime code, or modify any file under `sample_rag/` or `scripts/`;
- modify `docs/DOCUMENT_CONTRACT.md`, `docs/DOCUMENT_CONSTRUCTION_PLAN.md`, `docs/ENGINEERING_TRACEABILITY_REGISTER.md`, or any ADR;
- create an ADR, a contract erratum, a glossary term, a component, an interface, a pipeline stage, or a directory;
- decide D-2 — it recommends a mechanism and a direction; the decision is the repository owner's;
- begin Chunk Layer, Index Layer, or Retrieval Layer work;
- create any commit or tag;
- reopen text-extraction ownership, corpus-root containment, identity strategy S1, normalization rules N1–N5, list ordering, or determinism verification — all closed;
- resolve `docs/DOCUMENT_CONTRACT.md` Outstanding Questions 1, 3, or 4.

---

## 19. Design Readiness Checklist

| Deliverable | Where satisfied |
|---|---|
| 1. `DATA_QUALITY_VALIDATION_PLAN.md` — purpose, scope, principles, responsibilities, lifecycle, pipeline diagram, responsibility matrix, failure taxonomy, roadmap, specification strategy, acceptance criteria, completion criteria | This document, §1–§14 |
| 2. Repository Evidence Inventory | §4 |
| 3. Boundary Analysis | §5 |
| 4. Responsibility Matrix | §6 |
| 5. Validation Pipeline | §7 |
| 6. Implementation Readiness Assessment | §15 |
| 7. Design Decision Gate Summary | §16 |
| 8. Implementation Baseline Recommendation | §17 |
| 9. Governance Recommendation for D-2 | §10 (inconsistency §10.1, mechanism §10.2–§10.3, evidence §10.4, impact §10.5) |

| Engineering principle | Where honoured |
|---|---|
| Every recommendation supported by repository evidence | Every table row cites a file, section, commit, or measurement |
| Evidence distinguished from inference | O-2, O-4, and §5.4's classification are labelled **Inference**; everything else is quoted or cited |
| Separation of responsibilities preserved | §6 — one owner per responsibility, seven collisions resolved |
| No implementation before architecture | §18 — no code, no specification, no artifact created |
| Deterministic behaviour preserved | P7, §7.5, §13 |
| Architectural uncertainty recorded rather than assumed away | §16.1 — six recorded uncertainties, one blocking, each with a closing condition |

---

## Stop Condition

Per the sprint's governing instruction, this document ends here.

No runtime validation has been implemented. No executable specification, pytest test, validation module, or runtime code has been created or modified. `docs/DOCUMENT_CONTRACT.md`, `docs/DOCUMENT_CONSTRUCTION_PLAN.md`, `docs/ENGINEERING_TRACEABILITY_REGISTER.md`, `docs/adr/`, and every file under `sample_rag/`, `scripts/`, and `tests/` are unchanged. No ADR and no erratum has been created. No commit and no tag has been made.

This document is a design proposal. **Sprint P3.1.8.1 (Data Quality Validation Implementation) must not begin until the repository owner approves this plan and the D-2 governance recommendation in §10.**
