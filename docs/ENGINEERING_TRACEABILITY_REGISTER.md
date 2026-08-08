# Engineering Traceability Register

**Repository:** `ai-quality-engineering`
**Status:** Active — established at Sprint P3.1.7.2 (Assurance Remediation)
**Scope at establishment:** Knowledge Layer (Milestone 1A). Later layers are added as their decisions are dispositioned.
**Last synchronized:** Sprint P3.7.2 (Repository Governance Synchronization) — Retrieval, Evaluation, Dataset, Generation and CLI layers added, per `docs/P3.7.2_Repository_Governance_Synchronization_Report.md`; then Sprint **RO-09**, which added one open observation (**M2.01B-F-1**, §3.5) and changed nothing else

---

## 1. Purpose

A durable, **retrospective** record of engineering dispositions that outlives the sprint that produced them.

The repository reached Sprint P3.1.7 holding its engineering record in artifacts never intended to carry it: deferred findings in a pytest `conftest.py` docstring, resolved design decisions in module docstrings, and sprint provenance in commit messages alone. Both independent reviews at Sprint P3.1.7 recommended this register (`P3.1.7-GOV-01`, Major; `G-1`/`G-2`/`G-3`/`G-4`), and Sprint P3.1.7.1 verified every one of those governance findings against repository evidence.

### 1.1 Responsibilities — limited to five

1. Deferred findings
2. ADR references
3. Cross-sprint implementation observations
4. Review dispositions
5. Claim-to-specification mappings

### 1.2 What this register is NOT

Explicitly verified at establishment, and a standing constraint on every future edit:

| Not a… | Because |
|---|---|
| **Roadmap** | It contains no milestone sequence, no dates, no planned direction. `docs/roadmap.md` owns that. |
| **Backlog** | It contains no inventory of intended work. A deferred *finding* records a decision already taken about where a known issue belongs — it is not a work item awaiting scheduling. |
| **Sprint tracker** | It records no sprint status, progress, or completion state. |
| **Task manager** | It contains no tasks, assignees, priorities, or states. |

**The governing test:** every row is retrospective — a decision made, a finding dispositioned, a claim mapped. **If a row describes work to be scheduled, it does not belong here**; it belongs in `docs/roadmap.md` or a sprint brief. Entries are added only *after* a disposition has been established, never in anticipation of one.

---

## 2. Accepted architectural decisions

| ADR | Question | Decision | Sprint | Status |
|---|---|---|---|---|
| [`ADR-0001`](adr/ADR-0001-chunk-persistent-representation.md) | Does Chunk need a separate persistent-representation contract? | No — resolve the container shape inside Serialization Planning | P2.3.0 | Accepted |
| [`ADR-P3.1.7.2-F2`](adr/ADR-P3.1.7.2-F2-corpus-root-containment.md) | Where is corpus-root containment enforced — Construction or Data Quality Validation? | **Option A — Construction** | P3.1.7.2 | **Accepted** (repository owner) |

**Dispositions recorded outside the ADR series.** Two Generation gaps were dispositioned by the Repository Owner in the contract itself rather than by a separate ADR file, and are recorded here so the register remains the single index of accepted decisions. Neither creates an ADR; both cite the frozen authority that carries them.

| Reference | Question | Decision | Sprint | Status |
|---|---|---|---|---|
| `docs/GENERATION_CONTRACT.md` §22, **G-1** | The Generation artifact name | `GenerationResult` approved as the Generation artifact | P3.5.1-G | **Approved** (Repository Owner) |
| `docs/GENERATION_CONTRACT.md` §22, **G-2** | The Milestone 1A runtime interface | `Generator.generate(query, retrieval: RetrievalResult)` approved, in place of `generate(prompt)` | P3.5.1-G | **Approved** (Repository Owner) |

**Consequence recorded, not actioned.** §22 assigns the corresponding `docs/architecture.md` §5 `Generator` row amendment to the Repository Owner, in the manner `docs/MILESTONE_1A.md` build item 4 amended the `Retriever` row. It is unperformed at Sprint P3.7.2 and is carried in `docs/P3.7.2_Repository_Governance_Synchronization_Report.md` §5 as a deferred item, not as a finding.

**Standing governance rule**, established at Sprint P3.1.7.1 and carried forward: architectural disposition is not the implementing agent's decision. An implementing agent presents options and a recommendation; a recommendation is not a decision.

---

## 3. Findings register

### 3.1 F-1 — Duplicate manifest identifiers accepted silently

| | |
|---|---|
| **Raised** | Sprint P3.1.5 (Construction Validation) |
| **Verified** | Sprint P3.1.7.1 — **CONFIRMED**, independently reproduced: a manifest with two entries sharing `id: "dup"` returns two `Document`s sharing that id, no exception |
| **Evidence** | `sample_rag/knowledge_source.py` `load()` — no uniqueness check across entries |
| **Disposition** | **DEFERRED to Sprint P3.1.8 (Data Quality Validation)** — upheld at P3.1.7.1 and unchanged at P3.1.7.2 |
| **Why deferred** | Uniqueness is a collection-level, cross-artifact property. `docs/DOCUMENT_CONTRACT.md` §8.5 routes such checks to Data Quality Validation; it is not among §8.7's three invariants |
| **Coupled to** | **D-2** (§3.6) — **resolved** at Sprint P3.1.8.0B by Contract Erratum E-1 (`docs/DOCUMENT_CONTRACT.md` §8.9). The invariant F-1's check must enforce is now stated, so the check no longer risks inventing one |
| **Implementation** | Contract Erratum E-1 stated the invariant; Sprint P3.1.8.1B shipped the DQ-2 uniqueness specifications at commit `e9405ad`. `sample_rag/knowledge_source.py` is unchanged — a duplicate identifier is **detected** by Data Quality Validation, not **prevented** by `load()` (§8.9 item 5) |
| **Specifications** | `tests/test_data_quality.py` — 4 DQ-2 specifications: W2 predicates A and B, each with a synthetic duplicate-id case reproducing this finding's recorded shape |
| **Mutation evidence** | §6 — mutants **M20**, **M21**, **M22** killed by the DQ-2 specifications. **M21** is killed by `test_dq2_loaded_document_ids_are_pairwise_distinct`, the predicate the specification records as vacuous on the one-document corpus: it is vacuous against a duplicate *Manifest entry*, not against a `load()` that duplicates a `Document` |
| **Status** | **Closed** at Sprint P3.1.8.4, under the event-driven closure policy (§8). The trigger this entry documented — *"Sprint P3.1.8.1 ships the DQ-2 uniqueness specification"* — occurred at `e9405ad`. Sprint P3.1.8.1's own completion remains governed independently by `docs/DATA_QUALITY_VALIDATION_PLAN.md` §13 |

### 3.2 F-2 — Corpus-root containment not enforced

| | |
|---|---|
| **Raised** | Sprint P3.1.5 (Construction Validation) |
| **Verified** | Sprint P3.1.7.1 (EV-3) — **CONFIRMED**, both vectors reproduced: an absolute `documents[].source` and a `..` relative escape each loaded a file from outside `sample_rag/` and returned its contents as `Document.text` |
| **Disputed** | Codex review → defer to P3.1.8. Claude Code review → Construction, remediate first. P3.1.7.1 declined to resolve and escalated it |
| **Disposition** | **RESOLVED at Sprint P3.1.7.2** by [`ADR-P3.1.7.2-F2`](adr/ADR-P3.1.7.2-F2-corpus-root-containment.md), Option A — Construction |
| **Implementation** | `resolve_source_path` rejects an escaping source as an Input failure (§10.1) |
| **Specifications** | `tests/test_knowledge_source_failures.py` — 6 AH-7 specifications |
| **Status** | **Closed** |

### 3.3 Findings dispositioned at Sprint P3.1.7.2

Every finding the Sprint P3.1.7.1 Decision Gate classified as CONFIRMED, with the repository change that resolved it.

| Finding | Decision Gate status | Change | Evidence of closure |
|---|---|---|---|
| **EV-2 / I-1** — `Document.text` content unspecified; a mutation emptying it left 77/77 passing | CONFIRMED | AH-1: 4 content specifications (`.docx`, `.md`, `.txt` round-trips; real-corpus substantive-text) | Mutation `w:t findall` (empties text) now **KILLED**, 5 failures |
| **EV-1 / I-2** — rule N1 unprotected; 86 blocks → 1, Chunker driven to fallback | CONFIRMED | AH-2: 3 specifications including the full `.docx` → N1 → `Document.text` → Chunk-boundary chain | Mutation `PARAGRAPH_SEPARATOR="\n"` now **KILLED**, 4 failures |
| **EV-3 / A-2** — corpus-root containment | CONFIRMED | AH-7 (see §3.2) | Removing the check → **KILLED**; weakening it to absolute-only → **KILLED** |
| **EV-4 / D-1** — P3.1.5 evidence report not valid UTF-8 | CONFIRMED (escalated) | AH-5: structural restoration + Restoration Record | File is valid UTF-8; 6 structural hunks, **zero prose changes** |
| **I-3** — unreachable defensive guard, module's only uncovered line | CONFIRMED | AH-8: guard removed | `sample_rag/knowledge_source.py` coverage **100%** |
| **I-4** — no synthetic `.docx` success spec; `.md` never exercised | CONFIRMED | AH-1 (covers both) | `SyntheticCorpus.docx()` now invoked; `.md` fixture added |
| **I-5** — empty-text legality unspecified through `load()` | CONFIRMED | AH-3: 4 specifications | Mutation rejecting empty text now **KILLED** |
| **A-1** — `SUPPORTED_EXTENSIONS` duplicated, no spec asserting agreement | CONFIRMED | AH-9: cross-boundary equality specification | Widening one definition now **KILLED** |
| **D-3** — normalization rules existed only in source | CONFIRMED | AH-4: `DOCUMENT_CONSTRUCTION_PLAN.md` §20.1 | N1–N5 documented with rationale |
| **D-5** — "full plain-text content" vs. a normalizing extractor | CONFIRMED | AH-4: §20.2 clarification | Recorded as clarification, contract unchanged |
| **D-4** — plan status and §14.2 sync list stale | CONFIRMED | AH-6: status header + §14.2 corrected | Sync items marked complete at `8839802` |
| **G-1** — Decision Register never closed | CONFIRMED | §20.3 closure table | All Sprint-P3.1 decisions closed |
| **G-2** — P3.1.5 evidence committed under the P3.1.6 commit | CONFIRMED | Recorded in the Restoration Record and §5 below | Provenance documented |
| **G-4** — no mutation or coverage evidence in the repository | CONFIRMED | §6 below | Baseline recorded |

### 3.4 Findings closed without repository change

| Finding | Disposition | Rationale |
|---|---|---|
| **NEW-2** — "6 of 18 mutants survive" overstated the specification gap | **PARTIALLY CONFIRMED**, no change | Sprint P3.1.7.1 established M10 and M14 as **equivalent mutants** (see §6). The correction is the action |
| **NEW-1** — Codex's claim that the specifications "protect the approved behavior" | **REJECTED**, no change | Not supported: that review performed no mutation testing, and EV-1/EV-2 disprove the claim as unqualified. Its other findings each verified independently. A review report is an input, not a repository artifact |
| **D-6 / P3.1.7-DOC-01** — contract retains "proposed" wording | Confirmed, **no action** | Cosmetic; already self-disclosed in the contract's own Correction Record. §8.2–§8.7 are deliberately byte-for-byte frozen |
| **G-5** — dependency governance gate | Confirmed **closed correctly** | Construction is stdlib-only; `requirements.txt` unchanged, so §12.3 step 2 was never owed |
| **A-4** — no injection seam for the corpus root | **REJECTED as actionable** | Design observation; no defect observed at current scope |

### 3.5 Open findings and observations

Recorded because they have a disposition, not because they are scheduled.

**On the `M2.01B-F-1` identifier.** Sprint-report findings are numbered per report, so M2.01B's **F-1** is not this register's **F-1** (§3.1, duplicate manifest identifiers) and its **F-2** is not §3.2 (corpus-root containment). The row below is therefore qualified by its originating sprint, following the qualification this table already uses for `F-2-sym` and `P3.1.7-ARCH-01`. **The four §3.1 / §3.2 records keep their identifiers unchanged** — CP-3 governs, and nothing historical is renumbered.

| ID | Observation | Disposition |
|---|---|---|
| **F-2-sym** | Containment reads the manifest value, so a corpus file that is a **symlink** pointing outside the root is not detected | Deliberate boundary of `ADR-P3.1.7.2-F2`. Candidate for Data Quality Validation if evidence ever emerges; none exists today |
| **I-6** | `test_b6` hardcodes the corpus filename `Karthik_SR_Resume_v2_2.docx` | Re-verify at corpus expansion |
| **I-7** | `test_a15`'s allowlist tracks CPython-synthesized dataclass members (`__firstlineno__`, `__static_attributes__` are 3.13+; suite runs on 3.12) | Re-verify at the next CPython upgrade |
| **A-3** | `discover_manifest_entries` performs admissibility checks bounded only by a docstring against growing into a second `validate_manifest` | Re-inspect if that function grows |
| **P3.1.7-ARCH-01** | JobOps-as-`Document` classification unresolved (Contract Outstanding Question 3) | Intentionally deferred; structurally excluded today by the manifest discovery gate |
| **M2.01B-F-1** | **Index embedding-provider provenance.** `Index` (`sample_rag/indexer.py`) does not intrinsically carry embedding-model/provider identity — it holds `vectors`, `dimension` and `stub`, and nothing recording what embedded them. A caller can therefore theoretically pair an Index built by one provider with a different provider at persistence time, and record a false model identity in the vector-index metadata | **Future hardening — not a current defect.** No repository path exhibits it: the one production caller supplies the same provider it indexed with, and `docs/architecture.md` §7 freezes `EmbeddingProvider` at a single `embed` method, so M2.01B read identity defensively via `getattr` rather than growing the seam. Revisit whether provider/model identity should become part of the Index contract, so a mismatched provider/index pairing is detectable rather than merely improbable. **No implementation is owed by this entry**, and it allocates no capability and changes no milestone. Surfaced as finding **F-1** of `docs/M2.01B_FAISS_VectorStore_Foundation_Report.md` §15; recorded here at Sprint RO-09 |
| **M2.03-F-1** | **BM25 length normalization interacts badly with header-sized chunks.** The structure-aware chunker emits section headers as their own chunks — 48 of 259 chunks are ≤ 3 tokens, against a corpus mean of 17.2 — while the Evidence Trace Dataset's expected-evidence chunks average 37.6 tokens. With `b = 0.75`, BM25's length normalization can therefore rank a short header carrying one query term above a substantially longer body chunk carrying more query terms, and retrieval quality against the 22 committed expectations fell (hit rate 0.7273 → 0.4091; Chunk Precision@K micro 0.1481 → 0.0833) even though the ranking function is correct | **Corpus/tuning finding, not a BM25 defect** — every reported score is independently verified against the published formula (`tests/test_lexical_bm25.py`). **M2-04 is the next architectural checkpoint for this finding**, because it combines the independently validated semantic and lexical routes through RRF; the M2.03 evidence demonstrates that the routes have complementary retrieval characteristics, including cases where BM25 cannot recover paraphrased evidence that the semantic route can. **However, M2-04 is NOT designated by this entry as a guaranteed remedy.** Whether RRF actually improves, partially recovers, or fails to recover the observed regression must be established by M2-04's own implementation and retrieval-quality evidence. If the finding remains materially unresolved after M2-04, the appropriate subsequent candidates remain **M2-15** — retrieval-quality optimization, including `k1`/`b` tuning against an appropriate quality signal rather than tuning directly against the current 22-question Evidence Trace benchmark — and **M2-17** — chunk-size/granularity revision addressing the underlying corpus structure. **Revisit M2.03-F-1 after Sprint M2-04 completes and its own retrieval-quality measurements are available.** **No capability is allocated by this finding**, and **no implementation is owed by this entry**: **M2-15 and M2-17 remain independently scoped** in `docs/DEFERRED_ITEMS_REGISTER.md` §4, and neither is triggered automatically by this entry. Surfaced as finding **F-1** of `docs/M2.03_Real_BM25_Lexical_Retrieval_Report.md` §15; recorded here at Sprint RO-11 |

**On M2.03-F-1's four levels of claim**, kept deliberately distinct because collapsing them would convert a measurement into a plan:

| Level | Statement |
|---|---|
| **Fact** | BM25 currently performs worse on the committed 22-question benchmark than the distinct-term overlap scorer it replaced |
| **Fact** | The degradation has a demonstrated relationship to the corpus chunk-length distribution and BM25's length normalization — a sweep over `b` alone, holding the implementation fixed, is monotone (`docs/M2.03_…` §15 F-1) |
| **Fact** | The BM25 scores are mathematically correct for the selected formula, verified by independent recomputation rather than by asserting the implementation against itself |
| **Architectural hypothesis — not yet proven** | That fusing the semantic and lexical routes at **M2-04** recovers some of the regression. M2-04 is where this is **tested**, not where it is assumed; **M2-15** and **M2-17** are future options if the finding survives that test |

### 3.6 D-2 — Contract inconsistency on `Document.id` uniqueness

| | |
|---|---|
| **Raised** | Sprint P3.1.7 (`docs/P3.1.7_Independent_Implementation_Review_ClaudeCode.md`, **MAJOR**) |
| **Verified** | Sprint P3.1.7.1 — **Independently Verified**; routed to Sprint P3.1.8 together with F-1 |
| **Previously carried in** | §3.5 (Open findings), until resolution moved it here. `docs/DOCUMENT_CONTRACT.md` §8.9 cites §3.5, the location current when Erratum E-1 was authored |
| **Evidence** | `docs/DOCUMENT_CONTRACT.md` §8.3 states `id` "is unique across the corpus"; §8.7's invariant list, declared complete, omits uniqueness. `sample_rag/knowledge_source.py` `load()` follows the weaker reading |
| **Analysed** | Sprint P3.1.8.0A (Governance Analysis) — five governance mechanisms evaluated against repository evidence; **Option A (Scoped Contract Erratum)** recommended with **Interpretation I-C** (corpus-scoped uniqueness inherited from the Knowledge Manifest, recorded adjacently) |
| **Disposition** | **RESOLVED at Sprint P3.1.8.0B** by **Contract Erratum E-1**, approved by the repository owner |
| **Implementation** | `docs/DOCUMENT_CONTRACT.md` §8.9 records the guarantee as binding, corpus-scoped, inherited from `docs/MILESTONE_1A.md` build item 1, and enforced by Data Quality Validation. §8.2–§8.8 verified byte-for-byte unchanged; `Contract Version` remains `1.0`; no ADR created |
| **Coupled to** | **F-1** (§3.1) — the invariant a DQ-2 check must enforce is now stated, satisfying the precondition that the check enforce a stated invariant rather than invent one. F-1 itself closed at Sprint P3.1.8.4 |
| **Status** | **Closed** |

### 3.7 P3.1.8.2-D1 — DQ-4 synthetic negative case not constructible under identity strategy S1

| | |
|---|---|
| **Raised** | Sprint P3.1.8.2 (Data Quality Validation Layer Review) |
| **Verified** | Sprint P3.1.8.3 (Governance & Evidence Verification) — `docs/DATA_QUALITY_VALIDATION_PLAN.md` §13's criterion *"Each check has a synthetic negative case **and** a real-corpus positive case"* is explicit and unqualified; DQ-4 is a check by §8.1 and §11.2 W5; W5 ships a synthetic **positive** case only. The criterion is therefore unmet as written |
| **Evidence** | `sample_rag/knowledge_source.py` `load()` iterates `discover_manifest_entries()`, reads `document_id = entry["id"]` and passes it through unchanged under identity strategy S1 (`docs/DOCUMENT_CONSTRUCTION_PLAN.md` §20.3; `docs/DOCUMENT_CONTRACT.md` §8.4, A5), and appends exactly one `Document` per entry. A `Document.id` with no corresponding `documents[]` entry is unreachable through repository execution at any corpus size |
| **Architectural reasoning** | DQ-4's failure state cannot be exercised without fabricating a state the repository cannot produce, which would specify a fiction rather than repository behaviour. `docs/DATA_QUALITY_VALIDATION_PLAN.md` §12's negative-case examples name a duplicate id, a stale hash, and an unmanifested file — DQ-1, DQ-2, DQ-3 — and do not name DQ-4. This is distinct from §16 open item **O-5**, which records DQ-4 as vacuously true for the separate reason of corpus scale (one document). Both limits are real and neither substitutes for the other |
| **Disposition** | **Owner-approved governance deviation, Sprint P3.1.8.4.** A literal DQ-4 synthetic negative case is determined **not constructible** under S1. The §13 synthetic-negative criterion is waived for DQ-4 alone. No artificial, synthetic, or otherwise non-representative DQ-4 negative specification is to be introduced |
| **What protects DQ-4 instead** | Regression protection against a change of identity strategy, **measured rather than asserted**: §6 records mutants **M20** (`Document.id` derived rather than read), **M21** (each entry yields two `Document`s), and **M22** (enumeration truncated) as **KILLED** by the DQ-4 specifications |
| **Scope** | DQ-4 only. DQ-1, DQ-2, and DQ-3 each retain a synthetic negative case, and §13's criterion is unmodified for them |
| **Recorded in the implementation** | `tests/test_data_quality.py` cites this section as the decision's authoritative record rather than carrying it in a module docstring — the defect class §1 records this register as having been established to end |
| **Status** | **Closed** |

---

## 4. Review dispositions

| Review | Verdict | Disposition |
|---|---|---|
| `docs/DOCUMENT_CONTRACT_REVIEW.md` (P2.5) | Outcome A — APPROVED | Findings F1, F4–F8 applied at P2.5.1; F2 → Construction Plan §9, F3 → §12 |
| `docs/P3.1.7_Independent_Implementation_Review_Codex.md` | APPROVED WITH OBSERVATIONS | Accepted except its unqualified specification-adequacy claim (§3.4, NEW-1). `P3.1.7-IMPL-01` superseded by `ADR-P3.1.7.2-F2` |
| `docs/P3.1.7_Independent_Implementation_Review_ClaudeCode.md` | CHANGES REQUESTED | Accepted, with its mutation-survivor count corrected (§3.4, NEW-2). All three required items closed at P3.1.7.2 |
| `docs/P3.1.7.1_Decision_Gate_Report_Evidence_Verification.md` | Decision Gate | Authority for every change made at Sprint P3.1.7.2 |
| `docs/P3.7.0_Manual_Review_Evidence.md` (P3.7.0) | Evidence record — not a verdict | The committed verbatim terminal transcript of the Repository Owner's manual review of commit `b50e45f`. Completes `docs/MILESTONE_1A.md` build item 10. Assessed, not re-run, by P3.7.1 |
| `docs/P3.7.1_Manual_Review_Report.md` (P3.7.1) | **Milestone 1A READY FOR Repository Governance Synchronization** | Accepted. 24 of 24 verification items PASS, 0 FAIL. Findings 1 and 2 dispositioned as confirmations of previously-diagnosed, contract-conforming accepted limitations, each linked to the authority that already records it. **No backlog item created** (§7 of that report) |

**Recorded divergence.** The two P3.1.7 reviews reached opposite verdicts. Sprint P3.1.7.1 traced the divergence to a single methodological difference — **one review measured specification adequacy; the other asserted it**. Retained as a standing lesson: an adequacy claim about a specification suite requires measurement.

---

## 5. Cross-sprint implementation observations

| Observation | Evidence | Status |
|---|---|---|
| `SUPPORTED_EXTENSIONS` is **deliberately duplicated** in `sample_rag/knowledge_source.py` and `scripts/build_manifest.py`. Centralizing would require `sample_rag/` → `scripts/` import (barred by `docs/architecture.md` §6) or a new shared module (a new architectural concept without the evidence bar `ADR-0001` applied) | Construction Plan §9.1 rated this pattern **High** drift risk when rejecting identity strategy S3 | Accepted, and now **enforced by specification** (AH-9) rather than by convention |
| No Sprint P3.1.5 commit exists; its evidence report was first committed under `5b903db`, the Sprint P3.1.6 commit, while the report's own §12 states "Repository Impact: None" | `git log --diff-filter=A` | Recorded (G-2). Documented in the report's Restoration Record |
| Construction depends on the Manifest artifact at runtime — an accepted consequence of identity strategy S1 | Construction Plan §9.1 | Accepted |
| The terminal-capture path that damaged the P3.1.5 report is still active: `docs/P3.1.7.1_Decision_Gate_Report_Evidence_Verification.md` carries 2 truncated box-drawing characters in decorative borders | Verified at Sprint P3.1.7.2 | Inert — no finding, evidence, or disposition affected. Relevant when capturing future reports |
| **No Sprint P3.3.1 commit and no Sprint P3.3.1 report exist.** The Retrieval Runtime it produced — `sample_rag/retriever.py` and `scripts/run_retrieval.py` — was first committed under `dfe1b5b`, the Sprint P3.3.2 commit. `docs/P3.3.2_Retrieval_Evaluation_Report.md` §1 records the two files as untracked at that sprint's start, *"left uncommitted because P3.3.1 also barred Git operations"* | `git log --diff-filter=A -- sample_rag/retriever.py`; P3.3.2 §1 | Recorded at Sprint P3.7.2. **Same defect class as G-2** (P3.1.5 evidence committed under the P3.1.6 commit). The runtime's own module docstring names Sprint P3.3.1, and P3.3.2 §§1, 5.4 cite its observations, so provenance is recoverable from committed artifacts — but from no single report |
| `docs/P3.3.5_Evaluation_Record_Enrichment_Report.md`'s file-impact table states 9 specifications added to `tests/test_retrieval_evaluation.py` and 8 to `tests/test_retrieval_diagnosis.py`. The measured deltas across `439e2a7`…`1b568f3` are **+8** and **+9** respectively | `diff` of `def test_` names between the two commits; totals at HEAD are 35 and 47 | Recorded at Sprint P3.7.2, **historical report unchanged**. The two counts are transposed; their sum (17) and every verdict in that report are unaffected |
| `documents[].indexed` is `false` for both catalogued documents, while `sample_rag/chunks.json` carries 172 chunks derived from them and `docs/P3.3.5_…` §4 reasons that the expected document *"demonstrably **is** indexed"* | `sample_rag/knowledge_manifest.json`; `docs/MILESTONE_1A.md` build item 1 schema; `docs/P3.3.5_…` §4, §5 | Recorded at Sprint P3.7.2. The field's semantics under a chunk-only Index stage are unresolved; regeneration of the Manifest is barred by that sprint's scope. Carried as a deferred item in `docs/P3.7.2_Repository_Governance_Synchronization_Report.md` §5 |
| The **Index Layer** named by `docs/MILESTONE_1A.md` build item 3 — deterministic placeholder vectors behind an `EmbeddingProvider` interface — does not exist. No `Indexer`, `EmbeddingProvider` or `VectorStore` is defined anywhere in the repository; the only occurrence of the name is a docstring in `tests/test_data_quality.py` recording the blocker | `grep -rn "EmbeddingProvider" --include=*.py`; `docs/DATA_QUALITY_VALIDATION_PLAN.md` §8.1 (DQ-7), §11.2 W6, §16 O-6 | **Previously recorded**, by the DQV plan, as the blocker for DQ-7 and for build item 2's Index Coverage Validation clause. Re-verified unchanged at Sprint P3.7.2 and carried in that sprint's Deferred Repository Items Register |

---

## 6. Specification adequacy baseline

Recorded so the figure is not re-cited without its qualification (finding G-4).

**Mutation baseline — Sprint P3.1.7.1**, 18 semantically meaningful mutations against commit `5b903db`: 12 killed, 6 survived. Sprint P3.1.7.1 established that the survivor count **overstated** the gap:

| Survivor | Classification |
|---|---|
| `PARAGRAPH_SEPARATOR "\n\n"→"\n"` | Genuine blind spot → closed by AH-2 |
| `paragraph.iter(w:t)`→`findall` | Genuine blind spot → closed by AH-1 |
| reject empty text in `load()` | Unspecified legality → closed by AH-3 |
| remove unreachable non-`str` guard | Dead code; survival expected → resolved by AH-8 |
| `newline=""` removed from `extract_text` | **Equivalent mutant** — final `Document.text` is byte-identical; only the intermediate raw string differs |
| `body.iter(w:p)`→`findall` | **Equivalent mutant on the current corpus** — the resume has 0 nested paragraphs (86 via both). Becomes a genuine gap only if the corpus gains tables or text boxes |

**Post-remediation, Sprint P3.1.7.2:** every genuine mutant is killed. The only survivors are the two equivalent mutants above, whose survival is correct behaviour.

**Mutation baseline — Data Quality Validation, Sprint P3.1.8.4**, 23 semantically meaningful mutations against commit `3a32253`, satisfying `docs/DATA_QUALITY_VALIDATION_PLAN.md` §12 (*"must run a mutation pass over any code its checks protect and record the result"*) and §13's Evidence criterion.

**Scope**, fixed before execution and not broadened: `scripts/build_manifest.py` — `load_manifest`, `validate_manifest`, `compute_sha256`, `discover_documents`, `normalize_source_path`; `sample_rag/knowledge_source.py` — `resolve_source_path`, `load()`. Every mutation lies inside one of those seven function bodies. Mutants were applied to a throwaway copy of the repository, one at a time, with the source restored between runs; the working tree was never mutated.

Each mutant was run twice — against the **DQV suite alone** (`tests/test_data_quality.py`) and against the **full suite** — so protection attributable to W1–W5 is distinguished from protection the repository already had:

| | Count |
|---|---|
| Mutants generated | **23** |
| Killed by the DQV suite alone | **11** — M01, M04, M06, M07, M09, M10, M13, M18, M20, M21, M22 |
| Killed by the full suite | **14** — the 11 above, plus M17, M19, M23 |
| Survived both | **9** |
| — of which **equivalent mutants** | **5** |
| — of which **genuine survivors outside DQV's scope** | **4** |
| — of which **genuine survivors inside DQV's scope** | **0** |

| Survivor | Function | Classification |
|---|---|---|
| M02 `path.suffix.lower()` → `path.suffix` | `discover_documents` | **Equivalent on the current corpus** — every corpus file and every synthetic fixture carries a lowercase extension. A genuine gap only if a file with an uppercase extension enters the corpus |
| M03 hidden / `__pycache__` skip removed | `discover_documents` | **Equivalent on the current corpus** — `sample_rag/documents/**` contains no hidden or `__pycache__` path |
| M05 `as_posix()` → `str(...)` | `normalize_source_path` | **Equivalent on POSIX** — the two agree when the OS separator is `/`; the suite runs on Linux. A genuine gap on Windows |
| M08 read chunk size 8192 → 1 | `compute_sha256` | **Equivalent, unconditionally** — SHA-256 is a streaming digest; chunking changes performance, never the value |
| M11 read encoding `utf-8` → `latin-1` | `load_manifest` | **Equivalent on the current artifact** — `knowledge_manifest.json` is pure ASCII, where the two decodings coincide. A genuine gap if a non-ASCII byte enters the Manifest |
| M12 JSON parse failure no longer wrapped | `load_manifest` | **Genuine survivor, outside DQV's scope.** Manifest load/parse failure is a `ManifestValidationError` concern, listed at plan §8.2 under *"Explicitly **not** DQV failure classes"* and owned by Structural Artifact Validation |
| M14 `manifest_version` equality check removed | `validate_manifest` | **Genuine survivor, outside DQV's scope** — same §8.2 assignment |
| M15 per-entry field type check removed | `validate_manifest` | **Genuine survivor, outside DQV's scope** — same §8.2 assignment |
| M16 missing-`documents` guard removed | `validate_manifest` | **Genuine survivor, outside DQV's scope** — same §8.2 assignment |

**No genuine survivor lies inside a DQV-owned behaviour.** The four genuine survivors are all manifest *structural* failures, which plan §8.2 assigns to Structural Artifact Validation and §11.2 records against W1 as failure classes *"—"*. They are a measured confirmation that W1 is a gate call and not a structural-failure specification, not a DQV blind spot.

**Boundary confirmation, in the other direction.** Three mutants were killed by the full suite but survived the DQV suite, each correctly:

| Mutant | Survived DQV because | Killed by |
|---|---|---|
| M17 corpus-root containment removed | Containment is Construction's, per `ADR-P3.1.7.2-F2`; plan §5.5 and §11.3 bar DQV from specifying it | AH-7 |
| M19 extension gate removed | Construction's single-entry admissibility gate (§6.1 row 2) | Construction failure surface |
| M23 manifest order reversed | Ordering is Construction Behaviour; §11.3 bars DQV from re-specifying it. W5 asserts cardinality, not order | B9 / B10 |

**Protection attributable to each work package**, by killed mutant: **W1** — M13 (the gate must return the same object, not a copy). **W3 / DQ-1** — M07, M09, M10, M18. **W4 / DQ-3** — M01, M04, M06. **W2 / DQ-2** — M18, M20, M21, M22. **W5 / DQ-4** — M18, M20, M21, M22.

**One measured correction to a recorded limitation.** `tests/test_data_quality.py` records W2 as vacuously true on the one-document corpus. M21 (`load()` appends two `Document`s per entry) is killed by `test_dq2_loaded_document_ids_are_pairwise_distinct`. The predicate is therefore vacuous against a duplicate *Manifest entry* — the F-1 shape — but not against a `load()` that duplicates a `Document`. The recorded limitation is narrower than stated, in the repository's favour.

**Line coverage:** `sample_rag/document.py` 100%, `sample_rag/knowledge_source.py` 100%.

### 6.1 Later mutation rounds — added at Sprint P3.7.2

Recorded from the sprint reports that produced them. Each figure is that sprint's own; none is re-derived here, and none is a repository-wide adequacy claim.

| Sprint | Scope | Mutants | Killed | Survived | Recorded in |
|---|---|---|---|---|---|
| **P3.4.1** — Dataset authority validation | Golden Dataset, QA pairs, Evidence Trace, cross-dataset integrity, mutated in memory | 34 | **34** | 0 | `docs/P3.4.1_Dataset_Authority_Validation_Report.md` §Mutation evidence |
| **P3.5.2** — Generation runtime | `sample_rag/generator.py`, via mutant results and mutant `Generator` subclasses in memory | 25 | **25** | 0 | `docs/P3.5.2_Generation_Implementation_Report.md` §Mutation evidence |
| **P3.6.0** — CLI integration | `scripts/cli.py`, structural mutants against the module source and behavioural mutants executed as real processes | 25 | **25** | 0 | `docs/P3.6.0_CLI_Integration_Report.md` §Mutation evidence |

**No repository file was modified during any of the three rounds** — each report records the isolation mechanism it used.

**Two consecutive rounds found a defect in a specification rather than in an implementation**, and both were fixed and re-verified before the sprint closed: P3.5.2's §12 varying-value scan missed the `created_at` key (killed independently by the exact-key `diagnostics` check, so coverage never had a hole); P3.6.0's authority-import check was written to skip docstrings and was thereby skipping the imports it existed to inspect, and its orchestration check accepted any assignment binding a call. Recorded because it qualifies the figures above in the direction the standing caution already warns about — **the validation layer is itself under test, and twice it was the thing that failed.**

**No mutation round was performed for Sprints P3.3.2, P3.3.3, P3.3.4 or P3.3.5.** Those sprints used **two-path independence** instead — an engine and a validator that share no import, each computing the same quantity by a different route (`docs/P3.3.3_…` §Validation, `docs/P3.3.4_…` §Independence), with the independence itself enforced by AST specifications. That is a different instrument, not a weaker application of the same one, and it is not interchangeable with a mutation figure.

**Standing caution:** a surviving mutant is evidence of a blind spot; a killed mutant is not proof of adequacy. Line coverage is not evidence of behavioural protection — at Sprint P3.1.7.1 the module measured 99% while a mutation emptying its entire output went undetected.

---

## 7. Claim-to-specification mapping

**372 specifications at commit `d9a6db4`**, collected read-only at Sprint P3.7.2 and matching the count `docs/P3.7.0_Manual_Review_Evidence.md` lines 1–5 record as passing. The register carried **109** when it was written at Sprint P3.1.7.2 — 17 pre-existing (`test_chunker.py`), 78 Knowledge Layer, 14 Data Quality Validation — and §7.1 records the 263 added since, by owning sprint.

The table below is unchanged from establishment and continues to map the original 109.

| Claim family | Source | Specifications | File |
|---|---|---|---|
| Runtime Contract A1–A16 | P3.1.5 Layer A | 22 | `tests/test_document_contract.py` |
| Construction Behaviour B2–B10, invariant 3 | P3.1.5 Layer B | 16 | `tests/test_knowledge_source_construction.py` |
| Failure surface (18 modes, Case B, error-type independence) | P3.1.5 §8 | 22 | `tests/test_knowledge_source_failures.py` |
| **AH-1** `Document.text` content | Decision Gate EV-2, I-4 | 4 | `tests/test_knowledge_source_construction.py` |
| **AH-2** rule N1 and Chunk-boundary chain | Decision Gate EV-1 | 3 | `tests/test_knowledge_source_construction.py` |
| **AH-3** empty-text legality | Decision Gate I-5 | 4 | `tests/test_knowledge_source_construction.py` |
| **AH-7** corpus-root containment | `ADR-P3.1.7.2-F2` | 6 | `tests/test_knowledge_source_failures.py` |
| **AH-9** admissibility-gate agreement | Decision Gate A-1 | 1 | `tests/test_knowledge_source_failures.py` |
| **W1** Manifest structural gate | DQV Plan §11.2; `docs/MILESTONE_1A.md` build item 1 | 3 | `tests/test_data_quality.py` |
| **W2 / DQ-2** identifier uniqueness (F-1) | DQV Plan §11.2; `docs/DOCUMENT_CONTRACT.md` §8.9 (Erratum E-1) | 4 | `tests/test_data_quality.py` |
| **W3 / DQ-1** freshness / integrity | DQV Plan §11.2; `docs/MILESTONE_1A.md` build item 1, Architectural AC 3 | 2 | `tests/test_data_quality.py` |
| **W4 / DQ-3** completeness — Case A | DQV Plan §11.2, §8.3; `docs/DOCUMENT_CONSTRUCTION_PLAN.md` §20.3 | 2 | `tests/test_data_quality.py` |
| **W5 / DQ-4** referential integrity | DQV Plan §11.2; `docs/DOCUMENT_CONTRACT.md` §8.5 (A8) | 3 | `tests/test_data_quality.py` |

**Not specified, deliberately:** symlink containment (§3.5, F-2-sym); `Document` persistence and structural validation (unresolved by the contract); a DQ-4 synthetic negative case (§3.7, **P3.1.8.2-D1** — owner-approved governance deviation).

### 7.1 Specifications added after establishment — recorded at Sprint P3.7.2

263 specifications across six families, each attributed to the sprint that shipped it. Counts are the collected count at `d9a6db4`; where a sprint report states a different figure, both are shown and the divergence is recorded in §5.

| Claim family | Owning sprint(s) | Specifications | File |
|---|---|---|---|
| **Retrieval evaluation** — classification algebra, pairing, validation checks, committed corpus | P3.3.2 (27), **+8** at P3.3.5 for document identity | **35** | `tests/test_retrieval_evaluation.py` |
| **Retrieval metrics** — metric algebra, input contract, two-path independence, committed corpus | P3.3.3; unchanged at P3.3.5 | **35** | `tests/test_retrieval_metrics.py` |
| **Retrieval diagnosis** — rule transcription against `docs/altm.md`, rule selection, confidence, dependency rule, independence, committed corpus | P3.3.4 (38), **+9** at P3.3.5 | **47** | `tests/test_retrieval_diagnosis.py` |
| **Golden Dataset** — GD-1 … GD-13 | P3.4.1 | **16** | `tests/test_golden_dataset.py` |
| **QA pairs** — QA-1 … QA-10 | P3.4.1 | **14** | `tests/test_qa_pairs.py` |
| **Evidence Trace Dataset** — ET-1 … ET-6 | P3.4.1 | **25** | `tests/test_evidence_trace_dataset.py` |
| **Cross-dataset integrity** — X-1 … X-16 | P3.4.1 | **16** | `tests/test_cross_dataset_integrity.py` |
| **Generation** — `docs/GENERATION_CONTRACT.md` §16, guarantees G-1 … G-14, every guarantee mapped | P3.5.2 | **48** | `tests/test_generator.py` |
| **CLI integration** — contract behaviour, byte-identity, exit codes, and six AST specifications constraining what the module may contain and import | P3.6.0 | **27** | `tests/test_cli.py` |

**Reconciliation:** 109 (§7) + 263 (§7.1) = **372**, the collected total at `d9a6db4`. Sprint P3.4.1's four dataset families complete `docs/MILESTONE_1A.md` build item 9.

**Two claim families in §7.1 are enforced structurally rather than behaviourally** and are recorded as such so the distinction is not lost: the CLI's *"contains no business logic"* property and the metrics/diagnosis validators' import independence are AST-parsed allowlist specifications. A behavioural test cannot observe a branch being added; these can.

---

## 8. Maintenance

- Add a row only **after** a disposition is established.
- **Finding closure is event-driven** (policy adopted at Sprint P3.1.8.4). A finding closes when the implementation trigger its own entry documents occurs — not when the sprint carrying that work is judged complete. Sprint completion is governed independently, by that sprint's own acceptance criteria. Applied first to F-1 (§3.1).
- Every row cites repository evidence — a file, a commit, a measurement, or an ADR.
- A finding is never removed. It moves to Closed, with the change that closed it.
- If a row would describe work to be scheduled, it belongs in `docs/roadmap.md` instead (§1.2).
- **Governance synchronization does not create dispositions.** Sprint P3.7.2 added §2's non-ADR disposition table, two §4 review rows, four §5 observations, §6.1 and §7.1 — every one of them a record of something a committed authority had already established. Where P3.7.2 found deferred work, it recorded it in its own Deferred Repository Items Register, **not here**: a deferred item awaiting a Repository Owner sequencing decision is scheduled work, which §1.2 bars from this register.
