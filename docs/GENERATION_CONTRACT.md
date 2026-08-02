# Generation Contract

**Repository:** `ai-quality-engineering`
**Status:** **Approved (Frozen)** — Repository Owner approval recorded at Sprint P3.5.1-G. Both contract gaps (§6) are dispositioned; see §22, Repository Owner Decisions.
**Generation Contract Version:** `1.0.0`
**Milestone:** 1A

> **Milestone 1A Freeze**
>
> This contract is frozen following Repository Owner approval. Behavioural or structural changes belong to Milestone 2 unless correcting a repository defect.

**Related authorities:** `docs/architecture.md` §5/§9, `docs/MILESTONE_1A.md` build items 4–6, `docs/altm.md` §3–§5, `docs/roadmap.md` §2.4/§5, `docs/CHUNK_CONTRACT.md` §5/§13/§17, `docs/glossary.md`, `docs/AI_Quality_Metrics_Reference.md` Layer 4

---

## 1. Executive Summary

This document defines **what Generation is** in this repository for Milestone 1A. It defines no algorithm, no prompt, no template, and no LLM behaviour, and it changes no runtime behaviour. It exists so that Sprint P3.5.2 implements an approved contract rather than discovering one while implementing.

The contract's central claim is a single chain:

```text
GenerationResult
      │  every statement resolves to
      ▼
supporting evidence (a citable span)
      │  every span resolves to
      ▼
chunk id
      │  every chunk id exists in
      ▼
the committed Chunk Corpus
```

That chain is satisfiable **by construction** in Milestone 1A, and this document specifies it so that it is satisfied by construction rather than measured after the fact. Measuring it — Faithfulness, Groundedness, Hallucination Rate — is Milestone 2 (`docs/AI_Quality_Metrics_Reference.md` Layer 4, DeepEval) and is out of scope here.

The repository already names a Generation component, an interface, an owning ALTM stage, and an outcome vocabulary. **None of it is replaced.** §2 records what was found, §3 records what is carried forward verbatim, and §6 records the only two places where existing repository text cannot be adopted as written — both raised as gaps for approval, not resolved unilaterally.

---

## 2. Repository Discovery Findings

Findings from the mandatory design reconciliation. Every row is a quotation or a direct reading of committed repository text.

| # | Finding | Source | Consequence for this contract |
|---|---|---|---|
| **D-1** | A **`Generator`** component already exists in the architecture: *"Produce an answer from an assembled prompt"*, interface `Generator.generate(prompt: Prompt) -> Answer`, dependencies `Context Builder`, status *"1A — deterministic stub generator"*, future *"DeepSeek API integration"* | `docs/architecture.md` §5 | Component name, responsibility and milestone status **adopted unchanged** |
| **D-2** | The `Generator` **owns the Infer stage**, and also the Post-Process guardrail layer | `docs/glossary.md`; `docs/altm.md` §4 rows *Infer* / *Post-Process* | ALTM stage ownership **adopted unchanged**; Post-Process is not exercised in 1A (§21) |
| **D-3** | The repository names Generation's artifacts at the stage boundaries: **Prompt** (Assemble → Infer), **Raw Output** (Infer → Post-Process), **Delivered Output** (Post-Process → Evaluate) | `docs/altm.md` §4 artifact-boundary table | Terminology **preserved**; §7's model is the Milestone 1A realization of *Raw Output* where Post-Process is not exercised |
| **D-4** | `docs/MILESTONE_1A.md` build item 5 is the entire committed Generation build item: *"**Generation** — deterministic Response Generator (stub). Real DeepSeek integration deferred to Milestone 2; the seam is forward-compatible now."* No fields, no shape, no schema | `docs/MILESTONE_1A.md` build item 5 | **No committed Generation artifact schema exists.** There is nothing to supersede — only something to define |
| **D-5** | `RetrievalResult` is the repository's one existing runtime artifact contract: four fields (`chunks`, `retrieval_route`, `score`, `diagnostics`), *"all populated with deterministic placeholder values in M1A, not `None`"*, `diagnostics` being *"the contract's own open mapping"* | `docs/MILESTONE_1A.md` build item 4; `sample_rag/retriever.py` | The **shape precedent** this contract follows: a small closed field set plus one open diagnostics mapping |
| **D-6** | Build item 4 **superseded** `docs/architecture.md` §5's `Retriever.retrieve(query, filters) -> List[Chunk]` explicitly — *"not a bare `List[Chunk]`"* | `docs/MILESTONE_1A.md` build item 4 | The **governance precedent** for refining an architecture §5 interface row in a downstream contract rather than silently diverging |
| **D-7** | Outcome vocabulary already exists and is already implemented: `Expected Outcome | Answer / Abstain / Clarify`, with `Clarify` excluded from Milestone 1A and `No Answer` mapped to `Abstain` | `docs/roadmap.md` §2.4; `scripts/build_evidence_trace.py` Decisions B/C, `OUTCOME_ANSWER`, `OUTCOME_ABSTAIN`, `NO_ANSWER_CATEGORY` | **Adopted verbatim.** No new outcome state is proposed (§9) |
| **D-8** | Generation quality metrics are Milestone 2, tool-owned: Faithfulness, Groundedness, Hallucination Rate, *"Evaluated by: DeepEval"* | `docs/AI_Quality_Metrics_Reference.md` Layer 4; `docs/roadmap.md` §5 | This contract states evidence structure; it **defines no metric and computes none** |
| **D-9** | Two ALTM rules already attribute failures to the `Generator`, and one attributes a *determinism* failure to it: `ALTM-INFER-1` (hallucinated fact), `ALTM-INFER-2` (false confidence on an unanswerable question — metric *"Hallucination Rate; abstention check"*), `ALTM-INDEX-1` (*"Contradictory answer across repeated runs on the same input"*, component *"Indexer / Generator"*) | `evaluation/altm_rules.py`; `docs/altm.md` §5 | These are the **recorded failure modes this contract is shaped to make unreachable by construction** (§16, G-4/G-5/G-6) |
| **D-10** | `Infer`, `Assemble`, `Post-Process`, `Evaluate` and `Final Answer` are recorded as **unreachable** — *"there is no Assemble, Infer, Post-Process, Evaluate or Final Answer component"* — and `REACHABLE_STAGES` is `("Knowledge", "Index", "Retrieve")` | `evaluation/altm_rules.py`; `docs/P3.3.4_Retrieval_Diagnosis_Report.md` | Implementing the `Generator` in P3.5.2 makes **Infer** reachable. That is a Diagnosis-layer consequence, recorded in §22 as an outstanding question, **not** actioned here |
| **D-11** | `sample_rag/generator.py` is already named in the repository structure table as part of *"the pipeline under test"* | `docs/architecture.md` §6 | P3.5.2's implementation file is **already allocated**; no new repository location is introduced |
| **D-12** | `sample_rag/` **must not import from `scripts/`** — the direction `docs/architecture.md` §6 bars — and the repository has already accepted deliberate duplication rather than violate it (`SUPPORTED_EXTENSIONS`, register **AH-9**) | `docs/architecture.md` §6; `docs/ENGINEERING_TRACEABILITY_REGISTER.md` §5; `sample_rag/retriever.py` module docstring | The outcome literals `"Answer"`/`"Abstain"` **will be duplicated** in `sample_rag/generator.py` rather than imported from `scripts/build_evidence_trace.py` (§20.4) |
| **D-13** | Runtime artifacts are a recognised repository class, distinct from persistent canonical artifacts, and `RetrievalResult` is the named example: lifecycle *"Data Model → Contract Freeze → Construction → Validation"*, lifetime *"Query-derived; exists only for the duration of one request"*, determinism *"Identical query + identical corpus/index state ⇒ identical result"* | `docs/CHUNK_CONTRACT.md` §5 | `GenerationResult` is classified into this **existing** class (§5). No new artifact category is invented |
| **D-14** | Determinism is enforced in this repository by **excluding** non-deterministic values, twice, deliberately: `created_at` was removed from the Knowledge Manifest because *"its presence would make the manifest non-deterministic"*, and `retrieval_time_ms` is *"fixed at 0 rather than measured: a real duration would make repeated runs differ"* | `docs/MILESTONE_1A.md` build item 1; `sample_rag/retriever.py` | The same exclusion is **binding** on this contract (§12, §15) |
| **D-15** | Milestone 1A architecture is **frozen**: *"All public contracts remain unchanged throughout Milestone 1A implementation unless a documented contract gap is discovered and explicitly approved"* | `docs/MILESTONE_1A.md` Definition of Done, Architecture Freeze | The route §6 uses. Both gaps are documented; neither is approved by this document |
| **D-16** | *"Architectural disposition is not the implementing agent's decision. An implementing agent presents options and a recommendation; a recommendation is not a decision."* | `docs/ENGINEERING_TRACEABILITY_REGISTER.md` §2, standing governance rule | Why §6 presents options and recommendations, and why this document was authored with status **Proposed** (approved and frozen at Sprint P3.5.1-G; §22) |

**Nothing named `GenerationResult` exists at HEAD.** The sprint brief raises it as a hypothetical (*"for example `GenerationResult`"*); a repository-wide search finds no such symbol, no Generation dataclass, no `sample_rag/generator.py`, and no Generation schema in any committed authority. D-4 is the operative finding: there is no existing Generation artifact to adopt or refine, only existing *terminology* (D-1, D-2, D-3, D-7) which §3 carries forward intact.

---

## 3. Repository Terminology — carried forward

Preserved verbatim. This contract introduces **no** new repository terminology beyond the artifact name proposed in §6.1.

| Term | Meaning, as already defined | Authority |
|---|---|---|
| **Generator** | The component that produces an answer from assembled evidence. Owns the Infer stage. Stubbed deterministically in Milestone 1A; DeepSeek in Milestone 2. Capitalized, per the glossary's naming rule for named components | `docs/glossary.md`; `docs/architecture.md` §5 |
| **Infer** | Lifecycle stage 5 of 8. Input *assembled prompt*, output *raw model output*. Failure mode: *"Unsupported or fabricated claims; blended parametric and retrieved knowledge without distinction"* | `docs/altm.md` §3, §4 |
| **Assemble** | Lifecycle stage 4 of 8, owned by the Context Builder. **Not implemented in this repository** | `docs/altm.md` §4; `evaluation/altm_rules.py` |
| **Answer / Abstain / Clarify** | The three `Expected Outcome` values. `Clarify` is outside Milestone 1A | `docs/roadmap.md` §2.4; `scripts/build_evidence_trace.py` Decision C |
| **No Answer** | A *failure taxonomy category* of the QA Dataset — *"Tests abstention"* — **not** an outcome. Maps to the `Abstain` outcome | `docs/roadmap.md` §2.3; `scripts/build_evidence_trace.py` `derive_expected_outcome` |
| **Groundedness** | *"Can every individual claim be traced to a specific, citable piece of evidence — stricter than 'not contradicted'?"* | `docs/AI_Quality_Metrics_Reference.md` Layer 4 |
| **Runtime Artifact** | Query-derived, exists for one request, not version-controlled; determinism is *identical query + identical corpus state ⇒ identical result* | `docs/CHUNK_CONTRACT.md` §5 |

### 3.1 One term this contract must disambiguate

`docs/glossary.md` §naming already warns that repository terms are load-bearing. The word **"answer"** currently carries five distinct meanings in committed text:

| Usage | Meaning | Authority |
|---|---|---|
| `Answer` (outcome value) | The Evidence Trace expectation that the pipeline should answer rather than abstain | `docs/roadmap.md` §2.4 |
| `Answer` (return type) | The unnamed, undefined return type of `Generator.generate` | `docs/architecture.md` §5 |
| `Expected Answer` / `expected_answer` | Ground truth text in the QA Dataset and Evidence Trace Dataset | `docs/roadmap.md` §2.4; `datasets/golden/` |
| `Final Answer` | Lifecycle stage 8, owned by the Evaluation Engine — **not** the Generator | `docs/altm.md` §3 |
| `Answer Relevancy` | A Final Answer-stage metric | `docs/AI_Quality_Metrics_Reference.md` |

This is the evidence behind gap **G-1** (§6.1). It is recorded as a finding rather than resolved by fiat.

---

## 4. Architectural Context

Where Generation sits, using the repository's own two lifecycles.

```text
Query-Time Lifecycle (docs/architecture.md §4)

   User Query
       │
       ▼
   Retrieval          ← implemented (Sprint P3.3.1) → RetrievalResult
       │
       ▼
   Context Assembly   ← NOT implemented; no Context Builder, no Prompt contract
       │
       ▼
   Generation         ← this contract (P3.5.1) / implementation (P3.5.2)
       │
       ▼
   Evaluation         ← Layer 1 only in Milestone 1A
```

The Assemble stage is unimplemented (D-10). Milestone 1A Generation therefore consumes the **completed retrieval output directly**, which is gap **G-2** (§6.2). This is the same reasoning `reachable_stage()` already applies and already documents: *"the row's other stage is not ruled out on evidence, it is ruled out because the component does not exist."*

---

## 5. Repository Engineering Principles

This contract follows the lifecycle already applied to the Knowledge Manifest, `Document`, `Chunk`, and `RetrievalResult`:

```text
Canonical Data Model → Contract Freeze → Construction → Validation
```

`GenerationResult` is classified as a **Runtime Artifact** under `docs/CHUNK_CONTRACT.md` §5's existing two-track distinction — the same class as `RetrievalResult`, not the Persistent Canonical Artifact class of the Knowledge Manifest and Chunk Corpus. The classification is justified by repository fact rather than asserted: the artifact is query-derived, exists for the duration of one request, and is not version-controlled. Consequently **there is no Serialization sprint** between Contract Freeze and Construction, and §13 specifies a serialization *form* without requiring persistence.

Binding principles from `docs/architecture.md` §2, applied here:

- **Docs before code** — this document exists precisely so P3.5.2 does not design while implementing.
- **Interface-first design** — §7 defines what `GenerationResult` *is*; §6.2 is the only place a signature is touched, and it is raised as a gap.
- **Deterministic before probabilistic** — no field below carries a probability, a confidence, a score, or a duration (§15).
- **Data validation before retrieval** — the ordering that put P3.4.1 before this sprint; Generation is contracted only now that every upstream authority has committed validation.

---

## 6. Contract Gaps Requiring Repository Owner Approval

Two places where existing committed text cannot be adopted as written. Both are raised under the Definition of Done's documented-gap route (D-15), and both are presented as options with a recommendation, per the standing governance rule (D-16). **A recommendation is not a decision**, and neither gap was resolved by this document as authored.

> **Governance state.** Both gaps have since been **approved** by the Repository Owner at Sprint P3.5.1-G. The analysis below is retained verbatim as the record of what was considered and why; the dispositions are recorded in §22.

### 6.1 G-1 — The artifact name: `Answer` is ambiguous

`docs/architecture.md` §5 names the Generator's return type `Answer`. It is never defined anywhere in the repository, and §3.1 records four other committed meanings of the same word — one of which, the `Answer` **outcome value**, would appear *inside* the artifact. Adopting the name literally produces contract text of the form *"an `Answer` whose outcome is `Answer`"*, and specification text that cannot state which is meant without a qualifier every time.

| Option | Assessment |
|---|---|
| **(a) Adopt `Answer` verbatim** | Maximal fidelity to §5. **Rejected as the recommendation**: it collides with the outcome value this same contract must carry, and the collision is inside a single object |
| **(b) Adopt `GenerationResult`, mirroring `RetrievalResult`** | **RECOMMENDED.** Consistent with the repository's one existing runtime-artifact name (D-5); unambiguous against all five §3.1 usages; follows precedent D-6, where build item 4 refined an architecture §5 return type in a downstream contract rather than diverging silently. The word *answer* survives as the field name `answer_text`, so §5's meaning is preserved even though its type name is refined |
| **(c) Adopt `RawOutput`, from `docs/altm.md` §4** | Faithful to the artifact-boundary table (D-3), and defensible. Rejected as the recommendation because it names a *stage boundary*, not a component's return value, and because it reads as pre-guardrail output — a Post-Process distinction Milestone 1A does not exercise |

**Recommendation: (b).** If approved, `docs/architecture.md` §5's `Generator` row should be amended by the Repository Owner in the same way build item 4 amended the `Retriever` row — an explicit supersession recorded in the authority, not a silent divergence. **This document does not make that amendment.**

### 6.2 G-2 — The input: `Prompt` does not exist

`docs/architecture.md` §5 specifies `Generator.generate(prompt: Prompt) -> Answer`, with `Context Builder` as the dependency. In this repository:

- there is no `Context Builder` implementation,
- there is no `Prompt` contract, data model, or schema, anywhere,
- the Assemble stage is formally recorded as unreachable (D-10),
- and the sprint's normative Runtime Dependency Boundary permits `RetrievalResult` *"or a future Assemble-stage artifact if introduced by a later approved contract."*

| Option | Assessment |
|---|---|
| **(a) Define a `Prompt` contract in this sprint** | **Rejected.** It would design the Assemble stage — a different component, a different ALTM stage, and a different contract — inside a Generation sprint, and would introduce an artifact no build item requires |
| **(b) Milestone 1A `Generator` consumes `RetrievalResult` directly** | **RECOMMENDED.** Stays inside the permitted dependency boundary; consumes only completed runtime retrieval output; introduces no new artifact; and applies exactly the reasoning `reachable_stage()` already applies to unimplemented stages. The §5 signature remains the Milestone 2 target, reached when a Context Builder exists |
| **(c) Generator constructs its own prompt internally** | **Rejected.** It would silently absorb the Assemble stage into the Generator, making a future Assemble-stage failure undiagnosable — the exact confusion `ALTM-ASSEMBLE-1` exists to separate (*"Diff the assembled prompt against the retrieved chunk set before suspecting the model"*) |

**Recommendation: (b)**, with the Milestone 1A signature:

```text
Generator.generate(query: str, retrieval: RetrievalResult) -> GenerationResult
```

`query` is the request input, not a repository authority — the same input `Retriever.retrieve(query, filters)` already takes, and the same input `ContextBuilder.assemble(chunks, query)` is specified to take. Passing it explicitly rather than reading `retrieval.diagnostics["query"]` keeps the Generator independent of another component's open diagnostics mapping.

---

## 7. Generation Data Model

Three nested structures. The nesting is not decorative: it is the executable form of the evidence chain in §1, and each level exists because a repository guarantee (§16) quantifies over it.

```text
GenerationResult
├── answer_text            str
├── outcome                str          "Answer" | "Abstain"
├── statements             list[GeneratedStatement]
└── diagnostics            dict

GeneratedStatement
├── text                   str
└── supporting_evidence    list[SupportingEvidence]

SupportingEvidence
├── chunk_id               str
├── document_id            str
├── character_start        int
├── character_end          int
└── text                   str
```

### 7.1 Why the middle level is called *evidence* and not *fact*

Sprint guarantee 1 requires every generated statement to resolve to *"one or more supporting facts"*, and guarantee 2 requires every fact to resolve to *"one or more supporting chunks."* The word **fact** is already taken: `datasets/golden/resume_facts.json` `facts[]` is a committed dataset authority, and the Runtime Dependency Boundary bars the Generator from reading it.

Both statements are nonetheless satisfied, because the repository already establishes that a Golden Dataset fact and a runtime evidence span **meet at the chunk id**:

```text
validation time                                runtime
───────────────                                ───────
Golden Dataset fact                            GeneratedStatement
      │ GD-8: source_text verbatim in Document        │ guarantee 1
      ▼                                               ▼
  document-frame span                          SupportingEvidence
      │ X-15: resolves to chunks                      │ guarantee 2
      ▼                                               ▼
   chunk id  ◄───────────── the join ──────────►  chunk_id
      │ X-12: exists in the Chunk Corpus              │ guarantee 3
      ▼                                               ▼
        the committed Chunk Corpus (172 chunks)
```

`SupportingEvidence` **is** the runtime realization of "a supporting fact": a citable span with a document-frame location, which is precisely the shape a Golden Dataset fact resolves to under `resolve_fact_chunks`. Naming it `evidence` rather than `fact` preserves `fact` for the dataset authority that owns it, and keeps the runtime free of any dataset dependency while leaving the two joinable at validation time (§19.4).

---

## 8. Field Definitions

### 8.1 `GenerationResult`

| Field | Type | Required | Definition |
|---|---|---|---|
| `answer_text` | `str` | Yes | The delivered answer, as one text. On `Answer`, it is assembled from the `statements` below and contains no content not present in them. On `Abstain`, it is a fixed abstention text that asserts nothing about the corpus (§9.3). Never empty; never `None` |
| `outcome` | `str` | Yes | Exactly one of `"Answer"` or `"Abstain"` (§9). Never `None` |
| `statements` | `list` | Yes | The individually evidenced claims the answer makes, in the order defined by §11. Possibly empty — and empty **exactly** when `outcome == "Abstain"` (§16, G-8). Never `None` |
| `diagnostics` | `dict` | Yes | The contract's own open mapping, exactly as `RetrievalResult.diagnostics` is (D-5). Carries per-request runtime detail without growing new top-level fields. Never `None`; may be empty of optional keys but SHALL carry the required keys of §8.4 |

### 8.2 `GeneratedStatement`

| Field | Type | Required | Definition |
|---|---|---|---|
| `text` | `str` | Yes | One claim, as delivered. Non-empty |
| `supporting_evidence` | `list` | Yes | The spans this claim is derived from, ordered per §11.2. **Non-empty** — a statement with no evidence is exactly what guarantee 1 forbids, so the empty list is not a representable state |

### 8.3 `SupportingEvidence`

| Field | Type | Required | Definition |
|---|---|---|---|
| `chunk_id` | `str` | Yes | The `Chunk.id` this span was taken from. Equal to an `id` carried by a chunk in the consumed `RetrievalResult.chunks` |
| `document_id` | `str` | Yes | The parent document's identity, equal to that chunk's `document_id` — the repository's canonical document identity and the join key the Manifest, Chunk Corpus and Golden Dataset already share (`docs/DOCUMENT_CONTRACT.md` §8.4) |
| `character_start` | `int` | Yes | Zero-based, **inclusive**, Unicode-code-point offset into the **parent document's text** — the same reference frame `Chunk.character_start` uses (`docs/CHUNK_CONTRACT.md` §13) |
| `character_end` | `int` | Yes | Zero-based, **exclusive**, in the same frame |
| `text` | `str` | Yes | The span's literal text, verbatim from the corpus. Equals `document_text[character_start:character_end]`, the same relationship `Chunk` invariant 3 already freezes |

**Why the document frame and not the chunk frame.** Every offset already in this repository — `Chunk.character_start`/`character_end`, the offsets `resolve_fact_chunks` computes, the frame GD-8/GD-9 ground facts in — is document-frame. A chunk-frame offset would be a second, incompatible coordinate system for the same corpus. The values are computable from `RetrievalResult` alone: a span at chunk-relative offset `o` sits at `chunk["character_start"] + o`, so no document, dataset, or corpus read is required at runtime.

### 8.4 Required `diagnostics` keys

`diagnostics` is open, as `RetrievalResult`'s is. Three keys are nonetheless **required**, each because a repository authority requires the information to exist:

| Key | Type | Required because |
|---|---|---|
| `query` | `str` | Traceability: the artifact must record which request produced it. `RetrievalResult.diagnostics["query"]` sets the precedent exactly |
| `retrieval_route` | `str` | Carries through the route the consumed `RetrievalResult` reported, so the generation record states which retrieval path fed it. Copied, never re-derived |
| `stub` | `bool` | `docs/MILESTONE_1A.md` build item 4's own worked example carries `"stub": True` so *"the pytest suite [can] assert on structure and semantics now"*; `docs/architecture.md` §9 records Generation as a Milestone 1A stub. `True` throughout Milestone 1A |

No key in `diagnostics` may carry a timestamp, a duration, a random value, or any other value that varies between runs on identical input (§12, D-14).

---

## 9. Outcome Semantics — reconciliation

### 9.1 The existing vocabulary is adopted unchanged

`docs/roadmap.md` §2.4 defines three `Expected Outcome` values — **Answer / Abstain / Clarify** — and `scripts/build_evidence_trace.py` already implements the Milestone 1A restriction of that domain: `OUTCOME_ANSWER = "Answer"`, `OUTCOME_ABSTAIN = "Abstain"`, with *"Clarify … outside this milestone and … never emitted"* (Decision C).

**This contract proposes no new outcome state**, and adopts the same two values, spelled identically. `Clarify` remains defined by `docs/roadmap.md` and remains outside Milestone 1A; nothing here narrows or redefines it, and a future milestone may emit it without amending this section's vocabulary.

### 9.2 The four terms, kept distinct

| Term | What it is | Who owns it |
|---|---|---|
| `Answer` | An **outcome** the pipeline produces | This contract; `docs/roadmap.md` §2.4 |
| `Abstain` | An **outcome** the pipeline produces | This contract; `docs/roadmap.md` §2.4 |
| `Clarify` | An **outcome** defined but not produced in Milestone 1A | `docs/roadmap.md` §2.4 |
| `No Answer` | A **QA Dataset failure-taxonomy category** — *"Tests abstention"* — never an outcome | `docs/roadmap.md` §2.3 |

The `No Answer → Abstain` mapping is already implemented by `derive_expected_outcome` and is **not restated** by this contract. That function remains the sole owner of the mapping; the Generator never reads the QA Dataset and therefore never sees a failure category at all.

### 9.3 What `Abstain` means at runtime

`Abstain` is the outcome in which the Generator makes **no claim about the corpus**. It is produced when the consumed `RetrievalResult` yields no evidence the Generator can quote. On this path:

- `statements` is empty — there is nothing to evidence, and nothing is evidenced;
- `answer_text` is a fixed text that asserts nothing about the corpus;
- guarantees G-4 and G-5 (§16) hold **vacuously**, which is stated here rather than glossed: on the Abstain path the evidence chain protects nothing, because nothing is claimed. Its protection is on the Answer path.

The condition under which abstention occurs is an implementation matter for P3.5.2 (§20.2). What this contract fixes is the *shape and meaning* of the outcome, not the predicate that selects it.

`ALTM-INFER-2` — *"False confidence on an unanswerable question"*, metric *"Hallucination Rate; abstention check"* — is the recorded repository failure mode this section exists to make structurally unreachable: a Milestone 1A Generator that can only emit quoted evidence cannot express confidence it has no evidence for.

---

## 10. Traceability Requirements

| Requirement | Statement |
|---|---|
| **T-1** | Every `SupportingEvidence.chunk_id` SHALL be traceable to the Chunk Corpus, through the `RetrievalResult` that produced it |
| **T-2** | Every `SupportingEvidence.document_id` SHALL be traceable to a `documents[]` entry of the Knowledge Manifest, through that chunk |
| **T-3** | Every `GeneratedStatement` SHALL be traceable to at least one `SupportingEvidence`, and therefore to at least one chunk and one document |
| **T-4** | Every `GenerationResult` SHALL be traceable to the query that produced it, via `diagnostics["query"]` |
| **T-5** | Traceability SHALL be recoverable from the artifact alone, without re-executing retrieval and without consulting any dataset authority |

T-5 is what makes validation possible without making the runtime depend on evaluation artifacts: the artifact carries enough identity to be joined against repository authorities *later*, by a validator, rather than being built from them.

---

## 11. Ordering Semantics

Both orderings are total, and both are inherited from an ordering the repository has already frozen. Neither is invented here.

### 11.1 `statements`

`statements` SHALL be ordered by the **retrieval rank** of their highest-ranked supporting evidence — that is, by the position within `RetrievalResult.chunks` of the earliest chunk any of the statement's evidence cites. Ties, if a future implementation can produce them, SHALL be broken by ascending `(document_id, character_start)`.

Retrieval rank is the ordering `RetrievalResult` already froze: `rank_candidates` sorts by descending score then ascending committed corpus position, which is itself Knowledge Manifest document order then `chunk_index` (Sprint P3.2.2). Statement order is therefore a property of the corpus and the query, not of the Generator's iteration.

**Why not ascending `chunk_index`,** the ordering Evidence Trace `expected_chunk` uses (Decision G): that field orders *expectations*, where retrieval rank does not exist and corpus order is the only available total order. A runtime artifact has retrieval rank available, and discarding it would mean the answer's own reading order contradicted the ranking that produced it.

### 11.2 `supporting_evidence`

Within one statement, `supporting_evidence` SHALL be ordered by ascending `(document_id, character_start)` — corpus reading order within a document, documents in a fixed lexicographic order of identity. No two entries within one statement SHALL share `(chunk_id, character_start, character_end)`, which is what makes the order total rather than merely defined.

---

## 12. Determinism

Determinism is stated in the form `docs/CHUNK_CONTRACT.md` §5 already uses for runtime artifacts: **identical query + identical corpus/index state ⇒ identical result.**

Concretely, for a fixed committed Chunk Corpus and a fixed query, two executions of `Generator.generate` SHALL produce `GenerationResult` values that are equal field-for-field, and whose serializations (§13) are byte-identical.

This is not achieved by testing for it. It is achieved by **excluding the values that would break it**, which is what this repository has already done twice (D-14):

- no timestamp, in any field or diagnostics key — the `created_at` exclusion;
- no measured duration — the `retrieval_time_ms = 0` precedent;
- no random, hash-seed-dependent, locale-dependent, or filesystem-iteration-dependent value;
- no set or dict iteration order escaping into a serialized sequence;
- no floating-point value at all in Milestone 1A (§15).

`ALTM-INDEX-1` — *"Contradictory answer across repeated runs on the same input"*, component *"Indexer / Generator"* — is the recorded failure mode this section makes unreachable by construction.

---

## 13. Serialization Specification

**The semantic model of §7 and the serialization form below are separate concepts.** §7 is implementation-independent: it is satisfiable by a frozen dataclass, a JSON document, a protobuf message, or a future representation not yet chosen. This section specifies one serialization, and specifying it does not make the semantic model depend on it.

### 13.1 In-memory representation (Milestone 1A)

Frozen dataclasses, mirroring `RetrievalResult` (`@dataclass(frozen=True)`), with field order exactly as listed in §7. Frozen because the artifact is a record of what happened, and no consumer has any reason to mutate it.

### 13.2 Serialized form

Where a `GenerationResult` is serialized — for a CLI transcript in P3.6.0, a report, or a test fixture — it SHALL use the repository's established convention, unchanged:

```text
json.dumps(result, indent=2) + "\n"      UTF-8, insertion-order keys, one trailing newline
```

This is exactly the form `write_manifest`, `write_chunks` and `write_evidence_trace` already share. Field order in the serialized object SHALL be the §7 declaration order; keys SHALL NOT be sorted, because insertion order *is* the contract's order and re-sorting would discard it.

### 13.3 Persistence

**No persistence is required or defined by this contract.** `GenerationResult` is a Runtime Artifact (§5): query-derived, single-request, not version-controlled. Nothing in Milestone 1A writes one to `datasets/`, `reports/`, or `sample_rag/`.

Requiring byte-identical serialization (§16, G-9) without requiring persistence is deliberate and is not a contradiction: the property is what makes two runs *comparable* — by a test, by a CLI diff, by a future regression harness — and it must hold whether or not anything is written to disk. Should a later approved contract introduce a persisted generation artifact, it inherits §13.2 rather than choosing a new form.

---

## 14. Contract Traceability Matrix

Every field, justified. No field appears here that is not in §7, and no field appears in §7 that is not here.

| Generation field | Repository authority | Justification |
|---|---|---|
| `answer_text` | `docs/architecture.md` §5 (`Generator` — *"Produce an answer"*, `-> Answer`); `docs/altm.md` §4 (*Raw Output*, Infer's output); `docs/roadmap.md` §2.4 (*Expected Answer* is what it will be compared against) | The Generator's defining output. Without it the component produces nothing. Named `answer_text` rather than `answer` to keep the §3.1 collision resolved inside the artifact |
| `outcome` | `docs/roadmap.md` §2.4 (*Expected Outcome | Answer / Abstain / Clarify*); `scripts/build_evidence_trace.py` `OUTCOME_ANSWER`, `OUTCOME_ABSTAIN`, Decision C; `docs/roadmap.md` §2.3 (*No Answer — tests abstention*) | The Evidence Trace Dataset already records an expected outcome for all 22 committed questions. Without this field the pipeline produces nothing that expectation can ever be compared against |
| `statements` | `docs/AI_Quality_Metrics_Reference.md` Layer 4, Groundedness (*"Can every individual claim be traced to a specific, citable piece of evidence"*); sprint guarantee 1 | Groundedness is defined **per claim**. A single answer string cannot carry per-claim traceability, so the claim must be a first-class element. `docs/altm.md` §5 `ALTM-INFER-1` localizes failures to individual fabricated claims for the same reason |
| `statements[].text` | Same as `statements` | The claim itself; the unit Groundedness quantifies over |
| `statements[].supporting_evidence` | Sprint guarantees 1–2; `docs/altm.md` §5 `ALTM-ASSEMBLE-1` (*"Diff the assembled prompt against the retrieved chunk set"*) | The per-claim citation. Non-empty by contract, which is what makes guarantee 1 structural rather than measured |
| `supporting_evidence[].chunk_id` | `docs/CHUNK_CONTRACT.md` §17 (`Chunk.id`, unique across the corpus); sprint guarantee 3; `RetrievalResult.chunks` | The join point between the runtime artifact and every committed evidence authority (§7.1). The one field that makes T-1 and validation §19.4 possible |
| `supporting_evidence[].document_id` | `docs/DOCUMENT_CONTRACT.md` §8.4 (canonical document identity); `docs/roadmap.md` §2.4 (*Expected Source*); `docs/altm.md` §5 `ALTM-KNOWLEDGE-1` (*"Answer cites the wrong document version"*) | The corpus holds two overlapping resume versions, and `ALTM-KNOWLEDGE-1` is a recorded symptom against exactly that. An answer that cannot say which document version it quoted cannot be checked for it |
| `supporting_evidence[].character_start` | `docs/CHUNK_CONTRACT.md` §13 (zero-based, inclusive, document-frame, Unicode code points) | Locates the citation precisely, in the repository's existing coordinate system. Reused verbatim, not redefined |
| `supporting_evidence[].character_end` | `docs/CHUNK_CONTRACT.md` §13 (zero-based, exclusive) | As above. The half-open pair is what makes `text == document_text[start:end]` checkable, mirroring Chunk invariant 3 |
| `supporting_evidence[].text` | `docs/CHUNK_CONTRACT.md` §17 invariant 3; `datasets/golden/resume_facts.json` `source_text` and its GD-8 verbatim guarantee | Carries the quotation itself, so the artifact is self-contained (T-5) and a verbatim check is possible without re-reading the corpus. The repository already treats a verbatim span as its unit of grounding |
| `diagnostics` | `docs/MILESTONE_1A.md` build item 4 (*"`diagnostics`… deterministic placeholder values… not `None`"*); `sample_rag/retriever.py` (*"the contract's own open mapping"*) | Direct precedent, same milestone, same artifact class. Absorbs per-request detail so the closed field set stays small |
| `diagnostics["query"]` | `sample_rag/retriever.py` `diagnostics["query"]`; T-4 | Request traceability, precedent-for-precedent |
| `diagnostics["retrieval_route"]` | `docs/MILESTONE_1A.md` build item 4 (`retrieval_route`); `docs/roadmap.md` §2.4 (*Expected Route*) | Carries through which retrieval path fed generation. Copied from the consumed `RetrievalResult`, never re-derived |
| `diagnostics["stub"]` | `docs/MILESTONE_1A.md` build item 4 worked example (`"stub": True`); `docs/architecture.md` §9 (*"Deterministic stub `Generator`"*), Milestone Capability Matrix (Generation: Stub → DeepSeek) | Marks the Milestone 2 swap-in seam, and lets a specification assert the milestone status rather than assume it |

---

## 15. Explicit Omissions

Fields considered and **deliberately not included**, because no committed repository authority requires them. Per the sprint's own rule, explicit omission is preferable to unjustified addition.

| Omitted field | Why it was considered | Why it is omitted |
|---|---|---|
| `generation_route` | Symmetry with `RetrievalResult.retrieval_route` | `retrieval_route` exists because retrieval genuinely has four routes (SQL / BM25 / Vector / Hybrid) and `docs/roadmap.md` §2.4 records an *Expected Route* field for them. Generation has **one** route per milestone and no corresponding expectation field anywhere. Symmetry alone is not a justification. The Milestone 1A/2 distinction is already carried by `diagnostics["stub"]` |
| `score` / `confidence` | Symmetry with `RetrievalResult.score` | A generation confidence is a probabilistic value, barred by *"deterministic before probabilistic"* (`docs/architecture.md` §2), and no authority defines what it would measure. `RetrievalResult.score` is a defined lexical overlap fraction; there is no analogous defined quantity here |
| `faithfulness`, `groundedness`, `hallucination_rate` | The Layer 4 metric set | Milestone 2, DeepEval-owned (D-8). A runtime artifact carrying its own quality scores would also make the system under test grade itself — the coupling `docs/architecture.md` §6 separates `sample_rag/` from `evaluation/` to prevent |
| `expected_answer` / any Golden Dataset value | It would make answers directly comparable | Barred by the Runtime Dependency Boundary (§18). A Generator that reads the expected answer is not answering the question |
| `generation_time_ms` | Symmetry with `diagnostics["retrieval_time_ms"]` | The retriever's own precedent is to fix it at `0` rather than measure it, because *"a real duration would make repeated runs differ"*. Carrying a constant `0` would add a field that means nothing; carrying a real duration would break §12 |
| `created_at` / any timestamp | Provenance | Explicitly removed from the Knowledge Manifest for exactly this reason (D-14). The precedent is binding, not advisory |
| `prompt` / `assembled_context` | It is what §5's signature implies | There is no Assemble stage and no `Prompt` contract (G-2). Carrying a field for an artifact this repository does not define would embed an unratified concept in a ratified one |
| `citations` as free text | Human-readable attribution | `supporting_evidence` already carries attribution in resolvable, checkable form. A parallel prose field would be a second source of truth for the same claim, with no mechanism keeping the two in step — the exact defect GD-7 exists to catch in the Golden Dataset |

---

## 16. Repository Guarantees

Normative. A `GenerationResult` that violates any guarantee below does not conform to this contract.

**G-1 — Artifact shape.** Every `GenerationResult` SHALL carry exactly the four fields of §8.1, each at its declared type, and none SHALL be `None`.

**G-2 — Outcome domain.** `outcome` SHALL be exactly one of `"Answer"` or `"Abstain"`. No other value SHALL be emitted in Milestone 1A.

**G-3 — Answer non-emptiness.** `answer_text` SHALL be a non-empty string on every path, including the Abstain path.

**G-4 — Statement support.** Every `GeneratedStatement` SHALL carry at least one `SupportingEvidence`. *(Sprint guarantee 1, expressed in this contract's terms per §7.1.)*

**G-5 — Evidence resolution.** Every `SupportingEvidence` SHALL carry a `chunk_id` present in the consumed `RetrievalResult.chunks`, and a `document_id` equal to that chunk's `document_id`. *(Sprint guarantee 2.)*

**G-6 — Corpus membership.** Every `chunk_id` carried by a `GenerationResult` SHALL exist in the committed Chunk Corpus. *(Sprint guarantee 3.)* This holds **by construction** and not by lookup: chunk ids are carried through from retrieval, which draws them from the corpus, and the Generator never constructs a chunk id.

**G-7 — Support by construction.** Every `GeneratedStatement.text` SHALL be supported by repository evidence **by construction** — the text SHALL be derivable from its `supporting_evidence` spans by verbatim quotation and deterministic template assembly alone. *(Sprint guarantee 4.)* No semantic entailment, claim verification, hallucination detection, faithfulness evaluation or groundedness evaluation is introduced by this contract; those are Milestone 2 (D-8).

**G-8 — Abstention exclusivity.** `statements` SHALL be empty if and only if `outcome == "Abstain"`. An Abstain result SHALL make no claim about the corpus; an Answer result SHALL carry at least one statement.

**G-9 — Determinism.** Repeated execution over an identical query and an identical corpus state SHALL produce field-for-field equal results, and SHALL produce byte-identical serialized output under §13.2. *(Sprint guarantee 5.)*

**G-10 — Deterministic ordering.** `statements` and `supporting_evidence` SHALL be ordered per §11, and those orderings SHALL be total. *(Sprint guarantee 6.)*

**G-11 — Verbatim evidence.** Every `SupportingEvidence.text` SHALL equal `document_text[character_start:character_end]` for its parent document — the relationship `docs/CHUNK_CONTRACT.md` §17 invariant 3 already freezes for chunks, and `datasets/golden/` GD-8 already freezes for facts.

**G-12 — Traceability.** Every `GenerationResult` SHALL satisfy T-1 … T-5 (§10), and SHALL remain fully traceable to committed repository authorities without re-executing retrieval. *(Sprint guarantee 7.)*

**G-13 — Runtime dependency boundary.** The Generator SHALL depend at runtime on the query and a `RetrievalResult` only, and SHALL NOT read any repository authority listed in §18.

**G-14 — Observational purity.** Generation SHALL perform no filesystem I/O, no network I/O, and no mutation of the `RetrievalResult` it consumes — the same structural read-only property `sample_rag/retriever.py` already holds.

---

## 17. Final Generation Contract (Approved)

Consolidated reference shape, combining §7–§12.

**Interface (Milestone 1A, approved per §22, G-2):**

```text
Generator.generate(query: str, retrieval: RetrievalResult) -> GenerationResult
```

**Schema:**

| Field | Type | Required | Purpose |
|---|---|---|---|
| `GenerationResult.answer_text` | `str` | Yes | The delivered answer; non-empty on every path |
| `GenerationResult.outcome` | `str` | Yes | `"Answer"` or `"Abstain"` |
| `GenerationResult.statements` | `list[GeneratedStatement]` | Yes | Individually evidenced claims, ordered per §11.1; empty iff Abstain |
| `GenerationResult.diagnostics` | `dict` | Yes | Open mapping; required keys `query`, `retrieval_route`, `stub` |
| `GeneratedStatement.text` | `str` | Yes | One claim, non-empty |
| `GeneratedStatement.supporting_evidence` | `list[SupportingEvidence]` | Yes | Non-empty, ordered per §11.2 |
| `SupportingEvidence.chunk_id` | `str` | Yes | `Chunk.id`, carried through from retrieval |
| `SupportingEvidence.document_id` | `str` | Yes | Parent document identity |
| `SupportingEvidence.character_start` | `int` | Yes | Document-frame, inclusive |
| `SupportingEvidence.character_end` | `int` | Yes | Document-frame, exclusive |
| `SupportingEvidence.text` | `str` | Yes | Verbatim span |

**Invariants (all must hold for every conforming `GenerationResult`):**

1. `outcome ∈ {"Answer", "Abstain"}`.
2. `answer_text` is non-empty.
3. `statements == []` if and only if `outcome == "Abstain"`.
4. For every statement: `supporting_evidence` is non-empty.
5. For every evidence span: `character_end > character_start`.
6. For every evidence span: `len(text) == character_end - character_start`.
7. For every evidence span: `text == document_text[character_start:character_end]`.
8. For every evidence span: `chunk_id` is the `id` of a chunk in the consumed `RetrievalResult.chunks`, and `document_id` equals that chunk's `document_id`.
9. For every evidence span: `chunk.character_start <= character_start` and `character_end <= chunk.character_end` — the span lies **within** the chunk it cites.
10. `statements` is ordered per §11.1; `supporting_evidence` is ordered per §11.2; both orderings are total.
11. Within one statement, no two evidence spans share `(chunk_id, character_start, character_end)`.
12. `diagnostics` carries `query`, `retrieval_route` and `stub`, and carries no value that varies between runs on identical input.
13. Identical query + identical corpus state ⇒ identical `GenerationResult`, field-for-field, and byte-identical under §13.2.

**No fields beyond the eleven above exist in this version of the contract.** Every candidate evaluated in §15 is explicitly deferred, not silently included as optional.

---

## 18. Runtime Dependency Boundary

Normative, and restated here because it is the constraint most likely to be eroded by convenience during implementation.

**Permitted at runtime:** the request `query`, and a `RetrievalResult` produced by the Retriever.

**Barred at runtime** — the Generator SHALL NOT read, import, load, or otherwise depend on:

```text
Knowledge Manifest            Retrieval Evaluation
Golden Dataset                Retrieval Metrics
QA Dataset                    Retrieval Diagnosis
Chunk Corpus (as a file)      ALTM rules
Evidence Trace Dataset
```

These MAY be consulted only for terminology, contract justification, validation strategy, field traceability, and architectural rationale — which is exactly what this document does and what §19 permits validators to do.

**Why this boundary is load-bearing and not bureaucratic.** Every barred artifact exists for the repository's own 22 benchmark questions. A Generator that reads any of them can answer those 22 questions and nothing else, while appearing to work. The boundary is what keeps Generation capable of answering an arbitrary future query — and it is what makes the P3.5.2 validation suite meaningful rather than circular.

`sample_rag/` also SHALL NOT import from `scripts/` (D-12), which is why the outcome literals are duplicated rather than imported (§20.4).

---

## 19. Validation Strategy

How P3.5.2's implementation will be validated. Deterministic repository validation only: pytest, stdlib, committed state. **No DeepEval, no Ragas, no LLM judge, no embedding evaluation, no semantic evaluation** — all Milestone 2 (D-8).

### 19.1 Contract conformance (synthetic)

Specifications over constructed `GenerationResult` values asserting §17's invariants 1–12, each with a synthetic negative case, following the pattern `tests/test_evidence_trace_dataset.py` established: one deliberately malformed value per failure class, plus a control confirming the valid baseline is accepted.

### 19.2 Runtime behaviour (over the committed corpus)

The Generator executed over the committed Chunk Corpus, via the Retriever, for the repository's committed questions — asserting shape, invariants, and the Answer/Abstain split, and asserting **no** particular answer text. Freezing today's answers would convert a future generation improvement into a test failure, which is the reasoning `tests/test_retrieval_evaluation.py` already records for retrieval classifications.

### 19.3 Determinism

Two executions over an identical query and corpus, asserting field-for-field equality and byte-identical §13.2 serialization. This is G-9 executed, and it is the specification that would catch a set or dict iteration order escaping into a serialized sequence.

### 19.4 Cross-authority validation — at validation time only

Validators, unlike the runtime, MAY read repository authorities. This is where the §7.1 join is exercised:

| Check | Joins |
|---|---|
| Every emitted `chunk_id` exists in the committed Chunk Corpus | `GenerationResult` → `sample_rag/chunks.json` |
| Every emitted `document_id` is catalogued by the Knowledge Manifest | → `knowledge_manifest.json` |
| Every `SupportingEvidence.text` is verbatim at its document-frame offsets | → `KnowledgeSource().load()` — the same mechanism GD-8 uses |
| For the repository's benchmark questions, emitted chunk ids relate to the Evidence Trace `expected_chunk` | → `datasets/golden/resume_evidence_trace.json` |

The last row is **observational**, and deliberately not an equality assertion: `expected_chunk` records what retrieval *should* return, and the Milestone 1A retriever is a documented lexical stub whose behaviour Milestone 2 is expected to change. Asserting equality would make a retrieval improvement fail a generation test.

### 19.5 Mutation verification

Every load-bearing specification verified to fail when its invariant is broken, by the in-memory mutation method Sprint P3.4.1 used — no repository file modified. A guarantee that cannot be observed failing is not evidence.

### 19.6 What validation does *not* do

It does not assert answer quality, relevance, fluency, or truthfulness. Those require Layer 3/4 tooling that Milestone 1A does not have and does not import. The Milestone 1A claim is narrower and fully checkable: **every claim the Generator makes is a verbatim quotation of committed corpus evidence, cited to the chunk and document it came from.**

---

## 20. Implementation Readiness — what P3.5.2 implements

The implementation sprint SHALL require no architectural redesign. Everything below is an engineering task against this document.

### 20.1 Artifacts to create

| Item | Location | Notes |
|---|---|---|
| `GenerationResult`, `GeneratedStatement`, `SupportingEvidence` | `sample_rag/generator.py` | Frozen dataclasses, §7 field order. Location already allocated by `docs/architecture.md` §6 (D-11) |
| `Generator` | `sample_rag/generator.py` | `generate(query, retrieval) -> GenerationResult`, per §6.2's approved resolution |
| Specifications | `tests/test_generator.py` (and a cross-authority file if §19.4 warrants separation) | Per §19 |

### 20.2 Decisions P3.5.2 must make, and which this contract deliberately leaves open

These are **implementation** decisions, not contract decisions. Each is constrained by the guarantees above but not determined by them:

1. **The abstention predicate** — the condition on `RetrievalResult` under which `outcome` is `Abstain`. §9.3 fixes the meaning and shape; the predicate is P3.5.2's.
2. **Span selection** — which span of a retrieved chunk becomes a `SupportingEvidence`. The whole chunk is the simplest conforming choice; a sentence-level span is also conforming. G-11 and invariant 9 bound it either way.
3. **Statement construction** — the deterministic template by which spans become `GeneratedStatement.text`, and whether a statement maps to one chunk or several.
4. **`answer_text` assembly** — the deterministic joining of statements into one text, and the fixed abstention text.
5. **How many chunks are used** — all of `retrieval.chunks`, or a prefix.

### 20.3 What P3.5.2 must not do

Implement prompting, templates that call a model, or any LLM; introduce a `Prompt` or Context Builder; modify `RetrievalResult`, the Retriever, or any evaluation layer; read any authority barred by §18; introduce a metric; persist a generation artifact; or amend `docs/architecture.md` §5 (a Repository Owner action, per §6).

### 20.4 One implementation constraint recorded in advance

The outcome literals `"Answer"` and `"Abstain"` already exist as `OUTCOME_ANSWER` / `OUTCOME_ABSTAIN` in `scripts/build_evidence_trace.py`. `sample_rag/` **cannot import them** — `docs/architecture.md` §6 bars the direction, and the repository has already accepted deliberate duplication over violating it (D-12, register AH-9). P3.5.2 SHALL therefore define the two literals in `sample_rag/generator.py`, record the duplication in its module docstring exactly as `sample_rag/retriever.py` records the `SUPPORTED_EXTENSIONS` case, and a specification SHOULD assert the two definitions agree — turning the duplication from a convention into a checked property, which is what the register asked for at AH-9.

### 20.5 Readiness assessment

| Question | Answer |
|---|---|
| Is the artifact shape fully specified? | **Yes** — §17, eleven fields, thirteen invariants |
| Is every field justified? | **Yes** — §14, with §15 recording what was refused |
| Is the input fully specified? | **Yes** — G-2 approved (§22) |
| Is the output vocabulary settled? | **Yes** — adopted verbatim from `docs/roadmap.md` §2.4 (§9) |
| Is determinism specified? | **Yes** — §12, by exclusion, following two existing precedents |
| Is validation specified? | **Yes** — §19 |
| Does implementation require an architectural decision? | **No** — §6's two gaps are dispositioned by the Repository Owner (§22) |
| Are any blockers open? | **No.** G-1 and G-2 are approved (§22); P3.5.2 is unblocked |

---

## 21. Explicit Out-of-Scope

Not defined by this contract, and not to be inferred from it:

- Any algorithm, prompt, template, or model behaviour
- The `Prompt` artifact, the Context Builder, and the Assemble stage
- The **Post-Process** stage. `docs/altm.md` assigns the Generator a guardrail layer at Post-Process; Milestone 1A exercises no guardrail, so `GenerationResult` is the Infer-stage output and *Raw Output* and *Delivered Output* (D-3) coincide. A future guardrail contract may distinguish them; this one does not
- Every Layer 3/4 metric: Faithfulness, Groundedness, Hallucination Rate, Answer Relevancy
- Semantic entailment, claim verification, hallucination detection
- Multi-document synthesis policy, contradiction resolution between the two committed resume versions, and answer-length or style policy
- Any change to `RetrievalResult`, the Retriever, the evaluation layers, or any dataset authority
- Persistence of a generation artifact (§13.3), and any CLI behaviour (P3.6.0)

---

## 22. Repository Owner Decisions

Completed governance decisions, recorded at Sprint P3.5.1-G. This section records dispositions; it introduces no technical content and changes none.

| # | Decision | Disposition |
|---|---|---|
| **G-1** | The Generation artifact name | ✓ **Approved.** `GenerationResult` is approved as the Generation artifact |
| **G-2** | The Milestone 1A runtime interface | ✓ **Approved.** `Generator.generate(query, retrieval: RetrievalResult)` is approved as the Milestone 1A runtime interface |
| **Contract** | Status of this document | ✓ **Frozen.** The Generation Contract is approved as the frozen Milestone 1A repository authority |

Consequences of these decisions, recorded for traceability and **not actioned by this document**:

- The `docs/architecture.md` §5 `Generator` row amendment contemplated by §6.1 remains a Repository Owner action, in the manner `docs/MILESTONE_1A.md` build item 4 amended the `Retriever` row.
- Sprint P3.5.2 is unblocked and implements §17 and §20 as written.

---

## 23. Architectural Follow-ups

Formerly *Outstanding Questions*. Q-1 and Q-2 were dispositioned by the Repository Owner and are recorded in §22; the questions below **remain intentionally unresolved** and are retained to preserve architectural history for Milestone 2. Nothing here is answered, redesigned, or removed.

| # | Question | Impact | Resolved by |
|---|---|---|---|
| **Q-1** | Is gap **G-1** (artifact name `GenerationResult`) approved? | Blocks P3.5.2 naming and the `docs/architecture.md` §5 amendment | **Resolved** — Repository Owner, Sprint P3.5.1-G (§22) |
| **Q-2** | Is gap **G-2** (`generate(query, retrieval)` rather than `generate(prompt)`) approved? | Blocks P3.5.2's signature | **Resolved** — Repository Owner, Sprint P3.5.1-G (§22) |
| **Q-3** | Implementing the `Generator` makes the ALTM **Infer** stage reachable. `evaluation/altm_rules.py` `REACHABLE_STAGES` is `("Knowledge", "Index", "Retrieve")`, and `ALTM-INFER-1`, `ALTM-INFER-2`, `ALTM-INDEX-1` and `ALTM-ASSEMBLE-1` all name the Generator | **Not a P3.5.1 or P3.5.2 concern.** Diagnosis is a separate layer with its own committed specifications; widening `REACHABLE_STAGES` is a deliberate scope decision, not a side effect of implementing a component | A later sprint, if the Repository Owner scopes one. Recorded here so it is not rediscovered |
| **Q-4** | Milestone 1A's answers are verbatim quotations. Is that *sufficient* as an answer, or only as a *grounded* answer? | None for Milestone 1A — Answer Relevancy is a Final Answer-stage metric owned by the Evaluation Engine in Milestone 2 (`docs/altm.md` §5 `ALTM-FINAL-ANSWER-1`). Recorded because a reviewer will ask | Milestone 2 |
| **Q-5** | Two committed resume versions can both supply evidence for one query. This contract requires each statement to cite its `document_id`; it does not require the Generator to *prefer* one version | Deliberate. Version preference is Canonical Document Marking — an explicitly separate, un-started piece of work — and deciding it here would settle a corpus-composition question inside a Generation contract | Canonical Document Marking, if scoped |

---

*This document defines what Generation **is** for Milestone 1A. It defines no implementation. It is a frozen repository authority: Repository Owner approval of §6's two gaps was recorded at Sprint P3.5.1-G (§22).*
