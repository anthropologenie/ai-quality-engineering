# Glossary

**Repository:** `ai-quality-engineering`
**Status:** Milestone 0.5 — Canonical Vocabulary Locked
**Related documents:** `docs/roadmap.md`, `docs/architecture.md`, `docs/altm.md`, `docs/interview-notes.md`

This document is the canonical terminology reference for the repository. Every term defined here has exactly one authoritative definition. Other documents apply these terms; they do not redefine them.

---

## 1. Purpose

Terminology drift is a real engineering risk on a project that spans multiple documents authored over multiple sessions — the same concept described slightly differently in the roadmap, the architecture spec, and the diagnostic framework eventually produces confusion about whether two similarly-worded things are actually the same thing.

This repository intentionally separates:

- **Definitions** (this document) — what a term means
- **Architecture** (`docs/architecture.md`) — how the system is designed
- **Diagnostics** (`docs/altm.md`) — how failures are traced
- **Execution planning** (`docs/roadmap.md`) — what gets built, in what order

A term should be defined here once, then referenced everywhere else. If a document needs to explain a concept in more depth than a glossary entry allows, it should expand on the *application* of the term, not restate its definition.

## Documentation Hierarchy

The repository documentation is intentionally layered, each document building on the one above it:

```text
roadmap.md
      │
      ▼
architecture.md
      │
      ▼
altm.md
      │
      ▼
glossary.md
      │
      ▼
implementation
```

`roadmap.md` defines execution strategy. `architecture.md` defines system design. `altm.md` defines diagnostic reasoning. `glossary.md` defines repository terminology. Implementation applies all four.

## Document Roles

Each repository document has one primary responsibility:

| Document | Primary Responsibility |
|-----------|------------------------|
| `docs/roadmap.md` | Defines execution strategy and milestone sequencing. |
| `docs/architecture.md` | Defines system structure, components, interfaces, and technical design. |
| `docs/altm.md` | Defines the diagnostic reasoning framework used to localize failures. |
| `docs/glossary.md` | Defines canonical repository terminology used throughout the documentation. |
| `docs/interview-notes.md` | Translates repository concepts into interview-ready explanations and discussion points. |
| `docs/learning-log.md` | Records the evolution of understanding, design decisions, and milestone progression over time. |

Each document has a single primary responsibility, and documents intentionally reference each other rather than duplicate content — this separation of concerns improves maintainability and reduces terminology drift as the repository evolves.

---

## 2. How to Use This Glossary

This document defines terms. Other documents apply them. When a concept is first introduced in another document, that document should cross-reference this glossary rather than re-explaining the concept inline.

Entries are grouped by category (Sections 3–7) and alphabetized within each category — this is a lookup reference, not a narrative, and is meant to be searched, not read start to end.

## Definition Rules

Every glossary entry follows the same structure:

| Element | Purpose |
|---|---|
| Definition | What the term means |
| Why it Matters | Why the repository cares about it |
| Used In | Where it appears |

Future glossary entries should follow the same pattern whenever applicable. This does not change the existing entries above, which already convey the same information in a denser table form.

## Cross-reference Philosophy

This glossary owns terminology. `architecture.md` owns structural design. `altm.md` owns failure diagnosis. `roadmap.md` owns execution planning.

Documents should reference each other rather than duplicate explanations. Introducing a new concept should generally involve:

1. Add the definition here.
2. Apply it in architecture or ALTM.
3. Reference it elsewhere.

---

## 3. Core Repository Concepts

| Term | Definition | Used In |
|---|---|---|
| **AI Quality Engineering** | The discipline this repository practices: applying engineering-grade validation (verified ground truth, layered testing, regression detection) to AI system behavior, rather than informal manual spot-checking. | `roadmap.md`, `architecture.md` |
| **Chunk** | A single retrievable unit of text produced by splitting a document — the smallest span retrieval operates on. | `roadmap.md`, `architecture.md`, `altm.md` |
| **Chunking** | The process of splitting a validated document into chunks, performed at the Index stage. | `architecture.md`, `altm.md` |
| **Context Builder** | The component responsible for assembling retrieved chunks into a final prompt within budget. Owns the Assemble stage. | `architecture.md`, `altm.md` |
| **Context Window** | The bounded input space available to the generation model; retrieved content that doesn't fit is dropped or truncated at the Assemble stage. | `architecture.md`, `altm.md` |
| **Corpus** | The full set of validated source documents (resume, job descriptions, JobOps data) available to the pipeline at a given point in time. | `roadmap.md`, `architecture.md`, `altm.md` |
| **Deterministic Pipeline** | A pipeline implementation using stub logic and placeholder vectors instead of real embeddings or LLM calls, so plumbing correctness can be proven before non-determinism is introduced. The defining characteristic of Milestone 1A. | `roadmap.md`, `architecture.md` |
| **Embedding Provider** | The interface (`EmbeddingProvider`) responsible for converting text into vector representations. Defined in Milestone 1A; implemented for real (BGE-small-en-v1.5) in Milestone 2. | `architecture.md` |
| **Evaluation Engine** | The component that scores pipeline output against the Golden Dataset across the four evaluation layers. Owns the Evaluate and Final Answer stages. | `architecture.md`, `altm.md` |
| **Evaluation Layer** | One of four distinct evaluation responsibilities (Data Quality, Retrieval Quality, Generation Quality, Regression), each mapped to a specific tool and a specific set of ALTM stages. See `roadmap.md` Section 5 and `altm.md` Section 9. | `roadmap.md`, `altm.md` |
| **Evidence Trace Dataset** | An extension of the Golden Dataset that records the expected *behavior* of the whole pipeline for each question (expected source, chunk, retrieval route, reasoning type, metrics, outcome) — not only the expected answer. | `roadmap.md` |
| **Failure Localization** | The act of identifying which specific pipeline stage is responsible for an observed incorrect output. The primary operational purpose of ALTM. | `altm.md` |
| **Generator** | The component that produces an answer from an assembled prompt. Owns the Infer stage. Stubbed deterministically in Milestone 1A; DeepSeek API in Milestone 2. | `architecture.md`, `altm.md` |
| **Golden Dataset** | The verified, reference corpus of questions and expected answers, reverse-engineered from real resume and JobOps data, against which retrieval, generation, and evaluation are all validated. Built before any embeddings or LLM calls exist in the pipeline. | `roadmap.md`, `altm.md` |
| **Ground Truth** | A verified correct answer or fact, anchored to a specific source document, used as the basis for evaluation. The Golden Dataset exists to make ground truth trustworthy before any metric is measured against it. | `roadmap.md` |
| **Hybrid Retrieval** | The retrieval topology combining structured SQL filtering, BM25 keyword search, and vector search, merged via Reciprocal Rank Fusion (RRF). Locked in Session 2; implemented for real in Milestone 2. | `roadmap.md`, `architecture.md` |
| **Index** | (1) As a stage: converting validated documents into retrievable chunks and vectors. (2) As a noun: the resulting lookup structure produced by the Indexer. | `architecture.md`, `altm.md` |
| **Knowledge Manifest** | The canonical catalogue of the corpus (`knowledge_manifest.json`), produced by the Knowledge Source. Records `id`, `source`, `hash`, and `indexed` for every document. Used by corpus integrity and freshness validation. | `MILESTONE_1A.md`, `architecture.md` |
| **Knowledge Source** | The component exposing validated resume, job description, and JobOps data to the rest of the pipeline. Owns the Knowledge stage. | `architecture.md`, `altm.md` |
| **Production Readiness** | The Milestone 3 objective — hardening the pipeline and its documentation (benchmark reports, regression automation) to a standard suitable for citing as a finished artifact, distinct from further feature expansion. | `roadmap.md`, `architecture.md` |
| **Regression** | A change in a prompt, corpus, or code that silently degrades previously-correct pipeline output. Detected by re-running identical test cases against an old vs. new version and diffing results (Promptfoo, Layer 4). | `roadmap.md`, `altm.md` |
| **Retriever** | The component that returns ranked evidence for a query. Owns the Retrieve stage. SQL-filter stage real in Milestone 1A; full hybrid fusion in Milestone 2. | `architecture.md`, `altm.md` |
| **Root Cause** | The specific stage, component, and metric that explains an observed failure, identified by tracing upstream through the ALTM workflow rather than fixing the stage where the symptom was first noticed. | `altm.md` |
| **Vector Store** | The interface (and, in Milestone 2, FAISS implementation) responsible for persisting and querying vector representations of chunks. | `architecture.md` |

---

## 4. Evaluation Terminology

| Term | Definition | Stage | Used In |
|---|---|---|---|
| **Answer Relevancy** | Whether the generated answer directly and completely addresses what was actually asked, independent of whether it is true. The only Core Six metric independent of truthfulness. | Final Answer | `roadmap.md`, `altm.md` |
| **Context Precision** | Of everything retrieved, how much was actually relevant versus noise. | Retrieve | `roadmap.md`, `architecture.md`, `altm.md` |
| **Context Recall** | Of everything relevant that exists in the corpus, how much was actually retrieved. | Retrieve | `roadmap.md`, `architecture.md`, `altm.md` |
| **Evaluation Harness** | The overall test infrastructure (pytest suite, Ragas config, DeepEval metrics, Promptfoo suite) responsible for actually running evaluation — as distinct from the metrics it computes. A harness that silently fails to run is itself an Evaluate-stage failure. | Evaluate | `altm.md` |
| **Faithfulness** | Whether everything the model claimed is supported or entailed by the retrieved context. | Infer | `roadmap.md`, `architecture.md`, `altm.md` |
| **Groundedness** | Whether every important claim in the output can be traced to a specific, citable piece of retrieved evidence — stricter than Faithfulness, closer to individual claim-level sourcing. | Infer | `roadmap.md`, `altm.md` |
| **Hallucination Rate** | Of everything the model claimed, how much was fabricated or unsupported. Usually the near-complement of Faithfulness, but not guaranteed to sum to 100% once partial or ambiguous claims exist. | Infer | `roadmap.md`, `altm.md` |

**Retrieval metrics** (Context Precision, Context Recall) measure what was fetched and never touch what is eventually said. **Generation metrics** (Faithfulness, Groundedness, Hallucination Rate) measure what was said against what was fetched, and never touch whether the fetched material was itself current or correct. This distinction is load-bearing throughout `altm.md` — see Section 6 of that document.

---

## 5. ALTM Terminology

Terms specific to failure diagnosis. Full context in `docs/altm.md`; not re-explained here beyond definition.

| Term | Definition |
|---|---|
| **Corrective Action** | The fix scoped to the specific stage identified as the root cause — never applied broadly across the pipeline based on where a symptom was merely observed. |
| **Detection** | The specific check, test, or metric that confirms or rules out a given stage as the source of a failure (e.g., a hash mismatch detects a Knowledge-stage failure). |
| **Downstream** | Any stage later in the pipeline order than the stage currently under investigation. Downstream stages inherit the effects of upstream failures. |
| **Evidence** | The concrete output of a stage-specific check (a hash comparison, a chunk coverage report, a metric score) used to rule a stage in or out — as distinct from intuition about which stage "seems" responsible. |
| **Failure Propagation** | The tendency of an early-stage failure to make every downstream stage appear broken, even though only one stage is actually at fault. The reason the ALTM workflow moves strictly upstream to downstream. |
| **Lifecycle Stage** | One of the eight stages information passes through (Knowledge, Index, Retrieve, Assemble, Infer, Post-Process, Evaluate, Final Answer), each with distinct inputs, outputs, and failure modes. |
| **Primary Origin** | The first stage in pipeline order where a check genuinely fails — the target of failure localization, as opposed to every stage that merely appears affected. |
| **Symptom** | The observable manifestation of a failure (e.g., "hallucinated fact," "stale answer") as distinct from its root cause, which may originate several stages earlier. |
| **Upstream** | Any stage earlier in the pipeline order than the stage currently under investigation. Diagnosis always checks upstream stages before concluding a later stage is at fault. |

---

## 6. Architecture Terminology

| Term | Definition |
|---|---|
| **Component** | A named unit of the system with defined responsibilities, an interface, and a current implementation status (stub or real) — e.g., Retriever, Generator, Context Builder. |
| **Interface** | A defined contract (method signatures, not implementation) that a component is called through, allowing the underlying implementation to change without affecting calling code. |
| **Milestone** | A numbered, bounded phase of implementation (0, 0.5, 1A, 2, 3) producing an inspectable, demonstrable artifact. New milestones require a deliberate scope decision recorded in `docs/roadmap.md`. |
| **Protocol** | The Python typing construct used to express an Interface in this repository's code (e.g., `class EmbeddingProvider(Protocol)`) without requiring inheritance. |
| **Repository Boundary** | The one-directional data relationship between `jobs-application-automation` (production, read-only source) and `ai-quality-engineering` (evaluation lab, no write-back). |
| **Scope Freeze** | A locked decision that a category of technology, tool, or capability is intentionally excluded from active work until a specific, later milestone — deferred, not forgotten. |

---

## Notational Conventions

Naming conventions used throughout the documentation:

- Repository components (Retriever, Generator, Context Builder) are capitalized because they refer to named software components.
- Lifecycle stages (Knowledge, Retrieve, Infer, Post-Process) are capitalized because they refer to specific ALTM stages.
- General engineering concepts (retrieval, prompt, generation, embedding) remain lowercase unless referring to a defined repository concept.

This convention improves consistency across documentation and code.

---

## 7. Repository Conventions

These are conventions specific to this repository's working practice, not general industry definitions.

| Term | Definition |
|---|---|
| **Docs Before Code** | The practice of writing and freezing architectural and scope decisions before implementation begins on a given milestone. |
| **Evaluation-First** | The practice of designing the evaluation strategy for a component before the component itself is built. |
| **Interface-First** | The practice of defining a component's interface (Section 6) before any concrete implementation exists behind it. |
| **JobOps** | Shorthand for `jobs-application-automation`, the production repository this project consumes data from. |
| **Milestone 1A** | The current milestone: deterministic pipeline, Golden Dataset, Data Quality Validation, stub interfaces, no embeddings or LLM calls. |
| **Milestone 2** | Real embedding model, FAISS vector store, real BM25, full hybrid retrieval, Ragas and DeepEval activation. |
| **Milestone 3** | Promptfoo regression activation and production-readiness hardening. |
| **Read-only** | The access level this repository holds over JobOps data — data is consumed but never modified or written back. |
| **Real Implementation** | A production-grade implementation behind an interface (e.g., FAISS behind `VectorStore`), as distinct from a Stub. |
| **Small Demonstrable Milestones** | The practice of scoping each milestone to something inspectable and testable on its own, rather than a partial, unverifiable state. |
| **Source of Truth** | JobOps's role relative to this repository — the authoritative version of resume, job, and application data that this repository's corpus must stay synchronized against. |
| **Stub** | A deterministic placeholder implementation behind an interface (e.g., placeholder vectors behind `EmbeddingProvider`), used in Milestone 1A to prove pipeline correctness before a Real Implementation exists. |

---

## 8. Ambiguous Terms

Pairs of terms that are easy to conflate. Each distinction below is already established in `roadmap.md` or `altm.md` — this section exists to make each distinction explicit and quickly checkable, which is also useful interview preparation.

**Ground Truth vs. Knowledge**

| Ground Truth | Knowledge |
|---|---|
| A verified correct *answer*, tied to a specific question in the Golden Dataset. | The underlying *source corpus* (resume, JobOps data) that ground truth is derived from. |
| Used to evaluate output. | Used to produce output. Also the first ALTM lifecycle stage. |

**Faithfulness vs. Groundedness**

| Faithfulness | Groundedness |
|---|---|
| Is the claim logically entailed by the retrieved context, even if derived by combining multiple sentences? | Can the claim be traced to one specific, citable piece of evidence? |
| Can be satisfied by multi-hop reasoning across sources. | Stricter — weaker on claims that require combining sources without a single direct citation. |

**Hallucination vs. Wrong Retrieval**

| Hallucination | Wrong Retrieval |
|---|---|
| Occurs at the Infer stage — the model states something not present in the retrieved context at all. | Occurs at the Retrieve stage — the correct type of information was fetched, but from the wrong document, section, or version. |
| Retrieval cannot hallucinate; only generation can. | The evidence pulled back is real, just not the right evidence. |

**Chunk vs. Document**

| Chunk | Document |
|---|---|
| The smallest unit retrieval operates on — a slice of a document. | A full source item (one resume, one job description) before chunking. |
| Produced at the Index stage. | Consumed at the Knowledge stage. |

**Index vs. Corpus**

| Index | Corpus |
|---|---|
| The retrievable, structured lookup built *from* the corpus (chunks + vectors). | The raw set of validated source documents *before* indexing. |
| A stale index can exist even if the corpus itself is current, if re-indexing hasn't run. | A stale corpus is a Knowledge-stage failure; a stale index given a current corpus is an Index-stage failure. |

**Evaluation vs. Validation**

| Evaluation | Validation |
|---|---|
| Scoring retrieval and generation quality against the Golden Dataset (Layers 2–4). | Checking the *inputs* to the pipeline are trustworthy before anything is built on them (Layer 1 — Data Quality). |
| Assumes the corpus is already trustworthy. | Is what establishes that the corpus is trustworthy in the first place. |

**Architecture vs. ALTM**

| Architecture | ALTM |
|---|---|
| Explains how information flows through the system. | Explains where failures originate once something is running. |
| The map. | The procedure for using the map when something doesn't match reality. |

**Metric vs. Evaluation Tool**

| Metric | Evaluation Tool |
|---|---|
| A specific measurable quantity (Faithfulness, Context Recall). | The software that computes one or more metrics (DeepEval computes Faithfulness; Ragas computes Context Recall). |
| Belongs to exactly one ALTM stage. | May be scoped to exactly one evaluation layer, by design in this repository (Section 4 above). |

---

## Repository-specific vs Industry Concepts

| Concept | Scope |
|---|---|
| AI Lifecycle Traceability Model (ALTM) | Repository framework |
| Evaluation Layers | Repository organization |
| Docs Before Code | Repository convention |
| Golden Dataset | Widely used industry concept |
| Ground Truth | Widely used industry concept |
| Hybrid Retrieval | Widely used industry architecture |
| Faithfulness | Industry evaluation metric |
| Context Precision | Industry retrieval metric |

Some concepts originate from established AI engineering practice. Others are organizational conventions specific to this repository. The glossary intentionally distinguishes between these so readers understand which ideas are repository-specific and which reflect broader industry terminology.

---

## 9. Out of Scope

This glossary does not attempt to define every AI or machine learning term. It defines only terminology actually used within this repository's documentation set — `roadmap.md`, `architecture.md`, `altm.md`, and `interview-notes.md`. General AI/ML concepts not referenced by name in those documents (for example, broader transformer architecture terminology, or evaluation tools explicitly out of scope per `roadmap.md` Section 7) are not defined here. Readers should consult external references for terminology this repository does not itself use.

---

## 10. Document Stability

This glossary changes only when repository vocabulary changes — a new term is introduced into `roadmap.md`, `architecture.md`, or `altm.md`, or an existing term's meaning is deliberately revised. Architecture, ALTM, and implementation each evolve independently of this document and of each other; a new Milestone 2 component, for instance, gets its definition added here without requiring any other section of this glossary to change.

Terms should not be redefined in any other document once they have an entry here. If a document needs to introduce a genuinely new term, the term is added here first, then referenced.

---

*This document is the canonical vocabulary reference for `ai-quality-engineering`. It should be revised only when a new term enters use in `roadmap.md`, `architecture.md`, or `altm.md`, or when an existing definition is deliberately changed at the source document that governs it.*
