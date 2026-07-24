# Chunk Builder — Implementation Plan

**Repository:** `ai-quality-engineering`
**Status:** Planning (Readiness Review — Sprint P2.2.0)
**Related documents:** `docs/CHUNK_CONTRACT.md` (frozen v1.0 — the only source of Chunk field/invariant truth), `docs/MILESTONE_1A.md` (build item 3, Indexing), `docs/architecture.md` (§5 Component Architecture, §6 Repository Structure, §7 Interface Design), `docs/glossary.md` (canonical terminology)

This document plans **how** Sprint P2.2.1 will realize the frozen Chunk Contract. It does not define what a Chunk is (that is `docs/CHUNK_CONTRACT.md`'s job, unchanged here) and it authorizes no implementation work by itself. It is a planning artifact only — no production code, tests, serialization, or validation logic is introduced by this document.

---

## Terminology Note

The sprint that commissioned this plan uses the working names "Chunk Builder" / "ChunkBuilder." Neither name appears in `docs/glossary.md` or `docs/architecture.md`. The repository's canonical name for this component is **Chunker**, with the frozen interface signature `Chunker.chunk(doc: Document) -> List[Chunk]` (`docs/architecture.md` §5). This plan uses "Chunker" for the component and "Chunk Builder" only when referring to the sprint by its own working title, to avoid introducing an unauthorized second name for the same component.

---

## 1. Implementation Boundaries (Priority 1)

### 1.1 Implementation Scope

Sprint P2.2.1 implements exactly one thing: the `Chunker` component's construction responsibility — given a document, produce an ordered `list[Chunk]` satisfying every invariant in `docs/CHUNK_CONTRACT.md` §17. Nothing else.

### 1.2 Implementation Assumptions

- **Input shape assumption (bounded, not a Document Data Model).** `docs/CHUNK_CONTRACT.md` §11 and §20 record, as an open and explicitly out-of-scope gap, that the runtime `Document` object returned by `KnowledgeSource.load()` has no frozen field-level schema. No `Document` class, loader, or `.docx`-parsing code exists anywhere in this repository today, and no `.docx` parsing dependency is declared in `requirements.txt`. This plan does not resolve that gap — resolving it would be Document Data Model design, which is out of scope for both the Chunk Contract and this plan. Construction (P2.2.1) is therefore planned against the **minimal shape the Chunk Contract itself already assumes**: an input exposing `.id: str` (equal to the corresponding `knowledge_manifest.json` `documents[].id`) and `.text: str` (the document's full extracted plain text). P2.2.1 must not build a `.docx` parser, a `KnowledgeSource` implementation, or a fuller `Document` schema under this scope — if real end-to-end input is needed for a demonstration, it is supplied by a test fixture, not by new pipeline code.
- **No referential integrity check.** Construction does not verify that `doc.id` actually exists in `knowledge_manifest.json`. That is explicitly deferred to P2.4 (`docs/CHUNK_CONTRACT.md` §11).
- **Single chunking strategy, not swappable.** Unlike `EmbeddingProvider`, `VectorStore`, `Retriever`, and `Generator` — which all have a stub-now/real-later split — chunking is "Structure-aware, deterministic → Unchanged" across every milestone (`docs/architecture.md` §8–§9 Milestone Capability Matrix: "Chunking ✅ ✅ ✅"). There is no Milestone 2 swap-in planned for `Chunker`, which is why it is absent from the four `Protocol` classes in `docs/architecture.md` §7 despite being listed as a component in §5.

### 1.3 Allowed Implementation Decisions

P2.2.1 may freely decide, because the Chunk Contract explicitly leaves these open:

- The concrete `id`-derivation mechanism, within the position-derived family (`document_id` + `chunk_index`, not content) frozen by Contract §10 / §14.1.
- The concrete `Chunk` representation (see §3.4 below for a non-binding recommendation).
- The concrete structural-boundary-detection algorithm (how resume headers / JD fields such as Responsibilities/Requirements are located) — `docs/MILESTONE_1A.md` build item 3 names the strategy category, not the algorithm.
- The concrete recursive-character fallback algorithm and its trigger condition.
- Internal module decomposition, helper naming, and the construction-error type name.
- Whether `Chunker` is exposed as a class with a `chunk` method or some other callable shape, provided the public call matches `Chunker.chunk(doc) -> List[Chunk]` (`docs/architecture.md` §5).

### 1.4 Prohibited Implementation Decisions

P2.2.1 must **not**:

- Modify `docs/CHUNK_CONTRACT.md`, `docs/MILESTONE_1A.md`, `docs/architecture.md`, or `docs/glossary.md` — all frozen/locked.
- Add, rename, or reinterpret any Chunk field. The six required fields (Contract §8) are the only fields; there is no optional tier (Contract §9).
- Implement `token_count`, `heading`, `section`, `page_number`, `embedding`, `embedding_model`, `vector_id`, `retrieval_score`, `rerank_score`, or `similarity_score` on `Chunk` — all ten are explicitly deferred (Contract §15).
- Change the offset convention (half-open `[start, end)`), the zero-based `chunk_index` convention, or the position-derived identity *family* — these are frozen decisions (Contract §7, §12, §13, §14.1), even though their concrete mechanisms are open.
- Implement Chunk serialization (P2.3) or Chunk validation (P2.4) — construction only.
- Implement a `Document` Data Model, a `.docx` parser, or a `KnowledgeSource` — out of scope, backlogged (Contract §20).
- Make recursive-character chunking the default path — it is fallback-only (`docs/MILESTONE_1A.md` build item 3).
- Add a new external dependency without a recorded scope decision (`docs/roadmap.md` §6, "Minimal dependencies").
- Import any embedding, vector-store, or LLM-evaluation library (`docs/MILESTONE_1A.md` Architectural Acceptance Criteria — this blanket constraint applies to every M1A component, `Chunker` included).

### 1.5 Acceptance Criteria (for P2.2.1's own Verification phase)

- Every Chunk Contract §17 invariant holds for chunks constructed from the real corpus resume document.
- Recursive-character fallback is demonstrably unused on the current corpus's structured documents (mirrors `docs/MILESTONE_1A.md` Functional Acceptance Criterion 1, restated here because it directly governs `Chunker`).
- `chunk()` performs no filesystem I/O, no network I/O, and mutates no shared/global state.
- Determinism holds: two calls against an identical input produce a structurally identical output list.
- No import of any embedding/vector-store/LLM-evaluation library.
- Malformed input (missing `.id`/`.text`, wrong types) raises a defined construction error rather than leaking an unrelated exception from internals.

---

## 2. Implementation Repository Discovery (Priority 2)

Findings, by repository evidence:

- **No `Chunker`, `Document`, or `Chunk` code exists anywhere in the repository.** `grep` for `class Chunk`, `class Document`, and `KnowledgeSource` across all Python files returns zero implementation matches — `KnowledgeSource` appears only as prose in `docs/`.
- **No `.docx`-reading capability exists.** `SUPPORTED_EXTENSIONS = {".docx", ".md", ".txt"}` in `scripts/build_manifest.py` only gates which files are *catalogued* (hashed and listed) — it never opens or parses their content. `requirements.txt` (`pytest`, `deepeval`, `promptfoo`, `ragas`, `pandas`, `python-dotenv`) declares no `.docx`/document-parsing library. Text extraction for the one real corpus document (`sample_rag/documents/resume/Karthik_SR_Resume_v2_2.docx`) is therefore not currently possible with anything in the repository. Recorded in §1.2 as a bounded, non-blocking planning assumption — not resolved here.
- **`tests/` contains only `.gitkeep`.** No existing tests can be leveraged; P2.2.1 starts unit testing from zero. No `pytest.ini`, `pyproject.toml`, `setup.cfg`, or `conftest.py` exists anywhere, so there is no established import-root convention for future test files either — a fact for P2.2.1 to account for when it writes its own tests, not something this plan resolves.
- **Existing reusable helper style: `scripts/build_manifest.py`.** This is the only implemented pipeline-adjacent module in the repository. It demonstrates the repository's working style for a deterministic-artifact builder: small, named, pure module-level functions (`discover_documents`, `normalize_source_path`, `compute_sha256`, `generate_document_id`, `build_document_entry`) composed by a thin orchestrator (`assemble_manifest`, `main`), with a dedicated exception type (`ManifestValidationError`) and an explicit `sorted(...)` call used specifically to force determinism over an otherwise OS-order-dependent `rglob`. This decomposition style is directly reusable as a *convention*, not as code (no function in `build_manifest.py` is itself reusable by `Chunker` — manifest entries carry no document text).
- **Dependencies already present:** stdlib only (`pathlib`, `hashlib`, `json`, `dataclasses`, `collections.abc.Mapping` are the only non-stdlib-adjacent imports seen across the repo so far). `dataclasses` is explicitly named in `docs/MILESTONE_1A.md`'s Libraries table for "structured configuration and the `RetrievalResult` contract itself" — direct precedent for representing contract-shaped entities as dataclasses.
- **Repository conventions confirmed:** no package directories exist anywhere (`find . -name "__init__.py"` returns nothing) — every module in the repository so far is a flat, standalone `.py` file. `docs/architecture.md` §6 names `sample_rag/retriever.py` and `sample_rag/generator.py` as the expected file-per-component convention for pipeline components, even though neither file exists yet.
- **New files likely required:** exactly one new module for Construction (location decided in §2.1 below); no new directories.

### 2.1 Repository Structure Assessment

**Question:** should `Chunker` follow `scripts/build_manifest.py`'s single-file pattern, get a dedicated module/package, or use another organization?

**Evidence:**

| Fact | Source |
|---|---|
| `scripts/` = "Operational scripts (e.g., dataset regeneration, report generation) — **not pipeline logic**." | `docs/architecture.md` §6 |
| `sample_rag/` = "The pipeline under test — `retriever.py`, `generator.py`, `documents/`. **This is the system being evaluated**, not the evaluation logic itself." | `docs/architecture.md` §6 |
| `Chunker` is listed in the Component Architecture table as a named pipeline component — same table row-shape as `Retriever` and `Generator` — with a declared interface `Chunker.chunk(doc: Document) -> List[Chunk]`, "Dependencies: Knowledge Source," "Current Milestone: 1A." | `docs/architecture.md` §5 |
| The Knowledge Manifest, whose builder lives in `scripts/`, is explicitly **not** a pipeline component: "The Knowledge Source owns the Knowledge Manifest... it is not a separate pipeline component or interface." | `docs/architecture.md` §5 |
| No package directory (`__init__.py`) exists anywhere in the repository; every existing module is a flat single file. | Repository scan |

**Recommendation:** a new file, `sample_rag/chunker.py`, following the `retriever.py` / `generator.py` naming convention already declared (but not yet instantiated) in `docs/architecture.md` §6 — **not** `scripts/build_chunker.py`, and **not** a new package directory.

**Why not the single-file `scripts/` pattern:** `build_manifest.py` combines discovery, assembly, serialization, and validation because the Knowledge Manifest is a cataloguing *artifact*, explicitly disclaimed as not being a pipeline component (`docs/architecture.md` §5). `scripts/` itself is defined as "not pipeline logic" (§6). `Chunker`, by contrast, is architecturally a pipeline component of the same class as `Retriever`/`Generator` — it is called at runtime by the CLI and depended on by the Indexer, not run occasionally to regenerate a catalogue. Placing it in `scripts/` would contradict §6's own stated boundary between operational tooling and pipeline logic.

**Why not a dedicated package/module directory:** nothing in the repository establishes that convention — zero `__init__.py` files exist anywhere, and `docs/architecture.md` §6 already names flat files (`retriever.py`, `generator.py`) as the expected shape for `sample_rag/` pipeline components. Introducing a package would be a new organizational pattern with no evidence behind it, and this sprint is explicitly barred from architectural redesign.

**Disposition:** `sample_rag/chunker.py`, a flat single file, internally decomposed into small named functions in the same style `build_manifest.py` already demonstrates (§2 above) — reusing the repository's existing *convention* for function decomposition without reusing `scripts/`'s *location*, since the two modules serve architecturally different roles.

---

## 3. Public Interface Planning (Priority 3)

This is not a new contract — it restates `docs/CHUNK_CONTRACT.md`'s existing guarantees in interface-planning terms and adds the input/exception/side-effect shape the Contract deliberately leaves to Construction.

### 3.1 Public API

```
Chunker.chunk(doc) -> list[Chunk]
```

Matches `docs/architecture.md` §5's frozen signature. `Chunker` is planned as a plain class exposing a `chunk` method — no `abc.ABC` or `typing.Protocol` machinery, unlike `EmbeddingProvider`/`VectorStore`/`Retriever`/`Generator`. This is not a deviation from repository convention: those four are `Protocol`-typed in `docs/architecture.md` §7 specifically because each has a stub-now/real-later swap planned for Milestone 2. `Chunker` has no such swap (§1.2 above) — it is fully real from Milestone 1A onward, so `Protocol` ceremony has no future implementation to decouple from.

### 3.2 Input Assumptions

- `doc` exposes `.id: str` and `.text: str` at minimum (§1.2). The full `Document` Data Model is not frozen and is not designed by this plan.
- `doc.text` is assumed to already be a stable, deterministic plain-text extraction (Contract §13's "reference frame" clause) — how that extraction happens is explicitly out of scope here and in the Contract.

### 3.3 Output Guarantees

- `list[Chunk]`, ordered ascending by `chunk_index`, which itself matches ascending `character_start` (Contract §12).
- Every returned `Chunk` satisfies all 8 invariants in Contract §17.
- An empty or entirely-unstructured-but-empty `doc.text` yields an empty list — zero chunks is a legal outcome (Contract §11: "a document produces zero or more chunks"), not an error.

### 3.4 Chunk Representation (recommended default, non-binding)

`docs/CHUNK_CONTRACT.md` §14.5 leaves the concrete representation open. This plan recommends `@dataclass(frozen=True)` for `Chunk`, consistent with `docs/MILESTONE_1A.md`'s Libraries table (`dataclasses` already named for contract-shaped entities such as `RetrievalResult`) and with Chunk's classification as a corpus-derived, immutable Persistent Canonical Artifact (Contract §5). P2.2.1 may deviate with justification; this plan does not freeze it.

### 3.5 Raised Exceptions

A dedicated exception — recommended name `ChunkConstructionError`, mirroring `ManifestValidationError`'s existing naming precedent — raised only on malformed input (`doc` missing `.id`/`.text`, or either field of the wrong type). Not raised for empty `doc.text` (§3.3).

### 3.6 Determinism Guarantees

Restates Contract §7: identical `doc` + identical algorithm ⇒ identical ordered `Chunk` list, field-for-field. No randomness, no wall-clock or timestamp dependence — mirrors the Knowledge Manifest's own removal of `created_at` for exactly this reason (`docs/MILESTONE_1A.md` build item 1, "Contract Change").

### 3.7 Side Effects

None. `chunk()` is planned as a pure function of its input: no filesystem I/O, no network I/O. This mirrors `build_manifest.py`'s own separation of pure transformation (`assemble_manifest`) from I/O (`write_manifest`, `load_manifest`) — Construction (P2.2) stays pure; Serialization (P2.3) is where persistence is introduced, exactly as the Contract's lifecycle table prescribes (Contract §5).

---

## 4. Construction Planning (Priority 4)

### 4.1 Implementation Pipeline (internal stages)

1. **Input validation** — confirm `doc` exposes the minimal assumed shape (§3.2); raise `ChunkConstructionError` on failure. Structural only — no check against `knowledge_manifest.json` (referential integrity is deferred to P2.4, Contract §11).
2. **Structural boundary detection** — locate section/field boundaries in `doc.text` per the primary strategy named (not algorithmically specified) in `docs/MILESTONE_1A.md` build item 3 (resume headers; JD fields such as Responsibilities/Requirements). The concrete algorithm is an allowed implementation decision (§1.3).
3. **Fallback boundary detection** — recursive-character chunking, invoked only when structural detection is insufficient or absent for a span. Kept as a distinct, separately testable path so the "fallback demonstrably unused in the default path" acceptance criterion (§1.5) stays checkable in isolation.
4. **Offset and index assignment** — for each detected span, compute `character_start`/`character_end` (half-open, Contract §13) and assign `chunk_index` in ascending order matching `character_start` (Contract §12).
5. **Identity derivation** — derive `id` from `(document_id, chunk_index)` per the position-derived family frozen in Contract §14.1; concrete mechanism is an allowed decision (§1.3).
6. **Chunk assembly** — construct each `Chunk` value, slicing `text = doc.text[start:end]` to satisfy the Contract's hard invariant (Contract §13).
7. **Internal invariant self-check (recommended, non-binding)** — before returning, verify the constructed list against Contract §17's 8 invariants. This is a construction-time sanity check, not a substitute for P2.4's standalone Chunk Validation, mirroring how `build_manifest.py` keeps `assemble_manifest` and `validate_manifest` as separate functions even though one could in principle call the other.

### 4.2 Module Organization

Single file, `sample_rag/chunker.py` (§2.1), decomposed as small module-level functions in the `build_manifest.py` style, e.g. (illustrative naming only — final names are an allowed P2.2.1 decision):

- `detect_structural_boundaries(text: str) -> list[tuple[int, int]]`
- `detect_fallback_boundaries(text: str) -> list[tuple[int, int]]`
- `generate_chunk_id(document_id: str, chunk_index: int) -> str`
- `build_chunk(document_id, chunk_index, start, end, text) -> Chunk`
- `Chunker.chunk(doc) -> list[Chunk]` (public orchestrator)

### 4.3 Dependency Flow

`doc` (minimal assumed shape, §3.2) → structural boundary detection → fallback boundary detection (only where needed) → offset/index assignment → per-span identity derivation and assembly → ordered `list[Chunk]`. No dependency on `Indexer`, `VectorStore`, `EmbeddingProvider`, or `knowledge_manifest.json` at construction time — matches Contract §11's explicit deferral of referential checks.

### 4.4 Deterministic Construction Strategy

Boundary detection must be a pure function of `doc.text` content only — no reliance on filesystem iteration order, wall-clock time, or any non-deterministic source. Direct precedent: `build_manifest.py`'s `main()` explicitly wraps `discover_documents`' `rglob` output in `sorted(...)` specifically to force determinism over an OS-unspecified iteration order. `Chunker` has no filesystem interaction at all (§3.7), so this class of non-determinism risk is structurally smaller, but any internal iteration (e.g., over candidate boundary matches) must preserve the same discipline.

### 4.5 Error Handling Boundaries

`ChunkConstructionError` (§3.5) is the only error surface, raised solely on malformed input. No I/O errors are possible in this stage (§3.7), unlike `build_manifest.py`'s `load_manifest`, which legitimately raises on file/JSON errors because it performs I/O.

---

## 5. Readiness Review (Priority 5)

| Item | Status |
|---|---|
| Repository discovery complete | ✅ Complete — §2 |
| Builder location selected | ✅ `sample_rag/chunker.py` — §2.1, evidence-based |
| Repository structure assessment completed | ✅ §2.1 — single-file `scripts/` pattern and new-package pattern both explicitly evaluated and rejected with evidence |
| Public interface defined | ✅ §3 |
| Public interface reviewed against `docs/architecture.md` | ✅ Matches §5's `Chunker.chunk(doc: Document) -> List[Chunk]` signature; `Protocol`-omission explained (§3.1) against §7 |
| Dependencies identified | ✅ Stdlib only, consistent with `docs/roadmap.md` §6. One bounded, non-blocking gap flagged: no `.docx`-extraction capability exists yet (§1.2, §2) — explicitly not resolved by this plan or by P2.2.1, scoped out to a minimal input assumption instead |
| Construction approach reviewed | ✅ §4 |
| No contract ambiguity remains | ✅ `docs/CHUNK_CONTRACT.md` is unambiguous on every field, invariant, and boundary this plan needed. The one open item (Document's schema) is the Contract's own recorded, deliberate backlog item (Contract §20), not an ambiguity in what Chunk itself is |
| Ready for implementation | ✅ Yes, bounded by §1.2's minimal input assumption |

**Result: PASS.** No blocking gap was found. The one genuine repository-evidenced gap — no `Document` Data Model and no `.docx`-extraction capability anywhere in the repository — is real, but it does not conflict with anything this plan needed to assume: `docs/CHUNK_CONTRACT.md` §11 already scoped its own dependency on `Document` down to a single equality assumption (`Document.id == knowledge_manifest.json documents[].id`), and this plan adopts that same minimal boundary rather than silently expanding Sprint P2.2.1 to also build a document loader. If Construction later needs a fuller `Document` shape or real `.docx` text for an end-to-end demonstration, that is a separate, explicitly out-of-scope dependency (Contract §20 backlog) — not something this plan resolves or defers silently.

---

## 6. Success Criteria Confirmation

- Implementation ambiguity removed: the location (§2.1), public interface (§3), and construction pipeline (§4) are all decided with repository evidence.
- Repository evidence supports every recommendation made (§2, §2.1).
- No architectural decision was reopened: `Chunker.chunk(doc) -> List[Chunk]` (`docs/architecture.md` §5) and every Chunk Contract field/invariant are used exactly as frozen.
- `docs/CHUNK_CONTRACT.md` is unchanged by this document.
- Implementation (Sprint P2.2.1) can begin immediately following approval of this plan.

---

*This document is a planning artifact for Sprint P2.2.1. It authorizes no implementation. Per the Implementation Track, this sprint (P2.2.0) ends at the Readiness Review above — Construction, Unit Testing, Verification, and Commit belong to P2.2.1 and are not performed here.*
