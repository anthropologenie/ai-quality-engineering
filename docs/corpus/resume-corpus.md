# Resume Corpus

This directory contains versioned resume documents that form part of the AI Quality Engineering repository's knowledge corpus.

## Purpose

The resume corpus supports deterministic retrieval evaluation across multiple document revisions.

It is used to evaluate:

- canonical document selection
- historical version retrieval
- stale-version detection
- provenance and evidence attribution
- regression testing across corpus evolution

## Corpus

| Version | Status | Notes |
|---------|--------|-------|
| `Karthik_SR_Resume_v2_2.docx` | Historical | Intentionally retained to support the **Stale Version** and **Contradiction** failure-taxonomy scenarios used during retrieval evaluation. |
| `Karthik_SR_Resume_v2_3.docx` | Historical | Superseded by the Milestone 1A canonical resume while remaining part of the historical evaluation corpus. |
| `Karthik_SR_Resume_v3_0.docx` | Canonical (Milestone 1A) | Current canonical resume snapshot for the Milestone 1A deterministic retrieval evaluation baseline. |

## Repository Principle

Historical versions are intentionally preserved.

The repository evaluates retrieval against a versioned knowledge corpus rather than only the latest document. This enables reproducible evaluation of:

- canonical document selection
- historical retrieval
- provenance attribution
- contradiction handling
- stale-version detection
- regression scenarios across corpus evolution

New resume versions are introduced only after explicit review and acceptance, at which point they become new canonical knowledge snapshots while previous canonical versions remain part of the historical corpus.

## Repository Note

This README documents the purpose and organization of the resume corpus.

Machine-readable corpus metadata is maintained independently as part of the repository's retrieval infrastructure.

Documentation updates do not imply runtime metadata changes. Operational corpus metadata is synchronized only through normal milestone implementation and acceptance.
