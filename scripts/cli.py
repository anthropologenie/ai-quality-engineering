"""Deterministic command-line entry point for the Milestone 1A pipeline.

Sprint P3.6.0: implements `docs/MILESTONE_1A.md` build item 6 — *"ties Knowledge
→ Indexer → Retriever → Assembler → Response Generator (stub) into local,
reproducible runs"* — for the stages this repository implements. `argparse` is
the library that build item's own table names for the CLI (*"Deterministic,
reproducible local execution"*), and this is its first use in the repository.

Composition, not computation
-----------------------------
This module is an orchestration layer and holds no domain behaviour whatsoever.
It implements no retrieval, no generation, no serialization, no evaluation, no
metrics, no diagnosis, and no repository-authority logic. Every one of those
belongs to a component that already owns it, and the CLI's sole responsibility
is to call them in order:

    parse -> load_corpus -> Retriever.retrieve -> Generator.generate
          -> serialize -> stdout -> exit

It plays the same role `scripts/run_retrieval.py`, `scripts/evaluate_retrieval.py`,
`scripts/report_retrieval_metrics.py` and `scripts/diagnose_retrieval.py`
already play, and lives in `scripts/` for the same reason they do: the
dependency direction is `scripts/` → `sample_rag/`, and
`docs/architecture.md` §6 bars the reverse. A CLI inside `sample_rag/` would
have to import `scripts/` to reach `load_corpus`.

Nothing is re-implemented here. `load_corpus` and `DEFAULT_FILTERS` are
`scripts/run_retrieval.py`'s own — the corpus is loaded through the same
`validate_chunks(load_chunks())` gate every other consumer uses
(`docs/CHUNK_VALIDATION_PLAN.md` §P7.1), and the filter mapping is the one the
retrieval runtime already established, so the CLI cannot disagree with
`scripts/run_retrieval.py` about what the corpus is or how retrieval is
parameterized.

Runtime dependency boundary
----------------------------
The permitted chain above, and nothing else. This module does not read the
Knowledge Manifest, the Golden Dataset, the QA Dataset, the Evidence Trace
Dataset, or any evaluation, metrics or diagnosis layer — those authorities are
validation-only, and `docs/GENERATION_CONTRACT.md` §18 records why that matters:
they exist for the repository's own 22 benchmark questions, so a runtime path
that reads one can serve those 22 and nothing else while appearing to work. The
CLI answers an arbitrary question typed at a terminal, which is the whole point
of exposing the pipeline this way.

Runtime artifacts pass through untouched
-----------------------------------------
The `RetrievalResult` the retriever returns is handed to the generator exactly as
received, and the `GenerationResult` the generator returns is handed to
`serialize` exactly as received — the same object, not a copy, a wrapper, a
flattened mapping, or a reconstruction. The CLI never re-orders, filters,
augments or clones a runtime artifact. `serialize` is
`docs/GENERATION_CONTRACT.md` §13.2's form, owned by `sample_rag/generator.py`;
this module chooses no representation of its own.

Output determinism
-------------------
Standard output is exactly `serialize(generation_result)` and nothing else: no
banner, timestamp, colour, progress indicator, elapsed time, completion message
or debug line. `sys.stdout.write` is used rather than `print` for one specific
reason — `print` would append a second newline to a string §13.2 already
terminates with exactly one, and the byte-identity guarantee would be lost to a
formatting convenience.

Determinism therefore inherits from the components: the retriever is a fixed
function of query and corpus, the generator constructs no varying value
(`docs/GENERATION_CONTRACT.md` §12), and this module adds nothing. Two runs of
the same question over the same corpus produce byte-identical stdout.

Exit codes
-----------
`0` on successful execution. Invalid command-line arguments are reported by
`argparse` to **stderr** and exit `2`, argparse's own convention; stdout stays
empty on that path, so the byte-identity guarantee above is never diluted by an
error message.
"""

import argparse
import sys

from sample_rag.generator import Generator, serialize
from sample_rag.retriever import Retriever

from scripts.run_retrieval import DEFAULT_FILTERS, load_canonical_documents, load_corpus


def parse_args(argv: list = None) -> argparse.Namespace:
    """Parse the CLI's single argument.

    `--question` is required, so an invocation without it is an argparse usage
    error: a message on stderr and exit code 2, without this module handling,
    reformatting, or re-reporting it. Argument validation is argparse's
    responsibility and is not re-implemented here.

    `argv` defaults to `sys.argv[1:]`. It is a parameter so a specification can
    exercise the pipeline in-process, which is what makes the runtime-artifact
    identity guarantees observable at all — a subprocess can only be checked at
    the byte level.
    """
    parser = argparse.ArgumentParser(
        prog="python -m scripts.cli",
        description=(
            "Answer a question from the committed corpus, emitting the "
            "GenerationResult as JSON on stdout."
        ),
    )
    parser.add_argument(
        "--question",
        required=True,
        help="The question to answer against the committed Chunk Corpus.",
    )
    return parser.parse_args(argv)


def main(argv: list = None) -> int:
    """Orchestrate one question through the completed Milestone 1A pipeline.

    Every statement below is exactly one of: argument parsing, runtime component
    construction, runtime component invocation, serialization, stdout emission,
    or process exit. No statement computes anything about the domain — there is
    no branch, no transformation, and no value derived from a runtime artifact's
    contents.

    The artifact chain is passed by reference throughout: `retrieval` is the
    object `retrieve` returned, and `generation` is the object `generate`
    returned and the object `serialize` receives.
    """
    arguments = parse_args(argv)
    chunks = load_corpus()
    canonical_documents = load_canonical_documents()
    retriever = Retriever(chunks, canonical_documents)
    retrieval = retriever.retrieve(arguments.question, DEFAULT_FILTERS)
    generator = Generator()
    generation = generator.generate(arguments.question, retrieval)
    serialized = serialize(generation)
    sys.stdout.write(serialized)
    return 0


if __name__ == "__main__":
    sys.exit(main())
