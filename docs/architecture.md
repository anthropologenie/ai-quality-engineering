# Architecture

## Evaluation pipeline (target state)

```
Prompt / RAG change
      |
      v
  GitHub Push
      |
      v
GitHub Actions (CI)
      |
      +--> Promptfoo   (prompt regression, consistency across N runs)
      |
      +--> DeepEval    (faithfulness, hallucination, answer relevancy)
      |
      +--> Ragas       (context precision, context recall, retrieval quality)
      |
      v
  reports/ (evaluation_report.md, metrics.csv)
      |
      v
  Pass / Fail gate
```

## Components

- **sample_rag/retriever.py** — minimal retrieval step over `datasets/rag/`
- **sample_rag/generator.py** — LLM call producing an answer from retrieved context
- **evaluation/deepeval/** — assertion-style tests (faithfulness, hallucination, answer relevancy)
- **evaluation/promptfoo/** — promptfooconfig.yaml running the same prompt N times + prompt A/B comparisons
- **evaluation/ragas/** — context precision/recall, faithfulness scoring on the retrieval step
- **reports/** — before/after tables, not just pass/fail booleans

## Data quality layer (ETL-style validation applied to AI inputs)

Before any evaluation run, `datasets/rag/` is validated for:
- Missing values
- Duplicate records
- Context completeness
- Chunk size validation
- Embedding coverage
- Metadata validation

This mirrors the data profiling discipline already used on the HP GA4 pipeline (172 columns / 14 tables).
