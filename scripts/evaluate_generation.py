"""Native generation-quality evaluation — Sprint M2.08.

The on-demand entry point Repository Owner ruling **RO-18** authorizes:

    committed golden dataset
          ->  explicit selection: --case-id ID, or --all
          ->  real retrieval (semantic + lexical + RRF, unmodified)
          ->  ContextBuilder  ->  Prompt
          ->  ModelGenerator  ->  GenerationResult      (one provider call each)
          ->  evaluation/generation_metrics.py
          ->  DeepSeek judge, through the one sanctioned provider boundary
          ->  Faithfulness / Groundedness / Hallucination Rate / Answer Relevancy
          ->  evidence printed for a human to read

**This is not part of the deterministic pytest suite and must never become
one.** RO-14 Decision 2 — carried forward by **RO-18 Decision 6** — reads *"no
provider call may enter the deterministic pytest suite"*, and **a judge call is
a provider call**. `tests/test_generation_metrics.py` specifies the metric
engine against a non-networked substitute; this performs the real generation and
the real judging, on demand, from a terminal. It is the seventh instance of the
`scripts/run_*.py` / `scripts/evaluate_*.py` pattern (`docs/architecture.md` §6 —
*"Operational scripts … not pipeline logic"*), not a new mechanism.

Nothing runs without an explicit selection
--------------------------------------------
Every real run of this script spends provider budget — one generation call per
selected case, plus judge calls per claim — so **there is no default and no
implicit full-dataset run**. `--case-id ID` evaluates exactly one committed
golden entry; `--all` is the only thing that authorizes the whole dataset; any
other invocation, including none at all, is a usage error that exits before a
model, an index or a provider exists.

**The guard is structural, not a matter of statement order.** Argument parsing
and selection are the first two things `main` does, and the two expensive
imports — `sample_rag.vector_runtime` and `scripts.run_hybrid_retrieval`, which
between them pull `torch`, `transformers`, `sentence_transformers` and `faiss`
into the process at roughly 3.1 s — are performed **inside** the functions that
need them rather than at module scope. So `--help`, an unknown flag, a missing
selection and an unknown case id all cost a JSON read and nothing more. See the
comment above the import block for the measured chains.

Generation and retrieval are measured, never modified
------------------------------------------------------
**M2-08 is MEASURE, not IMPROVE.** Every stage below is called through the
component that already owns it — `load_corpus` and `load_canonical_documents`
from `scripts/run_retrieval.py`; `canonical_order`, `fuse_routes`,
`lexical_route`, `semantic_route`, `load_documents` and `ROUTE_TOP_K` from
`scripts/run_hybrid_retrieval.py`; `ContextBuilder` and `ModelGenerator`
unchanged. Nothing here sorts, filters, re-weights, truncates, reranks or budgets
anything, no `top_k` is chosen, no RRF constant is restated, no prompt template
is written and no generation parameter is set. So the pipeline this script
measures is *the repository's* pipeline rather than a second one arranged to
score well.

`sample_rag/model_generator.py`, `sample_rag/context_builder.py`,
`sample_rag/deepseek.py`, `sample_rag/fusion.py`, `sample_rag/retriever.py`, the
chunking and the prompts are all untouched by this sprint, and **M2-07's
`evaluation/context_metrics.py`, `tests/test_context_metrics.py` and
`scripts/evaluate_context.py` are untouched** — RO-18 Decision 11.

The evidence frame is the assembled prompt, and that is checked
----------------------------------------------------------------
`docs/altm.md` §4 states the **Infer** failure as *"Model states something not
supported by **the assembled prompt**"*. So the passages handed to the metric
engine are the blocks of `Prompt.context`, in assembled order, and
`generate_cases` **verifies** that `CONTEXT_SEPARATOR.join(passages)` equals
`prompt.context` byte for byte rather than assuming the two agree. A mismatch is
raised, not measured: an evidence frame that is not the prompt the model saw
would charge **Infer** with an **Assemble**-stage failure.

The reference that is deliberately not read
---------------------------------------------
**`expected_answer` is never read by this script**, and
`evaluation/generation_metrics.py` **refuses** a case that carries it. None of
the four metrics references ground truth: `docs/roadmap.md` §5 Layer 3 fixes
three of them as *"consistency with retrieved context only"*, and Answer
Relevancy is *"independent of whether it's true"*. Three golden fields are read —
`id`, `question`, and `expected_outcome` for dataset composition only.

**The partition is taken from the observed `GenerationResult.outcome`, not from
`expected_outcome`.** The abstention domain statement is about whether the system
asserted anything, which is a property of what it produced.

The judge, and the boundary it reuses
---------------------------------------
**RO-18 Decision 4** independently and narrowly authorizes `sample_rag/deepseek.py`
as M2-08's judge seam, in the shape *native M2-08 evaluator → injected judge seam
→ existing provider boundary*, *"conditional on technical reuse"* and explicitly
not by extending RO-17 Decision 4.

**The condition is satisfied, and the finding is that nothing had to change.**
`DeepSeekClient.complete(messages) -> str` is already the whole of what a judge
needs, so the adapter below is one call over the existing method.
`sample_rag/deepseek.py` is **not modified, not subclassed and not wrapped in a
second client**; no alternate provider client exists; no SDK, router, session,
retry, backoff or HTTP primitive is introduced here. **One client instance serves
both roles** — generation through `ModelGenerator`, judging through the seam —
because creating a second would be a second provider architecture for one
authorized boundary.

Credential handling
--------------------
`DEEPSEEK_API_KEY` is consumed by `sample_rag/deepseek.py` from the process
environment. **This script never reads it, never receives it, never prints it,
never accepts it as an argument and does not report its presence as a boolean.**
A run without it fails as `ProviderConfigurationError` by name, which is what an
operator needs and says nothing about the value.

What is recorded, and what is deliberately not
------------------------------------------------
**Recorded:** dataset identity, entry counts and composition, the retrieval route
and depth, the generation component and the judge's provider and model, the
metric definitions and aggregation rule, all four metrics under both aggregations
where both exist, and the per-case evidence that explains them — per claim its
text, its support verdict, its faithful / grounded / hallucinated classification,
the passages judged for grounding and which one carried it; per answer the three
relevancy conjunct verdicts.

**Retained as diagnostic evidence only:** the `GenerationResult.statements` count
and the `SupportingEvidence` chunk ids the system itself attributed. These are
printed **beside** the metrics and are **never passed to the metric engine** —
`docs/GENERATION_CONTRACT.md` §24.3 guarantees their provenance, not that a claim
is entailed by them, and using them as a reference would convert a structural
guarantee into the empirical property M2-08 exists to measure.

**Never recorded, in stdout or anywhere else:** the credential, the authorization
header, any raw judge or generation request payload, any raw response payload,
any other provider metadata. A verdict and a parsed claim are the *derived
evaluation evidence* the metric is computed from and cannot be explained without;
the payloads that carried them are not, and `evaluation/generation_metrics.py`
never returns them, so there is nothing here to suppress.

**This script writes no file.** The M2-18 execution trace is untouched — no trace
field is added, `scripts/execution_trace.py` is not imported, and RO-18 Decision
12 keeps M2-18 ✅ DISCHARGED and unmodified. `reports/baseline/` and
`reports/regressions/` are **M3-03** scaffolds and are not populated.

What a score here does and does not establish
-----------------------------------------------
**A number is evidence, not a verdict.** No repository authority states a target,
a threshold or an acceptance criterion for any of the four metrics, so this
script prints no pass, fail, good or bad and computes no comparison against one.

`docs/roadmap.md` §5 Layer 3: these metrics check *"consistency with retrieved
context only — never whether that context was itself current or correct. **A
model can be 100% faithful to a stale document.**"* No figure printed here is a
statement that an answer is correct.

None of it is deterministic. The judge is a live model, the claim denominator is
itself a judge product, and `docs/GENERATION_CONTRACT.md` **G-9** under v2.0.0
does not require `answer_text` to be reproducible at all. Two runs may differ,
and the printed evidence is what a reader checks a run against.
"""

import argparse
import sys

from sample_rag.context_builder import ContextBuilder
from sample_rag.deepseek import DeepSeekClient
from sample_rag.model_generator import ModelGenerator
from sample_rag.retriever import Retriever

from evaluation.generation_metrics import (
    ABSTAIN_OUTCOME,
    ANSWER_OUTCOME,
    CONTEXT_SEPARATOR,
    GenerationMetricsError,
    compute,
)
from scripts.build_evidence_trace import load_evidence_trace, validate_evidence_trace
from scripts.run_retrieval import load_canonical_documents, load_corpus

# `sample_rag.vector_runtime` and `scripts.run_hybrid_retrieval` are **deliberately
# absent from this import block**, and the absence is measured rather than assumed.
#
#     scripts/evaluate_generation.py
#       └─ sample_rag.vector_runtime          3.14 s
#            └─ sample_rag.embedding
#                 └─ sentence_transformers  ->  torch, transformers
#            └─ sample_rag.vector_index      ->  faiss
#       └─ scripts.run_hybrid_retrieval       3.11 s
#            └─ sample_rag.vector_runtime         (the same chain)
#
# Every other import in this module measures at or below 0.02 s and pulls no
# machine-learning library at all. Importing those two costs ~3.1 s and loads
# `torch`, `transformers`, `sentence_transformers` and `faiss` into the process
# **merely because the module was imported** — before `main` runs, and therefore
# before argument parsing could possibly refuse the invocation.
#
# `--help`, a missing selection, an unknown flag and an unknown case id must all
# cost nothing, so the two heavy imports are performed **inside** the functions
# that need them, which run only after selection has been validated. No model
# weight is loaded at import time in either case — that happens later still, when
# `VectorIndexRuntime` is constructed and indexed — but the library import is real
# work and is what this arrangement defers.
#
# This is the whole of the laziness: no other import is moved, and nothing about
# the pipeline below changes.


class SelectionError(Exception):
    """Raised when the requested selection cannot be resolved against the dataset.

    A tenth independent, flat exception type, following the repository's
    per-responsibility pattern (`GenerationMetricsError`, `ContextMetricsError`,
    `RetrievalMetricsError`, …). It is raised **before** any model, index or
    provider object exists, and `main` converts it into argparse's own usage
    error so the process exits non-zero through the mechanism
    `scripts/cli.py` already records as *"argument validation is argparse's
    responsibility"*.
    """


def load_reference_entries() -> list:
    """Read the Evidence Trace Dataset for the questions to evaluate.

    Through `validate_evidence_trace(load_evidence_trace())` — the chained gate
    every other consumer uses — so this evaluation and the runtime cannot
    disagree about what the golden dataset says.

    **Two fields are used to evaluate: `id` and `question`.**
    `expected_outcome` is read for dataset composition in the printed
    provenance and takes no part in any metric. **`expected_answer`,
    `expected_chunk` and `expected_metrics` are not read at all** — none is the
    reference of any of the four metrics, and
    `evaluation/generation_metrics.py` refuses a case carrying one.
    """
    return list(validate_evidence_trace(load_evidence_trace())["evidence_trace"])


def generate_cases(entries: list, client: DeepSeekClient) -> tuple:
    """Run the repository's pipeline for every entry and shape the cases.

    The hybrid route exactly as `scripts/run_generation.py` reaches it: both legs
    at `ROUTE_TOP_K`, fused by `sample_rag/fusion.py` through `fuse_routes`, in
    the canonical tie-break order the corpus defines, resolved and assembled by
    `ContextBuilder` and answered by `ModelGenerator`. **No ranking, depth,
    fusion, assembly or generation decision is taken here.**

    Returns the metric cases, the diagnostic rows, and the corpus size.

    **The case's `outcome` is the artifact's own `GenerationResult.outcome`**,
    not the golden expectation — the Abstain partition is a statement about what
    the system asserted.

    **The assembled context is checked, not assumed.** `ContextBuilder.assemble`
    joins the chunk texts with its own separator; this rebuilds the same list and
    verifies the join equals `prompt.context` byte for byte, so the block the
    Faithfulness judge sees is the block the model saw. A mismatch raises rather
    than being measured.

    **`statements` and `supporting_evidence` leave this function as diagnostics
    only.** They are not placed in a case; the engine would refuse one that
    carried them.

    **The two expensive imports happen here**, not at module scope, and this is
    the first point in the process at which they are permitted: `main` has
    already parsed the arguments and resolved `entries` against the committed
    dataset, so nothing below can run for an invocation the selection layer
    would have refused. Nothing else about this function changed.
    """
    from sample_rag.vector_runtime import VectorIndexRuntime
    from scripts.run_hybrid_retrieval import (
        FUSED_ROUTE,
        canonical_order,
        fuse_routes,
        lexical_route,
        load_documents,
        semantic_route,
    )

    chunks = load_corpus()
    canonical_ids = load_canonical_documents()
    order = canonical_order(chunks, canonical_ids)

    retriever = Retriever(chunks, canonical_ids)
    runtime = VectorIndexRuntime(chunks, load_documents())
    runtime.index()

    builder = ContextBuilder(chunks)
    generator = ModelGenerator(client, retrieval_route=FUSED_ROUTE)

    cases = []
    diagnostics = []
    for entry in entries:
        question = entry["question"]
        fused = fuse_routes(
            semantic_route(runtime, question),
            lexical_route(retriever, question),
            order,
        )
        assembled = builder.resolve(fused)
        prompt = builder.assemble(assembled, question)
        result = generator.generate(prompt)

        passages = [
            {"chunk_id": chunk["id"], "text": chunk["text"]} for chunk in assembled
        ]
        if CONTEXT_SEPARATOR.join(passage["text"] for passage in passages) != prompt.context:
            raise GenerationMetricsError(
                f"The assembled context for case {entry['id']!r} does not "
                f"reconstruct Prompt.context, so the evidence frame is not the "
                f"prompt the model was given."
            )

        cases.append(
            {
                "id": entry["id"],
                "question": question,
                "answer_text": result.answer_text,
                "outcome": result.outcome,
                "context": passages,
            }
        )
        diagnostics.append(
            {
                "id": entry["id"],
                "outcome": result.outcome,
                "statements": len(result.statements),
                "attributed_chunk_ids": sorted(
                    {
                        evidence.chunk_id
                        for statement in result.statements
                        for evidence in statement.supporting_evidence
                    }
                ),
            }
        )

    return cases, diagnostics, len(chunks)


def report_scores(report: dict, cases: list, diagnostics: list, entries: list, corpus_size: int, model: str) -> None:
    """Print the evaluation evidence.

    Structured so a reader can check a score against what produced it:
    provenance first, then the metric definitions and the aggregation rule, then
    the numbers, then the per-case rows, then the per-claim evidence. **No
    judgement about the numbers is printed** — no threshold exists in any
    repository authority, and this script has no basis for one.

    The system's own attribution is printed in its own section, labelled as
    diagnostic, so a reader can compare what the system cited against what the
    judge found without either being mistaken for the other.

    The route constants are imported here for the same reason `generate_cases`
    imports its own: they live in `scripts/run_hybrid_retrieval.py`, whose import
    chain is expensive. This function only ever runs after an evaluation has
    completed, so the module is already loaded and the import costs nothing at
    this point — it is written this way so that **no path through this file can
    reach the heavy chain without having been authorized first.**
    """
    from scripts.run_hybrid_retrieval import FUSED_ROUTE, ROUTE_TOP_K

    expected = [entry["expected_outcome"] for entry in entries]
    observed = [case["outcome"] for case in cases]
    faithfulness = report["faithfulness"]
    groundedness = report["groundedness"]
    hallucination = report["hallucination_rate"]
    relevancy = report["answer_relevancy"]

    print("M2-08 native generation-quality evaluation")
    print()
    print("Provenance")
    print("  dataset                      datasets/golden/resume_evidence_trace.json")
    print(f"  entries                      {len(entries)}")
    print(f"  expected_outcome Answer      {expected.count(ANSWER_OUTCOME)}")
    print(f"  expected_outcome Abstain     {expected.count(ABSTAIN_OUTCOME)}")
    print(f"  observed outcome Answer      {observed.count(ANSWER_OUTCOME)}")
    print(f"  observed outcome Abstain     {observed.count(ABSTAIN_OUTCOME)}")
    print(f"  corpus chunks                {corpus_size}")
    print(f"  retrieval route              {FUSED_ROUTE} (top_k {ROUTE_TOP_K})")
    print("  generation                   sample_rag/model_generator.py")
    print("  metric engine                evaluation/generation_metrics.py")
    print("  judge provider               DeepSeek")
    print(f"  judge model                  {model}")
    print()
    print("Semantics")
    print("  claim unit                   one claim of the delivered answer_text")
    print("                               decomposed without the context in view")
    print("  faithfulness                 supported claims / claims")
    print("                               judged against the whole assembled context")
    print("  groundedness                 claims carried by one passage alone / claims")
    print("                               each passage judged in isolation")
    print("  hallucination_rate           unsupported or contradicted claims / claims")
    print("                               NOT computed as 1 - faithfulness")
    print("  answer_relevancy             answers that are DIRECT, COMPLETE and ONLY")
    print("                               judged against the question alone")
    print("  aggregation                  macro (per case) and micro (per claim), both")
    print("                               answer_relevancy: one figure, macro == micro")
    print("  determinism                  NOT deterministic — a live judge and a")
    print("                               synthesized answer both contribute")
    print()
    for title, block, metric, counted in (
        ("Faithfulness", faithfulness, "faithfulness", "claims_faithful"),
        ("Groundedness", groundedness, "groundedness", "claims_grounded"),
        ("Hallucination Rate", hallucination, "hallucination_rate", "claims_hallucinated"),
    ):
        print(f"{title} — Answer outcomes (the metric's domain)")
        print(f"  cases measured               {block['cases_measured']} of {block['cases_evaluated']}")
        print(f"  cases without claims         {block['cases_without_claims']} (Abstain — no denominator)")
        print(f"  claims                       {block['claims_total']}")
        print(f"  claims counted               {block[counted]}")
        print(f"  macro                        {block[f'{metric}_macro']}")
        print(f"  micro                        {block[f'{metric}_micro']}")
        print()
    print("Answer Relevancy — Answer outcomes (the metric's domain)")
    print(f"  cases measured               {relevancy['cases_measured']} of {relevancy['cases_evaluated']}")
    print(f"  cases undefined              {relevancy['cases_undefined']} (Abstain — M2.08 report U-3)")
    print(f"  answers relevant             {relevancy['answers_relevant']}")
    print(f"  judged DIRECT                {relevancy['answers_direct']}")
    print(f"  judged COMPLETE              {relevancy['answers_complete']}")
    print(f"  judged ONLY                  {relevancy['answers_only']}")
    print(f"  answer_relevancy             {relevancy['answer_relevancy']}")
    print()
    print("Instrument consistency")
    print(f"  grounded but not faithful    {report['instrument']['grounded_but_not_faithful']}")
    print("                               a definition violation, not a result;")
    print("                               grounded implies faithful")
    print()
    print("Per case")
    for row in report["per_case"]:
        print(
            f"  {row['id']:<38} "
            f"{row['outcome']:<8} "
            f"F {str(row['faithfulness']):<7} "
            f"G {str(row['groundedness']):<7} "
            f"H {str(row['hallucination_rate']):<7} "
            f"AR {row['answer_relevancy']}"
        )
    print()
    print("Per case evidence")
    for row in report["per_case"]:
        print(f"  {row['id']}")
        if row["unmeasured_reason"]:
            print(f"    claims unmeasured  {row['unmeasured_reason']}")
        for claim in row["claims"]:
            print(f"    claim              {claim['claim']}")
            print(
                f"      support          {claim['support_verdict']}  "
                f"faithful={claim['faithful']}  "
                f"hallucinated={claim['hallucinated']}"
            )
            print(
                f"      grounded         {claim['grounded']}  "
                f"by {claim['grounding_chunk_id']}"
            )
            for passage in claim["passages"]:
                print(f"        {passage['chunk_id']}  {passage['verdict']}")
        if row["relevancy_unmeasured_reason"]:
            print(f"    relevancy undefined  {row['relevancy_unmeasured_reason']}")
        else:
            verdicts = row["relevancy_verdicts"]
            print(
                f"    relevancy          {verdicts['direct']}  "
                f"{verdicts['complete']}  {verdicts['only']}"
            )
    print()
    print("System attribution — diagnostic only, not a metric reference")
    for row in diagnostics:
        print(
            f"  {row['id']:<38} {row['outcome']:<8} "
            f"statements {row['statements']:<3} "
            f"cited {','.join(row['attributed_chunk_ids']) or '-'}"
        )


def build_parser() -> argparse.ArgumentParser:
    """The selection/authorization parser — the first thing the process does.

    **Two mutually exclusive selections, and neither is a default.** An
    invocation that names no selection is a usage error, so **full-dataset
    evaluation is unreachable without `--all`** and a subset is unreachable
    without naming a case. `argparse` owns the usage text, the `--help` exit and
    the exit code, exactly as `scripts/cli.py` records: *"argument validation is
    argparse's responsibility"*, and its errors go to stderr with exit `2`.

    **`--help` returns here and never reaches `main`'s body**, which is what
    makes the guarantee structural rather than a matter of statement order.

    `prog` names the module form because that is the repository's invocation
    convention throughout — `python3 -m scripts.<name>`, as every other script's
    docstring and every `docs/` reference uses. `scripts/` modules import one
    another (`from scripts.run_retrieval import …`), so the package form is the
    one under which this file's own imports resolve.

    **No selection mode beyond these two is offered.** No `--limit`, `--subset`,
    `--sample`, `--index` or `--ids`: a selection that is neither *one named case*
    nor *the whole committed dataset* would produce a figure over cases someone
    chose, which is the thing this guard exists to prevent.
    """
    parser = argparse.ArgumentParser(
        prog="python3 -m scripts.evaluate_generation",
        description=(
            "Evaluate generation quality (M2-08) over the committed golden "
            "dataset. Performs real provider calls: one generation call per "
            "selected case, plus judge calls per claim. A selection is "
            "required — there is no implicit full-dataset run."
        ),
    )
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument(
        "--case-id",
        metavar="ID",
        help=(
            "Evaluate exactly the one committed golden entry with this id. "
            "The id is validated against the dataset before any model, index "
            "or provider work begins."
        ),
    )
    selection.add_argument(
        "--all",
        action="store_true",
        help=(
            "Evaluate every committed golden entry. This is the only way to "
            "authorize a full-dataset run."
        ),
    )
    return parser


def select_entries(entries: list, arguments: argparse.Namespace) -> list:
    """Resolve the requested selection against the committed golden entries.

    **A pure function over data that is already in memory.** It constructs no
    client, touches no index, loads no model and reaches no network, so every
    refusal below costs nothing — which is the property that makes an unknown
    case id cheap rather than expensive.

    **Selection happens here, and generation happens after.** The returned list
    is what `generate_cases` receives, so a single-case run generates one case;
    it does not generate the dataset and filter afterwards, which would spend the
    whole provider budget to report one row.

    **The committed dataset is the source of truth.** No count, id or subset is
    written into this function; it resolves against whatever
    `datasets/golden/resume_evidence_trace.json` currently holds, so adding or
    removing a golden entry changes what `--all` means without changing this
    code.

    Entry contents, ids and dataset order are preserved exactly — `--all`
    returns the entries as loaded, and `--case-id` returns the one entry object
    itself, not a copy or a projection of it.
    """
    if arguments.all:
        return list(entries)

    if not arguments.case_id:
        raise SelectionError(
            "a selection is required: pass --case-id ID to evaluate one "
            "committed golden entry, or --all to authorize a full-dataset "
            "evaluation"
        )

    selected = [entry for entry in entries if entry["id"] == arguments.case_id]
    if not selected:
        raise SelectionError(
            f"unknown --case-id {arguments.case_id!r}; it is not an id in "
            f"datasets/golden/resume_evidence_trace.json "
            f"({len(entries)} entries)"
        )
    return selected


def main(argv: list = None) -> int:
    """Evaluate the selected golden entries and report what was measured.

    Composition only: parsing, selection, loading, retrieval, assembly,
    generation, judging, aggregation, reporting. No branch decides anything
    about the domain.

    **The order of the first four statements is the safety property**, and it is
    the reason this function reads the way it does:

        parse_args            `--help`, an unknown flag and `--case-id` with
                              `--all` all exit here, inside argparse
              ↓
        load_reference_entries    a JSON read and its existing validation gate;
                              no model, no index, no provider
              ↓
        select_entries        an unknown id or a missing selection exits here
              ↓
        DeepSeekClient        the first provider object in the process
              ↓
        generate_cases        the first expensive import, and the first model
                              load, retrieval and generation — over the
                              **selected** entries only

    Nothing above `generate_cases` can load a model or reach a provider, so
    every refusal is free. **`generate_cases` receives the selected entries**,
    which is what makes a single-case run cost one generation rather than
    twenty-two.

    **Failures are not caught**, deliberately and on `scripts/run_generation.py`'s
    precedent. `ProviderConfigurationError`, `ProviderRequestError`,
    `ProviderResponseError`, `GenerationInputError` and `GenerationMetricsError`
    each propagate with their own name: a run that could not read a verdict
    produces no score rather than a score with a guess in it, and
    `sample_rag/deepseek.py` performs no retry, so neither does this.
    `SelectionError` is the one exception this function does convert, into
    argparse's own usage error, so a refused selection exits the way every other
    bad invocation in this repository exits.
    """
    parser = build_parser()
    arguments = parser.parse_args(argv)

    entries = load_reference_entries()
    try:
        selected = select_entries(entries, arguments)
    except SelectionError as refusal:
        parser.error(str(refusal))

    client = DeepSeekClient()
    cases, diagnostics, corpus_size = generate_cases(selected, client)

    # The whole of the RO-18 Decision 4 reuse: the existing sanctioned boundary,
    # called through its existing method, adapted to the engine's provider-free
    # `judge(prompt) -> str` seam. No client is created, modified or wrapped in a
    # second architecture; no credential passes through this line.
    def judge(prompt: str) -> str:
        return client.complete([{"role": "user", "content": prompt}])

    report = compute(cases, judge)

    # `selected`, not `entries`: the provenance block states what was actually
    # evaluated, so a single-case run reports one entry rather than describing a
    # dataset it did not measure.
    report_scores(report, cases, diagnostics, selected, corpus_size, client.model)
    return 0


if __name__ == "__main__":
    sys.exit(main())
