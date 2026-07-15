# AI Quality Engineering — Learning Roadmap Baseline

**Owner:** Karthik S R
**Purpose:** Baseline scope document defining what to learn, build, and speak to for AI/LLM QA interview readiness. This is the reference point for all future prep — additions require a deliberate decision to expand scope, not ad-hoc tool collecting.

**Guiding principle:**
> Become the engineer who can answer "How do we know our AI system is correct, reliable, repeatable, and production-ready?" — not an AI framework collector.

---

## 1. In Scope

### 1.1 Tools (3 only)

| Priority | Tool | Role | Mental Model |
|---|---|---|---|
| ⭐⭐⭐⭐⭐ | **DeepEval** | Primary LLM testing framework | PyTest for LLMs |
| ⭐⭐⭐⭐⭐ | **Promptfoo** | Prompt regression & consistency testing | Regression suite for prompts |
| ⭐⭐⭐⭐⭐ | **Ragas** | RAG / retrieval evaluation | ETL validation, but for retrieval quality |

No further tools to be added to active learning until these three are demonstrable in the GitHub project (Section 3).

### 1.2 Concepts — Classical ML Evaluation

Know definitions **and** trade-offs, not just formulas.

- Accuracy
- Precision
- Recall
- F1 Score
- ROC-AUC

**Must be able to explain:**
- When accuracy is misleading (class imbalance)
- The precision/recall trade-off
- Why F1 is preferred in many real-world cases

### 1.3 Concepts — LLM Evaluation

**Core six (know deeply — ~80% of interview discussion):**
- Faithfulness
- Groundedness
- Hallucination Rate
- Answer Relevancy
- Context Precision
- Context Recall

**Conceptual only (don't need deepest expertise):**
- Toxicity
- Bias

### 1.4 Concepts — Agent Evaluation

Priority is *above* Classical ML — this is where the resume already has direct proof points (HP RCA pipeline).

- Task Completion Rate
- Tool Success Rate
- Retry Rate
- Planning Accuracy
- Reasoning Accuracy
- Loop Detection
- Latency
- Cost per Task

### 1.5 Concepts — Production Metrics

- P95 latency
- Token usage
- Cost per request
- Failure rate
- Drift

*(User satisfaction and escalation rate: useful to know, but treated as product KPIs, not engineering metrics — lower priority.)*

### 1.6 GitHub Project — "AI Quality Evaluation Suite"

One project only. Framed as a **testing framework**, not an AI chatbot demo.

```
AI Quality Evaluation Suite
├── sample_rag/
│   ├── retriever.py
│   ├── generator.py
│   └── documents/
├── tests/
│   ├── test_faithfulness.py
│   ├── test_hallucination.py
│   ├── test_consistency.py
│   ├── test_prompt_regression.py
│   └── test_ragas.py
├── promptfoo/
│   └── promptfooconfig.yaml
├── deepeval/
│   └── metrics.py
├── reports/
│   ├── evaluation_report.md
│   └── metrics.csv
├── github_actions/
└── README.md
```

**Required README elements:**
- Evaluation pipeline diagram (prompt change → push → CI → Promptfoo → DeepEval → Ragas → report → pass/fail)
- Data quality section applying ETL-style validation to AI inputs:
  - Missing values
  - Duplicate records
  - Context completeness
  - Chunk size validation
  - Embedding coverage
  - Metadata validation
- Before/after results table (not just "I used DeepEval" — show numbers)

**Stretch (only after core project works):** GitHub Actions running the eval suite on push.

### 1.7 Interview Narrative — Resume Reinterpretation

Existing project experience is to be *relabeled* with AI QA vocabulary, not replaced with new stories.

| Resume experience | AI Quality interpretation |
|---|---|
| Eliminated duplicate-write collisions | Improved tool success rate, reduced retry failures |
| Confidence scoring in RCA agent | Output calibration / reasoning confidence |
| Evidence Retrieval → Reasoning Agent | RAG pipeline with retrieval + reasoning validation |
| GA4 data profiling (172 columns, 14 tables) | AI input data quality / reliability assessment |
| Redshift → Databricks migration | Data foundation supporting trustworthy AI systems |
| 10–15 min alert-to-RCA target vs. hours/days manual | Latency and cost-per-task improvement story |

---

## 2. Out of Scope (for now)

Explicitly deprioritized to avoid dilution. Revisit only if a specific interview or role calls for it.

| Item | Status | Reason |
|---|---|---|
| LangSmith | Conceptual only, no hands-on build | Covered by knowing "traces/datasets/regression for LLMs" one-liner |
| MLflow | Conceptual only, no hands-on build | Databricks-adjacent, but not core to the 3-tool project |
| OpenTelemetry | Conceptual only | Bridges backend observability to AI tracing; nice-to-mention, not to build |
| Phoenix (Arize) | Name + one-line purpose only | Observability tool, not a testing framework |
| TruLens | Name + one-line purpose only | Overlaps with Ragas' RAG evaluation coverage |
| Weights & Biases | Name recognition only | Experiment tracking, not core QA |
| Evidently AI | Name + one-line purpose only | Drift/monitoring; adjacent to Production Metrics section |
| OpenAI Evals | Conceptual understanding only | Good to know exists, not a priority to hands-on learn |
| Second GitHub project | Not planned | One finished project > multiple partial ones |
| Toxicity/Bias deep expertise | Conceptual only | Included in metrics list but not a focus area |

---

## 3. Priority Order (Execution Sequence)

1. **Concepts first** — Classical ML trade-offs, LLM core six, Agent metrics (map each to HP RCA pipeline as you go)
2. **DeepEval** — pytest-style, fastest transition from existing skill set
3. **Promptfoo** — consistency + regression testing (directly answers "how do you test AI consistency" question)
4. **Ragas** — RAG/retrieval evaluation
5. **GitHub project** — combine all three into the Evaluation Suite structure above, with a real results table
6. **Interview narrative** — finalize STAR-format story connecting HP RCA project to AI QA vocabulary (Section 1.7)

---

## 4. Success Criteria

This roadmap is "done" when Karthik can:

- [ ] Explain precision/recall/F1 trade-offs with an RCA-pipeline example, not a textbook one
- [ ] Define the LLM core six metrics without hesitation and give a concrete example for each
- [ ] Map every Agent Evaluation metric to a specific HP RCA pipeline detail already on the resume
- [ ] Run DeepEval, Promptfoo, and Ragas against the sample RAG project and produce a results report
- [ ] Point to a live GitHub repo during an interview and walk through the evaluation pipeline end-to-end
- [ ] Deliver the STAR narrative in Section 1.7 fluently, in under 90 seconds

---

*This document is the baseline. Any new tool, metric, or project addition should be weighed against Section 2 (Out of Scope) before being added — the goal is depth on a small surface area, not breadth.*

