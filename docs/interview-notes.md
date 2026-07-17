# Engineering Communication Companion

**Repository:** `ai-quality-engineering`
**Status:** Milestone 0.5 — Companion Document
**Related documents:** `docs/roadmap.md`, `docs/architecture.md`, `docs/altm.md`, `docs/glossary.md`

*(Filename kept as `interview-notes.md` for practicality; the document itself is broader than interview prep — useful for design reviews, mentoring conversations, and technical presentations as well.)*

---

## 1. Purpose

The reference documents in this repository describe the system: what it is, how it is built, and how it fails. This document is different — it explains **how to talk about that system**, and more importantly, how to reason your way to an answer you haven't rehearsed.

Interview answers built on memorization break the moment a question is phrased slightly differently than expected. Interview answers built on understanding survive rephrasing, because they're derived fresh each time from the same small set of underlying relationships. Everything in this document exists to reinforce those relationships, not to supply a script.

Reference documents remain authoritative. If this document and `altm.md` ever appear to disagree, `altm.md` is correct — this document only explains how to talk about what's there.

---

## 2. How to Use This Document

1. Learn the concepts from the reference documents (`roadmap.md`, `architecture.md`, `altm.md`, `glossary.md`).
2. Come here to see how those concepts connect to each other.
3. Practice explaining the connections out loud, in your own words, not the document's words.
4. In an actual conversation, derive the answer from the relationship — don't recall a stored answer.

This document complements the glossary; it does not replace it. The glossary tells you what a term means. This document tells you why it exists and how it relates to the terms around it.

---

## Engineering Thinking Modes

Strong engineering explanations move through progressively richer levels of understanding:

```text
Facts
   │
   ▼
Concepts
   │
   ▼
Systems
   │
   ▼
Engineering Decisions
```

**Facts**
- Individual pieces of information.
- Answer "What?"

**Concepts**
- Explain why facts matter.
- Answer "Why?"

**Systems**
- Connect multiple concepts together.
- Answer "How does this interact with everything else?"

**Engineering Decisions**
- Explain why one design was chosen instead of another.
- Answer "Why this approach?"

Interviews rarely evaluate isolated facts — they evaluate the ability to move naturally through these four levels of understanding.

---

## Answer Construction Pattern

Unfamiliar interview questions can be answered consistently by following the same reasoning process:

```text
Question
    │
    ▼
Identify Principle
    │
    ▼
Identify System Layer
    │
    ▼
Explain Relationships
    │
    ▼
Give Repository Example
    │
    ▼
Discuss Trade-offs
    │
    ▼
Conclusion
```

Start from the question itself. Identify the underlying engineering principle it's really testing. Place that principle within a system layer (Section 3 below). Explain how that layer relates to the ones around it. Ground the explanation in a concrete repository example rather than a generic one. Discuss the trade-offs the repository accepted in reaching its design. Close with a conclusion that ties the reasoning back to the original question.

The engineer is deriving an answer rather than recalling a memorized response. This reasoning pattern is equally useful for interviews, design reviews, debugging sessions, and architecture discussions.

---

## 3. Engineering Mental Models

A useful way to place AI Quality Engineering in context is as a sequence of layers, each one adding a new kind of failure mode on top of the layer beneath it — not replacing it.

```
Software Engineering
        │
        ▼
Data Engineering
        │
        ▼
Machine Learning
        │
        ▼
LLMs
        │
        ▼
RAG
        │
        ▼
Agentic AI   ← resume experience (HP AAVA), one layer beyond what this repository builds
```

**Software Engineering.** Correctness is about logic — did the code do what it was supposed to do. QA traces execution, layer by layer (Requirement → Design → Implementation → Database → API → UI → Testing).

**Data Engineering.** Adds a new failure mode: the logic can be perfect and the *data* can still be wrong — stale, incomplete, duplicated, mismatched. This is the world of ETL testing, and it's the layer this project's seven years of prior experience sits in most heavily.

**Machine Learning.** Adds statistical uncertainty. A model isn't "right" or "wrong" the way a function is — it's evaluated with precision, recall, and trade-offs between them, because there's no single correct output to diff against.

**LLMs.** Adds language-level uncertainty on top of statistical uncertainty. Output isn't just "closer or further from a number" — it can be fluent and confident while being entirely fabricated. This is where Faithfulness, Groundedness, and Hallucination Rate become necessary; classical accuracy stops being sufficient.

**RAG.** Adds an information-retrieval stage in front of generation, splitting the failure surface in two: was the right evidence found (retrieval), and was the eventual answer actually supported by that evidence (generation). This split — retrieval vs. generation — is the single most load-bearing idea in `altm.md`.

**Agentic AI.** Adds multi-step execution, tool use, and autonomous decision-making on top of RAG. This is where the HP AAVA five-agent RCA pipeline sits, and it's genuine resume experience — but it is explicitly **one layer beyond what this repository builds**. `roadmap.md` and `architecture.md` both scope agent orchestration out entirely. Being able to say *why* that's a deliberate scope decision, not a gap, is a stronger answer than pretending the repository does something it doesn't.

**What stays the same across every layer:** the QA instinct of "don't trust the output until you've verified the input, and don't trust the whole system until you've isolated which stage is responsible." That instinct is the actual throughline of the resume narrative — from Maruti Suzuki ETL validation to HP AAVA agent validation to this repository's evaluation suite. It's the same discipline applied one layer deeper each time, not a different skill being learned from scratch.

---

## 4. First-Principles Explanations

Short derivations, each starting from something simpler.

**What is AI Quality Engineering?**
Take QA's core question — "how do we know this system is correct?" — and apply it to a system where correctness can't be checked by comparing output to a single expected value, because the same input can validly produce different phrasings of a correct answer. AI Quality Engineering is the set of techniques for answering that question anyway: verified ground truth, layered evaluation, and regression detection substituting for the exact-match testing that classical software allows.

**Why is RAG needed?**
An LLM alone only knows what was in its training data, frozen at a point in time. A resume, a job posting, or a company's internal data will never be in that training data. RAG retrieves the actual current source material at query time and hands it to the model, so the model can answer using real, current facts instead of guessing from training-data memory.

**Why embeddings exist.**
Keyword search only matches literal words. "Team leadership" and "managed a group of engineers" mean nearly the same thing but share almost no words. Embeddings convert text into vectors positioned by meaning, so semantically similar text ends up numerically close — enabling retrieval by meaning, not just by exact term.

**Why vector search exists.**
Once text is embedded as vectors, finding "similar meaning" becomes a geometry problem — finding the nearest vectors to a query vector. Vector search is the mechanism for doing that lookup efficiently over a large corpus.

**Why chunking exists.**
A whole document is usually too large and too topically mixed to embed as one meaningful unit, and too large to usefully retrieve as a single block. Chunking splits a document into smaller, semantically coherent pieces so retrieval can return just the relevant part, not the entire source.

**Why retrieval is evaluated separately from generation.**
They fail independently. A system can retrieve perfectly and still generate a hallucinated answer from good evidence; a system can retrieve garbage and still generate a fluent, faithful-sounding answer to the wrong material. Evaluating them together hides which one actually broke.

**Why deterministic pipelines come before LLMs.**
An LLM's non-determinism makes it hard to tell whether a bug is in your pipeline plumbing or in the model's own variability. Building the pipeline with deterministic stubs first proves the plumbing is correct in isolation, so once a real model is introduced in Milestone 2, any new failure can be attributed to the model, not to code that was already broken.

**Why evaluation precedes implementation.**
Designing the evaluation strategy after the system is built tends to produce evaluation that matches whatever the system happens to do, rather than what it's actually supposed to do. Designing it first keeps the target fixed and independent of the implementation.

**Why regression testing matters for AI.**
A prompt tweak, a corpus update, or a model swap can silently make previously-correct answers wrong, with no error thrown anywhere — the system still runs, it's just quietly worse. Regression testing (Promptfoo, Layer 4) is what catches degradation that would otherwise ship undetected.

---

## 5. System Thinking

Two ways the repository's core pipeline connects end to end.

**The evaluation chain:**
```
Golden Dataset → Retrieval → Prompt → Generation → Evaluation → Regression
```
Each arrow is a dependency, not just a sequence — retrieval quality can only be judged against a trustworthy Golden Dataset; generation quality can only be judged against what was actually retrieved; regression can only be judged against a stable evaluation baseline. Break the Golden Dataset and every downstream link becomes meaningless, even if it technically still runs.

**The information lifecycle (ALTM):**
```
Knowledge → Index → Retrieve → Assemble → Infer → Post-Process → Evaluate → Final Answer
```
Same principle, finer resolution — see `altm.md` for the full stage-by-stage failure model. The relationship worth internalizing: each arrow is a place where correct input can become incorrect output, and each stage's evaluation method only checks *its own* transformation, never the ones before it. A metric passing at one stage is never evidence that an earlier stage was fine.

---

## 6. Engineering Reasoning Patterns

Not Q&A pairs — reasoning paths. The value is in the *shape* of the reasoning, which transfers to differently-phrased questions.

**"How would you debug hallucinations?"**
Hallucination is a symptom, not a diagnosis — start there. Use the ALTM upstream-first workflow rather than jumping straight to "the model is hallucinating." First rule out whether retrieval actually succeeded — check the assembled prompt for whether the claim was even present in retrieved evidence. If it was present, the failure is at Infer (a real Faithfulness problem). If it wasn't present, the model didn't hallucinate in isolation — retrieval failed to supply the fact, and the model filled the gap from training-data memory. The corrective action differs completely depending on which of those two it is, which is why jumping straight to "tune the prompt" without checking retrieval first is the common mistake.

**"How do you know your AI system is production-ready?"**
Production-ready isn't a single yes/no property — decompose it into the four evaluation layers. Is the data trustworthy (Layer 1)? Is retrieval finding the right evidence (Layer 2)? Is generation faithful to that evidence (Layer 3)? Does a change stay stable over time without silent regressions (Layer 4)? A system can be strong on three layers and still not be production-ready because the fourth was never checked — which is exactly why this repository treats all four as required, not optional extras.

**"What's the difference between testing traditional software and testing an AI system?"**
Traditional software testing compares actual output to one expected output — a diff either passes or fails. AI systems often don't have one correct output; multiple phrasings can all be correct. The shift is from exact-match testing to entailment and traceability checking — does the output logically follow from and cite verifiable evidence, rather than does it match a fixed string.

**"Walk me through how you'd design an evaluation dataset for a new AI feature."**
Start from ground truth, not from tooling. Identify a source of already-verified facts (in this repository's case, the resume). Derive multiple question phrasings per fact so the dataset covers lexical, semantic, and reasoning variation without inventing new knowledge. Then deliberately add failure-oriented categories — no-answer, stale-version, contradiction, false-premise — because a dataset of only easy questions passes everything and reveals nothing. Only after that foundation exists does tool selection (DeepEval, Ragas, Promptfoo) even become a relevant question.

---

## 7. Connecting Concepts

Short concept chains worth being able to trace forward and backward, not just recite in order.

```
Faithfulness → Groundedness → Evidence → ALTM
```
Faithfulness asks if a claim follows from context. Groundedness asks the stricter question of whether it traces to one specific citable piece of evidence. Evidence is the concrete artifact (a chunk, a hash check) that either claim is checked against. ALTM is the framework that organizes which stage produces that evidence and which check consumes it.

```
Context Recall → Retrieval → Chunking → Embeddings
```
Context Recall measures whether relevant material was found. What can be found depends on what retrieval can search over. What retrieval can search over depends on how the corpus was chunked. How well a chunk can be matched to a query depends on the embedding representing it. A weak link anywhere in this chain shows up as a Context Recall problem, even though the actual cause might be several steps upstream (a bad chunk boundary, not a bad retrieval algorithm).

```
Architecture → Interfaces → Testing → Regression
```
Architecture defines what components exist. Interfaces define how those components are called, independent of their implementation. Testing validates a component against its interface contract. Regression validates that testing outcome stays stable as the implementation behind the interface changes — the whole chain is what makes it possible to swap a stub `Generator` for a real DeepSeek integration in Milestone 2 without rewriting the rest of the pipeline.

---

## 8. Explaining Repository Decisions

Short rationale for decisions already locked elsewhere — useful for defending engineering choices in conversation, not for re-litigating them.

**Why three evaluation tools, not more.** Each of DeepEval, Promptfoo, and Ragas maps to exactly one evaluation layer with no overlap. Adding a fourth tool without a fourth distinct responsibility would be tool collection, not better coverage — the goal stated in `roadmap.md` is depth on a small surface area.

**Why interface-first.** It decouples "is the pipeline logic correct" from "is the specific model or vector store correct" — two very different kinds of correctness that would otherwise be debugged simultaneously and confusingly.

**Why docs before code.** Architecture debates are expensive to have in the middle of implementation, because half-built code creates pressure to rationalize whatever was already built rather than choose the best design. Freezing decisions first removes that pressure.

**Why a deterministic Milestone 1A.** Proving the pipeline's plumbing is correct without any model-level non-determinism in play means any bug found later, once real embeddings and generation are introduced, can be confidently attributed to the new component rather than to pre-existing code.

**Why the Golden Dataset comes first.** Every metric this project will ever report is only as meaningful as the ground truth it's compared against. Building retrieval or generation before the dataset exists means there is nothing trustworthy yet to measure either of them against.

**Why ALTM exists.** "The AI is wrong" is not an actionable diagnosis. ALTM exists to convert that into "which of eight specific stages produced the wrong output," which is actionable — the same move classical QA already makes when it asks "which layer failed" instead of "why doesn't the app work."

**Why the glossary exists.** A project built across multiple sessions and multiple documents is at real risk of the same concept being described slightly differently in each one. A single authoritative definition per term, referenced rather than restated, prevents that drift.

### Why This Repository Exists

This repository was created to demonstrate disciplined AI Quality Engineering, not simply to showcase AI tooling. It demonstrates the ability to engineer AI systems, evaluate AI systems, diagnose failures systematically, and communicate engineering decisions clearly. These capabilities build directly upon classical QA and Data Engineering practices rather than replacing them.

---

## 9. Common Misconceptions

Each of these is a genuine distinction already established in the reference documents — not a new claim introduced here.

**RAG is not an LLM.** RAG is a pipeline architecture — retrieval plus generation. The LLM is one component inside it (the Generator). A system can have excellent RAG architecture around a mediocre model, or vice versa; they fail independently.

**Groundedness is not Faithfulness.** Faithfulness allows a claim built by combining multiple context sentences (multi-hop reasoning). Groundedness is stricter — it wants a single, direct, citable source per claim. The two usually agree, but the cases where they diverge are the interview-relevant ones.

**Promptfoo is not "an evaluator" in the same sense as DeepEval or Ragas.** DeepEval and Ragas compute quality scores for a single run. Promptfoo's role is comparison across two runs — old vs. new — to catch regressions. Describing all three as interchangeable "evaluation tools" erases that Promptfoo answers a different question (did something get worse) than the other two (is this good).

**ALTM is not an industry standard.** It is this repository's own internal reasoning framework, built from direct diagnostic work on this project's pipeline. Presenting it as an established framework rather than a personal mental model misrepresents both its origin and its authority — see `altm.md` Section 11 for the full framing guidance.

**Architecture is not diagnostics.** Architecture describes how the system is built, independent of whether anything is currently broken. ALTM describes how to find what's broken. Knowing the architecture well doesn't automatically make someone good at using it to debug — that's a separate, practiced skill.

---

## Communication Depth

The same engineering concept should be explainable at different levels of detail depending on the audience:

| Depth | Typical Audience | Goal |
|---|---|---|
| 30-second explanation | Recruiter / HR screening | Demonstrate conceptual understanding without excessive detail. |
| 2-minute explanation | Hiring manager / Senior engineer | Explain reasoning, architecture, and trade-offs. |
| 10-minute discussion | Architect / Principal engineer | Explore assumptions, alternatives, diagnostics, metrics, and implementation decisions. |

The underlying reasoning should remain the same — the amount of detail changes, not the engineering principles.

---

## 10. Interview Mindset

- **Think like an engineer, not like a candidate reciting facts.** The strongest signal is being able to derive an answer live, including visibly working through which stage or layer is responsible, not producing a polished paragraph instantly.
- **Reason from evidence, not assumption.** The same discipline `altm.md` insists on for the system — evidence before intuition — applies to how you talk about the system too. If asked something you'd need to check rather than recall, say so.
- **Explain trade-offs, don't just state conclusions.** "We chose hybrid retrieval" is weaker than "we chose hybrid retrieval because JobOps already has structured data, and ignoring it for vector-only search would have been a weaker evaluation setup" — the second version shows the decision process, not just the outcome.
- **Use concrete examples from this repository** rather than generic textbook ones — the AAVA RCA worked example in `altm.md` is stronger than an invented scenario because it's real and specific.
- **Admit uncertainty precisely.** "I haven't benchmarked embedding models yet — that's explicitly Milestone 2 scope" is a stronger answer than guessing, and it demonstrates the same scope discipline the repository itself practices.
- **Prefer principles over named frameworks.** Being able to explain *why* retrieval and generation are evaluated separately is worth more than being able to name that ALTM says so — the principle should be able to stand on its own, independent of the label.

---

## 11. Repository Cross-Reference Map

| Need | Go to |
|---|---|
| System design, components, interfaces | `docs/architecture.md` |
| Terminology, precise definitions | `docs/glossary.md` |
| Failure diagnosis, root cause tracing | `docs/altm.md` |
| Implementation order, milestone scope | `docs/roadmap.md` |
| How a decision was reached, session history | `docs/learning-log.md` |
| How to talk about any of the above | This document |

---

## 12. Document Stability

This document evolves as communication and explanation improve — a clearer way to phrase a first-principles derivation, or a new conversation pattern worth capturing, can be added here without touching any other document. It does not redefine engineering concepts, introduce new terminology, or make new architectural claims; the reference documents remain authoritative for all of that. If a change here would require a corresponding change in `roadmap.md`, `architecture.md`, `altm.md`, or `glossary.md`, it belongs in one of those documents instead, not here.

---

*This document is the repository's engineering communication companion — a guide to explaining `ai-quality-engineering` naturally, not a script to recite. It should be revised when a new conversation pattern or connection is worth capturing, not when the underlying system changes; system changes belong in the reference documents.*
