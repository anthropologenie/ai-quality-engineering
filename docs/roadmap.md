# AI Quality Engineering — Roadmap

**Owner:** Karthik S R
**Repository:** `ai-quality-engineering`
**Purpose:** Master execution plan for this repository — what is being built, why, in what order, how each stage is validated, and what is intentionally excluded. This document is the reference point for all future work here. Additions require a deliberate scope decision, not ad-hoc tool collecting.

**Guiding principle:**
> Become the engineer who can answer "How do we know our AI system is correct, reliable, repeatable, and production-ready?" — not an AI framework collector.

---

## 0. Current Repository Status

> **Status synchronized at Sprint P3.7.4**, under authorization **A4** of `docs/P3.7.3_Repository_Owner_Constitutional_Decision.md`. Two statements in this section were accurate when written and became false as the repository advanced — *"Milestone 0.5 … In progress"* and *"No pipeline code has been written yet, by design"* — as recorded by `docs/P3.7.2_Repository_Governance_Synchronization_Report.md` §4.2. Both are corrected below. The order in which milestones were executed, and the reasoning that produced them, are unchanged.

- **Milestone 0 (Repository Scaffold): Complete.** Directory structure exists — `docs/`, `datasets/golden/`, `evaluation/{deepeval,promptfoo,ragas}`, `sample_rag/`, `tests/`, `reports/{baseline,regressions}`, `scripts/`, `notebooks/`. Docs and data structure came first, by design; pipeline code followed under Milestone 1A. *(This line previously read `datasets/{rag,synthetic}`. `rag/` was renamed `golden/` during Milestone 1A — `datasets/README.md` Repository Note — and `synthetic/` was removed by Repository Owner decision **RO-05**. Amended here because the sentence states present repository structure, not Milestone 0 history.)*
- **Session 1 (LLM Core Six Baseline) and Session 2 (RAG Architecture Closure): Finalized.** Architecture is locked; no further architectural debate is scheduled. See Section 8 for a summary of decisions made in each session.
- **Milestone 0.5 (Documentation Synchronization): Complete.** This document is part of that synchronization — bringing architectural decisions that existed only in working notes into the repository itself, so the repository is self-contained and does not depend on external chat history to be understood. Its six documents are committed.
- **Milestone 1A (Deterministic Knowledge Pipeline): Implementation and validation complete; awaiting closure.** The full pipeline exists and runs end to end from a terminal; 372 executable specifications pass; manual review is complete and accepted. The North Star Question is answered **yes, by demonstration**. Three Definition of Done items remain unmet, and the capabilities that would meet them are constitutionally reassigned to Milestone 1B. Canonical record: `docs/MILESTONE_1A.md` — *Milestone Synchronization Record (P3.7.2)* and *Repository Owner Scope Ruling (P3.7.3)*.
- **Milestone 1B (Retrieval Infrastructure Foundation): Established, not started.** Constituted by `docs/P3.7.3_Repository_Owner_Constitutional_Decision.md` Decision 2. Its capability set is the canonical register at `docs/DEFERRED_ITEMS_REGISTER.md`.

---

# Documentation Map

These documents together form the repository documentation set:

| Document | Purpose |
|----------|---------|
| roadmap.md | Master execution plan for the repository |
| architecture.md | System architecture, repository boundaries, interfaces, and design decisions |
| altm.md | AI Lifecycle Traceability Model (ALTM) and diagnostic framework |
| glossary.md | Core terminology and metric definitions |
| interview-notes.md | Interview narratives, resume reinterpretation, and STAR mappings |
| learning-log.md | Historical progression of Sessions 1, 2, and future sessions |

---

## 1. Milestone Ordering

| Milestone | Scope |
|---|---|
| **Milestone 0** | Repository scaffold |
| **Milestone 0.5** | Documentation synchronization (`docs/roadmap.md`, `docs/architecture.md`, `docs/altm.md`, `docs/glossary.md`, `docs/interview-notes.md`, `docs/learning-log.md`) |
| **Milestone 1A** | Golden Dataset → Data Quality Validation → Deterministic Retrieval Pipeline → CLI |
| **Milestone 1B** | Retrieval Infrastructure Foundation — Index Layer, `EmbeddingProvider` / `VectorStore` interfaces, corpus expansion (job descriptions, JobOps), DQ-5 / DQ-6 / DQ-7 |
| **Milestone 2** | Embeddings, Vector Retrieval, Retrieval Evaluation (Ragas), Generation Evaluation (DeepEval) |
| **Milestone 3** | Regression (Promptfoo), Production Readiness |

**Milestone 1B — amendment recorded, Sprint P3.7.4, 2026-08-04.** This section previously stated *"There is no Milestone 1B."* Milestone 1B is established by `docs/P3.7.3_Repository_Owner_Constitutional_Decision.md` Decision 2 §2.2, and this table is amended under its authorization **A3**. **The reasoning behind the original statement is retained in full and still governs:** retrieval evaluation and generation evaluation are both Milestone 2 activities, gated behind a working deterministic pipeline from Milestone 1A — they are not a separate numbered milestone.

Milestone 1B contains **no evaluation activity whatsoever.** It contains only the deterministic retrieval infrastructure that Milestone 2's gate is itself composed of — the Index Layer, the `EmbeddingProvider` and `VectorStore` interfaces, corpus expansion, and the three blocked Data Quality checks. Ragas and DeepEval remain Milestone 2 exactly as this section has always required, and no capability moved out of Milestone 2 or Milestone 3.

Milestone 1B also **restores** Section 3's Locked Implementation Order rather than departing from it. That order is *Chunking → Indexing → Retrieval*; the repository executed Retrieval (Sprint P3.3.1) while Indexing was never built. Milestone 1B builds the missing stage. Section 3 is unchanged.

```
Milestone 0
Repository Scaffold
        │
        ▼
Milestone 0.5
Documentation Synchronization
        │
        ▼
Milestone 1A
Golden Dataset
        │
        ▼
Data Quality Validation
        │
        ▼
Deterministic Retrieval Pipeline
        │
        ▼
Milestone 1B
Index Layer
        │
        ▼
EmbeddingProvider / VectorStore Interfaces
        │
        ▼
Corpus Expansion (Job Descriptions, JobOps)
        │
        ▼
Milestone 2
Embeddings
Retrieval Evaluation
Generation Evaluation
        │
        ▼
Milestone 3
Regression
Production Readiness
```

---

## 2. Golden Dataset Design

The Golden Dataset is the reference corpus against which retrieval, generation, and evaluation are all validated. It is built before any embeddings, vector store, or LLM call — Milestone 1A implements it entirely in Python stdlib and pytest.

Every metric this project eventually reports (Faithfulness, Context Precision, Context Recall, and the rest) is only as trustworthy as the ground truth it is measured against. A passing DeepEval assertion says nothing about system quality if the underlying "correct answer" was never verified. This is the same discipline that already governs ETL testing on the resume — a transformation is not trusted until the source has been validated.

### 2.1 Data Sources

Reverse-engineered from real, evolving production data — not authored as synthetic examples:

- **Resume** — primary source of verified biographical and project fact
- **Job Descriptions** — JobOps-sourced
- **JobOps structured metadata** — SQLite database (application status, salary, location)
- Cover letters and portfolio documents — **future**, not in scope until produced

Real, evolving data surfaces production-realistic problems (a resume revision, a re-scraped job posting, a corrected fact) that a fixed synthetic dataset cannot, without requiring hand-maintenance of the eval set itself.

### 2.2 Question Generation Strategy

Core principle: **one verified fact → many question forms.**

For every fact in the resume already validated as accurate, derive multiple phrasings a real evaluator might ask. This produces genuine variation without inventing any new knowledge.

Example — resume fact: *"Led a cross-functional QA team of 5, owning test strategy and stakeholder communication."*

| Question | Category |
|---|---|
| How many engineers did Karthik lead? | Exact fact / lexical |
| Describe his leadership experience. | Summarization |
| Which project demonstrates leadership? | Reasoning / retrieval |
| Has he managed stakeholders? | Paraphrase |
| Give an example of cross-functional coordination. | Semantic / reworded |

This produces four question categories from a single fact — lexical, semantic, summarization, and reasoning — without a separate synthetic-question-writing effort.

### 2.3 Failure Taxonomy

The dataset intentionally includes difficult categories, not only happy-path questions. A dataset made only of easy factual lookups passes everything and reveals nothing.

| Category | Purpose | Example |
|---|---|---|
| **Exact Fact** | Tests deterministic retrieval | "What is Karthik's total experience?" |
| **Paraphrase** | Tests semantic retrieval | "What background does Karthik have in data engineering?" |
| **Multi-hop** | Requires combining multiple resume sections | "Which project best demonstrates AI Quality Engineering?" |
| **No Answer** | Tests abstention | "What Kubernetes cluster did he manage?" |
| **Stale Version** | Tests freshness | Historical knowledge vs. current canonical knowledge |
| **Contradiction** | Tests conflict handling | Historical knowledge conflicts with current canonical knowledge on the same fact |
| **False Premise** | Tests hallucination resistance | "Didn't Karthik work at Microsoft?" |

Each category is deliberately targeted at a different ALTM failure stage (see `docs/altm.md`) — the taxonomy gives the Milestone 1A data-quality pytest suite something concrete to validate against.

The **Stale Version** and **Contradiction** rows are expressed in terms of Historical Knowledge and Canonical Knowledge under Repository Owner ruling **R-01 — Historical Knowledge Semantics**, which retains historical knowledge *solely as evaluation evidence*; no document version is named. Their category names are unchanged: they are locked `failure_category` values in `datasets/golden/resume_qa_pairs.json`.

### 2.4 Evidence Trace Schema

A conventional golden dataset evaluates only the final answer. This is not sufficient to validate the hybrid retrieval architecture (Section 4) — a correct final answer can still hide a wrong retrieval route or an unintended reasoning shortcut.

The **Evidence Trace Dataset** extends each golden dataset entry to record the expected behavior of the whole pipeline, not just the expected output:

| Field | Purpose |
|---|---|
| Question | Test input |
| Ground Truth / Expected Answer | Ground truth |
| Expected Source | Correct document |
| Expected Chunk | Retrieval validation |
| Retrieval Evidence / Expected Route | BM25 / Vector / SQL / Hybrid |
| Expected Reasoning Type | Single-hop / Multi-hop / Aggregation |
| Evaluation Metrics | Faithfulness, Groundedness, Context Recall, Context Precision, Answer Relevancy |
| Expected Outcome | Answer / Abstain / Clarify |

This does not change the retrieval architecture itself — it changes what the Golden Dataset is capable of validating: whether the *architecture* behaved as designed, not only whether the *answer* happened to be correct. It is a data-schema decision, buildable entirely as labeled data in Milestone 1A — no embeddings or vector store required to define it, only to eventually validate against it in Milestone 2.

**Why this dataset is foundational:** without a golden, verified reference corpus, no downstream metric — retrieval or generation — has anything meaningful to be measured against. Building it first is not a detour from the pipeline; it is the precondition for the pipeline being testable at all.

---

## 3. Locked Implementation Order

```
Documentation
      │
      ▼
Golden Dataset
      │
      ▼
Data Quality Validation
      │
      ▼
Chunking
      │
      ▼
Indexing
      │
      ▼
Retrieval
      │
      ▼
Context Assembly
      │
      ▼
Evaluation
      │
      ▼
Generation
```

**Why data validation precedes pipeline construction:** building a chunker, indexer, or retriever against unvalidated data risks the same failure category already surfaced during Session 2 — a stale or malformed source silently producing plausible-looking but wrong output downstream. Data Quality Validation exists to catch that before any retrieval logic is trusted, the same discipline as validating source data before an ETL transformation runs.

---

## 4. Architecture Summary

Full detail lives in `docs/architecture.md`. Summary for roadmap context:

- **Pipeline stages:** Knowledge → Index → Retrieve → Assemble → Infer → Evaluate
- **Retrieval topology:** Hybrid — SQL structured filtering (JobOps) + BM25 + Vector search, merged via Reciprocal Rank Fusion (RRF)
- **Repository boundary:** `jobs-application-automation` (JobOps) is the production data source, read-only from this repository's perspective. `ai-quality-engineering` is the evaluation lab — it never writes back to JobOps.
- **Generation model (Milestone 2):** DeepSeek API
- **Design pattern:** Interface-first — `EmbeddingProvider` and vector-store access are defined as interfaces in Milestone 1A, with deterministic stub implementations; real implementations (BGE-small, FAISS) are swapped in at Milestone 2 without changing the interface contract.

The architecture describes how information flows through the system. ALTM describes how failures are localized across that lifecycle. The two are complementary: architecture explains system design; ALTM explains system diagnosis.

---

## 5. Evaluation Strategy

Evaluation is organized in four layers, each with a distinct responsibility. A system can pass one layer and fail another — they are not substitutes for each other.

| Layer | Responsibility | Tool | Notes |
|---|---|---|---|
| **Layer 1 — Data Quality** | Is the corpus itself trustworthy? Freshness, completeness, hashing, duplicate detection, chunk validity. | PyTest | Pure data engineering. No LLM call. Runs before any retrieval exists. |
| **Layer 2 — Retrieval Quality** | Did retrieval find the right evidence, and was it free of noise? | Ragas — Context Precision, Context Recall | Assumes the corpus itself is current — a stale corpus is a Layer 1 failure, not a Layer 2 one. |
| **Layer 3 — Generation Quality** | Is the model's output supported by what was retrieved? | DeepEval — Faithfulness, Groundedness, Hallucination Rate, Answer Relevancy | Checks consistency with retrieved context only — never whether that context was itself current or correct. A model can be 100% faithful to a stale document. |
| **Layer 4 — Regression** | Did a prompt, corpus, or code change silently degrade previously-correct behavior? | Promptfoo — re-run old vs. new, diff results | Not a pipeline stage at runtime. A comparison methodology applied across two full pipeline runs. |

This four-layer structure is the practical, tool-mapped expression of the ALTM stage-wise evaluation philosophy documented in `docs/altm.md` — each layer corresponds to specific ALTM stages, not to a specific tool's marketing scope.

---

## 6. Repository Principles

These are locked engineering principles governing all work in this repository:

- **Docs before code.** Architectural and scope decisions are written down and frozen before implementation begins.
- **Interface-first design.** Program to an interface (`EmbeddingProvider`, `retrieve()`), not to a specific implementation — implementations are swapped in later without changing calling code.
- **Deterministic implementation before AI.** Milestone 1A uses stub logic and placeholder vectors, not real embeddings or LLM calls — correctness of pipeline plumbing is proven before non-determinism is introduced.
- **Knowledge validation before retrieval.** Data quality is checked before it is trusted as a retrieval source (Section 3).
- **Small, demonstrable milestones.** Each milestone produces something inspectable and testable, not a partial, unverifiable state.
- **Evaluation-first mindset.** The evaluation plan (Section 5) is designed before the system being evaluated is built.
- **Minimal dependencies.** Milestone 1A is Python stdlib + pytest only. Dependencies are added only when a milestone specifically requires them.
- **Production thinking over demos.** This project is framed as a testing framework, not an AI chatbot demo — see Section 7 for what that excludes.

---

## 7. Scope Freeze

Explicitly excluded until Milestone 2 or later. Deferred intentionally, not forgotten — do not add these without a deliberate scope decision recorded in this document.

| Item | Status |
|---|---|
| Real embedding models (BGE-small, E5, Nomic) | Deferred to Milestone 2 |
| Vector databases (FAISS) | Deferred to Milestone 2 |
| Real BM25 implementation | Deferred to Milestone 2 |
| Hybrid retrieval (RRF) execution | Deferred to Milestone 2 |
| LangChain / LangGraph | Out of scope entirely |
| Agent orchestration, multi-agent frameworks | Out of scope entirely |
| MLflow | Conceptual only — not core to the 3-tool project |
| LangSmith | Conceptual only |
| Phoenix (Arize) | Name recognition only |
| Production orchestration, distributed retrieval, GPU optimization | Out of scope entirely |
| A second GitHub project | Not planned — one finished project over multiple partial ones |

Tool scope remains fixed at three: **DeepEval, Promptfoo, Ragas.** No further evaluation tools are added until these three are demonstrable end-to-end in this repository.

---

## 8. Session Progress Summary

### Session 1 — LLM Core Six Baseline

Established fluency with the six core LLM evaluation metrics, anchored to a real AAVA example (inconsistent Page Object Model generation count):

- Context Recall, Context Precision (retrieval stage)
- Faithfulness, Groundedness, Hallucination Rate (generation stage)
- Answer Relevancy (orthogonal to both — the only metric independent of truthfulness)

Key corrected distinction: retrieval cannot hallucinate — only generation can. Retrieval's only failure mode is pulling in real-but-irrelevant material (noise).

### Session 2 — RAG Architecture Closure

Closed the architecture debate for this repository, triggered by a real incident (a stale mounted document producing contradictory answers across two chats):

- Locked the seven-stage pipeline: Knowledge → Index → Retrieve → Assemble → Generate → Regression → Task Success
- Locked repository boundaries: `jobs-application-automation` (production, read-only source) vs. `ai-quality-engineering` (evaluation lab)
- Locked hybrid retrieval: SQL + BM25 + Vector → RRF
- Introduced the AI Lifecycle Traceability Model (ALTM) — a personal, explicitly-not-industry-standard framework for tracing information through an AI system stage by stage
- Introduced the Golden Dataset concept (Section 2 above), later expanded with the Failure Taxonomy and Evidence Trace Schema following external validation against independent industry sources

This history is preserved here as context for future contributors — no further architectural re-litigation is expected; the foundation is considered stable.

---

## 9. Interview Narrative — Resume Reinterpretation

Existing project experience is *relabeled* with AI QA vocabulary, not replaced with new stories. Full detail in `docs/interview-notes.md`.

| Resume experience | AI Quality interpretation |
|---|---|
| Eliminated duplicate-write collisions | Improved tool success rate, reduced retry failures |
| Confidence scoring in RCA agent | Output calibration / reasoning confidence |
| Evidence Retrieval → Reasoning Agent | RAG pipeline with retrieval + reasoning validation |
| GA4 data profiling (172 columns, 14 tables) | AI input data quality / reliability assessment |
| Redshift → Databricks migration | Data foundation supporting trustworthy AI systems |
| 10–15 min alert-to-RCA target vs. hours/days manual | Latency and cost-per-task improvement story |

---

## 10. Success Criteria

This roadmap is "done" when Karthik can:

- [ ] Explain precision/recall/F1 trade-offs with an RCA-pipeline example, not a textbook one
- [ ] Define the LLM core six metrics without hesitation and give a concrete example for each
- [ ] Map every Agent Evaluation metric to a specific HP RCA pipeline detail already on the resume
- [ ] Run DeepEval, Promptfoo, and Ragas against the sample RAG project and produce a results report
- [ ] Point to a live GitHub repo during an interview and walk through the evaluation pipeline end-to-end
- [ ] Deliver the STAR narrative fluently, in under 90 seconds

---

*This document is the baseline for the `ai-quality-engineering` repository. Any new tool, metric, or milestone addition should be weighed against Section 7 (Scope Freeze) before being added — the goal is depth on a small surface area, not breadth.*
