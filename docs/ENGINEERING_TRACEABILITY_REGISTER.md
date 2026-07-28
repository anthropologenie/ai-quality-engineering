# Engineering Traceability Register

**Repository:** `ai-quality-engineering`
**Status:** Active — established at Sprint P3.1.7.2 (Assurance Remediation)
**Scope at establishment:** Knowledge Layer (Milestone 1A). Later layers are added as their decisions are dispositioned.

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
| **Coupled to** | **D-2** below — must be resolved together |
| **Status** | Open |

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

| ID | Observation | Disposition |
|---|---|---|
| **F-1** | Duplicate manifest identifiers (§3.1) | Sprint P3.1.8 |
| **D-2** | `docs/DOCUMENT_CONTRACT.md` §8.3 states `id` "is unique across the corpus"; §8.7's invariants omit uniqueness. The implementation follows the weaker reading | Reconcile **with F-1** at Sprint P3.1.8, *before* implementing a uniqueness check, so the check enforces a stated invariant rather than inventing one |
| **F-2-sym** | Containment reads the manifest value, so a corpus file that is a **symlink** pointing outside the root is not detected | Deliberate boundary of `ADR-P3.1.7.2-F2`. Candidate for Data Quality Validation if evidence ever emerges; none exists today |
| **I-6** | `test_b6` hardcodes the corpus filename `Karthik_SR_Resume_v2_2.docx` | Re-verify at corpus expansion |
| **I-7** | `test_a15`'s allowlist tracks CPython-synthesized dataclass members (`__firstlineno__`, `__static_attributes__` are 3.13+; suite runs on 3.12) | Re-verify at the next CPython upgrade |
| **A-3** | `discover_manifest_entries` performs admissibility checks bounded only by a docstring against growing into a second `validate_manifest` | Re-inspect if that function grows |
| **P3.1.7-ARCH-01** | JobOps-as-`Document` classification unresolved (Contract Outstanding Question 3) | Intentionally deferred; structurally excluded today by the manifest discovery gate |

---

## 4. Review dispositions

| Review | Verdict | Disposition |
|---|---|---|
| `docs/DOCUMENT_CONTRACT_REVIEW.md` (P2.5) | Outcome A — APPROVED | Findings F1, F4–F8 applied at P2.5.1; F2 → Construction Plan §9, F3 → §12 |
| `docs/P3.1.7_Independent_Implementation_Review_Codex.md` | APPROVED WITH OBSERVATIONS | Accepted except its unqualified specification-adequacy claim (§3.4, NEW-1). `P3.1.7-IMPL-01` superseded by `ADR-P3.1.7.2-F2` |
| `docs/P3.1.7_Independent_Implementation_Review_ClaudeCode.md` | CHANGES REQUESTED | Accepted, with its mutation-survivor count corrected (§3.4, NEW-2). All three required items closed at P3.1.7.2 |
| `docs/P3.1.7.1_Decision_Gate_Report_Evidence_Verification.md` | Decision Gate | Authority for every change made at Sprint P3.1.7.2 |

**Recorded divergence.** The two P3.1.7 reviews reached opposite verdicts. Sprint P3.1.7.1 traced the divergence to a single methodological difference — **one review measured specification adequacy; the other asserted it**. Retained as a standing lesson: an adequacy claim about a specification suite requires measurement.

---

## 5. Cross-sprint implementation observations

| Observation | Evidence | Status |
|---|---|---|
| `SUPPORTED_EXTENSIONS` is **deliberately duplicated** in `sample_rag/knowledge_source.py` and `scripts/build_manifest.py`. Centralizing would require `sample_rag/` → `scripts/` import (barred by `docs/architecture.md` §6) or a new shared module (a new architectural concept without the evidence bar `ADR-0001` applied) | Construction Plan §9.1 rated this pattern **High** drift risk when rejecting identity strategy S3 | Accepted, and now **enforced by specification** (AH-9) rather than by convention |
| No Sprint P3.1.5 commit exists; its evidence report was first committed under `5b903db`, the Sprint P3.1.6 commit, while the report's own §12 states "Repository Impact: None" | `git log --diff-filter=A` | Recorded (G-2). Documented in the report's Restoration Record |
| Construction depends on the Manifest artifact at runtime — an accepted consequence of identity strategy S1 | Construction Plan §9.1 | Accepted |
| The terminal-capture path that damaged the P3.1.5 report is still active: `docs/P3.1.7.1_Decision_Gate_Report_Evidence_Verification.md` carries 2 truncated box-drawing characters in decorative borders | Verified at Sprint P3.1.7.2 | Inert — no finding, evidence, or disposition affected. Relevant when capturing future reports |

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

**Line coverage:** `sample_rag/document.py` 100%, `sample_rag/knowledge_source.py` 100%.

**Standing caution:** a surviving mutant is evidence of a blind spot; a killed mutant is not proof of adequacy. Line coverage is not evidence of behavioural protection — at Sprint P3.1.7.1 the module measured 99% while a mutation emptying its entire output went undetected.

---

## 7. Claim-to-specification mapping

95 specifications: 17 pre-existing (`test_chunker.py`) and 78 Knowledge Layer.

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

**Not specified, deliberately:** identifier uniqueness (F-1 — not yet approved behaviour); symlink containment (§3.5, F-2-sym); `Document` persistence and structural validation (unresolved by the contract).

---

## 8. Maintenance

- Add a row only **after** a disposition is established.
- Every row cites repository evidence — a file, a commit, a measurement, or an ADR.
- A finding is never removed. It moves to Closed, with the change that closed it.
- If a row would describe work to be scheduled, it belongs in `docs/roadmap.md` instead (§1.2).
