# Datasets

This directory contains the datasets used throughout the `ai-quality-engineering` repository. It exists to explain **why each dataset directory exists**, not how evaluation works. Evaluation strategy, failure taxonomy, and the Evidence Trace schema are defined in `docs/roadmap.md`; they are not duplicated here.

---

## Dataset Organization

Two dataset categories exist, each with a single, non-overlapping responsibility:

- `datasets/golden/` — the human-verified reference dataset
- `datasets/synthetic/` — reserved for artificially constructed datasets, currently empty by design

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

### datasets/synthetic/

Reserved for artificially constructed evaluation datasets, including examples such as:

- adversarial scenarios
- regression stress cases
- scalability datasets
- generated edge-case corpora

**Status: empty by design.**

The directory is intentionally not populated during Milestone 1A. The Golden Dataset (constructed from verified resume and JobOps data) is the sole evaluation corpus throughout Milestone 1A.

`datasets/synthetic/` is **deferred intentionally, not forgotten**. It becomes relevant during Milestone 2+ once the deterministic retrieval and generation pipeline exists and empirical testing identifies genuine edge cases that cannot be adequately represented within the Golden Dataset.

---

## Repository Principle

- Real, verified data before artificial data.
- Documentation before implementation.
- Synthetic datasets complement the Golden Dataset rather than replace it.
