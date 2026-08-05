# MILESTONE_1A_CAPABILITY_INVENTORY.md

**Purpose:** make the technical substance of Milestone 1A explicit and checkable — what exists, what it proves, and what evidence backs each claim. Every number here should be independently reproducible from the committed repository, not taken on faith.

---

## 1. The pipeline, as built

```
Knowledge Manifest → Chunk Corpus → Retriever → Generator → CLI
        (1)               (2)          (3)         (4)       (5)
```

All five stages are implemented, deterministic, stdlib-only, and runnable end to end:
```
python -m scripts.cli --question "..."
```

| Stage | Artifact | Status |
|---|---|---|
| Knowledge | `sample_rag/knowledge_manifest.json` | 2 documents cataloged (resume v2.2, v2.3), hash-verified, canonical flag set |
| Index | `sample_rag/chunks.json` | 172 chunks, structure-aware chunking, deterministic |
| Retrieve | `sample_rag/retriever.py` → `RetrievalResult` | Lexical scoring, canonical-aware tie-break |
| Generate | `sample_rag/generator.py` → `GenerationResult` | Deterministic, contract-frozen (v1.0.0) |
| CLI | `scripts/cli.py` | Byte-identical stdout, correct exit codes, pure orchestration |

## 2. The evaluation assets — what makes this a *quality engineering* project, not just a RAG demo

### Golden Dataset
- **26 facts, 22 QA pairs**, all sourced from the resume corpus.
- **Full 7/7 failure taxonomy populated**: Exact Fact, Paraphrase, Multi-hop, No Answer, False Premise, Stale Version, Contradiction. The last two required deliberately retaining resume v2.2 in the corpus specifically to have a second version to test against.
- Every fact's `source_text` is verified as a **verbatim substring** of its parent document — the load-bearing grounding guarantee, enforced by a committed pytest suite with a synthetic negative case (a deliberately-broken fact must fail the check).

### Evidence Trace Dataset
- **22 entries**, extending each QA pair with `expected_chunk`, `expected_document_ids`, `expected_reasoning_type`, `expected_outcome` — the machine-checkable definition of "correct retrieval behavior" for every question.
- Enriched with document identity (Sprint P3.3.5) specifically to distinguish "wrong chunk within the right document" from "right topic, wrong document version."

### Retrieval Evaluation → Metrics → Diagnosis stack
Four layers, each consuming only the layer below it (a frozen dependency boundary, verified by running each layer in isolation with no repository present):

1. **Evaluation** (`evaluation/retrieval_evaluation.py`): classifies each question's retrieval outcome — Exact Match, Full Coverage, Partial Match, No Match. Classifications verified exhaustive and mutually exclusive by brute-force enumeration, not assumption.
2. **Metrics** (`evaluation/retrieval_metrics.py`): classical IR metrics computed from Evaluation records — Chunk Precision@K, Chunk Recall@K (macro + micro), Hit Rate. Deliberately **not** called "Context Precision/Recall" — those names are reserved for Ragas, Milestone 2 scope, per `AI_Quality_Metrics_Reference.md`.
3. **Diagnosis** (`evaluation/retrieval_diagnosis.py`): attributes each finding to a specific ALTM stage (Knowledge, Index, Retrieve — the only reachable stages pre-Generation) via a numbered rule table derived from `docs/altm.md` §5.
4. **Independent validators** at every layer — separately-authored code with zero shared logic, confirming the primary engine's output rather than trusting it.

## 3. The one fully-diagnosed, fully-fixed defect — the strongest evidence artifact in the project

A concrete, four-stage arc, each stage independently verified:

1. **Observed** (P3.3.1): resume v2.2 outranked the canonical v2.3 on 21 of 22 retrieval questions.
2. **Root-caused** (P3.3.1 investigation): not a relevance failure — a mechanical tie-break artifact. Both versions score identically on ~95% shared text; ties broke on alphabetical file path, and "v2_2" sorts before "v2_3."
3. **Formally diagnosed** (P3.3.5, after enriching Evaluation records with document identity): named `ALTM-RETRIEVE-1` ("right topic, wrong specific document"), 3 of 22 questions affected, cause distinguished from Knowledge-stage staleness by ruling Knowledge innocent first — the corpus does contain the expected document; retrieval just isn't preferring it.
4. **Visibly confirmed** (manual review, P3.7.0/P3.7.1): duplicate near-identical paragraphs (Fortune 500 vs. large-scale enterprise wording) appeared in nearly every real generated answer — the abstract diagnosis made concrete.
5. **Fixed at the correct layer** (P3.7.4/P3.7.5): a `canonical: bool` field added to the Knowledge Manifest (Knowledge-stage signal), retriever tie-break updated to prefer canonical documents **only among already-equal-scoring candidates** (no scoring logic touched — the fix stays in the stage it was diagnosed in).
6. **Re-measured**: `ALTM-RETRIEVE-1` went from 3 → 0. Chunk Precision@K macro 0.1273 → 0.1455, Recall macro 0.5227 → 0.5432, Hit Rate 0.6364 → 0.6818 — every metric improved as a side effect of a Knowledge-stage fix, not a Retrieval-algorithm change.

This is the single most citable example of the project's actual thesis: a retrieval-quality-*looking* problem was root-caused to a Knowledge-stage labeling gap and fixed there, not papered over with retrieval tuning.

## 4. Validation discipline — the numbers

- **372 committed pytest specifications**, spanning chunking, retrieval, generation, CLI, dataset grounding, cross-dataset integrity, evaluation, metrics, and diagnosis.
- **Mutation testing** run on every load-bearing suite (Data Quality Validation, dataset grounding, CLI orchestration, Retrieval Evaluation) — every recorded run shows 0 surviving mutants after correction. Twice, mutation testing caught a hole in the *test* rather than the implementation (a docstring-splitting bug that silently excluded an entire import block from a check; a `created_at` marker missed by a keyword scanner) — a meaningful finding in itself: this project's validation layer has been mutation-tested, not just its implementation.
- **Determinism verified, not assumed**, at every layer — repeated builds/runs compared byte-for-byte or by hash, including across process boundaries.

## 5. What is explicitly out of scope for Milestone 1A (by design, not oversight)

- Real LLM generation (DeepSeek) — stub only, deterministic
- Real embeddings, vector search, hybrid retrieval — `EmbeddingProvider` interface deferred to Milestone 1B/2
- Ragas Context Precision/Recall, DeepEval Faithfulness/Groundedness — require an LLM judge, Milestone 2
- JobOps/job-description ingestion, SQL-filter retrieval against real structured data — deferred to Milestone 1B, reasoned explicitly in the P3.7.3 Constitutional Decision

Each of these is a **named, owned, deferred item** in `docs/DEFERRED_ITEMS_REGISTER.md`, not a silently dropped scope.
