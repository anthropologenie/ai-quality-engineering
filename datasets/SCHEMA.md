# Dataset Schema

**Repository:** `ai-quality-engineering`
**Status:** Sprint 1A.1 — P0.5, Representation Contract
**Related documents:** `datasets/README.md` (dataset organization), `docs/roadmap.md` (Golden Dataset design, Section 2)

---

## 1. Purpose

This document defines the representation conventions for every dataset artifact under `datasets/golden/` — file format, fact granularity, identifier scheme, repository layout, and container shape.

It intentionally does **not** define:

- Evaluation strategy — see `docs/roadmap.md`, Section 5
- Retrieval architecture — see `docs/architecture.md`
- Milestone sequencing — see `docs/roadmap.md`, Section 1
- Failure taxonomy or Evidence Trace field semantics — see `docs/roadmap.md`, Section 2

This document is the representation contract only: **how** data is stored, not **what** the data means or **why** it exists. `datasets/README.md` explains why the directories exist; this document explains how their contents are shaped.

---

## 2. Schema Version

| Field | Value |
|---|---|
| Schema Version | `1.0` |
| Status | Active |
| Milestone | 1A |

Every JSON artifact under `datasets/golden/` carries a `schema_version` field at its top level. Future changes to file structure, container shape, or identifier convention must increment this version rather than silently changing structure under an unchanged version number. A schema version bump should be accompanied by a corresponding update to this document.

---

## 3. Canonical Data Sources

Three sources are supported, per `docs/roadmap.md` Section 2.1:

- **Resume** — verified biographical and project fact
- **Job Descriptions** — JobOps-sourced
- **JobOps** — structured SQLite metadata (application status, salary, location)

All three sources follow the same representation contract defined in this document. Source-specific fields may exist within individual fact records where required, but the container structure, identifier conventions, and traceability model remain identical across all sources.

---

## 4. Dataset File Format

**Format: JSON.**

Rationale:

- Native support in Python's standard library — no additional dependency, consistent with the Milestone 1A "minimal dependencies" principle
- Naturally represents nested structures required by the Evidence Trace container
- Matches the ingestion shape expected by DeepEval and Ragas in Milestone 2, avoiding a translation step later

---

## 5. Fact Granularity

**Granularity: clause-level.**

A canonical fact represents one coherent experience, responsibility, or outcome. Multiple supporting numbers remain part of the same fact when they describe a single claim.

**Example.** The resume text *"Reduced execution time by 40% while sustaining 98% pass rate across 100+ scenarios"* is **one** fact, not three — all three numbers describe a single demonstrated outcome. A fact is split only when a source sentence spans genuinely distinct topics (for example, a bullet mixing a tooling detail with an unrelated leadership claim).

This granularity is consistent with the worked example already established in `docs/roadmap.md` Section 2.2, which treats a compound claim ("led a team of 5, owning test strategy and stakeholder communication") as a single fact with multiple derived question forms — not as multiple separate facts.

---

## 6. Identifier Conventions

All identifiers are source-prefixed and relational — every downstream artifact derives its ID from exactly one canonical fact ID.

**Fact IDs:**
```
resume_f001
job_f001
jobops_f001
```

**Question IDs** (derived from a parent fact):
```
qa_resume_f001_lexical
qa_resume_f001_semantic
qa_resume_f001_reasoning
qa_resume_f001_multihop
```

**Evidence Trace IDs** (derived from a parent fact):
```
meta_resume_f001
```

The source prefix (`resume`, `job`, `jobops`) is carried through every derived ID, preventing collisions across sources and making provenance recoverable from the ID alone without a lookup.

---

## 7. Repository Layout

```
datasets/
├── README.md
├── SCHEMA.md
├── golden/
│   ├── resume_facts.json
│   ├── resume_qa_pairs.json
│   ├── resume_evidence_trace.json
│   ├── job_facts.json
│   ├── job_qa_pairs.json
│   ├── job_evidence_trace.json
│   ├── jobops_facts.json
│   ├── jobops_qa_pairs.json
│   └── jobops_evidence_trace.json
└── synthetic/
    └── .gitkeep
```

| File | Responsibility |
|---|---|
| `*_facts.json` | Canonical, source-traceable facts for one data source |
| `*_qa_pairs.json` | Questions derived from that source's facts, across the four question forms |
| `*_evidence_trace.json` | Per-question expected pipeline behavior, keyed to the parent fact |

One file is maintained for each artifact category. This provides a stable, deterministic representation while keeping repository organization consistent across all supported data sources.

---

## 8. JSON Shape

Each file's top-level container. This defines the outer structure only — individual record schemas for `facts` and `qa_pairs` are intentionally left undefined here. They are specified alongside the first implementation of each artifact type and evolve under the current schema version.

**Facts container:**
```json
{
  "schema_version": "1.0",
  "facts": []
}
```

**QA pairs container:**
```json
{
  "schema_version": "1.0",
  "qa_pairs": []
}
```

**Evidence Trace container:**
```json
{
  "schema_version": "1.0",
  "evidence_trace": []
}
```

**Evidence Trace field names are not open for definition at P4.** They are already canonically locked in `docs/roadmap.md` Section 2.4: Question, Expected Answer, Expected Source, Expected Chunk, Expected Retrieval Route, Expected Reasoning Type, Expected Metrics, Expected Outcome. When P4 populates `evidence_trace` entries, these field names must be reused verbatim — not redefined, renamed, or reinterpreted at the implementation stage.

---

## 9. Population Strategy

The schema defined in this document applies uniformly to all three sources, effective immediately. The **files** do not populate uniformly in this sprint:

- **Resume** — populated with real, extracted facts under Sprint 1A.1, P1–P4.
- **Job Descriptions** — remain schema-valid empty stubs (`{"schema_version": "1.0", "facts": []}` and equivalents) until scraped job posting data is stable enough to extract from.
- **JobOps** — remain schema-valid empty stubs until the underlying SQLite schema fields are settled.

This is intentional, not an oversight: the representation interface is finalized for all three sources now, so that job and JobOps population in a later sprint requires no schema rework — only content. Populating job and JobOps facts is explicitly out of scope for Sprint 1A.1 and belongs to a subsequent sprint once its source-data preconditions are met.

---

## 10. Guiding Principles

- **Representation follows architecture.** Implementation conventions reinforce the documented architecture; they never contradict it.
- **Traceability over cleverness.** Every question and Evidence Trace record deterministically references exactly one canonical fact ID — no implicit or inferred relationships.
- **Simplicity before scalability.** Optimized for Milestone 1A's actual size and goals; complexity (e.g., per-fact files, UUIDs) is not introduced ahead of a demonstrated need.
- **Future compatibility.** Today's container shape is chosen to feed Milestone 2 evaluation tooling (DeepEval, Ragas) with minimal transformation.
- **Single source of truth.** Organizational rules live in `datasets/README.md`; representation rules live here; architecture and roadmap decisions remain unchanged and are referenced, not duplicated.
- **Interface before implementation.** This contract is finalized before any resume fact, question, or Evidence Trace entry is written — consistent with the interface-first principle already governing pipeline component design in `architecture.md`.

---

*This document is the canonical representation contract for `datasets/golden/`. It should be revised only when the schema itself changes (a version bump), not when new data is populated within the existing schema.*
