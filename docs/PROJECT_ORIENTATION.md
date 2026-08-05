# PROJECT_ORIENTATION.md

**Purpose of this document:** a fast, faithful entry point. Read this first in any new conversation about `ai-quality-engineering` — it should make the repository approachable without requiring the reader to have lived through every sprint.

---

## 1. What this project actually is

`ai-quality-engineering` is Karthik S R's (GitHub: anthropologenie) portfolio project demonstrating **AI Quality Engineering methodology** — not a production RAG product. The explicit, repeatedly-stated purpose: *"assist me to explain why a particular metric has this reading for AI evaluation — not to build a perfect RAG."*

It is one of two parallel professional tracks:
1. **Near-term:** job search targeting AI Quality Engineer / AI Evaluation Engineer / AI Test Automation Engineer / AI Governance roles, remote-first, Bengaluru, ₹20–30+ LPA floor.
2. **Long-term:** Krapheno, a separate governance-as-code venture — deliberately kept narratively separate from this repo for interview-optics reasons, though the two share a learning flywheel.

This repository is Track 1's primary evidence artifact.

## 2. The corpus, in one sentence

A single resume (two versions — v2.2 historical, v2.3 canonical) is the entire knowledge corpus for Milestone 1A. This is deliberate: a small, fully-understood corpus lets every claim about retrieval, evaluation, and diagnosis be independently hand-verified, rather than trusted on faith.

## 3. The pipeline (locked since Session 2)

```
Knowledge → Index → Retrieve → Assemble → Generate → Evaluate
```

Milestone 1A implements this **entirely deterministically, stdlib-only** — no LLM, no embeddings, no vector DB. That's not a limitation being apologized for; it's the point. A deterministic pipeline is one where every output can be traced to a specific cause, which is what makes the evaluation methodology provable rather than asserted. Real embeddings (BAAI/bge-small-en-v1.5), FAISS, DeepSeek generation, and Ragas/DeepEval activation are explicitly Milestone 2 scope.

## 4. Where to actually look

| If you want to understand... | Read... |
|---|---|
| Why the project exists, career context | `Career_Strategy_and_Search_Preferences.md` |
| The diagnostic framework used throughout | `docs/altm.md` (ALTM — AI Lifecycle Traceability Model) |
| What "done" means for Milestone 1A | `docs/MILESTONE_1A.md` (original DoD + P3.7.x annotations) |
| What was decided vs. what's still open | `docs/DEFERRED_ITEMS_REGISTER.md` |
| The reasoning behind major pivots | `ENGINEERING_JOURNEY.md` (companion doc) |
| What's technically built and verified | `MILESTONE_1A_CAPABILITY_INVENTORY.md` (companion doc) |
| The full sprint-by-sprint history | `docs/P3.*.md` reports, in numeric order |

## 5. Current state (as of Milestone 1A closure, Sprint P3.7.6)

**Milestone 1A is formally closed** — via an *annotated* Definition of Done, not a fully-satisfied one. Five of seven original acceptance criteria are met as originally written; two are met via explicit, reasoned Repository Owner rulings (not silently waived). This distinction is itself a demonstrated engineering-communication skill, not a technicality to gloss over.

- **372 tests passing**, all mutation-tested where it matters (0 surviving mutants on every audited module).
- **Full pipeline runnable end to end**: `python -m scripts.cli --question "..."` executes Knowledge → Chunk Corpus → Retriever → Generator → a fully traceable `GenerationResult`.
- **Milestone 1B** (deterministic infrastructure: Index Layer stub, DQ-5/6/7, JobOps/JD ingestion, SQL-filter retrieval) is scoped and authorized, not yet started.
- **Milestone 2** (real embeddings, FAISS, DeepSeek, Ragas/DeepEval) is planned, not yet started.

## 6. How work happens in this repository — the operating discipline

This matters as much as the code, and a new conversation should inherit it:

- **Docs-before-code, contract-first.** Every runtime artifact (`RetrievalResult`, `GenerationResult`) was frozen as a contract *before* implementation, in its own sprint, requiring explicit Repository Owner approval before the next sprint could begin.
- **Agents propose, the Repository Owner decides.** Every sprint prompt is reviewed for scope creep, unauthorized architecture, and undefined terms before it runs. Agents are instructed to **STOP and report** rather than invent an answer when a governing document doesn't define something — and this has happened repeatedly and productively (e.g., "Top-k Success Rate" had no authority behind it; the agent stopped rather than guessing).
- **Independent verification, not self-report.** Nearly every published number has a second, independently-derived check with zero shared code — the point is that agreement between two different implementations is real evidence, not agreement with itself.
- **Mutation testing over code coverage.** Passing tests alone have repeatedly been shown insufficient in this project (a 77/77-passing suite once masked a real defect). Mutation testing — deliberately breaking the code and confirming the tests catch it — is required for load-bearing specification suites.
- **Historical Preservation.** Committed reports are never edited after the fact, even when a later finding shows something in them needs updating. Corrections are appended as new, dated documents (the Erratum pattern), never silent rewrites.
- **Scope discipline, hard-won.** This project caught itself mid-spiral at least twice — once during a multi-sprint governance-hardening cycle that produced no new pipeline capability (P3.1.7–P3.1.8.5), and once when a proposed "Architecture Decision Review" sprint was about to formally re-derive a conclusion already reached in three paragraphs of conversation. Both times, the correction was explicit: *"the focus is not perfection, it's architect, implement, evaluate the metrics."*

## 7. If you're picking this up in a new conversation

Assume nothing has changed unless told otherwise. Check `docs/DEFERRED_ITEMS_REGISTER.md` and the most recent `docs/P3.*.md` report for the actual current state before proposing next steps — this document is a stable orientation layer, not a live status board.
