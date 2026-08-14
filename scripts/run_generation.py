"""End-to-end model-backed generation over the committed corpus — Sprint M2.06.

The runtime path `docs/GENERATION_CONTRACT.md` §24.2 states, executed against
the real corpus and the real provider:

    retrieval -> ordered chunk ids -> ContextBuilder -> Prompt
              -> Generator -> provider -> GenerationResult

**This is M2-06's answer to U-3**, and it is deliberately the smallest one
available. RO-13 left *"how the runtime reaches this contract"* to M2-06 while
authorizing **no** orchestration layer, runtime adapter, pipeline coordinator or
`ContextEngine`, and while leaving `evaluation/altm_rules.py` `REACHABLE_STAGES`
un-widened. None of those is created here.

Why a `scripts/run_*.py` and not something new
------------------------------------------------
`docs/architecture.md` §6 gives `scripts/` exactly this responsibility —
*"Operational scripts … not pipeline logic"* — and the repository already holds
four instances of the pattern: `run_retrieval.py`, `run_hybrid_retrieval.py`,
`compare_retrieval_routes.py` and `evaluate_retrieval.py`. **This is a fifth
instance of an existing seam, not a new mechanism.** No class is introduced, no
abstraction is added, nothing is registered, and no module in `sample_rag/`
learns about composition.

**Nothing here is re-implemented.** Every stage is called through the function
that already owns it: `load_corpus`, `load_canonical_documents` and
`load_questions` are `scripts/run_retrieval.py`'s; `canonical_order`,
`load_documents`, `semantic_route`, `lexical_route` and `fuse_routes` are
`scripts/run_hybrid_retrieval.py`'s, unmodified and imported rather than copied.
So this script cannot disagree with the retrieval runtime the repository already
measures about what the corpus is, how it is ranked, or what fusion returns —
which is the property that makes the generation observed here a generation over
*the repository's* retrieval rather than a second one built to suit it.

**`scripts/cli.py` is unchanged.** The Milestone 1A entry point keeps its
Milestone 1A chain (`Retriever.retrieve -> Generator.generate`) and its frozen
byte-identical reproducibility (`docs/P3.7.6_…` §4). It is not rewired here, and
`docs/M2.06_Generation_Report.md` records why: a CLI driving a model would put a
live provider call inside the deterministic pytest suite and would retire
acceptance evidence P3.7.6 froze — neither of which RO-13 authorized, and neither
of which is an implementing sprint's decision to take.

What this script is for
-------------------------
Two things, and it says which is which rather than blurring them:

1. **The runtime reachability evidence for U-3** — that the chain above exists
   and executes.
2. **The real-provider acceptance check for M2-06** — that a `Prompt` built from
   the committed corpus reaches DeepSeek, is accepted, and comes back as a
   mappable `GenerationResult`.

**It is not part of the deterministic pytest suite and must never become one.**
`tests/test_model_generator.py` specifies generation against injected fakes; this
performs the one real call, on demand, from a terminal.

What it does not establish
----------------------------
**A successful run is evidence of reachability and mapping. It is not evidence
of answer quality.** No faithfulness, groundedness, hallucination, answer
relevancy, context precision or context recall claim is made or measurable here,
and none may be read out of a successful call — §24.3 keeps those as later
evaluation work (**M2-07**, **M2-08**), and Ragas, DeepEval and Promptfoo are
untouched.

Latency is measured and reported as **sprint evidence only**.
`docs/GENERATION_CONTRACT.md` §15 defers `generation_time_ms` and §24.4 leaves
that deferral standing, so it is printed here and enters no artifact.

Credential handling
--------------------
`DEEPSEEK_API_KEY` is consumed by `sample_rag/deepseek.py` from the process
environment. **This script never reads it, never receives it, never prints it and
never accepts it as an argument.** Its presence is not even reported as a
boolean — a failed run reports `ProviderConfigurationError` by name, which says
what an operator needs and nothing about the value.
"""

import argparse
import sys
import time

from sample_rag.context_builder import ContextBuilder
from sample_rag.deepseek import DeepSeekClient
from sample_rag.generator import serialize
from sample_rag.model_generator import ModelGenerator
from sample_rag.retriever import Retriever
from sample_rag.vector_runtime import VectorIndexRuntime

from scripts.run_hybrid_retrieval import (
    FUSED_ROUTE,
    ROUTE_TOP_K,
    canonical_order,
    fuse_routes,
    lexical_route,
    load_documents,
    semantic_route,
)
from scripts.run_retrieval import load_canonical_documents, load_corpus


def parse_args(argv: list = None) -> argparse.Namespace:
    """Parse the script's single argument.

    `--question` is required, so an invocation without it is an argparse usage
    error — the same convention `scripts/cli.py` follows, and for the same
    reason: argument validation is argparse's responsibility and is not
    re-implemented.
    """
    parser = argparse.ArgumentParser(
        prog="python -m scripts.run_generation",
        description=(
            "Answer a question over the committed corpus through the hybrid "
            "retrieval route and model-backed generation. Performs one real "
            "provider call."
        ),
    )
    parser.add_argument(
        "--question",
        required=True,
        help="The question to answer against the committed Chunk Corpus.",
    )
    return parser.parse_args(argv)


def assemble_prompt(question: str):
    """Run the repository's retrieval and assemble the `Prompt` it produces.

    The first four stages of §24.2's pipeline, each delegated to the component
    that owns it. Returns the `Prompt` and the corpus size, the latter only so
    the report can state what the retrieval was performed over.

    **No ranking decision is taken here.** The fused order is
    `sample_rag/fusion.py`'s, reached through `scripts/run_hybrid_retrieval.py`'s
    own route functions, and `ContextBuilder.resolve` preserves it positionally.
    Nothing sorts, filters, re-weights, truncates or budgets between fusion and
    assembly — `ROUTE_TOP_K` is the repository's existing retrieval depth and is
    not varied, because searching over it is retrieval optimization (**M2-15**).
    """
    chunks = load_corpus()
    canonical_ids = load_canonical_documents()
    order = canonical_order(chunks, canonical_ids)

    retriever = Retriever(chunks, canonical_ids)
    runtime = VectorIndexRuntime(chunks, load_documents())
    runtime.index()

    fused = fuse_routes(
        semantic_route(runtime, question),
        lexical_route(retriever, question),
        order,
    )

    builder = ContextBuilder(chunks)

    return builder.assemble(builder.resolve(fused), question), len(chunks)


def report(prompt, result, corpus_size: int, model: str, elapsed_ms: float) -> None:
    """Print the safe evidence this check is permitted to record.

    **Recorded:** provider, selected model, corpus size, assembled chunk count,
    outcome, statement and span counts, whether response mapping succeeded, and
    latency.

    **Not recorded, ever:** the API key, the authorization header, any
    environment value, or any other secret. The raw provider response is not
    persisted either — nothing in the repository authorizes storing it, and
    `docs/GENERATION_CONTRACT.md` §13.3 keeps `GenerationResult` a runtime
    artifact that is never written to `datasets/`, `reports/` or `sample_rag/`.
    The serialized artifact goes to stdout for a human to read; this script
    writes no file.

    The answer text is printed because it is the point of the exercise. **No
    judgement about it is printed**, because this script has no basis for one.
    """
    spans = sum(len(statement.supporting_evidence) for statement in result.statements)

    print("M2-06 real-provider acceptance check")
    print(f"  provider                     DeepSeek")
    print(f"  model                        {model}")
    print(f"  corpus chunks                {corpus_size}")
    print(f"  retrieval route              {FUSED_ROUTE} (top_k {ROUTE_TOP_K})")
    print(f"  assembled chunks             {len(prompt.chunk_ids)}")
    print(f"  provenance records           {len(prompt.provenance)}")
    print(f"  context characters           {len(prompt.context)}")
    print(f"  provider call                accepted")
    print(f"  response mapping             succeeded")
    print(f"  outcome                      {result.outcome}")
    print(f"  statements                   {len(result.statements)}")
    print(f"  supporting evidence spans    {spans}")
    print(f"  latency (sprint evidence)    {round(elapsed_ms, 1)} ms")
    print()
    print("GenerationResult")
    sys.stdout.write(serialize(result))


def main(argv: list = None) -> int:
    """Execute one question end to end and report what happened.

    Composition only: every statement is argument parsing, component
    construction, component invocation, measurement or reporting. No branch
    decides anything about the domain.

    **Failures are not caught here**, deliberately. A `ProviderConfigurationError`,
    `ProviderRequestError`, `ProviderResponseError` or `GenerationInputError`
    propagates with its own name and its own message, which is what makes the
    failure semantics observable at the seam that produced them. Catching them to
    print a friendlier line would collapse four distinct conditions into one exit
    code and hide exactly the distinction M2-06 exists to establish.
    """
    arguments = parse_args(argv)
    prompt, corpus_size = assemble_prompt(arguments.question)

    client = DeepSeekClient()
    generator = ModelGenerator(client, retrieval_route=FUSED_ROUTE)

    started = time.perf_counter()
    result = generator.generate(prompt)
    elapsed_ms = (time.perf_counter() - started) * 1000

    report(prompt, result, corpus_size, client.model, elapsed_ms)
    return 0


if __name__ == "__main__":
    sys.exit(main())
