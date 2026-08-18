"""Executable specification — the M2-07 evaluator's selection guard.

Specifies the selection/authorization boundary in `scripts/evaluate_context.py`:
the layer that stands between a bare invocation and a run that loads the
embedding model, builds the vector index and spends judge budget. It specifies
**nothing about what Context Precision or Context Recall mean** — that is
`tests/test_context_metrics.py`, which this sprint does not touch, and neither
is `evaluation/context_metrics.py`.

Why a real process, and not only a mock
-----------------------------------------
The hazard this guard exists to remove is an **import-time** one. Python executes
module-level imports before any function runs, so re-ordering `main` cannot by
itself make `--help` cheap: if the module imports an expensive chain at module
scope, the cost is already paid by the time argparse could refuse the
invocation.

Measured on this repository, one of the evaluator's original top-level imports
pulled the whole machine-learning chain and a second pulled it transitively;
every other import was free:

    sample_rag.vector_runtime        seconds    torch, transformers,
                                                sentence_transformers, faiss
    scripts.run_hybrid_retrieval     seconds    (the same chain, transitively)
    every other import               <= 0.2 s   no machine-learning library

So a specification that patched an embedding provider inside an already-imported
process would assert nothing about the actual defect. The specifications below
therefore run the evaluator **in a fresh interpreter** and inspect `sys.modules`
afterwards, which is the only place the question *"was the heavy chain imported
at all?"* can be answered.

`HEAVY_MODULES` is the observable. `test_the_heavy_module_probe_is_not_vacuous`
proves the probe can actually see them, so a green run of the safety
specifications means the chain was absent rather than that the check was blind.

**No specification here performs a provider call, needs a credential, reaches
the network, downloads a model or touches FAISS state.** The refusal paths are
executed for real because they are free; the two accepting paths (`--case-id`,
`--all`) are specified at the selection seam, with retrieval and judging
substituted, because executing them for real is precisely the model load and
provider spend this guard exists to make deliberate.
"""

import ast
import inspect
import pathlib
import subprocess
import sys

import pytest

from scripts.evaluate_context import (
    SelectionError,
    build_parser,
    load_reference_entries,
    main,
    retrieve_cases,
    select_entries,
)

# The libraries whose presence in `sys.modules` means the expensive chain was
# imported. Loading them costs seconds and hundreds of megabytes; loading the
# model *weights* costs more still and happens later, when `VectorIndexRuntime`
# is constructed. This is the earlier and stricter line: the safe paths must not
# even import the libraries.
HEAVY_MODULES = ("torch", "faiss", "sentence_transformers", "transformers")

# The two imports that must not appear at module scope in the evaluator.
LAZY_IMPORTS = ("sample_rag.vector_runtime", "scripts.run_hybrid_retrieval")

# The retrieval stages `retrieve_cases` reaches through the module that owns
# them. Deferring the import must not have changed *which* stages the evaluator
# calls — M2-07 measures the repository's retrieval, and this is the list it
# measured before the selection guard existed.
HYBRID_NAMES = (
    "canonical_order",
    "fuse_routes",
    "lexical_route",
    "load_documents",
    "semantic_route",
)

EVALUATOR = ("scripts", "evaluate_context.py")

# Runs the evaluator's real `__main__` path in this process's argv, then reports
# the exit code and which heavy modules the run pulled in. `runpy` rather than a
# plain import because `if __name__ == "__main__"` is part of what is specified.
PROBE = """
import runpy, sys
sys.argv = ["python3 -m scripts.evaluate_context"] + sys.argv[1:]
code = 0
try:
    runpy.run_module("scripts.evaluate_context", run_name="__main__")
except SystemExit as finished:
    code = finished.code
loaded = [m for m in {heavy!r} if m in sys.modules]
sys.stderr.write("PROBE exit=%s heavy=%s\\n" % (code, ",".join(loaded)))
"""

# The same fresh-process run, with the one network primitive the repository owns
# replaced by a tripwire. `sample_rag/deepseek.py` is the only module holding a
# network primitive (`tests/test_context_metrics.py` specifies that), and
# `urllib.request.urlopen` is the single call through which it reaches the
# provider — so a refused invocation that somehow reached DeepSeek would trip
# this and be reported, rather than being inferred not to have happened.
PROVIDER_PROBE = """
import runpy, sys, urllib.request

reached = []
urllib.request.urlopen = lambda *a, **k: reached.append(a) or (_ for _ in ()).throw(
    AssertionError("a refused invocation reached the provider")
)

sys.argv = ["python3 -m scripts.evaluate_context"] + sys.argv[1:]
code = 0
try:
    runpy.run_module("scripts.evaluate_context", run_name="__main__")
except SystemExit as finished:
    code = finished.code
sys.stderr.write("PROVIDER exit=%s reached=%s\\n" % (code, len(reached)))
"""


# The environment every subprocess below runs under. **`DEEPSEEK_API_KEY` is
# deliberately absent**, and that is a second line of defence rather than a
# convenience: these specifications only ever invoke paths that must be refused,
# so a run that somehow reached the provider would be a defect — and without a
# credential it fails as `ProviderConfigurationError` instead of spending
# budget. A regression in the guard therefore cannot turn `pytest` into a
# billable run, which is the failure mode this whole sprint exists to remove.
SAFE_ENVIRONMENT = {"PATH": "/usr/bin:/bin"}

# The operator's shell, modelled. A credential-free environment proves the
# refusal paths are safe *for pytest*; it does not by itself prove they are safe
# for the operator, whose shell normally exports the key. This value is not a
# credential and is never sent anywhere — the specifications that use it assert
# the run exits before any provider call, with `PROVIDER_PROBE` watching.
CREDENTIALLED_ENVIRONMENT = {
    **SAFE_ENVIRONMENT,
    "DEEPSEEK_API_KEY": "not-a-credential-this-run-must-never-reach-a-provider",
}

# Every invocation that must be refused, in the two shapes the guard has to
# handle: argparse's own refusals, and the dataset-resolved one.
REFUSED_INVOCATIONS = (
    [],
    ["--unknown-argument"],
    ["--case-id", "DOES_NOT_EXIST"],
)


def run_evaluator(repository_root, *arguments, environment=None):
    """Execute the evaluator as a real process, from the repository root.

    `python3 -m scripts.evaluate_context`, which is this repository's invocation
    convention throughout — `scripts/` modules import one another, so the package
    form is the one under which the evaluator's own imports resolve. The same
    shape `tests/test_cli.py::run_cli` already uses, with the credential-free
    environment above.
    """
    return subprocess.run(
        [sys.executable, "-m", "scripts.evaluate_context", *arguments],
        cwd=repository_root,
        capture_output=True,
        text=True,
        env={
            **(environment or SAFE_ENVIRONMENT),
            "PYTHONPATH": str(repository_root),
        },
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


def probe_provider(repository_root, *arguments, environment):
    """Run the evaluator with the network primitive replaced by a tripwire.

    Returns `(exit_code, urlopen_call_count)`.
    """
    completed = subprocess.run(
        [sys.executable, "-c", PROVIDER_PROBE, *arguments],
        cwd=repository_root,
        capture_output=True,
        text=True,
        env={**environment, "PYTHONPATH": str(repository_root)},
    )
    line = [l for l in completed.stderr.splitlines() if l.startswith("PROVIDER ")]
    assert line, f"the probe produced no report; stderr was:\n{completed.stderr}"
    exit_field, reached_field = line[-1].split()[1:]
    return exit_field.split("=", 1)[1], int(reached_field.split("=", 1)[1])


def golden_entries():
    """The committed golden entries, read through the repository's own gate."""
    return load_reference_entries()


def parse(*arguments):
    """Parse an argument list the way `main` does."""
    return build_parser().parse_args(list(arguments))


def evaluator_source(repository_root):
    return pathlib.Path(repository_root, *EVALUATOR).read_text(encoding="utf-8")


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


def function_named(tree, name):
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError(f"{name!r} is not a module-scope function of the evaluator")


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
# 2. Fresh-process safety — the invocations that must cost nothing
# ---------------------------------------------------------------------------


def test_help_exits_successfully_and_prints_usage(repository_root):
    completed = run_evaluator(repository_root, "--help")

    assert completed.returncode == 0
    assert "--case-id" in completed.stdout
    assert "--all" in completed.stdout
    assert "python3 -m scripts.evaluate_context" in completed.stdout


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
    not a default, because every real run loads a model and spends judge
    budget."""
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
    a retriever and an index.
    """
    code, heavy = probe_evaluator(repository_root, "--case-id", "DOES_NOT_EXIST")

    assert code == "2"
    assert heavy == []


def test_case_id_and_all_are_mutually_exclusive(repository_root):
    entry = golden_entries()[0]
    completed = run_evaluator(repository_root, "--case-id", entry["id"], "--all")

    assert completed.returncode != 0
    assert "not allowed with" in completed.stderr


def test_case_id_and_all_together_import_no_machine_learning_library(repository_root):
    entry = golden_entries()[0]
    code, heavy = probe_evaluator(
        repository_root, "--case-id", entry["id"], "--all"
    )

    assert code == "2"
    assert heavy == []


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
# 3. Credential-free, and credential-present — the provider never being reached
# ---------------------------------------------------------------------------


def test_refused_invocations_reach_no_provider_without_a_credential(repository_root):
    """The refusals are free, and the tripwire proves it rather than implying it.

    `urllib.request.urlopen` is replaced before the evaluator runs;
    `sample_rag/deepseek.py` is the only module in the repository holding a
    network primitive, so a refused invocation that reached DeepSeek would be
    counted here.
    """
    for arguments in REFUSED_INVOCATIONS:
        code, reached = probe_provider(
            repository_root, *arguments, environment=SAFE_ENVIRONMENT
        )

        assert code == "2", arguments
        assert reached == 0, f"{arguments} reached the provider"


def test_refused_invocations_reach_no_provider_with_a_credential_present(repository_root):
    """**The operator's shell, modelled.**

    A credential-free `pytest` proves the refusals are safe under `pytest`. The
    operator runs this evaluator from a shell that exports `DEEPSEEK_API_KEY`,
    and the guarantee that matters to them is that the refusal itself never
    reaches the provider — not that the key happened to be missing. So the same
    refusals run again with a key in the environment, and the tripwire still
    counts zero.
    """
    for arguments in REFUSED_INVOCATIONS:
        code, reached = probe_provider(
            repository_root, *arguments, environment=CREDENTIALLED_ENVIRONMENT
        )

        assert code == "2", arguments
        assert reached == 0, f"{arguments} reached the provider with a key present"


def test_help_reaches_no_provider_with_a_credential_present(repository_root):
    code, reached = probe_provider(
        repository_root, "--help", environment=CREDENTIALLED_ENVIRONMENT
    )

    assert code == "0"
    assert reached == 0


def test_a_credential_is_never_echoed_by_a_refused_invocation(repository_root):
    """`docs/M2.07_Native_Context_Metrics_Report.md`: the credential is never
    read, printed, logged or reported — not even as a boolean."""
    for arguments in ([], ["--help"], ["--case-id", "DOES_NOT_EXIST"]):
        completed = run_evaluator(
            repository_root, *arguments, environment=CREDENTIALLED_ENVIRONMENT
        )
        combined = completed.stdout + completed.stderr

        assert CREDENTIALLED_ENVIRONMENT["DEEPSEEK_API_KEY"] not in combined
        assert "DEEPSEEK_API_KEY" not in combined


# ---------------------------------------------------------------------------
# 4. Selection — resolved against the committed dataset, before retrieval
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


def test_a_selected_entry_is_the_committed_entry_itself():
    """Selection selects. It does not rewrite, project or copy.

    What reaches retrieval must be the committed golden entry, so the run
    measures the dataset rather than something the evaluator made from it.
    """
    entries = golden_entries()
    wanted = entries[7]

    selected = select_entries(entries, parse("--case-id", wanted["id"]))

    assert selected[0] is wanted


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
    """Expressed as a signature, following `evaluation/context_metrics.py`.

    `select_entries` receives the entries and the parsed arguments and nothing
    else, so there is no parameter through which a client, a retriever, an index
    or a runtime could reach it — and none through which it could reach one.
    """
    assert list(inspect.signature(select_entries).parameters) == ["entries", "arguments"]


# ---------------------------------------------------------------------------
# 5. Selection happens BEFORE retrieval — the budget property
# ---------------------------------------------------------------------------


class RecordingRetrieval:
    """Stands in for `retrieve_cases`, recording the entries it was handed.

    The substitution is what keeps this specification free: the real function
    loads the embedding model, builds the vector index and runs both retrieval
    legs once per entry it receives, which is exactly the cost the guard exists
    to make deliberate.
    """

    def __init__(self):
        self.received = None

    def __call__(self, entries):
        self.received = list(entries)
        return [], 0


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
def evaluator_without_retrieval(monkeypatch):
    """`main` with retrieval, judging, partitioning and reporting substituted.

    Everything up to and including selection runs for real — the parser, the
    golden read and `select_entries` — so what is specified is the real
    selection path. Only what would load a model or spend budget is replaced.
    """
    import scripts.evaluate_context as evaluator

    recorder = RecordingRetrieval()
    monkeypatch.setattr(evaluator, "retrieve_cases", recorder)
    monkeypatch.setattr(evaluator, "DeepSeekClient", SilentClient)
    monkeypatch.setattr(evaluator, "compute", lambda cases, judge: {})
    monkeypatch.setattr(evaluator, "partition", lambda report, entries: {})
    monkeypatch.setattr(evaluator, "report_scores", lambda *a, **k: None)
    return recorder


def test_a_single_case_run_retrieves_exactly_one_case(evaluator_without_retrieval):
    """**The budget property.**

    A `--case-id` run must hand retrieval one entry. An implementation that
    retrieved the dataset and filtered afterwards would satisfy every assertion
    about the *reported* result while running every route and judging every
    passage, so what is asserted here is the input to retrieval, not the output.
    """
    entries = golden_entries()
    wanted = entries[5]

    assert main(["--case-id", wanted["id"]]) == 0

    assert evaluator_without_retrieval.received == [wanted]
    assert len(evaluator_without_retrieval.received) == 1
    assert len(entries) > 1, "the dataset must have more than one entry to specify this"


def test_a_single_case_run_reaches_retrieval_with_no_other_entry(evaluator_without_retrieval):
    """The same property stated as an exclusion, over the whole dataset.

    Not one unrelated committed entry may reach retrieval — that is what makes a
    single-case run a single case rather than a filtered full run.
    """
    entries = golden_entries()
    wanted = entries[5]

    assert main(["--case-id", wanted["id"]]) == 0

    reached = [row["id"] for row in evaluator_without_retrieval.received]
    assert reached == [wanted["id"]]
    for other in entries:
        if other["id"] != wanted["id"]:
            assert other["id"] not in reached


def test_every_committed_case_id_selects_only_itself(evaluator_without_retrieval):
    """Swept across the committed dataset, not demonstrated on one entry."""
    entries = golden_entries()

    for entry in entries:
        assert main(["--case-id", entry["id"]]) == 0
        assert evaluator_without_retrieval.received == [entry]


def test_an_all_run_retrieves_every_committed_case(evaluator_without_retrieval):
    assert main(["--all"]) == 0

    entries = golden_entries()
    assert evaluator_without_retrieval.received == entries
    assert [row["id"] for row in evaluator_without_retrieval.received] == [
        row["id"] for row in entries
    ]


def test_a_refused_selection_never_reaches_retrieval(evaluator_without_retrieval):
    """Every refusal path leaves retrieval untouched, in-process as well as in a
    fresh one — argparse exits `2` and the recorder is never called."""
    for arguments in ([], ["--case-id", "NOT_A_CASE"]):
        with pytest.raises(SystemExit) as exit_:
            main(arguments)

        assert exit_.value.code == 2
        assert evaluator_without_retrieval.received is None


# ---------------------------------------------------------------------------
# 6. Structural — the laziness, and the pipeline that did not change
# ---------------------------------------------------------------------------


def test_the_evaluator_imports_no_expensive_chain_at_module_scope(repository_root):
    """The regression guard for the import-time fix.

    A later edit that hoists either import back to module scope would restore
    the original defect — `--help` paying seconds and four machine-learning
    libraries before argparse could refuse the invocation. This fails on that
    edit directly, rather than waiting for the subprocess specifications to
    notice it.
    """
    module_scope = imported_modules(evaluator_source(repository_root))

    for lazy in LAZY_IMPORTS:
        assert lazy not in module_scope, (
            f"{lazy!r} is imported at module scope again; --help would pay for it"
        )


def test_the_expensive_imports_are_present_inside_the_authorized_path(repository_root):
    """The other half: deferred, not deleted.

    `retrieve_cases` still reaches the same runtime through the same modules —
    the pipeline is unchanged, only the moment of import moved.
    """
    tree = ast.parse(evaluator_source(repository_root))

    inside = {
        node.module
        for function in tree.body
        if isinstance(function, ast.FunctionDef)
        for node in ast.walk(function)
        if isinstance(node, ast.ImportFrom) and node.module
    }

    for lazy in LAZY_IMPORTS:
        assert lazy in inside, f"{lazy!r} is not imported anywhere it can run"


def test_retrieval_still_reaches_every_stage_through_its_owning_module(repository_root):
    """**M2-07 is MEASURE, not IMPROVE — and deferring an import is not a change
    to what is measured.**

    `retrieve_cases` must still call `canonical_order`, `fuse_routes`,
    `lexical_route`, `load_documents` and `semantic_route` from
    `scripts/run_hybrid_retrieval.py`, and construct `VectorIndexRuntime`. A
    refactor that quietly dropped or replaced one of these would change the
    retrieval M2-07 reports on, which this sprint has no authority to do.
    """
    tree = ast.parse(evaluator_source(repository_root))
    node = function_named(tree, "retrieve_cases")

    imported = {
        alias.name
        for statement in ast.walk(node)
        if isinstance(statement, ast.ImportFrom)
        for alias in statement.names
    }

    assert set(HYBRID_NAMES) <= imported
    assert "VectorIndexRuntime" in imported


def test_retrieval_takes_only_the_entries_it_is_given(repository_root):
    """`retrieve_cases` gained no selection parameter, and no case id.

    Selection is the caller's business. Had the id reached this function, the
    filtering could have moved *after* retrieval without any test above
    noticing.
    """
    assert list(inspect.signature(retrieve_cases).parameters) == ["entries"]

    source = evaluator_source(repository_root)
    node = function_named(ast.parse(source), "retrieve_cases")

    assert "case_id" not in ast.get_source_segment(source, node)


def test_main_selects_before_it_retrieves(repository_root):
    """**No filter-after-retrieve path exists**, read off the control flow.

    Established from the order of the calls in `main` rather than from a test
    name: `select_entries` is called, and only afterwards is `retrieve_cases`
    called — on the selection's result, never on the loaded dataset.
    """
    source = evaluator_source(repository_root)
    node = function_named(ast.parse(source), "main")

    called_at = {}
    for statement in ast.walk(node):
        if isinstance(statement, ast.Call) and isinstance(statement.func, ast.Name):
            line = called_at.get(statement.func.id)
            called_at[statement.func.id] = min(line or statement.lineno, statement.lineno)

    assert called_at["load_reference_entries"] < called_at["select_entries"]
    assert called_at["select_entries"] < called_at["retrieve_cases"]
    assert called_at["select_entries"] < called_at["compute"]

    retrieval_arguments = [
        statement.args
        for statement in ast.walk(node)
        if isinstance(statement, ast.Call)
        and isinstance(statement.func, ast.Name)
        and statement.func.id == "retrieve_cases"
    ]
    assert len(retrieval_arguments) == 1
    (argument,) = retrieval_arguments[0]
    assert isinstance(argument, ast.Name)
    assert argument.id != "entries", (
        "retrieve_cases is called on the loaded dataset, not on the selection"
    )


def test_the_metric_pipeline_after_selection_is_unchanged(repository_root):
    """The stages below selection are the pre-existing ones, in the same order.

    `retrieve_cases -> compute -> partition -> report_scores` is what the
    evaluator did before this sprint. Selection was inserted above it; nothing
    was inserted into it, and no stage was removed.
    """
    source = evaluator_source(repository_root)
    node = function_named(ast.parse(source), "main")

    stages = [
        (statement.lineno, statement.func.id)
        for statement in ast.walk(node)
        if isinstance(statement, ast.Call)
        and isinstance(statement.func, ast.Name)
        and statement.func.id
        in {"retrieve_cases", "compute", "partition", "report_scores"}
    ]
    order = [name for _, name in sorted(stages)]

    assert order == ["retrieve_cases", "compute", "partition", "report_scores"]


def test_the_parser_offers_exactly_the_two_authorized_selections(repository_root):
    """The interface is deliberately narrow.

    A selection that is neither *one named case* nor *the whole committed
    dataset* would report a figure over cases someone chose. `--limit`,
    `--subset`, `--sample`, `--index`, `--question` and `--ids` are absent, and
    stay absent.
    """
    options = {
        action.option_strings[0]
        for action in build_parser()._actions
        if action.option_strings
    }

    assert options == {"-h", "--case-id", "--all"}
