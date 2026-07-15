# AI Quality Engineering

**Owner:** Karthik S R
**Status:** Active learning + portfolio repository

## What this is

This repository is a public engineering portfolio answering one question:

> Can this engineer evaluate and validate LLM and agentic AI systems the way a QA engineer validates any other production system?

It is not a chatbot demo, and it is not a framework showcase. It applies the same
discipline used for ETL testing, data validation, and backend QA — test strategy,
regression suites, CI, and reporting — to LLM, RAG, and agent systems.

## Structure

- `docs/` — roadmap, architecture, learning log, interview notes, glossary
- `datasets/` — synthetic and RAG-related sample data used for evaluation
- `evaluation/` — DeepEval, Promptfoo, and Ragas configs and metrics
- `sample_rag/` — a minimal retriever + generator pipeline used as the evaluation target
- `reports/` — baseline and regression evaluation reports (numbers, not just tool names)
- `tests/` — pytest-style test suites wrapping the evaluation frameworks
- `scripts/` — utility scripts (report generation, dataset prep, etc.)
- `.github/workflows/` — CI pipeline running the evaluation suite on push (stretch goal)

## Why this exists

Full context and scope are documented in [`docs/roadmap.md`](docs/roadmap.md).
Short version: 3 evaluation frameworks (DeepEval, Promptfoo, Ragas), a defined set of
classical ML / LLM / agent / production metrics, and one finished project — deliberately
scoped narrow so it can be finished and demonstrated end-to-end in an interview.

## Status

See `docs/learning-log.md` for progress against the roadmap's success criteria.
