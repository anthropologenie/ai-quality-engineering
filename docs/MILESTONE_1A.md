# Milestone 1A — Deterministic Foundation

**Project:** AI Quality Evaluation Suite (`ai-quality-engineering`)
**Roadmap reference:** `AI_QA_Learning_Roadmap_Scope.md` §1.6, §1.6.1
**Architecture reference:** `Session2_RAG_Architecture_Closure.md`, `AI_Systems_Diagnostic_Framework_v1.md`
**Status:** Locked. Implementation may begin. No further architectural debate expected without a deliberate scope decision.

---

## North Star Question

> **Can we deterministically trace every answer back to verified knowledge, without relying on any probabilistic AI component?**

If yes — Milestone 1A has succeeded. If no — do not proceed to Milestone 2. Every build item and evaluation asset in this document exists to answer this one question. Any proposed addition should be checked against it before being added.

## Governing Principle

> **Milestone 1A validates contracts, not implementations.**

Interfaces, schemas, and manifests must be complete and meaningful now. The concrete engines behind them (real embeddings, real vector search, real LLM generation) are Milestone 2's job. This principle resolves most scope questions on its own — if something is about *what an interface promises*, it's in scope; if it's about *how well an implementation performs*, it's out.

> Every Milestone 2 component must replace an implementation behind an existing contract rather than introduce a new contract. Milestone 2 extends implementations; it should not reshape interfaces established here.

---

## Architecture: Two Independent Systems

Milestone 1A explicitly separates the system that will eventually serve answers from the system that proves those answers are correct. They evolve independently from this point forward.

### A. Runtime Pipeline

```
Knowledge
   │
   ▼
Indexer
   │
   ▼
Retriever
   │
   ▼
Assembler
   │
   ▼
Response Generator (stub)
   │
   ▼
CLI
```

### B. Evaluation Assets

```
Golden Dataset
   │
   ▼
Evidence Trace Dataset
   │
   ▼
Pytest Validation
   │
   ▼
Manual Review
```

**Assembler** deterministically converts retrieved chunks into the canonical context structure consumed by the Response Generator (stub). It performs no reasoning and makes no probabilistic decisions; its responsibility is only to prepare structured context.

These two tracks are built together in M1A but tracked and extended separately from here forward — this mirrors how production AI platforms keep the serving path and the evaluation harness as distinct systems.

---

## In Scope

### A. Runtime Pipeline — Build Items

1. **Knowledge Manifest** — `knowledge_manifest.json` cataloguing every document in the corpus. This is the single canonical description of what the corpus *is*; freshness checks validate against it rather than against scattered ad-hoc checks.

   **Contract status (frozen at Sprint P1.2.0):** the schema below defines what the Knowledge Manifest *is*. How it is generated, assembled, or serialized is an implementation concern for P1.2.1 and later — not defined here.

   **Schema:**

   | Field | Type | Purpose |
   |---|---|---|
   | `manifest_version` | string, `"1.0"` | Versions the Knowledge Manifest schema itself — independent of document content and independent of document versions. Exists solely for forward compatibility and schema evolution. |
   | `documents[]` | array | One entry per corpus document. |
   | `documents[].id` | string | Unique identifier for the document within the manifest. |
   | `documents[].source` | string | Filesystem path relative to `sample_rag/`. |
   | `documents[].hash` | string | SHA-256 digest of the document contents; the basis for freshness/integrity checks. |
   | `documents[].indexed` | boolean | Whether the document has been successfully processed by the indexing stage. |

   These are the only fields in the contract. This versioning is documentation-level forward compatibility, not a new subsystem — the manifest remains one file.

   **Manifest version format.** `manifest_version` is a Major.Minor string, frozen at `"1.0"`. It versions the Knowledge Manifest schema itself, independent of document versions, and exists for forward compatibility and schema evolution.

   **Version Evolution.** `manifest_version` changes only when the Knowledge Manifest schema itself changes. Changes to corpus contents, document hashes, or the set of catalogued documents (additions, removals, updates) do not change `manifest_version`.

   **Artifact relationship.** `manifest_version` versions the Knowledge Manifest. `schema_version` (`datasets/SCHEMA.md`) versions Golden Dataset artifacts. They are independent schema contracts.

   **Deterministic artifact contract.** The Knowledge Manifest is a deterministic artifact: an identical corpus produces an identical Knowledge Manifest. Deterministic generation is a contractual requirement of this specification — every conforming implementation of the Knowledge Manifest must preserve this property.

   **Contract Change — `created_at` removed.** An earlier draft of this contract included `created_at` (manifest creation timestamp). It has been intentionally removed, not silently dropped:
   - A creation timestamp is operational provenance, not a description of the corpus, and its presence would make the manifest non-deterministic for an identical corpus generated at two different times — in direct conflict with the deterministic artifact contract above.
   - Operational provenance is out of scope for Milestone 1A.
   - Future schema evolution may introduce provenance metadata if a concrete need justifies it; no such mechanism is designed by this note.

   **Document version responsibility.** The Knowledge Manifest schema does not carry document version information. Filenames remain the authoritative source of document versioning; the manifest intentionally does not duplicate that metadata.

   - Validated by: one pytest suite running hash comparison against the manifest. No separate validation subsystem — this stays a file plus a check.

   **Document contract status (frozen at Sprint P2.5):** `Document` — the runtime entity `KnowledgeSource.load()` returns, distinct from the `documents[]` catalogue entries above — is defined in `docs/DOCUMENT_CONTRACT.md`, not here.

2. **Data Quality Validation** — resume validation, chunk validation, metadata validation, Index Coverage Validation. Index Coverage Validation ensures every chunk produced during indexing has a deterministic placeholder representation behind the `EmbeddingProvider` interface. This validates indexing completeness rather than real embedding quality. Pure Python, pure pytest, no external model calls.

3. **Indexing** — structure-aware chunking (primary strategy: section/field-based boundaries — resume headers, JD fields like Responsibilities/Requirements). Recursive-character chunking exists only as a fallback for unstructured overflow, never the default. Deterministic placeholder vectors/hashes stand in for real embeddings, behind the `EmbeddingProvider` interface.

   **Contract status (frozen at Sprint P2.1):** the canonical Chunk Data Model and Chunk Contract are defined in `docs/CHUNK_CONTRACT.md`, not here.

4. **Retrieval** — SQL-filter stage implemented for real (JobOps structured queries: salary, location, application status, exclusion criteria per `Career_Strategy_and_Search_Preferences.md` §4). Semantic stage stubbed behind the retriever interface.
   - **Contract:** `retrieve(query, filters) -> RetrievalResult`, not a bare `List[Chunk]`. `RetrievalResult` carries `chunks`, `retrieval_route`, `score`, and `diagnostics` — all populated with deterministic placeholder values in M1A, not `None`. Example:
     ```python
     RetrievalResult(
         chunks=[...],
         retrieval_route="SQL",
         score=1.0,
         diagnostics={
             "matched_fields": ["skills"],
             "retrieval_time_ms": 0,
             "stub": True,
         },
     )
     ```
     Placeholder values are meaningful, not arbitrary — they let the pytest suite assert on structure *and* semantics now (e.g. `diagnostics["stub"] is True`), so Milestone 2 swaps values inside an already-correct shape rather than changing the shape itself.

5. **Generation** — deterministic Response Generator (stub). Real DeepSeek integration deferred to Milestone 2; the seam is forward-compatible now.

6. **CLI** — ties Knowledge → Indexer → Retriever → Assembler → Response Generator (stub) into local, reproducible runs.

### B. Evaluation Assets — Build Items

7. **Golden Dataset** — reverse-engineered from verified resume facts, one fact → many question forms (lexical, semantic, summarization, reasoning categories).

8. **Evidence Trace Dataset** — extends each Golden Dataset entry with: Question, Expected Answer, Expected Source, Expected Chunk, Expected Retrieval Route, Expected Reasoning Type, Expected Metrics, Expected Outcome. Includes the full failure taxonomy: Exact Fact, Paraphrase, Multi-hop, No Answer, Stale Version, Contradiction, False Premise.

9. **Pytest Validation** — pytest suite run against both datasets.

10. **Manual Review** — manual review pass completed and logged before any automated scoring is trusted downstream.

### Libraries (stdlib-only)

| Purpose | Library | Why |
|---|---|---|
| Testing | `pytest` | Executable QA, matches existing ETL testing discipline |
| Interfaces | `abc`, `typing.Protocol` | Decouple contracts from implementations |
| Storage | `sqlite3` | Local structured access to JobOps data |
| Freshness validation | `hashlib` | Content-hash + timestamp checks against the Knowledge Manifest |
| CLI | `argparse` | Deterministic, reproducible local execution |
| Logging | `logging` | Trace pipeline execution across stages |
| Config | `dataclasses` | Structured configuration and the `RetrievalResult` contract itself |

No embedding library, vector store, LLM SDK, or evaluation-tool dependency (DeepEval/Promptfoo/Ragas) is imported anywhere in the M1A codebase.

### Stretch Goal (Optional — Not Required for Completion)

Implement SQL retrieval and the semantic stub concurrently using `concurrent.futures`, to demonstrate that interface independence enables parallel execution. This directly addresses the parallelism gap observed in AAVA, but concurrency is an *execution* concern, not an *architectural* one — Milestone 1A proves the pipeline shape is correct, not that it's fast. Parallelism should emerge naturally once interfaces are stable, not be forced in as a requirement.

---

## Out of Scope / Non-Goals

One canonical list — do not duplicate this elsewhere, and do not add to it without a deliberate scope decision per the roadmap's own discipline.

- Real embedding model integration (BGE-small or any alternative)
- FAISS or any real vector store
- Real BM25 implementation
- Hybrid retrieval / RRF merge logic
- Ragas, DeepEval, Promptfoo — any of the three evaluation tools
- Real DeepSeek (or any) LLM generation
- Retrieval quality optimization or benchmarking
- Embedding model benchmarking
- Prompt optimization
- Agent orchestration (CrewAI or otherwise)
- Performance optimization of any kind
- Semi-structured data sources (LinkedIn/Greenhouse/Lever JSON) — deferred until JobOps genuinely ingests these
- A second GitHub project

All of the above are Milestone 2+ concerns, already deferred in `Session2_RAG_Architecture_Closure.md`.

---

## Acceptance Criteria

### Functional

- [ ] Chunking correctly applies structure-aware splitting on the resume and at least one job description, with recursive-character fallback demonstrably unused in the default path
- [ ] SQL-filter retrieval returns correct results against real JobOps data, including at least one exclusion-criteria case (e.g. Selenium-only)
- [ ] CLI runs the full stub pipeline end-to-end locally with no external network or model calls
- [ ] Full pytest suite passes

### Architectural

- [ ] `EmbeddingProvider` interface and retriever interface are defined and swappable — a stub implementation can be replaced without changing calling code
- [ ] `RetrievalResult` is a defined dataclass (not a bare list) returned by every retrieval path, with deterministic, meaningful placeholder values in every field
- [ ] `knowledge_manifest.json` exists and is the sole source of truth that freshness/hash validation checks against
- [ ] Runtime Pipeline and Evaluation Assets exist as clearly separated modules/directories, not interleaved
- [ ] Zero imports of any embedding, vector-store, or LLM-evaluation library anywhere in the codebase

---

### Architectural Invariant

Every Runtime Pipeline stage must expose a typed input and typed output. Stages communicate exclusively through defined contracts and never through another stage's internal state.

This invariant reinforces the interface-driven architecture and ensures future Milestone 2 implementations remain swappable.

---

## Success Criteria

Milestone 1A is "done" when you can:

- Walk through Knowledge → Indexer → Retriever → Assembler → Response Generator (stub) and point to a real, working stdlib component at each stage
- Explain, using the resume-version example, why a stale corpus is a Knowledge-stage failure and not a Retrieval-stage one
- Show a reviewer the Golden Dataset and Evidence Trace schema and justify why ground truth had to exist before any metric could be trusted
- Answer the North Star Question with a demonstrated "yes," not an assertion

---

## Definition of Done

- All Runtime Pipeline build items (1–6) and Evaluation Asset build items (7–10) complete
- All Functional and Architectural acceptance criteria checked
- Interfaces committed with docstrings explaining the Milestone 2 swap-in plan for each seam
- All public contracts remain unchanged throughout Milestone 1A implementation unless a documented contract gap is discovered and explicitly approved
- `docs/architecture.md` (the Session 2 pipeline diagram) committed as the canonical reference
- Manual review pass on the Golden Dataset completed and logged
- Non-Goals list reviewed and confirmed untouched — no premature Milestone 2 dependency has crept in

---

## Architecture Freeze

Milestone 1A architecture is now frozen.

Future implementation work should focus on building and validating the documented contracts rather than redesigning them.

Any newly discovered optimization, library, feature request, orchestration capability, evaluation framework, or performance improvement should be recorded for Milestone 2 unless it exposes a genuine contract gap or contradiction with the North Star Question.

---

*This document is locked. Revise only when Milestone 1A implementation surfaces a contract gap not anticipated here, or when Milestone 2 formally begins and this document is superseded.*
