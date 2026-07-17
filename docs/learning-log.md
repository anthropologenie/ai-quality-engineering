# Engineering Evolution Log

**Repository:** `ai-quality-engineering`
**Status:** Living document — never frozen
**Related documents:** `docs/roadmap.md`, `docs/architecture.md`, `docs/altm.md`, `docs/glossary.md`, `docs/interview-notes.md`

---

## 1. Purpose

The other five documents in this repository describe the system as it currently exists — what is being built, how it is designed, how it is diagnosed, what its terms mean, and how to talk about it. Every one of those documents is frozen at Milestone 0.5: correct today, and changed only through a deliberate revision, not casually.

This document is different. It records **how the understanding behind those documents came to be** — which beliefs turned out to be incomplete, what observation exposed the gap, what was understood instead, and what changed in the repository as a result. It is not a diary, a changelog, or a session transcript. It records conceptual evolution, not chronology.

---

## 2. Relationship to the Documentation Set

```
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
interview-notes.md
    │
    ▼
learning-log.md
```

The first five documents describe the repository as it stands. This document describes the evolution that produced them. A future contributor could, in principle, understand the repository entirely from the first five documents alone — this one exists to explain *why* those five ended up saying what they say, for anyone who wants the reasoning behind the conclusions rather than just the conclusions.

---

## 3. Learning Principles

Recurring principles that shaped the repository, evident across every phase in Section 4:

- **Understanding over memorization.** A definition that can be recited but not derived doesn't survive a differently-phrased question. Every concept in this repository was pushed until it could be re-derived from a simpler one, not just repeated.
- **First principles over framework collection.** Naming a tool or a framework is not the same as understanding the problem it solves. Each tool adopted in this repository (DeepEval, Ragas, Promptfoo) was mapped to a specific stage failure before being trusted as "the" solution for that stage.
- **Evidence before conclusions.** A claim about why something failed is only as good as the specific check that confirms it. This is the same principle later formalized as an ALTM design principle, but it governed the documentation process itself before ALTM existed.
- **Evaluation before implementation.** The evaluation strategy for a component was designed before the component was built, not fitted to it afterward.
- **Documentation before code.** Architectural and scope decisions were written and frozen before any pipeline code exists — Milestone 0.5 exists specifically to complete this before Milestone 1A begins.
- **Interfaces before integrations.** Component contracts were defined before any real embedding model, vector store, or LLM was chosen.
- **Diagnose before optimize.** A failure is localized to a specific stage before any fix is attempted — fixing the stage where a symptom is merely observed, rather than where the check first fails, was identified early as the most common source of misdiagnosis.

---

## 4. Evolution Timeline

Phases are anchored to repository milestones, not calendar sessions, so this document continues to make sense as the project ages. All conceptual work to date occurred within **Milestone 0** (scaffold) and **Milestone 0.5** (documentation synchronization) — no implementation phase has started yet, so Milestone 1A has no entries below. It will be populated as real diagnostic and implementation work happens there.

### Milestone 0 — Foundation

#### Phase 0 — Learning AI Quality Engineering

**Initial Understanding:** Evaluating an AI system meant applying the same accuracy-style thinking already familiar from classical QA and ETL testing — run it, check if the output matches expectation, report a pass rate.

**Observation:** A real production example (the AAVA workflow generating an inconsistent count of Page Object Models — sometimes 14, sometimes 13 — from the same input) didn't fit that model. A simple accuracy number ("80/100 runs matched the expected count") could be computed, but it hid *why* the system was unreliable, and it didn't map cleanly onto a generation task where "correctly did not generate something" isn't a meaningful category.

**Revised Understanding:** Generation tasks need metrics built for entailment and traceability (Faithfulness, Groundedness, Hallucination Rate), not the confusion-matrix math (accuracy, precision, recall) that classical ML and classical QA both rely on. The 14-vs-13 inconsistency was reframed as a repeatability/determinism problem first, with recall only meaningfully describing a specific low-count run — not the inconsistency itself.

**Repository Impact:** Established the Core Six metrics as the foundation of `roadmap.md` Section 1.3, and set the precedent — followed throughout the rest of the documentation set — of anchoring every abstract metric to a concrete, real pipeline example rather than a textbook one.

#### Phase 1 — Understanding RAG

**Initial Understanding:** RAG was, roughly, "the model looks things up before answering" — a single added step in front of generation.

**Observation:** A real incident — two chats producing contradictory answers because one had a stale mounted copy of a roadmap file — couldn't be explained by "the model looked something up." The model was faithful and grounded to what it actually received; the failure was somewhere upstream of retrieval entirely.

**Revised Understanding:** RAG is a multi-stage pipeline, not a single lookup step, and evaluation has to begin before the LLM is even in the picture — at Knowledge and Index, well before Retrieval.

**Repository Impact:** Directly produced the corrected pipeline model now locked in `architecture.md` (Knowledge → Index → Retrieve → Assemble → Infer → Evaluate) and the explicit distinction, now in `altm.md`, that a stale corpus is a Knowledge-stage failure, not a Retrieval-stage one.

#### Phase 2 — Separating Retrieval from Generation

**Initial Understanding:** "Precision" and "recall" were assumed to apply the same way regardless of which stage of the pipeline was being discussed.

**Observation:** Attempting to define Context Precision took three attempts. The first attempt redescribed Faithfulness ("did the agent add anything extra that doesn't exist"). The second attempt used the word "hallucination" to describe a retrieval failure — which turned out to be a category error, since retrieval can only pull in real-but-irrelevant material; it cannot fabricate anything. Only generation can hallucinate.

**Revised Understanding:** Retrieval-stage and generation-stage failures are structurally different, not just differently named. Precision and recall are generic confusion-matrix formulas that get *scoped* to a stage — "Context Precision" is precision scoped to retrieval; "Faithfulness" is the equivalent concept scoped to generation, deliberately given a different name specifically to prevent this confusion from recurring.

**Repository Impact:** Became the single most load-bearing distinction in the entire documentation set — repeated explicitly in `altm.md` Section 6 as "the retrieval-vs-generation split," and used as the organizing principle for the four-layer evaluation strategy in `roadmap.md` Section 5.

### Milestone 0.5 — Documentation Architecture

#### Phase 3 — Evaluation Layers

**Initial Understanding:** Three tools (DeepEval, Promptfoo, Ragas) were understood as three roughly interchangeable ways to "evaluate the AI."

**Observation:** Treating them as interchangeable made it unclear which tool to reach for when a specific failure was observed, and blurred the fact that Promptfoo doesn't score a single run the way the other two do — it compares two runs.

**Revised Understanding:** Each tool maps to exactly one distinct responsibility, corresponding to a specific band of pipeline stages: Data Quality (pytest), Retrieval Quality (Ragas), Generation Quality (DeepEval), and Regression (Promptfoo, a comparison methodology rather than a single-run metric).

**Repository Impact:** Became the four-layer Evaluation Strategy in `roadmap.md` Section 5, and directly informed the decision to keep tool scope frozen at exactly three tools — adding a fourth without a fourth distinct responsibility would be collecting frameworks, not improving coverage.

#### Phase 4 — Diagnostic Thinking (ALTM)

**Initial Understanding:** Diagnosing a wrong AI output meant reading the prompt and reasoning about what the model might have done wrong.

**Observation:** This approach didn't scale to a real, multi-stage RCA pipeline failure (the HP AAVA `Root Cause = Database Failure` worked example) — there were too many plausible explanations and no systematic way to rule most of them out before guessing.

**Revised Understanding:** The same "which layer failed" discipline already applied in classical QA stacks (Requirement → Design → Implementation → Database → API → UI → Testing) could be applied to AI systems by tracing information through the pipeline stage by stage, ruling out earlier stages before suspecting later ones — because earlier-stage failures propagate downstream and make every later stage look broken even when only one stage is actually at fault.

**Repository Impact:** Became the AI Lifecycle Traceability Model, documented in full in `altm.md` — including the explicit, deliberate framing of ALTM as an internal reasoning framework for this repository, not an industry-standard model, to avoid overclaiming its authority.

#### Phase 5 — Repository Documentation Architecture

**Initial Understanding:** Architectural decisions, failure-diagnosis reasoning, terminology, and interview narrative could reasonably live together in a smaller number of documents, or in working notes outside the repository entirely.

**Observation:** Reviewing the accumulated working notes revealed the same concepts described slightly differently in different places, and revealed that the actual locked architecture existed only in conversation history — not in Git — which meant the repository could not be understood on its own.

**Revised Understanding:** Each concern needed a document with a single, non-overlapping responsibility — execution planning, system design, failure diagnosis, terminology, and communication are five genuinely different questions, and collapsing them back together would reintroduce the same drift risk that motivated separating them.

**Repository Impact:** Produced the current Milestone 0.5 documentation set itself: `roadmap.md`, `architecture.md`, `altm.md`, `glossary.md`, `interview-notes.md`, and this document — each scoped to exactly one of those five concerns, cross-referencing rather than duplicating.

### Milestone 1A — Deterministic RAG Pipeline

*Not yet populated. This phase begins once real implementation work — the structure-aware chunker, SQL-filter retriever stage, deterministic stub generator, CLI, and data-quality pytest suite — surfaces conceptual shifts worth recording, rather than routine coding work, which does not belong in this log (see Section 10).*

---

## 5. Major Engineering Decisions

Reasoning behind decisions already locked elsewhere — the "why," not a restatement of the "what."

**Why deterministic Milestone 1A.** Model non-determinism and pipeline bugs look identical from the outside — both produce inconsistent output. Proving the pipeline is correct with deterministic stubs first means any inconsistency observed after Milestone 2 introduces a real model can be attributed to the model, not to code that was already unreliable.

**Why interface-first architecture.** The cost of choosing an embedding model or vector store too early is that the choice becomes entangled with pipeline logic, making it expensive to revisit either independently later. Defining `EmbeddingProvider` and `VectorStore` as interfaces before any implementation exists keeps those two kinds of correctness — "is the pipeline right" and "is this specific model right" — separable.

**Why evaluation-first.** Designing an evaluation strategy after a system is built tends to produce evaluation shaped by what the system happens to do. Designing it first, against the Golden Dataset's failure taxonomy, keeps the target independent of the implementation being judged.

**Why Golden Dataset first.** Every metric this project will report is only as trustworthy as the ground truth it's measured against. There is no meaningful way to evaluate retrieval or generation quality against a target that hasn't itself been verified — this is the same TDM (Test Data Management) discipline already applied on the Maruti Suzuki and Betts Group engagements, applied one layer earlier in the pipeline.

**Why three evaluation tools.** Once each tool was mapped to a distinct pipeline responsibility (Phase 3), a fourth tool would only make sense if it covered a genuinely distinct fifth responsibility — none of the commonly-suggested alternatives (LangSmith, MLflow, Phoenix) did, so they were scoped out rather than added for name recognition.

**Why documentation before implementation.** The stale-mounted-file incident (Phase 1) demonstrated concretely what happens when architecture exists only in working memory or chat history rather than in the repository — the repository becomes unable to explain itself, and different conversations can reach contradictory conclusions about the same system.

**Why ALTM exists.** "The AI is wrong" is not an actionable starting point for debugging. ALTM exists to convert a vague symptom into a specific, checkable claim about one of eight pipeline stages.

**Why the glossary exists.** A project developed across many separate working sessions and multiple documents is at genuine risk of the same term drifting to mean slightly different things in different places. A single authoritative definition per term, referenced everywhere else, was adopted specifically to prevent that.

---

## 6. Concept Evolution

```
QA
    │
    ▼
ETL QA
    │
    ▼
AI Quality Engineering
    │
    ▼
Production AI Quality
```
Each step adds a new failure surface without discarding the discipline of the step before it. QA established "verify before trusting." ETL QA added "the data itself, not just the logic, can be wrong." AI Quality Engineering added "the output can be fluent and confident while being unsupported by anything real." Production AI Quality (Milestone 2–3 territory) will add "correct today does not mean correct after the next change" — the regression concern this repository has already designed for but not yet implemented.

```
LLM
    │
    ▼
RAG
    │
    ▼
Evaluation
    │
    ▼
Traceability
    │
    ▼
ALTM
```
Understanding began at the LLM as a single opaque unit. RAG decomposed that into retrieval plus generation. Evaluation then had to decompose further — a single "is this good" score wasn't enough once retrieval and generation were understood to fail independently. Traceability was the recognition that evaluation needed to be *locatable* to a specific stage, not just measured in aggregate. ALTM is the concrete framework that resulted from formalizing that need.

---

## 7. Mistakes That Improved Understanding

Each entry below was a genuine, if temporary, misunderstanding — recorded because the correction was more instructive than getting it right the first time would have been.

**Thought RAG was semantic search.** → Learned RAG is a full multi-stage pipeline (Knowledge through Final Answer), of which semantic search is only one component of one stage (Retrieve). Believing otherwise would have meant evaluating the whole system with a retrieval-only mental model — missing Knowledge-stage staleness and Infer-stage hallucination entirely.

**Thought embeddings generate answers.** → Learned embeddings only enable retrieval — converting text to vectors so semantically similar content can be found. Generation is a separate step performed by the model on the retrieved content, not something embeddings do themselves.

**Thought Promptfoo evaluates quality the way DeepEval and Ragas do.** → Learned Promptfoo's actual role is detecting regressions — comparing old vs. new runs, not scoring a single run in isolation. Treating all three tools as interchangeable "quality checkers" would have left regression detection unaccounted for as a distinct responsibility.

**Thought ALTM described architecture.** → Learned ALTM describes diagnostics — where a failure originated, not how the system is built in the first place. The two are complementary but answer different questions, which is why they ended up as two separate documents (`architecture.md` and `altm.md`) rather than one.

Each of these misconceptions was useful precisely because correcting it produced a distinction that the corrected version alone would not have made as sharply — the wrong belief made the eventual right one memorable, not just correct.

---

## 8. Communication Evolution

```
Definitions
    │
    ▼
Concepts
    │
    ▼
Relationships
    │
    ▼
Systems
    │
    ▼
Engineering Decisions
```

Communication about this project started at the level of definitions — being able to state what Faithfulness or Context Precision means. It progressed to concepts — being able to explain *why* each metric exists, not just what it measures. From there to relationships — being able to explain how Faithfulness and Groundedness diverge, or how Context Recall depends on chunking quality several steps upstream. From there to systems — being able to reason about the whole pipeline, not just an isolated metric. And finally to engineering decisions — being able to justify *why* the repository is built the way it is, trade-offs included, not just describe what it does.

The goal shifted, over that progression, from memorizing answers to being able to explain reasoning live — which is exactly the operating principle `docs/interview-notes.md` is built around. That document is the practical application of this progression; this section records that the progression itself is what changed, not just the content being communicated.

---

## 9. Knowledge Crystallization

A recurring reflection pattern, reused whenever a significant insight changed the repository. New entries should follow the same five-step structure.

```
Initial Belief
    │
    ▼
Observation
    │
    ▼
New Understanding
    │
    ▼
Repository Change
    │
    ▼
Enduring Principle
```

**Example 1**
- *Initial Belief:* Accuracy is a sufficient metric for judging whether an AI system is working correctly.
- *Observation:* The AAVA 14-vs-13 POM generation inconsistency couldn't be explained by an accuracy number alone.
- *New Understanding:* Generation tasks need entailment-based metrics (Faithfulness, Groundedness), because "true negative" is often undefined for generation.
- *Repository Change:* Core Six metrics established as the baseline of `roadmap.md` Section 1.3.
- *Enduring Principle:* Accuracy alone hides *why* a system is unreliable; the failure mode matters as much as the failure rate.

**Example 2**
- *Initial Belief:* A model that is faithful to its retrieved context can be trusted.
- *Observation:* A model can be 100% faithful to a stale or wrong document.
- *New Understanding:* Faithfulness checks consistency with what was retrieved, never whether that retrieved content was itself current or correct.
- *Repository Change:* This distinction is now stated explicitly in both `architecture.md` and `altm.md`, at the Infer-stage and Knowledge-stage entries respectively.
- *Enduring Principle:* Passing one metric never guarantees correctness at an adjacent, independently-checked stage.

**Example 3**
- *Initial Belief:* Documentation could be written after the architecture stabilized through implementation.
- *Observation:* Architecture existed only in working conversation, and different conversations produced contradictory conclusions about the same locked decisions.
- *New Understanding:* Documentation is not a record of a stable system — it is what makes the system stable enough to be built on at all.
- *Repository Change:* Milestone 0.5 was introduced as a required phase before Milestone 1A implementation resumes.
- *Enduring Principle:* Docs before code is not a stylistic preference; it is what prevents an architecture debate from recurring mid-implementation.

---

## Engineering Maturity

The repository reflects a progression in engineering capability rather than simply an accumulation of knowledge:

```text
Understanding
      │
      ▼
Application
      │
      ▼
Evaluation
      │
      ▼
Diagnosis
      │
      ▼
Communication
      │
      ▼
Architecture
      │
      ▼
Engineering Judgment
```

**Understanding**
- Learning individual concepts.

**Application**
- Applying concepts to real engineering problems.

**Evaluation**
- Measuring correctness using evidence.

**Diagnosis**
- Localizing failures rather than observing symptoms.

**Communication**
- Explaining engineering reasoning clearly.

**Architecture**
- Designing systems intentionally rather than incrementally.

**Engineering Judgment**
- Making trade-offs based on evidence, constraints, and long-term maintainability.

Engineering maturity in this repository is characterized by moving from learning isolated tools toward making disciplined engineering decisions grounded in first principles.

---

## Enduring Patterns

Although individual lessons evolve, several recurring patterns emerged throughout the repository:

```text
Component Thinking
        │
        ▼
System Thinking

Metric Thinking
        │
        ▼
Lifecycle Thinking

Tool Thinking
        │
        ▼
Engineering Thinking
```

- Many misunderstandings originated from treating an entire pipeline as though it were a single component.
- Metrics became meaningful only after being tied to a specific lifecycle stage.
- Tools became useful only after understanding the engineering problem they solved.
- Separating responsibilities consistently produced clearer architecture, diagnostics, documentation, and evaluation.

Engineering maturity repeatedly emerged through **separation of concerns**, rather than by increasing complexity.

---

## 10. Future Evolution

Future milestones should continue extending this document — but selectively. Only entries that represent a genuine shift in engineering *understanding* belong here: a belief that turned out to be incomplete, an observation that exposed the gap, and a resulting change to how the repository is built or reasoned about.

Routine implementation work — writing a chunker, fixing a bug, adding a test case — does not belong here unless it produced a conceptual shift the way the stale-mounted-file incident or the Context Precision confusion did. The reference documents (`roadmap.md`, `architecture.md`, `altm.md`, `glossary.md`, `interview-notes.md`) should only change when an actual engineering decision changes, not when this log grows — the two update independently of each other.

---

## 11. Document Stability

Unlike every other document in this repository, this document is intentionally **never frozen**. It is the repository's living engineering memory — expected to grow for as long as the repository is actively developed.

The reference documents remain the stable, authoritative description of the system at any given point in time. This document is the record of how that description came to be correct, and it will keep growing as understanding keeps evolving — including, eventually, entries from Milestone 1A onward that don't exist yet.

---

*This document is the repository's Engineering Evolution Log. Add to it whenever engineering understanding meaningfully changes; leave it alone otherwise. It should be readable, six months from now, by a contributor who wants to know not just what this repository does, but why it ended up doing it that way.*
