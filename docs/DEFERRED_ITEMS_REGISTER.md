# Deferred Items Register

**Repository:** `ai-quality-engineering`
**Status:** Active — **canonical repository authority for deferred capabilities**
**Established:** Sprint P3.7.4 (Repository Authority Synchronization), under authorization **A2** of `docs/P3.7.3_Repository_Owner_Constitutional_Decision.md`
**Baseline:** commit `180dcdc` — *docs(governance): record Repository Owner constitutional decision (P3.7.3)*, branch `main`, working tree clean
**Seeded from:** `docs/P3.7.2_Repository_Governance_Synchronization_Report.md` §5 (every item preserved) and `docs/P3.7.3_Repository_Owner_Constitutional_Decision.md` Decision 3 (allocation) and Decision 4 (reasoning)

---

## 1. Purpose and standing

This register is the **single canonical authority for what the repository has deferred, where it goes, and on whose authority.** Before it existed, that record was split across a historical report (`docs/P3.7.2_…` §5), a constitutional decision (`docs/P3.7.3_…` Decision 3), four contracts and two plans.

### 1.1 Why a standalone document

Neither existing home could carry an allocated register:

| Candidate home | Why not |
|---|---|
| `docs/P3.7.2_…` §5 | A historical report. Immutable under `docs/P3.7.3_…` **CP-3**; it cannot be extended as the repository advances |
| `docs/ENGINEERING_TRACEABILITY_REGISTER.md` | §1.2 bars scheduled work by construction: *"a deferred item awaiting a Repository Owner sequencing decision is scheduled work, which §1.2 bars from this register."* `docs/P3.7.3_…` did not amend that constraint, and neither does this document |

The two registers are complementary and do not overlap. `docs/ENGINEERING_TRACEABILITY_REGISTER.md` is **retrospective** — dispositions already made. This register is **prospective** — capabilities allocated to a milestone and not yet built.

### 1.2 What this register is NOT

| Not a… | Because |
|---|---|
| **Constitutional authority** | It records allocations; it does not make them. `docs/P3.7.3_…` is the authority for every row |
| **Roadmap** | It carries no dates, no sequence within a milestone, no sprint plan. `docs/roadmap.md` owns milestone ordering |
| **Backlog or task manager** | No assignees, priorities or states. A row is an allocation, not a ticket |
| **Findings register** | A defect with a disposition belongs in `docs/ENGINEERING_TRACEABILITY_REGISTER.md` §3 |

### 1.3 Maintenance rules

- A capability is **added** only when a Repository Owner decision or a committed authority defers it. Adding one here does not defer it.
- A capability is **reallocated** only by a Repository Owner constitutional decision, cited in the row.
- A capability is **never deleted.** When built, it moves to §8 *Discharged* with the sprint that built it.
- Every row cites both an **originating repository authority** and a **constitutional authorization**.
- **This register creates nothing.** Sprint P3.7.4 reclassified no capability, reallocated no capability and introduced no capability.

---

## 2. How to read a row

### 2.1 Capability class

| Class | Meaning |
|---|---|
| **Interface** | A contract or seam; no engine behind it |
| **Deterministic Runtime** | Executable, stdlib, reproducible, no probabilistic component |
| **Corpus** | Changes what the corpus *is* |
| **Validation** | An executable specification family |
| **Probabilistic Runtime** | Introduces a model or non-deterministic engine |
| **Evaluation Tooling** | One of the three named tools — DeepEval, Promptfoo, Ragas |
| **Metric** | A reported quantity over ground truth |
| **Regression** | Comparative across repository versions |
| **Diagnostic** | ALTM rule reachability or attribution |
| **Governance** | Documentation or authority amendment |

### 2.2 Blocking status

Current blocking status, as of commit `180dcdc` and **after** the Repository Owner Scope Ruling recorded in `docs/MILESTONE_1A.md`.

| Value | Meaning |
|---|---|
| **Blocks 1B** | Milestone 1B cannot complete without it |
| **Blocks 2 entry** | Milestone 2's governing precondition — *replace an implementation behind an existing contract* — is unsatisfiable without it |
| **Blocks 2** / **Blocks 3** | That milestone cannot complete without it |
| **Blocks 1A Closure** | Repository Owner sequencing decision, not repository fact |
| **Non-blocking — trigger-bound** | Owed only when a named trigger fires |
| **Non-blocking — accepted** | A closed decision, not open work |
| **Non-blocking — excluded** | Out of scope entirely; not a deferral |

**No capability blocks Milestone 1A.** The four that did are reassigned to Milestone 1B by `docs/P3.7.3_…` Decision 5. Their prior classification is preserved in the **P3.7.2 class** column and in §7, never deleted.

### 2.3 Rationale

Each row carries a one-line rationale. **Full reasoning — repository evidence, Repository Owner reasoning, why the capability belongs in its milestone, and why it does not belong in Milestone 1A — is at `docs/P3.7.3_…` Decision 4**, at the section id given in the row. This register points at that reasoning rather than restating it, so the two cannot drift apart.

---

## 3. Milestone 1B — Retrieval Infrastructure Foundation

**16 capabilities.** Eight reassigned from Milestone 1A by `docs/P3.7.3_…` Decision 5; eight affirmed here without ever having been Milestone 1A obligations.

| id | Capability | Class | Blocking status | P3.7.2 class | Auth. | Originating repository authority | Rationale (full reasoning at) |
|---|---|---|---|---|---|---|---|
| **1B-01** | `EmbeddingProvider` interface | Interface | **Blocks 2 entry** | Blocks Milestone 1A | A1, A7 | `docs/MILESTONE_1A.md` build item 3, criterion A-1; `docs/architecture.md` §5, §7; `docs/P3.7.2_…` §5.1 | Milestone 2 must replace an implementation behind a contract that already exists; this one does not exist — §4.1 R-1B-01/02 |
| **1B-02** | `VectorStore` interface | Interface | **Blocks 2 entry** | *(not in §5)* | A1, A7 | `docs/architecture.md` §5, §7; `docs/MILESTONE_1A.md` DoD status | Same seam, same constraint; scoped *"interface only, no implementation"* and absent — §4.1 R-1B-01/02 |
| **1B-03** | Index Layer — `Indexer` component (stub) | Deterministic Runtime | **Blocks 1B** | Blocks Milestone 1A | A1, A7 | `docs/MILESTONE_1A.md` build item 3; `docs/ENGINEERING_TRACEABILITY_REGISTER.md` §5; `docs/P3.7.2_…` §5.1 | An entire build item with **no owning sprint**; the ALTM Index stage has no component — §4.1 R-1B-03/04 |
| **1B-04** | Deterministic placeholder vectors | Deterministic Runtime | **Blocks 2 entry** | Blocks Milestone 1A | A1, A7 | `docs/MILESTONE_1A.md` build items 3 and 4; `docs/architecture.md` §9 | Placeholder values must be *meaningful* so Milestone 2 swaps values inside a correct shape — §4.1 R-1B-03/04 |
| **1B-05** | Job Description corpus | Corpus | **Blocks 1B** | Blocks Milestone 1A | A1 | `docs/MILESTONE_1A.md` F-1; `sample_rag/knowledge_manifest.json`; `datasets/SCHEMA.md` §9 | Criterion F-1's second half: the corpus catalogues two resume documents and no job description — §4.1 R-1B-05/06/07/12 |
| **1B-06** | JobOps structured data ingest | Corpus | **Blocks 1B** | Blocks Milestone 1A | A1 | `datasets/SCHEMA.md` §9; `docs/roadmap.md` §2.1; `docs/P3.7.2_…` §5.1 | The precondition for F-2; already deferred *"until the underlying SQLite schema fields are settled"* — §4.1 R-1B-05/06/07/12 |
| **1B-07** | SQL filtering exercised, incl. an exclusion-criteria case | Deterministic Runtime | **Blocks 1B** | Blocks Milestone 1A | A1, A7 | `docs/MILESTONE_1A.md` F-2; `sample_rag/retriever.py` module docstring | The stage is implemented but unexercised — `sql_filter_applied: False`. It needs data, not code — §4.1 R-1B-05/06/07/12 |
| **1B-08** | **DQ-5** — chunk validity as a corpus property | Validation | **Blocks 1B** | Does not block Milestone 1A | A7 | `docs/DATA_QUALITY_VALIDATION_PLAN.md` §8.1, §11.2 W6, §16 O-6 | Recorded blocker has **cleared** — `chunks.json` exists, digest `323723b4fe82` — and the check remains unimplemented — §4.1 R-1B-08/09 |
| **1B-09** | **DQ-6** — chunk referential integrity, incl. Chunk invariant 3's full form | Validation | **Blocks 1B** | Does not block Milestone 1A | A7 | `docs/DATA_QUALITY_VALIDATION_PLAN.md` §8.1, §11.2 W6; `docs/CHUNK_CONTRACT.md` §11, §17 inv. 3 | Same cleared blocker; validates the Chunk/Document join the Index Layer will consume — §4.1 R-1B-08/09 |
| **1B-10** | **DQ-7** — index-coverage validation | Validation | **Blocks 1B** | Blocks Milestone 1A | A1, A7 | `docs/DATA_QUALITY_VALIDATION_PLAN.md` §8.1, §16 O-6; `docs/MILESTONE_1A.md` build item 2 | Build item 2's own Index Coverage Validation clause; blocked by name on 1B-01 and 1B-03 — §4.1 R-1B-10 |
| **1B-11** | `documents[].indexed` semantics resolution | Governance + Deterministic Runtime | **Blocks 1B** | Blocks Closure | — | `sample_rag/knowledge_manifest.json`; `docs/P3.3.5_…` §4; `docs/ENGINEERING_TRACEABILITY_REGISTER.md` §5; `docs/P3.7.2_…` §5.2 | The field is **undefined**, not wrong: its contract names an indexing stage the repository does not have. 1B-03 creates it — §4.1 R-1B-11 |
| **1B-12** | Golden Dataset population for `job_*` / `jobops_*` | Corpus | **Blocks 1B** | *(not in §5)* | — | `datasets/SCHEMA.md` §9 | Schema-valid empty stubs; already deferred *"to a subsequent sprint once its source-data preconditions are met"* — 1B-05, 1B-06 — §4.1 R-1B-05/06/07/12 |
| **1B-13** | **O-5** — corpus-scale vacuity of DQ-2 / DQ-4 | Validation | Non-blocking — **trigger satisfied** | *(not in §5)* | A7 | `docs/DATA_QUALITY_VALIDATION_PLAN.md` §16 O-5 | **Trigger fired.** Recorded trigger is *"corpus expansion"*, originally attributed to 1B-05 / 1B-06; the expansion that fired it was resume-side (2 → 3 catalogued documents) at Milestone 1B Corpus Synchronization. Repository Owner ruled this satisfies the documented trigger. DQ-2 / DQ-4 are correspondingly less vacuous; the capability remains open work — §4.1 R-1B-13/14/15/16 |
| **1B-14** | **I-6** — `test_b6` hardcodes `Karthik_SR_Resume_v2_2.docx` | Validation | Non-blocking — **trigger satisfied** | Does not block Milestone 1A | — | `docs/ENGINEERING_TRACEABILITY_REGISTER.md` §3.5 | **Trigger fired**, same expansion and same Repository Owner ruling. Re-verified at Milestone 1B Corpus Synchronization: `tests/test_knowledge_source_construction.py` still resolves the hardcoded filename, because v2.2 is retained as a historical corpus artifact under RO-01. **A re-verification obligation met, not a failure** — §4.1 R-1B-13/14/15/16 |
| **1B-15** | **P3.1.7-ARCH-01** — JobOps-as-`Document` classification | Interface | Non-blocking — trigger-bound | Does not block Milestone 1A | — | `docs/ENGINEERING_TRACEABILITY_REGISTER.md` §3.5; `docs/DOCUMENT_CONTRACT.md` Outstanding Question 3 | *"Structurally excluded today by the manifest discovery gate."* 1B-06 removes the exclusion — §4.1 R-1B-13/14/15/16 |
| **1B-16** | **F-2-sym** — symlink containment | Validation | Non-blocking — **conditional** | Does not block Milestone 1A | — | `docs/ENGINEERING_TRACEABILITY_REGISTER.md` §3.5; `docs/adr/ADR-P3.1.7.2-F2-…` | Deliberate ADR boundary. **No specification is owed unless a symlinked corpus file actually appears** — §4.1 R-1B-13/14/15/16 |

**Milestone 1B exit condition** (`docs/P3.7.3_…` Work Package 6): every capability above, with `docs/MILESTONE_1A.md` criteria F-1, F-2 and A-1 satisfiable in substance, and the repository still passing a byte-identity determinism specification. **Criterion A-5 — zero imports of any embedding, vector-store or LLM-evaluation library — remains binding throughout Milestone 1B.**

---

## 4. Milestone 2 — AI-Enabled Retrieval & Generation

**17 capabilities.** Every one affirmed at Milestone 2 by an existing authority; **none was moved here by `docs/P3.7.3_…`.**

| id | Capability | Class | Blocking status | P3.7.2 class | Auth. | Originating repository authority | Rationale (full reasoning at) |
|---|---|---|---|---|---|---|---|
| **M2-01** | BGE embeddings — real `EmbeddingProvider` | Probabilistic Runtime | **Blocks 2** | Does not block Milestone 1A | — | `docs/MILESTONE_1A.md` Out of Scope; `docs/architecture.md` §5, §9; `docs/roadmap.md` §7 | The first probabilistic component; replaces 1B-01's stub behind an unchanged contract — §4.2 |
| **M2-02** | Vector store implementation | Probabilistic Runtime | **Blocks 2** | Does not block Milestone 1A | **A6** | `docs/architecture.md` §5, §9; `docs/roadmap.md` §7 | Replaces 1B-02's interface. **Implementation unresolved** — see §6 | §4.2 R-M2-02 |
| **M2-03** | Real BM25 | Probabilistic Runtime | **Blocks 2** | Does not block Milestone 1A | — | `docs/MILESTONE_1A.md` Out of Scope; `sample_rag/retriever.py` docstring | A ranking function replacing plain distinct-term overlap — §4.2 |
| **M2-04** | Hybrid retrieval — SQL + BM25 + Vector → RRF | Probabilistic Runtime | **Blocks 2** | Does not block Milestone 1A | — | `docs/MILESTONE_1A.md` Out of Scope; `docs/architecture.md` §10; `docs/roadmap.md` §4 | Fusion is meaningful only once all three routes return real results — §4.2 |
| **M2-05** | Reranking | Probabilistic Runtime | Non-blocking | Does not block Milestone 1A | — | `docs/MILESTONE_1A.md` Out of Scope; `docs/P3.7.1_…` §5.2 | Retrieval-quality optimization — §4.2 |
| **M2-06** | DeepSeek API generation | Probabilistic Runtime | **Blocks 2** | Does not block Milestone 1A | — | `docs/MILESTONE_1A.md` build item 5, Out of Scope; `docs/GENERATION_CONTRACT.md` §22 G-2 | Replaces the quotation Generator behind the frozen `generate(query, retrieval)` signature — §4.2 |
| **M2-07** | Ragas activation — Layer 2 | Evaluation Tooling | **Blocks 2** | Does not block Milestone 1A | — | `docs/roadmap.md` §5; `docs/altm.md` §9, §12; `docs/MILESTONE_1A.md` Out of Scope | Measures the Retrieve stage; presupposes real retrieval to measure — §4.2 |
| **M2-08** | DeepEval activation — Layer 3 | Evaluation Tooling | **Blocks 2** | Does not block Milestone 1A | — | `docs/roadmap.md` §5; `docs/altm.md` §9, §12 | Measures the Infer stage; meaningless against a verbatim-quotation generator — §4.2 |
| **M2-09** | Answer Relevancy (**Q-4**) | Metric | **Blocks 2** | Does not block Milestone 1A | — | `docs/GENERATION_CONTRACT.md` §23 Q-4; `docs/altm.md` §5 `ALTM-FINAL-ANSWER-1` | A Final Answer-stage metric owned by the Evaluation Engine; impact on 1A recorded as *"None"* — §4.2 R-M2-09 |
| **M2-10** | Context Precision / Context Recall | Metric | **Blocks 2** | *(not in §5)* | — | `docs/P3.3.3_…` §3; `docs/roadmap.md` §5 | Reserved for Ragas; the `chunk_`-prefixed metrics are explicitly not proxies for them — §4.2 |
| **M2-11** | Document Recall | Metric | Non-blocking | Does not block Milestone 1A | — | `docs/P3.3.5_…` §3 | Derivable post-enrichment and *"deliberately not implemented"* — §4.2 |
| **M2-12** | Assemble stage — Context Builder, `Prompt` artifact | Interface + Deterministic Runtime | **Blocks 2** | *(not in §5)* | — | `docs/GENERATION_CONTRACT.md` §21; `docs/architecture.md` §4, §5 | A prompt has no meaning until a model consumes one — §4.2 R-M2-12/13 |
| **M2-13** | Post-Process guardrail layer | Deterministic Runtime | Non-blocking | *(not in §5)* | — | `docs/GENERATION_CONTRACT.md` §21; `docs/altm.md` §4 | 1A exercises no guardrail; a guardrail constrains a model's output — §4.2 R-M2-12/13 |
| **M2-14** | `docs/architecture.md` §5 `Generator` row — Milestone 2 restatement | Governance | Non-blocking | Does not block Milestone 1A | — | `docs/P3.7.2_…` §5.3; `docs/GENERATION_CONTRACT.md` §22 | The row's *Future Evolution* column, revisited when DeepSeek lands. **Distinct from RO-03**, which is discharged — §4.2 R-M2-14 |
| **M2-15** | Embedding benchmarking; retrieval-quality optimization; prompt optimization | Probabilistic Runtime | Non-blocking | Does not block Milestone 1A | — | `docs/MILESTONE_1A.md` Out of Scope; `docs/P3.7.1_…` §5.6 | Optimization of implementations — what the 1A Governing Principle excludes by definition — §4.2 |
| **M2-16** | Semi-structured sources (LinkedIn / Greenhouse / Lever JSON) | Corpus | Non-blocking | Does not block Milestone 1A | — | `docs/MILESTONE_1A.md` Out of Scope | Deferred *"until JobOps genuinely ingests these"* — an external precondition — §4.2 |
| **M2-17** | Chunk-size / overlap benchmarking | Deterministic Runtime | Non-blocking | *(not in §5)* | — | `docs/architecture.md` §5 | Requires a retrieval-quality signal sensitive enough to distinguish configurations — §4.2 R-M2-17 |

---

## 5. Milestone 3 — Production Evaluation & Regression

**6 capabilities**, one spanning Milestones 2–3.

| id | Capability | Class | Blocking status | P3.7.2 class | Auth. | Originating repository authority | Rationale (full reasoning at) |
|---|---|---|---|---|---|---|---|
| **M3-01** | Promptfoo activation — Layer 4 | Regression | **Blocks 3** | Does not block Milestone 1A | — | `docs/roadmap.md` §5; `docs/altm.md` §9, §12; `docs/architecture.md` §9 | A differential instrument: requires two comparable baselines. A diff over one byte-identical baseline is trivially empty — §4.3 R-M3-01 |
| **M3-02** | `REACHABLE_STAGES` expansion (**Q-3**) | Diagnostic | **Blocks 3** | Does not block Milestone 1A | — | `docs/GENERATION_CONTRACT.md` §23 Q-3; `evaluation/altm_rules.py`; `docs/P3.5.2_…` §10 obs. 2 | **Repository Owner ruling supplying a milestone the authority left open.** Widening today would make structurally vacuous rules reachable — §4.3 R-M3-02 |
| **M3-03** | Production regression capabilities — `reports/baseline/`, `reports/regressions/` | Regression | **Blocks 3** | *(not in §5)* | — | `docs/architecture.md` §6, §9 | Scaffold directories defined by their content, and their content is Layer 4 output — §4.3 R-M3-03/04 |
| **M3-04** | Production-readiness hardening — benchmark reports, GitHub Actions on push | Regression | Non-blocking | *(not in §5)* | — | `docs/architecture.md` §9; `docs/roadmap.md` §10 | Hardening presupposes a stable system; retrieval and generation engines are both due for replacement — §4.3 R-M3-03/04 |
| **M3-05** | Assemble / Post-Process / Final Answer automated metrics | Metric | **Blocks 3** *(M2 partial)* | Does not block Milestone 1A | — | `docs/altm.md` §9; `docs/roadmap.md` §7 | *"A known, accepted gap under the three-tool scope freeze."* Final Answer partly covered by M2-09; Assemble and Post-Process reach only Layer 4 — §4.3 R-M3-05 |
| **M3-06** | `requirements.txt` declarations → real imports; `evaluation/*` scaffolds populated | Evaluation Tooling | **Blocks 2 and 3** | Does not block Milestone 1A | — | `docs/P3.7.2_…` §5.3; `docs/MILESTONE_1A.md` DoD status | *"A declaration is not an import, so A-5 holds as written."* `ragas/` and `deepeval/` at 2; `promptfoo/` at 3 — §4.3 R-M3-06 |

---

## 6. Unresolved implementation choice — M2-02 vector store

**Recorded, not resolved.** `docs/P3.7.3_…` authorization **A6** requires an explicit Repository Owner election, and none has been made as of Sprint P3.7.4.

| | |
|---|---|
| **Named by every committed authority** | **FAISS** — `docs/architecture.md` §5, §9, Capability Matrix; `docs/roadmap.md` §7; `docs/MILESTONE_1A.md` Out of Scope |
| **Named by the P3.7.3 sprint brief** | **sqlite-vec** — appears in no committed repository authority |
| **Milestone allocation** | **Milestone 2**, unaffected. Both candidates satisfy it |
| **Current standing** | **FAISS stands**, because it is what the committed authorities say |
| **To change it** | An explicit Repository Owner election, after which `docs/architecture.md` §5 and §9 and `docs/roadmap.md` §7 may be amended, citing that election — **not** `docs/P3.7.3_…`, which records the divergence rather than resolving it |

---

## 7. Retained by the Repository Owner — not milestone capabilities

**5 items.** Two were discharged by Sprint P3.7.4 and three by the Milestone 1B Corpus Synchronization execution; all are retained here with their discharge recorded, per §1.3 (*a capability is never deleted*). **No item in this section remains open.**

| id | Item | Class | Blocking status | P3.7.2 class | Auth. | Originating repository authority | Status |
|---|---|---|---|---|---|---|---|
| **RO-01** | Canonical Document Marking — version preference between resume v2.2 and v2.3 | Governance + Corpus | **Blocks 1A Closure** | Blocks Closure | — | `docs/GENERATION_CONTRACT.md` §21, §23 Q-5; `docs/P3.7.2_…` §6.6 | ✅ **DISCHARGED at Milestone 1B Corpus Synchronization.** Repository Owner decision: **resume v3.0 is canonical**; v2.2 and v2.3 remain historical corpus artifacts, catalogued with `canonical: false`. The decision space widened beyond the v2.2/v2.3 pair recorded in this row when v3.0 entered the corpus at commit `8ddcaa7` — §4.4 R-RO-01 |
| **RO-02** | `ALTM-KNOWLEDGE-1` determinability — *"wrong document version"* | Diagnostic | Non-blocking — trigger-bound | Does not block Milestone 1A | — | `docs/P3.3.5_…` §4; `docs/P3.3.4_…` §5, §7.1 | ✅ **DISCHARGED as a consequence of RO-01**, on this row's own terms — *"Follows RO-01 automatically; requires no engineering."* The rule's premise was a missing canonical designation, not a missing implementation; RO-01 supplies it. **No engineering was performed** — §4.4 R-RO-02 |
| **RO-03** | `docs/architecture.md` §5 `Generator` row amendment | Governance | — | Blocks Closure | **A5** | `docs/GENERATION_CONTRACT.md` §22, §20.3 | ✅ **DISCHARGED at Sprint P3.7.4.** The row now reads `Generator.generate(query, retrieval: RetrievalResult) -> GenerationResult`, dependency `Retriever` — §4.4 R-RO-03 |
| **RO-04** | `docs/roadmap.md` §0 status synchronization | Governance | — | Blocks Closure | **A4** | `docs/P3.7.2_…` §4.2, §5.2 | ✅ **DISCHARGED at Sprint P3.7.4.** Both false statements corrected; Milestone 1A and 1B status added — §4.4 R-RO-04 |
| **RO-05** | `datasets/synthetic/` purpose decision | Governance | **Blocks 1B start** | *(not in §5)* | — | `docs/architecture.md` §11; `datasets/README.md` | ✅ **DISCHARGED at Milestone 1B Corpus Synchronization.** Repository Owner decision: the directory is **removed**. The knowledge corpus is intentionally composed of real, versioned knowledge artifacts and their Golden Datasets. Any future synthetic dataset requires an explicit Repository Owner decision naming both its architectural purpose and the milestone that consumes it. Milestone 1A never wrote data into it — §4.4 R-RO-05 |

---

## 8. No milestone allocation — recorded with reason

**7 items.** Each is recorded so that a future sprint does not mistake it for unscheduled work.

| id | Item | Reason no allocation | Originating repository authority |
|---|---|---|---|
| **NA-01** | Report coverage for Sprints P3.2.0–P3.2.4 and P3.3.1 | *"Reconstructing a report for a past sprint would manufacture history."* Barred by **CP-3**. Provenance is recoverable from commits, docstrings and consuming reports — but from no single document | `docs/P3.7.2_…` §4.4; `docs/ENGINEERING_TRACEABILITY_REGISTER.md` §5 |
| **NA-02** | **I-7** — `test_a15` allowlist tracks CPython-synthesized dataclass members | A conditional trigger — *"re-verify at the next CPython upgrade"* — that no milestone controls | `docs/ENGINEERING_TRACEABILITY_REGISTER.md` §3.5 |
| **NA-03** | **A-3** — `discover_manifest_entries` bounded only by a docstring | Conditional: *"re-inspect if that function grows"* | `docs/ENGINEERING_TRACEABILITY_REGISTER.md` §3.5 |
| **NA-04** | Accepted limitations of P3.5.2 §9 and P3.6.0 §9 — whole-chunk evidence spans; `answer_text` separator dependency; mutable containers on a frozen dataclass; corpus reload per invocation; `--help` outside byte-identity; abstention reachable only by lexical disjointness; `--question` as the entire interface; POSIX-only byte-identity | *"Recorded as accepted, not as defects."* Allocating one would silently reclassify it as a defect awaiting repair, reversing an accepted decision — barred by **CP-9**. Several will be *superseded* by later milestones; supersession is a consequence of other work, not an obligation of it | `docs/P3.5.2_…` §9; `docs/P3.6.0_…` §9; `docs/P3.7.2_…` §5.3 |
| **NA-05** | Two structural identities in metrics validation that cannot fail | A disclosure so they are not read as independent evidence. The disclosure *is* the remedy | `docs/P3.3.3_…` §5 finding R-1 |
| **NA-06** | Provenance citations to `AI_QA_Learning_Roadmap_Scope.md`, `Session2_RAG_Architecture_Closure.md`, `AI_Systems_Diagnostic_Framework_v1.md`, `Career_Strategy_and_Search_Preferences.md` | Citations to pre-repository working notes, not broken links. *"Repointing them would assert a supersession no authority has recorded"* | `docs/P3.7.2_…` §4.5 |
| **NA-07** | LangChain / LangGraph; agent orchestration; MLflow; LangSmith; Phoenix; distributed retrieval; GPU optimization; production orchestration; a second GitHub project | **Excluded, not deferred.** `docs/roadmap.md` §7 marks some rows *"Deferred to Milestone 2"* and these *"Out of scope entirely"* in the same table. Allocating one would convert an exclusion into a plan | `docs/roadmap.md` §7; `docs/architecture.md` §11; `docs/MILESTONE_1A.md` Out of Scope |

### 8.1 Discharged capabilities

Capabilities built or performed, retained per §1.3.

| id | Capability | Discharged by | Evidence |
|---|---|---|---|
| **RO-03** | `docs/architecture.md` §5 `Generator` row amendment | Sprint **P3.7.4**, authorization A5 | `docs/architecture.md` §5; `docs/P3.7.4_Repository_Authority_Synchronization_Report.md` |
| **RO-04** | `docs/roadmap.md` §0 status synchronization | Sprint **P3.7.4**, authorization A4 | `docs/roadmap.md` §0; `docs/P3.7.4_…` |
| **RO-01** | Canonical Document Marking | **Milestone 1B Corpus Synchronization**, Repository Owner decision | `scripts/build_manifest.py` `CANONICAL_SOURCES`; `sample_rag/knowledge_manifest.json` digest `84a3c4e7a853`, `d1a4d530f9c1` `canonical: true`; `docs/P3.7.6_…` appended erratum |
| **RO-02** | `ALTM-KNOWLEDGE-1` determinability | **Consequence of RO-01** — no engineering performed | `evaluation/altm_rules.py` unchanged; `sample_rag/knowledge_manifest.json` canonical designation; `docs/P3.7.6_…` appended erratum |
| **RO-05** | `datasets/synthetic/` purpose decision | **Milestone 1B Corpus Synchronization**, Repository Owner decision | `datasets/synthetic/` removed; `docs/architecture.md` §6, §11; `datasets/README.md`; `datasets/SCHEMA.md` §7; `README.md`; `docs/roadmap.md` §0 |

**Commit reference.** These three rows are discharged by the working-tree change under Repository Owner review; the commit that carries it does not yet exist. This follows the precedent `docs/P3.7.6_…` §3 set for the same situation — *"That commit does not yet exist — it is the commit that will add this document."* **The commit hash is to be recorded here at commit time.** The evidence column above cites the artifacts, which are verifiable independently of the hash.

---

## 9. Sprint sequence — recorded under authorization A8

Four committed authorities carry different sprint numbers for the same downstream work. **Each was accurate when committed, and none is corrected** (**CP-3**). This section exists so a reader of any one of them can resolve the reference.

| Authority | States |
|---|---|
| `docs/P3.7.1_…` §8 | Closure belongs to **P3.7.3** |
| `docs/P3.7.2_…` §5.2, §8 | Canonical Document Marking is **P3.7.3**; closure is **P3.7.4** |
| `docs/P3.7.3_…` Work Package 7, A8 | Constitutional Decision is **P3.7.3**; Canonical Document Marking is **P3.7.4**; closure is **P3.7.5** |
| **P3.7.4 sprint brief** (Repository Owner) | **P3.7.4 is Repository Authority Synchronization**; closure is **P3.7.5** |

### Current sequence

```text
P3.7.0  Manual Review Evidence                        ✅ committed 8e73173
P3.7.1  Manual Review Assessment                      ✅ committed d9a6db4
P3.7.2  Governance Synchronization                    ✅ committed 8b2d387
P3.7.3  Repository Owner Constitutional Decision      ✅ committed 180dcdc
P3.7.4  Repository Authority Synchronization          ◀ this sprint
P3.7.5  Milestone 1A Closure & Frozen Baseline
```

### 9.1 Canonical Document Marking is now unsequenced — Repository Owner decision required

`docs/P3.7.3_…` Work Package 7 authorized *"Progression to P3.7.4 Canonical Document Marking."* The P3.7.4 sprint brief re-designates P3.7.4 as Repository Authority Synchronization and places Milestone 1A Closure at P3.7.5. **Canonical Document Marking (RO-01) therefore has no sprint number.**

This register **records** the condition and does not resolve it: assigning a sprint number is a Repository Owner sequencing decision, and Sprint P3.7.4 may not create constitutional authority.

**What the Repository Owner should weigh.** `docs/P3.7.2_…` §5.2 classifies RO-01 **Blocks Closure — Repository Owner sequencing decision**, and §6.6 verifies the repository ready for it on three grounds. If RO-01 is not sequenced before P3.7.5, Milestone 1A closes with a *Blocks Closure* item outstanding — which is legitimate, because that class is explicitly a sequencing decision rather than repository fact, but it should be a decision rather than an oversight.

---

## 10. Reconciliation to `docs/P3.7.2_…` §5

Every item in the source register maps to at least one row above. **Nothing was dropped, merged away or reclassified.**

### 10.1 §5.1 — *Blocks Milestone 1A* (4 items)

| `docs/P3.7.2_…` §5.1 item | Register ids | Owning milestone now |
|---|---|---|
| Index Layer — `Indexer` + placeholder vectors behind `EmbeddingProvider` | **1B-01, 1B-02, 1B-03, 1B-04** | Milestone 1B |
| DQ-7 — index-coverage validation | **1B-10** | Milestone 1B |
| Job description in the corpus (F-1) | **1B-05** | Milestone 1B |
| SQL-filter retrieval against real JobOps data (F-2) | **1B-06, 1B-07** | Milestone 1B |

**All four reassigned to Milestone 1B** by `docs/P3.7.3_…` Decision 5, recorded in `docs/MILESTONE_1A.md` under authorization A1. **Their §5.1 classification is preserved in the P3.7.2 class column and here; it is not deleted.**

### 10.2 §5.2 — *Blocks Closure* (4 items)

| `docs/P3.7.2_…` §5.2 item | Register id | Status |
|---|---|---|
| Canonical Document Marking | **RO-01** | Open — unsequenced, §9.1 |
| `knowledge_manifest.json` `indexed` semantics | **1B-11** | Allocated to Milestone 1B; **not resolved** |
| `docs/architecture.md` §5 `Generator` row amendment | **RO-03** | ✅ Discharged at P3.7.4 |
| `docs/roadmap.md` §0 status synchronization | **RO-04** | ✅ Discharged at P3.7.4 |

### 10.3 §5.3 — *Does not block Milestone 1A*

| `docs/P3.7.2_…` §5.3 item | Register id |
|---|---|
| DQ-5 · DQ-6 | **1B-08** · **1B-09** |
| `REACHABLE_STAGES` widening (Q-3) | **M3-02** |
| Answer Relevancy (Q-4) | **M2-09** |
| Document Recall | **M2-11** |
| `architecture.md` §5 Generator row — Milestone 2 restatement | **M2-14** |
| Ragas activation · DeepEval activation · Promptfoo activation | **M2-07** · **M2-08** · **M3-01** |
| Real embeddings · Real BM25 · FAISS / any vector store · Hybrid retrieval / RRF · Real LLM generation | **M2-01** · **M2-03** · **M2-02** · **M2-04** · **M2-06** |
| Reranking; retrieval-quality optimization; embedding benchmarking; prompt optimization; performance optimization; semi-structured sources | **M2-05**, **M2-15**, **M2-16** |
| Agent orchestration; a second GitHub project | **NA-07** *(excluded, not deferred)* |
| Assemble / Post-Process / Final Answer automated metrics | **M3-05** *(with **M2-12**, **M2-13**)* |
| `requirements.txt` declarations; empty `evaluation/` scaffolds | **M3-06** |
| Report coverage for P3.2.x / P3.3.1 | **NA-01** |
| Symlink containment (F-2-sym) | **1B-16** |
| I-6 · I-7 · A-3 · P3.1.7-ARCH-01 | **1B-14** · **NA-02** · **NA-03** · **1B-15** |
| `ALTM-KNOWLEDGE-1` determinability | **RO-02** |
| Accepted limitations of P3.5.2 §9 and P3.6.0 §9 | **NA-04** |

### 10.4 Capabilities added by `docs/P3.7.3_…` from authorities outside `docs/P3.7.2_…` §5

Twelve capabilities were surfaced by the constitutional audit from authorities the source register did not enumerate. **None is new work; each was already deferred by the authority named.**

| Register id | Capability | Authority it was already deferred by |
|---|---|---|
| **1B-02** | `VectorStore` interface | `docs/architecture.md` §5, §7 |
| **1B-12** | `job_*` / `jobops_*` Golden Dataset population | `datasets/SCHEMA.md` §9 |
| **1B-13** | O-5 corpus-scale vacuity | `docs/DATA_QUALITY_VALIDATION_PLAN.md` §16 |
| **M2-10** | Context Precision / Context Recall | `docs/P3.3.3_…` §3 |
| **M2-12** · **M2-13** | Assemble stage / Context Builder · Post-Process | `docs/GENERATION_CONTRACT.md` §21 |
| **M2-17** | Chunk-size / overlap benchmarking | `docs/architecture.md` §5 |
| **M3-03** · **M3-04** | `reports/` regression output · production-readiness hardening | `docs/architecture.md` §6, §9 |
| **RO-05** | `datasets/synthetic/` purpose decision | `docs/architecture.md` §11 |
| **NA-05** | Structural identities in metrics validation | `docs/P3.3.3_…` §5 R-1 |
| **NA-06** | Provenance citations to pre-repository notes | `docs/P3.7.2_…` §4.5 |

### 10.5 Count

| Section | Capabilities |
|---|---|
| §3 Milestone 1B | **16** |
| §4 Milestone 2 | **17** |
| §5 Milestone 3 | **6** |
| §7 Retained — Repository Owner | **5** |
| §8 No allocation | **7** |
| **Total** | **51** |
| Remaining in Milestone 1A | **0** |

Matches `docs/P3.7.3_…` Decision 3 §3.6 exactly. **No capability was reclassified, reallocated or introduced by Sprint P3.7.4.**

---

*This register is the canonical repository authority for deferred capabilities. It records allocations made by `docs/P3.7.3_Repository_Owner_Constitutional_Decision.md`; it makes none of its own. Reallocation requires a Repository Owner constitutional decision, cited in the affected row.*
