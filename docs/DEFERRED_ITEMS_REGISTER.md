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
- A capability is **never deleted.** When discharged, its original register row is **retained in place and marked ✅** with the sprint and the evidence that discharged it.
- **Git is the authoritative implementation history; this register records engineering state.** A discharge names its **sprint** and its **evidence** — not a commit hash. No row carries a placeholder awaiting one, and no commit is made solely to insert one. Commit references already present are historical records and are retained under **CP-3** — see §8.1.
- Every row cites both an **originating repository authority** and a **constitutional authorization**.
- **An implementation sprint may synchronize this register** when **both** conditions hold: the sprint **explicitly discharges** a registered capability, and the sprint's brief **explicitly authorizes** register synchronization. Ratified by the Repository Owner at the Sprint M2.01A review; recorded here at Sprint **M2.01A-R**. Sprint **M2.01A**'s discharge of **M2-01** is the case it was ratified on, and that entry stands. The permission covers **recording engineering state only** — allocation, reallocation and creation remain governed by the rules above and require Repository Owner authority.
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
| **Blocks 2B** | Milestone 2's **2B** stage — structured corpus integration, JobOps activation — cannot complete without it. Added at Sprint RO-02 / RO-03 for the four capabilities **RO-06** reallocated out of the Milestone 1B completion boundary; see §3.1 |
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

**16 capabilities.** Eight reassigned from Milestone 1A by `docs/P3.7.3_…` Decision 5; eight affirmed here without ever having been Milestone 1A obligations. **Nine are discharged and retained here with their discharge recorded**, per §1.3 (*a capability is never deleted*) — **1B-08** and **1B-09** by Sprint 1B.1; **1B-01**, **1B-02**, **1B-03**, **1B-04** and **1B-10** by Sprint 1B.2; **1B-11** by Sprint 1B.2B, under Repository Owner ruling **R-02**; and **1B-13** by Sprint 1B.2C, discharged by verification rather than by implementation. **Four — 1B-05, 1B-06, 1B-07 and 1B-12 — are reallocated to Milestone 2B by Repository Owner ruling RO-06** and are retained in this section rather than moved, per §1.3's *never deleted* rule and **CP-3**; their rows carry the reallocation and §4 cross-references them. **Three remain open at Milestone 1B**, all non-blocking and trigger-bound: **1B-14**, **1B-15**, **1B-16**. The count is unchanged for that reason: it counts capabilities allocated, not capabilities outstanding.

| id | Capability | Class | Blocking status | P3.7.2 class | Auth. | Originating repository authority | Rationale (full reasoning at) |
|---|---|---|---|---|---|---|---|
| **1B-01** | `EmbeddingProvider` interface | Interface | **Blocks 2 entry** | Blocks Milestone 1A | A1, A7 | `docs/MILESTONE_1A.md` build item 3, criterion A-1; `docs/architecture.md` §5, §7; `docs/P3.7.2_…` §5.1 | ✅ **DISCHARGED at Sprint 1B.2 (Index Layer).** The contract Milestone 2 replaces an implementation behind now exists — `sample_rag/embedding.py`, the Protocol shape `docs/architecture.md` §7 states — §4.1 R-1B-01/02 |
| **1B-02** | `VectorStore` interface | Interface | **Blocks 2 entry** | *(not in §5)* | A1, A7 | `docs/architecture.md` §5, §7; `docs/MILESTONE_1A.md` DoD status | ✅ **DISCHARGED at Sprint 1B.2 (Index Layer).** `sample_rag/vector_store.py`, Protocol only — the *"interface only, no implementation"* scope is preserved and specified structurally — §4.1 R-1B-01/02 |
| **1B-03** | Index Layer — `Indexer` component (stub) | Deterministic Runtime | **Blocks 1B** | Blocks Milestone 1A | A1, A7 | `docs/MILESTONE_1A.md` build item 3; `docs/ENGINEERING_TRACEABILITY_REGISTER.md` §5; `docs/P3.7.2_…` §5.1 | ✅ **DISCHARGED at Sprint 1B.2 (Index Layer).** `sample_rag/indexer.py` gives the ALTM Index stage a component; `docs/roadmap.md` §3's *Chunking → Indexing → Retrieval* order is restored — §4.1 R-1B-03/04 |
| **1B-04** | Deterministic placeholder vectors | Deterministic Runtime | **Blocks 2 entry** | Blocks Milestone 1A | A1, A7 | `docs/MILESTONE_1A.md` build items 3 and 4; `docs/architecture.md` §9 | ✅ **DISCHARGED at Sprint 1B.2 (Index Layer).** Content-derived and deterministic, meeting build item 4's *meaningful, not arbitrary* standard: identical text yields an identical vector, differing text differs, width is stable — §4.1 R-1B-03/04 |
| **1B-05** | Job Description corpus | Corpus | **Blocks 2B** | Blocks Milestone 1A | A1, **RO-06** | `docs/MILESTONE_1A.md` F-1; `sample_rag/knowledge_manifest.json`; `datasets/SCHEMA.md` §9 | Criterion F-1's second half: the corpus catalogues three resume documents and no job description — §4.1 R-1B-05/06/07/12. **Reallocated to Milestone 2B by Repository Owner ruling RO-06 — Milestone 1B Corpus Capability Reallocation** (§3.1): the remaining work is external-data integration, not deterministic repository engineering. Purpose, ownership, class, acceptance criteria and originating authority are unchanged |
| **1B-06** | JobOps structured data ingest | Corpus | **Blocks 2B** | Blocks Milestone 1A | A1, **RO-06** | `datasets/SCHEMA.md` §9; `docs/roadmap.md` §2.1; `docs/P3.7.2_…` §5.1 | The precondition for F-2; already deferred *"until the underlying SQLite schema fields are settled"* — §4.1 R-1B-05/06/07/12. **Reallocated to Milestone 2B by RO-06** (§3.1). It is the JobOps activation RO-07 names as Milestone 2B's defining event. Purpose, ownership, class, acceptance criteria and originating authority are unchanged |
| **1B-07** | SQL filtering exercised, incl. an exclusion-criteria case | Deterministic Runtime | **Blocks 2B** | Blocks Milestone 1A | A1, A7, **RO-06** | `docs/MILESTONE_1A.md` F-2; `sample_rag/retriever.py` module docstring | The stage is implemented but unexercised — `sql_filter_applied: False`. It needs data, not code — §4.1 R-1B-05/06/07/12. **Reallocated to Milestone 2B by RO-06** (§3.1). This is the structured retrieval branch **M2-04** activates at 2B under the Repository Owner clarification recorded in §3.1. Purpose, ownership, class, acceptance criteria and originating authority are unchanged |
| **1B-08** | **DQ-5** — chunk validity as a corpus property | Validation | **Blocks 1B** | Does not block Milestone 1A | A7 | `docs/DATA_QUALITY_VALIDATION_PLAN.md` §8.1, §11.2 W6, §16 O-6 | ✅ **DISCHARGED at Sprint 1B.1 (Corpus Integrity).** Recorded blocker had cleared — `chunks.json` exists — and the check is now implemented as plan §11.2 phase **W6** in `tests/test_data_quality.py` — §4.1 R-1B-08/09 |
| **1B-09** | **DQ-6** — chunk referential integrity, incl. Chunk invariant 3's full form | Validation | **Blocks 1B** | Does not block Milestone 1A | A7 | `docs/DATA_QUALITY_VALIDATION_PLAN.md` §8.1, §11.2 W6; `docs/CHUNK_CONTRACT.md` §11, §17 inv. 3 | ✅ **DISCHARGED at Sprint 1B.1 (Corpus Integrity).** Same cleared blocker; the Chunk/Document join the Index Layer will consume is now validated, including invariant 3's full reconstruction form — §4.1 R-1B-08/09 |
| **1B-10** | **DQ-7** — index-coverage validation | Validation | **Blocks 1B** | Blocks Milestone 1A | A1, A7 | `docs/DATA_QUALITY_VALIDATION_PLAN.md` §8.1, §16 O-6; `docs/MILESTONE_1A.md` build item 2 | ✅ **DISCHARGED at Sprint 1B.2 (Index Layer).** Both named blockers — 1B-01 and 1B-03 — cleared in the same sprint; build item 2's Index Coverage Validation clause is specified in `tests/test_data_quality.py` — §4.1 R-1B-10 |
| **1B-11** | `documents[].indexed` semantics resolution | Governance + Deterministic Runtime | **Blocks 1B** | Blocks Closure | **R-02** | `sample_rag/knowledge_manifest.json`; `docs/P3.3.5_…` §4; `docs/ENGINEERING_TRACEABILITY_REGISTER.md` §5; `docs/P3.7.2_…` §5.2 | ✅ **DISCHARGED at Sprint 1B.2B (Repository Owner Governance Synchronization)** by ruling **R-02 — Runtime Index Semantics**. The field was **undefined**, not wrong, and its resolution was never reachable by implementation alone. R-02 resolves it by **removing it from the persisted schema**: `indexed` is a derived runtime property, the manifest stays a deterministic knowledge artifact, and **DQ-7** remains the deterministic proof of runtime representation — §8.1 |
| **1B-12** | Golden Dataset population for `job_*` / `jobops_*` | Corpus | **Blocks 2B** | *(not in §5)* | **RO-06** | `datasets/SCHEMA.md` §9 | Schema-valid empty stubs; already deferred *"to a subsequent sprint once its source-data preconditions are met"* — 1B-05, 1B-06 — §4.1 R-1B-05/06/07/12. **Reallocated to Milestone 2B by RO-06** (§3.1), with the source-data preconditions it names. Purpose, ownership, class, acceptance criteria and originating authority are unchanged |
| **1B-13** | **O-5** — corpus-scale vacuity of DQ-2 / DQ-4 | Validation | Non-blocking — **trigger satisfied** | *(not in §5)* | A7 | `docs/DATA_QUALITY_VALIDATION_PLAN.md` §16 O-5 | ✅ **DISCHARGED at Sprint 1B.2C (Verification).** Recorded trigger is *"corpus expansion"*, originally attributed to 1B-05 / 1B-06; the expansion that fired it was resume-side (2 → 3 catalogued documents) at Milestone 1B Corpus Synchronization, which the Repository Owner ruled satisfies the documented trigger. **Verification confirmed the vacuity is cleared, not merely reduced**: O-5's mitigation was never code, and the DQ-2 / DQ-4 specifications are corpus-size agnostic, so the expansion discharged the item on its own. DQ-2's real-corpus predicates now perform three genuine pairwise comparisons and DQ-4's asserts a real three-way one-to-one mapping. **No implementation was required or performed**; the specification disclosures in `tests/test_data_quality.py`, which still stated the one-document limitation, were synchronized. DQ-4's separate **S1 structural** limit is unchanged and is explicitly not O-5 — §4.1 R-1B-13/14/15/16 |
| **1B-14** | **I-6** — `test_b6` hardcodes `Karthik_SR_Resume_v2_2.docx` | Validation | Non-blocking — **trigger satisfied** | Does not block Milestone 1A | — | `docs/ENGINEERING_TRACEABILITY_REGISTER.md` §3.5 | **Trigger fired**, same expansion and same Repository Owner ruling. Re-verified at Milestone 1B Corpus Synchronization: `tests/test_knowledge_source_construction.py` still resolves the hardcoded filename, because v2.2 is retained as a historical corpus artifact under RO-01. **A re-verification obligation met, not a failure** — §4.1 R-1B-13/14/15/16 |
| **1B-15** | **P3.1.7-ARCH-01** — JobOps-as-`Document` classification | Interface | Non-blocking — trigger-bound | Does not block Milestone 1A | — | `docs/ENGINEERING_TRACEABILITY_REGISTER.md` §3.5; `docs/DOCUMENT_CONTRACT.md` Outstanding Question 3 | *"Structurally excluded today by the manifest discovery gate."* 1B-06 removes the exclusion — §4.1 R-1B-13/14/15/16 |
| **1B-16** | **F-2-sym** — symlink containment | Validation | Non-blocking — **conditional** | Does not block Milestone 1A | — | `docs/ENGINEERING_TRACEABILITY_REGISTER.md` §3.5; `docs/adr/ADR-P3.1.7.2-F2-…` | Deliberate ADR boundary. **No specification is owed unless a symlinked corpus file actually appears** — §4.1 R-1B-13/14/15/16 |

**Milestone 1B exit condition** (`docs/P3.7.3_…` Work Package 6): every capability above, with `docs/MILESTONE_1A.md` criteria F-1, F-2 and A-1 satisfiable in substance, and the repository still passing a byte-identity determinism specification. **Criterion A-5 — zero imports of any embedding, vector-store or LLM-evaluation library — remains binding throughout Milestone 1B.**

> **Exit condition synchronized at Sprint RO-02 / RO-03**, under Repository Owner ruling **RO-06**. The condition above is retained as written — it was accurate when set, and **CP-3** governs. What changed is its scope, not its text: **RO-06 removed 1B-05, 1B-06, 1B-07 and 1B-12 from the Milestone 1B completion boundary**, so "every capability above" now means every capability still allocated to Milestone 1B.
>
> **Consequence for F-1 and F-2, stated explicitly because the condition names them.** 1B-05 is criterion **F-1**'s second half and 1B-07 is criterion **F-2**. Both moved to Milestone 2B, so **F-1 and F-2 become satisfiable in substance at Milestone 2B, not at Milestone 1B.** Criterion **A-1** and the byte-identity determinism specification are unaffected and were satisfied at Milestone 1B. `docs/MILESTONE_1A.md` is **not** amended: it is a completed Milestone 1 engineering artifact, and RO-06 changes milestone allocation, not the criteria themselves.
>
> **Milestone 1B engineering implementation is complete as of commit `e76623f`** (RO-06). The three capabilities still allocated here — **1B-14**, **1B-15**, **1B-16** — are all *non-blocking, trigger-bound* and none was ever a completion obligation.

### 3.1 Repository Owner rulings RO-06 and RO-07 — Sprint RO-02 / RO-03

Issued at Sprint **RO-02 / RO-03 (Repository Owner Governance Synchronization)**, after the Authority Discrepancy Report produced at Sprint **M2.0**. Both are fixed repository authority. This section records them; it does not interpret them.

**On the numbering.** These two rulings were issued as *RO-02* and *RO-03* and **renumbered to RO-06 and RO-07 at Sprint RO-06 / RO-07**, because those identifiers were already in use by two discharged items in §7. **The issuing sprint keeps its original name — Sprint RO-02 / RO-03 — under CP-3**, since a sprint label is a historical record. Only the rulings were renumbered; neither ruling's effect, scope, or reasoning changed.

| Ruling | Title | Effect |
|---|---|---|
| **RO-06** | **Milestone 1B Corpus Capability Reallocation** | Reallocates **1B-05**, **1B-06**, **1B-07**, **1B-12** from the Milestone 1B completion boundary to **Milestone 2B**. Their remaining work is external-data integration — Job Description corpus, JobOps repository, structured job data — rather than deterministic repository engineering. **Milestone 1B engineering implementation is complete as of commit `e76623f`.** Changes milestone allocation only: not capability purpose, ownership, acceptance criteria, originating authority, or architecture |
| **RO-07** | **Milestone 2 Execution Sequencing** | Milestone 2 executes in three stages — **2A** controlled single-corpus semantic retrieval, **2B** structured corpus integration (JobOps activation), **2C** remaining approved Milestone 2 capabilities. **Sequencing only**: adds, removes and splits no capability, redesigns no architecture, and does not alter Milestone 3 |

**Repository Owner clarification — M2-04 is one capability and shall not be split.** `docs/architecture.md`'s approved Hybrid Retrieval architecture is unchanged. **M2-04** reaches its stages by *staged activation*, not by division: Milestone **2A** exercises the semantic and lexical retrieval routes; Milestone **2B** activates the structured SQL branch and completes the architecture. This register continues to carry **M2-04 as a single row** — see §4.

**Where the stage allocation lives.** RO-07 states that detailed capability allocation *"remains repository planning."* §1.2 of this register bars it from carrying *"no sequence within a milestone"* and assigns milestone ordering to `docs/roadmap.md`. **The 2A / 2B / 2C allocation is therefore recorded in `docs/roadmap.md` §1.1, not here.** This register continues to record *which milestone* a capability belongs to; the roadmap records *which stage within it*.

> **Identifier collision — resolved at Sprint RO-06 / RO-07.** As first issued, the two rulings above were numbered **RO-02** and **RO-03**, which collided with two items already in §7: a discharged **RO-02** (*`ALTM-KNOWLEDGE-1` determinability*) and a discharged **RO-03** (*`docs/architecture.md` §5 `Generator` row amendment*), both from the P3.7.4 / Milestone 1B Corpus Synchronization series. Sprint **RO-06 / RO-07** resolved it by **renumbering the two rulings in this section to RO-06 and RO-07**, repository-wide.
>
> **The §7 pair is untouched and keeps its original numbers.** RO-02 and RO-03 there continue to mean `ALTM-KNOWLEDGE-1` determinability and the `Generator` row amendment, exactly as they always have; no citation of either was altered, including the *"Distinct from RO-03"* note in the **M2-14** row of §4, which refers to the §7 RO-03 and remains correct as written.
>
> **No ruling's substance changed — only two identifiers.** Citations remain title-qualified as a readability convention, not as a disambiguation crutch.

---

## 4. Milestone 2 — AI-Enabled Retrieval & Generation

**17 capabilities.** Every one affirmed at Milestone 2 by an existing authority; **none was moved here by `docs/P3.7.3_…`.** **Six — M2-01, M2-02, M2-03, M2-06, M2-12 and M2-18 — are discharged and retained here with their discharges recorded**, per §1.3 (*a capability is never deleted*), by Sprints M2.01A, M2.01C, M2.03, M2.06, M2.12 and M2.18 respectively. The count is unchanged for that reason: it counts capabilities allocated, not capabilities outstanding.

> **▶ Count synchronized at Sprint RO-15 — the paragraph above is retained as written.** It was accurate when written and **CP-3** governs: **the seventeen capabilities it counts are exactly the seventeen `docs/P3.7.3_…` affirmed at Milestone 2**, and that statement — including *"none was moved here by `docs/P3.7.3_…`"* — remains true of those seventeen. **Repository Owner ruling RO-15 (§4.7) subsequently allocates an eighteenth — `M2-18`, Execution Evidence / Traceability** — which is a **subsequent Repository Owner allocation**, not a member of the affirmed set and not a reclassification of anything in it. **The section therefore now carries 18 capability rows.** No existing row is edited by that allocation, no capability is split, renamed or reallocated, and no derivative identifier is created. The corresponding total is recorded at §10.5.

> **M2-02's acceptance was staged by Repository Owner ruling RO-08 — see §4.1.** It remained **one capability** throughout: Sprint M2.01B built the persistent FAISS-backed foundation without discharging it, and Sprint M2.01C supplied the `query` side. **No derivative identifier was created, no row was duplicated, and no capability was reallocated.** The count above is unaffected. **M2-02 is now DISCHARGED by Repository Owner ruling RO-10 — see §4.3**, which fixes the Milestone 2A discharge scope as `query(vector, top_k)` plus the whole-corpus rebuild lifecycle and **defers `upsert`** without implementing, stubbing or allocating it.
>
> **The artifacts M2-02 produces are governed by Repository Owner ruling RO-09 — see §4.2.** The FAISS index and its metadata are **derived, rebuildable runtime/build state**, not Git source artifacts; the canonical corpus remains authoritative; and **M2.01C owns the concrete runtime location and consumption lifecycle**. RO-09 discharges nothing and allocates nothing — M2-02's status above is unaffected by it.

> **Criterion A-5 — the embedding-library portion lapsed at Sprint M2.01A.** `docs/MILESTONE_1A.md` criterion A-5 (*"Zero imports of any embedding, vector-store, or LLM-evaluation library anywhere in the codebase"*) was binding through Milestone 1A and **remained binding throughout Milestone 1B**, as §3's exit condition states and as it continues to state — that sentence is a Milestone 1B fact and is unaltered.
>
> Discharging **M2-01** required importing an embedding library, which is the transition Milestone 2 was always going to make: `docs/architecture.md` §9 places *"Real `EmbeddingProvider` implementation (BGE-small-en-v1.5 default)"* at Milestone 2, and a real implementation cannot exist under a zero-import rule. **The lapse is confined to the embedding library, in `sample_rag/embedding.py`, from Sprint M2.01A.** The **vector-store** portion (**M2-02**) and the **LLM-evaluation** portion (**M2-07**, **M2-08**, **M3-06**) are untouched and still hold, and `tests/test_indexer.py` enforces both structurally by AST allowlist rather than by convention. No criterion was amended: `docs/MILESTONE_1A.md` is a completed Milestone 1 artifact and is not edited here.

> **Criterion A-5 — the vector-store-library portion lapsed at Sprint M2.01B.** The same transition, one capability later and equally narrow. Building **M2-02**'s persistence stage required importing a vector-store library, which `docs/architecture.md` §9 has placed at Milestone 2 since it named *"FAISS `VectorStore` implementation"*, and which the Repository Owner elected as FAISS at Sprint RO-06 / RO-07 (§6).
>
> **The lapse is confined to `faiss-cpu`, in `sample_rag/vector_index.py`, from Sprint M2.01B.** The package is the **CPU** build deliberately — `docs/roadmap.md` §7 places *"GPU optimization"* out of scope, and `sample_rag/embedding.py` already fixes embedding execution to CPU. The **LLM SDK** portion (**M2-06**) and the **LLM-evaluation** portion (**M2-07**, **M2-08**, **M3-06**) are untouched and still hold. `tests/test_vector_index.py` enforces the boundary structurally — an AST allowlist on the one authorized module and a glob check that no other `sample_rag/*.py` imports `faiss` — mirroring the two specifications `tests/test_indexer.py` carries for the embedding seam. No criterion was amended.
>
> **These are the repository's only two A-5 exceptions.** Each is one library, in one module, for one capability.
>
> **A third A-5 exception is AUTHORIZED but NOT YET TAKEN — Repository Owner ruling RO-13, §4.5 Decision 4.** The **LLM SDK** portion, which the M2.01B note above records as still holding, is the one **M2-06** lapses when it implements model-backed generation. The authorization keeps the same narrow shape as the two above — **one approved LLM/provider integration dependency, in one generation/provider module or the smallest equivalent boundary, for M2-06 only** — and authorizes **no** model router, agent framework, second SDK, evaluation framework, general-purpose orchestration library, or arbitrary HTTP access elsewhere in the repository. **RO-13 authorizes the category and scope and does NOT select the library**; M2-06 chooses it after repository inspection and records it in that sprint's evidence. **Until then this remains a two-exception repository**: no dependency was added by RO-13, `requirements.txt` is unchanged, and the sentence above is stated as the fact it still is. The **LLM-evaluation** portion (**M2-07**, **M2-08**, **M3-06**) is untouched by that authorization and still holds.
>
> **▶ Synchronized at the M2-06 discharge — the third exception was NOT taken, and the paragraph above is retained as written.** That paragraph was accurate when RO-13 issued it and **CP-3** governs: it records what RO-13 authorized and what RO-13 anticipated. **The anticipation is the part that did not happen.** Sprint **M2.06** performed the repository inspection RO-13 required and then **declined the dependency**, reaching the provider through the Python standard library — `urllib.request` and `json`, from `sample_rag/deepseek.py` — on the reasoning that the two exceptions already taken were taken because the **algorithm** was the dependency (a transformer checkpoint, an ANN index), which an HTTP POST carrying a JSON document is not. **`requirements.txt` is byte-identical**; no LLM SDK, HTTP client or provider abstraction was added; and `tests/test_model_generator.py::test_m206_no_dependency_was_added` makes taking it silently a visible failure. **The *"only two A-5 exceptions"* sentence above therefore stands unamended and remains literally true**, and the third exception **remains AUTHORIZED and UNTAKEN** — available to a later sprint on RO-13's original scope, without a further ruling and without this note reopening or widening it. The **LLM-evaluation** portion (**M2-07**, **M2-08**, **M3-06**) is untouched and still holds. Evidence: `docs/M2.06_Generation_Report.md` §2.1.

> **A fourth A-5 exception is AUTHORIZED but NOT YET TAKEN — Repository Owner ruling RO-16, §4.8 Decision 1.** The **LLM-evaluation** portion, which all four notes above record as still holding, is the one **M2-07** lapses when it activates Ragas — and it lapses **only for Ragas, only at `evaluation/ragas/`, and only for M2-07**. The authorization keeps the same narrow shape as the three above — **one library, in one boundary, for one capability** — and authorizes **no** other LLM-evaluation library, additional evaluation framework, model router, agent framework, second or general-purpose SDK, orchestration library, or arbitrary HTTP access elsewhere in the repository. **It grants no new embedding or vector-store exception**, and **no transitive or supporting dependency is authorized by it** however the selected Ragas version may require one. **RO-16 authorizes the library and the boundary and does NOT select the version or API**; M2-07 determines those after repository inspection and records them in that sprint's evidence. **RO-16 is not a reading of RO-13's third exception and does not reopen, widen or take it** — that one is scoped to *"M2-06 model-backed generation only"* and excludes *"evaluation frameworks"* by name, which is why a fourth was required. **Until M2-07 takes it this remains a two-exception repository**: no dependency was added by RO-16, `requirements.txt` is byte-identical, **no `import ragas` exists anywhere**, and the *"only two A-5 exceptions"* sentence above therefore **stands unamended and remains literally true**. **M2-08** and **M3-01** are untouched by this authorization, and the **LLM-evaluation** portion continues to hold for them and for **M3-06**'s remaining declarations (`deepeval`, `promptfoo`).

> **Four further Milestone 2B capabilities are recorded in §3, not here.** Repository Owner ruling **RO-06 — Milestone 1B Corpus Capability Reallocation** moved **1B-05**, **1B-06**, **1B-07** and **1B-12** to Milestone 2B. Their rows stay in §3 with their full history, per §1.3 (*a capability is never deleted*) and **CP-3**; duplicating them here would create two records of one capability. **They retain their `1B-` identifiers**, which record where a capability was first allocated, not where it is now — see §3.1.
>
> **Milestone 2's stage allocation (2A / 2B / 2C) is recorded in `docs/roadmap.md` §1.1** under ruling **RO-07**, because §1.2 bars this register from carrying sequence within a milestone. **M2-04 remains one capability**, staged-activated across 2A and 2B by Repository Owner clarification — it is not split, and no row below is divided.
>
> **M2-04's Milestone 2A activation is DELIVERED and evidenced — see §4.4.** Sprint **M2.04** implemented and validated two-route RRF over the semantic and lexical routes, and Repository Owner ruling **RO-12** records that completed stage without discharging the capability. **M2-04 itself remains OPEN**, because Milestone 2B's structured SQL / JobOps route and three-route RRF are outstanding. **No derivative identifier was created, no row was duplicated, and no capability was reallocated.** The count above is unaffected, and **M2-04 is not among the discharged capabilities it names**.

| id | Capability | Class | Blocking status | P3.7.2 class | Auth. | Originating repository authority | Rationale (full reasoning at) |
|---|---|---|---|---|---|---|---|
| **M2-01** | BGE embeddings — real `EmbeddingProvider` | Probabilistic Runtime | **Blocks 2** | Does not block Milestone 1A | — | `docs/MILESTONE_1A.md` Out of Scope; `docs/architecture.md` §5, §9; `docs/roadmap.md` §7 | ✅ **DISCHARGED at Sprint M2.01A (Real Embedding Foundation).** `sample_rag/embedding.py` implements `BGEEmbeddingProvider` over **`BAAI/bge-small-en-v1.5`**, pinned at revision **`5c38ec7c405ec4b44b94cc5a9bb96e735b38267a`**; `sample_rag/indexer.py` supplies it as the Index stage's default, so every committed chunk carries a real 384-component semantic embedding. **The contract was unchanged** — the `EmbeddingProvider` Protocol frozen at Sprint 1B.2 was not touched, which is what §4.1 R-1B-01/02 existed to make possible. The first probabilistic component; replaces 1B-01's stub behind an unchanged contract — §4.2. Evidence: `docs/M2.01A_Real_Embedding_Foundation_Report.md` |
| **M2-02** | Vector store implementation | Probabilistic Runtime | **Blocks 2** | Does not block Milestone 1A | **A6**, **RO-08**, **RO-10** | `docs/architecture.md` §5, §9; `docs/roadmap.md` §7 | ✅ **DISCHARGED at Sprint M2.01C (Semantic Query Foundation), by Repository Owner ruling RO-10** (§4.3). Replaces 1B-02's interface. Implementation elected — **FAISS**, §6. Acceptance was staged across two sprints by **RO-08** (§4.1), one capability and not split. ▶ **M2.01B** — `sample_rag/vector_index.py` builds, persists, loads and identity-validates a `faiss-cpu` `IndexFlatIP` artifact over the committed corpus, with the RO-08 Decision 1 fingerprint and the RO-08 Decision 3 signal set. ▶ **M2.01C** — `query(vector, top_k) -> list[str]` and the query-time nearest-neighbour behaviour, plus the RO-09 runtime lifecycle in `sample_rag/vector_runtime.py`: locate, exists-check, compatibility validation, stale detection, load, rebuild. **The `VectorStore` Protocol is untouched by both sprints.** **Discharge basis, per RO-10 Decision 1: `query(vector, top_k)` plus the whole-corpus rebuild lifecycle** — the scope at which the Milestone 2A capability is satisfied. **`upsert` is NOT implemented, NOT stubbed, and NOT required for this discharge**; it is **deferred** until a real caller requires incremental mutation, is owned by no register capability, and must be explicitly allocated if revisited. **M2.01C correctly recorded M2-02 as OPEN when it completed**; RO-10 is the subsequent authority that changes the status — §4.2 R-M2-02. Evidence: `docs/M2.01B_FAISS_VectorStore_Foundation_Report.md`; `docs/M2.01C_Semantic_Query_Foundation_Report.md` |
| **M2-03** | Real BM25 | Probabilistic Runtime | **Blocks 2** | Does not block Milestone 1A | — | `docs/MILESTONE_1A.md` Out of Scope; `sample_rag/retriever.py` docstring | ✅ **DISCHARGED at Sprint M2.03 (Real BM25 Lexical Retrieval Foundation).** `sample_rag/retriever.py` implements genuine Okapi BM25 — the **non-negative (Lucene)** IDF `idf(t) = ln(1 + (N − df + 0.5)/(df + 0.5))`, `tf` saturation at `k1 = 1.2`, length normalization at `b = 0.75` — replacing the plain distinct-term overlap this row names (§4.2). **The lexical seam is unchanged:** the same module, the same `retrieve(query, filters) -> RetrievalResult` contract, the same `tokenize` contract, the same three-level deterministic ordering (score → canonical rank → committed corpus position), and the same canonical `chunks[].id` identity the semantic route returns. **No lexical Protocol was introduced** — none exists in `docs/architecture.md` §5 or §7, and inventing one to mirror `EmbeddingProvider` and `VectorStore` would add an abstraction nothing varies behind. **No dependency was added**; BM25 is `math` and `collections`, so criterion A-5's two standing exceptions did not widen. **No RRF, hybrid ranking, score fusion or reranking** — **M2-04** and **M2-05** are untouched, and the two routes remain independently callable and unconnected. `k1`, `b` and the IDF variant are **engineering decisions, not Repository Owner authority**, recorded as such. Evidence: `docs/M2.03_Real_BM25_Lexical_Retrieval_Report.md`; `tests/test_lexical_bm25.py` |
| **M2-04** | Hybrid retrieval — SQL + BM25 + Vector → RRF | Probabilistic Runtime | **Blocks 2** | Does not block Milestone 1A | **RO-12** | `docs/MILESTONE_1A.md` Out of Scope; `docs/architecture.md` §10; `docs/roadmap.md` §4 | Fusion is meaningful only once all three routes return real results — §4.2. **OPEN — activation staged across Milestones 2A and 2B by the Repository Owner clarification recorded at §3.1**, under ruling **RO-07**; the completed stage is recorded by ruling **RO-12** (§4.4). ▶ **Milestone 2A activation DELIVERED at Sprint M2.04 (Two-Route Reciprocal Rank Fusion)**, not discharging: `sample_rag/fusion.py` fuses the semantic route (**M2-02**) and the lexical BM25 route (**M2-03**) by Reciprocal Rank Fusion over the union of their candidates — deterministic, with the P3.7.5 canonical ordering as tie-break — and `scripts/run_hybrid_retrieval.py` and `scripts/compare_retrieval_routes.py` exercise it against the committed corpus. **36 new specifications; 594/594 passing.** **The 2A activation covers the semantic and lexical routes only.** **The structured SQL / JobOps route is not implemented and three-route RRF does not exist**, so the capability is **not satisfied** — Milestone **2B** activates the structured branch and completes the approved architecture (`docs/architecture.md` §10; the structured branch is **1B-07**, reallocated to 2B by **RO-06**). **Discharged only when the approved three-route architecture is fused**, per RO-07's clarification that M2-04 is one capability and shall not be split. One capability, staged — not split: **no derivative identifier was created, this row is not divided, and no capability is discharged beyond the 2A activation** — §4.2. Stage evidence: `docs/M2.04_RRF_Fusion_Report.md` |
| **M2-05** | Reranking | Probabilistic Runtime | Non-blocking | Does not block Milestone 1A | — | `docs/MILESTONE_1A.md` Out of Scope; `docs/P3.7.1_…` §5.2 | Retrieval-quality optimization — §4.2 |
| **M2-06** | DeepSeek API generation | Probabilistic Runtime | **Blocks 2** | Does not block Milestone 1A | **RO-13**, **RO-14** | `docs/MILESTONE_1A.md` build item 5, Out of Scope; `docs/GENERATION_CONTRACT.md` §22 G-2, §24 | Replaces the quotation Generator with model-backed generation — §4.2. ✅ **DISCHARGED at Sprint M2.06 (Real Generation)**, on the authority already named in this row — **RO-13** (§4.5) and **RO-14** (§4.6) — see the discharge record at the end of this cell. **The former wording of this cell — *"behind the frozen `generate(query, retrieval)` signature"* — is superseded by Repository Owner ruling RO-13** (§4.5), which resolved the transition the stopped M2-06 sprint escalated: that signature was v1.0.0's, and **Generation Contract v2.0.0** (`docs/GENERATION_CONTRACT.md` §24) is now the authoritative contract for model-backed Milestone 2 generation. M2-06 implements **`Generator.generate(prompt: Prompt) -> GenerationResult`** — the **U-1** resolution — consuming the **M2-12** `Prompt` extended with the minimal ordered `provenance` of **U-2** (`chunk_id`, `document_id`, `character_start`, `character_end`, and no chunk text), which is what makes a conforming `SupportingEvidence` constructible without the Generator reaching back into the corpus. The `GenerationResult` artifact of §7/§8/§17 is **unchanged**, as are G-1…G-6, G-8, G-10, G-11 and G-12; **G-7**, **G-9**, **G-13/§18** and **G-14** transition per §24.3, permitting **exactly one sanctioned provider interaction** at the generation boundary and splitting **structural determinism** from **model-output reproducibility**, which is **not** guaranteed. The **third A-5 dependency exception** is authorized in scope but **the library is not selected** — M2-06 chooses it after repository inspection and records it in its own evidence (§4.5 Decision 4). **U-3 remains open**: `REACHABLE_STAGES` is not widened and no orchestration layer is authorized, so **how the runtime reaches this contract is M2-06's to determine and evidence**, not RO-13's. **M2-14 remains a separate open capability** — the `docs/architecture.md` §5 `Generator` row synchronization is authorized by §4.5 Decision 5 and is not performed by it. **Nothing is implemented at the time of this ruling**, and **M2-06 is not discharged by it**. ▶ **DISCHARGE RECORD — Sprint M2.06 (Real Generation).** `sample_rag/model_generator.py` implements **`ModelGenerator.generate(prompt: Prompt) -> GenerationResult`** — §24.2's method contract literally, at the **U-1** signature — consuming the **M2-12** `Prompt` extended to `Prompt(query, context, chunk_ids, provenance)` with the **U-2** four-field `ChunkProvenance` (`chunk_id`, `document_id`, `character_start`, `character_end`, carrying no chunk text and introducing no second identity system), and **never a `RetrievalResult`**, asserted over the module's referenced names rather than over its text. **`sample_rag/deepseek.py` is the sanctioned provider boundary** — the only module in `sample_rag/` holding a network primitive, an endpoint or a credential — so **G-14**'s *"exactly one sanctioned provider interaction"* is a structural property of the package, checkable by AST, rather than a promise about a function body. **The third A-5 dependency exception RO-13 authorized was NOT taken**: the provider is reached through `urllib.request` and `json`, `requirements.txt` is byte-identical, and the repository **remains a two-exception repository** — the §4 preamble's anticipation that M2-06 would lapse the **LLM SDK** portion of A-5 was therefore **not realized**, and that authorization remains available and untaken for a later sprint. **Real DeepSeek-backed generation was executed against the live service** from `scripts/run_generation.py` — two runs, `deepseek-v4-flash`, both accepted, parsed and mapped to a real `GenerationResult` with outcome `Answer`, five statements and five evidence spans each, the first carrying the repository's **first synthesized `answer_text`**. **`SupportingEvidence` is constructed from `Prompt.context` and `Prompt.provenance` *before* the provider is called**, by offset arithmetic rather than separator splitting, so no identifier the model produced enters the artifact and **G-6** holds exactly as it did under v1.0.0. **Provider failure is never a successful `GenerationResult`**: configuration, request/transport, malformed-response and malformed-`Prompt` conditions are distinguished by named exceptions (`ProviderConfigurationError`, `ProviderRequestError`, `ProviderResponseError`, `GenerationInputError`), none convertible into an answer, an abstention, an empty string or a partial artifact, a malformed `Prompt` is rejected before any call is spent, and no retry, backoff, cache or pool exists. **The §24.3 G-9 split was implemented as two separate claims** — structural determinism asserted, model-output reproducibility neither guaranteed nor asserted, and `ALTM-INDEX-1` recorded as a property to observe. **The frozen Milestone 1A path is preserved exactly**: `sample_rag/generator.py` is byte-identical, `scripts/cli.py` was **not** migrated and keeps its Milestone 1A chain and byte-identical reproducibility, `tests/test_generator.py` (**48**) and `tests/test_cli.py` (**27**) hold their `docs/P3.7.6_…` §3.2 frozen counts, and **no provider call exists in the deterministic pytest suite**. **`REACHABLE_STAGES` was not widened** and **no orchestration layer, runtime adapter, pipeline coordinator or `ContextEngine` was created** — the runtime seam is a fifth instance of the existing `scripts/run_*.py` pattern, so **U-3 is only *partly* resolved** and its diagnosability half remains open. **Discharge basis: the model-backed generation implementation boundary** — `Prompt → ModelGenerator.generate → provider → GenerationResult` — the scope at which this capability, as its originating authorities and Generation Contract **v2.0.0** state it, is satisfied. **The dual-path component identity this implementation produced is authorized by RO-14** (§4.6 Decision 1) and **recorded in `docs/architecture.md` by Sprint M2-14** (`docs/M2.14_Architecture_Synchronization_Report.md`): **`ModelGenerator` is the Milestone 2 model-backed generation component and `Generator` remains the frozen Milestone 1A deterministic / reference component**, which is what lets this row be read without ambiguity about which component carries which contract era. **M2-14 itself remains OPEN and is NOT discharged by this row**, and `docs/architecture.md` is not modified by it. **89 new specifications; 728/728 passing.** **Sprint M2.06 correctly recorded M2-06 as OPEN when it completed** and edited no register, contract, roadmap or architecture document; this row is the subsequent Repository Owner synchronization, under §1.3 as **RO-10 Decision 2** reads it. **No Repository Owner ruling was created by this discharge — there is no RO-15** — and **no derivative identifier exists**: no `M2-06a`, no `M2-06b`. **This discharge asserts NO generation-quality claim.** A successful live provider call establishes that **real generation exists**; it establishes nothing about **Faithfulness**, **Groundedness**, **Hallucination Rate**, **Answer Relevancy**, **Context Precision** or **Context Recall**, none of which is implemented, measured or claimed. §21's exclusion of the Layer 3/4 metric set stands, empirical evaluation remains **M2-07** / **M2-08** work, and **M2-07, M2-08 and M3-01 are not activated by this discharge.** **TWO FINDINGS REMAIN OPEN AND ARE NOT RESOLVED BY THIS DISCHARGE**, recorded here so that ✅ is not read as *"no known findings remain"*: **M2.06-F-1** — **DeepSeek provides no native citation or evidence-attribution mechanism**, so `SupportingEvidence` asserts only that these spans were assembled and this answer was produced with them present, and **no provider citation capability was fabricated**; and **M2.06-F-3** — **the Abstain path is unreachable through the current hybrid retrieval route**, because the semantic route returns `top_k` nearest neighbours regardless of distance and no relevance threshold exists, which is a **retrieval-side** property M2-06 was barred from tuning. **Both are non-blocking to this discharge**, because neither falls inside M2-06's stated acceptance boundary; **neither is marked fixed**; **neither allocates a capability, owes an implementation or creates an identifier**; and **RO-14 expressly declined to dispose of either** (§4.6). **Both remain recorded at `docs/M2.06_Generation_Report.md` §6.2 (F-1) and §7 (F-3), and are dispositioned as `M2.06-F-1` and `M2.06-F-3` in `docs/ENGINEERING_TRACEABILITY_REGISTER.md` §3.5.** **M2.06-F-2** and **M2.06-F-4** were already resolved by **RO-14** Decisions 5 and 1 and are recorded in that same §3.5 at Sprint RO-14. Evidence: `docs/M2.06_Generation_Report.md`; `docs/GENERATION_CONTRACT.md` §24 (**RO-13**) and §25 (**RO-14**); `docs/architecture.md` §5 and `docs/M2.14_Architecture_Synchronization_Report.md`; `tests/test_model_generator.py`; `tests/test_context_builder.py` |
| **M2-07** | Ragas activation — Layer 2 | Evaluation Tooling | **Blocks 2** | Does not block Milestone 1A | **RO-16**, **RO-17** | `docs/roadmap.md` §5; `docs/altm.md` §9, §12; `docs/MILESTONE_1A.md` Out of Scope | Measures the Retrieve stage; presupposes real retrieval to measure — §4.2. **OPEN.** ▶ **IMPLEMENTATION PATH RESCOPED BY RO-17 (§4.9) — read this row's *Capability* name as the original mechanism label, not as the current one.** The capability, its identifier **M2-07**, its class, its blocking status, its milestone (**2**) and its stage (**2A**) are **unchanged**; **only the implementation mechanism is rescoped**, and **no new `M2-xx` was created and nothing was renamed**. **M2-07 is now authorized to implement a native, repository-owned computation of Context Precision and Context Recall**, faithful to `docs/AI_Quality_Metrics_Reference.md`'s tool-independent definitions and to `docs/altm.md`'s Retrieve-stage framing — and **explicitly not** reducible to a simplified set-overlap calculation, which `docs/P3.3.3_…` §3 already records the `chunk_`-prefixed metrics as **not** being proxies for. **RO-17 independently authorizes the existing `sample_rag/deepseek.py` boundary as the native evaluation judge**, on conditional technical reuse without architectural widening — **not** on RO-16 D-3, whose condition named the Ragas API and therefore has no subject on this path — and **RO-14 D-2 remains binding: no provider call may enter the deterministic pytest suite.** **Ragas-the-library is NOT adopted for M2-07 under the current repository constitution** (§4.9 Decision 2), because every release carrying the required metric API hard-depends on **LangChain**, which **NA-07** records as *"Excluded, not deferred"*; **NA-07 is preserved unchanged** and **no fifth A-5 exception was created**. **RO-16 is not rewritten**: its fourth A-5 exception stands as issued and is simply **untaken**, exactly as RO-13's third is — nothing is installed, no `import ragas` exists, and `requirements.txt` is byte-identical. **RO-17 discharges nothing and grants no new embedding, vector-store, provider or orchestration authority.** ▼ *The RO-16 record below is retained as written and remains accurate as the account of what RO-16 authorized.* **Dependency and evaluation-judge authority supplied by Repository Owner ruling RO-16** (§4.8), after this sprint STOPped at the **A-5** boundary: Ragas is an **LLM-evaluation library**, A-5 bars importing one, and RO-13's third exception is scoped to M2-06 and excludes *"evaluation frameworks"* by name. RO-16 authorizes a **fourth A-5 exception — Ragas, at `evaluation/ragas/`, for M2-07 only** — and, as a **separate** decision, the **existing `sample_rag/deepseek.py` boundary as the evaluation judge, conditional on technical reuse without architectural widening**. **RO-16 selects no Ragas version or API**, authorizes **no transitive or supporting dependency**, and grants **no new embedding or vector-store exception** — each of those remains an M2-07 STOP if genuinely required. **The exception is AUTHORIZED and UNTAKEN**: nothing is installed, `requirements.txt` is byte-identical, no `import ragas` exists, and **RO-16 discharges nothing** — **M2-07 remains OPEN**, as do **M2-08**, **M2-10** and **M3-06**, and exercising Context Precision / Context Recall does **not** discharge **M2-10** (§4.8 Decision 8) |
| **M2-08** | DeepEval activation — Layer 3 | Evaluation Tooling | **Blocks 2** | Does not block Milestone 1A | — | `docs/roadmap.md` §5; `docs/altm.md` §9, §12 | Measures the Infer stage; meaningless against a verbatim-quotation generator — §4.2 |
| **M2-09** | Answer Relevancy (**Q-4**) | Metric | **Blocks 2** | Does not block Milestone 1A | — | `docs/GENERATION_CONTRACT.md` §23 Q-4; `docs/altm.md` §5 `ALTM-FINAL-ANSWER-1` | A Final Answer-stage metric owned by the Evaluation Engine; impact on 1A recorded as *"None"* — §4.2 R-M2-09 |
| **M2-10** | Context Precision / Context Recall | Metric | **Blocks 2** | *(not in §5)* | — | `docs/P3.3.3_…` §3; `docs/roadmap.md` §5 | Reserved for Ragas; the `chunk_`-prefixed metrics are explicitly not proxies for them — §4.2 |
| **M2-11** | Document Recall | Metric | Non-blocking | Does not block Milestone 1A | — | `docs/P3.3.5_…` §3 | Derivable post-enrichment and *"deliberately not implemented"* — §4.2 |
| **M2-12** | Assemble stage — Context Builder, `Prompt` artifact | Interface + Deterministic Runtime | **Blocks 2** | *(not in §5)* | — | `docs/GENERATION_CONTRACT.md` §21; `docs/architecture.md` §4, §5 | A prompt has no meaning until a model consumes one — §4.2 R-M2-12/13. ✅ **DISCHARGED at Sprint M2.12 (Context Builder / Prompt Foundation).** `sample_rag/context_builder.py` implements the `docs/architecture.md` §5 `Context Builder` row **at that row's interface exactly** — `ContextBuilder.assemble(chunks, query) -> Prompt` — with `resolve(chunk_ids) -> list[chunk record]` bridging **M2-04**'s `list[str]` of canonical chunk ids to §5's `chunks` argument, and `ContextAssemblyError` following the repository's existing named-error convention. **The `Prompt` artifact is `query`, `context`, `chunk_ids`** — a frozen dataclass, and an **engineering decision**, because no committed authority states a field, schema or serialization for the artifact `docs/architecture.md` §5/§7 and `docs/glossary.md` only name. **The pipeline seam is preserved:** the supplied RRF order is the emitted order (no sort, no key, no score read anywhere — AST-verified), the canonical `chunks[].id` identity is the one **M2-04** fuses on and **no second identity system was introduced**, duplicates are preserved rather than collapsed, a missing id **raises rather than dropping evidence silently** — the Assemble-stage failure `docs/architecture.md` §4 names — and an empty retrieval assembles to an empty-context `Prompt` **without making an abstention decision**, which `docs/GENERATION_CONTRACT.md` §9.3/§20.2 places in the `Generator`. **No retrieval, reranking or fusion logic** — the module imports `dataclasses` alone, so **M2-02**, **M2-03**, **M2-04** and **M2-05** are unreachable from it and untouched. **No context-window or token-budget heuristic**, none being derivable: a context window is a property of a generation model, `docs/architecture.md` §5 records *"Context-overflow handling under real token budgets"* as this row's **Future Evolution**, and no model is connected until **M2-06**. **No `Generator` invocation, and no end-to-end model-backed RAG path is established by this discharge.** **The Generation contract is unchanged in every part:** `docs/GENERATION_CONTRACT.md` remains frozen at v1.0.0, §17/§22 **G-2**'s `Generator.generate(query, retrieval: RetrievalResult)` is untouched, and no runtime path consumes a `Prompt` — **the Context Builder has no runtime consumer**, recorded as **M2.12-F-1** in `docs/ENGINEERING_TRACEABILITY_REGISTER.md` §3.5. **Discharge basis: the Context Builder / Assemble boundary** — the scope at which this capability, as its originating authorities state it, is satisfied. **The Generator input transition is NOT decided by this discharge**: §6.2 records `generate(prompt: Prompt)` as *"the Milestone 2 target, reached when a Context Builder exists"*, and which sprint performs it, whether the frozen contract is amended or superseded, whether `Prompt` must then carry further fields, and whether the Assemble stage becomes runtime-reachable are **handed to M2-06** (with the §5 `Generator` row owned by **M2-14**). **No field was added in anticipation of an answer**, none of those questions is owned by any register capability beyond M2-06, and each must be **explicitly allocated** if it requires more. **No Repository Owner ruling was created**: the discharge rests on the originating authorities already named in this row, as **M2-01**'s and **M2-03**'s do — no authority contradiction was found (`docs/M2.12_…` §1.6). **Sprint M2.12 correctly recorded M2-12 as OPEN when it completed** and edited no register, contract, roadmap or architecture document; this row is the subsequent Repository Owner synchronization, under §1.3 as RO-10 Decision 2 reads it. **45 new specifications; 639/639 passing.** Evidence: `docs/M2.12_Context_Builder_Report.md`; `tests/test_context_builder.py` |
| **M2-13** | Post-Process guardrail layer | Deterministic Runtime | Non-blocking | *(not in §5)* | — | `docs/GENERATION_CONTRACT.md` §21; `docs/altm.md` §4 | 1A exercises no guardrail; a guardrail constrains a model's output — §4.2 R-M2-12/13 |
| **M2-14** | `docs/architecture.md` §5 `Generator` row — Milestone 2 restatement, and **`Generator` / `ModelGenerator` component identity** | Governance | Non-blocking | Does not block Milestone 1A | **RO-14** | `docs/P3.7.2_…` §5.3; `docs/GENERATION_CONTRACT.md` §22, §24.2 | The row's *Future Evolution* column, revisited when DeepSeek lands. **Distinct from RO-03**, which is discharged — §4.2 R-M2-14. **Scope widened by Repository Owner ruling RO-14** (§4.6). **The original wording above is retained and is not deleted** — the *Future Evolution* column remains in scope; RO-14 **adds** to this capability rather than replacing it. M2-14 now additionally owns: **`Generator` / `ModelGenerator` component identity**; the **dual-path architectural disposition** RO-14 authorizes; the relationship between the Milestone 1A and Milestone 2 generation components; and the synchronization of `docs/architecture.md` with that authorized identity. **RO-14 supersedes RO-13 Decision 5 ONLY as to its singular-row synchronization target** — the instruction to synchronize one `Generator` row to `Generator.generate(prompt: Prompt) -> GenerationResult`, which the two concrete components Sprint M2.06 delivered make inapplicable as literal text. **Every other part of RO-13 stands, and RO-13 is not rewritten.** **RO-14 authorizes the synchronization and deliberately does not prescribe its text** — the minimum coherent set of documentation changes is M2-14's to determine (§4.6 Decision 4). **M2-14 remains OPEN and is NOT discharged by RO-14**; `docs/architecture.md` is unmodified by the ruling; blocking status is unchanged; and **no derivative identifier is created** — no `M2-14a`, no `M2-14b`, no `M2-14.1` |
| **M2-15** | Embedding benchmarking; retrieval-quality optimization; prompt optimization | Probabilistic Runtime | Non-blocking | Does not block Milestone 1A | — | `docs/MILESTONE_1A.md` Out of Scope; `docs/P3.7.1_…` §5.6 | Optimization of implementations — what the 1A Governing Principle excludes by definition — §4.2 |
| **M2-16** | Semi-structured sources (LinkedIn / Greenhouse / Lever JSON) | Corpus | Non-blocking | Does not block Milestone 1A | — | `docs/MILESTONE_1A.md` Out of Scope | Deferred *"until JobOps genuinely ingests these"* — an external precondition — §4.2 |
| **M2-17** | Chunk-size / overlap benchmarking | Deterministic Runtime | Non-blocking | *(not in §5)* | — | `docs/architecture.md` §5 | Requires a retrieval-quality signal sensitive enough to distinguish configurations — §4.2 R-M2-17 |
| **M2-18** | Execution Evidence / Traceability | Deterministic Runtime | Non-blocking | *(not in §5)* | **RO-15** | `docs/DEFERRED_ITEMS_REGISTER.md` §4.7 (**RO-15**); `docs/altm.md` §5 `ALTM-ASSEMBLE-1`, `ALTM-INDEX-1`; `docs/GENERATION_CONTRACT.md` §24.3 **G-9** | ✅ **DISCHARGED at Sprint M2.18 (Execution Evidence / Traceability)**, on the authority already named in this row — **RO-15** (§4.7) — see the discharge record at the end of this cell. **Allocated by Repository Owner ruling RO-15 (§4.7)**, which is this row's whole authority — it is a **subsequent Repository Owner allocation**, not one of the seventeen `docs/P3.7.3_…` affirmed (see the §4 preamble note and §10.5). Authorizes a **repository-native execution-evidence capability** that makes a completed pipeline execution inspectable and diagnostically traceable **after the process exits** — a **distinct execution-evidence envelope** observing the existing `Retrieve → Assemble → Infer` path, **not** a serialized `GenerationResult`, **not** an ALTM stage, and **not** production observability infrastructure. **Non-blocking for M2-07 and M2-08**, which obtain their inputs in-process and remain independently executable; trace presence improves the **diagnostic explainability** of their results, which is not the same as being **technically necessary to compute** them. **JSONL is the authorized v1 storage representation** — one execution, one record — and traces are **derived runtime artifacts** that **SHALL NOT be Git-tracked**. **No semantic similarity score is authorized**, and the `VectorStore` boundary (`sample_rag/vector_index.py`, `docs/architecture.md` §7) is **not widened** to expose one. **The trace schema is deliberately NOT frozen by RO-15**: the authorized content boundary is a capability boundary, and M2-18 determines the minimal concrete representation, module placement, wiring, runtime path and `.gitignore` mechanism from data **already available at existing boundaries** — no instrumentation may be invented to manufacture a field that does not exist. **Nothing was implemented at the time of this allocation** — `sample_rag/`, `scripts/`, `tests/`, `requirements.txt` and `.gitignore` were untouched by RO-15 — and **M2-18 was NOT discharged by RO-15**, which discharged nothing. Milestone **2C**, recorded at `docs/roadmap.md` §1.1 under **RO-07**'s stage-allocation split. **Discharges, reopens and modifies no other capability** — **M2-06** stays ✅ DISCHARGED with **M2.06-F-1** and **M2.06-F-3** open and unresolved, and **M2-07**, **M2-08** and **M3-01** stay OPEN, unactivated and unblocked — §4.7. ▶ **DISCHARGE RECORD — Sprint M2.18 (Execution Evidence / Traceability).** `scripts/execution_trace.py` implements the **execution-evidence envelope** RO-15 Decision 3 authorized — a cross-stage record **about** a completed execution, **not** a serialized `GenerationResult` — wired at the existing execution boundary in `scripts/run_generation.py`, which is where all three stages' evidence exists at once. **One completed execution produces exactly one JSONL record** (Decision 4): `json.dumps(trace, ensure_ascii=False) + "\n"`, one object per line, appended as executions occur. That form deliberately **is not** §13.2's `indent=2` form, which is Decision 4's concrete consequence — an indented object cannot be one JSONL line — and **`docs/GENERATION_CONTRACT.md` is byte-for-byte unchanged**, §13.2 and §13.3 remaining in force, unamended, for the `GenerationResult` they govern. **The recorded projection is the minimal one Decision 5 required**, verified against the runtime rather than copied from the authorized list: `query`; the **whole retrieval candidate union** with per-route `semantic_rank` and `lexical_rank`, `rrf_rank`, `rrf_score` and `source_legs`; `Prompt` provenance as §24.4's four fields; and `component`, `contract_version`, `provider`, `model`, `outcome`, `answer_text`, statement evidence references and observed latency. **`source_legs` is the route a candidate actually entered the fusion path through** — membership in the ranked list that route returned for that query — not the chunk's document, corpus or category; a route that supplied no candidate records **`null`, never `0`**. **`answer_text` is persisted for the specific reason Decision 6 gives**: §24.3's **G-9** split declines to guarantee model-output reproducibility, so it cannot be recovered by re-running. **Selected chunk ids, evidence offsets, `document_id`, `SupportingEvidence.text`, `GeneratedStatement.text` and `Prompt.context` are REFERENCED, not duplicated** — selected ids *are* the provenance `chunk_id` sequence, which is one structure rather than two and therefore cannot come to disagree with itself. **Every RO-15 exclusion holds and was verified structurally**: **no semantic similarity score** — the `VectorStore` boundary stayed CLOSED and `sample_rag/vector_index.py` is untouched, `query(vector, top_k) -> list[str]` returning ids and not distances, so semantic **rank** is recorded and semantic **score** does not exist to record; **no BM25 score**, which is available in `RetrievalResult.diagnostics` but is **not** in RO-15's authorized list — availability is not authorization; **no credential, token, `Authorization` header or provider secret**, which is structural rather than promised because the module imports only `json`, `pathlib` and `sample_rag.fusion` and references no `os`, `environ` or `getenv`; **no raw provider request or response payload**; and **no `GenerationResult.diagnostics`**. **Traces are derived runtime artifacts and are NOT Git-tracked** (Decision 8), excluded by `.gitignore` at `scripts/execution_trace/` — the RO-09 shape mirrored exactly, the **directory** ignored while `scripts/execution_trace.py` is committed source. **No dependency was added and `requirements.txt` is byte-identical.** **Four reference-integrity relationships raise rather than write** — the executed selection must be the leading order of the scored union, provenance must correspond to the assembled ids, every assembled chunk must appear among the candidates, and every cited chunk must appear in the assembled prompt — so a trace can never carry a dangling reference. **The frozen Milestone 1A path is preserved exactly** (Decision 3, RO-14 Decision 2): `sample_rag/` is byte-identical in every module, `scripts/cli.py` was not rewired and stays on `Generator`, `tests/test_generator.py` (**48**) and `tests/test_cli.py` (**27**) hold their `docs/P3.7.6_…` §3.2 frozen counts, and **no provider call exists in the deterministic pytest suite**. **`docs/altm.md` is unmodified, no ALTM stage was created, `REACHABLE_STAGES` was not widened, and no orchestration layer, runtime adapter, pipeline coordinator or `ContextEngine` exists** (Decision 9). **65 new specifications; 793/793 passing.** **Discharge basis: the execution-evidence boundary RO-15 allocated** — `Retrieve → Assemble → Infer → ExecutionTrace → one JSONL record` — the scope at which this capability, as RO-15 states it, is satisfied. **This discharge asserts NO evaluation, retrieval-quality or generation-quality claim.** A trace records what an execution did; it records nothing about whether the execution was correct, and **M2-07**, **M2-08** and **M3-01** are **not activated, not modified and not blocked** by it — Decision 2's *"technically necessary to calculate a metric" ≠ "valuable for explaining the metric"* stands exactly as ruled. **FOUR FINDINGS REMAIN OPEN AND ARE NOT RESOLVED BY THIS DISCHARGE**, recorded here so ✅ is not read as *"no known limitation remains"*: **M2.18-F-1** — **no temporal or execution-identity evidence is recorded**, because no wall-clock or identity convention exists anywhere in `sample_rag/` or `scripts/`, and RO-15 Decision 5 requires an item unavailable at an existing boundary to be *"omitted and reported, not engineered into existence"*; **M2.18-F-2** — **no concurrency, locking, rotation or retention behaviour exists**, all four being what Decision 4 *"deliberately NOT prescribed"* and left to this sprint; **M2.18-F-3** — **the frozen Milestone 1A path is not traced**, which Decision 3 **requires** rather than permits; and **M2.18-F-4** — **statement-to-evidence attribution is currently 1:1**, because `ModelGenerator._statements` emits one statement per assembled chunk under **M2.06-F-1**, and the trace records that linkage structurally rather than assuming it. **All four are non-blocking to this discharge**, because none falls outside the boundary RO-15 allocated and **none is a shortfall against it — F-1 and F-3 are compliance with RO-15, and F-2 is an exercise of a delegation it granted**; **none is marked fixed**; **none allocates a capability, owes an implementation or creates an identifier**; and **M2-18 resolves neither M2.06-F-1 nor M2.06-F-3** — it may make their behaviour more observable, and **observability is not repair** (§4.7 Decision 11). **All four are dispositioned as `M2.18-F-1` … `M2.18-F-4` in `docs/ENGINEERING_TRACEABILITY_REGISTER.md` §3.5.** **No Repository Owner ruling was created by this discharge — there is no RO-16** — and **no derivative identifier exists**: no `M2-18a`, no `M2-18b`. **RO-15 is unamended in every part**, as are RO-06 through RO-14, `docs/architecture.md`, `docs/roadmap.md`'s stage allocation, every contract, and `docs/M2.18_Execution_Evidence_Report.md`. Evidence: `docs/M2.18_Execution_Evidence_Report.md`; `scripts/execution_trace.py`; `scripts/run_generation.py`; `tests/test_execution_trace.py`; `.gitignore` |

### 4.1 Repository Owner ruling RO-08 — Sprint RO-08

Issued at Sprint **RO-08 (M2-02 VectorStore Contract and Milestone 2A Freshness Semantics)**, after Sprint **M2.01B** STOPped before implementation on three authority ambiguities it could not resolve without inventing repository authority. It is fixed repository authority. **This section records it; it does not interpret it.**

**On the section number.** This is the register's own §4.1. It is **not** the `§4.1` / `§4.2` that the *Rationale* column of the tables above cites — those point at `docs/P3.7.3_…` **Decision 4**, as §2.3 states. The same distinction already applies to §3.1 and is disclosed here rather than left to be inferred.

| Ruling | Title | Effect |
|---|---|---|
| **RO-08** | **M2-02 VectorStore Contract and Milestone 2A Freshness Semantics** | Authorizes an **index-local chunk-content fingerprint**; **stages M2-02's acceptance across Sprints M2.01B and M2.01C without splitting the capability**; and fixes the **Milestone 2A freshness/compatibility basis** for the resume-only corpus. Adds, removes and renames no capability, alters no `VectorStore` method or signature, and changes no milestone allocation |

#### Decision 1 — index-local chunk-content fingerprint

Sprint **M2.01B** is authorized to introduce a fingerprint over the ordered `(chunk_id, chunk_text)` sequence used to construct a persisted vector index. It exists to detect chunk-content drift that document identity, the document content hash, position-derived chunk ids and chunk count alone cannot detect.

| The fingerprint SHALL | The fingerprint SHALL NOT |
|---|---|
| Live in the persisted vector-index metadata | Modify `sample_rag/chunks.json` |
| Identify the exact chunk material used by that index | Modify the existing chunk contract |
| Participate in M2.01B stale-index validation | Redefine chunk ids |
| | Introduce corpus-level metadata into the chunk container |
| | Amend **ADR-0001 §2** |
| | Replace the repository's existing document identity model |

**It is an index-local identity mechanism and is not a new canonical corpus identity.** RO-08 authorizes the identity **concept and its scope only**. The algorithm, canonical serialization and storage layout are **M2.01B implementation concerns**: that sprint may select a reasonable deterministic hashing algorithm and serialization by following the nearest existing repository identity/hash conventions, without a further Repository Owner ruling, provided the choice stays inside the scope above. **M2.01B SHALL record the exact algorithm, serialization and input construction in its engineering evidence**, and SHALL NOT treat either as Repository Owner authority unless existing repository conventions separately establish it.

#### Decision 2 — M2-02 remains one capability, staged

**M2-02 remains exactly one repository capability.** No `M2-02a`, no `M2-02b`, no derivative identifier, and no duplicate row. Its **acceptance** is staged:

| Sprint | May establish | M2-02 status |
|---|---|---|
| **M2.01B** | Persistent FAISS-backed `VectorStore` foundation; persistence; loading; index identity; source/chunk mapping; compatibility validation; freshness / stale-index validation; deterministic rebuild semantics | **SHALL NOT discharge M2-02.** M2-02 remains **OPEN** after M2.01B |
| **M2.01C** | The remaining `VectorStore` protocol conformance required by existing repository authority — `query(vector, top_k) -> list[str]` and the associated query-time nearest-neighbour behaviour | **M2-02 may be discharged only when the complete repository-defined `VectorStore` contract is satisfied** |

**The existing `VectorStore` Protocol is unchanged.** RO-08 adds, removes, renames and alters no method, signature, return type or protocol requirement; `docs/architecture.md` §5 and §7 and `sample_rag/vector_store.py` stand exactly as written. The ruling permits **staged implementation of one capability**; it does not redefine M2-02 as two.

**M2-02's milestone allocation is unchanged.** It remains a Milestone 2A capability under **RO-07**. RO-08 governs *how* it is implemented, not *which* milestone owns it.

#### Decision 3 — Milestone 2A freshness semantics

For the **resume-only Milestone 2A corpus**, M2.01B stale-index detection is authorized to use, and is bounded to:

- document content hash
- ordered chunk-id set
- chunk count
- the index-local ordered `(chunk_id, chunk_text)` fingerprint of Decision 1
- embedding model identity
- embedding model revision
- embedding dimension
- relevant FAISS index configuration / type

**Timestamp-based freshness is not required for M2.01B**, and that sprint SHALL NOT introduce `created_at` as a deterministic artifact field, `documents[].indexed` as persisted state, last-indexed timestamps in the manifest, or timestamp-based manifest identity. **JobOps SQLite freshness semantics remain deferred to Milestone 2B**, where JobOps integration is allocated (**1B-06**, reallocated by **RO-06**).

This is a **scoped execution rule for the resume-only Milestone 2A implementation**. `docs/architecture.md` §9's broader JobOps-oriented freshness design is neither deleted nor redesigned by it.

#### What RO-08 does not amend

**R-01**, **R-02**, **RO-06**, **RO-07**, **ADR-0001 §2**, the chunk contract, the manifest contract, the `VectorStore` Protocol, and the approved Hybrid Retrieval architecture — all unchanged. RO-08 establishes only the authority needed for M2.01B to proceed without inventing missing identity or lifecycle semantics.

**Where the stage allocation lives.** As with RO-06 / RO-07, §1.2 bars this register from carrying sequence within a milestone. **The M2.01B / M2.01C staging of M2-02 within Milestone 2A is recorded in `docs/roadmap.md` §1.1**; this register continues to record only that M2-02 is one capability, allocated to Milestone 2, and still open.

### 4.2 Repository Owner ruling RO-09 — Sprint RO-09

Issued at Sprint **RO-09**, after Sprint **M2.01B** surfaced the artifact-policy question as finding **F-2** of `docs/M2.01B_FAISS_VectorStore_Foundation_Report.md` §15. It is fixed repository authority. **This section records it; it does not interpret it.**

**On the section number.** This is the register's own §4.2, in the same sense §4.1 is the register's own — **not** the `§4.2` the *Rationale* column of §4's table cites, which points at `docs/P3.7.3_…` **Decision 4** (§2.3). The distinction is the one §4.1 already discloses, restated here because §4.2 is the more heavily cited of the two.

**On the identifier.** **RO-09 is the next available unique Repository Owner ruling identifier**: RO-01 through RO-05 are in use in §7, RO-06 and RO-07 in §3.1, and RO-08 in §4.1. No identifier is reused and no historical ruling is renamed.

**On its standing relative to M2.01B.** This ruling was made **after** M2.01B completed and is not represented as having existed during it. M2.01B is committed, complete and historical; **CP-3** governs, and neither its report nor its evidence is rewritten by this section.

| Ruling | Title | Effect |
|---|---|---|
| **RO-09** | **FAISS index artifact policy** | The FAISS vector index produced by M2.01B is a **derived, rebuildable runtime/build artifact**; the **canonical corpus remains authoritative**; generated FAISS index artifacts and their generated metadata are **not Git source artifacts**; **Milestone 2A's M2.01C owns the concrete runtime artifact location and consumption lifecycle**. Creates no capability, discharges none, alters no contract and authorizes no retrieval |

#### The decision

The FAISS vector index produced by Sprint M2.01B is **derived, rebuildable runtime/build artifact state**. The canonical corpus remains the source of truth:

    Canonical corpus → chunks / corpus representation → embeddings
                     → FAISS index + metadata → retrieval

The FAISS index is therefore **not canonical source material**.

1. FAISS index artifacts are **derived**.
2. They are **rebuildable** from the canonical corpus and the established embedding/index configuration.
3. Generated FAISS index artifacts are **not repository source artifacts** and **SHALL NOT be committed to Git merely to make the index available**.
4. This includes generated `index.faiss`, generated vector-index directories, and generated runtime FAISS binaries.
5. `index_metadata.json` generated alongside the FAISS index is **likewise derived** runtime/build metadata.
6. The **canonical corpus remains authoritative**.
7. **M2.01C owns the concrete runtime artifact location and consumption lifecycle.**
8. M2.01C must determine how the runtime **locates** the derived index, **determines whether it exists**, **validates compatibility**, **determines whether it is stale**, **loads** it, **rebuilds** it when necessary, and **exposes** it to the query/retrieval path.
9. **This ruling prescribes no final runtime directory, filesystem path, CLI flag, environment variable, cache layout or API for M2.01C**, none being defined by existing repository authority.

#### What this ruling explicitly preserves

**M2-02 remains OPEN** and remains exactly one capability — this ruling **does not discharge it** and creates no derivative identifier. **Sprint M2.01B remains complete** and historical. **Sprint M2.01C remains the query/protocol completion stage**, and the only sprint that may discharge M2-02. **RO-08** stands unchanged in every part, including its Decision 3 freshness signal set. Canonical corpus identity, the chunk contract, the manifest contract, `sample_rag/chunks.json`, the `VectorStore` Protocol and M2-02's staged acceptance are all unchanged.

#### What this ruling explicitly does not do

**No retrieval implementation is authorized by this ruling** — not query semantics, top-k, similarity, ranking, BM25, RRF, or retrieval evaluation. **No new capability is created.** **No architecture redesign is performed.** **No timestamp or JobOps freshness mechanism is introduced** — no `created_at`, no persisted `documents[].indexed`, no last-indexed timestamp, no `generated_at`, no JobOps dependency, no timestamp-based manifest identity.

#### On `.gitignore`

**No `.gitignore` change is made by this ruling, and none is implied.** Item 3 states that generated FAISS artifacts are not committed; expressing that as an ignore rule requires naming a path, and item 9 reserves the concrete runtime location to M2.01C. An ignore rule written now would prescribe what this ruling declines to prescribe. Whether one is warranted is therefore a question for M2.01C, once the location exists.

### 4.3 Repository Owner ruling RO-10 — Sprint RO-10

Issued at Sprint **RO-10**, after Sprint **M2.01C** completed the query stage and reported **M2-02 OPEN** on unresolved `upsert` semantics (`docs/M2.01C_Semantic_Query_Foundation_Report.md` §16). It is fixed repository authority. **This section records it; it does not interpret it.**

**On the section number.** This is the register's own §4.3, in the same sense §4.1 and §4.2 are the register's own — **not** the `§4.3` the *Rationale* column of §5's table cites, which points at `docs/P3.7.3_…` **Decision 4** (§2.3). The distinction is the one §4.1 and §4.2 already disclose.

**On the identifier.** **RO-10 is the next available unique Repository Owner ruling identifier**: RO-01 through RO-05 are in use in §7, RO-06 and RO-07 in §3.1, RO-08 in §4.1 and RO-09 in §4.2. No identifier is reused and no historical ruling is renamed.

**On its standing relative to M2.01C.** This ruling was made **after** M2.01C completed and is not represented as having existed during it. **M2.01C recorded M2-02 as OPEN correctly**, on the authority available to it; RO-10 is the subsequent authority that changes the registered status. Neither M2.01B's nor M2.01C's report is rewritten by this section, and **CP-3** governs both.

| Ruling | Title | Effect |
|---|---|---|
| **RO-10** | **M2-02 Discharge Scope and Register-Editing Precedent** | Fixes the Milestone 2A **discharge scope** for M2-02 — `query(vector, top_k)` plus the whole-corpus rebuild lifecycle — and **discharges M2-02 as of Sprint M2.01C**; **defers `upsert`** without implementing, stubbing or allocating it; and fixes **M2.01C's stricter reading of §1.3** as the governing register-editing standard. Alters no `VectorStore` method or signature, amends neither RO-08 nor RO-09, authorizes no retrieval beyond the completed query stage, and changes no milestone allocation |

#### Decision 1 — `upsert` scope

**M2-02's `VectorStore` capability is satisfied at Milestone 2A by `query(vector, top_k) -> list[str]` plus the whole-corpus rebuild lifecycle established by Sprints M2.01B and M2.01C.**

The reasoning, recorded as the ruling states it:

- Every artifact in this repository's pipeline — the Knowledge Manifest, the Chunk Corpus and the FAISS index — is **rebuilt whole** from the canonical corpus.
- **Nothing in the current architecture performs incremental mutation.**
- **No caller in any milestone currently in scope** needs to upsert a single vector into a live index.
- The corpus-rebuild lifecycle authorized by **RO-09** already handles every current case — a **missing**, **stale** or **incompatible** index → **rebuild**.
- Sprint M2.01C's finding **F-1** establishes that the frozen `upsert` signature — `(chunk_id, vector)` — **cannot carry two of the identity signals RO-08 Decision 3 requires an index to track**: `chunk_fingerprint` and `document_hashes`.

Defining correct `upsert` semantics would therefore require **either** widening the Protocol / changing the architecture, **or** accepting an index whose identity could silently drift. **Neither is required by the current Milestone 2A capability.**

| `upsert` at Milestone 2A |
|---|
| **Deferred** |
| **NOT implemented** |
| **NOT stubbed** |
| **NOT required for M2-02 discharge** |

It **may be revisited only if a real caller requires incremental mutation**, most plausibly when a later milestone introduces genuinely incremental corpus updates. **No existing register capability owns that future work.** If revisited, it **must be explicitly allocated at that time** rather than inferred from this ruling.

**Consequence.** **M2-02 is DISCHARGED as of Sprint M2.01C**, on the basis of `query(vector, top_k)` **plus** the whole-corpus rebuild lifecycle. **The discharge does not imply implementation or acceptance of `upsert`.**

#### Decision 2 — register-editing precedent

Sprint **M2.01B** edited its own **M2-02** register row while discharging nothing. Sprint **M2.01C** read §1.3 more strictly:

> a sprint may synchronize the canonical register row only when the sprint **actually discharges** the registered capability **and** the sprint is **authorized** to perform that synchronization.

**M2.01C's stricter interpretation is the governing interpretation going forward.**

| | |
|---|---|
| A sprint that does **not** discharge a capability | **may propose** register language for Repository Owner review |
| The same sprint | **may NOT** itself edit the canonical capability row |
| M2.01B's historical edit | **Not reopened, not reversed** — **CP-3** applies |
| Future sprints | Follow the stricter **M2.01C** standard |

#### What RO-10 does not do

**The `VectorStore` Protocol, RO-08 and RO-09 are all unchanged**, in every part. RO-10 **does not implement `upsert`**; **authorizes no retrieval beyond the already completed query stage** — no BM25, no RRF, no hybrid retrieval, no generation; and **changes no milestone allocation.**

### 4.4 Repository Owner ruling RO-12 — Sprint RO-12

Issued at Sprint **RO-12**, after Sprint **M2.04** completed the **Milestone 2A activation** of **M2-04** and escalated the staged-recording question and finding **M2.04-F-1** for Repository Owner decision (`docs/M2.04_RRF_Fusion_Report.md` §12, §14). It is fixed repository authority. **This section records it; it does not interpret it.**

**On the section number.** This is the register's own §4.4, in the same sense §4.1, §4.2 and §4.3 are the register's own — **not** the `§4.x` the *Rationale* column of §4's table cites, which points at `docs/P3.7.3_…` **Decision 4** (§2.3). The distinction is the one §4.1, §4.2 and §4.3 already disclose.

**On the identifier.** **RO-12 is the next available unique Repository Owner ruling identifier**: RO-01 through RO-05 are in use in §7, RO-06 and RO-07 in §3.1, RO-08 in §4.1, RO-09 in §4.2 and RO-10 in §4.3. **`RO-11` is a sprint label, not a ruling** — Sprint RO-11 discharged **M2-03** and dispositioned **M2.03-F-1** under authority that already existed, and issued no numbered ruling. The identifier is not reclaimed as a ruling number, because reusing a label already in service is the collision §3.1 records the repository having had to resolve once. No identifier is reused and no historical ruling is renamed.

**On its standing relative to Sprint M2.04.** This ruling was made **after** M2.04 completed and is not represented as having existed during it. `docs/M2.04_RRF_Fusion_Report.md` **correctly recorded M2-04 as not discharged**, correctly left the staged-recording question to the Repository Owner, and correctly declined to edit a discharged sprint's specification; RO-12 is the subsequent authority. **That report is not rewritten by this section**, and **CP-3** governs it. The chronology is **M2.03 → RO-11 → M2.04 → RO-12**.

**On the authorization to synchronize.** Sprint M2.04 discharged no capability, so under **RO-10 Decision 2** it could not itself edit the canonical **M2-04** row — and did not. The Repository Owner supplied that authorization explicitly at Sprint RO-12, which is what permits the row synchronization recorded in §4. **RO-10 Decision 2 is applied here, not amended.**

| Ruling | Title | Effect |
|---|---|---|
| **RO-12** | **M2-04 Milestone 2A Activation Recording and M2.01C Artifact-Specification Correction** | Records M2-04's **Milestone 2A activation as DELIVERED and evidenced** while the capability **remains OPEN** for Milestone 2B; **corrects the M2.01C artifact specification** to verify Git non-tracking rather than filesystem absence; and directs the **M2.03-F-1** and **M2.04-F-1** dispositions to the findings register. **Discharges no capability**, creates, splits and renames no capability, amends **RO-06** through **RO-11** in no part, alters no contract, changes no milestone allocation, and authorizes no retrieval beyond the completed 2A activation |

#### Decision 1 — M2-04's Milestone 2A activation is recorded, not discharged

**M2-04 remains exactly one repository capability.** No `M2-04a`, no `M2-04b`, no derivative identifier, no duplicate row, and no new capability class. What is recorded is a **completed stage of an undivided capability**:

| M2-04 | |
|---|---|
| **Milestone 2A activation** — semantic + lexical two-route RRF | **DELIVERED / evidenced** |
| **Overall capability** | **OPEN** |
| **Discharged** | **No** — and nothing is discharged beyond the 2A activation |
| **Split** | **No** |

The 2A activation is **evidenced** by `docs/M2.04_RRF_Fusion_Report.md`: `sample_rag/fusion.py` implements and validates Reciprocal Rank Fusion over the semantic (**M2-02**) and lexical (**M2-03**) routes, at **594/594** passing specifications, of which 36 are new. **It covers those two routes only.** The Milestone **2B** structured SQL / JobOps route and the three-route fusion the approved Hybrid Retrieval architecture requires (`docs/architecture.md` §10) are **not implemented**, and cannot be while no JobOps corpus is connected — the structured branch is **1B-07**, reallocated to Milestone 2B by **RO-06**.

**RO-07 remains the governing authority** and is unchanged: M2-04 is one capability reaching its stages by *staged activation*, not by division.

**On the vocabulary, and on how far the RO-08 precedent carries.** The register's existing term for a completed stage of a capability that is not yet discharged is **DELIVERED**, from the **M2-02** row exactly as it stood between Sprints M2.01B and M2.01C — *"▶ **Persistence/foundation stage DELIVERED at Sprint M2.01B**, not discharging … so the capability is **not satisfied** … **Discharged only when** … One capability, staged — not split."* **RO-12 reuses that vocabulary and invents none**: there is no "partial discharge" here, and no stage-derived identifier.

**The precedent's shape differs, and the difference is recorded rather than smoothed over.** **RO-08** authorized staging **prospectively** — before Sprint M2.01B ran — and the completed stage was recorded afterwards, with discharge arriving later under a separate ruling (**RO-10**). **RO-12 records a completed stage retrospectively**, in the same event that affirms the capability remains open, which RO-08 did not do in one step. **The row vocabulary transfers exactly; the timing does not.** No new concept was introduced to bridge the difference.

#### Decision 2 — M2.01C artifact-specification correction

**RO-09 items 3–5** state that generated FAISS index artifacts and their generated metadata are **not Git source artifacts**. `tests/test_vector_query.py::test_m201c_the_runtime_artifact_is_not_a_repository_source_artifact` asserted **absence from the filesystem**, which is a different and stricter property than the policy it cites — and one that RO-09 item 6 and item 9 positively contradict, since the artifact is derived runtime state that a caller is expected to generate at the runtime location.

Sprint **M2.04** was the first repository path to execute `VectorIndexRuntime` at its default location and therefore the first to expose the defect. **The defect is in the M2.01C specification assertion, not in the M2-04 fusion implementation** — see `docs/ENGINEERING_TRACEABILITY_REGISTER.md` §3.5 **M2.04-F-1**.

| The correction SHALL | The correction SHALL NOT |
|---|---|
| Verify that nothing under `sample_rag/vector_index/` is **tracked by Git** | Change `VectorIndexRuntime`, `sample_rag/vector_index.py` or the FAISS lifecycle |
| Retain the specification's existing purpose, name and `.gitignore` half | Change `.gitignore` |
| Allow the runtime artifact to exist at `sample_rag/vector_index/` | Create a second artifact location |
| | Weaken the specification, or modify any other M2.01C or M2-04 specification |

**RO-09 is not amended in any part**, the artifact policy is unchanged, and `docs/M2.01C_Semantic_Query_Foundation_Report.md` is not rewritten. **The corrected assertion is a present correction and is not represented as having existed during Sprint M2.01C.**

#### Decision 3 — findings are dispositioned in the findings register, not here

**M2.03-F-1** — the **RO-11** revisit condition (*"revisit after Sprint M2-04 completes and its own retrieval-quality measurements are available"*) is now satisfied, and the finding is classified **CASE B — improved but insufficient / partially unresolved**. **M2.04-F-1** is resolved by Decision 2. Both dispositions are recorded in `docs/ENGINEERING_TRACEABILITY_REGISTER.md` §3.5, because §1.2 of this register places a defect with a disposition there. **Neither disposition allocates a capability, and neither triggers M2-15 or M2-17**, which remain independently scoped in §4.

#### What RO-12 does not do

**RO-06, RO-07, RO-08, RO-09, RO-10 and the Sprint RO-11 dispositions are all unchanged**, in every part, as are `docs/architecture.md`'s approved Hybrid Retrieval architecture, `docs/roadmap.md` §1.1's stage allocation, and every contract. RO-12 **discharges no capability** — M2-01, M2-02 and M2-03 remain the only discharged Milestone 2 capabilities; **allocates no capability**; **triggers neither M2-15 nor M2-17**; **defines no materiality threshold**, none existing in any committed authority; and **authorizes no retrieval work beyond the 2A activation already delivered** — no reranking, no generation, no tuning, no chunking revision, and no structured or three-route fusion.

### 4.5 Repository Owner ruling RO-13 — Sprint RO-13

Issued at Sprint **RO-13**, after the **M2-06** sprint STOPped before implementation on a contract conflict it could not resolve without inventing repository authority: real model-backed generation contradicts four normative guarantees of the frozen Generation Contract v1.0.0, and two repository authorities disagreed on M2-06's own scope. It is fixed repository authority. **This section records it; it does not interpret it.**

**On the section number.** This is the register's own §4.5, in the same sense §4.1 through §4.4 are the register's own — **not** the `§4.x` the *Rationale* column of §4's table cites, which points at `docs/P3.7.3_…` **Decision 4** (§2.3). The distinction is the one §4.1 through §4.4 already disclose.

**On the identifier.** **RO-13 is the next available unique Repository Owner ruling identifier**: RO-01 through RO-05 are in use in §7, RO-06 and RO-07 in §3.1, RO-08 in §4.1, RO-09 in §4.2, RO-10 in §4.3 and RO-12 in §4.4. **`RO-11` remains a sprint label, not a ruling**, exactly as §4.4 records it. No identifier is reused and no historical ruling is renamed.

**On its standing relative to the stopped M2-06 sprint.** That sprint **made no repository change** — it correctly stopped at the contract boundary, implemented nothing, and invented no authority. RO-13 is the subsequent authority that resolves what it could not. **No sprint report is rewritten**, and **CP-3** governs. The chronology is **M2.12 → M2-12 discharge → M2-06 STOP → RO-13 → M2-06 implementation**.

**On the authorization to synchronize the M2-06 row.** Under **RO-10 Decision 2** a sprint that discharges nothing may not itself edit a canonical capability row. **RO-13 discharges nothing either**; the Repository Owner supplied that authorization explicitly at this sprint, which is what permits the **M2-06** row synchronization recorded in §4. **RO-10 Decision 2 is applied here, not amended.**

| Ruling | Title | Effect |
|---|---|---|
| **RO-13** | **M2-06 Generation Contract Transition** | Authorizes **Generation Contract v2.0.0** for model-backed Milestone 2 generation, recorded at `docs/GENERATION_CONTRACT.md` §24; resolves the **G-7**, **G-9**, **G-13/§18** and **G-14** guarantee transitions; resolves **U-1** (`generate(prompt: Prompt)`) and **U-2** (minimal `Prompt` provenance); authorizes the **third A-5 dependency exception**, scoped but unselected; and authorizes the future **M2-14** architecture synchronization. **Discharges no capability**, creates, splits and renames no capability, amends **RO-06** through **RO-12** in no part, reopens **M2-12** in no part, changes no milestone allocation, and implements nothing |

#### Decision 1 — Generation Contract v2.0.0 is authorized

**v2.0.0 is the authoritative contract for model-backed Milestone 2 generation. v1.0.0 remains the historical Milestone 1A contract**, unwithdrawn and uncorrected — every guarantee it states was true of the deterministic quotation Generator it described.

| Contract | Authoritative for |
|---|---|
| **v1.0.0** — `docs/GENERATION_CONTRACT.md` §1–§23 | The historical Milestone 1A deterministic quotation-generator contract |
| **v2.0.0** — `docs/GENERATION_CONTRACT.md` §24 | Model-backed Milestone 2 generation |

**On the materialization mechanism, and that none was invented.** The repository already has one: `docs/DOCUMENT_CONTRACT.md` §8.9 (**Erratum E-1**) and §8.10 (**Erratum E-2**, issued under Repository Owner ruling **R-02**) record contract change as an **adjacent, non-destructive section within the same contract document**, each declaring the prior range *"byte-for-byte unchanged"* and each stating what it changes, what it does not change, and what it does not do. `docs/DATA_QUALITY_VALIDATION_PLAN.md` names that form the repository's *"established way of recording a correction rather than silently applying one"*, and `docs/CHUNK_CONTRACT.md` already reserves revision for when *"Milestone 2 formally supersedes this contract."* **v2.0.0 is recorded through that existing mechanism and no other.** **No `contracts/` directory, versioning hierarchy, parallel contract system, second authoritative location, generated-contract mechanism, replacement documentation architecture, new authority layer or new storage convention was created.**

**The v1.0.0 body is byte-for-byte unchanged** — §24 is appended, and the header carries an added adjacent supersession note that edits no existing line.

#### Decision 2 — the four guarantee transitions

Recorded in full at `docs/GENERATION_CONTRACT.md` §24.3. **G-1, G-2, G-3, G-4, G-5, G-6, G-8, G-10, G-11 and G-12 are unchanged in every part.**

| | v1.0.0 | v2.0.0 |
|---|---|---|
| **G-14** | *"no filesystem I/O, no network I/O"* | **Exactly one sanctioned provider interaction** at the generation boundary. Filesystem I/O stays barred; **no** general filesystem, corpus, retrieval, indexing, arbitrary-network, tool, memory or model-routing access is granted |
| **G-9** | One determinism guarantee | **Split.** **Structural determinism** — prompt structure and provenance, request construction, request shape, response parsing, schema mapping, error classification, and every `GenerationResult` field other than answer content — **SHALL** hold. **Model output reproducibility** of `answer_text` is **NOT guaranteed**, and **request reproducibility SHALL NOT be reported as model-output determinism** |
| **G-7** | `answer_text` derivable *"by verbatim quotation and deterministic template assembly alone"* | **Narrowed, not deleted.** `answer_text` **MAY be synthesized**; **`SupportingEvidence` SHALL remain grounded in the assembled `Prompt` context and provenance**, and the Generator **SHALL NOT** obtain evidence from an independent retrieval or corpus path |
| **G-13 / §18** | Permitted input: `query` + `RetrievalResult` | Permitted input: a **`Prompt`**, plus G-14's single provider interaction. **§18's barred list carries forward unchanged and in full** |

**RO-13 asserts no faithfulness claim.** Structural evidence provenance, model answer synthesis, and empirical Faithfulness / Groundedness are three distinct things; the third is **later evaluation work**, is neither established nor claimed here, and §21's exclusion of the Layer 3/4 metric set stands. **`ALTM-INDEX-1` becomes reachable** under v2.0.0 and is a property to be observed, not asserted away.

#### Decision 3 — U-1 and U-2 resolved; U-3 remains open

**U-1 — RESOLVED.** The authoritative v2 Generator input is `generate(prompt: Prompt) -> GenerationResult` — `docs/architecture.md` §5's original signature and the *"Milestone 2 target"* §6.2 recorded, whose stated condition (*"reached when a Context Builder exists"*) **M2-12** satisfied. The Generator **SHALL NOT** consume a `RetrievalResult` under v2, and **exactly one authoritative generation input path exists**.

**U-2 — RESOLVED, and the extension is required rather than speculative.** `SupportingEvidence` (§8.3) needs `chunk_id`, `document_id`, `character_start`, `character_end`; `Prompt.chunk_ids` carries only the first, and **G-13 bars the Generator from reaching back into the corpus for the rest**. The semantic `Prompt` becomes `Prompt(query, context, chunk_ids, provenance)`, where `provenance` is an ordered per-chunk structure carrying **exactly** `chunk_id`, `document_id`, `character_start`, `character_end` — ordered to match assembled chunk order, **carrying no chunk text** (`context` already holds it), and **introducing no second identity system**. Every other candidate field is barred absent separate governance, and **no new `GenerationResult` field is authorized** — §15's omissions, `generation_time_ms` included, stand.

**U-3 — REMAINS OPEN.** `REACHABLE_STAGES` is **not** widened; no orchestration layer, runtime adapter, pipeline coordinator or `ContextEngine` is authorized; `scripts/cli.py` is unchanged. **RO-13 defines what the Generator contract is; M2-06 determines how the runtime reaches it.** §23's Q-3 reasoning — widening is *"a deliberate scope decision, not a side effect of implementing a component"* — is unchanged, and **U-3 is not converted into a capability.**

#### Decision 4 — the third A-5 exception, scoped but not selected

Criterion **A-5** (*"Zero imports of any embedding, vector-store, or LLM-evaluation library anywhere in the codebase"*) has two recorded exceptions — `sentence-transformers` at Sprint M2.01A and `faiss-cpu` at Sprint M2.01B (§4 preamble). **RO-13 authorizes a third**, on the same narrow shape: **one approved LLM/provider integration dependency, in one generation/provider module or the smallest equivalent boundary, for M2-06 model-backed generation only.**

**Not authorized:** multiple model SDKs, model routers, agent frameworks, arbitrary HTTP access elsewhere in the repository, evaluation frameworks, and general-purpose orchestration libraries.

**RO-13 authorizes the category and scope; it does not select the library.** The concrete dependency is **M2-06's**, chosen after repository inspection and recorded in that sprint's evidence, exactly as **RO-08 Decision 1** left the fingerprint algorithm to M2.01B. **The exception is authorized but not yet taken** — no dependency is added by this ruling, and the two existing exceptions are unchanged.

#### Decision 5 — M2-14 architecture synchronization authorized, not performed

`docs/architecture.md` §5's `Generator` row records the v1.0.0 signature and its dependency *Retriever*. **RO-13 authorizes** a future synchronization of that row to `Generator.generate(prompt: Prompt) -> GenerationResult`, in the manner P3.7.4 amended it under authorization **A5** and `docs/MILESTONE_1A.md` build item 4 amended the `Retriever` row before it.

**No architecture document is edited by this ruling**, no architecture history is rewritten, and **M2-14 is NOT discharged** — it remains a separate open capability, and §20.3's bar on implementing sprints amending §5 is unchanged. **`docs/architecture.md` §8's sequence-diagram divergence (M2.12-F-3) is not resolved here** and is not made part of M2-06's scope.

#### What RO-13 does not do

**RO-06 through RO-12 are unchanged in every part**, as are `docs/roadmap.md` §1.1's stage allocation, `docs/architecture.md`, every retrieval contract, and the `VectorStore`, `EmbeddingProvider` and `Chunk` contracts. **It implements nothing** — `sample_rag/generator.py`, `sample_rag/context_builder.py`, `tests/test_generator.py` and `scripts/cli.py` are untouched, no dependency is added, and no provider call was made. **It discharges no capability** — **M2-06** and **M2-14** both remain **OPEN**, and **M2-12 is not reopened, its discharge row is not edited, and `docs/M2.12_Context_Builder_Report.md` is unchanged.** It **creates no capability and no derivative identifier** — no `M2-06a`, no `M2-06b`. It **activates no evaluation tooling**, **changes no retrieval**, **triggers neither M2-15 nor M2-17**, and introduces **no context-window policy, context compression, token budget, memory, agent runtime, tool calling or model routing.**

### 4.6 Repository Owner ruling RO-14 — Sprint RO-14

Issued at Sprint **RO-14**, after the **M2-14** sprint STOPped without making any repository modification: it established from the repository itself that two concrete generation components had come to exist, that no committed authority decided whether they are one architectural component or two, and that selecting between the alternatives required a Repository Owner decision rather than an implementing agent's inference. It is fixed repository authority. **This section records it; it does not interpret it.**

**On the section number and the identifier.** This is the register's own §4.6, in the same sense §4.1 through §4.5 are — not the `§4.x` the *Rationale* column of §4's table cites. **RO-14 is the next available unique Repository Owner ruling identifier**: RO-01 through RO-05 are in use in §7, RO-06 and RO-07 in §3.1, RO-08 in §4.1, RO-09 in §4.2, RO-10 in §4.3, RO-12 in §4.4 and RO-13 in §4.5. **`RO-11` remains a sprint label, not a ruling.** No identifier is reused, no historical ruling is renamed, and **no `RO-15` is created.**

**On its standing relative to the M2-14 STOP.** That sprint **made no repository change** — it modified no file, created no report, invented no authority and correctly stopped at the authority boundary. **There is therefore no committed M2-14 STOP document, and none is cited below as though there were.** Every fact this ruling rests on is verifiable at commit `b6579a9` by direct inspection of the files named. **No sprint report is rewritten**, and **CP-3** governs. The chronology is **M2.12 → M2-12 discharge → M2-06 STOP → RO-13 → M2-06 implementation → M2-14 STOP (no change) → RO-14**.

**On the authorization to synchronize the M2-14 row.** Under **RO-10 Decision 2** a sprint that discharges nothing may not itself edit a canonical capability row. **RO-14 discharges nothing either**; the Repository Owner supplied that authorization explicitly at this sprint, which is what permits the **M2-14** row synchronization recorded in §4. **RO-10 Decision 2 is applied here, not amended**, exactly as RO-12 and RO-13 applied it before.

| Ruling | Title | Effect |
|---|---|---|
| **RO-14** | **Generator / ModelGenerator Architectural Identity** | Authorizes the **dual-path generation architecture**: **`Generator`** is the frozen Milestone 1A deterministic/reference generation component and **`ModelGenerator`** is the Milestone 2 model-backed generation component, and **both are authorized architectural components**. Preserves the `docs/P3.7.6_…` Milestone 1A frozen baseline and keeps `scripts/cli.py` on the Milestone 1A path. **Supersedes RO-13 Decision 5 only as to its singular-row architectural synchronization target.** Widens **M2-14**'s scope to include component identity and authorizes — without prescribing — the subsequent `docs/architecture.md` synchronization. Resolves **M2.06-F-2** (`answer_text` under v2.0.0) and clarifies **G-5** for the v2 boundary, both recorded adjacently at `docs/GENERATION_CONTRACT.md` **§25**. **Discharges no capability**, creates, splits and renames no capability, creates no milestone, amends **RO-06** through **RO-13** in no other part, reopens **M2-12** in no part, and **implements nothing** |

#### Decision 1 — the dual-path generation architecture is authorized

**The repository intentionally contains two generation components across two contract eras, and both are authorized architectural components.**

| Component | Architectural identity | Interface | Contract era | Execution surface |
|---|---|---|---|---|
| **`Generator`** (`sample_rag/generator.py`) | The **frozen Milestone 1A deterministic / reference** generation component | `generate(query: str, retrieval: RetrievalResult) -> GenerationResult` | **v1.0.0** — `docs/GENERATION_CONTRACT.md` §1–§23 | `scripts/cli.py` |
| **`ModelGenerator`** (`sample_rag/model_generator.py`) | The **Milestone 2 model-backed** generation component | `generate(prompt: Prompt) -> GenerationResult` | **v2.0.0** — `docs/GENERATION_CONTRACT.md` §24 | `scripts/run_generation.py` |

**They are distinct architectural components, not two implementations of one current interface.** Their signatures differ, so neither is substitutable for the other at a call site.

**Grounded in repository authority, not in preference.** §24.1 already holds two contracts live at once and states that v1.0.0 *"is not withdrawn, corrected, or falsified"* and *"remains the accurate, frozen record"* of the Milestone 1A quotation Generator — a component that still exists and is still executed. `docs/P3.7.6_…` §3 requires subsequent milestones to *"**extend**"* and not *"**redefine**"* that baseline, and §3.2 and §4 freeze the specifications and the byte-identical CLI reproducibility that depend on the v1.0.0 component continuing to exist. Dual path is the arrangement under which both of those authorities remain true simultaneously.

**They may share the artifact types the implementation already shares.** `sample_rag/model_generator.py` imports `GenerationResult`, `GeneratedStatement`, `SupportingEvidence` and the outcome literals from `sample_rag/generator.py` rather than redefining them. **That sharing is authorized and is not a component merger**: §24.3 keeps §7's data model, §8's field definitions and §9's outcome domain unchanged across the transition, so one artifact definition serving both components is the contract's own position. A second copy would be the defect §20.4 exists to avoid.

**Two things are disclosed rather than glossed.** First, **the interface-first principle (`docs/architecture.md` §2, §10) is NOT retroactively satisfied between these two components**, and RO-14 does not claim that it is: the principle's *"Implementations are swapped in later without changing calling code"* describes one component's implementations being exchanged, which is not what these two are. Second, `docs/architecture.md` §10 requires that a locked decision be revisited only by *"a deliberate redesign discussion, not an incidental change made while implementing a later milestone."* **RO-14 is that deliberate decision**, taken outside any implementing sprint and after the implementing sprint declined to take it. How — and whether — §2 and §10 need a corresponding note is a documentation question belonging to **M2-14** under Decision 4, and **RO-14 does not prescribe it.**

#### Decision 2 — the Milestone 1A frozen baseline is preserved

**`docs/P3.7.6_Milestone_1A_Closure_and_Frozen_Baseline.md` is preserved in full and is not edited by this ruling.** Specifically:

- **`scripts/cli.py` remains on `Generator`** and is not migrated.
- **`tests/test_generator.py` remains frozen at 48 specifications** and `tests/test_cli.py` **at 27**, as §3.2 froze them.
- **§4's byte-identical answer and abstain reproducibility remains valid Milestone 1A acceptance evidence.**
- **The deterministic / reference path is not retired, renamed, relocated or superseded.**
- **No provider call is introduced into the deterministic pytest suite**, and none may be.
- **No Milestone 1A contract is redefined**, silently or otherwise.

**The existence of `ModelGenerator` does not invalidate the Milestone 1A baseline.** It is an extension of the repository, which is what §3 requires of a subsequent milestone.

#### Decision 3 — RO-13 Decision 5, disposed of precisely

**RO-13 Decision 5 was valid when issued.** Against the authority and repository state known at Sprint RO-13 — where exactly one generation component existed and nothing consumed a `Prompt` — synchronizing the single `docs/architecture.md` §5 `Generator` row to `Generator.generate(prompt: Prompt) -> GenerationResult` was the correct and sufficient instruction.

**Sprint M2.06 subsequently produced two concrete generation components**, and the class implementing the v2 signature is named `ModelGenerator`. The singular-row target therefore **cannot be applied literally**: written as authorized, the row would assert a signature that the only class named `Generator` in the repository does not have.

| | |
|---|---|
| **Superseded** | RO-13 **Decision 5**, and **only** its singular-row architectural synchronization target |
| **Not superseded** | RO-13 **Decisions 1, 2, 3 and 4** — Generation Contract v2.0.0, the four guarantee transitions, the U-1 / U-2 resolutions and the open U-3, and the third A-5 dependency exception — all of which **remain in force in every part** |
| **Not done** | **RO-13 is not withdrawn**, is not invalidated as a whole, and **is not rewritten**. §4.5 stands as the historical record of what was ruled and when |

The relationship, stated exactly:

```text
RO-13 D-5
    ↓  superseded ONLY as to its singular-row architectural synchronization target
RO-14
    ↓
dual-component architecture authorized
```

**No new Generation Contract version is created by this** — no v2.1.0, no v3.0.0. §24.2's `Generator.generate(prompt: Prompt) -> GenerationResult` remains the v2.0.0 **method contract**, and it is implemented literally by `ModelGenerator.generate`. What RO-14 changes is which *component* the architecture document records as carrying it, not what the contract requires.

#### Decision 4 — M2-14 is authorized to synchronize the architecture, and its text is not prescribed

**M2-14's scope is widened** (row synchronized in §4) to include `Generator` / `ModelGenerator` component identity, the dual-path disposition, the M1A ↔ M2 component relationship, and the synchronization of `docs/architecture.md` with that identity. **M2-14 remains one capability** — no `M2-14a`, no `M2-14b`, no `M2-14.1`, and no new capability or milestone is created.

**M2-14 is authorized to perform the minimum documentation synchronization necessary** for `docs/architecture.md` to accurately represent:

1. `Generator` as the frozen Milestone 1A deterministic / reference component;
2. `ModelGenerator` as the Milestone 2 model-backed component;
3. their distinct contract eras — v1.0.0 and v2.0.0;
4. their distinct execution paths — `scripts/cli.py` and `scripts/run_generation.py`;
5. the preservation of the Milestone 1A CLI path.

**RO-14 deliberately does not prescribe how.** It fixes no line count, table layout, §5 wording, row ordering, diagram change or *Future Evolution* prose. **Determining the minimum coherent set of document changes is M2-14's responsibility**, and §20.3's bar on *implementing* sprints amending §5 is unchanged — M2-14 is a Governance capability performing an authorized synchronization, which is the same standing P3.7.4 had under authorization **A5**.

The governing separation:

```text
RO-14   — WHAT is authorized
   ↓
M2-14   — HOW docs/architecture.md records it
```

**`docs/architecture.md` is NOT modified by this ruling**, no architecture history is rewritten, and **M2-14 is NOT discharged.** `docs/architecture.md` §8's sequence-diagram divergence (**M2.12-F-3**) and the §5 `Context Builder` row's residual divergence are **not resolved here** and are not made part of RO-14's scope; whether M2-14 encounters them is M2-14's to report.

#### Decision 5 — M2.06-F-2 resolved: `answer_text` under v2.0.0

**The finding.** `docs/GENERATION_CONTRACT.md` §24.3 states that *"§8's field definitions"* are unchanged, while §8.1 defines `answer_text` on the Answer path as *"assembled from the `statements` below and contains no content not present in them."* The same §24.3 states, specifically and by name, that under v2.0.0 `answer_text` *"**MAY be synthesized by the model**"* and that *"the quotation-only derivation requirement no longer applies to it."* Surfaced as **F-2** of `docs/M2.06_Generation_Report.md` §6.2 and reported there *"for confirmation"*, not resolved.

**Repository Owner interpretation — the specific G-7 transition governs.**

- Under **v2.0.0**, `answer_text` **MAY be model-synthesized**. §16 is where guarantees are normative, and §24.3 names **G-7** as one of the four guarantees that transition; §8.1's sentence is the descriptive restatement of the guarantee, and it does not survive the guarantee's own transition.
- **The structural field is unchanged.** `answer_text` keeps its name, its type, its required status, its non-emptiness (**G-3**) and its position in §7's field order and §13.2's serialization. **No field is added, removed or retyped.**
- **The v1.0.0 quotation-only behaviour remains historical and remains accurate** of the Milestone 1A component that still exhibits it. §8.1 is **not edited**.
- **`GeneratedStatement.text` is unaffected** and remains a verbatim quotation of its own span under both eras.
- **`SupportingEvidence` remains grounded in the assembled `Prompt` context and provenance**, and in nothing else — the surviving half of G-7, unchanged.
- **No faithfulness, groundedness, hallucination-absence or answer-relevancy guarantee is created by this decision.** §24.3's three-way distinction stands and §21's exclusion of the Layer 3/4 metric set stands; empirical evaluation remains **M2-07** / **M2-08** work.

**Recorded at `docs/GENERATION_CONTRACT.md` §25.1**, through the repository's established adjacent-erratum mechanism — `docs/DOCUMENT_CONTRACT.md` §8.9 (**E-1**), whose own purpose is a contract that *"admits two readings of the same requirement"* and which *"resolves that, without editing either statement."* **§1 through §24 are byte-for-byte unchanged**, the contract version metadata is unchanged, and **no new contract version is created.**

#### Decision 6 — G-5 clarified for the v2.0.0 boundary

**The observation.** §24.3 lists **G-5** among the guarantees *"unchanged in every part"*, and G-5 (§16) reads: *"Every `SupportingEvidence` SHALL carry a `chunk_id` present in the consumed `RetrievalResult.chunks`, and a `document_id` equal to that chunk's `document_id`."* But §24.3's **G-13 / §18** transition makes a `Prompt` — not a `RetrievalResult` — the v2 Generator's permitted input, and §24.2 states the v2 Generator *"SHALL NOT consume a `RetrievalResult`."* The literal wording therefore names an artifact the v2 component is barred from consuming. **This was surfaced during the M2-14 re-anchoring, which produced no repository modification; RO-14 is its first repository record.**

**Repository Owner interpretation — the intent is binding, the input citation is historical.**

- **G-5's evidence-identity intent remains binding under v2.0.0**: every `SupportingEvidence` carries a `chunk_id` that resolves to a real committed corpus chunk, and a `document_id` equal to that chunk's own.
- **The `RetrievalResult.chunks` phrase is a v1.0.0 input citation**, accurate for the component and the era it was written for, and **superseded as a statement of the v2.0.0 Generator boundary** — the same disposition `docs/DOCUMENT_CONTRACT.md` §8.10 (**E-2**) applies to a citation whose cited contract has since changed: *"Each remains accurate as the observation it was when recorded, and none is edited."*
- **Under v2.0.0 the requirement is satisfied through `Prompt.provenance`**, the ordered four-field structure §24.4 authorizes — `chunk_id`, `document_id`, `character_start`, `character_end` — which **U-2** established precisely because `SupportingEvidence` could not otherwise be constructed without the Generator reaching back into the corpus.
- **A `RetrievalResult` remains the upstream source of that provenance**, reached through `ContextBuilder` along §24.2's pipeline. It is **not** a direct v2 Generator input, and RO-14 does not make it one.
- **G-6 is unchanged** — corpus membership continues to hold by construction, because chunk ids are carried through and *"the Generator never constructs a chunk id."*
- **No evidence is fabricated, no runtime code changes, and no new contract version is created.** The existing implementation already satisfies the intent; this decision records why it does, and does not authorize any modification to make it so.

**Recorded at `docs/GENERATION_CONTRACT.md` §25.2**, through the same adjacent mechanism and under the same byte-for-byte preservation of §1–§24.

#### What RO-14 does not do

**`docs/architecture.md` is unmodified** — that synchronization is M2-14's, under Decision 4. **`docs/roadmap.md` is unmodified.** **It implements nothing** — `sample_rag/generator.py`, `sample_rag/model_generator.py`, `sample_rag/context_builder.py`, `sample_rag/deepseek.py`, `scripts/cli.py`, `scripts/run_generation.py`, every `tests/` module and `requirements.txt` are untouched; **no dependency is added, no provider call was made, no credential was read, and no network access occurred.** **It renames nothing** — neither `Generator` nor `ModelGenerator`.

**It discharges no capability** — **M2-06** and **M2-14** both remain **OPEN**, and **M2-06 is not discharged, staged, split or reclassified.** **M2-12 is not reopened, its discharge row is not edited, and `docs/M2.12_Context_Builder_Report.md` is unchanged.** It **creates no capability, no milestone and no derivative identifier** — no `M2-06a`, no `M2-06b`, no `M2-14a`, no trace or traceability capability, and no evaluation capability.

**RO-06 through RO-13 are unchanged in every part except RO-13 Decision 5's singular-row synchronization target** (Decision 3), as are `docs/roadmap.md` §1.1's stage allocation, every retrieval contract, and the `VectorStore`, `EmbeddingProvider`, `Chunk` and `Document` contracts. **Generation Contract v1.0.0 (§1–§23) and v2.0.0 (§24) are byte-for-byte unchanged**, and **no v2.1.0 or v3.0.0 is created.** It **activates no evaluation tooling** — **M2-07**, **M2-08** and **M3-01** are untouched and no Faithfulness, Groundedness, Hallucination Rate, Answer Relevancy, Context Precision or Context Recall claim is authorized. It **changes no retrieval**, **does not widen `REACHABLE_STAGES`**, **does not resolve U-3**, **triggers neither M2-15 nor M2-17**, **does not dispose of M2.06-F-1 or M2.06-F-3**, and introduces **no orchestration layer, runtime adapter, pipeline coordinator, `ContextEngine`, context-window policy, context compression, token budget, memory, agent runtime, tool calling or model routing.**

### 4.7 Repository Owner ruling RO-15 — Sprint RO-15

Issued at Sprint **RO-15**, after an allocation investigation established that the repository can now execute a full `Retrieve → Assemble → Infer` path end to end and **retains nothing of what it executed** once the process exits: `RetrievalResult`, `Prompt` and `GenerationResult` are Runtime Artifacts (`docs/GENERATION_CONTRACT.md` §5, §13.3), and **no committed authority decided whether a durable execution-evidence artifact is authorized, what it may contain, or where it belongs.** Selecting among the alternatives is a Repository Owner decision rather than an implementing agent's inference. It is fixed repository authority. **This section records it; it does not interpret it.**

**On the section number and the identifier.** This is the register's own §4.7, in the same sense §4.1 through §4.6 are — not the `§4.x` the *Rationale* column of §4's table cites, which points at `docs/P3.7.3_…` **Decision 4** (§2.3). **RO-15 is the next available unique Repository Owner ruling identifier**: RO-01 through RO-05 are in use in §7, RO-06 and RO-07 in §3.1, RO-08 in §4.1, RO-09 in §4.2, RO-10 in §4.3, RO-12 in §4.4, RO-13 in §4.5 and RO-14 in §4.6. **`RO-11` remains a sprint label, not a ruling.** No identifier is reused and no historical ruling is renamed.

**On the two statements that say `RO-15` does not exist, and why neither is edited.** §4.6 records that RO-14 created *"no `RO-15`"*, and the **M2-06** discharge record in §4 states that *"no Repository Owner ruling was created by this discharge — there is no RO-15."* **Both were accurate as statements about the sprints that made them**, and **CP-3** governs: RO-14 created no ruling beyond itself, and Sprint M2.06's discharge created none at all. **RO-15 is a subsequent and separate Repository Owner act**, taken at its own sprint, and it neither contradicts nor amends either statement. **Neither sentence is edited, and no M2-06 or RO-14 evidence is rewritten** — this paragraph is the adjacent record, in the manner §4 already uses for a statement overtaken by a later sprint.

**On its standing relative to the allocation investigation.** That investigation **made no repository change** — it created no module, no trace, no report and no register edit, and invented no authority. **There is therefore no committed investigation document, and none is cited below as though there were.** Every fact this ruling rests on is verifiable at commit `0bb76c6` by direct inspection of the files named. The chronology is **M2-06 STOP → RO-13 → M2-06 implementation → M2-14 STOP → RO-14 → M2-14 architecture synchronization → M2-06 DISCHARGED → allocation investigation → RO-15**.

**On the authority to add a capability row.** §1.3 admits a capability *"only when a Repository Owner decision or a committed authority defers it"*, and reserves allocation to Repository Owner authority; **RO-10 Decision 2** separately bars a sprint that discharges nothing from editing a canonical capability row. **RO-15 is itself that Repository Owner decision** — it is the authority the **M2-18** row in §4 cites, and the Repository Owner supplied the row-synchronization authorization explicitly at this sprint, exactly as RO-12, RO-13 and RO-14 were supplied it. **RO-10 Decision 2 and §1.3 are applied here, not amended.**

| Ruling | Title | Effect |
|---|---|---|
| **RO-15** | **M2-18 Execution Evidence / Traceability Allocation** | **Allocates one new capability — `M2-18`, Execution Evidence / Traceability — at Milestone 2, stage 2C**, as a **subsequent Repository Owner allocation** beyond the seventeen `docs/P3.7.3_…` affirmed. Authorizes a **distinct execution-evidence envelope** that is **not** a serialized `GenerationResult`; fixes it **Non-blocking** for **M2-07** and **M2-08**; resolves the `docs/GENERATION_CONTRACT.md` **§13.2 / §13.3** scope question; authorizes **JSONL** as the v1 storage representation; classifies traces as **derived runtime artifacts that SHALL NOT be Git-tracked**; and **excludes credentials, raw provider payloads and semantic similarity scores** from the authorized boundary. **Discharges no capability**, splits, renames and reallocates none, creates no milestone and no derivative identifier, amends **RO-06** through **RO-14** in no part, **implements nothing**, and **freezes no schema** |

#### Decision 1 — M2-18 is allocated

**The capability is allocated, and it is one capability.**

| | |
|---|---|
| **Identifier** | **`M2-18`** |
| **Name** | **Execution Evidence / Traceability** |
| **Milestone** | **Milestone 2** — stage **2C**, recorded at `docs/roadmap.md` §1.1 under **RO-07** |
| **Class** | **Deterministic Runtime** (§2.1) — it records what an execution did; it introduces no model and no probabilistic engine of its own |
| **Status** | **OPEN — allocated, not implemented** |

**Purpose.** To make a **completed** AI pipeline execution inspectable and diagnostically traceable **after the process exits**, by preserving sufficient evidence to answer questions the repository currently cannot answer once a run ends: what query was executed; which retrieval candidates participated; through which retrieval legs they entered; what ranks they held; which chunks reached `Prompt` construction; which provenance was attached; which generation component and contract era executed; which provider and model executed; what generation outcome and answer were produced; what evidence references supported the result; and what latency was observed.

**What it is not, stated because each is a capability that already exists elsewhere or does not exist at all.** It is **not an evaluation capability** — **M2-07**, **M2-08**, **M2-09**, **M2-10** and **M3-01** are untouched and unactivated. It is **not an optimization capability** — **M2-05**, **M2-15** and **M2-17** are untriggered. It is **not a generation capability** and **not a retrieval capability** — no generation, retrieval, fusion, indexing or embedding behaviour changes. It is **not production observability infrastructure** — **no observability framework, database, OpenTelemetry integration, collector, dashboard, external telemetry sink or tracing infrastructure is created or authorized.**

**On the identifier, specifically.** **`M2-16` is already allocated** (semi-structured sources) and **`M2-17` is already allocated** (chunk-size / overlap benchmarking); neither is reused, reinterpreted or displaced. **`M2-18` is the next available Milestone 2 identifier**, and **no new milestone taxonomy is created** — no `M2C-01`, no `M4`, no trace-milestone series, and no derivative identifier such as `M2-18a`.

#### Decision 2 — M2-18 is NON-BLOCKING, and the reason is preserved

**Blocking status: `Non-blocking`**, recorded in the existing *Blocking status* column of §4's table in the same convention **M2-05**, **M2-11** and **M2-13** use.

**M2-18 SHALL NOT block M2-07, and SHALL NOT block M2-08.** Both remain **OPEN** and **independently executable**.

**The reason, which is the part that must not be lost:**

| | |
|---|---|
| **Why they are not blocked** | **M2-07** and **M2-08** can obtain every input they require **in-process** — a retrieval result, an assembled `Prompt` and a `GenerationResult` are all live objects at the moment a metric is computed. **Trace absence therefore does not prevent metric computation.** |
| **What the trace adds instead** | **Diagnostic traceability of the metric.** A recorded execution explains *why* a score came out as it did — which candidates competed, which legs supplied them, which chunks reached the prompt — after the run is over. |

**The distinction, stated exactly:**

```text
"technically necessary to calculate a metric"
        ≠
"valuable for explaining the metric"
```

**M2-18 is the second, not the first.** M2-07 and M2-08 **MAY** be sequenced after M2-18 for diagnostic value; that is a sequencing preference and **not a dependency**, and **neither is converted into a trace-dependent capability.** **M2-07 remains retrieval / context evaluation and M2-08 remains generation evaluation**, unchanged in scope, and **neither is discharged, modified or activated by this ruling.**

#### Decision 3 — the trace is a distinct execution-evidence envelope

**An M2-18 trace record is a cross-stage execution-evidence envelope. It is NOT a serialized instance of `GenerationResult`.**

```text
GenerationResult
    = runtime generation artifact, produced by the generation component

M2-18 Execution Trace
    = cross-stage execution-evidence envelope, recorded about the execution
```

**The envelope observes the pipeline and records selected evidence about what it did.** It therefore:

- **does not redefine `GenerationResult`** and **adds no field to it** — §15's omissions, `generation_time_ms` included, stand exactly as **RO-13 Decision 3** left them;
- **does not change `Prompt`**, whose shape is fixed by **RO-13**'s **U-2** resolution at §24.4;
- **does not change `RetrievalResult`** or its frozen four fields, and **does not change `SupportingEvidence`**;
- **does not change `Generator`, `ModelGenerator`, `ContextBuilder` or any retrieval component**;
- **does not touch the frozen Milestone 1A path** preserved by **RO-14 Decision 2** — `scripts/cli.py` stays on `Generator`, the frozen specification counts stand, and **no provider call may enter the deterministic pytest suite.**

#### Decision 4 — §13.2 / §13.3 resolved, and JSONL authorized for v1

**The question the investigation identified.** `docs/GENERATION_CONTRACT.md` **§13.2** fixes a serialized form — *"`json.dumps(result, indent=2) + "\n"`, UTF-8, insertion-order keys, one trailing newline"*, at §7 declaration order — and **§13.3** states that *"no persistence is required or defined by this contract."* A trace record containing a projection of generation evidence could be read as falling under that form.

**Repository Owner interpretation.**

- **§13.2 and §13.3 govern the serialization of a `GenerationResult`** — that artifact type, and approved persisted generation artifacts *of that type*.
- **The M2-18 envelope is a different artifact.** It is **not** a `GenerationResult`, and it does not become one by containing a projection of generation evidence — a citation of evidence is not an instance of the artifact cited.
- **The M2-18 envelope is therefore NOT governed by the `GenerationResult` serialization form**, and may use its own authorized representation.

```text
§13.2 / §13.3
    ↓  govern
GenerationResult serialization
    ≠
M2-18 ExecutionTrace serialization
    ↓
M2-18 may use its own authorized representation
```

**The previously identified ambiguity is resolved by this decision.** **§13.2 and §13.3 are not amended, not narrowed and not edited**; what is fixed is their **scope**, which is the `GenerationResult` artifact they were written about. **`docs/GENERATION_CONTRACT.md` is byte-for-byte unchanged by this ruling** — **no §26 is appended, no erratum is issued, and no v2.1.0 or v3.0.0 is created** — because no contract text is reinterpreted here: the ruling states that the contract does not reach a new artifact, not that it says something other than what it says.

**JSONL is AUTHORIZED as the v1 storage representation for M2-18 execution traces.** **One execution = one JSON object = one record**, and records **MAY** be appended as executions occur.

**Deliberately NOT prescribed, and belonging to the M2-18 implementation sprint:** concurrency and locking semantics, file rotation, retention policy, filename conventions, directory path, exact field ordering, key naming, and nesting shape. **RO-15 fixes the representation family; M2-18 fixes the representation.**

#### Decision 5 — the authorized trace content boundary, and what is excluded

**The governing principle is minimality.** The implementation **SHOULD** derive the **smallest useful trace projection** from data **already available at existing boundaries** — `RetrievalResult.diagnostics` is the contract's own open mapping and already carries per-query runtime detail; `sample_rag/fusion.py` already computes per-route positional ranks and `(chunk_id, score)` pairs; `Prompt` already carries `chunk_ids` and the four-field `provenance`. **A trace SHALL NOT become a serialized copy of every runtime object.**

**AUTHORIZED as trace evidence, where available at an existing boundary:** execution identity; timestamp; query; the retrieval candidate union; semantic rank; BM25 rank; RRF rank; RRF score; source-leg attribution; selected chunk ids; `Prompt` provenance; generation component identity; generation contract version; provider; model; generation outcome; `answer_text`; supporting-evidence references; observed latency.

**This list is a capability boundary, not a mandatory implementation schema.** **M2-18 MUST verify availability** for each item and determine the minimal concrete representation. **No instrumentation may be invented solely to manufacture a field that does not exist**, and an item that proves unavailable at an existing boundary is **omitted and reported**, not engineered into existence.

**EXCLUDED from persistence, and not authorized by any reading of the list above:** API credentials; bearer tokens; `Authorization` headers; provider secrets; raw provider request payloads where they carry credentials; raw provider response payloads; **semantic similarity scores**; duplicated corpus or chunk text where existing ids plus provenance suffice; arbitrary `Prompt` duplication where the same information can be referenced; arbitrary library or version telemetry; unrelated system telemetry; and Git metadata recorded merely for convenience.

**On semantic similarity scores, specifically — the frozen `VectorStore` boundary remains CLOSED.** `docs/architecture.md` §7's `VectorStore` Protocol and `sample_rag/vector_index.py` expose `query(vector, top_k) -> list[str]` — **ids, not distances** — and **RO-10** fixed exactly that as M2-02's discharge scope. **RO-15 authorizes NO widening of that contract, or of any equivalent retrieval contract, to expose a similarity score**, and **no alternative path to obtain one may be invented** — not by re-embedding, not by recomputing a distance outside the store, and not by a second index. **Semantic rank is authorized; semantic score is not.**

#### Decision 6 — `GenerationResult` minimality, and why `answer_text` is authorized

**RO-15 does NOT authorize persisting the complete `GenerationResult` object.** M2-18 determines the **minimum projection** that constitutes execution evidence.

**The governing principle:**

| | |
|---|---|
| **Persist** | Evidence that **cannot otherwise be recovered** once the process exits |
| **Reference** | Evidence that **can be deterministically recovered** from the existing committed corpus and provenance |

**`answer_text` is authorized as trace evidence**, and the reason is specific rather than general: it is a **genuine execution artifact** that **cannot be reconstructed by rerunning v2 generation**, because **RO-13 Decision 2**'s **G-9** split expressly declines to guarantee model-output reproducibility (`docs/GENERATION_CONTRACT.md` §24.3). Structural determinism holds; the answer's reproducibility does not. **Evidence text and `Prompt` context SHOULD NOT be blindly duplicated** where chunk ids plus the four-field provenance already give a deterministic reference back into the committed corpus — **G-6**'s corpus membership by construction is what makes that reference sound.

**This decision prescribes no JSON structure.** It states which class of evidence must survive and which need only be referenced; **how that is represented is M2-18's.**

#### Decision 7 — component and contract identity at the observation boundary

**RO-14 Decision 1** established two distinct generation components:

| Component | Contract era | Path |
|---|---|---|
| **`Generator`** | **v1.0.0** | frozen Milestone 1A deterministic / reference |
| **`ModelGenerator`** | **v2.0.0** | Milestone 2 model-backed |

**M2-18 is authorized to record trace evidence sufficient to distinguish these two execution identities**, so a trace can never be read ambiguously as to which component and which contract era produced it. **The preferred minimum conceptual identity is `component` and `contract_version`** — for the current M2-06 path, **`ModelGenerator`** and **`2.0.0`**.

**The trace layer owns this identity, at the observation boundary.** **No field is added to `GenerationResult`**; **`sample_rag/generator.py` and `sample_rag/model_generator.py` are NOT modified to carry trace metadata**; and neither component is renamed, retired or made trace-aware by this ruling.

#### Decision 8 — traces are derived runtime artifacts and SHALL NOT be Git-tracked

**M2-18 traces are classified as DERIVED RUNTIME ARTIFACTS**, in the same class **RO-09** fixed for the FAISS index and its metadata: query-derived, run-local, rebuildable-or-discardable, and **not source artifacts**.

**They SHALL be excluded from Git tracking**, through `.gitignore` or an equivalent repository-native mechanism, **during the M2-18 implementation**. **RO-15 prescribes no runtime path and edits no `.gitignore`** — the concrete location and exclusion mechanism are M2-18's, exactly as **RO-09** left M2.01C the runtime location of the index.

**Two boundaries, kept distinct because conflating them would weaken both:**

| | |
|---|---|
| **Credential safety** | **Absolute.** Credentials, tokens, `Authorization` headers and provider secrets **SHALL NEVER** enter a trace, under any configuration, in any environment, at any verbosity |
| **Content sensitivity** | **Separate and real.** Query, context, answer and evidence may carry resume and job-corpus content, which makes a trace **potentially sensitive derived data** even when it holds no credential |

**Neither is solved by the other.** **RO-15 introduces no redaction, anonymization, encryption, database storage, retention policy or external telemetry** — those are outside this ruling and are not authorized by it.

#### Decision 9 — no ALTM stage is created

**M2-18 is an EVIDENCE LAYER, not a pipeline stage.** It sits *across* the existing execution —

```text
Retrieve  →  Assemble  →  Infer
        (observed by the evidence layer)
```

— and makes already-existing execution artifacts durable.

**`docs/altm.md` is NOT modified**, **no ALTM stage is created or renamed**, **`REACHABLE_STAGES` is NOT widened** (`evaluation/altm_rules.py`), **U-3 is not resolved and is not converted into a capability**, and **M3-02 is untouched.** **M2-18 is not an orchestration capability** — no orchestration layer, runtime adapter, pipeline coordinator or `ContextEngine` is authorized by it.

#### Decision 10 — the historical §10.5 reconciliation is preserved exactly

**The historical statement stands, unedited and still true:**

```text
Historical state
    51 capabilities  ↔  P3.7.3 reconciliation        (accurate as recorded; unedited)
        +
Subsequent Repository Owner allocation
    M2-18                                            (RO-15, this section)
        =
Current capability count: 52
```

**§10.5's *"Matches `docs/P3.7.3_…` Decision 3 §3.6 exactly"* remains true of the original 51** and is **not rewritten.** **RO-15 does not claim, and no reader may infer, that `docs/P3.7.3_…` originally contained M2-18** — it did not, and the ruling that allocates M2-18 is this one. The count is synchronized through the repository's **adjacent-note** mechanism at §10.5, which is the same non-destructive form `docs/DOCUMENT_CONTRACT.md` §8.9 (**E-1**) and §8.10 (**E-2**) established for recording a change rather than silently applying one. **No historical wording is altered anywhere in §10.**

#### Decision 11 — relationship to M2-06, and to M3-01

**M2-06 is and remains ✅ DISCHARGED.** **RO-15 does not reopen it, does not modify its evidence, does not alter its acceptance, and does not reinterpret it as incomplete.** M2-18 **builds on** the real generation path M2-06 established; it does not revisit it.

**M2.06-F-1 and M2.06-F-3 remain OPEN and non-blocking**, dispositioned at `docs/ENGINEERING_TRACEABILITY_REGISTER.md` §3.5 exactly as they are. **M2-18 resolves neither.** It **may make their behaviour more observable** — a recorded execution shows that no provider citation was returned, and shows the candidate set that made the Abstain path unreachable — and **observability is not repair.** Neither finding is marked fixed, and neither is dispositioned by this ruling.

**On M3-01, recorded as architectural context and nothing more.** The investigation observed that Promptfoo (**M3-01**) may eventually benefit from persisted execution evidence, because **G-9** does not guarantee v2.0.0 answer reproducibility and a regression instrument compares runs. **That observation creates no dependency.** **M3-01 is not modified, M2-18 is not blocking for it, no capability is created from the observation, and it is recorded here only as future architectural context.**

#### What RO-15 does not do

**It implements nothing.** `sample_rag/generator.py`, `sample_rag/model_generator.py`, `sample_rag/deepseek.py`, `sample_rag/context_builder.py`, `sample_rag/retriever.py`, `sample_rag/fusion.py`, `sample_rag/vector_index.py`, `scripts/run_generation.py`, `scripts/cli.py`, every `tests/` module, `requirements.txt` and `.gitignore` are **untouched**. **No trace module, trace directory or instrumentation is created**; **no dependency is added**; **no provider call was made, no credential was read, and no network access occurred**; **no metric was computed**; and **Ragas, DeepEval and Promptfoo remain unactivated.**

**It freezes no schema.** No JSON structure, field set, field ordering, key naming, module placement, concurrency semantics, retention policy or filename convention is dictated. **RO-15 fixes WHAT is authorized; M2-18 determines HOW**, within that boundary:

```text
RO-15   — WHAT is authorized
   ↓
M2-18   — HOW it is implemented, within those boundaries
```

**It discharges no capability** — **M2-18** is allocated **OPEN** and is **not** discharged by the ruling that allocates it; **M2-07**, **M2-08**, **M2-14** and **M3-01** are **not discharged**; and **M2-06** is **not reopened**. It **creates no capability beyond M2-18**, **no milestone**, **no milestone taxonomy** and **no derivative identifier** — no `M2-18a`, no `M2-18b`. **`M2-16` and `M2-17` are neither reused nor reinterpreted.**

**RO-06 through RO-14 are unchanged in every part**, as are `docs/architecture.md`, `docs/altm.md`, `docs/MILESTONE_1A.md`, `docs/P3.7.3_…`, `docs/P3.7.6_…`, every retrieval contract, and the `VectorStore`, `EmbeddingProvider`, `Chunk` and `Document` contracts. **Generation Contract v1.0.0 (§1–§23), v2.0.0 (§24) and the §25 errata are byte-for-byte unchanged**, and **no new contract version is created.** `docs/roadmap.md` is amended **only** by the addition of **M2-18** to §1.1's Milestone 2C table, under **RO-07**'s split that assigns stage-within-milestone to that section; **no other roadmap line, and no stage allocation of any existing capability, is altered.** It **widens no contract**, **exposes no semantic similarity score**, **triggers neither M2-15 nor M2-17**, **does not widen `REACHABLE_STAGES`**, **does not resolve U-3**, **does not dispose of M2.06-F-1 or M2.06-F-3**, and **asserts no generation-quality, retrieval-quality, faithfulness, groundedness or hallucination claim** — a trace records what an execution did, and records nothing about whether it was correct.

### 4.8 Repository Owner ruling RO-16 — Sprint RO-16

Issued at Sprint **RO-16**, after the **M2-07** sprint STOPped before implementation on a dependency-authority boundary it could not cross without inventing repository authority: **Ragas is an LLM-evaluation library**, criterion **A-5** bars importing one, and **no existing exception covers it** — RO-13's third exception is scoped to M2-06 and excludes *"evaluation frameworks"* by name. It is fixed repository authority. **This section records it; it does not interpret it.**

**On the section number and the identifier.** This is the register's own §4.8, in the same sense §4.1 through §4.7 are — not the `§4.x` the *Rationale* column of §4's table cites, which points at `docs/P3.7.3_…` **Decision 4** (§2.3). **RO-16 is the next available unique Repository Owner ruling identifier**: RO-01 through RO-05 are in use in §7, RO-06 and RO-07 in §3.1, RO-08 in §4.1, RO-09 in §4.2, RO-10 in §4.3, RO-12 in §4.4, RO-13 in §4.5, RO-14 in §4.6 and RO-15 in §4.7. **`RO-11` remains a sprint label, not a ruling.** No identifier is reused and no historical ruling is renamed.

**On the statement that says `RO-16` does not exist, and why it is not edited.** The **M2-18** discharge record in §4 states that *"no Repository Owner ruling was created by this discharge — there is no RO-16."* **That was accurate as a statement about the sprint that made it**, and **CP-3** governs: Sprint M2.18's discharge created no ruling at all. **RO-16 is a subsequent and separate Repository Owner act**, taken at its own sprint, and it neither contradicts nor amends that statement. **The sentence is not edited and no M2-18 evidence is rewritten** — this paragraph is the adjacent record, in the manner §4.7 already used for the two statements that said RO-15 did not exist.

**On its standing relative to the M2-07 STOP.** That sprint **made no repository change** — it installed nothing, imported nothing, added no dependency, ran no evaluation, and invented no authority. **There is therefore no committed M2-07 STOP document, and none is cited below as though there were.** Every fact this ruling rests on is verifiable at commit `5985785` by direct inspection of the files named. The chronology is **M2-18 DISCHARGED → M2-07 STOP (no change) → RO-16**.

**On the authority to synchronize the M2-07 row.** Under **RO-10 Decision 2** a sprint that discharges nothing may not itself edit a canonical capability row. **RO-16 discharges nothing either**; the Repository Owner supplied that authorization explicitly at this sprint, which is what permits the **M2-07** row's *Auth.* synchronization recorded in §4. **RO-10 Decision 2 is applied here, not amended**, exactly as RO-12, RO-13, RO-14 and RO-15 applied it before.

| Ruling | Title | Effect |
|---|---|---|
| **RO-16** | **M2-07 Ragas Dependency and Evaluation-Judge Authority** | Authorizes a **fourth A-5 exception** — the **Ragas** library, confined to the existing **`evaluation/ragas/`** boundary, **for M2-07 only** — and, as a **separate and independent** decision, authorizes the **existing `sample_rag/deepseek.py` provider boundary** as M2-07's evaluation judge, **conditional on technical reuse without architectural widening**. Selects **no Ragas version or API**, authorizes **no transitive or supporting dependency**, grants **no new embedding or vector-store exception**, and creates **no capability**. **Discharges nothing** — **M2-07**, **M2-08**, **M2-10** and **M3-06** all remain **OPEN** — amends **RO-06** through **RO-15** in no part, leaves **M2-18** ✅ DISCHARGED and untouched, **implements nothing**, installs nothing, and **imports nothing** |

#### Decision 1 — a fourth A-5 exception, for Ragas, scoped to M2-07

**The problem, stated from repository text.** Criterion **A-5** (`docs/MILESTONE_1A.md`) reads *"Zero imports of any embedding, vector-store or LLM-evaluation library"*, and that document records the current position exactly: `requirements.txt` *declares* `ragas`, `evaluation/ragas/` is an **empty scaffold directory**, and *"a declaration is not an import, so A-5 holds as written."* **The declaration is not authority to import.** Verified at `5985785`: no `import ragas` or `from ragas` exists anywhere in the repository, and the package is not installed.

**RO-16 authorizes a fourth exception**, on the same narrow shape as the three before it — **one library, in one boundary, for one capability**:

| | |
|---|---|
| **Library** | **Ragas** |
| **Boundary** | **`evaluation/ragas/`** — the scaffold directory `docs/MILESTONE_1A.md` already names, or the repository's existing equivalent Ragas evaluation boundary should the structure differ at implementation time |
| **Capability** | **M2-07** — Ragas activation / evaluation tooling |
| **Portion of A-5 lapsed** | The **LLM-evaluation** portion, **for Ragas only**, **at that boundary only** |

**A-5 is not lapsed generally.** The criterion stands in every other part, and **RO-16 authorizes no other LLM-evaluation library, no additional evaluation framework, no model router, no agent framework, no second or general-purpose SDK, no orchestration library, and no arbitrary HTTP access anywhere in the repository.** It **does not** automatically authorize **M2-08** (DeepEval), **M3-01** (Promptfoo), **M2-10** or **M3-06**; each remains governed as it is.

**On the three existing exceptions, which are unchanged.** `sentence-transformers` (M2.01A, embedding) and `faiss-cpu` (M2.01B, vector-store) are **taken**; RO-13 Decision 4's LLM/provider exception is **authorized and untaken**, and **RO-16 neither takes, reopens, widens nor reinterprets it** — it is scoped to *"M2-06 model-backed generation only"* and excludes *"evaluation frameworks"* by name, which is precisely why a fourth exception was required rather than a reading of the third. **The §4 preamble's *"These are the repository's only two A-5 exceptions"* sentence remains literally true and is not edited**, because RO-16 — like RO-13 before it — **adds no dependency**: `requirements.txt` is byte-identical at this ruling, and this exception is **AUTHORIZED and UNTAKEN** until M2-07 takes it.

#### Decision 2 — the Ragas version and API are M2-07's, not RO-16's

**RO-16 authorizes the dependency category and its boundary. It selects nothing inside them.**

**Deliberately NOT prescribed:** the Ragas version; the Ragas API surface; the metric-invocation method; the dataset/evaluation adapter design; the mapping of repository artifacts to Ragas inputs; the internal structure or schema of `evaluation/ragas/`; and the test structure.

**M2-07 MUST inspect the compatible version and API against this repository's actual Python environment and record its selection in implementation evidence**, exactly as **RO-13 Decision 4** left the library choice to M2-06 and **RO-08 Decision 1** left the fingerprint algorithm to M2.01B. **No package is installed by this ruling.**

```text
RO-16   — WHAT is authorized
   ↓
M2-07   — HOW it is implemented, within that boundary
```

#### Decision 3 — the existing DeepSeek boundary is authorized as M2-07's evaluation judge, conditionally

**This is a separate and independent authorization.** Ragas metrics are LLM-judge-backed, and the M2-07 STOP identified the judge as a **second** authority question that Decision 1 does not answer.

**RO-16 independently authorizes the existing `sample_rag/deepseek.py` provider boundary for M2-07 evaluation judging.** It is **not** an extension, widening or reinterpretation of **RO-13 Decision 4**, which is scoped to M2-06 generation and is untouched by this ruling.

**The authorization is CONDITIONAL ON TECHNICAL REUSE.** It holds **if and only if** the selected Ragas API can use the existing boundary **without**: modifying the provider architecture; widening the existing provider boundary; introducing another provider integration; introducing another provider SDK; introducing a model router; or introducing arbitrary HTTP access.

| M2-07 finds | Then |
|---|---|
| The selected Ragas API **can** reach the existing boundary as it stands | **Use it.** The authorization is live |
| It **cannot**, without architectural expansion | **STOP** and report the exact incompatibility and the minimum additional Repository Owner decision required |

**M2-07 is NOT required to force the fit.** An implementation that reshapes the provider client to satisfy an evaluation library is the outcome this condition exists to prevent, and **RO-16 does not authorize rewriting `sample_rag/deepseek.py`.**

**Not authorized by this decision:** DeepSeek for arbitrary evaluation frameworks; DeepSeek for **M2-08** automatically; any other provider; any provider SDK; a model router; arbitrary model calls; or general evaluation infrastructure.

**One existing constraint is carried forward unchanged and is binding on M2-07.** **RO-14 Decision 2**: *"No provider call is introduced into the deterministic pytest suite, and none may be."* **A judge call is a provider call.** M2-07's specifications exercise the adapter through injected fakes; the live judge belongs to an on-demand evaluation entry point, on the pattern `scripts/run_generation.py` already establishes for the one real provider call.

#### Decision 4 — the two authorizations are separate, and neither implies the other

**Stated explicitly because conflating them is the likely misreading:**

```text
Decision A — A-5 exception    →  Ragas             →  evaluation/ragas/
Decision B — Provider authority →  existing DeepSeek →  M2-07 judge use only,
                                                        conditional on technical reuse
```

**RO-16 does NOT rule that "Ragas is authorized, therefore whatever model or provider Ragas needs is authorized."** That is not the decision, and no reading of Decision 1 supplies Decision 3's subject. **Only the explicitly named Ragas library and the explicitly named existing DeepSeek provider boundary are authorized** — each on its own terms, each revocable in the other's absence.

#### Decision 5 — no automatic transitive or supporting dependency authorization

**RO-16 authorizes exactly two things**: the named **Ragas** library, and the named **existing DeepSeek provider boundary** under Decision 3's condition. **It authorizes nothing else, and a dependency does not become authorized by being required.**

**Not automatically authorized, however the selected Ragas version may pull them in:** additional evaluation libraries; new embedding libraries; additional provider SDKs; orchestration libraries; model routers; arbitrary HTTP clients; new vector-store packages; and any other supporting or transitive package.

**M2-07 MUST inspect its actual dependency requirements.** Where a required dependency falls outside existing authority, M2-07 **STOPs** — it does **not** install it, does **not** add it to `requirements.txt`, and does **not** read RO-16 as covering it — and reports the exact dependency together with the minimum additional Repository Owner decision required. **This is the same discipline `tests/test_model_generator.py::test_m206_no_dependency_was_added` already enforces structurally for the M2-06 boundary.**

#### Decision 6 — no new embedding or vector-store exception

**RO-16 grants NO new embedding dependency exception, and no new vector-store exception.** The two taken exceptions — `sentence-transformers` in `sample_rag/embedding.py` and `faiss-cpu` in `sample_rag/vector_index.py` — are **unchanged in scope and in module**, and the `VectorStore` boundary stays closed exactly as **RO-10** and **RO-15 Decision 5** left it.

**A Ragas metric that supports or defaults to an embedding model does not thereby authorize one.** **M2-07 MUST first determine whether its selected API actually requires an embedding model for Context Precision and Context Recall.** If a new embedding dependency proves genuinely required and no existing authority covers it, **M2-07 STOPs and requests the minimum additional authorization** — it does **not** manufacture an embedding exception inside the implementation sprint, and it does **not** reach the existing `BGEEmbeddingProvider` for evaluation purposes on the strength of this ruling.

#### Decision 7 — credential safety is carried forward intact

**Any M2-07 judge implementation reusing the existing provider boundary SHALL preserve the credential discipline that boundary already has**, unchanged and unweakened. The credential **SHALL NEVER** be logged, printed, persisted, written into an evaluation report, written into an M2-18 trace artifact, placed in an exception message, or present in any persisted raw provider payload.

**That discipline is currently structural rather than promised**, and RO-16 requires it to stay so: `sample_rag/deepseek.py` exposes **no credential accessor** and reads `DEEPSEEK_API_KEY` inside `complete` alone, which is why `scripts/run_generation.py` can report a failure by exception name without reporting anything about the value, and why `scripts/execution_trace.py` cannot reach a secret at all.

**`sample_rag/deepseek.py` is NOT modified by this ruling**, and **RO-16 does not authorize rewriting the provider client.** Should M2-07 find that the existing client cannot safely support the required judge boundary, that is a **future STOP and a future Repository Owner decision**, not an implementation liberty.

#### Decision 8 — M2-07 and M2-10 remain separate capabilities

**Both remain OPEN, and both remain distinct rows.**

| | |
|---|---|
| **M2-07** | Ragas activation — Layer 2. **Evaluation Tooling** |
| **M2-10** | Context Precision / Context Recall. **Metric**, *"reserved for Ragas"* |

**RO-16 authorizes M2-07 to implement and exercise Ragas tooling against the Context Precision / Context Recall evaluation target**, which `docs/roadmap.md` §5 already names as Layer 2's metric pair — so producing real measurements is within M2-07's stated scope and is not scope creep.

**But exercising the metrics is not discharging the metric capability:**

```text
M2-07 implementation   ≠   M2-10 discharge
```

**The rows are NOT merged, M2-10 is NOT discharged, and its status is NOT changed by this ruling.** Any future M2-10 synchronization remains separately governed and requires its own Repository Owner decision. **A sprint that measures is not thereby a sprint that discharges the measurement capability.**

#### Decision 9 — M3-06 remains OPEN

**RO-16 authorizes the Ragas import and dependency required by M2-07, and nothing broader.** **M3-06** — *"`requirements.txt` declarations → real imports; `evaluation/*` scaffolds populated"*, **Blocks 2 and 3** — remains the wider declaration-to-import and scaffold-population capability, and **remains OPEN**. RO-16 **does not discharge it**, does not rewrite its status, and does not complete it: `deepeval` and `promptfoo` remain declarations, and `evaluation/deepeval/` and `evaluation/promptfoo/` remain empty scaffolds.

**Recorded as a finding rather than acted on:** M3-06's row quotes *"A declaration is not an import, so A-5 holds as written."* When M2-07 takes this exception, that sentence becomes partly overtaken **for `ragas` alone** — the other declarations are untouched and the sentence stays true of them. **No wording is edited here**, and whether M3-06's row needs an adjacent note once the exception is taken is a synchronization question for the sprint that takes it, under §1.3 and **RO-10 Decision 2**.

#### Decision 10 — M2-18 remains discharged and untouched

**M2-18 is and remains ✅ DISCHARGED**, and **RO-15 is unamended in every part.** **M2-07 MAY use M2-18 execution evidence for diagnostic analysis** — which is exactly the diagnostic explainability **RO-15 Decision 2** describes — but **M2-18 is NOT a technical prerequisite for M2-07**, and RO-15 Decision 2's finding that M2-07 obtains its inputs in-process stands unchanged.

**Not modified by this ruling, and not to be modified to suit evaluation:** `scripts/execution_trace.py`, `tests/test_execution_trace.py`, `docs/M2.18_Execution_Evidence_Report.md`, and **RO-15** itself. **No trace field may be added, no `VectorStore` widened and no semantic similarity score exposed** to make a Ragas metric convenient; RO-15's exclusions hold against evaluation exactly as they hold against implementation.

#### What RO-16 does not do

**It implements nothing.** No package was installed — `ragas` remains absent from the environment and is still a declaration only, with **no `import ragas` anywhere in the repository**. `requirements.txt` is **byte-identical**. `evaluation/`, `sample_rag/`, `scripts/`, `tests/` and `.gitignore` are **untouched**; **no evaluation was executed, no metric was computed, no judge call was made, no credential was read and no network access occurred.**

**It discharges no capability** — **M2-07**, **M2-08**, **M2-10**, **M3-01** and **M3-06** all remain **OPEN**, and **M2-18** stays ✅ DISCHARGED without being reopened, edited or re-evidenced. It **creates no capability, no milestone and no derivative identifier** — no `M2-07a`, no evaluation capability beyond the authorization itself, and no new milestone taxonomy. **It allocates nothing**: unlike RO-15, this ruling adds no register row.

**RO-06 through RO-15 are unchanged in every part**, as are `docs/architecture.md`, `docs/altm.md`, `docs/MILESTONE_1A.md`, `docs/P3.7.3_…`, `docs/P3.7.6_…`, `docs/roadmap.md`'s stage allocation, every contract, and the `VectorStore`, `EmbeddingProvider`, `Chunk` and `Document` contracts. **Generation Contract v1.0.0 (§1–§23), v2.0.0 (§24) and the §25 errata are byte-for-byte unchanged**, and **no new contract version is created.** **A-5 is not amended** — `docs/MILESTONE_1A.md` is a completed Milestone 1 artifact and is not edited; a narrow exception is recorded here, which is how the three before it were recorded. It **does not widen `REACHABLE_STAGES`**, **does not resolve U-3**, **triggers neither M2-15 nor M2-17**, **disposes of no finding**, and **asserts no retrieval-quality, context-quality, faithfulness or groundedness claim** — authorizing an instrument is not a statement about what it will measure.

### 4.9 Repository Owner ruling RO-17 — Sprint RO-17

Issued at Sprint **RO-17**, after the **M2-07** implementation sprint STOPped at RO-16's own transitive-dependency gate: **RO-16 Decision 5** required M2-07 to inspect what Ragas actually requires and to STOP if a required dependency fell outside existing authority, and it does. It is fixed repository authority. **This section records it; it does not interpret it.**

**On the section number and the identifier.** This is the register's own §4.9, in the same sense §4.1 through §4.8 are — not the `§4.x` the *Rationale* column of §4's table cites, which points at `docs/P3.7.3_…` **Decision 4** (§2.3). **RO-17 is the next available unique Repository Owner ruling identifier**: RO-01 through RO-05 are in use in §7, RO-06 and RO-07 in §3.1, RO-08 in §4.1, RO-09 in §4.2, RO-10 in §4.3, RO-12 in §4.4, RO-13 in §4.5, RO-14 in §4.6, RO-15 in §4.7 and RO-16 in §4.8. **`RO-11` remains a sprint label, not a ruling.** No identifier is reused and no historical ruling is renamed.

**On its standing relative to the M2-07 STOP.** That sprint **made no repository change** — it installed nothing, imported nothing, added no dependency, ran no evaluation and invented no authority; it downloaded one wheel to a scratchpad outside the repository for inspection and removed it. **There is therefore no committed M2-07 STOP document, and none is cited below as though there were.** Every fact this ruling rests on is verifiable at commit `8da2930` by direct inspection of the files named and of the selected package's own published metadata. **RO-16 is not rewritten**, and **CP-3** governs.

**The chronology, stated explicitly because the ruling only makes sense as a sequence:**

```text
M2-07 allocated — "Ragas activation — Layer 2"     (docs/P3.7.3_…; docs/roadmap.md §5)
        ↓
M2-07 STOP #1 — A-5 bars importing an LLM-evaluation library
        ↓
RO-16 — fourth A-5 exception: Ragas at evaluation/ragas/, for M2-07 only;
        DeepSeek judge authorized conditionally; D-5 requires dependency inspection
        ↓
M2-07 dependency investigation — every Ragas release carrying the required
        Context Precision / Context Recall API hard-depends on LangChain
        ↓
M2-07 STOP #2 — RO-16 D-5 boundary crossed; NA-07 is an EXCLUSION, not a deferral
        ↓
RO-17 — the implementation path is rescoped to a native evaluation; the
        capability, its identifier, its milestone and its stage are unchanged
```

**On the authority to synchronize the M2-07 row.** Under **RO-10 Decision 2** a sprint that discharges nothing may not itself edit a canonical capability row. **RO-17 discharges nothing either**; the Repository Owner supplied that authorization explicitly at this sprint, which is what permits the **M2-07** row synchronization recorded in §4. **RO-10 Decision 2 is applied here, not amended**, exactly as RO-12 through RO-16 applied it before.

| Ruling | Title | Effect |
|---|---|---|
| **RO-17** | **M2-07 Native Evaluation Rescoping** | **Rescopes M2-07's authorized implementation path** from Ragas activation to a **native, repository-owned implementation of Context Precision and Context Recall**, faithful to the repository's own metric definitions. Records that **Ragas-the-library is not adopted for M2-07 under the current repository constitution**, and **preserves NA-07 unchanged**. **Independently** authorizes the existing `sample_rag/deepseek.py` boundary as the native evaluation judge, on the same conditional-reuse terms, **without relying on RO-16 D-3**. Grants **no** new embedding, vector-store, provider or orchestration authority. **Changes no capability identity, identifier, milestone, stage or ownership**; **creates no capability, milestone or ruling dependency**; **discharges nothing** — **M2-07**, **M2-08**, **M2-10**, **M3-01** and **M3-06** all remain **OPEN** and **M2-18** stays ✅ DISCHARGED and untouched; and **implements nothing** |

#### Decision 1 — M2-07's implementation path is rescoped to a native evaluation

**M2-07 is authorized to implement and exercise a native, repository-owned computation of Context Precision and Context Recall** against the existing RAG pipeline and the authorized evaluation data.

**M2-07 remains the same capability, under the same identifier.** **No new `M2-xx` is created**, the capability is **not renamed**, its **milestone (2) and stage (2A) are unchanged**, and its ownership is unchanged. **Only the implementation mechanism is rescoped** — what changes is *how* Layer 2 becomes measurable, not *what* M2-07 is or where it sits.

**The implementation must be faithful to the repository's own metric definitions**, which exist and are tool-independent — `docs/AI_Quality_Metrics_Reference.md` defines **Context Precision** as *"Of everything retrieved, how much was actually relevant?"* and **Context Recall** as *"Of everything relevant that exists in the source, how much did retrieval actually find?"* — and to the ALTM framing that places both at the **Retrieve** stage (`docs/altm.md` §9, §12).

**A simplified set-overlap calculation is NOT authorized as a substitute for the metric's meaning.** The repository already draws this distinction against itself: `docs/P3.3.3_…` §3 records the existing `chunk_`-prefixed metrics as **explicitly not proxies** for Context Precision and Context Recall, and **M2-10**'s row carries that same reservation. **M2-07 MUST derive the semantics from the authoritative definitions and determine the minimum faithful computation**; producing the easier arithmetic under the harder name is the failure this decision exists to prevent.

**RO-17 authorizes the native path and prescribes no implementation detail** — not the algorithm, not the module structure, not the entry point, not the result shape, not the test strategy.

```text
RO-17   — WHAT is authorized
   ↓
M2-07   — HOW it is implemented, within that boundary
```

**Native precedent exists and is not invented here:** `evaluation/retrieval_metrics.py` already computes retrieval metrics over the committed corpus in the standard library alone, and **M2-07 may follow that shape** — that is an observation about precedent, not a prescription of design.

#### Decision 2 — Ragas-the-library is not adopted for M2-07 under the current repository constitution

**The finding, from the package's own published metadata rather than from preference.** **Every Ragas release carrying the required Context Precision / Context Recall API declares `langchain`, `langchain-core`, `langchain-community` and `langchain-openai` among its core — non-extra — dependencies, together with `openai`.** The releases whose core dependencies omit LangChain are the 2023 pre-alpha line, which predates that API entirely and depends on `sentence-transformers`, `transformers`, `spacy` and `nltk` instead — **new embedding libraries, which RO-16 Decision 6 bars**. **There is no release that satisfies the metric requirement and the authorized dependency boundary at the same time.**

**The dependency is not incidental to packaging; it is load-bearing.** Ragas' own custom-judge extension point — the mechanism by which RO-16 Decision 3's DeepSeek reuse would have been reached — is defined in LangChain types, and the modules reached by `import ragas` import LangChain unconditionally at module level rather than under `TYPE_CHECKING`. **Repository code could therefore not construct a judge without importing an excluded framework**, which is RO-16 Decision 5's category B, not its category A.

**Therefore: Ragas-the-library is NOT adopted for M2-07 under the current repository constitution.**

**Stated in exactly that form, and no wider.** This is **not** a finding that Ragas is defective, unsuitable in general, or permanently prohibited. **It is a disposition of a previously authorized-but-unexercised implementation path**, and it is contingent on a constitution the Repository Owner may later change.

**What this decision does NOT do.** **RO-16 is not rewritten, withdrawn or invalidated** — §4.8 stands as the historical record of what was authorized and why, and its fourth A-5 exception **was correctly issued on the evidence available when it was issued**. **RO-16's Ragas exception is simply not taken**, exactly as **RO-13's third exception remains authorized and untaken**; the repository is unchanged by an authorization no sprint exercises. **No new Ragas exception is created**, **no Ragas is installed or imported**, and `requirements.txt` is byte-identical — the `ragas` declaration stays a declaration.

#### Decision 3 — NA-07 is preserved unchanged

**`NA-07` — *"LangChain / LangGraph; agent orchestration; MLflow; LangSmith; Phoenix; distributed retrieval; GPU optimization; production orchestration; a second GitHub project"* — remains recorded as *"Excluded, not deferred"*, in every part.** Its own reasoning is the reason RO-17 rescopes rather than widens: *"Allocating one would convert an exclusion into a plan."*

**RO-17 creates no authorization for** LangChain, LangGraph, `langchain-core`, `langchain-community`, `langchain-openai`, any other orchestration framework, any additional provider SDK, arbitrary HTTP access, a model router, or an agent framework.

**`docs/roadmap.md` §7, `docs/architecture.md` §11 and `docs/MILESTONE_1A.md` are NOT modified**, and specifically not modified to accommodate Ragas. **An exclusion is not converted into a plan by this ruling**, and the repository remains a **two-A-5-exception** repository — `sentence-transformers` and `faiss-cpu` — with RO-13's third and RO-16's fourth both authorized and untaken.

#### Decision 4 — the DeepSeek evaluation judge, independently authorized for the native path

**RO-17 independently authorizes the existing `sample_rag/deepseek.py` provider boundary as M2-07's evaluation-judge boundary for the native Context Precision / Context Recall evaluation.**

**This does not rest on RO-16 Decision 3, and RO-16 Decision 3 is not the authority for it.** That decision was expressly conditional on *"the selected Ragas API"* reusing the existing boundary; Ragas is no longer the implementation path, so its condition has no subject and cannot carry the native path. **This is a fresh authorization on its own terms.** It equally **does not amend or expand RO-13 Decision 4**, which is scoped to M2-06 generation and remains untouched and untaken.

**The authorization is CONDITIONAL ON TECHNICAL REUSE**, on the same shape RO-16 used. It holds **if and only if** the native implementation can use the existing boundary **without**: modifying its provider architecture; changing its credential model; introducing another provider integration; introducing another provider SDK; introducing a model router; introducing arbitrary HTTP access; or otherwise widening the authorized provider boundary.

| M2-07 finds | Then |
|---|---|
| The native judge can reach the existing boundary as it stands | **Use it.** The authorization is live |
| It cannot, without one of the changes above | **STOP** and report the exact incompatibility and the minimum further Repository Owner decision required |

**M2-07 MUST NOT force compatibility.** **`sample_rag/deepseek.py` is not modified by this ruling and may not be rewritten to fit an evaluation caller**, no alternate provider client may be created, and no second provider architecture may be introduced.

**Scope.** The authorization applies to **M2-07 native evaluation only**. It does **not** authorize **M2-08**, **M3-01**, general evaluation infrastructure, another provider, another provider SDK, provider-architecture change, a model router, or arbitrary HTTP access.

**Credential safety is carried forward intact**, on the terms **RO-16 Decision 7** already fixed and which this decision restates rather than relaxes: the credential **SHALL NEVER** be printed, logged, persisted, written into an evaluation report or an M2-18 trace, placed in an exception message, or present in any persisted raw provider payload. That discipline is **structural today** — the client exposes no credential accessor and reads `DEEPSEEK_API_KEY` inside `complete` alone — and **RO-17 requires it to remain structural**.

**`RO-14` Decision 2 remains binding and is not relaxed by this ruling:** *"No provider call is introduced into the deterministic pytest suite, and none may be."* **A judge call is a provider call.** M2-07's deterministic specifications **MUST** exercise the evaluation path through a non-networked substitute, and **live judging MUST remain confined to an explicit, on-demand evaluation entry point** — the pattern `scripts/run_generation.py` already establishes for the repository's one real provider call.

#### Decision 5 — the embedding and vector-store boundaries remain closed

**RO-17 grants NO new embedding exception and NO new vector-store exception.** The two taken A-5 exceptions keep their existing scope and module — `sentence-transformers` in `sample_rag/embedding.py`, `faiss-cpu` in `sample_rag/vector_index.py` — and the `VectorStore` boundary stays closed exactly as **RO-10** and **RO-15 Decision 5** left it.

**Not authorized:** another embedding library; another vector-store package; any change to `VectorStore`; any widening of the existing embedding seam; and **use of `BGEEmbeddingProvider` for evaluation purposes**, which is not authorized by this ruling merely because the provider already exists in the repository for retrieval.

**M2-07 MUST first determine what its native metric semantics actually require.** If a faithful implementation genuinely requires a dependency or capability outside existing authority, **M2-07 STOPs and reports the exact authority conflict** — it does not resolve an authority question by installing something.

#### Decision 6 — metric semantics are derived, not prescribed

**RO-17 authorizes the two metrics and does not prescribe their algorithm.** The later sprint derives the semantics from the repository's authoritative material — `docs/AI_Quality_Metrics_Reference.md`, `docs/altm.md` §9 and §12, and `docs/P3.3.3_…` §3 — and records its derivation in implementation evidence.

**Two distinctions MUST survive the implementation, because they are what the metric names mean:**

| | |
|---|---|
| **Context Recall** | Whether the retrieved context contains the **independently authored** expected/relevant information. The reference is the committed golden ground truth — **never the system's own retrieval output** |
| **Context Precision** | Whether the retrieved context is **relevant**, on the repository's authoritative metric semantics rather than on an incidental identifier match |

**If the authoritative definition requires an LLM relevance judgement, M2-07 MAY use the judge Decision 4 independently authorizes.** Whether it does is an implementation finding for that sprint to establish and evidence, not a conclusion reached here.

**M2-07 MUST preserve enough evidence to explain a metric result**, so a score can be read as evidence rather than as an assertion. **RO-17 prescribes no evidence schema, no report format and no trace shape**, and **M2-18 is not modified to carry evaluation output** — see Decision 9.

#### Decision 7 — M2-07 and M2-10 remain separate, and both remain OPEN

| | |
|---|---|
| **M2-07** | The evaluation **implementation and exercise** — Layer 2 becoming measurable |
| **M2-10** | The **Context Precision / Context Recall metric capability**, *"reserved for Ragas"* as its row records |

**M2-07 may produce real Context Precision and Context Recall measurements** — that is its stated evaluation target and `docs/roadmap.md` §5 already names the pair as Layer 2's.

**M2-07 implementation ≠ M2-10 discharge.** **M2-10 is not discharged by this ruling, its row is not edited, its status is unchanged, and the two rows are not merged.** Any future M2-10 synchronization remains separately governed and requires its own Repository Owner decision. **A sprint that measures is not thereby a sprint that discharges the measurement capability** — RO-16 Decision 8 said this of the Ragas path, and it is equally true of the native one.

**Recorded as a finding, not acted on:** **M2-10's row reserves those metrics *"for Ragas"***, and RO-17 rescopes the mechanism away from Ragas. That reservation's **tool attribution** is overtaken while its substance — that the metrics are not implemented at Milestone 1A and belong to Milestone 2 — stands unchanged. **No M2-10 wording is edited here**; whether a synchronization is owed is a question for the sprint or ruling that disposes of M2-10.

#### Decision 8 — M3-06 remains OPEN

**M3-06** — *"`requirements.txt` declarations → real imports; `evaluation/*` scaffolds populated"* — **remains OPEN and is not discharged, and its status is not altered.** `evaluation/deepeval/` and `evaluation/promptfoo/` are **not populated**, and **DeepEval and Promptfoo are not imported**.

**The Ragas declaration remains a declaration.** RO-16 Decision 9 anticipated that M3-06's *"a declaration is not an import"* wording would be partly overtaken **for `ragas`** once M2-07 took the exception; **M2-07 did not take it**, so that anticipation did not occur and **the sentence remains true of every declaration in the file, `ragas` included**. **No M3-06 synchronization is owed or invented here.**

#### Decision 9 — M2-18 remains discharged and untouched

**M2-18 remains ✅ DISCHARGED**, and **RO-15 is unamended in every part and is not reinterpreted.**

**Not modified by this ruling, and not to be modified to suit evaluation:** `scripts/execution_trace.py`, `scripts/run_generation.py`, `tests/test_execution_trace.py` and `docs/M2.18_Execution_Evidence_Report.md`. **No trace field may be added for evaluation, no `VectorStore` widened and no semantic similarity score exposed.**

**M2-07 MAY consume M2-18 execution evidence diagnostically** — which is exactly the diagnostic explainability **RO-15 Decision 2** describes — but **M2-18 is not an M2-07 prerequisite and M2-07 may not redesign it.**

#### Decision 10 — no implied future authority

**RO-17 authorizes the native M2-07 evaluation path described above, and nothing else.**

**Not authorized:** **M2-08** / DeepEval; **M3-01** / Promptfoo; retrieval optimization; prompt optimization; generation optimization; **M2-15**; **M2-17**; additional evaluation frameworks; additional providers; and any new capability. Each remains governed by its own existing authority or by a future ruling.

#### Finding — the Ragas tool attribution in the wider documentation set

**Recorded, deliberately not acted on.** Several committed documents attribute Layer 2 to **Ragas** as the implementing tool: `docs/roadmap.md` §5's four-layer table (*Tool* column) and its §1.1 note that the retrieval-quality signal *"is Ragas (M2-07)"*; `docs/altm.md` §9's Retrieve-stage row, §12's layer mapping and its Milestone 2 summary; and `docs/P3.3.3_…` §3's *"Reserved for Milestone 2, Ragas."*

**RO-17 edits none of them**, for three reasons stated rather than assumed. **First**, `docs/P3.3.3_…` is a completed sprint report and **CP-3** governs it. **Second**, the substance of each statement survives the rescoping — the **layer**, the **metric pair**, the **ALTM stage**, the **capability**, the **milestone** and the **stage** are all unchanged, and `docs/roadmap.md` §5 itself states that its layers correspond *"to specific ALTM stages, not to a specific tool's marketing scope."* **Third**, and decisively, changing the *Tool* column of the repository's evaluation strategy — alongside §7's *"Tool scope remains fixed at three: DeepEval, Promptfoo, Ragas"* — would be a **semantic revision of the evaluation strategy**, which is a larger act than an implementation-path ruling should perform on its own authority.

**RO-17 adds no evaluation tool**, so §7's three-tool ceiling is **not breached** by it.

**This finding owes no implementation and allocates no capability.** Whether the wider documentation set is synchronized — and how — is a **separate Repository Owner documentation decision**, and it is recorded here so that the divergence is visible rather than discovered later.

#### What RO-17 does not do

**It implements nothing.** No package was installed — `ragas`, `langchain-core` and `openai` are all absent from the environment — **no import was added anywhere**, and `requirements.txt` is **byte-identical**. `sample_rag/`, `scripts/`, `tests/`, `evaluation/`, `datasets/` and `.gitignore` are **untouched**; **no evaluation was executed, no metric computed, no judge call made, no credential read and no network access performed for evaluation.**

**It discharges no capability** — **M2-07**, **M2-08**, **M2-10**, **M3-01** and **M3-06** all remain **OPEN**, and **M2-18** stays ✅ DISCHARGED without being reopened or re-evidenced. It **creates no capability, no milestone, no derivative identifier and no new `M2-xx`** — **M2-07 keeps its identifier, its name, its class, its blocking status, its milestone and its stage.** It **allocates nothing**: no register row is added.

**RO-06 through RO-16 are unchanged in every part** — including **RO-16**, whose fourth A-5 exception stands as issued and simply goes untaken — as do `docs/architecture.md`, `docs/altm.md`, `docs/roadmap.md`, `docs/MILESTONE_1A.md`, `docs/P3.7.3_…`, `docs/P3.7.6_…`, **NA-07**, every retrieval contract, and the `VectorStore`, `EmbeddingProvider`, `Chunk` and `Document` contracts. **Generation Contract v1.0.0 (§1–§23), v2.0.0 (§24) and the §25 errata are byte-for-byte unchanged**, and **no new contract version is created.** **A-5 is not amended and no fifth exception is created.** It **does not widen `REACHABLE_STAGES`**, **triggers neither M2-15 nor M2-17**, **disposes of no finding**, and **asserts no retrieval-quality or context-quality claim** — rescoping how a measurement will be taken says nothing about what it will show.

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

## 6. Resolved implementation choice — M2-02 vector store

**RESOLVED at Sprint RO-06 / RO-07.** `docs/P3.7.3_…` authorization **A6** required an explicit Repository Owner election. **That election has now been made: the Milestone 2 vector-store implementation is FAISS.** The record of the divergence is retained below under **CP-3**; the election is recorded beneath it.

| | |
|---|---|
| **Named by every committed authority** | **FAISS** — `docs/architecture.md` §5, §9, Capability Matrix; `docs/roadmap.md` §7; `docs/MILESTONE_1A.md` Out of Scope |
| **Named by the P3.7.3 sprint brief** | **sqlite-vec** — appears in no committed repository authority |
| **Milestone allocation** | **Milestone 2**, unaffected. Both candidates satisfy it |
| **Standing before the election** | **FAISS stood**, because it is what the committed authorities say |
| **How it was to be changed** | An explicit Repository Owner election, after which `docs/architecture.md` §5 and §9 and `docs/roadmap.md` §7 may be amended, citing that election — **not** `docs/P3.7.3_…`, which records the divergence rather than resolving it |

> **Repository Owner election — FAISS. Recorded at Sprint RO-06 / RO-07, under authorization A6.**
>
> **The elected Milestone 2 vector-store implementation is FAISS.** The election is made because **every committed repository authority already names FAISS** — `docs/architecture.md` §5 (*"FAISS (Milestone 2 default)"*), §9 and its Milestone Capability Matrix; `docs/roadmap.md` §7 (*"Vector databases (FAISS)"*); `docs/MILESTONE_1A.md` Out of Scope — and **no committed authority names sqlite-vec.** Only the P3.7.3 sprint brief did, and `docs/P3.7.3_…` R-M2-02 expressly declined to rule from a brief rather than from committed evidence.
>
> **Authorization A6 is DISCHARGED.** It was conditional — *"binding only if the Repository Owner elects it"* — and its condition is now met in favour of the standing authority rather than against it.
>
> **No document was amended to record the election, and none needed to be.** A6 authorized amending `docs/architecture.md` §5 and §9 and `docs/roadmap.md` §7 **only if sqlite-vec were elected.** Because FAISS was elected, those documents already say what the election ratifies; editing them would restate an unchanged fact. `docs/P3.7.3_…` §522's observation that sqlite-vec would suit the stdlib-`sqlite3` storage choice is retained as what it was recorded as — *"an argument, not an authority"* — and is not reopened here.
>
> **M2-02's row in §4 is unchanged.** Its *"Implementation unresolved — see §6"* note now resolves to this election. The capability, its class, its milestone and its blocking status are untouched: the election settles *which* implementation, not *whether* or *when*.

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
| **1B-08** | **DQ-5** — chunk validity as a corpus property | **Sprint 1B.1 (Corpus Integrity)**, commit `f4544bf` | `tests/test_data_quality.py` — plan §11.2 phase **W6**: the committed-collection contract gate, the §17 six-field completeness check, and the §17 positional-derivation check for `chunks[].id`; `tests/conftest.py` `real_chunk_collection` |
| **1B-09** | **DQ-6** — chunk referential integrity, incl. Chunk invariant 3's full form | **Sprint 1B.1 (Corpus Integrity)**, commit `f4544bf` | `tests/test_data_quality.py` — plan §11.2 phase **W6**: `chunks[].document_id` → Manifest entry and → loaded `Document`; Manifest-side coverage; and `docs/CHUNK_CONTRACT.md` §17 invariant 3 in full form, `text == document_text[character_start:character_end]` |

| **1B-01** | `EmbeddingProvider` interface | **Sprint 1B.2 (Index Layer)** | `sample_rag/embedding.py` — `EmbeddingProvider` Protocol per `docs/architecture.md` §5, §7; `tests/test_indexer.py` |
| **1B-02** | `VectorStore` interface | **Sprint 1B.2 (Index Layer)** | `sample_rag/vector_store.py` — `VectorStore` Protocol, no implementation; `tests/test_indexer.py`, incl. an AST specification that the module declares nothing else |
| **1B-03** | Index Layer — `Indexer` component (stub) | **Sprint 1B.2 (Index Layer)** | `sample_rag/indexer.py` — `Index`, `Indexer.index(chunks) -> Index` per `docs/architecture.md` §5; `tests/test_indexer.py` |
| **1B-04** | Deterministic placeholder vectors | **Sprint 1B.2 (Index Layer)** | `sample_rag/embedding.py` — `DeterministicEmbeddingProvider`, content-derived and stdlib-only; `tests/test_indexer.py` |
| **1B-10** | **DQ-7** — index-coverage validation | **Sprint 1B.2 (Index Layer)** | `tests/test_data_quality.py` — index coverage over the committed Chunk Corpus, coverage exactness, representation width, and the placeholder marker |
| **1B-11** | `documents[].indexed` semantics resolution | **Sprint 1B.2B**, Repository Owner ruling **R-02** | `docs/MILESTONE_1A.md` build item 1 *Contract Change — `documents[].indexed` removed*; `docs/DOCUMENT_CONTRACT.md` §8.10 Erratum E-2; `docs/DATA_QUALITY_VALIDATION_PLAN.md` §7.2, §9; `scripts/build_manifest.py` `REQUIRED_DOCUMENT_FIELDS`; `sample_rag/knowledge_manifest.json` regenerated without the field; `docs/P3.7.6_…` §E-4 |

**Commit reference — Git is authoritative.**

**This register does not record implementation commit hashes.** A row is discharged by the **sprint** that built it, and its **Evidence** column names the artifacts — modules, specifications, digests — that are verifiable in the working tree by inspection. Commit identity for that work is read from Git, which is the authoritative implementation history; duplicating it here would create a second, weaker copy that can drift from the first.

Two consequences, recorded so they are not mistaken for omissions:

- **No placeholder is ever left in this table** awaiting a hash, and **no documentation-only follow-up commit** is made for the sole purpose of inserting one. A discharge row is complete when it names its sprint and its evidence.
- **Existing commit references are retained, not removed.** `docs/P3.7.3_…` **CP-3** governs: a record that was accurate when written stays. The two below are historical fact and remain readable as such — `RO-01`/`RO-02`/`RO-05` at **`e5d7ce0`**, and `1B-08`/`1B-09` at **`f4544bf`**. The same applies to every other commit named in this document: §0's baseline `180dcdc`, §2.2's blocking-status horizon, §9's sprint sequence, and `8ddcaa7` in the RO-01 row.

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
| `knowledge_manifest.json` `indexed` semantics | **1B-11** | ✅ Discharged at Sprint 1B.2B by Repository Owner ruling **R-02** |
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

> **▶ Adjacent note — subsequent allocation recorded at Sprint RO-15. The table and the sentence above are retained exactly as written, and both remain true.**
>
> **The table above is the P3.7.3 reconciliation**, and it is a **historical** statement: those **51** capabilities are the ones `docs/P3.7.3_…` Decision 3 §3.6 allocated, and they **match it exactly**, as the sentence says. **Nothing in this note edits, reinterprets or weakens that.** In particular, **`docs/P3.7.3_…` did NOT contain M2-18**, and no reader may infer from this note that it did.
>
> **Repository Owner ruling RO-15 (§4.7) subsequently allocates one further capability — `M2-18`, Execution Evidence / Traceability**, at Milestone 2, stage 2C. It is a **subsequent Repository Owner allocation**, made at Sprint RO-15 on RO-15's own authority, and it is **not** a member of the reconciled set above.
>
> ```text
> Historical state
>     51 capabilities  ↔  P3.7.3 reconciliation     (unedited; still exact)
>         +
> Subsequent Repository Owner allocation
>     M2-18                                         (RO-15, §4.7)
>         =
> Current capability count: 52
> ```
>
> | | Section | Capabilities |
> |---|---|---|
> | Historical | §4 Milestone 2, as reconciled to P3.7.3 | **17** |
> | Subsequent | **M2-18**, allocated by **RO-15** | **+1** |
> | **Current** | **§4 Milestone 2** | **18** |
> | **Current** | **Total** | **52** |
>
> **Remaining in Milestone 1A is still 0** — M2-18 is a Milestone 2 capability and touches no Milestone 1A obligation. **No capability was reclassified or reallocated by RO-15**, no existing row was edited, no identifier was reused, and the §10.1 through §10.4 reconciliations are unchanged in every part. This note is recorded in the repository's established **adjacent, non-destructive** form — `docs/DOCUMENT_CONTRACT.md` §8.9 (**E-1**) and §8.10 (**E-2**) — rather than by amending the table, precisely so the historical reconciliation stays verifiable against `docs/P3.7.3_…`.

---

*This register is the canonical repository authority for deferred capabilities. It records allocations made by `docs/P3.7.3_Repository_Owner_Constitutional_Decision.md`; it makes none of its own. Reallocation requires a Repository Owner constitutional decision, cited in the affected row.*
