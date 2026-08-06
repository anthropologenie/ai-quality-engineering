# sample_rag

Sample corpus and reference implementation used throughout the AI Quality Engineering learning roadmap.

## Knowledge Sources

    documents/
    ├── resume/
    │   └── Versioned resume corpus
    └── jobs/
        └── Job descriptions

## Purpose

Provides deterministic data for chunking, indexing, retrieval, generation, and evaluation experiments without relying on external services.

## Current Corpus

Three resume documents, all catalogued in `knowledge_manifest.json`:

| Document | Designation |
|---|---|
| `documents/resume/Karthik_SR_Resume_v2_2.docx` | Historical |
| `documents/resume/Karthik_SR_Resume_v2_3.docx` | Historical |
| `documents/resume/Karthik_SR_Resume_v3_0.docx` | **Canonical** |

Historical versions are retained deliberately, not left over. Canonical designation is declared by the Repository Owner in `scripts/build_manifest.py` and recorded per document as `documents[].canonical`; it is never inferred from a filename. See `docs/corpus/resume-corpus.md` for the corpus's purpose and versioning policy.

`documents/jobs/` is empty. Job descriptions and JobOps data are Milestone 1B capabilities — `docs/DEFERRED_ITEMS_REGISTER.md` **1B-05**, **1B-06**.
