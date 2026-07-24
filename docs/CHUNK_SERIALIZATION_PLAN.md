# Chunk Serialization — Implementation Plan

**Repository:** `ai-quality-engineering`
**Status:** Planning (Construction Readiness Review — Sprint P2.3.1)
**Related documents:** `docs/CHUNK_CONTRACT.md` (frozen v1.0 — the only source of Chunk field/invariant truth), `docs/adr/ADR-0001-chunk-persistent-representation.md` (authoritative — no separate Chunk Artifact Contract; container decided here, per its own precedent), `docs/architecture.md` (§5 Component Architecture, §6 Repository Structure), `docs/MILESTONE_1A.md` (Knowledge Manifest contract; build item 3, Indexing), `docs/glossary.md` (canonical terminology), `scripts/build_manifest.py` (Knowledge Manifest assembly/serialization/validation precedent), `sample_rag/chunker.py` (Chunk Construction, Sprint P2.2)

This document plans **how** the already-frozen Chunk Contract (`docs/CHUNK_CONTRACT.md`) is serialized into a deterministic persistent representation. It does not define what a Chunk is (unchanged), and — per the Sprint P2.3.0 ADR — it does not introduce a new architectural layer. It is a planning artifact only: no serializer, persistence, validation, or loader code is implemented by this document, and no runtime code is modified.

---

## Terminology Note

No new terminology is introduced. "Serialization," "container," and "schema version" are used descriptively, in the same sense `docs/MILESTONE_1A.md` and `datasets/SCHEMA.md` already use them for the Knowledge Manifest and Golden Dataset artifacts, respectively. This plan does not propose additions to `docs/glossary.md`.

---

## P0 — Repository Discovery

Per the sprint's own governing instruction, discovery here is scoped to implementation planning; it does not reopen the Sprint P2.3.0 ADR's conclusion (no separate Chunk Artifact Contract).

### P0.1 Knowledge Manifest serialization (the primary precedent)

`scripts/build_manifest.py` is the repository's only existing example of the full assemble → serialize → load → validate lifecycle for a Persistent Canonical Artifact:

| Responsibility | Function | Behavior |
|---|---|---|
| Assembly | `assemble_manifest(document_entries) -> dict` | Pure transform. Wraps entries in `{"manifest_version": MANIFEST_VERSION, "documents": list(document_entries)}`, preserving order and values exactly as received. No I/O. |
| Serialization | `write_manifest(manifest) -> None` | `json.dumps(manifest, indent=2) + "\n"`, UTF-8, insertion-order keys (no `sort_keys`), trailing newline. Writes to `sample_rag/knowledge_manifest.json`. No validation, no recomputation. |
| Loading | `load_manifest() -> Mapping` | Reads and `json.loads`s the persisted file. Raises `ManifestValidationError` on I/O or JSON-decode failure. No structural checking. |
| Validation | `validate_manifest(manifest) -> Mapping` | Read-only structural check (required top-level fields, required per-entry fields and types). Raises `ManifestValidationError` on violation. Returns the same object on success. |

Determinism is enforced one layer up, in `main()`: `discover_documents`'s `rglob` returns an OS-order-dependent listing, so `main()` explicitly wraps it in `sorted(normalize_source_path(...) for ...)` before any entry is built — determinism is a property the orchestrator forces, not something assumed of the filesystem.

### P0.2 Manifest validation workflow

`validate_manifest()` is read-only and mapping-based (`collections.abc.Mapping`), not file-based — it accepts anything already loaded (a real file, a test fixture, a synthetic malformed dict) and never touches disk itself. Loading (`load_manifest`) and validation (`validate_manifest`) are kept as two separate functions even though the CLI/tests could trivially chain them — a repository convention this plan reuses in §P3.

### P0.3 Repository serialization and versioning conventions

Two existing, distinct container-versioning conventions exist in the repository — both were inspected, per the sprint's explicit instruction, before this plan defines the Chunk container's version field:

| | Knowledge Manifest | Golden Dataset (`datasets/SCHEMA.md`) |
|---|---|---|
| Field name | `manifest_version` | `schema_version` |
| Value (current) | `"1.0"` | `"1.0"` |
| Value format | String, `Major.Minor` (`docs/MILESTONE_1A.md`, build item 1: *"Manifest version format. `manifest_version` is a Major.Minor string, frozen at `"1.0"`."*) — explicitly **not** described as semantic versioning anywhere in its own contract. | String, same `Major.Minor` shape (`datasets/SCHEMA.md` §2, "Schema Version: `1.0`"), also never described as semantic versioning. |
| Version Evolution rule | "changes only when the Knowledge Manifest schema itself changes. Changes to corpus contents, document hashes, or the set of catalogued documents... do not change `manifest_version`." (`docs/MILESTONE_1A.md`, build item 1) | "Future changes to file structure, container shape, or identifier convention must increment this version rather than silently changing structure under an unchanged version number." (`datasets/SCHEMA.md` §2) |
| Reuse scope | One artifact (`knowledge_manifest.json`) | Reused verbatim across nine files / three container types (`facts`, `qa_pairs`, `evidence_trace`) × three sources (`datasets/SCHEMA.md` §7–§8) |
| Entity-level versioning | None — `documents[]` entries carry no version field | None — `facts`/`qa_pairs`/`evidence_trace` entries carry no version field |

**Finding, stated explicitly per the sprint's instruction:** neither convention uses semantic versioning (no patch tier is ever incremented; both are frozen `Major.Minor` strings that change only on structural/schema change, independent of content). This finding is carried into §P1 rather than assumed.

### P0.4 Repository layout and generated-artifact precedent

`git ls-files` confirms `sample_rag/knowledge_manifest.json` is tracked in version control (not `.gitignore`d — `.gitignore` excludes `__pycache__/`, `*.pyc`, `.venv/`, `.pytest_cache/`, `reports/regressions/*.csv`, and similar transient/environment output, but not this artifact). `datasets/golden/*.json` files are not yet populated (only `.gitkeep` placeholders exist per `datasets/SCHEMA.md` §9's phased-population plan), so they provide no additional evidence either way. This is carried into §P4.

### P0.5 Chunk Construction output (Sprint P2.2, already committed)

`sample_rag/chunker.py` defines `Chunk` as `@dataclass(frozen=True)` with exactly the six frozen fields, in the order `id, document_id, text, chunk_index, character_start, character_end` (matching `docs/CHUNK_CONTRACT.md` §8's table order exactly), and `Chunker.chunk(doc) -> list[Chunk]` — pure, no I/O, operating on one `doc` at a time. No multi-document orchestration, no persistence, and no `Document`/`KnowledgeSource` implementation exist anywhere in the repository yet (confirmed by `git ls-files` and by `docs/CHUNK_BUILDER_IMPLEMENTATION_PLAN.md` §1.2, §2, which already recorded this as a bounded, non-blocking gap for Construction). This gap does not block Serialization *Planning* (this document plans against the frozen `Chunk` shape regardless of how a given `doc` was obtained) but is carried forward as a genuine, already-flagged forward dependency for Serialization *Construction* (§P4.5).

### P0.6 Conclusion of Discovery

The reusable pattern is the Knowledge Manifest's assemble → serialize → load → validate decomposition (`scripts/build_manifest.py`), with the version-field *name* drawn from the wider repository convention rather than copied verbatim from the Knowledge Manifest (§P1). No new pattern is invented; no architectural decision from the ADR is reopened.

---

## P1 — Serialization Requirements

Each requirement below cites its authoritative source directly, per the sprint's instruction.

### P1.1 Required serialized fields

The only fields serialized per chunk are the six frozen by `docs/CHUNK_CONTRACT.md` §8: `id`, `document_id`, `text`, `chunk_index`, `character_start`, `character_end`. No additional field (deferred or otherwise) is serialized — `docs/CHUNK_CONTRACT.md` §15 defers ten candidate fields explicitly; §9 states there is no optional tier. Field order in the serialized object mirrors Contract §8's table order and `sample_rag/chunker.py`'s existing dataclass field order — no divergence.

### P1.2 Container requirement

A wrapping container is required. Authority: `docs/CHUNK_CONTRACT.md` §19 ("whether a wrapping container... is needed for a persisted chunk collection... this document recommends the same pattern for Chunk") and ADR-0001 §3 Consequences ("P2.3.1 should carry forward... entities stay unversioned; the container carries the version marker"). The container carries exactly two top-level fields — a version marker and an array of chunk entities — and nothing else. Authority: ADR-0001 §2 ("Collection-level metadata beyond a version + list wrapper — None [found]... No other collection-level field is named anywhere").

### P1.3 Version placement

The version field belongs on the container, not on individual `Chunk` entities. Authority: `docs/CHUNK_CONTRACT.md` §9 (precedent: "individual `documents[]`/`facts` entries never carry `schema_version`; only their containers do") and §19, both cited directly by ADR-0001 §1.

### P1.4 Version field name and value format — explicit verification (per sprint instruction)

Per §P0.3, `sample_rag/knowledge_manifest.json`'s exact convention was verified before any decision was made here. That verification is kept separate, below, from the decision it feeds — the first subsection is repository evidence; the second is this planning sprint's own choice.

**What repository evidence establishes (fact, not decision):**

- Two established top-level version-field conventions currently exist in the repository, each scoped to its own artifact family:
  - `manifest_version` — used by exactly one artifact family, the Knowledge Manifest (`sample_rag/knowledge_manifest.json`).
  - `schema_version` — used by the Golden Dataset family, reused verbatim across nine files spanning three distinct container types (`datasets/SCHEMA.md` §7–§8).
- Both conventions share an identical value format and Version Evolution rule: a frozen `Major.Minor` string (currently `"1.0"` in both families), incremented only on a structural/schema change and never on a content or count change — and neither is, or is described anywhere as, semantic versioning.
- **Repository evidence does not establish a universal, repository-wide version-field convention.** No document in the repository states a single naming rule that every artifact family must follow. `manifest_version` and `schema_version` are two independently-named, family-scoped conventions that happen to share the same value format — not two instances of one shared rule.

**What this planning document decides (an intentional repository evolution, not a pre-existing rule):**

Chunk is a third artifact family that has never had a version field before, so no existing convention already covers it — a name must be chosen. This document adopts **`schema_version`** for the Chunk container. This is a deliberate choice made by this planning sprint, not a fact repository history already settled:

- `schema_version` is reused because it is the more *reusable* of the two existing conventions — already generalized across three unrelated container types — making it the stronger candidate for extending to a fourth artifact family. This is this sprint's judgment applied to the evidence above, not a rule the repository enforced beforehand.
- `manifest_version` is deliberately not reused, because it is name-bound to the Knowledge Manifest concept specifically (a document catalogue with hash/freshness metadata), which a chunk collection is not.
- No unprecedented name is invented (e.g. a `chunk_version` field appears nowhere in the repository and is not introduced here) — the choice is between the two names evidence already established, not a third one.

**Consequence for interpretation — version values are family-scoped, not shared:** extending `schema_version` to the Chunk container is this document's own repository evolution, not evidence that Chunk was always part of the Golden Dataset's versioning scheme. `schema_version: "1.0"` in `sample_rag/chunks.json` and `schema_version: "1.0"` in a `datasets/golden/*.json` file are independent values, meaningful only within their own artifact family, and must not be read as positions on one shared version timeline — exactly as `manifest_version: "1.0"` (Knowledge Manifest) and `schema_version: "1.0"` (Golden Dataset) are already independent of each other today, despite the coincidentally identical value.

Value for this version: `"1.0"` — matching, as a starting-point convention this document does reuse, both existing families' current value and format.

### P1.5 Ordering guarantee

The serialized `chunks` array preserves the same ordering guarantee already frozen for chunk construction: within a `document_id`, ascending array position matches ascending `chunk_index`, which matches ascending `character_start` (`docs/CHUNK_CONTRACT.md` §7, §12, §17 invariants 4–5). Across documents (a forward-looking concern — the current corpus has exactly one document, `sample_rag/knowledge_manifest.json`), documents are iterated in the same deterministic order the Knowledge Manifest itself already established: normalized-source-path sort order (`scripts/build_manifest.py`, `main()`'s `sorted(...)` call over `normalize_source_path` output), the same order in which `documents[]` entries already appear in `knowledge_manifest.json`. This reuses an existing determinism mechanism rather than inventing a new cross-document ordering rule.

### P1.6 Determinism guarantee

Identical input `list[Chunk]` (in identical order) produces byte-identical serialized output on every run. Authority: `docs/CHUNK_CONTRACT.md` §7 ("Deterministic artifact contract... every conforming implementation of the Chunk Data Model must preserve it") and the identical precedent already implemented for the Knowledge Manifest (`write_manifest`'s fixed `json.dumps(..., indent=2)` call, no non-deterministic key ordering, no timestamps).

### P1.7 Repository location

`sample_rag/chunks.json`, sibling to `sample_rag/knowledge_manifest.json`. Rationale and full evidence in §P4.

### P1.8 Implementation constraints

Stdlib only (`json`, `pathlib`, `dataclasses`) — matches `docs/MILESTONE_1A.md`'s Libraries table and the "minimal dependencies" principle (`docs/roadmap.md` §6), already the exact dependency set `scripts/build_manifest.py` uses for the same responsibility.

---

## P2 — Container Planning

### P2.1 Canonical Serialization Container

```json
{
  "schema_version": "1.0",
  "chunks": [
    {
      "id": "…",
      "document_id": "…",
      "text": "…",
      "chunk_index": 0,
      "character_start": 0,
      "character_end": 0
    }
  ]
}
```

### P2.2 Field-by-field rationale

| Field | Rationale | Evidence |
|---|---|---|
| `schema_version` (top-level) | Container-level version marker, entity-unversioned pattern. | `docs/CHUNK_CONTRACT.md` §9, §19; ADR-0001 §3; §P1.3–P1.4 above |
| `chunks` (top-level array) | Array key named after the plural entity it holds — matches `documents[]` (Knowledge Manifest) and `facts`/`qa_pairs`/`evidence_trace` (Golden Dataset), both of which name the container key after their contained entity type. | `docs/MILESTONE_1A.md` build item 1; `datasets/SCHEMA.md` §8 |
| Six per-chunk fields, unchanged | Direct mapping, no reshaping — the frozen entity is already flat and serialization-ready (`str`/`int` only). | `docs/CHUNK_CONTRACT.md` §8, §17; ADR-0001 §2 ("no nested objects, no runtime-only fields... nothing about persisting a Chunk requires restructuring it") |
| No additional top-level field (e.g. document count, corpus hash, generation metadata) | No repository evidence of a need; explicitly checked and rejected during the ADR's own analysis. | ADR-0001 §2 ("Collection-level metadata beyond a version + list wrapper — None [found]") |
| No per-chunk `schema_version` | Entities stay unversioned; only the container versions. | `docs/CHUNK_CONTRACT.md` §9 precedent, cited directly by ADR-0001 §1, §3 |

This is the concrete shape ADR-0001 left open (§3 Consequences: "P2.3.1 inherits the responsibility of finalizing the container shape... it is not blocked on a prerequisite architecture sprint"). No collection semantics beyond a version marker and an ordered list are introduced, per the ADR's own scope boundary.

---

## P3 — Serialization Design

Design only — no code is written or implemented by this section.

### P3.1 Module placement

**Decision: `scripts/build_chunks.py`** (new file), not `sample_rag/`.

This deliberately mirrors the reasoning `docs/CHUNK_BUILDER_IMPLEMENTATION_PLAN.md` §2.1 already used for the opposite call (placing *Construction* in `sample_rag/chunker.py`), applied to the opposite conclusion for *Serialization*:

| Fact | Source |
|---|---|
| `sample_rag/` = "The pipeline under test... This is the system being evaluated, not the evaluation logic itself." | `docs/architecture.md` §6 |
| `scripts/` = "Operational scripts (e.g., dataset regeneration, report generation) — not pipeline logic." | `docs/architecture.md` §6 |
| The runtime pipeline hands Chunks from `Chunker` to `Indexer` directly, in-memory (`C->>IDX: Chunks`) — no disk round-trip exists on the query-time or build-time runtime path. | `docs/architecture.md` §8 sequence diagram, cited directly by ADR-0001 §1 |
| Persistence exists for a different, already-named reason: the Evidence Trace Dataset's `Expected Chunk` field needs a stable, reviewable, on-disk ground-truth form — the same role `knowledge_manifest.json` plays for freshness validation. | `docs/MILESTONE_1A.md` build item 8; ADR-0001 §1 |
| There is no `Serializer` row, and no frozen interface signature for chunk persistence, anywhere in `docs/architecture.md` §5 or §7 — unlike `Chunker`, which has both. | `docs/architecture.md` §5, §7 |
| The Knowledge Manifest's own serialization (`write_manifest`, `load_manifest`) already lives in `scripts/build_manifest.py`, performing the exact same role this module performs for Chunk — deterministic build-artifact generation, not a runtime interface call. | `scripts/build_manifest.py` |

Chunk *Construction* (`Chunker`) is a named pipeline component with a frozen interface — it correctly lives in `sample_rag/`. Chunk *Serialization* is not a pipeline component at all; it is an operational, build-time artifact generator with the same role as `build_manifest.py`, so it follows that module's location, not `chunker.py`'s.

### P3.2 Function signatures (design only)

Modeled directly on `scripts/build_manifest.py`'s existing four-function decomposition:

| Function | Signature | Responsibility | Precedent |
|---|---|---|---|
| Per-entity serialization | `serialize_chunk(chunk: Chunk) -> dict` | Pure transform of one `Chunk` into a plain, JSON-serializable mapping with the six fields in Contract §8 order. Explicit field-by-field construction (not a bare `dataclasses.asdict(chunk)` call) so that serialized field order and presence are an intentional, documented decision — not an incidental consequence of the dataclass's current declared field order. | `build_manifest.py`'s `build_document_entry` |
| Collection assembly | `assemble_chunk_collection(chunks: list[Chunk]) -> dict` | Pure transform. Wraps an already-ordered `list[Chunk]` in `{"schema_version": SCHEMA_VERSION, "chunks": [serialize_chunk(c) for c in chunks]}`, preserving input order exactly. No I/O, no re-sorting, no invariant re-checking (already enforced by Construction, `sample_rag/chunker.py`'s `_check_invariants`). | `build_manifest.py`'s `assemble_manifest` |
| Serialization to disk | `write_chunks(collection: dict) -> None` | `json.dumps(collection, indent=2) + "\n"`, UTF-8, insertion-order keys, trailing newline, written to `sample_rag/chunks.json`. No validation, no recomputation. | `build_manifest.py`'s `write_manifest` |
| Loading from disk | `load_chunks() -> Mapping` | Reads and `json.loads`s the persisted file. Raises a dedicated error on I/O or JSON-decode failure. Performs no structural validation. | `build_manifest.py`'s `load_manifest` |

### P3.3 Deterministic output rules

- Fixed `json.dumps` parameters (`indent=2`, no `sort_keys`, insertion-order keys) — identical to `write_manifest`.
- No wall-clock, random, or environment-dependent values anywhere in the output — no `created_at`-style field is introduced, for the same reason the Knowledge Manifest explicitly removed one (`docs/MILESTONE_1A.md` build item 1, "Contract Change").
- Cross-document ordering is forced deterministic exactly as `build_manifest.py`'s `main()` already forces it for `documents[]` (§P1.5) — an explicit `sorted(...)` over normalized source paths, not incidental filesystem/OS order.

### P3.4 Version handling

`SCHEMA_VERSION = "1.0"` module constant (mirroring `MANIFEST_VERSION` in `build_manifest.py`), written into `assemble_chunk_collection`'s output. No mechanism to override or bump it at call time — a version bump is a deliberate, future schema-change event, not a runtime parameter, matching the Knowledge Manifest's own precedent.

### P3.5 Error handling

A dedicated exception, `ChunkSerializationError`, scoped strictly to I/O and JSON-decode failures in `load_chunks` (mirroring `ManifestValidationError`'s role in `load_manifest`, but deliberately **not** reused for structural validation). This keeps Serialization (P2.3) and the future Chunk Validation (P2.4) cleanly separated at the exception-type level, consistent with `docs/CHUNK_CONTRACT.md` §9's own note that P2.4's validation stance is "that sprint's decision, not this one's" — P2.3 does not pre-empt P2.4 by overloading one exception type across both responsibilities.

### P3.6 Responsibilities and extension boundaries

- **In scope for this module:** entity-to-dict mapping, container assembly, disk write, disk read (parse only).
- **Explicitly not this module's responsibility:** structural validation of the loaded container (P2.4), verifying `document_id` referential integrity against `knowledge_manifest.json` (already deferred by Contract §11 to a later validation stage), and any multi-document `Chunker` orchestration logic (a Construction-stage concern, §P4.5) — this module accepts an already-assembled, already-ordered `list[Chunk]` as its sole input to `assemble_chunk_collection`.

---

## P4 — Repository Integration

### P4.1 Output location

**`sample_rag/chunks.json`** — sibling to `sample_rag/knowledge_manifest.json`, inside `sample_rag/` (not `datasets/`, not `reports/`).

- Not `datasets/`: that directory is the Golden Dataset's own representation-contract territory (`datasets/SCHEMA.md`), governing `facts`/`qa_pairs`/`evidence_trace` — a distinct artifact family serving evaluation ground truth, not corpus indexing. Chunk is a Knowledge/Index-stage corpus artifact, not a Golden Dataset artifact (`docs/architecture.md` §4–§5).
- Not `reports/`: that directory holds "Generated evaluation *output*" (`docs/architecture.md` §6) — non-deterministic-in-principle run results (baselines, regression diffs), not a deterministic corpus-derived build artifact.
- `sample_rag/` already holds the pipeline's other corpus-derived artifact, `knowledge_manifest.json`, alongside `documents/` — direct, exact precedent for a corpus-derived JSON artifact's location.

### P4.2 Naming convention

`chunks.json` — a plain descriptive noun, matching `knowledge_manifest.json`'s naming style (no embedded version number, no date, no "canonical"/"generated" qualifier in the filename itself — the version lives inside the file, per §P1.3).

### P4.3 Relationship to datasets

None structurally. `sample_rag/chunks.json` is referenced by, but does not live inside, the Golden Dataset family. The Evidence Trace Dataset's `Expected Chunk` field (`docs/MILESTONE_1A.md` build item 8) will point at chunk data as ground truth, but — per ADR-0001 §2 — imposes no shape requirement of its own on the Chunk container; it is a consumer, not a co-designer, of this schema.

### P4.4 Relationship to evaluation artifacts

None. `reports/baseline/` and `reports/regressions/` hold evaluation run output (Layer 2–4, Milestone 2+); `sample_rag/chunks.json` is a build-time corpus artifact generated once per corpus state, analogous in role to `knowledge_manifest.json`, not an evaluation result.

### P4.5 Repository integration strategy — forward dependency (recorded, not resolved here)

Serialization Construction (a future sprint) will need to invoke `Chunker.chunk(doc)` once per corpus document and concatenate results in the deterministic order established in §P1.5/§P3.3. No `Document`/`KnowledgeSource` implementation or `.docx` text-extraction capability exists in the repository yet — an already-flagged, non-blocking gap (`docs/CHUNK_CONTRACT.md` §20; `docs/CHUNK_BUILDER_IMPLEMENTATION_PLAN.md` §1.2, §2, §5), which did not block Chunk Construction planning and does not block Chunk Serialization planning for the same reason: this plan defines how to serialize whatever ordered `list[Chunk]` Construction produces, regardless of how that `list[Chunk]` was obtained. This is recorded here as a forward dependency for whichever future sprint attempts real end-to-end serialization against the actual corpus, exactly as Contract §20 already records the underlying `Document` gap — not resolved or scoped by this document.

### P4.6 Repository artifact policy — committed vs. generated build output

**Primary precedent, per the sprint's explicit instruction:** `sample_rag/knowledge_manifest.json` is tracked in git (`git ls-files` lists it; `git check-ignore` confirms it is not excluded by any `.gitignore` rule — the existing rules target `__pycache__/`, `*.pyc`, `.venv/`, `.pytest_cache/`, and `reports/regressions/*.csv`, none of which apply here). This is a repository fact, not a written policy: no document (`docs/architecture.md`, `docs/roadmap.md`, or otherwise) states a general rule for whether generated canonical artifacts should be committed.

**Evaluation:** should `sample_rag/chunks.json` be committed, or excluded as generated build output?

- **Committed** (recommended): `chunks.json`, like `knowledge_manifest.json`, is fully deterministic — identical corpus + identical algorithm ⇒ identical bytes (§P1.6; Contract §7) — so committing it does not introduce merge-conflict or drift risk beyond what the Knowledge Manifest already tolerates today. It also serves the same reviewable-ground-truth role the ADR already assigned to Chunk persistence: a stable, on-disk, diffable form the Evidence Trace Dataset's `Expected Chunk` field and future Chunk Validation (P2.4) can reference without regenerating it, mirroring exactly how `knowledge_manifest.json` already serves freshness/hash validation.
- **Excluded** (rejected): would treat `chunks.json` as ephemeral build output (like `__pycache__/` or `reports/regressions/*.csv`), which contradicts its role as a corpus-derived Persistent Canonical Artifact (Contract §5) — a classification `chunks.json` shares with `knowledge_manifest.json`, which *is* committed. No repository evidence distinguishes the two artifacts on this dimension.

**Recommendation — formal policy (no formal policy currently exists):**

> Deterministic, corpus-derived Persistent Canonical Artifacts (currently: Knowledge Manifest, Chunk collection) are committed to version control. They are small, fully deterministic given a fixed corpus and algorithm, and serve as reviewable, diffable ground truth for downstream validation and evaluation — as distinct from non-deterministic or environment-specific build output (`__pycache__/`, `.pytest_cache/`, `reports/regressions/*.csv`), which remains `.gitignore`d.

**Retroactive application:** yes, this recommendation should apply retroactively to the Knowledge Manifest artifact as well — it already follows this behavior in practice (committed), so formalizing the policy only names an existing convention explicitly rather than changing anything about `knowledge_manifest.json`'s current handling. This mirrors the same "naming what's already practiced" pattern the Chunk Contract used for its own Persistent-vs-Runtime-Artifact distinction (Contract §5). Recording this policy in `docs/architecture.md` §6 or a similarly-scoped location is itself a documentation edit to a currently-locked document — out of this planning sprint's authorized scope (this sprint does not modify locked docs) — and is therefore recommended as a follow-up action, not performed here, consistent with how Contract §18 already records — without performing — its own follow-up documentation edits.

---

## P5 — Serialization Verification Strategy

Strategy only. No tests are implemented by this document.

| Verification concern | What would be checked | Precedent / rationale |
|---|---|---|
| Deterministic serialization | Two serialization runs over an identical `list[Chunk]` (identical order) produce byte-identical `chunks.json` output. | Mirrors the Knowledge Manifest's implicit determinism and Contract §7's explicit requirement. |
| Ordering | Serialized `chunks[]` array position matches ascending `chunk_index` within a `document_id`, and document iteration order matches the deterministic order established in §P1.5. | Contract §12, §17 invariants 4–5. |
| Schema/structural | Container has exactly the two top-level keys (`schema_version`, `chunks`); every chunk entry has exactly the six required fields, correctly typed — same check style as `validate_manifest`'s `REQUIRED_DOCUMENT_FIELDS` loop. | `scripts/build_manifest.py`'s `validate_manifest` pattern, reused as a *style* precedent (P2.4 owns the actual implementation). |
| Version | `schema_version` is present, is a string, and equals the frozen value for the current schema. | §P1.4; `validate_manifest`'s existing `manifest_version` equality check. |
| Regression / round-trip | Serialize a known `list[Chunk]`, then `load_chunks()` the result, and confirm field-for-field equality with the original input. | New coverage — no equivalent round-trip test exists yet for the Knowledge Manifest either; scoped here since it directly exercises `serialize_chunk`/`assemble_chunk_collection`/`write_chunks`/`load_chunks` together. |
| Malformed input — empty collection | An empty `list[Chunk]` serializes to `{"schema_version": "1.0", "chunks": []}` — legal, not an error (Contract §11: "a document produces zero or more chunks"). | Contract §11; mirrors `test_chunker.py`'s existing `test_empty_document_produces_no_chunks`. |
| Malformed input — non-`Chunk` entries | A `list` containing a non-`Chunk` object raises a clear, defined error from `serialize_chunk`/`assemble_chunk_collection` rather than silently emitting malformed JSON. | Mirrors `Chunker`'s own defined-error-over-leaked-exception acceptance criterion (`docs/CHUNK_BUILDER_IMPLEMENTATION_PLAN.md` §1.5). |
| Failure — write | An unwritable output path (permissions, missing parent directory) raises `ChunkSerializationError` rather than an unhandled `OSError`. | Mirrors `load_manifest`'s existing `OSError` → `ManifestValidationError` handling in `build_manifest.py`. |
| Failure — load | A corrupt or non-JSON `chunks.json` raises `ChunkSerializationError` rather than an unhandled `json.JSONDecodeError`. | Mirrors `load_manifest`'s existing `JSONDecodeError` handling. |

---

## P6 — Scope Boundaries

**IN SCOPE**

- Deterministic serialization of a `list[Chunk]` to JSON
- Collection wrapper (`{schema_version, chunks}`) generation
- Version field placement and value format
- `chunks.json` generation and its repository location
- Repository integration (location, naming, commit policy)

**OUT OF SCOPE**

- Alternate serialization formats (non-JSON)
- Persistence media beyond a local JSON file (databases, object storage)
- Storage APIs
- Loaders that reconstruct `Chunk` dataclass instances from disk (beyond the plain-`Mapping` `load_chunks()` design in §P3.2)
- Structural or semantic Chunk validation (P2.4)
- Indexing, retrieval
- Any runtime modification to `sample_rag/chunker.py`, `docs/CHUNK_CONTRACT.md`, or the ADR

---

## P7 — Serialization Traceability Matrix

| Requirement | Authoritative Source | Planning Decision | Construction Impact |
|---|---|---|---|
| Six Chunk fields serialized unchanged | `docs/CHUNK_CONTRACT.md` §8, §17 | Direct field-by-field mapping, Contract order preserved | `serialize_chunk` — direct mapping, no transform |
| Container required (version + list) | `docs/CHUNK_CONTRACT.md` §19; ADR-0001 §3 | `{schema_version, chunks}` wrapper | `assemble_chunk_collection` |
| Version lives on container, not entity | `docs/CHUNK_CONTRACT.md` §9; ADR-0001 §1 | No `schema_version` on individual chunk entries | `serialize_chunk` excludes any version field |
| Version field name | `sample_rag/knowledge_manifest.json` (`manifest_version`) + `datasets/SCHEMA.md` (`schema_version`) — two independent, family-scoped conventions, neither repository-wide; verified per §P1.4 | This sprint extends `schema_version` to the Chunk family (most reusable existing name); does not reuse `manifest_version` (name-bound to a different artifact); values remain family-scoped, not a shared timeline | `SCHEMA_VERSION` module constant in the new serializer |
| Version value format | `docs/MILESTONE_1A.md` build item 1; `datasets/SCHEMA.md` §2 | Frozen `Major.Minor` string, `"1.0"`, not semantic versioning | Version bump = deliberate schema-change event only |
| Ordering (within a document) | `docs/CHUNK_CONTRACT.md` §7, §12, §17 (invariants 4–5) | Array order preserves `chunk_index`/`character_start` order | `assemble_chunk_collection` performs no re-sorting; relies on Construction's guarantee |
| Ordering (across documents) | `scripts/build_manifest.py` `main()`'s `sorted(...)` precedent | Deterministic document iteration order, matching `knowledge_manifest.json`'s `documents[]` order | Future multi-document orchestration (Construction-stage, §P4.5) must reuse the same sort |
| No collection-level metadata beyond version + list | ADR-0001 §2 | No `document_count`, `corpus_hash`, or timestamp field | Container stays minimal |
| Module location | `docs/architecture.md` §6; ADR-0001 §1; `docs/CHUNK_BUILDER_IMPLEMENTATION_PLAN.md` §2.1 | `scripts/build_chunks.py`, not `sample_rag/` | New file, mirrors `scripts/build_manifest.py`'s decomposition style |
| Output location | `sample_rag/knowledge_manifest.json` precedent | `sample_rag/chunks.json` | Sibling artifact to the Knowledge Manifest |
| Repository artifact policy | `git ls-files` / `git check-ignore` evidence on `knowledge_manifest.json` | Commit `chunks.json`; recommend formalizing the policy retroactively for both artifacts | No `.gitignore` change required; documentation follow-up recommended, not performed here |
| Error handling | `scripts/build_manifest.py`'s `ManifestValidationError` | New, separately-scoped `ChunkSerializationError` (I/O/parse only — not structural validation) | Keeps P2.3 and P2.4 error surfaces cleanly separated |
| Determinism | `docs/CHUNK_CONTRACT.md` §7; `write_manifest`'s fixed `json.dumps` parameters | Same fixed `json.dumps(..., indent=2) + "\n"` call, no non-deterministic fields | `write_chunks` byte-identical across runs on identical input |

---

## Construction Readiness Review

- [x] Serialization requirements frozen — §P1
- [x] Container schema frozen — §P2
- [x] Version strategy frozen — §P1.4, §P3.4
- [x] Serializer interface frozen — §P3.2
- [x] Repository integration complete — §P4
- [x] Repository artifact policy documented — §P4.6
- [x] Verification strategy complete — §P5
- [x] Serialization Traceability Matrix complete — §P7
- [x] Scope boundaries explicit — §P6

**Result: PASS.** No blocking gap was found for Serialization Planning itself. One forward dependency is recorded, not resolved: real end-to-end Serialization Construction against the actual corpus still depends on a `Document`/`KnowledgeSource` capability that does not yet exist (§P4.5) — an already-known gap (Contract §20) that also did not block Chunk Construction planning, for the identical reason.

---

## Stop Condition

Per the sprint's own governing instruction, this document ends here.

No serialization has been implemented. No Python code has been written. No runtime module (`sample_rag/chunker.py`) has been modified. `docs/CHUNK_CONTRACT.md` and `docs/adr/ADR-0001-chunk-persistent-representation.md` are unchanged. No commit has been made.

Awaiting review and approval before Sprint P2.3.2 (Serialization Construction) begins.
