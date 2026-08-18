"""Native Context Precision / Context Recall evaluation — Sprint M2.07.

The on-demand entry point Repository Owner ruling **RO-17** authorizes:

    committed golden dataset
          ->  explicit selection: --case-id ID, or --all
          ->  real retrieval (semantic + lexical + RRF, unmodified)
          ->  evaluation/context_metrics.py
          ->  DeepSeek judge, through the one sanctioned provider boundary
          ->  Context Precision / Context Recall
          ->  evidence printed for a human to read

**This is not part of the deterministic pytest suite and must never become
one.** RO-14 Decision 2 — carried forward verbatim by RO-17 Decision 4 — reads
*"No provider call is introduced into the deterministic pytest suite, and none
may be"*, and **a judge call is a provider call**. `tests/test_context_metrics.py`
specifies the metric engine against a non-networked substitute; this performs
the real judging, on demand, from a terminal. It is the sixth instance of the
`scripts/run_*.py` / `scripts/evaluate_*.py` pattern
(`docs/architecture.md` §6 — *"Operational scripts … not pipeline logic"*), not
a new mechanism.

Nothing runs without an explicit selection
--------------------------------------------
Every real run of this script spends provider budget — judge calls per retrieved
passage and per reference claim — and loads the embedding model and the vector
index, so **there is no default and no implicit full-dataset run**. `--case-id ID`
evaluates exactly one committed golden entry; `--all` is the only thing that
authorizes the whole dataset; any other invocation, including none at all, is a
usage error that exits before a model, an index or a provider object exists.

**Selection changes the entry set and nothing else.** The selected entries are
handed to `retrieve_cases` — the same function, calling the same retrieval
stages, in the same order — so a single-case run performs the repository's
retrieval once rather than performing it twenty-two times and discarding
twenty-one results. The evaluator is being made safer to execute, not redefined:
§"Retrieval is measured, never modified" below is unchanged in every part, and
so is `evaluation/context_metrics.py`.

Retrieval is measured, never modified
---------------------------------------
**M2-07 is MEASURE, not IMPROVE.** Every retrieval stage below is called through
the function that already owns it — `load_corpus`, `load_canonical_documents`
from `scripts/run_retrieval.py`; `canonical_order`, `load_documents`,
`semantic_route`, `lexical_route`, `fuse_routes` and `ROUTE_TOP_K` from
`scripts/run_hybrid_retrieval.py` — imported rather than copied, exactly as
`scripts/run_generation.py` does. Nothing here sorts, filters, re-weights,
truncates, reranks or budgets anything, no `top_k` is chosen, no RRF constant is
restated and no threshold is introduced. So the retrieval this script measures
is *the repository's* retrieval rather than a second one arranged to score well,
and a change in the measurement cannot be a change in the system.

`sample_rag/fusion.py`, `sample_rag/embedding.py`, `sample_rag/vector_index.py`,
`sample_rag/retriever.py`, `sample_rag/context_builder.py`, the chunking, the
prompts and `ModelGenerator` are all untouched by this sprint.

The judge, and the boundary it reuses
---------------------------------------
**RO-17 Decision 4** independently authorizes `sample_rag/deepseek.py` as
M2-07's evaluation-judge boundary, *"conditional on technical reuse"* — it holds
only if the native implementation can use the existing boundary without
modifying its provider architecture, changing its credential model, adding
another provider integration or SDK, adding a model router, or adding arbitrary
HTTP access.

**The condition is satisfied, and the finding is that nothing had to change.**
`DeepSeekClient.complete(messages) -> str` is already the whole of what a judge
needs, so the adapter below is one lambda over the existing method.
`sample_rag/deepseek.py` is **not modified, not subclassed and not wrapped in a
second client**; no alternate provider client exists; no SDK, router, session,
retry, backoff or HTTP primitive is introduced here. The evaluation engine holds
no provider concept at all — it takes a `judge(prompt: str) -> str` callable —
so the provider shape is adapted at this seam and nowhere else.

Credential handling
--------------------
`DEEPSEEK_API_KEY` is consumed by `sample_rag/deepseek.py` from the process
environment. **This script never reads it, never receives it, never prints it,
never accepts it as an argument and does not report its presence as a boolean.**
A run without it fails as `ProviderConfigurationError` by name, which is what an
operator needs and says nothing about the value.

What is recorded, and what is deliberately not
------------------------------------------------
**Recorded:** dataset identity and digest, entry counts and composition, the
retrieval route and depth, the judge's provider and model, the metric
definitions and aggregation rule, both scores under both aggregations, and the
per-case evidence that explains them — per passage a rank, a chunk id and a
relevance verdict; per reference claim its text and an attribution verdict.

**Never recorded, in stdout or anywhere else:** the credential, the
authorization header, any raw judge request payload, any raw judge response
payload, any other provider metadata. A verdict and a parsed claim are the
*derived evaluation evidence* the metric is computed from and cannot be
explained without; the payloads that carried them are not, and
`evaluation/context_metrics.py` never returns them, so there is nothing here to
suppress. This is `sample_rag/deepseek.py`'s and `scripts/execution_trace.py`'s
discipline, unchanged.

**This script writes no file.** The M2-18 execution trace is untouched — no
trace field is added, `scripts/execution_trace.py` is not imported, and RO-17
Decision 9 keeps M2-18 ✅ DISCHARGED and unmodified. `reports/baseline/` and
`reports/regressions/` are **M3-03** scaffolds and are not populated.

What a score here does and does not establish
-----------------------------------------------
**A number is evidence, not a verdict.** No repository authority states a target,
a threshold or an acceptance criterion for either metric, so this script prints
no pass, fail, good or bad and computes no comparison against one. Inventing a
threshold to declare success would be this sprint asserting a standard no
authority set.

Neither metric is deterministic. The judge is a live model; the recall
denominator is itself a judge product. Two runs may differ, and the printed
evidence is what a reader checks a run against.
"""

import argparse
import sys

from sample_rag.deepseek import DeepSeekClient
from sample_rag.retriever import Retriever

from evaluation.context_metrics import aggregate_recall, compute
from scripts.build_evidence_trace import load_evidence_trace, validate_evidence_trace
from scripts.run_retrieval import load_canonical_documents, load_corpus

# `sample_rag.vector_runtime` and `scripts.run_hybrid_retrieval` are **deliberately
# absent from this import block**, and the absence is measured rather than assumed.
#
#     scripts/evaluate_context.py
#       └─ sample_rag.vector_runtime          heavy
#            └─ sample_rag.embedding
#                 └─ sentence_transformers  ->  torch, transformers
#            └─ sample_rag.vector_index      ->  faiss
#       └─ scripts.run_hybrid_retrieval       heavy
#            └─ sample_rag.vector_runtime         (the same chain)
#
# Every other import in this module measures at or below 0.2 s and pulls no
# machine-learning library at all. Importing those two loads `torch`,
# `transformers`, `sentence_transformers` and `faiss` into the process **merely
# because the module was imported** — before `main` runs, and therefore before
# argument parsing could possibly refuse the invocation.
#
# `--help`, a missing selection, an unknown flag and an unknown case id must all
# cost nothing, so the two heavy imports are performed **inside** the functions
# that need them, which run only after selection has been validated. No model
# weight is loaded at import time in either case — that happens later still, when
# `VectorIndexRuntime` is constructed and indexed — but the library import is real
# work and is what this arrangement defers.
#
# This is the whole of the laziness: no other import is moved, no name is
# rebound, and nothing about the pipeline below changes.

# The golden outcome whose reference answer states information the corpus
# contains. See `partition` for why Context Recall is reported over this subset
# as well as over the whole dataset.
ANSWER_OUTCOME = "Answer"


class SelectionError(Exception):
    """Raised when the requested selection cannot be resolved against the dataset.

    An independent, flat exception type, following the repository's
    per-responsibility pattern (`ContextMetricsError`, `GenerationMetricsError`,
    `RetrievalMetricsError`, …). It is raised **before** any model, index or
    provider object exists, and `main` converts it into argparse's own usage
    error so the process exits non-zero through the mechanism `scripts/cli.py`
    already records as *"argument validation is argparse's responsibility"*.
    """


def load_reference_entries() -> list:
    """Read the Evidence Trace Dataset as the evaluation reference.

    Through `validate_evidence_trace(load_evidence_trace())` — the chained gate
    every other consumer uses — so this evaluation and the retrieval runtime
    cannot disagree about what the golden dataset says.

    **Three fields are read: `id`, `question` and `expected_answer`**, plus
    `expected_outcome` for partitioning. **`expected_chunk` is deliberately not
    read**, here or in `evaluation/context_metrics.py`: recall over expected
    chunk identifiers is `chunk_recall_at_k`, which
    `docs/P3.3.3_Retrieval_Metrics_Report.md` §3 records as explicitly not this
    metric, and RO-17 Decision 1 bars publishing that arithmetic under this name.

    `expected_answer` is the reference because it is the **independently
    authored** statement of what the source says in answer to the question —
    committed, and existing entirely independently of any retrieval result.
    """
    return list(validate_evidence_trace(load_evidence_trace())["evidence_trace"])


def retrieve_cases(entries: list) -> tuple:
    """Execute the repository's retrieval for every entry and shape the cases.

    The hybrid route exactly as `scripts/run_generation.py` reaches it: both
    legs at `ROUTE_TOP_K`, fused by `sample_rag/fusion.py` through
    `fuse_routes`, in the canonical tie-break order the corpus defines. **No
    ranking, depth or fusion decision is taken here.**

    Chunk text is resolved from the committed corpus by id, preserving fused
    rank order positionally — the same thing `ContextBuilder.resolve` does for
    generation, done here without importing it, because this evaluation needs
    the retrieved passages themselves rather than an assembled prompt.

    **The two expensive imports happen here**, not at module scope, and this is
    the first point in the process at which they are permitted: `main` has
    already parsed the arguments and resolved `entries` against the committed
    dataset, so nothing below can run for an invocation the selection layer would
    have refused. **`entries` is the selected set**, so the loop below runs once
    per selected entry — a single-case run retrieves once. Nothing else about
    this function changed: the same stages, called through the same owning
    functions, in the same order, at the same depth.
    """
    from sample_rag.vector_runtime import VectorIndexRuntime
    from scripts.run_hybrid_retrieval import (
        canonical_order,
        fuse_routes,
        lexical_route,
        load_documents,
        semantic_route,
    )

    chunks = load_corpus()
    canonical_ids = load_canonical_documents()
    order = canonical_order(chunks, canonical_ids)
    text_of = {chunk["id"]: chunk["text"] for chunk in chunks}

    retriever = Retriever(chunks, canonical_ids)
    runtime = VectorIndexRuntime(chunks, load_documents())
    runtime.index()

    cases = []
    for entry in entries:
        question = entry["question"]
        fused = fuse_routes(
            semantic_route(runtime, question),
            lexical_route(retriever, question),
            order,
        )
        cases.append(
            {
                "id": entry["id"],
                "question": question,
                "reference_answer": entry["expected_answer"],
                "retrieved": [
                    {"chunk_id": chunk_id, "text": text_of[chunk_id]}
                    for chunk_id in fused
                ],
            }
        )

    return cases, len(chunks)


def partition(report: dict, entries: list) -> dict:
    """Re-aggregate Context Recall over the entries whose reference asserts
    information the corpus contains.

    **Why the dataset is partitioned, and why both partitions are published.**
    Two of the twenty-two golden entries carry `expected_outcome: "Abstain"`,
    and their reference answers open with an *absence* claim — *"The resume does
    not state any Kubernetes experience"*, *"The resume does not state
    compensation for any role"*. Context Recall's denominator is, in the
    repository's own words, *"everything relevant that **exists** in the
    source"*; a claim about what the source does **not** contain is not
    information retrieval could recover, and the Retrieve stage cannot establish
    absence from a top-k window in any case — five retrieved passages not
    containing a fact is not the corpus not containing it.

    So the Answer-only figure is the domain-faithful one. **The all-entries
    figure is published beside it rather than instead of it**, because a
    partition that only ever appears as a filtered number is indistinguishable
    from a partition chosen for its number. Both are printed, the difference is
    visible, and no golden entry is modified, excluded from the dataset or
    rewritten to suit the metric.

    Context Precision is **not** partitioned: whether a retrieved passage is
    relevant to a question is well defined for an abstention question too, and
    both abstention entries carry expected evidence chunks of their own.
    """
    outcome_of = {entry["id"]: entry["expected_outcome"] for entry in entries}
    answer_rows = [
        row for row in report["per_case"] if outcome_of[row["id"]] == ANSWER_OUTCOME
    ]

    return {
        "all_entries": report["context_recall"],
        "answer_entries": aggregate_recall(answer_rows),
    }


def report_scores(report: dict, recall: dict, entries: list, corpus_size: int, model: str) -> None:
    """Print the evaluation evidence.

    Structured so a reader can check the score against what produced it:
    provenance first, then the metric definitions and the aggregation rule, then
    the numbers, then the per-case rows. **No judgement about the numbers is
    printed** — no threshold exists in any repository authority, and this script
    has no basis for one.

    The route constants are imported here for the same reason `retrieve_cases`
    imports its own: they live in `scripts/run_hybrid_retrieval.py`, whose import
    chain is expensive. This function only ever runs after an evaluation has
    completed, so the module is already loaded and the import costs nothing at
    this point — it is written this way so that **no path through this file can
    reach the heavy chain without having been authorized first.**
    """
    from scripts.run_hybrid_retrieval import FUSED_ROUTE, ROUTE_TOP_K

    outcomes = [entry["expected_outcome"] for entry in entries]
    precision = report["context_precision"]

    print("M2-07 native Context Precision / Context Recall evaluation")
    print()
    print("Provenance")
    print(f"  dataset                      datasets/golden/resume_evidence_trace.json")
    print(f"  entries                      {len(entries)}")
    print(f"  expected_outcome Answer      {outcomes.count(ANSWER_OUTCOME)}")
    print(f"  expected_outcome Abstain     {len(outcomes) - outcomes.count(ANSWER_OUTCOME)}")
    print(f"  corpus chunks                {corpus_size}")
    print(f"  retrieval route              {FUSED_ROUTE} (top_k {ROUTE_TOP_K})")
    print(f"  metric engine                evaluation/context_metrics.py")
    print(f"  judge provider               DeepSeek")
    print(f"  judge model                  {model}")
    print()
    print("Semantics")
    print("  context_precision            relevant retrieved passages / retrieved passages")
    print("                               relevance judged against the question alone")
    print("  context_recall               supported reference claims / reference claims")
    print("                               reference = golden expected_answer, decomposed")
    print("                               without any retrieval input")
    print("  aggregation                  macro (per case) and micro (per unit), both")
    print("  determinism                  NOT deterministic — a live judge contributes")
    print()
    print("Context Precision — all entries")
    print(f"  retrieved passages           {precision['retrieved_passages']}")
    print(f"  judged relevant              {precision['relevant_passages']}")
    print(f"  macro                        {precision['context_precision_macro']}")
    print(f"  micro                        {precision['context_precision_micro']}")
    print()
    print("Context Recall — Answer entries only (the metric's domain)")
    answers = recall["answer_entries"]
    print(f"  cases                        {answers['cases_evaluated']}")
    print(f"  reference claims             {answers['reference_claims']}")
    print(f"  claims supported             {answers['supported_claims']}")
    print(f"  macro                        {answers['context_recall_macro']}")
    print(f"  micro                        {answers['context_recall_micro']}")
    print()
    print("Context Recall — all entries (published beside it, not instead of it)")
    every = recall["all_entries"]
    print(f"  cases                        {every['cases_evaluated']}")
    print(f"  reference claims             {every['reference_claims']}")
    print(f"  claims supported             {every['supported_claims']}")
    print(f"  macro                        {every['context_recall_macro']}")
    print(f"  micro                        {every['context_recall_micro']}")
    print()
    print("Per case")
    for row in report["per_case"]:
        print(
            f"  {row['id']:<38} "
            f"CP {row['context_precision']:<6} "
            f"({row['relevant_passages']}/{row['retrieved_passages']})   "
            f"CR {row['context_recall']:<6} "
            f"({row['claims_supported']}/{row['claims_total']})"
        )
    print()
    print("Per case evidence")
    for row in report["per_case"]:
        print(f"  {row['id']}")
        for passage in row["passages"]:
            print(
                f"    rank {passage['rank']}  {passage['chunk_id']}  "
                f"{passage['verdict']}"
            )
        for claim in row["claims"]:
            print(f"    claim  {claim['verdict']:<14} {claim['claim']}")
        if row["unmeasured_reason"]:
            print(f"    recall unmeasured  {row['unmeasured_reason']}")


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
        prog="python3 -m scripts.evaluate_context",
        description=(
            "Evaluate Context Precision / Context Recall (M2-07) over the "
            "committed golden dataset. Loads the embedding model and the vector "
            "index and performs real judge calls per retrieved passage and per "
            "reference claim. A selection is required — there is no implicit "
            "full-dataset run."
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

    **Selection happens here, and retrieval happens after.** The returned list is
    what `retrieve_cases` receives, so a single-case run retrieves one case; it
    does not retrieve the dataset and filter afterwards, which would load the
    model, run every route and spend the whole judge budget to report one row.

    **The committed dataset is the source of truth.** No count, id or subset is
    written into this function; it resolves against whatever
    `datasets/golden/resume_evidence_trace.json` currently holds, so adding or
    removing a golden entry changes what `--all` means without changing this
    code.

    Entry contents, ids and dataset order are preserved exactly — `--all`
    returns the entries as loaded, and `--case-id` returns the one entry object
    itself, not a copy or a projection of it. **Nothing about a selected entry is
    rewritten**, so what reaches retrieval is the committed golden entry.
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

    Composition only: parsing, selection, loading, retrieval, judging,
    aggregation, reporting. No branch decides anything about the domain.

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
        retrieve_cases        the first expensive import, and the first model
                              load and retrieval — over the **selected** entries
                              only
              ↓
        DeepSeekClient        the first provider object in the process

    Nothing above `retrieve_cases` can load a model or reach a provider, so every
    refusal is free. **`retrieve_cases` receives the selected entries**, which is
    what makes a single-case run retrieve and judge one case rather than
    twenty-two. The retrieval it performs, and the metric engine it feeds, are
    the pre-existing ones: only the size of the entry set differs.

    **Failures are not caught**, deliberately and on `scripts/run_generation.py`'s
    precedent. `ProviderConfigurationError`, `ProviderRequestError`,
    `ProviderResponseError` and `ContextMetricsError` each propagate with their
    own name: a run that could not read a verdict produces no score rather than
    a score with a guess in it, and `sample_rag/deepseek.py` performs no retry,
    so neither does this. `SelectionError` is the one exception this function
    does convert, into argparse's own usage error, so a refused selection exits
    the way every other bad invocation in this repository exits.
    """
    parser = build_parser()
    arguments = parser.parse_args(argv)

    entries = load_reference_entries()
    try:
        selected = select_entries(entries, arguments)
    except SelectionError as refusal:
        parser.error(str(refusal))

    cases, corpus_size = retrieve_cases(selected)

    client = DeepSeekClient()

    # The whole of the RO-17 Decision 4 reuse: the existing sanctioned boundary,
    # called through its existing method, adapted to the engine's provider-free
    # `judge(prompt) -> str` seam. No client is created, modified or wrapped in
    # a second architecture; no credential passes through this line.
    def judge(prompt: str) -> str:
        return client.complete([{"role": "user", "content": prompt}])

    report = compute(cases, judge)

    # `selected`, not `entries`: the partition and the provenance block both
    # describe what was actually evaluated, so a single-case run reports one
    # entry rather than describing a dataset it did not measure.
    recall = partition(report, selected)

    report_scores(report, recall, selected, corpus_size, client.model)
    return 0


if __name__ == "__main__":
    sys.exit(main())
