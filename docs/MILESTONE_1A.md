# Milestone 1A — Deterministic Foundation

**Project:** AI Quality Evaluation Suite (`ai-quality-engineering`)
**Roadmap reference:** `AI_QA_Learning_Roadmap_Scope.md` §1.6, §1.6.1
**Architecture reference:** `Session2_RAG_Architecture_Closure.md`, `AI_Systems_Diagnostic_Framework_v1.md`
**Status:** Locked. Implementation executed and validated; governance synchronized to the verified repository state at Sprint P3.7.2. No further architectural debate expected without a deliberate scope decision.

> **Milestone Synchronization Record (Sprint P3.7.2)** — build-item status, sprint references, acceptance-criteria status, Definition of Done status and milestone readiness are recorded at the end of this document. **No scope statement, contract, schema, acceptance criterion or Definition of Done item in this document was reworded, added or removed by that sprint.** The only in-place changes are checkbox marks against criteria verified complete.

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
- [x] CLI runs the full stub pipeline end-to-end locally with no external network or model calls
- [x] Full pytest suite passes

### Architectural

- [ ] `EmbeddingProvider` interface and retriever interface are defined and swappable — a stub implementation can be replaced without changing calling code
- [x] `RetrievalResult` is a defined dataclass (not a bare list) returned by every retrieval path, with deterministic, meaningful placeholder values in every field
- [x] `knowledge_manifest.json` exists and is the sole source of truth that freshness/hash validation checks against
- [x] Runtime Pipeline and Evaluation Assets exist as clearly separated modules/directories, not interleaved
- [x] Zero imports of any embedding, vector-store, or LLM-evaluation library anywhere in the codebase

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

## Milestone Synchronization Record — Sprint P3.7.2

Added by **Sprint P3.7.2 — Repository Governance Synchronization**, against the repository at commit `d9a6db4` with a clean working tree. Every row below traces to a committed repository authority. **This record synchronizes governance to the implementation; it defines no scope, adds no completion requirement, and changes no statement above it.**

Full derivation, cross-reference audit and Deferred Repository Items Register: `docs/P3.7.2_Repository_Governance_Synchronization_Report.md`.

### Build Item Matrix

| # | Build item | Implementing sprint(s) | Committed artifact | Executable evidence | Status |
|---|---|---|---|---|---|
| **1** | Knowledge Manifest | P1.2.0 (contract), P1.2.1–P1.2.2 (`92a35e9`, `19f8f48`), P1.3 (`25b6770`) | `sample_rag/knowledge_manifest.json`, `scripts/build_manifest.py` | W1 structural gate (3), W3 / DQ-1 freshness (2) | **Complete.** Digest `a1fa0857b723`. `documents[].indexed` is `false` for both entries — semantics open, see Deferred Register |
| **2** | Data Quality Validation | P3.1.8.1A–E (`78b5daf` … `3a32253`), P3.1.8.4 (`ea629b2`) | `tests/test_data_quality.py` | 14 specifications, DQ-1 … DQ-4; 23-mutant baseline | **Partially complete.** DQ-5, DQ-6, DQ-7 recorded **blocked** by `docs/DATA_QUALITY_VALIDATION_PLAN.md` §8.1, §11.2 W6, §16 O-6. Index Coverage Validation — this item's own clause — **is** DQ-7 |
| **3** | Indexing | Chunking: `e556a98`, `11299b7`. Placeholder vectors: **no sprint** | `sample_rag/chunker.py`, `sample_rag/chunks.json` (172 chunks) | `tests/test_chunker.py` — 17 | **Partially complete.** Structure-aware chunking with recursive-character fallback shipped; digest `323723b4fe82`. **No `Indexer`, no `EmbeddingProvider`, no placeholder vectors exist in the repository** |
| **4** | Retrieval | P3.3.1 — runtime committed under `dfe1b5b` (see Register §5) | `sample_rag/retriever.py`, `scripts/run_retrieval.py` | `RetrievalResult` exercised by 117 evaluation, 48 generation and 27 CLI specifications | **Complete for the corpus as committed.** Route `LEXICAL`. The SQL-filter stage is **not exercised** — the corpus carries no JobOps structured data; `diagnostics["sql_filter_applied"]` is `False` and unapplied filters are reported in `diagnostics["filters_ignored"]` rather than dropped |
| **5** | Generation | P3.5.1 (`dfbc86b`), P3.5.2 (`17d077b`) | `docs/GENERATION_CONTRACT.md` v1.0.0 **frozen**, `sample_rag/generator.py` | `tests/test_generator.py` — 48, mapping G-1 … G-14; 25 mutants, 25 killed | **Complete** |
| **6** | CLI | P3.6.0 (`b50e45f`) | `scripts/cli.py` | `tests/test_cli.py` — 27, six of them AST-structural; 25 mutants, 25 killed | **Complete.** As built the chain is Knowledge → Chunk Corpus → Retriever → Generator → CLI. There is **no Assembler**: `docs/GENERATION_CONTRACT.md` §21 excludes the Assemble stage from Milestone 1A and §22 / G-2 approves `Generator.generate(query, retrieval)`. A contract-approved deviation from build item 6's diagram, not a silent one |
| **7** | Golden Dataset | `39ed0e4`, `64a3e16` | `datasets/golden/resume_facts.json` (26 facts), `resume_qa_pairs.json` (22 pairs) | P3.4.1 — 16 + 14 | **Complete.** Digests `d5035f4013fc`, `c8c8f120f423` |
| **8** | Evidence Trace Dataset | `1a260af` | `datasets/golden/resume_evidence_trace.json` (22 entries) | P3.4.1 — 25, plus 16 cross-dataset integrity | **Complete.** Digest `f45c2c2f5f41` |
| **9** | Pytest Validation | P3.4.1 (`4705db4`) | `tests/` — 14 files | **372** specifications at `d9a6db4` | **Complete.** `docs/P3.4.1_Dataset_Authority_Validation_Report.md` records this sprint as completing build item 9 |
| **10** | Manual Review | P3.7.0 (`8e73173`), P3.7.1 (`d9a6db4`) | `docs/P3.7.0_Manual_Review_Evidence.md`, `docs/P3.7.1_Manual_Review_Report.md` | 16 manual verifications; 24 verification items, **24 PASS / 0 FAIL** | **Complete** |

**Seven of ten build items complete. Three partially complete** — items 2, 3 and 4, each with the gap and its owning authority named above. No build item is unstarted.

### Acceptance Criteria status

Checkbox marks above are set only where a committed authority establishes completion. Criteria left unchecked are recorded here with the evidence establishing that they are unmet — none was reworded, and none was removed.

| Criterion | Status | Evidence |
|---|---|---|
| **F-1** Structure-aware chunking on the resume **and at least one job description**, fallback demonstrably unused in the default path | **Partially met — unchecked** | Resume half met: 172 chunks, `tests/test_chunker.py`. Job-description half **not met** — the corpus catalogues two resume documents and no job description (`sample_rag/knowledge_manifest.json`) |
| **F-2** SQL-filter retrieval against real JobOps data, including an exclusion-criteria case | **Not met — unchecked** | The SQL-filter stage is not exercised; the corpus contains no JobOps structured data (`sample_rag/retriever.py` module docstring) |
| **F-3** CLI runs the full stub pipeline end-to-end locally with no external network or model call | **Met — checked** | `docs/P3.7.1_…` §3 V-23, V-24; `docs/P3.6.0_…` §3 |
| **F-4** Full pytest suite passes | **Met — checked** | 372 passed, `docs/P3.7.0_…` lines 1–5; V-04, V-05 |
| **A-1** `EmbeddingProvider` **and** retriever interfaces defined and swappable | **Partially met — unchecked** | Retriever half met — `RetrievalResult` returned on every path, stub swappable behind the frozen signature. `EmbeddingProvider` **is not defined anywhere in the repository** |
| **A-2** `RetrievalResult` is a dataclass with deterministic, meaningful placeholder values in every field | **Met — checked** | `sample_rag/retriever.py`; every field populated on both the match and no-match paths, none ever `None` |
| **A-3** `knowledge_manifest.json` is the sole source of truth for freshness/hash validation | **Met — checked** | W3 / DQ-1, `tests/test_data_quality.py` |
| **A-4** Runtime Pipeline and Evaluation Assets separated, not interleaved | **Met — checked** | `docs/architecture.md` §6; enforced structurally by the CLI and validator import specifications |
| **A-5** Zero imports of any embedding, vector-store or LLM-evaluation library | **Met — checked** | AST allowlist specifications in `tests/test_cli.py`, `tests/test_retrieval_metrics.py`, `tests/test_retrieval_diagnosis.py`, `tests/test_generator.py` |

### Definition of Done status

| Item | Status | Evidence |
|---|---|---|
| All build items 1–6 and 7–10 complete | **Not met** | Items 2, 3 and 4 partially complete (matrix above) |
| All Functional and Architectural acceptance criteria checked | **Not met** | F-1, F-2 and A-1 unchecked (table above) |
| Interfaces committed with docstrings explaining the Milestone 2 swap-in plan for each seam | **Met for every interface that exists** | `sample_rag/retriever.py`, `sample_rag/generator.py`, `sample_rag/knowledge_source.py`, `sample_rag/chunker.py`. Not assessable for `EmbeddingProvider` / `VectorStore`, which do not exist |
| All public contracts unchanged throughout implementation unless a documented contract gap is approved | **Met** | One approved gap pair — `docs/GENERATION_CONTRACT.md` §22, G-1 and G-2, Repository Owner, Sprint P3.5.1-G. One approved erratum — `docs/DOCUMENT_CONTRACT.md` §8.9, E-1. Both recorded in `docs/ENGINEERING_TRACEABILITY_REGISTER.md` §2 and §3.6 |
| `docs/architecture.md` committed as the canonical reference | **Met** | Committed; its §5 `Generator` row amendment remains a Repository Owner action per `docs/GENERATION_CONTRACT.md` §22 |
| Manual review pass on the Golden Dataset completed and logged | **Met** | `docs/P3.7.0_Manual_Review_Evidence.md`, assessed by `docs/P3.7.1_Manual_Review_Report.md` |
| Non-Goals list reviewed and confirmed untouched | **Met** | Audited at Sprint P3.7.2 against the repository: **no embedding library, vector store, LLM SDK, BM25, RRF or evaluation-tool module is imported anywhere** — the criterion A-5 states. No Out of Scope item has crept in. Recorded alongside it: `requirements.txt` *declares* `deepeval`, `promptfoo`, `ragas`, `pandas` and `python-dotenv`, and `evaluation/deepeval/`, `evaluation/promptfoo/` and `evaluation/ragas/` are empty scaffold directories. A declaration is not an import, so A-5 holds as written; the declarations are carried as a deferred item |

### North Star Question

> Can we deterministically trace every answer back to verified knowledge, without relying on any probabilistic AI component?

**Answered yes, by demonstration.** Three separate processes given identical input produced indistinguishable output; all 45 statements emitted across the manual review carry a chunk id, a document id and document-frame offsets; no model call, network call or external dependency occurred in the session. `docs/P3.7.1_…` §4 Finding 3, §6.4 — the demonstrated form this document's Success Criteria require.

**The North Star Question and the Definition of Done are answered separately, and only the first is answered yes.** Determinism and traceability are demonstrated; three Definition of Done items are not met. Both statements are true at `d9a6db4`, and neither substitutes for the other.

### Milestone readiness

Governance documentation is synchronized to the verified repository state. Milestone status is **unchanged by Sprint P3.7.2** — that sprint closed no milestone, froze no baseline, and resolved no deferred item. Closure sequencing (Canonical Document Marking → Milestone 1A Closure & Frozen Baseline) is a Repository Owner decision, informed by the Deferred Repository Items Register in `docs/P3.7.2_Repository_Governance_Synchronization_Report.md` §5.

---

## Repository Owner Scope Ruling — Sprint P3.7.3

Appended by **Sprint P3.7.4 — Repository Authority Synchronization**, implementing authorization **A1** of `docs/P3.7.3_Repository_Owner_Constitutional_Decision.md` (commit `180dcdc`). Like the Milestone Synchronization Record above, this is **appended governance state, not a revision of the locked scope.**

**Nothing above this section was modified.** The Definition of Done, every Acceptance Criterion and its checkbox state, every In Scope build item, the Out of Scope list, the Architectural Invariant, the Success Criteria, the Architecture Freeze and the Milestone Synchronization Record are all preserved verbatim.

### The ruling

`docs/P3.7.3_…` Decision 5 rules that:

1. **Milestone 1A establishes the repository's deterministic engineering baseline.** Its objective — the North Star Question — is met and demonstrated.
2. **Retrieval Infrastructure capabilities are constitutionally reassigned to Milestone 1B** — the Retrieval Infrastructure Foundation, established by `docs/P3.7.3_…` Decision 2 §2.2 and recognized in `docs/roadmap.md` §1.
3. **AI capabilities remain assigned to Milestone 2**, unchanged.
4. **Production regression capabilities remain assigned to Milestone 3**, unchanged.
5. The Milestone 1A **Definition of Done, Acceptance Criteria, In Scope, Out of Scope and Success Criteria remain textually unchanged.**

**This is engineering sequencing, not scope reduction.** No capability was removed from the repository. Eight capabilities that previously had no owning milestone — three of them with no owning sprint at all — now have one. The full reasoning, including why the two alternative constructions (implementing the items inside Milestone 1A, or rewording the Definition of Done) were rejected, is at `docs/P3.7.3_…` Decision 5 §5.2.

### Capabilities reassigned to Milestone 1B

Each row names the clause or criterion in this document that the capability belongs to, and the capability identifier under which it is now tracked in `docs/DEFERRED_ITEMS_REGISTER.md`.

| This document's clause or criterion | Capability reassigned | Register id | Constitutional authority |
|---|---|---|---|
| **Build item 2** — *Index Coverage Validation* clause | DQ-7, index-coverage validation | **1B-10** | `docs/P3.7.3_…` §3.1, §4.1 R-1B-10 |
| **Build item 3** — Index Layer clause | `Indexer` component (stub) | **1B-03** | `docs/P3.7.3_…` §3.1, §4.1 R-1B-03/04 |
| **Build item 3** — Index Layer clause | Deterministic placeholder vectors | **1B-04** | `docs/P3.7.3_…` §3.1, §4.1 R-1B-03/04 |
| **Build item 3**, **criterion A-1** | `EmbeddingProvider` interface | **1B-01** | `docs/P3.7.3_…` §3.1, §4.1 R-1B-01/02 |
| **Build item 3** (via `docs/architecture.md` §5, §7) | `VectorStore` interface | **1B-02** | `docs/P3.7.3_…` §3.1, §4.1 R-1B-01/02 |
| **Criterion F-1**, job-description half | Job Description corpus | **1B-05** | `docs/P3.7.3_…` §3.1, §4.1 R-1B-05/06/07/12 |
| **Criterion F-2** | JobOps structured data ingest | **1B-06** | `docs/P3.7.3_…` §3.1, §4.1 R-1B-05/06/07/12 |
| **Criterion F-2** | SQL filtering exercised, incl. an exclusion-criteria case | **1B-07** | `docs/P3.7.3_…` §3.1, §4.1 R-1B-05/06/07/12 |

Eight further capabilities are **affirmed** at Milestone 1B without having been Milestone 1A obligations — DQ-5, DQ-6, `documents[].indexed` semantics, `job_*`/`jobops_*` dataset population, O-5, I-6, P3.1.7-ARCH-01 and F-2-sym (register **1B-08, 1B-09, 1B-11, 1B-12, 1B-13, 1B-14, 1B-15, 1B-16**). They are recorded here only so the Milestone 1B set is legible from this document; none was ever required by the text above.

### Effect on the Definition of Done

**No Definition of Done item was reworded, added or removed.** The status of the two affected items is recorded below and nowhere else; the items themselves stand as written.

| Definition of Done item | Status | Recorded reason |
|---|---|---|
| *All Runtime Pipeline build items (1–6) and Evaluation Asset build items (7–10) complete* | **Annotated — not satisfied** | Build items 2 and 3 remain partially complete. The clauses that complete them — Index Coverage Validation, and the Index Layer with its `EmbeddingProvider` seam — are reassigned to Milestone 1B by this ruling |
| *All Functional and Architectural acceptance criteria checked* | **Annotated — not satisfied** | F-1, F-2 and A-1 remain unchecked, exactly as the Milestone Synchronization Record above records them. The capabilities that would check them are reassigned to Milestone 1B by this ruling |
| The remaining five items | **Met** | Unchanged from the Milestone Synchronization Record above |

**Milestone 1A closes with its Definition of Done annotated, not satisfied.** `docs/P3.7.3_…` Decision 5 §5.3 states the reason plainly: *"A closure that claimed satisfaction would be the first false statement in this repository's governance record."*

### The North Star Question is unaffected

> Can we deterministically trace every answer back to verified knowledge, without relying on any probabilistic AI component?

**Still answered yes, by demonstration.** This ruling reassigns capabilities; it touches no part of the demonstration recorded in the Milestone Synchronization Record above. `docs/P3.7.3_…` Decision 2 §2.1: the North Star Question and the Definition of Done are answered separately, and this ruling changes neither answer.

### Authority

| | |
|---|---|
| **Constitutional authority** | `docs/P3.7.3_Repository_Owner_Constitutional_Decision.md` — Decision 3 §3.1, Decision 4 §4.1, Decision 5, authorization **A1** |
| **Governance finding that produced it** | `docs/P3.7.2_Repository_Governance_Synchronization_Report.md` §5.1, §6.7 |
| **Canonical deferred-capability authority** | `docs/DEFERRED_ITEMS_REGISTER.md` |
| **Synchronization sprint** | `docs/P3.7.4_Repository_Authority_Synchronization_Report.md` |

---

*This document is locked. Revise only when Milestone 1A implementation surfaces a contract gap not anticipated here, or when Milestone 2 formally begins and this document is superseded. The Milestone Synchronization Record above is appended governance state, not a revision of the locked scope.*
