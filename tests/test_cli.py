"""Specification Family 11 — Deterministic CLI Integration.

Sprint P3.6.0: executable specifications for `scripts/cli.py`, the orchestration
layer that exposes the completed Milestone 1A pipeline
(`docs/MILESTONE_1A.md` build item 6).

What an integration suite has to prove, and what it must not
------------------------------------------------------------
The CLI owns no domain behaviour, so nothing here re-specifies retrieval,
generation or serialization: those are specified by
`tests/test_chunker.py`, `tests/test_generator.py` and the retrieval families,
and repeating them here would be testing the components through a second front
door. What is specified here is exactly what integration can get wrong —

    the sequence            the components are called in the right order
    the artifacts           runtime objects pass through unmodified
    the identity            the object generated is the object serialized
    the bytes               stdout is the serialization and nothing else
    the boundary            no authority is reachable from the runtime path
    the exit codes          0 on success, 2 on a usage error

— and, unusually for this repository, **the shape of the code itself**.
`test_every_statement_is_orchestration` and `test_main_calls_the_approved_sequence`
read `scripts/cli.py`'s AST and hold it to the Orchestration Traceability Rule:
every executable statement is a call, a return, or an argument declaration, and
the call sequence is the approved one. A CLI that grew a branch, a loop, or a
derived value would fail those specifications before any behavioural test
noticed — which is the point, because business logic in a composition layer is a
structural defect, not an output defect.

Two mechanisms, deliberately separated
---------------------------------------
    subprocess   real process, real stdout bytes, real exit codes — the only
                 way to specify what a user actually observes
    in-process   `main(argv)` called directly with the components wrapped, the
                 only way to observe object *identity*, which bytes cannot show

Neither alone is sufficient: a subprocess cannot tell whether the serialized
object was the generated one or a faithful copy, and an in-process call cannot
tell whether `print` added a second newline.
"""

import ast
import json
import subprocess
import sys

from pathlib import Path

import pytest

from sample_rag.generator import OUTCOME_ABSTAIN, Generator, serialize
from sample_rag.retriever import Retriever

from scripts import cli
from scripts.run_retrieval import DEFAULT_FILTERS, load_corpus

# A question the committed corpus answers, and one no chunk shares a term with.
# Neither is asserted to produce particular *content* — the abstention question
# is chosen for lexical disjointness, which is a property of the query, not a
# claim about what the corpus contains.
ANSWERABLE_QUESTION = "What cloud platforms have you worked with?"
UNANSWERABLE_QUESTION = "zzzz qqqq wwww"

# The orchestration categories the sprint permits, expressed as the AST node
# types that can carry them. Anything else is business logic.
ORCHESTRATION_NODES = (ast.Assign, ast.Expr, ast.Return)

# Node types whose presence would mean the CLI decides something.
CONTROL_FLOW_NODES = (
    ast.If,
    ast.For,
    ast.While,
    ast.Try,
    ast.With,
    ast.ListComp,
    ast.DictComp,
    ast.SetComp,
    ast.GeneratorExp,
    ast.IfExp,
    ast.Lambda,
    ast.BoolOp,
    ast.Compare,
)

# Work Package 3's sequence, in order: parse, load, construct, invoke, construct,
# invoke, serialize, emit.
APPROVED_CALL_SEQUENCE = [
    "parse_args",
    "load_corpus",
    "Retriever",
    "retrieve",
    "Generator",
    "generate",
    "serialize",
    "write",
]

# What each function is permitted to call. Enumerated rather than inferred: the
# Orchestration Traceability Rule constrains *what* may be called, not merely
# that a statement is a call, so a computation expressed as `len(...)` is
# refused here rather than passing as "an assignment binding a call".
APPROVED_CALLEES = {
    "main": set(APPROVED_CALL_SEQUENCE),
    "parse_args": {"ArgumentParser", "add_argument", "parse_args"},
}

# Repository authorities that are validation-only. The CLI may reach none of
# them, and each is named so a failure says which boundary was crossed.
BARRED_AUTHORITY_MODULES = (
    "scripts.build_manifest",
    "scripts.build_chunks",
    "scripts.build_evidence_trace",
    "scripts.evaluate_retrieval",
    "scripts.report_retrieval_metrics",
    "scripts.diagnose_retrieval",
    "sample_rag.knowledge_source",
    "evaluation",
)


def cli_source():
    """The CLI module's source, for the structural specifications."""
    return Path(cli.__file__).read_text(encoding="utf-8")


def imported_names(tree):
    """Every module name the CLI imports, fully qualified.

    Read from the AST rather than by scanning text: a source scan would also
    match a module named inside a docstring, and — more dangerously — a scan
    written to skip docstrings can silently skip the import block along with
    them, checking nothing while appearing to pass.
    """
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def run_cli(repository_root, *arguments):
    """Execute the CLI as a real process, capturing raw bytes.

    `python -m scripts.cli`, from the repository root, exactly as a user runs
    it. Bytes rather than text: the byte-identity guarantee is about bytes, and
    decoding first would hide a newline translation.
    """
    return subprocess.run(
        [sys.executable, "-m", "scripts.cli", *arguments],
        cwd=repository_root,
        capture_output=True,
    )


def expected_output(question):
    """The serialization the pipeline produces for `question`, computed independently.

    Built by calling the same components in the same order the CLI does, but
    assembled here rather than by the CLI — so a specification comparing the two
    is comparing the CLI's output against the pipeline's, not against itself.
    """
    retrieval = Retriever(load_corpus()).retrieve(question, DEFAULT_FILTERS)

    return serialize(Generator().generate(question, retrieval))


@pytest.fixture
def recorded(monkeypatch):
    """Run the CLI in-process with each component wrapped, recording what flowed.

    Returns a callable taking a question and yielding the objects that crossed
    each seam. The wrappers subclass the real components and delegate, so the
    pipeline executed is the real one — nothing is stubbed, and no behaviour is
    simulated. Only the identities are observed.
    """
    captured = {}

    real_serialize = cli.serialize

    def capturing_serialize(result):
        captured["serialized"] = result
        return real_serialize(result)

    class RecordingRetriever(Retriever):
        def retrieve(self, query, filters):
            result = super().retrieve(query, filters)
            captured["retrieved"] = result
            captured["filters"] = filters
            return result

    class RecordingGenerator(Generator):
        def generate(self, query, retrieval):
            result = super().generate(query, retrieval)
            captured["generated"] = result
            captured["received_retrieval"] = retrieval
            captured["received_query"] = query
            return result

    monkeypatch.setattr(cli, "serialize", capturing_serialize)
    monkeypatch.setattr(cli, "Retriever", RecordingRetriever)
    monkeypatch.setattr(cli, "Generator", RecordingGenerator)

    def run(question):
        captured["exit_code"] = cli.main(["--question", question])
        return captured

    return run


# ---------------------------------------------------------------------------
# Orchestration Traceability Rule — the shape of the code
# ---------------------------------------------------------------------------


def test_every_statement_is_orchestration():
    """Every executable statement is a call, an assignment of a call, or a return.

    The Orchestration Traceability Rule, executable. Each permitted category —
    argument parsing, component construction, component invocation,
    serialization, stdout emission, process exit — is expressible as a call or a
    return, and nothing else is. A statement that computed, compared, or
    transformed a value would not match, which is what makes "no business logic"
    a checked property rather than a review opinion.

    The module guard (`if __name__ == "__main__":`) is excluded: it is not part
    of any function's body and carries the process-exit category alone.
    """
    tree = ast.parse(cli_source())
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)]

    assert functions, "the CLI must define its orchestration in functions"

    for function in functions:
        for statement in function.body:
            if isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Constant):
                continue  # the docstring

            assert isinstance(statement, ORCHESTRATION_NODES), (
                f"{function.name}: statement {ast.dump(statement)[:60]} is not orchestration"
            )

            if isinstance(statement, ast.Assign):
                assert isinstance(statement.value, ast.Call), (
                    f"{function.name}: assignment does not bind a component call"
                )

        # "Is a call" is not sufficient on its own: `total = len(result.statements)`
        # is an assignment binding a call, and is a computation over an artifact's
        # contents — a category the rule does not permit. Constraining *what* may
        # be called is what makes the rule bite, and it is why the approved
        # callees are enumerated rather than inferred.
        called = {
            node.func.id if isinstance(node.func, ast.Name) else node.func.attr
            for node in ast.walk(function)
            if isinstance(node, ast.Call)
        }

        assert called <= APPROVED_CALLEES[function.name], (
            f"{function.name}: calls {sorted(called - APPROVED_CALLEES[function.name])}, "
            f"which is not component construction or invocation"
        )


def test_the_cli_contains_no_control_flow():
    """No branch, loop, comprehension, comparison or lambda inside any function.

    A composition layer that decides something is a computation layer. This is
    the structural form of *"No additional processing. No business logic. No
    orchestration beyond this sequence."* — and it is stricter than reading the
    code, because it also refuses the conditional expression and the boolean
    short-circuit that would hide a decision inside a single statement.

    Scoped to function bodies, where all orchestration lives. The module carries
    exactly one branch — Python's `if __name__ == "__main__":` entry guard,
    present in every `scripts/*.py` in this repository — which is a process-entry
    convention rather than a decision about the domain. It is not exempted so
    much as **specified separately**: the next specification pins it to the
    standard idiom, so the exclusion here cannot become a place for logic to
    hide.
    """
    tree = ast.parse(cli_source())
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)]

    offenders = sorted(
        f"{function.name}: {type(node).__name__}"
        for function in functions
        for node in ast.walk(function)
        if isinstance(node, CONTROL_FLOW_NODES)
    )

    assert offenders == [], f"the CLI carries control flow: {offenders}"


def test_the_only_module_level_branch_is_the_standard_entry_guard():
    """The module's one branch is `if __name__ == "__main__": sys.exit(main())`.

    Pinned exactly, so the exclusion the previous specification makes is not a
    loophole: the guard tests one name against one constant, and its body is a
    single call. Anything else — a configuration branch, a fallback, an
    environment check — would fail here even though it sits outside a function.
    """
    tree = ast.parse(cli_source())
    branches = [node for node in tree.body if isinstance(node, ast.If)]

    assert len(branches) == 1

    guard = branches[0]
    test = guard.test

    assert isinstance(test, ast.Compare)
    assert isinstance(test.left, ast.Name) and test.left.id == "__name__"
    assert [constant.value for constant in test.comparators] == ["__main__"]
    assert guard.orelse == []
    assert len(guard.body) == 1
    assert ast.dump(guard.body[0]).count("Call") == 2  # sys.exit(main())


def test_main_calls_the_approved_sequence():
    """`main` calls exactly Work Package 3's sequence, in order.

    Parse, load corpus, construct retriever, retrieve, construct generator,
    generate, serialize, emit. Asserted as an ordered list rather than a set:
    the order *is* the pipeline, and a CLI that generated before retrieving, or
    serialized a value it built earlier, would satisfy a membership check.
    """
    tree = ast.parse(cli_source())
    main = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "main")

    called = []
    for node in ast.walk(main):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                called.append(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                called.append(node.func.attr)

    assert called == APPROVED_CALL_SEQUENCE


def test_the_cli_implements_no_serialization_of_its_own():
    """Serialization is `sample_rag/generator.py`'s, per `docs/GENERATION_CONTRACT.md` §13.2.

    The CLI neither imports `json` nor formats output: a second serialization
    path would be a second answer to a question the contract has already frozen,
    and the two could drift.
    """
    tree = ast.parse(cli_source())

    assert "json" not in {name.split(".")[0] for name in imported_names(tree)}

    # No string building either: an f-string, a `%` format, or a `.format` call
    # inside a function body would be the CLI shaping output itself, which is a
    # representation decision §13.2 has already made.
    formatting = [
        type(node).__name__
        for function in tree.body
        if isinstance(function, ast.FunctionDef)
        for node in ast.walk(function)
        if isinstance(node, ast.JoinedStr)
        or (isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mod))
    ]

    assert formatting == [], f"the CLI formats output itself: {formatting}"


def test_the_cli_constructs_no_runtime_artifact():
    """The CLI never constructs a `GenerationResult`, `RetrievalResult`, or evidence.

    Work Package 4's identity requirement, enforced structurally: the artifacts
    are produced by the components that own them and pass through. A CLI that
    rebuilt one — even faithfully — would be defining a runtime artifact, which
    Work Package 2 forbids.
    """
    tree = ast.parse(cli_source())
    constructed = {
        node.func.id for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }

    assert constructed & {
        "GenerationResult",
        "GeneratedStatement",
        "SupportingEvidence",
        "RetrievalResult",
    } == set()


# ---------------------------------------------------------------------------
# Runtime dependency boundary
# ---------------------------------------------------------------------------


def test_the_cli_reaches_no_repository_authority():
    """The permitted chain, and nothing else — enforced by an allowlist.

    `load_corpus` → `Retriever.retrieve` → `Generator.generate` → `serialize` →
    stdout. The Knowledge Manifest, Golden Dataset, QA Dataset, Evidence Trace
    Dataset and every evaluation layer are validation-only, and an allowlist
    fails on any import nobody thought to forbid, which a denylist would not.
    """
    tree = ast.parse(cli_source())

    roots, modules = set(), set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".")[0])
            modules.add(node.module)

    assert roots <= {"argparse", "sys", "sample_rag", "scripts"}
    assert modules <= {
        "argparse",
        "sys",
        "sample_rag.generator",
        "sample_rag.retriever",
        "scripts.run_retrieval",
    }


def test_the_cli_does_not_reach_the_evaluation_layers():
    """No evaluation, metrics, diagnosis, dataset or manifest module is imported.

    Stated separately from the allowlist and by name, so a failure says *which*
    boundary was crossed. `docs/GENERATION_CONTRACT.md` §18 records why it
    matters: those authorities exist for the repository's own 22 benchmark
    questions, and a runtime path that reads one serves those 22 and nothing
    else while appearing to work.
    """
    imported = imported_names(ast.parse(cli_source()))

    for barred in BARRED_AUTHORITY_MODULES:
        reached = [name for name in imported if name == barred or name.startswith(f"{barred}.")]

        assert reached == [], f"the CLI reaches the barred authority {reached}"


def test_the_cli_lives_in_scripts_not_sample_rag():
    """`docs/architecture.md` §6 — the dependency direction is `scripts/` → `sample_rag/`.

    The placement is load-bearing rather than cosmetic: the CLI needs
    `load_corpus`, which lives in `scripts/`, so a CLI inside `sample_rag/`
    would have to import `scripts/` — the direction the architecture bars and
    the reason `SUPPORTED_EXTENSIONS` and the outcome literals are duplicated
    (register AH-9, contract §20.4).
    """
    assert Path(cli.__file__).parent.name == "scripts"


# ---------------------------------------------------------------------------
# Identity preservation (in-process)
# ---------------------------------------------------------------------------


def test_the_generated_object_is_the_serialized_object(recorded, capsys):
    """Work Package 4 — `serialize` receives the exact object `generate` returned.

    Identity, not equality: `is`, not `==`. Frozen dataclasses compare by value,
    so a CLI that reconstructed an identical `GenerationResult` before
    serializing would pass an equality check while having defined a runtime
    artifact of its own. This is the specification that cannot be written
    against a subprocess, because bytes cannot distinguish an object from its
    perfect copy.
    """
    captured = recorded(ANSWERABLE_QUESTION)
    capsys.readouterr()

    assert captured["serialized"] is captured["generated"]


def test_the_retrieved_object_is_the_generated_from_object(recorded, capsys):
    """Work Package 4 — `generate` receives the exact object `retrieve` returned.

    The other seam. A CLI that filtered, re-ordered, or trimmed the retrieved
    chunks before handing them on would be making a retrieval decision the
    Retriever already made — and `docs/GENERATION_CONTRACT.md` §20.2 records
    that chunk selection is the *Generator's* delegated decision, not the
    caller's.
    """
    captured = recorded(ANSWERABLE_QUESTION)
    capsys.readouterr()

    assert captured["received_retrieval"] is captured["retrieved"]


def test_the_question_reaches_both_components_unaltered(recorded, capsys):
    """The parsed question is passed through to the generator verbatim.

    `docs/GENERATION_CONTRACT.md` §6.2 records that the Generator takes the
    query explicitly rather than reading `retrieval.diagnostics["query"]`. A CLI
    that normalized, lowercased, or trimmed the question between the two calls
    would make the artifact's recorded query differ from what the user typed.
    """
    captured = recorded(ANSWERABLE_QUESTION)
    capsys.readouterr()

    assert captured["received_query"] == ANSWERABLE_QUESTION
    assert captured["serialized"].diagnostics["query"] == ANSWERABLE_QUESTION


def test_retrieval_is_invoked_with_the_established_filter_mapping(recorded, capsys):
    """The CLI reuses `scripts/run_retrieval.py`'s `DEFAULT_FILTERS`.

    Not a filter mapping of its own: the retrieval runtime already owns how
    retrieval is parameterized, and a second default would let the CLI and
    `scripts/run_retrieval.py` disagree about what the same question retrieves.
    """
    captured = recorded(ANSWERABLE_QUESTION)
    capsys.readouterr()

    assert captured["filters"] is DEFAULT_FILTERS


def test_main_returns_zero_on_successful_execution(recorded, capsys):
    """Work Package 5 — successful execution reports success."""
    captured = recorded(ANSWERABLE_QUESTION)
    capsys.readouterr()

    assert captured["exit_code"] == 0


# ---------------------------------------------------------------------------
# Byte-identical stdout (subprocess)
# ---------------------------------------------------------------------------


def test_stdout_equals_the_serialized_generation_result(repository_root):
    """Work Package 5 — stdout is `serialize(generation_result)`, byte for byte.

    The expectation is computed independently, by driving the same components in
    the same order outside the CLI, so this compares the CLI's output against
    the pipeline's rather than against itself.
    """
    completed = run_cli(repository_root, "--question", ANSWERABLE_QUESTION)

    assert completed.returncode == 0
    assert completed.stdout == expected_output(ANSWERABLE_QUESTION).encode("utf-8")


def test_stdout_carries_exactly_one_trailing_newline(repository_root):
    """§13.2 terminates the serialization with one newline; the CLI adds none.

    The specific defect this refuses: `print(serialize(result))` would emit two.
    That is why `scripts/cli.py` uses `sys.stdout.write`, and this is the
    specification that keeps it that way.
    """
    completed = run_cli(repository_root, "--question", ANSWERABLE_QUESTION)

    assert completed.stdout.endswith(b"\n")
    assert not completed.stdout.endswith(b"\n\n")


def test_stdout_is_exactly_one_json_document(repository_root):
    """No banner, timestamp, progress indicator, or completion message.

    Parsing the *entire* stdout is what establishes the absence: any preamble or
    trailing line would make the payload invalid JSON rather than merely
    untidy, so this specification cannot be satisfied by output that carries
    anything else.
    """
    completed = run_cli(repository_root, "--question", ANSWERABLE_QUESTION)
    payload = json.loads(completed.stdout.decode("utf-8"))

    assert tuple(payload) == ("answer_text", "outcome", "statements", "diagnostics")


def test_repeated_execution_produces_byte_identical_stdout(repository_root):
    """Work Package 5 — two runs of the same question are byte-identical.

    Separate processes, so this also covers the sources of run-to-run variation
    a single process cannot show: hash randomization, dict iteration order
    established at import, and any environment-dependent formatting.
    """
    first = run_cli(repository_root, "--question", ANSWERABLE_QUESTION)
    second = run_cli(repository_root, "--question", ANSWERABLE_QUESTION)

    assert first.stdout == second.stdout
    assert first.returncode == second.returncode == 0


def test_stderr_is_silent_on_successful_execution(repository_root):
    """Nothing is written to stderr when execution succeeds.

    stderr is reserved for argument and usage errors, so a warning or debug line
    on the success path would make the stream meaningless as a signal.
    """
    completed = run_cli(repository_root, "--question", ANSWERABLE_QUESTION)

    assert completed.stderr == b""


# ---------------------------------------------------------------------------
# Abstention through the CLI
# ---------------------------------------------------------------------------


def test_a_question_with_no_retrievable_evidence_abstains(repository_root):
    """The Abstain path, end to end through the CLI.

    A query sharing no term with any chunk retrieves nothing, so the Generator
    abstains (`docs/GENERATION_CONTRACT.md` §9.3) and the CLI emits that result
    unchanged. Abstention is a successful execution, not an error: nothing went
    wrong, and the pipeline reported honestly that it had nothing to quote —
    which is exactly why the exit code is 0 and stderr stays empty.
    """
    completed = run_cli(repository_root, "--question", UNANSWERABLE_QUESTION)
    payload = json.loads(completed.stdout.decode("utf-8"))

    assert completed.returncode == 0
    assert completed.stderr == b""
    assert payload["outcome"] == OUTCOME_ABSTAIN
    assert payload["statements"] == []


def test_the_abstain_path_is_also_byte_identical_on_repetition(repository_root):
    """Determinism is not conditional on having produced an answer."""
    first = run_cli(repository_root, "--question", UNANSWERABLE_QUESTION)
    second = run_cli(repository_root, "--question", UNANSWERABLE_QUESTION)

    assert first.stdout == second.stdout


# ---------------------------------------------------------------------------
# Argument validation and exit codes
# ---------------------------------------------------------------------------


def test_a_missing_question_exits_two_and_reports_only_to_stderr(repository_root):
    """Work Package 5 — invalid arguments: exit 2, message on stderr, stdout empty.

    argparse's own convention, not re-implemented by this module. stdout staying
    **empty** is the load-bearing half: it is what keeps the byte-identity
    guarantee meaningful, since a consumer piping stdout never receives an error
    message in the stream it parses as JSON.
    """
    completed = run_cli(repository_root)

    assert completed.returncode == 2
    assert completed.stdout == b""
    assert b"--question" in completed.stderr


def test_an_unrecognized_argument_exits_two(repository_root):
    """Work Package 5 — an unknown option is a usage error, not a silent no-op."""
    completed = run_cli(repository_root, "--question", ANSWERABLE_QUESTION, "--top-k", "3")

    assert completed.returncode == 2
    assert completed.stdout == b""
    assert completed.stderr != b""


def test_an_empty_question_is_accepted_and_abstains(repository_root):
    """An empty `--question` is a valid argument, and produces an Abstain result.

    Recorded rather than assumed: `--question ""` is well-formed — argparse has
    no emptiness rule and the CLI adds none, because a non-emptiness check would
    be validation logic this layer is not permitted to hold. The empty query
    tokenizes to nothing, retrieves nothing, and abstains, so the pipeline
    handles it through its own contracted path rather than through a CLI guard.
    """
    completed = run_cli(repository_root, "--question", "")
    payload = json.loads(completed.stdout.decode("utf-8"))

    assert completed.returncode == 0
    assert payload["outcome"] == OUTCOME_ABSTAIN


def test_help_is_available_and_exits_zero(repository_root):
    """`--help` prints usage and exits 0 — argparse's convention, inherited.

    A usage query rather than an execution, so Work Package 5's byte-identity
    guarantee (which covers successful *execution*) does not apply to it. Named
    here so the CLI's full observable surface is specified rather than partly
    undocumented.
    """
    completed = run_cli(repository_root, "--help")

    assert completed.returncode == 0
    assert b"--question" in completed.stdout


# ---------------------------------------------------------------------------
# Public surface
# ---------------------------------------------------------------------------


def test_the_module_exposes_only_the_orchestration_surface():
    """Work Package 7 — no public API beyond the approved CLI surface.

    `parse_args` and `main`, and nothing else: no class, no helper, no
    convenience entry point. Read from the module's own top-level definitions,
    so imported names are not counted as surface this module offers.
    """
    tree = ast.parse(cli_source())

    defined = {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.ClassDef))
    } | {
        target.id
        for node in tree.body
        if isinstance(node, ast.Assign)
        for target in node.targets
        if isinstance(target, ast.Name)
    }

    assert {name for name in defined if not name.startswith("_")} == {"parse_args", "main"}


def test_the_cli_defines_no_class():
    """A composition layer needs no type of its own.

    Any class here would be a runtime artifact, a wrapper around one, or state
    the pipeline does not have — all three of which Work Package 4 forbids.
    """
    tree = ast.parse(cli_source())

    assert [node.name for node in tree.body if isinstance(node, ast.ClassDef)] == []
