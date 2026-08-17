"""Executable specification — the M2-08 evaluator's selection guard.

Specifies the selection/authorization boundary in `scripts/evaluate_generation.py`:
the layer that stands between a bare invocation and a run that spends provider
budget. It specifies **nothing about what the metrics mean** — that is
`tests/test_generation_metrics.py`, which this sprint does not touch.

Why a real process, and not only a mock
-----------------------------------------
The hazard this guard exists to remove is an **import-time** one. Python executes
module-level imports before any function runs, so re-ordering `main` cannot by
itself make `--help` cheap: if the module imports an expensive chain at module
scope, the cost is already paid by the time argparse could refuse the
invocation.

Measured on this repository, two of the evaluator's original top-level imports
were expensive and the rest were free:

    sample_rag.vector_runtime        3.14 s   torch, transformers,
                                              sentence_transformers, faiss
    scripts.run_hybrid_retrieval     3.11 s   (the same chain, transitively)
    every other import            <= 0.02 s   no machine-learning library

So a specification that patched `BGEEmbeddingProvider` inside an
already-imported process would assert nothing about the actual defect. The
specifications below therefore run the evaluator **in a fresh interpreter** and
inspect `sys.modules` afterwards, which is the only place the question *"was the
heavy chain imported at all?"* can be answered.

`HEAVY_MODULES` is the observable. `test_the_heavy_module_probe_is_not_vacuous`
proves the probe can actually see them, so a green run of the safety
specifications means the chain was absent rather than that the check was blind.

**No specification here performs a provider call, needs a credential, reaches
the network, downloads a model or touches FAISS state.** The refusal paths are
executed for real because they are free; the two accepting paths
(`--case-id`, `--all`) are specified at the selection seam, with generation
substituted, because executing them for real is precisely the provider spend
this guard exists to make deliberate.
"""

import ast
import pathlib
import subprocess
import sys

import pytest

from scripts.evaluate_generation import (
    SelectionError,
    build_parser,
    load_reference_entries,
    main,
    select_entries,
)

# The libraries whose presence in `sys.modules` means the expensive chain was
# imported. Loading them costs ~3.1 s and hundreds of megabytes; loading the
# model *weights* costs more still and happens later, when `VectorIndexRuntime`
# is constructed. This is the earlier and stricter line: the safe paths must not
# even import the libraries.
HEAVY_MODULES = ("torch", "faiss", "sentence_transformers", "transformers")

# The two imports that must not appear at module scope in the evaluator.
LAZY_IMPORTS = ("sample_rag.vector_runtime", "scripts.run_hybrid_retrieval")

EVALUATOR = ("scripts", "evaluate_generation.py")

# Runs the evaluator's real `__main__` path in this process's argv, then reports
# the exit code and which heavy modules the run pulled in. `runpy` rather than a
# plain import because `if __name__ == "__main__"` is part of what is specified.
PROBE = """
import runpy, sys
sys.argv = ["python3 -m scripts.evaluate_generation"] + sys.argv[1:]
code = 0
try:
    runpy.run_module("scripts.evaluate_generation", run_name="__main__")
except SystemExit as finished:
    code = finished.code
loaded = [m for m in {heavy!r} if m in sys.modules]
sys.stderr.write("PROBE exit=%s heavy=%s\\n" % (code, ",".join(loaded)))
"""


# The environment every subprocess below runs under. **`DEEPSEEK_API_KEY` is
# deliberately absent**, and that is a second line of defence rather than a
# convenience: these specifications only ever invoke paths that must be refused,
# so a run that somehow reached the provider would be a defect — and without a
# credential it fails as `ProviderConfigurationError` instead of spending
# budget. A regression in the guard therefore cannot turn `pytest` into a
# billable run, which is the failure mode this whole sprint exists to remove.
SAFE_ENVIRONMENT = {"PATH": "/usr/bin:/bin"}


def run_evaluator(repository_root, *arguments):
    """Execute the evaluator as a real process, from the repository root.

    `python3 -m scripts.evaluate_generation`, which is this repository's
    invocation convention throughout — `scripts/` modules import one another, so
    the package form is the one under which the evaluator's own imports resolve.
    The same shape `tests/test_cli.py::run_cli` already uses, with the
    credential-free environment above.
    """
    return subprocess.run(
        [sys.executable, "-m", "scripts.evaluate_generation", *arguments],
        cwd=repository_root,
        capture_output=True,
        text=True,
        env={**SAFE_ENVIRONMENT, "PYTHONPATH": str(repository_root)},
    )


def probe_evaluator(repository_root, *arguments):
    """Run the evaluator in a fresh interpreter and report what it imported.

    Returns `(exit_code, heavy_modules_loaded)`. The probe runs the real
    `__main__` path, so what it observes is what a user's invocation would do.
    """
    completed = subprocess.run(
        [sys.executable, "-c", PROBE.format(heavy=HEAVY_MODULES), *arguments],
        cwd=repository_root,
        capture_output=True,
        text=True,
        env={**SAFE_ENVIRONMENT, "PYTHONPATH": str(repository_root)},
    )
    line = [l for l in completed.stderr.splitlines() if l.startswith("PROBE ")]
    assert line, f"the probe produced no report; stderr was:\n{completed.stderr}"
    exit_field, heavy_field = line[-1].split()[1:]
    loaded = heavy_field.split("=", 1)[1]
    return exit_field.split("=", 1)[1], [m for m in loaded.split(",") if m]


def golden_entries():
    """The committed golden entries, read through the repository's own gate."""
    return load_reference_entries()


def parse(*arguments):
    """Parse an argument list the way `main` does."""
    return build_parser().parse_args(list(arguments))


def imported_modules(source):
    """Fully-qualified module names imported at **module scope** only.

    Deliberately not `ast.walk`: an import nested inside a function is exactly
    what this sprint moved the heavy chain into, and counting it would make the
    laziness specification assert its own opposite.
    """
    names = set()
    for node in ast.parse(source).body:
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


# ---------------------------------------------------------------------------
# 1. The probe itself — specified before anything relies on it
# ---------------------------------------------------------------------------


def test_the_heavy_module_probe_is_not_vacuous(repository_root):
    """A safety specification whose observable can never fire proves nothing.

    Importing `scripts.run_hybrid_retrieval` is the chain the evaluator used to
    perform at module scope. If the probe cannot see *that*, then its silence on
    the `--help` path is meaningless.
    """
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys, scripts.run_hybrid_retrieval;"
            f"print([m for m in {HEAVY_MODULES!r} if m in sys.modules])",
        ],
        cwd=repository_root,
        capture_output=True,
        text=True,
        env={**SAFE_ENVIRONMENT, "PYTHONPATH": str(repository_root)},
    )

    assert completed.returncode == 0, completed.stderr
    for module in HEAVY_MODULES:
        assert module in completed.stdout, (
            f"the probe cannot observe {module!r}; the safety specifications "
            f"below would pass blindly"
        )


# ---------------------------------------------------------------------------
# 2. Fresh-process safety — the four invocations that must cost nothing
# ---------------------------------------------------------------------------


def test_help_exits_successfully_and_prints_usage(repository_root):
    completed = run_evaluator(repository_root, "--help")

    assert completed.returncode == 0
    assert "--case-id" in completed.stdout
    assert "--all" in completed.stdout
    assert "python3 -m scripts.evaluate_generation" in completed.stdout


def test_help_imports_no_machine_learning_library(repository_root):
    """**The specification this sprint exists for.**

    `--help` must be answerable without `torch`, `faiss`,
    `sentence_transformers` or `transformers` entering the process — which is a
    statement about imports, not about call order, and is why it is observed in
    a fresh interpreter rather than asserted about a mock.
    """
    code, heavy = probe_evaluator(repository_root, "--help")

    assert code == "0"
    assert heavy == []


def test_no_arguments_refuses_and_says_what_to_pass(repository_root):
    """**There is no implicit full-dataset run.** A bare invocation is an error,
    not a default, because every real run spends provider budget."""
    completed = run_evaluator(repository_root)

    assert completed.returncode != 0
    assert "--case-id" in completed.stderr
    assert "--all" in completed.stderr


def test_no_arguments_imports_no_machine_learning_library(repository_root):
    code, heavy = probe_evaluator(repository_root)

    assert code == "2"
    assert heavy == []


def test_an_unknown_argument_refuses(repository_root):
    completed = run_evaluator(repository_root, "--unknown-argument")

    assert completed.returncode != 0
    assert "unrecognized arguments" in completed.stderr


def test_an_unknown_argument_imports_no_machine_learning_library(repository_root):
    code, heavy = probe_evaluator(repository_root, "--unknown-argument")

    assert code == "2"
    assert heavy == []


def test_an_unknown_case_id_refuses_and_names_it(repository_root):
    completed = run_evaluator(repository_root, "--case-id", "DOES_NOT_EXIST")

    assert completed.returncode != 0
    assert "DOES_NOT_EXIST" in completed.stderr
    assert "resume_evidence_trace.json" in completed.stderr


def test_an_unknown_case_id_imports_no_machine_learning_library(repository_root):
    """Validating an id costs a JSON read. It must not cost a model.

    This is the path most likely to regress: resolving an id is *about* the
    dataset, and it would be easy to resolve it somewhere that has already built
    a retriever.
    """
    code, heavy = probe_evaluator(repository_root, "--case-id", "DOES_NOT_EXIST")

    assert code == "2"
    assert heavy == []


def test_case_id_and_all_are_mutually_exclusive(repository_root):
    entry = golden_entries()[0]
    completed = run_evaluator(repository_root, "--case-id", entry["id"], "--all")

    assert completed.returncode != 0
    assert "not allowed with" in completed.stderr


def test_no_safe_invocation_prints_weight_loading_progress(repository_root):
    """The other visible face of the same property.

    `sentence_transformers` reports `Loading weights` and the Hugging Face hub
    warns about anonymous requests. Neither may appear on a path that was
    refused.
    """
    for arguments in ([], ["--help"], ["--unknown-argument"], ["--case-id", "NOPE"]):
        completed = run_evaluator(repository_root, *arguments)
        combined = completed.stdout + completed.stderr

        for symptom in ("Loading weights", "HF_TOKEN", "sentence_transformers", "faiss"):
            assert symptom not in combined, f"{arguments} produced {symptom!r}"


# ---------------------------------------------------------------------------
# 3. Selection — resolved against the committed dataset, before generation
# ---------------------------------------------------------------------------


def test_a_valid_case_id_selects_exactly_that_entry():
    entries = golden_entries()
    wanted = entries[3]

    selected = select_entries(entries, parse("--case-id", wanted["id"]))

    assert selected == [wanted]
    assert len(selected) == 1


def test_all_selects_every_committed_entry_in_dataset_order():
    entries = golden_entries()

    selected = select_entries(entries, parse("--all"))

    assert selected == entries
    assert [row["id"] for row in selected] == [row["id"] for row in entries]


def test_selection_resolves_against_the_supplied_dataset_not_a_constant():
    """No count and no id is written into the selection logic.

    Given a dataset the repository does not contain, `--all` selects that one —
    so adding or removing a golden entry changes what `--all` means without
    changing the evaluator.
    """
    synthetic = [{"id": "only-one"}, {"id": "and-another"}]

    assert select_entries(synthetic, parse("--all")) == synthetic
    assert select_entries(synthetic, parse("--case-id", "only-one")) == [synthetic[0]]


def test_no_selection_is_refused():
    with pytest.raises(SelectionError) as refusal:
        select_entries(golden_entries(), parse())

    assert "--case-id" in str(refusal.value)
    assert "--all" in str(refusal.value)


def test_an_unknown_case_id_is_refused_by_the_selection_layer():
    with pytest.raises(SelectionError) as refusal:
        select_entries(golden_entries(), parse("--case-id", "NOT_A_CASE"))

    assert "NOT_A_CASE" in str(refusal.value)


def test_the_selection_layer_touches_no_provider_and_no_runtime():
    """Expressed as a signature, following `evaluation/generation_metrics.py`.

    `select_entries` receives the entries and the parsed arguments and nothing
    else, so there is no parameter through which a client, a retriever, an index
    or a generator could reach it — and none through which it could reach one.
    """
    import inspect

    assert list(inspect.signature(select_entries).parameters) == ["entries", "arguments"]


# ---------------------------------------------------------------------------
# 4. Selection happens BEFORE generation — the budget property
# ---------------------------------------------------------------------------


class RecordingGeneration:
    """Stands in for `generate_cases`, recording the entries it was handed.

    The substitution is what keeps this specification free: the real function
    performs one provider generation call per entry it receives, which is
    exactly the spend the guard exists to make deliberate.
    """

    def __init__(self):
        self.received = None

    def __call__(self, entries, client):
        self.received = list(entries)
        return [], [], 0


class SilentClient:
    """Stands in for `DeepSeekClient`. Holds no endpoint, credential or socket.

    It carries `model` because `main` reads it when composing the report, and
    `complete` raises rather than returning: nothing in this file may reach a
    provider, so the substitute makes the attempt loud instead of silent.
    """

    model = "test-double"

    def complete(self, messages):
        raise AssertionError("a specification attempted a provider call")


@pytest.fixture
def evaluator_without_generation(monkeypatch):
    """`main` with generation, judging and reporting substituted.

    Everything up to and including selection runs for real — the parser, the
    golden read and `select_entries` — so what is specified is the real
    selection path. Only what would spend budget is replaced.
    """
    import scripts.evaluate_generation as evaluator

    recorder = RecordingGeneration()
    monkeypatch.setattr(evaluator, "generate_cases", recorder)
    monkeypatch.setattr(evaluator, "DeepSeekClient", SilentClient)
    monkeypatch.setattr(evaluator, "compute", lambda cases, judge: {})
    monkeypatch.setattr(evaluator, "report_scores", lambda *a, **k: None)
    return recorder


def test_a_single_case_run_generates_exactly_one_case(evaluator_without_generation):
    """**The budget property.**

    A `--case-id` run must hand generation one entry. An implementation that
    generated the dataset and filtered afterwards would satisfy every assertion
    about the *reported* result while spending the entire provider budget, so
    what is asserted here is the input to generation, not the output.
    """
    entries = golden_entries()
    wanted = entries[5]

    assert main(["--case-id", wanted["id"]]) == 0

    assert evaluator_without_generation.received == [wanted]
    assert len(evaluator_without_generation.received) == 1
    assert len(entries) > 1, "the dataset must have more than one entry to specify this"


def test_an_all_run_generates_every_committed_case(evaluator_without_generation):
    assert main(["--all"]) == 0

    assert evaluator_without_generation.received == golden_entries()


def test_a_refused_selection_never_reaches_generation(evaluator_without_generation):
    """Every refusal path leaves generation untouched, in-process as well as
    in a fresh one — argparse exits `2` and the recorder is never called."""
    for arguments in ([], ["--case-id", "NOT_A_CASE"]):
        with pytest.raises(SystemExit) as exit_:
            main(arguments)

        assert exit_.value.code == 2
        assert evaluator_without_generation.received is None


# ---------------------------------------------------------------------------
# 5. Structural — the laziness that makes the safety specifications hold
# ---------------------------------------------------------------------------


def test_the_evaluator_imports_no_expensive_chain_at_module_scope(repository_root):
    """The regression guard for the import-time fix.

    A later edit that hoists either import back to module scope would restore
    the original defect — `--help` paying 3.1 s and four machine-learning
    libraries before argparse could refuse the invocation. This fails on that
    edit directly, rather than waiting for the subprocess specifications to
    notice it.
    """
    source = pathlib.Path(repository_root, *EVALUATOR).read_text(encoding="utf-8")
    module_scope = imported_modules(source)

    for lazy in LAZY_IMPORTS:
        assert lazy not in module_scope, (
            f"{lazy!r} is imported at module scope again; --help would pay for it"
        )


def test_the_expensive_imports_are_present_inside_the_authorized_path(repository_root):
    """The other half: deferred, not deleted.

    `generate_cases` still reaches the same runtime through the same modules —
    the pipeline is unchanged, only the moment of import moved.
    """
    source = pathlib.Path(repository_root, *EVALUATOR).read_text(encoding="utf-8")
    tree = ast.parse(source)

    inside = {
        node.module
        for function in tree.body
        if isinstance(function, ast.FunctionDef)
        for node in ast.walk(function)
        if isinstance(node, ast.ImportFrom) and node.module
    }

    for lazy in LAZY_IMPORTS:
        assert lazy in inside, f"{lazy!r} is not imported anywhere it can run"


def test_the_parser_offers_exactly_the_two_authorized_selections(repository_root):
    """The interface is deliberately narrow.

    A selection that is neither *one named case* nor *the whole committed
    dataset* would report a figure over cases someone chose. `--limit`,
    `--subset`, `--sample`, `--index` and `--ids` are absent, and stay absent.
    """
    options = {
        action.option_strings[0]
        for action in build_parser()._actions
        if action.option_strings
    }

    assert options == {"-h", "--case-id", "--all"}
