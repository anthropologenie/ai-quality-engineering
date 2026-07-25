# Chunk Validation — Implementation Plan

**Repository:** `ai-quality-engineering`
**Status:** Planning (Construction Readiness Review — Sprint P2.4.0)
**Related documents:** `docs/CHUNK_CONTRACT.md` (frozen v1.0 — the only source of Chunk field/invariant truth), `docs/adr/ADR-0001-chunk-persistent-representation.md` (persistent container decision), `docs/CHUNK_SERIALIZATION_PLAN.md` (serializer responsibilities and container shape — frozen input to this plan), `docs/architecture.md` (§5 Component Architecture, §6 Repository Structure), `docs/MILESTONE_1A.md` (build item 2, Data Quality Validation), `docs/altm.md` (line 189, Chunk coverage check), `docs/glossary.md` (Evaluation vs. Validation), `scripts/build_manifest.py` (`validate_manifest` — the repository's only existing structural-validation precedent), `sample_rag/chunker.py` (Chunk Construction, defensive invariant enforcement), `scripts/build_chunks.py` (Chunk Serialization, Sprint P2.3.2)

This document plans **how** the already-frozen Chunk Contract (`docs/CHUNK_CONTRACT.md`) is validated against a persisted Chunk collection (`sample_rag/chunks.json`, per `docs/CHUNK_SERIALIZATION_PLAN.md`). It does not define what a Chunk is (unchanged), does not modify Construction or Serialization, and does not implement validation. It is a planning artifact only, per the governing sprint instruction.

---

## Terminology Note

No new repository-wide terminology is introduced. "Validation," "invariant," and "structural" are used descriptively, in the same sense `docs/glossary.md`'s Evaluation-vs-Validation entry and `scripts/build_manifest.py`'s `validate_manifest` already use them. "Field Invariant," "Relational Invariant," "Collection Invariant," "Representation Invariant," and "Layer 1/2/3" are this document's own working vocabulary for organizing Contract §17's invariant list (per P0/P3 below) — they are planning-scoping terms, not proposed glossary entries, exactly as `docs/CHUNK_SERIALIZATION_PLAN.md` treated "container" and "schema version."

---

## P0 — Repository Validation Precedent Review

### P0.1 `validate_manifest()` — structure, scope, and pattern

`scripts/build_manifest.py`'s `validate_manifest(manifest: Mapping) -> Mapping` is the repository's only existing example of structural validation for a Persistent Canonical Artifact:

| Property | Behavior |
|---|---|
| Signature | Accepts any already-loaded `Mapping` — a real file via `load_manifest()`, a test fixture, or a synthetic malformed dict. Never touches the filesystem itself. |
| Structure | One flat function. Two top-level checks (`manifest_version` presence/type/value, `documents` presence/type), then a single `for index, entry in enumerate(documents)` loop checking per-entry shape (`Mapping`) and per-field presence/type against `REQUIRED_DOCUMENT_FIELDS`. |
| Scope | Structural only: field presence and type. No cross-entry checks (e.g., `validate_manifest` does not check `documents[].id` uniqueness, despite `id` being a repository-wide identity field per Chunk Contract §10's own citation of Manifest precedent). No cross-artifact checks (does not verify the cataloged `source` paths exist on disk, or that `hash` matches file content — that is a separate concern). |
| Exception pattern | A single dedicated exception, `ManifestValidationError`, direct subclass of `Exception`. Raised **fail-fast** — the first violation encountered raises immediately; violations are not accumulated or reported as a batch. |
| Return | Returns the same `Mapping` object unchanged on success — read-only, no mutation, no copying, no repair. |
| Semantic/cross-artifact scope | Explicitly out of scope for this function. Its own docstring: *"Semantic validation is a later milestone."* Confirmed by `docs/MILESTONE_1A.md` build item 2, which separates **structural** validation (this function, embedded in the artifact's own assemble/serialize/validate module) from **Data Quality Validation** (`resume validation, chunk validation, metadata validation, Index Coverage Validation` — a distinct pytest suite, Layer 1, per `docs/glossary.md`'s Evaluation-vs-Validation entry: *"Checking the inputs to the pipeline are trustworthy before anything is built on them"*). |
| Test coverage | None exists (`tests/` contains `test_chunker.py` only — no `test_build_manifest.py`). Repository fact, not a judgment: the precedent itself has never been independently test-hardened. |

### P0.2 Comparison against the Chunk Contract's invariant set

`docs/CHUNK_CONTRACT.md` §17 freezes eight invariants for a conforming Chunk (or Chunk sequence). Checking each against what `validate_manifest()`'s pattern actually covers (field presence/type only, no cross-entry, no cross-artifact):

| # | Contract §17 invariant | Scope | Covered by the flat, field-only pattern `validate_manifest()` uses? |
|---|---|---|---|
| 1 | `character_end > character_start` | Single chunk, two fields | No — `validate_manifest()` has no relational (cross-field) check anywhere; Manifest's four fields have no such relationship to check. |
| 2 | `len(text) == character_end - character_start` | Single chunk, two+ fields | No — same reason. |
| 3 | `text == document_text[character_start:character_end]` | Single chunk, cross-artifact (needs `Document`) | No — and, per P1.3 below, not checkable at all from the persisted collection. |
| 4 | `chunk_index` contiguous `0..N-1` per `document_id` | Across chunks sharing a `document_id` | No — `validate_manifest()` performs no cross-entry checks of any kind. |
| 5 | Ascending `chunk_index` matches ascending `character_start` | Across chunks sharing a `document_id` | No — same reason. |
| 6 | No overlap between adjacent chunks | Across chunks sharing a `document_id` | No — same reason. |
| 7 | `id` unique across the corpus | Across **all** chunks | No — `validate_manifest()` doesn't even check `documents[].id` uniqueness, the closest analog it has. |
| 8 | Identical `Document` + algorithm ⇒ identical `Chunk` sequence (determinism) | Across construction runs, not a static-artifact property | No — not a property any single-artifact validator can check (see P1.4). |

**Finding:** five of eight Contract invariants (4–8, minus the non-checkable determinism invariant, leaves 4, 5, 6, 7) are **cross-entry (collection-scoped)** checks that `validate_manifest()`'s flat, per-entry-only pattern has no precedent for at all — not because Manifest validation chose not to do them, but because the Knowledge Manifest contract never froze a cross-entry invariant to check in the first place (`documents[]` entries have no declared ordering or relational constraint among themselves). Two more (1, 2) are **relational (cross-field, single-entity)** checks, which the Manifest's four independent, unrelated fields (`id`, `source`, `hash`, `indexed`) never needed either.

This is the decisive, evidence-based distinction: **the richer structure comes from the Contract itself (§17), not from a design preference of this planning sprint.** `validate_manifest()`'s flat pattern is not insufficient by taste — it is scoped to a contract (Knowledge Manifest) that never had cross-field or cross-entry invariants to check. Chunk's contract does.

### P0.3 Option A vs. Option B — explicit resolution

**Option A (reuse the flat pattern as-is) is rejected.** A single flat loop, styled exactly like `validate_manifest()`'s, cannot express invariants 4–7 without either (a) silently becoming a second, ad hoc pass bolted onto the same function with no organizing structure, or (b) checking them in the same per-entry loop using cross-entry state smuggled in via closures/lookups — both of which obscure, rather than reflect, the fact that these are a genuinely different *kind* of check (collection-scoped vs. entity-scoped) than anything `validate_manifest()` ever had to represent.

**Option B (categorized/layered) is adopted, narrowly.** The categorization is not invented — it falls directly out of the scopes already visible in Contract §17's own invariant list (Section 0.2's table): single-field, single-chunk-relational, multi-chunk-same-document, and corpus-wide. A fifth scope — the persisted **container** shape (`schema_version`, `chunks` key) — is required for the identical structural reason `validate_manifest()` itself checks `manifest_version` and `documents` before it ever looks at an entry: Chunk Validation operates on `sample_rag/chunks.json`'s container (`docs/CHUNK_SERIALIZATION_PLAN.md` §P2.1), not on a bare list of chunks.

This resolves the sprint's own P0 gate: taxonomy and layering are used below (P3, P4, P4.5) **because** the Contract's invariant set spans qualitatively different scopes that the Manifest precedent never had to distinguish — not as an independent architectural preference.

---

## P1 — Validation Responsibilities

Per the sprint's own framing and `docs/glossary.md`'s Evaluation-vs-Validation distinction, Chunk Validation answers exactly one question:

> **Does this persisted Chunk collection comply with the frozen Chunk Contract?**

### P1.1 Explicit non-responsibilities

Validation must never:

- **Construct data** — `sample_rag/chunker.py`'s `Chunker.chunk()` and `_check_invariants()` own construction-time enforcement. Validation re-checks the persisted artifact independently of however it was produced (see P7.2 on why this duplication is intentional, not redundant).
- **Repair data** — mirrors `validate_manifest()`'s read-only contract exactly: no mutation, no normalization, no silent coercion.
- **Serialize data** — `scripts/build_chunks.py`'s `serialize_chunk`/`assemble_chunk_collection`/`write_chunks` own this. Validation consumes their output; it does not produce it.
- **Read documents** — no `.docx`/text extraction, no `Document`/`KnowledgeSource` dependency. This is both a scope boundary and, per P1.3 below, a hard capability limit (no `Document` representation exists to read).
- **Orchestrate the pipeline** — no CLI wiring, no multi-artifact build sequencing. That is a forward dependency (P8).

### P1.2 Boundary from Construction

`sample_rag/chunker.py`'s `_check_invariants()` already enforces invariants 1, 2, 4, 6, 7 (non-empty, length/offset consistency, contiguous `chunk_index`, non-overlap, corpus-wide-shaped `id` uniqueness within one construction call) — defensively, at construction time, aborting `Chunker.chunk()` on violation. Its own docstring is explicit that this is **not** a substitute for P2.4: *"This is defensive invariant enforcement scoped to the chunks a single `chunk()` call just built — it is NOT a replacement for the standalone Chunk Validation component."* Chunk Validation re-checks the same invariant *set* independently, against the artifact **as persisted on disk**, which may have been produced by a different Chunker revision, hand-edited, or corrupted in transit — Validation's job is to check the artifact, not to trust its provenance.

### P1.3 Boundary from Serialization

`scripts/build_chunks.py` (`docs/CHUNK_SERIALIZATION_PLAN.md`) owns `serialize_chunk`, `assemble_chunk_collection`, `write_chunks`, `load_chunks` — pure transform and I/O only, explicitly **not** validating (§P3.6: *"Explicitly not this module's responsibility: structural validation of the loaded container (P2.4)"*). Chunk Validation is the consumer of `load_chunks()`'s output shape, never the other direction.

### P1.4 Boundary from a future Document layer

Invariant #3 (`text == document_text[character_start:character_end]`) and invariant #8 (determinism across construction runs) are **not checkable by Chunk Validation as scoped to a single persisted `chunks.json`**, for two independent reasons, both resolved explicitly here rather than left implicit:

- **Invariant #3** requires the parent document's full text. `sample_rag/chunks.json` does not carry it (`docs/CHUNK_SERIALIZATION_PLAN.md` §P1.1: only the six Contract fields are serialized), and no persisted `Document` representation exists anywhere in the repository to load it from (`docs/CHUNK_CONTRACT.md` §20, the open `Document`-has-no-frozen-Data-Model backlog item). Chunk Validation **can** check the internally-derivable half of this invariant — `len(text) == character_end - character_start` (already invariant #2, an Entity/Relational check) — but **not** the full substring-equality half. This is a hard capability limit, not a scope choice: the data needed does not exist yet. Recorded as a forward dependency (P8), parallel to the `Document`-schema gap already flagged in Contract §20 and Serialization Plan §P4.5.
- **Invariant #8** (determinism) is a property of *repeated construction*, not of one static artifact — it can only be checked by comparing two runs' output, which is a regression/test-strategy concern (exactly how `docs/CHUNK_SERIALIZATION_PLAN.md` §P5 treats its own analogous "Deterministic serialization" row: a two-run comparison, not a single-artifact structural check). Out of scope for `validate_chunks()`.

---

## P2 — Validation Architecture

### P2.1 Module location

**Decision: add validation functions to `scripts/build_chunks.py`** (existing file from Sprint P2.3.2), not a new module.

Direct precedent: `scripts/build_manifest.py` bundles all four Manifest lifecycle responsibilities — discovery, assembly, serialization, **and validation** (`validate_manifest`) — in one file, one artifact family per script. `scripts/build_chunks.py` already plays this exact role for Chunk (serialization). Adding `validate_chunks()` there continues that same one-file-per-artifact convention rather than introducing a new file/module boundary that has no repository precedent. (`docs/CHUNK_SERIALIZATION_PLAN.md` §P3.1 already made and justified this file's existence and role; this plan extends it, it does not reopen it.)

### P2.2 Public interface

Mirrors `validate_manifest(manifest: Mapping) -> Mapping`'s exact shape, for the same reason: reusable against a real loaded file, a test fixture, or a synthetic malformed collection, with no filesystem coupling.

```python
def validate_chunks(collection: Mapping) -> Mapping:
    """Verify that `collection` conforms to the frozen Chunk Contract
    (docs/CHUNK_CONTRACT.md §17) and the persisted container shape
    (docs/CHUNK_SERIALIZATION_PLAN.md §P2.1).

    Read-only. Raises ChunkValidationError on the first violation
    encountered. Returns the same object on success.
    """
```

Internally, three private helper functions implement the layers adopted in P4, composed by `validate_chunks()` in a fixed order (P4.1):

```python
def _validate_representation(collection: Mapping) -> list:
    """Layer: Representation. Returns the `chunks` list on success."""

def _validate_chunk_entry(entry: Mapping, index: int) -> None:
    """Layer: Entity. Field + Relational invariants for one chunk dict."""

def _validate_collection_invariants(entries: list) -> None:
    """Layer: Collection. Cross-chunk invariants, grouped by document_id,
    plus corpus-wide id uniqueness."""
```

This keeps the same **public surface shape** as the precedent (one function, `Mapping -> Mapping`) while giving the richer invariant set (P0.2) an internal structure that reflects its actual scopes — not a new public API, an internal decomposition.

### P2.3 Repository integration

- **Input:** the `Mapping` returned by `scripts/build_chunks.py`'s `load_chunks()`, or any equivalent already-loaded mapping (test fixture, synthetic dict) — identical calling convention to `load_manifest()` → `validate_manifest()`.
- **Dependency:** stdlib only (`collections.abc.Mapping`). No import of `sample_rag.chunker.Chunk` — validation operates on the plain dict/JSON shape `serialize_chunk` produces, the same representation-level decoupling `validate_manifest()` already has from any Manifest-entry dataclass (there is none; Manifest entries are plain dicts throughout their lifecycle, and so are Chunk collection entries once serialized).
- **Lifecycle placement:** structural validation, invoked after `load_chunks()`, before any consumer trusts `chunks.json`'s contents — mirrors `docs/MILESTONE_1A.md` build item 1's *"Validated by: one pytest suite... No separate validation subsystem — this stays a file plus a check"* framing for Manifest, applied to Chunk.

### P2.4 Divergence from `validate_manifest()`, explicitly justified

The **only** material divergence from the precedent is the internal three-layer decomposition (P2.2, P3, P4) — justified in full in P0.2/P0.3 by Contract §17's own invariant scopes, not by this plan's preference. The **exception pattern, fail-fast behavior, read-only contract, and `Mapping -> Mapping` public signature are all reused unchanged** (P6, P2.2).

---

## P3 — Validation Rule Classification

Justified by P0.3. Every rule derivable from `docs/CHUNK_CONTRACT.md` §17, classified into exactly one primary category.

### Field Invariants (single field, single chunk entry)

| Rule | Contract source |
|---|---|
| Entry is a `Mapping`/object (precondition for the checks below) | Mirrors `validate_manifest()`'s identical per-entry `isinstance(entry, Mapping)` check |
| `id` present, type `str` | §8 |
| `document_id` present, type `str` | §8 |
| `text` present, type `str` | §8 |
| `chunk_index` present, type `int` | §8 |
| `character_start` present, type `int` | §8 |
| `character_end` present, type `int` | §8 |

### Relational Invariants (relationships between fields on one chunk)

| Rule | Contract source |
|---|---|
| `character_end > character_start` (non-empty) | §17 invariant 1 |
| `len(text) == character_end - character_start` | §17 invariant 2 (also the checkable half of invariant 3 — P1.4) |

### Collection Invariants (relationships across multiple chunks)

| Rule | Contract source |
|---|---|
| For a fixed `document_id`: `chunk_index` values are exactly `0..N-1`, no gaps or duplicates | §17 invariant 4 |
| For a fixed `document_id`: ascending `chunk_index` matches ascending `character_start` | §17 invariant 5 |
| For a fixed `document_id`: `chunk[i].character_end <= chunk[i+1].character_start` (no overlap) | §17 invariant 6 |
| `id` unique across the entire collection | §17 invariant 7 |

### Representation Invariants (persisted container shape)

| Rule | Contract source |
|---|---|
| Container has required top-level field `schema_version` | `docs/CHUNK_SERIALIZATION_PLAN.md` §P2.1; mirrors `validate_manifest()`'s `manifest_version` check |
| `schema_version` is a `str` equal to the frozen current value (`"1.0"`) | Same |
| Container has required top-level field `chunks` | `docs/CHUNK_SERIALIZATION_PLAN.md` §P2.1 |
| `chunks` is a `list` | Same |

**Not classified as a validation rule (explicitly excluded, per P1.4):** `text == document_text[character_start:character_end]` (full substring check) and determinism (invariant 8) — neither is checkable from a single persisted collection; both are forward dependencies (P8).

**Deferred to a decision outside this taxonomy (P5):** `document_id` referential integrity against `knowledge_manifest.json`.

No category beyond these four is introduced. Every row above traces to Contract §17, §8, or the Serialization Plan's frozen container shape — none is invented.

---

## P4 — Validation Layers

Justified by P0.3/P3. Three execution layers, matching the sprint's own suggested layer names.

### Layer 1 — Entity Validation

Operates on one chunk entry (`Mapping`) at a time, in isolation. Runs **Field Invariants** then **Relational Invariants** for that entry (relational checks presuppose the fields they reference exist and are correctly typed, so they run second, within the same per-entry pass — mirroring `validate_manifest()`'s own per-entry loop structure exactly).

### Layer 2 — Collection Validation

Operates on the full list of already-individually-valid entries. Runs **Collection Invariants**: groups entries by `document_id`, checks `chunk_index` contiguity and ordering within each group, checks non-overlap within each group, and checks `id` uniqueness across the entire list (not per-group — Contract §10: corpus-wide).

### Layer 3 — Serialized Representation Validation

Operates on the top-level container `Mapping` before any entry is inspected. Runs **Representation Invariants**: `schema_version` and `chunks` presence/type. On success, yields the `chunks` list for Layers 1–2 to consume.

### P4.1 Execution order vs. layer numbering — explicit note

**Layer numbering is a categorization label, not an execution sequence.** The composed `validate_chunks()` (P2.2) executes **Layer 3 first**, as a structural gate — Layers 1 and 2 cannot safely iterate `collection["chunks"]` until Layer 3 has confirmed that key exists and is a list. Execution order is therefore **Layer 3 → Layer 1 → Layer 2**: representation shape, then each entry in isolation, then cross-entry relationships. This mirrors `validate_manifest()`'s own literal execution order (top-level `manifest_version`/`documents` checks run before the per-entry loop) — the layer *names* follow the sprint prompt's own suggested taxonomy (Entity=1, Collection=2, Representation=3); the *call order* follows the same gating logic `validate_manifest()` already uses, unchanged.

---

## P4.5 — Validation Flow Matrix

Both categorized and layered validation are adopted (P0.3), so this matrix is required per the sprint's own instruction.

| Validation Rule Category | Primary Validation Layer | Secondary Layer |
|---|---|---|
| Representation Invariants | Layer 3 (Serialized Representation) | — |
| Field Invariants | Layer 1 (Entity) | — |
| Relational Invariants | Layer 1 (Entity) | — |
| Collection Invariants | Layer 2 (Collection) | — |

No category spans multiple layers — each of Contract §17's checkable invariants (P3) maps to exactly one scope and therefore exactly one layer. No overlap to justify.

---

## P5 — Referential Integrity Resolution

**Question (Contract §11):** must `chunk.document_id` be validated against `knowledge_manifest.json`'s `documents[].id` during Chunk Validation (P2.4)?

**Decision: Option B — DEFERRED.** Referential integrity is explicitly **not** part of `validate_chunks()`'s structural scope in this sprint.

### Why

1. **The Contract itself frames this as semantic, not structural, validation.** §11: *"Referential integrity... is not part of this structural contract. It is a semantic/cross-artifact validation concern, analogous to how `validate_manifest()` today performs only structural checks and no semantic ones."* This planning sprint's own P0 review (above) independently confirms that framing: `validate_manifest()` performs **zero** cross-artifact checks of any kind — not `documents[].id` uniqueness, not filesystem existence of `source` paths, not `hash` freshness.
2. **The repository already has a separate, named home for semantic/cross-artifact checks.** `docs/MILESTONE_1A.md` build item 2 names "Data Quality Validation" — a distinct pytest suite (Layer 1, `docs/glossary.md`'s Evaluation-vs-Validation entry) — as the venue for resume/chunk/metadata/coverage validation, **separate from** the structural `validate_manifest()`/`assemble_manifest`/`write_manifest` module. Folding referential integrity into `validate_chunks()` would collapse a distinction the repository has already made deliberately for Manifest (structural checks live with the artifact's own build script; semantic/cross-artifact checks live in the pytest Data Quality layer) and would do so for Chunk alone, inconsistently.
3. **A genuine blocking dependency exists.** `chunk.document_id` referential integrity, if checked, would need to load `knowledge_manifest.json` (via `scripts/build_manifest.py`'s `load_manifest()`) from inside what is otherwise a `scripts/build_chunks.py`-local, single-artifact validator — introducing a cross-script dependency `validate_manifest()` has no equivalent of anywhere in the repository. This is not fatal to doing it eventually, but it is new coupling that this sprint's evidence does not yet require introducing.
4. **P7's own governing instruction** for this sprint states Chunk Validation "must remain reusable and independent of document extraction." While loading `knowledge_manifest.json` is not itself "document extraction," bundling a cross-artifact join into the same function that performs pure single-artifact structural checks blurs a boundary this plan otherwise keeps clean (P2.4).

### Where it belongs instead (recorded, not designed here)

When referential integrity is eventually implemented, repository evidence points to the **Data Quality Validation pytest layer** (`docs/MILESTONE_1A.md` build item 2) as its home — a check that loads both `sample_rag/chunks.json` and `sample_rag/knowledge_manifest.json` and confirms every `document_id` in the former exists in the latter's `documents[]` — not a fifth layer inside `validate_chunks()` itself. This keeps `validate_chunks()`'s structural/single-artifact scope intact, consistent with `validate_manifest()`'s own scope.

### Blocking dependency for full resolution

Independent of this decision, real referential-integrity checking is also blocked on the same `Document`-schema gap already recorded in Contract §20: nothing in this decision requires that gap to close, since `knowledge_manifest.json` already exists and is loadable today — but it is recorded here for completeness, since a future implementer will look for it.

---

## P6 — Validation Exception Strategy

### P6.1 Exception type

**`ChunkValidationError(Exception)`** — a new, dedicated exception, direct subclass of the built-in `Exception`. Defined in `scripts/build_chunks.py`, alongside `ChunkSerializationError`.

### P6.2 Independence from sibling exceptions

The repository's existing pattern is **three independent, flat exception types**, each a direct `Exception` subclass with no shared base class between them:

| Exception | Module | Scope |
|---|---|---|
| `ManifestValidationError` | `scripts/build_manifest.py` | Manifest load/parse/structural-validation failures |
| `ChunkConstructionError` | `sample_rag/chunker.py` | Chunk construction-time invariant violations |
| `ChunkSerializationError` | `scripts/build_chunks.py` | Chunk collection I/O/parse failures (explicitly **not** validation — §P3.5 of the Serialization Plan) |

`ChunkValidationError` follows this exact pattern: a fourth independent type, not a subclass of `ChunkConstructionError` or `ChunkSerializationError`, and not sharing a new common base class invented for this sprint (no repository evidence supports introducing a shared validation-exception hierarchy — the precedent is flat, sibling exception types per responsibility).

### P6.3 Raise behavior

**Fail-fast**, matching `validate_manifest()` exactly: `validate_chunks()` raises `ChunkValidationError` on the first violation encountered (in the P4.1 execution order — Layer 3, then Layer 1 per entry, then Layer 2), not after accumulating a full list of violations. This is a direct precedent reuse, not a new decision: nothing in Contract §17 or in this sprint's evidence calls for batch-reporting, and `validate_manifest()`'s fail-fast behavior has never been identified as a repository pain point (P0.1: no test suite even exists yet to have surfaced one).

### P6.4 Future extensibility

If a future sprint needs accumulated (non-fail-fast) reporting — e.g., a corpus-wide lint/report tool — that is a new, additive capability layered on top of `validate_chunks()` (e.g., a wrapper that catches and collects), not a change to `validate_chunks()`'s own raise behavior. Not designed here; recorded as a forward dependency (P8).

---

## P7 — Repository Integration

### P7.1 Invocation points

`validate_chunks(load_chunks())` — chainable exactly as `validate_manifest(load_manifest())` already is, and, per `docs/CHUNK_SERIALIZATION_PLAN.md` §P0.2, kept as two separate function calls rather than fused, following the same repository convention (load and validate are independently useful — a test can validate a synthetic dict without touching disk; a script can load without validating).

### P7.2 Interaction with Construction

No direct call dependency. `sample_rag/chunker.py`'s `_check_invariants()` and `scripts/build_chunks.py`'s `validate_chunks()` check an overlapping invariant subset (non-empty, offset/length consistency, `chunk_index` contiguity, non-overlap, id uniqueness) by design — this is **intentional independent re-verification**, already anticipated and named by `_check_invariants()`'s own docstring (P1.2), not accidental duplication for P2.4 to eliminate. Construction enforces defensively against what it just built in memory; Validation checks the artifact as it exists on disk, regardless of provenance.

### P7.3 Interaction with Serialization

Pure downstream consumer. `validate_chunks()` consumes exactly the `{schema_version, chunks: [...]}` shape `assemble_chunk_collection`/`write_chunks`/`load_chunks` already produce and read (`docs/CHUNK_SERIALIZATION_PLAN.md` §P2.1). No change to any Serialization function is required or proposed.

### P7.4 Interaction with a future Document layer

None at this sprint. Referential integrity (P5) and the full text-substring check (P1.4) are both explicitly deferred pending a `Document` Data Model that does not yet exist (Contract §20).

### P7.5 Reusability and independence

`validate_chunks()` depends on nothing but stdlib `collections.abc.Mapping` and operates on a plain `Mapping`, not a live pipeline object — reusable against `sample_rag/chunks.json`, a test fixture, or any synthetic malformed collection, with zero dependency on `KnowledgeSource`, `.docx` extraction, or any runtime pipeline state, per the sprint's own governing instruction.

---

## P8 — Forward Dependencies

Recorded only — none designed or scheduled here.

- **`Document` Data Model & Contract Freeze** (Contract §20 backlog item). Unblocks: (a) the full `text == document_text[character_start:character_end]` substring check (P1.4), currently only partially checkable; (b) real referential-integrity checking with a defined join key contract on both sides.
- **`chunk.document_id` referential integrity against `knowledge_manifest.json`** (P5) — recommended future home: the Data Quality Validation pytest layer (`docs/MILESTONE_1A.md` build item 2), not `validate_chunks()` itself.
- **Chunk coverage check** (`docs/altm.md` line 189: *"every span of source text should exist in exactly one chunk with a corresponding vector"*) — a strictly larger claim than invariant #3, requiring both `Document` text (unavailable, see above) **and** vector/index data behind `EmbeddingProvider`/`VectorStore` (Milestone 2, interface-only today per `docs/architecture.md` §5/§7). Out of scope for P2.4 entirely; a Milestone 2 concern.
- **Determinism regression testing** (invariant #8) — a two-run comparison strategy, analogous to `docs/CHUNK_SERIALIZATION_PLAN.md` §P5's own "Deterministic serialization" row; belongs to future test/CI design, not `validate_chunks()`.
- **DOCX extraction / multi-document corpus generation** — would supply real `Document` instances at scale; not designed here, per Contract §20 and Serialization Plan §P4.5's identical forward-dependency framing.
- **Build orchestration / CLI wiring** — invoking `validate_chunks(load_chunks())` from a reproducible entry point (`docs/architecture.md` §5's `CLI` component) is not designed here.
- **Integration testing for `validate_chunks()` itself** — a `tests/test_build_chunks.py`-style suite (no equivalent exists yet for `validate_manifest()` either, per P0.1) is a future sprint's responsibility, following `tests/test_chunker.py`'s existing style (explicit fixture-based positive/negative cases per invariant).

---

## Validation Governance Model (as realized by this plan)

```text
Repository Evidence
  docs/CHUNK_CONTRACT.md §17 (8 invariants, multiple scopes)
  scripts/build_manifest.py validate_manifest() (flat, field-only precedent)
↓
Repository Precedent Review (P0)
  validate_manifest() scoped to field-only checks because Manifest's contract
  never had cross-field/cross-entry invariants — not by design preference
↓
Architectural Decision (P0.3)
  Option B: categorized + layered, narrowly, because Contract §17 itself
  spans four distinct scopes Manifest's contract never had
↓
Validation Responsibilities (P1)
  One question only: does the persisted collection comply with the Contract
↓
Validation Architecture (P2)
  scripts/build_chunks.py, Mapping -> Mapping, fail-fast — precedent reused
  wherever the Contract doesn't force divergence
↓
Validation Rule Categories (P3)
  Field / Relational / Collection / Representation — each traced to Contract
  §17, §8, or the Serialization Plan's container shape
↓
Validation Flow Matrix (P4.5)
  1:1 category-to-layer mapping, no overlap
↓
Validation Layers (P4)
  Entity / Collection / Serialized Representation — execution order (3→1→2)
  distinguished explicitly from layer numbering
↓
Construction Specification (P2.2, P6)
  validate_chunks() + three private layer functions + ChunkValidationError
↓
Future Independent Verification (P8)
  Document layer, referential integrity, coverage check, determinism testing
```

---

## Explicit Scope

**IN SCOPE (this planning document):** repository precedent analysis, validation responsibilities, validation architecture, validation rule taxonomy, validation layers, Validation Flow Matrix, referential integrity resolution, exception strategy, repository integration, forward dependency documentation.

**OUT OF SCOPE:** validation implementation, Chunk construction changes, serialization changes, Document abstraction, KnowledgeSource, `.docx` loading, retrieval, embeddings, CLI, orchestration, integration testing, corpus generation. None of these are designed, scoped, or implied beyond the forward-dependency pointers in P8.

---

## Planning Traceability Checklist

**Repository Evidence**
- [x] repository validation precedent reviewed (P0.1)
- [x] precedent comparison documented (P0.2)
- [x] architectural divergence justified (P0.3, P2.4)

**Validation Design**
- [x] validation responsibilities defined (P1)
- [x] validation architecture defined (P2)
- [x] flat vs. categorized architecture resolved (P0.3 — Option B, narrowly)
- [x] validation taxonomy documented (P3)
- [x] validation layers documented (P4)
- [x] Validation Flow Matrix completed (P4.5)
- [x] rule categories mapped to validation layers (P4.5)
- [x] cross-layer responsibilities justified — none exist (P4.5)

**Repository Integration**
- [x] referential integrity scope resolved (P5 — deferred)
- [x] validation exception strategy defined (P6)
- [x] repository integration documented (P7)
- [x] implementation boundaries documented (P1.1, P1.4, Explicit Scope)
- [x] forward dependencies documented (P8)

**Readiness**
- [x] construction readiness achieved (see below)

---

## Construction Readiness Review

- [x] Repository validation precedent reviewed and compared — P0
- [x] Validation responsibilities frozen — P1
- [x] Validation architecture frozen (module, interface, integration) — P2
- [x] Validation rule taxonomy frozen — P3
- [x] Validation layers frozen, execution order disambiguated from layer numbering — P4
- [x] Validation Flow Matrix complete — P4.5
- [x] Referential integrity scope explicitly resolved (deferred) — P5
- [x] Exception strategy frozen — P6
- [x] Repository integration complete — P7
- [x] Forward dependencies recorded — P8

**Result: PASS.** No blocking gap was found for Validation *Planning* itself. Two capability limits are recorded, not resolved, both stemming from the same pre-existing gap (Contract §20 — no `Document` Data Model): the full `text`-substring invariant is only partially checkable, and referential integrity is deferred to a pytest Data Quality layer outside `validate_chunks()`'s structural scope. Neither blocks P2.4.1 (Chunk Validation Construction) from proceeding against the invariant set this document does freeze (P3, P4.5).

---

## Unresolved Architectural Questions

None block construction. Two items are flagged for awareness, not open decisions:

1. Whether the Data Quality Validation pytest layer (referential integrity's recommended future home, P5) should itself live under `tests/` or a new `scripts/` entry point is not decided here — it is out of scope until that layer is actually designed, and no repository evidence yet describes its structure beyond the one-line mention in `docs/MILESTONE_1A.md` build item 2.
2. Whether `ChunkValidationError` should eventually support accumulated (non-fail-fast) reporting (P6.4) is recorded as a possible future extension, not a present gap — no repository evidence currently demands it.

---

## Stop Condition

Per the sprint's own governing instruction, this document ends here.

No validation has been implemented. No Python code has been written. No runtime module (`sample_rag/chunker.py`, `scripts/build_chunks.py`) has been modified. `docs/CHUNK_CONTRACT.md`, `docs/adr/ADR-0001-chunk-persistent-representation.md`, and `docs/CHUNK_SERIALIZATION_PLAN.md` are unchanged. No commit has been made.

Awaiting review and approval before Sprint P2.4.1 (Chunk Validation Construction) begins.
