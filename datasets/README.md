# Datasets

This directory contains the datasets used throughout the `ai-quality-engineering` repository. It exists to explain **why each dataset directory exists**, not how evaluation works. Evaluation strategy, failure taxonomy, and the Evidence Trace schema are defined in `docs/roadmap.md`; they are not duplicated here.

---

## Dataset Organization

One dataset category exists:

- `datasets/golden/` — the human-verified reference dataset

---

### datasets/golden/

- Human-verified ground-truth dataset.
- Canonical evaluation corpus for Milestone 1A.
- Every entry is traceable to verified source material.
- Serves as the repository's authoritative reference dataset.

> **Repository Note**
>
> `datasets/golden/` was originally scaffolded as `datasets/rag/` during Milestone 0 and renamed in Milestone 1A to align with the repository's canonical documentation architecture established in Milestone 0.5.
>
> The rename reflects the directory's architectural role as the repository's canonical ground-truth dataset rather than data associated with a specific retrieval architecture.

---

## Repository Principle

- Real, verified data before artificial data.
- Documentation before implementation.

> **Repository Note — RO-05**
>
> This document previously described a `datasets/synthetic/` directory, reserved for artificially constructed datasets and recorded as *"deferred intentionally, not forgotten"* with an expectation that it would become relevant during Milestone 2+. That directory was never populated, and the Repository Owner decision **RO-05** removed it: the repository's knowledge corpus is intentionally composed of real, versioned knowledge artifacts and their associated Golden Datasets.
>
> Any future introduction of synthetic datasets requires an explicit Repository Owner decision identifying both the architectural purpose and the milestone that consumes them. The Milestone 2+ expectation recorded here previously is superseded by that decision, not carried forward.
