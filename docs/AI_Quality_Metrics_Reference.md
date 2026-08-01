# AI Quality Engineering — Metrics Reference (Full Lifecycle)

**Owner:** Karthik S R
**Document type:** Living reference, append-only — new metrics are added as they're encountered, never silently dropped or renamed. No deletions without a documented reason.
**Purpose:** A single, consolidated reference for every AI/RAG quality metric across the full information lifecycle — Knowledge → Index → Retrieval → Generation → Task — with each metric's definition, a project-specific example, an ETL/data-quality analogy, how it's evaluated, and its Primary/Secondary interview priority.

**Why this document exists:** Session 1 established the LLM Core Six (Retrieval + Generation stage only). Session 3 surfaced a real gap — none of those six can detect a Knowledge- or Index-stage failure, because all six presuppose the corpus is already correct. This document is the counterpart that closes that gap, and the single place all future metric discoveries get recorded so they don't scatter across session transcripts.

---

## Relationship to Other Governance Docs

| Document | What it owns |
|---|---|
| `Session1_LLM_Core_Six_Baseline.md` | Deep-dive derivation of Faithfulness, Groundedness, Hallucination Rate, Answer Relevancy, Context Precision, Context Recall — worked examples (Apple/Steve Jobs, AAVA POM) |
| `AI_Systems_Diagnostic_Framework_v1.md` | The ALTM pipeline stages themselves and the "time" categories (Data lifecycle / Request lifecycle / Software execution lifecycle) each layer belongs to |
| `AI_QA_Learning_Roadmap_Scope.md` §1.6.1 | Golden Dataset failure taxonomy — several metrics below exist specifically to catch categories defined there (Stale Version, Contradiction, No Answer) |
| `Engineering_Lessons_Register.md` | Architectural reasoning for *why* certain stages are kept deterministic — directly explains why Knowledge/Index metrics below must be pytest-style, never LLM-judged |
| **This document** | The metric layer itself, across all five stages — what to measure, why, and at what priority |

---

## The Five-Layer Metric Framework

```
Layer 1 — Knowledge Quality     (Knowledge Time  — Data lifecycle)
Layer 2 — Index Quality         (Index Time      — Data lifecycle)
Layer 3 — Retrieval Quality     (Query Time      — Request lifecycle)
Layer 4 — Generation Quality    (Inference Time  — subset of Query Time)
Layer 5 — Task Quality          (Query Time, post-inference)
```

**Core principle carried through every layer:** each metric answers exactly one QA question at exactly one pipeline stage — the same discipline already applied to ETL source validation, transformation validation, and load validation. No metric below is a substitute for another; each catches a failure mode the others structurally cannot.

**Hard boundary to remember:** Layers 1–2 are **pure data-quality checks** (pytest-style, deterministic, no LLM judge involved). Layers 3–5 are the only place LLM-evaluated or IR-style metrics apply. Collapsing this boundary — asking an LLM to self-assess Knowledge-stage completeness, for example — is a documented anti-pattern (`Engineering_Lessons_Register.md`, Lesson 3).

---

## Layer 1 — Knowledge Quality
*(Knowledge Time — before indexing, before anything AI-shaped exists)*

| Metric | Priority | Definition | Project Example | ETL Analogy |
|---|---|---|---|---|
| **Freshness** | Primary | Is the corpus using the latest version of the source? | Resume `v2.3` exists; corpus still indexed against `v2.2` | Yesterday's CSV loaded; today's file ignored |
| **Completeness** | Primary | Did every part of the source actually make it into the corpus? | Resume has a Projects section; corpus is missing it entirely | 10M source rows, 9.8M loaded — 200K silently dropped |
| **Provenance** | Primary | Can any downstream answer be traced back to a specific source document/version? | Resume → Chunk → Embedding → Answer — is that chain traceable? | Data lineage: source column → transformation → target column |
| **Consistency** | Secondary | Do different sources agree on the same fact? | Resume says 7.5 years experience; a JobOps-linked profile says 6 | Sales table says ₹10M revenue; Finance table says ₹12M for the same entity |
| **Duplicate Rate** | Secondary | Was the same document/fact accidentally ingested twice? | Same resume version imported twice into JobOps | Duplicate customer or invoice record |

**Evaluated by:** freshness/hash + timestamp comparison, schema/field completeness validation, cross-source diff checks — pure Python/pytest, no model call.

**Note on Consistency's priority:** kept Secondary for general interview framing, but it is *not* optional for this project specifically — it directly maps to the Golden Dataset's locked **Contradiction** category (`AI_QA_Learning_Roadmap_Scope.md` §1.6.1: "two resume versions disagree on the same fact"). Know it by name even though it's not the first thing to lead with.

---

## Layer 2 — Index Quality
*(Index Time — still Data lifecycle; this is where AI first enters, via embedding generation)*

| Metric | Priority | Definition | Project Example | ETL Analogy |
|---|---|---|---|---|
| **Chunk Coverage** | Primary | Did every piece of source content become a chunk? | 100 resume bullets in, 99 chunks out — one vanished | Every source row loaded? |
| **Chunk Integrity** | Primary | Did chunk boundaries preserve a complete semantic/business unit? | A single achievement bullet split across two chunks mid-sentence | A transformation splitting one business fact across two target columns |
| **Embedding Coverage** | Primary | Did every chunk that should have a vector actually get one? | 200 chunks in, 199 vectors out | One row skipped during a transform step |
| **Embedding Freshness** | Secondary | Were vectors regenerated after the underlying content changed? | Resume edited; old embedding reused, never re-embedded | Target table never refreshed after a source change |
| **Metadata Coverage** | Secondary | Does every chunk carry its provenance metadata (source, version, section, timestamp)? | A chunk with no record of which resume section it came from | Missing audit columns — load timestamp, batch ID, source system |

**Evaluated by:** chunk coverage / embedding coverage checks, pytest — still no LLM judge.

**Why Chunk Integrity is elevated to Primary for this project specifically:** this isn't a generic secondary nicety here — it's the literal metric that justifies the project's own locked architectural decision. Structure-aware chunking was chosen over recursive-character chunking in `Session2_RAG_Architecture_Closure.md` *specifically* because recursive-character risks tearing a fact/bullet mid-chunk. If an interviewer asks "why structure-aware chunking," Chunk Integrity is the metric that answers it — demoting it to secondary would drop your sharpest project-specific proof point.

**Why Embedding Freshness matters beyond the generic case:** this is the same failure category as the original stale-mount incident (Session 2), one layer down — and it's precisely why FAISS (Milestone 2's working default) requires the documented content-hash + last-indexed-timestamp sync design (`Session2_RAG_Architecture_Closure.md`, `AI_QA_Learning_Roadmap_Scope.md` §1.6 working defaults).

---

## Layer 3 — Retrieval Quality
*(Query Time begins — Request lifecycle, a user has now asked something)*

| Metric | Priority | Definition | Project Example | ETL Analogy |
|---|---|---|---|---|
| **Context Precision** | Primary | Of everything retrieved, how much was actually relevant? | Retrieved chunks: CrewAI experience, RCA pipeline (relevant) + a Bosch internship bullet (irrelevant) | A query with the wrong WHERE clause pulling extra rows |
| **Context Recall** | Primary | Of everything relevant that exists in the source, how much did retrieval actually find? | Resume mentions "CrewAI" twice; retrieval surfaces only one occurrence | A query silently missing rows it should have returned |

**Evaluated by:** Ragas. No substitutes at this layer — these are the canonical retrieval metrics and there is no secondary tier here.

**Boundary to hold firm:** both metrics are defined *relative to what exists in the already-validated corpus*. Neither can detect a Knowledge- or Index-stage failure — that's what Layers 1–2 exist for. See `Session3_Retrieval_Fundamentals_Closure.md`, Confusions #6 and #9 for the specific misclassifications this boundary was built to correct.

---

## Layer 4 — Generation Quality
*(Inference Time — the narrow window where the LLM is actively producing tokens, a subset of Query Time)*

| Metric | Priority | Definition | Project Example | ETL Analogy |
|---|---|---|---|---|
| **Faithfulness** | Primary | Of everything the model claimed, how much is supported/entailed by the retrieved context? | Resume never mentions Promptfoo; answer claims "expert in Promptfoo" | A transformation inventing a value not present in any source |
| **Groundedness** | Primary | Can every individual claim be traced to a specific, citable piece of evidence — stricter than "not contradicted"? | "Apple's founder passed away in 2011," derived by combining two separate sentences — faithful, but weaker on strict per-claim traceability | Source-to-target validation, claim by claim |
| **Hallucination Rate** | Primary | Of everything claimed, how much was fabricated or unsupported? | Near-complement of Faithfulness in the simple case; diverges once partial/ambiguous claims exist | No invented rows — the classic ETL correctness bar |

**Evaluated by:** DeepEval.

**Why Groundedness stays Primary here, against the more common "secondary" framing:** the Faithfulness-vs-Groundedness split — sharpest in the multi-hop Apple/Steve Jobs example (`Session1_LLM_Core_Six_Baseline.md`) — is exactly the distinction that separates "memorized six definitions" from "actually understands the six" in an interview. Dropping it to secondary removes the single strongest differentiator available at this layer.

---

## Layer 5 — Task Quality
*(Post-inference, still Query Time — the final, business-facing check)*

| Metric | Priority | Definition | Project Example | ETL Analogy |
|---|---|---|---|---|
| **Answer Relevancy** | Primary (sole metric at this layer) | Does the answer directly, completely, and only address what was actually asked — independent of whether it's true? | "Apple's founder passed away in 2011" (direct) vs. the same fact plus unrequested extra biographical detail — the second scores lower despite being equally true | A perfectly built warehouse feeding the wrong dashboard — technically correct, business still unhappy |

**Evaluated by:** DeepEval (embedding-similarity between reverse-engineered questions and the original query).

**The one property unique to this layer:** independence from truthfulness. A fully faithful, fully grounded, hallucination-free answer can still fail here if it doesn't address what was asked, or includes unrequested content. No other metric in this document has that property.

---

## Cross-Cutting: Metric-to-Time Mapping

| Layer | Time Category | Lifecycle |
|---|---|---|
| Knowledge Quality | Knowledge Time | Data lifecycle |
| Index Quality | Index Time | Data lifecycle |
| Retrieval Quality | Query Time | Request lifecycle |
| Generation Quality | Inference Time | Request lifecycle (subset of Query Time) |
| Task Quality | Query Time (post-inference) | Request lifecycle |

Per `AI_Systems_Diagnostic_Framework_v1.md` §2: Query Time ≠ Inference Time. Ragas-style metrics (Layer 3) evaluate *before* inference time starts; DeepEval-style metrics (Layer 4) evaluate the *output* of inference time. Same Query Time window, two different targets inside it.

---

## Necessary-and-Sufficient Summary (Primary Only — Interview Fast Reference)

```
Knowledge  →  Freshness, Completeness, Provenance
Index      →  Chunk Coverage, Chunk Integrity, Embedding Coverage
Retrieval  →  Context Precision, Context Recall
Generation →  Faithfulness, Groundedness, Hallucination Rate
Task       →  Answer Relevancy
```

**11 primary metrics, five stages, one metric-family boundary (Layers 1–2 deterministic data-quality vs. Layers 3–5 LLM/IR-evaluated).** This is the number to be fluent with — not 15+ definitions recited flatly, but 11 answers to 11 distinct QA questions, each tied to a stage.

---

## Interview Framing

> "In ETL I validated that source data was fresh, complete, and traceable before trusting any transformation. In AI systems I apply the same discipline one layer earlier than most people evaluate: Knowledge quality before indexing, Chunk Integrity before trusting retrieval, Context Precision and Context Recall before trusting generation, and Faithfulness and Groundedness — which I treat as distinct, not interchangeable — before trusting the final answer. The artifacts changed from rows to chunks and embeddings; the engineering discipline didn't."

---

## How This Project Uses These Metrics

| Milestone | What's implemented |
|---|---|
| **Milestone 1A** (current) | Layers 1–2 only — Knowledge and Index quality checks, pure pytest, stdlib-only. No embeddings, no LLM, so Layers 3–5 have nothing to measure yet. |
| **Milestone 2** | Layers 3–5 become measurable — Ragas wired to Context Precision/Recall, DeepEval wired to Faithfulness/Groundedness/Hallucination Rate/Answer Relevancy, once real embeddings, FAISS, and DeepSeek generation exist. |
| **Promptfoo (all milestones once generation exists)** | Not a sixth layer — a regression methodology applied *across* two full runs of any layer, re-run old vs. new prompt/corpus/code and diff. |

---

## Appendix: Future Metrics Log

*(Append new entries here as they're encountered — through articles, interviews, or project implementation. Never silently fold a new metric into an existing row above without a dated entry here first.)*

| Date Added | Metric | Layer | Priority | Source | Reason for Inclusion |
|---|---|---|---|---|---|
| — | *(none yet — this table is ready for the next addition)* | | | | |

---

## Change Log

| Date | Change |
|---|---|
| 2026-08-01 | Initial version — consolidated from Session 3 discussion (Knowledge/Index gap identification) and GPT-authored five-layer ETL-to-AI bridge, with two priority corrections applied (Chunk Integrity and Groundedness elevated to Primary against the original proposal) |
