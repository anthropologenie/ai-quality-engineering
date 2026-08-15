"""Specifications for execution-evidence recording — Sprint M2.18.

Register capability **M2-18** — *"Execution Evidence / Traceability"* —
implemented under Repository Owner ruling **RO-15**
(`docs/DEFERRED_ITEMS_REGISTER.md` §4.7).

**No specification in this file reaches the live DeepSeek service**, and none
may. Generation is exercised through an injected fake provider, and every
specification that writes a trace writes it to `tmp_path` — **no specification
writes to `TRACE_ROOT`**, which is the derived runtime location the running
script uses. An autouse fixture makes an un-patched network call a loud failure
rather than a slow one.

What this suite asserts
------------------------
That the recorded evidence is **true of the execution that produced it**: that
ranks are the ranks the routes returned, that source legs are the routes a
candidate actually entered through, that references between the retrieval,
assembly and generation sections cannot dangle, that one completed execution
yields exactly one JSONL record, and that a credential or a semantic similarity
score can never appear in one.

What it deliberately does not assert
-------------------------------------
**Nothing about answer quality, and nothing about retrieval quality.** A trace
records what an execution did; it records nothing about whether the execution
was right. There is no faithfulness, groundedness, hallucination, answer
relevancy, context precision or context recall assertion here — those are
**M2-07** and **M2-08** work, which this sprint does not activate and which
RO-15 expressly does not block.

It also asserts **no reproducibility property of `answer_text`**. §24.3's G-9
split makes model output explicitly non-reproducible, which is *why* the answer
is persisted rather than recovered — a specification asserting otherwise would
claim what RO-13 declined to claim.
"""

import ast
import inspect
import json
import pathlib
import urllib.request

import pytest

from sample_rag.context_builder import ContextBuilder
from sample_rag.deepseek import API_KEY_VARIABLE
from sample_rag.fusion import RRF_K, RRF_SCORE_PRECISION, rank_candidates, reciprocal_rank_fusion
from sample_rag.model_generator import ModelGenerator

from scripts import execution_trace
from scripts.execution_trace import (
    CONTRACT_VERSIONS,
    TRACE_FILENAME,
    TRACE_ROOT,
    TraceIntegrityError,
    append,
    assembly_evidence,
    build_trace,
    candidate_evidence,
    generation_evidence,
    retrieval_evidence,
    serialize,
)

SEMANTIC = "SEMANTIC"
LEXICAL = "LEXICAL"
FUSED = "RRF"
TOP_K = 3

MODEL_ANSWER = "The corpus records AWS and Azure work."
FAKE_MODEL = "fake-model-1"


def chunk(chunk_id, text, document_id="doc-a", start=0):
    """One corpus chunk, satisfying `docs/CHUNK_CONTRACT.md` §17 invariants 1-2."""
    return {
        "id": chunk_id,
        "document_id": document_id,
        "text": text,
        "chunk_index": start,
        "character_start": start,
        "character_end": start + len(text),
        "section": "Experience",
        "token_estimate": max(1, len(text) // 4),
    }


class FakeClient:
    """A provider stand-in exposing the two attributes the trace layer reads.

    `model` is a property on the real `DeepSeekClient` and is what the trace
    records; `complete` is the sanctioned interaction. **No credential
    attribute exists here either**, which is the point: the trace layer is
    handed a client and can only record what a client exposes.
    """

    def __init__(self, answer=MODEL_ANSWER):
        self.answer = answer
        self.model = FAKE_MODEL
        self.calls = []

    def complete(self, messages):
        self.calls.append(messages)
        return self.answer


@pytest.fixture(autouse=True)
def no_live_network(monkeypatch):
    """No specification in this file may reach the network un-patched."""

    def refuse(*arguments, **keywords):
        raise AssertionError(
            "A specification attempted a live provider call. The deterministic "
            "suite must never depend on the DeepSeek service."
        )

    monkeypatch.setattr(urllib.request, "urlopen", refuse)


@pytest.fixture
def builder():
    """A Context Builder over a small corpus spanning two documents."""
    return ContextBuilder(
        [
            chunk("c0", "Deployed services on AWS.", document_id="doc-a", start=100),
            chunk("c1", "Managed Azure pipelines.", document_id="doc-b", start=40),
            chunk("c2", "Wrote Python tooling.", document_id="doc-a", start=300),
        ]
    )


@pytest.fixture
def routes():
    """Two ranked routes that overlap on one candidate and differ on the rest.

    `c1` is returned by both, at different ranks; `c0` by the semantic route
    alone and `c2` by the lexical route alone. That shape is what makes source
    legs, per-route ranks and the `None` case all observable in one execution.
    """
    return {SEMANTIC: ["c0", "c1"], LEXICAL: ["c1", "c2"]}


@pytest.fixture
def scored(routes):
    """The scored candidate union, from the repository's own fusion primitive."""
    return rank_candidates(routes[SEMANTIC], routes[LEXICAL], RRF_K, ["c0", "c1", "c2"])


@pytest.fixture
def selected(routes):
    """The fused ids the execution assembled from, through the fusion entry point."""
    return reciprocal_rank_fusion(
        routes[SEMANTIC], routes[LEXICAL], RRF_K, TOP_K, ["c0", "c1", "c2"]
    )


@pytest.fixture
def retrieval(routes, scored, selected):
    """The retrieval section of one execution's evidence."""
    return retrieval_evidence(FUSED, TOP_K, routes, scored, selected)


@pytest.fixture
def prompt(builder, selected):
    """The `Prompt` assembled from the fused order, unmodified."""
    return builder.assemble(builder.resolve(selected), "Which clouds?")


@pytest.fixture
def client():
    """A fake provider that answers successfully."""
    return FakeClient()


@pytest.fixture
def generator(client):
    """A real `ModelGenerator` bound to the fake provider."""
    return ModelGenerator(client, retrieval_route=FUSED)


@pytest.fixture
def result(generator, prompt):
    """One `GenerationResult` from the real generation component."""
    return generator.generate(prompt)


@pytest.fixture
def trace(prompt, retrieval, generator, client, result):
    """One completed execution's trace record."""
    return build_trace(
        prompt.query,
        retrieval,
        assembly_evidence(prompt),
        generation_evidence(generator, client, result, 12.34),
    )


def by_id(candidates):
    """Index candidate records by chunk id."""
    return {candidate["chunk_id"]: candidate for candidate in candidates}


def imported_modules(module):
    """Fully-qualified module names a module imports."""
    tree = ast.parse(pathlib.Path(module.__file__).read_text(encoding="utf-8"))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def walk_values(value):
    """Every scalar reachable in a nested JSON-shaped structure."""
    if isinstance(value, dict):
        for item in value.values():
            yield from walk_values(item)
    elif isinstance(value, list):
        for item in value:
            yield from walk_values(item)
    else:
        yield value


def walk_keys(value):
    """Every mapping key reachable in a nested JSON-shaped structure."""
    if isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from walk_keys(item)
    elif isinstance(value, list):
        for item in value:
            yield from walk_keys(item)


# ---------------------------------------------------------------------------
# 1. Trace construction — RO-15 Decision 3
# ---------------------------------------------------------------------------


def test_m218_a_trace_carries_the_four_evidence_sections(trace):
    """One record spans the whole execution, not one stage of it."""
    assert list(trace) == ["query", "retrieval", "assembly", "generation"]


def test_m218_the_trace_records_the_query_that_was_executed(trace, prompt):
    assert trace["query"] == prompt.query


def test_m218_a_trace_is_not_a_serialized_generation_result(trace):
    """RO-15 Decision 3 — a distinct envelope, not `GenerationResult`'s four fields.

    §7's field order is `answer_text`, `outcome`, `statements`, `diagnostics`.
    A trace carries neither `statements` nor `diagnostics` at any depth, and its
    top level is the execution rather than the generation.
    """
    keys = set(walk_keys(trace))

    assert "statements" not in keys
    assert "diagnostics" not in keys
    assert list(trace) != ["answer_text", "outcome", "statements", "diagnostics"]


# ---------------------------------------------------------------------------
# 2. Retrieval attribution — RO-15 Decision 5, source-leg semantics
# ---------------------------------------------------------------------------


def test_m218_the_candidate_union_is_every_candidate_both_routes_returned(retrieval, routes):
    """The union, not the selection — a candidate that lost is the diagnostic."""
    recorded = {candidate["chunk_id"] for candidate in retrieval["candidates"]}

    assert recorded == set(routes[SEMANTIC]) | set(routes[LEXICAL])


def test_m218_each_route_rank_is_the_position_that_route_returned(retrieval, routes):
    """Rank is position in the route's own ranked output, 1-based."""
    candidates = by_id(retrieval["candidates"])

    for route, ranked in routes.items():
        for position, chunk_id in enumerate(ranked, start=1):
            assert candidates[chunk_id][f"{route.lower()}_rank"] == position


def test_m218_a_route_that_did_not_supply_a_candidate_records_absence_not_zero(retrieval):
    """`None`, never `0` — absence is not a rank in a 1-based scheme."""
    candidates = by_id(retrieval["candidates"])

    assert candidates["c0"]["lexical_rank"] is None
    assert candidates["c2"]["semantic_rank"] is None
    assert candidates["c0"]["semantic_rank"] == 1


def test_m218_source_legs_are_the_routes_a_candidate_actually_entered_through(retrieval):
    """Phase 1A semantics — the route that supplied it, not the chunk's origin.

    `c1` was returned by both routes and carries both legs; the other two carry
    exactly the one route that returned them. No candidate is labelled with a
    route that did not produce it.
    """
    candidates = by_id(retrieval["candidates"])

    assert candidates["c1"]["source_legs"] == [LEXICAL, SEMANTIC]
    assert candidates["c0"]["source_legs"] == [SEMANTIC]
    assert candidates["c2"]["source_legs"] == [LEXICAL]


def test_m218_source_legs_agree_with_the_recorded_ranks(retrieval, routes):
    """A leg is present exactly when that route recorded a rank — one fact, not two."""
    for candidate in retrieval["candidates"]:
        for route in routes:
            has_rank = candidate[f"{route.lower()}_rank"] is not None
            assert (route in candidate["source_legs"]) == has_rank


def test_m218_the_fused_rank_and_score_are_the_fusion_primitives_own(retrieval, scored):
    """Nothing is re-ranked or re-scored — the record reads fusion's output back."""
    for position, (chunk_id, score) in enumerate(scored, start=1):
        candidate = by_id(retrieval["candidates"])[chunk_id]

        assert candidate["rrf_rank"] == position
        assert candidate["rrf_score"] == round(score, RRF_SCORE_PRECISION)


def test_m218_the_recorded_route_and_depth_are_the_executions_own(retrieval):
    assert retrieval["route"] == FUSED
    assert retrieval["top_k"] == TOP_K


def test_m218_a_selection_that_is_not_the_scored_order_is_refused(routes, scored):
    """The scored union and the executed selection must be the same ranking.

    The two come from separate calls — `rank_candidates` for the scores,
    `reciprocal_rank_fusion` for the selection — so their agreement is asserted
    rather than assumed. A disagreement raises instead of being written down.
    """
    with pytest.raises(TraceIntegrityError):
        retrieval_evidence(FUSED, TOP_K, routes, scored, ["c2", "c0"])


# ---------------------------------------------------------------------------
# 3. Assembly linkage — RO-15 Decision 6, §24.4
# ---------------------------------------------------------------------------


def test_m218_the_assembled_provenance_is_the_four_contract_fields(trace):
    """§24.4's four fields and no other — no chunk text, no score, no offsetless id."""
    for record in trace["assembly"]["provenance"]:
        assert list(record) == ["chunk_id", "document_id", "character_start", "character_end"]


def test_m218_the_selected_chunk_ids_are_the_provenance_in_assembled_order(trace, prompt):
    """Selected ids are referenced through provenance rather than listed twice."""
    recorded = [record["chunk_id"] for record in trace["assembly"]["provenance"]]

    assert recorded == list(prompt.chunk_ids)


def test_m218_the_assembled_order_is_the_fused_order(trace, selected):
    recorded = [record["chunk_id"] for record in trace["assembly"]["provenance"]]

    assert recorded == list(selected)


def test_m218_prompt_context_is_never_persisted(trace, prompt):
    """Corpus text is referenced through ids and offsets, not duplicated."""
    values = {value for value in walk_values(trace) if isinstance(value, str)}

    assert prompt.context not in values
    for text in ("Deployed services on AWS.", "Managed Azure pipelines."):
        assert text not in values


def test_m218_a_prompt_whose_provenance_disagrees_with_its_ids_is_refused(builder, selected):
    """A record whose own two views of the selection disagree is not written."""

    class Divergent:
        query = "q"
        context = ""
        chunk_ids = ["c0"]
        provenance = builder.assemble(builder.resolve(selected), "q").provenance

    with pytest.raises(TraceIntegrityError):
        assembly_evidence(Divergent())


# ---------------------------------------------------------------------------
# 4. Generation identity — RO-14 Decision 1, RO-15 Decision 7
# ---------------------------------------------------------------------------


def test_m218_the_generation_component_is_observed_not_declared(trace, generator):
    """The class that actually ran, read off the object the execution used."""
    assert trace["generation"]["component"] == type(generator).__name__
    assert trace["generation"]["component"] == "ModelGenerator"


def test_m218_the_generation_contract_version_is_the_milestone_2_era(trace):
    """RO-14 — `ModelGenerator` carries v2.0.0."""
    assert trace["generation"]["contract_version"] == "2.0.0"


def test_m218_the_frozen_milestone_1a_component_is_not_given_a_contract_era(trace):
    """`Generator` is absent deliberately — `scripts/cli.py` is not traced.

    Recording a v1.0.0 era would describe an execution the repository does not
    produce, because RO-15 authorizes no change to the Milestone 1A path.
    """
    assert "Generator" not in CONTRACT_VERSIONS
    assert set(CONTRACT_VERSIONS) == {"ModelGenerator"}


def test_m218_an_unrecognized_component_is_refused_rather_than_versioned(client, result):
    """A guessed contract version is fabricated evidence, so it raises instead."""

    class Improvised:
        pass

    with pytest.raises(TraceIntegrityError):
        generation_evidence(Improvised(), client, result, 1.0)


def test_m218_the_provider_and_model_are_read_from_the_client(trace, client):
    assert trace["generation"]["provider"] == type(client).__name__
    assert trace["generation"]["model"] == client.model


# ---------------------------------------------------------------------------
# 5. Generation evidence — RO-15 Decision 6
# ---------------------------------------------------------------------------


def test_m218_the_answer_text_is_persisted_because_it_cannot_be_recovered(trace, result):
    """§24.3's G-9 split makes model output non-reproducible — so it is kept."""
    assert trace["generation"]["answer_text"] == result.answer_text
    assert trace["generation"]["answer_text"] == MODEL_ANSWER


def test_m218_the_outcome_is_recorded(trace, result):
    assert trace["generation"]["outcome"] == result.outcome == "Answer"


def test_m218_statement_evidence_is_referenced_by_chunk_id_not_duplicated(trace, result):
    """Ids only — offsets, document and span text all resolve through provenance."""
    recorded = trace["generation"]["statement_evidence_chunk_ids"]
    expected = [
        [evidence.chunk_id for evidence in statement.supporting_evidence]
        for statement in result.statements
    ]

    assert recorded == expected


def test_m218_supporting_evidence_text_is_never_persisted(trace, result):
    """The span text is corpus content and is recoverable — §24.4's own claim."""
    values = {value for value in walk_values(trace) if isinstance(value, str)}

    for statement in result.statements:
        for evidence in statement.supporting_evidence:
            assert evidence.text not in values


def test_m218_the_observed_latency_is_recorded(trace):
    """Measured at the existing boundary; it enters no `GenerationResult`.

    One decimal place, which is the precision `scripts/run_generation.py`
    already prints this same measurement at — reused rather than re-chosen.
    """
    assert trace["generation"]["latency_ms"] == 12.3


def test_m218_generation_diagnostics_are_not_copied_into_the_trace(trace, result):
    """Its three keys are already carried, more precisely, by other fields."""
    assert set(result.diagnostics) == {"query", "retrieval_route", "stub"}
    assert "stub" not in set(walk_keys(trace))


# ---------------------------------------------------------------------------
# 6. Reference integrity — RO-15's diagnostic standing
# ---------------------------------------------------------------------------


def test_m218_every_assembled_chunk_appears_among_the_retrieval_candidates(trace):
    candidates = {candidate["chunk_id"] for candidate in trace["retrieval"]["candidates"]}
    assembled = {record["chunk_id"] for record in trace["assembly"]["provenance"]}

    assert assembled <= candidates


def test_m218_every_cited_chunk_appears_in_the_assembled_prompt(trace):
    assembled = {record["chunk_id"] for record in trace["assembly"]["provenance"]}

    for cited in trace["generation"]["statement_evidence_chunk_ids"]:
        assert set(cited) <= assembled


def test_m218_an_assembled_chunk_absent_from_retrieval_is_refused(trace):
    """A prompt chunk retrieval never produced cannot be written down."""
    retrieval = {"route": FUSED, "top_k": TOP_K, "candidates": [{"chunk_id": "elsewhere"}]}

    with pytest.raises(TraceIntegrityError):
        build_trace("q", retrieval, trace["assembly"], trace["generation"])


def test_m218_evidence_citing_an_unassembled_chunk_is_refused(trace):
    """A dangling citation is worse than none — it looks checkable."""
    generation = dict(trace["generation"], statement_evidence_chunk_ids=[["never-assembled"]])

    with pytest.raises(TraceIntegrityError):
        build_trace("q", trace["retrieval"], trace["assembly"], generation)


# ---------------------------------------------------------------------------
# 7. JSONL storage — RO-15 Decision 4
# ---------------------------------------------------------------------------


def test_m218_one_execution_serializes_to_exactly_one_line(trace):
    line = serialize(trace)

    assert line.endswith("\n")
    assert line.count("\n") == 1


def test_m218_a_multiline_answer_does_not_break_the_record_boundary(trace):
    """JSON escapes the newline, so one record stays one line whatever it holds."""
    generation = dict(trace["generation"], answer_text="first line\nsecond line")
    line = serialize(dict(trace, generation=generation))

    assert line.count("\n") == 1
    assert json.loads(line)["generation"]["answer_text"] == "first line\nsecond line"


def test_m218_a_serialized_record_round_trips(trace):
    assert json.loads(serialize(trace)) == trace


def test_m218_the_trace_form_is_not_the_generation_contract_serialization_form(trace):
    """RO-15 Decision 4 — §13.2's `indent=2` form cannot be one JSONL line.

    The two forms differ because the two artifacts differ. §13.2 remains in
    force, unamended, for the `GenerationResult` it governs.
    """
    line = serialize(trace)

    assert line != json.dumps(trace, indent=2) + "\n"
    assert "\n" not in line[:-1]


def test_m218_one_execution_appends_one_record(tmp_path, trace):
    path = tmp_path / TRACE_FILENAME
    append(trace, path)

    assert path.read_text(encoding="utf-8").splitlines() == [serialize(trace).rstrip("\n")]


def test_m218_a_second_execution_appends_beside_the_first_rather_than_replacing_it(tmp_path, trace):
    """Earlier records are evidence of earlier executions and are not edited."""
    path = tmp_path / TRACE_FILENAME
    append(trace, path)
    append(dict(trace, query="a second question"), path)

    lines = path.read_text(encoding="utf-8").splitlines()

    assert len(lines) == 2
    assert [json.loads(line)["query"] for line in lines] == [trace["query"], "a second question"]


def test_m218_the_destination_directory_is_created_on_demand(tmp_path, trace):
    path = tmp_path / "absent" / TRACE_FILENAME
    append(trace, path)

    assert path.exists()


def test_m218_the_trace_file_is_not_a_json_array(tmp_path, trace):
    """JSONL, not a document — RO-15 authorizes one record per line and no wrapper."""
    path = tmp_path / TRACE_FILENAME
    append(trace, path)
    append(trace, path)
    text = path.read_text(encoding="utf-8")

    assert not text.lstrip().startswith("[")
    with pytest.raises(json.JSONDecodeError):
        json.loads(text)


# ---------------------------------------------------------------------------
# 8. Credential safety — RO-15 Decision 8, absolute
# ---------------------------------------------------------------------------


def test_m218_no_credential_reaches_a_trace(monkeypatch, trace):
    """The key is set in the environment and appears nowhere in the record."""
    secret = "sk-m218-specification-sentinel"
    monkeypatch.setenv(API_KEY_VARIABLE, secret)
    line = serialize(trace)

    assert secret not in line
    assert API_KEY_VARIABLE not in line


def test_m218_the_trace_layer_never_reads_the_environment(monkeypatch):
    """Credential absence is structural, not a promise about a code path."""
    source = pathlib.Path(execution_trace.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    names = {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}

    assert "os" not in imported_modules(execution_trace)
    assert "environ" not in names
    assert "getenv" not in names


def test_m218_no_authorization_or_header_material_is_recorded(trace):
    keys = {key.lower() for key in walk_keys(trace)}

    for barred in ("authorization", "api_key", "apikey", "token", "secret", "headers"):
        assert barred not in keys


def test_m218_no_raw_provider_payload_is_recorded(trace, client, result):
    """The request the provider received is not part of the evidence."""
    keys = set(walk_keys(trace))

    assert "request" not in keys
    assert "response" not in keys
    assert "messages" not in keys
    assert client.calls
    assert json.dumps(client.calls) not in serialize(trace)


# ---------------------------------------------------------------------------
# 9. The closed retrieval boundary — RO-15 Decision 5
# ---------------------------------------------------------------------------


def test_m218_no_semantic_similarity_score_is_recorded(trace):
    """Semantic rank is authorized; semantic score is not, and does not exist here."""
    keys = {key.lower() for key in walk_keys(trace)}

    for barred in ("similarity", "distance", "semantic_score", "embedding", "vector"):
        assert barred not in keys


def test_m218_the_only_recorded_score_is_the_fusion_score(trace):
    """One score field, and it is RRF's — the score the fusion primitive computes."""
    scoring = {key for key in walk_keys(trace) if "score" in key.lower()}

    assert scoring == {"rrf_score"}


def test_m218_the_trace_layer_does_not_reach_the_vector_store(trace):
    """The `VectorStore` boundary stays closed — RO-15 authorizes no widening."""
    imports = imported_modules(execution_trace)

    assert "sample_rag.vector_index" not in imports
    assert "sample_rag.vector_runtime" not in imports
    assert imports == {"json", "pathlib", "sample_rag.fusion"}


def test_m218_no_bm25_score_is_recorded(trace, retrieval):
    """RO-15's authorized list carries BM25 **rank**, not BM25 score."""
    for candidate in retrieval["candidates"]:
        assert "lexical_score" not in candidate
        assert "bm25_score" not in candidate
        assert candidate["lexical_rank"] is None or isinstance(candidate["lexical_rank"], int)


# ---------------------------------------------------------------------------
# 10. Nothing is fabricated — RO-15 Decision 5
# ---------------------------------------------------------------------------


def test_m218_absent_evidence_is_recorded_as_absent_rather_than_invented(routes, scored, selected):
    """A route that returned nothing contributes no ranks and no legs."""
    empty = {SEMANTIC: [], LEXICAL: routes[LEXICAL]}
    lexical_only = rank_candidates([], routes[LEXICAL], RRF_K, ["c0", "c1", "c2"])
    evidence = retrieval_evidence(
        FUSED,
        TOP_K,
        empty,
        lexical_only,
        [chunk_id for chunk_id, _ in lexical_only][:TOP_K],
    )

    for candidate in evidence["candidates"]:
        assert candidate["semantic_rank"] is None
        assert candidate["source_legs"] == [LEXICAL]


def test_m218_no_timestamp_is_invented(trace):
    """No wall-clock convention exists in the repository, so none is manufactured.

    Recorded as a limitation in `docs/M2.18_Execution_Evidence_Report.md` rather
    than satisfied with a value this repository has no convention for.
    """
    keys = {key.lower() for key in walk_keys(trace)}

    for invented in ("timestamp", "executed_at", "created_at", "started_at", "date", "time"):
        assert invented not in keys


def test_m218_no_synthetic_execution_identifier_is_invented(trace):
    keys = {key.lower() for key in walk_keys(trace)}

    for invented in ("execution_id", "trace_id", "run_id", "uuid", "id"):
        assert invented not in keys


def test_m218_no_value_in_a_trace_is_none(trace):
    """Absence is expressed only where a route genuinely supplied no rank."""
    optional = {"semantic_rank", "lexical_rank"}
    for section in ("query", "assembly", "generation"):
        assert all(value is not None for value in walk_values(trace[section]))

    for candidate in trace["retrieval"]["candidates"]:
        for key, value in candidate.items():
            assert value is not None or key in optional


# ---------------------------------------------------------------------------
# 11. Derived runtime artifact, not source — RO-15 Decision 8
# ---------------------------------------------------------------------------


def test_m218_the_trace_directory_is_git_ignored(repository_root):
    """RO-09's precedent, mirrored: the directory is ignored, the module is source."""
    ignored = (repository_root / ".gitignore").read_text(encoding="utf-8").splitlines()

    assert "scripts/execution_trace/" in ignored
    assert "scripts/execution_trace.py" not in ignored


def test_m218_no_trace_record_lives_outside_the_ignored_runtime_location(repository_root):
    """A runtime artifact must never be mistaken for a source fixture.

    Records **inside** `TRACE_ROOT` are expected — that is where a real run puts
    them, and the `.gitignore` rule above keeps them untracked. What must not
    exist is a `.jsonl` anywhere else, which is what a committed sample trace or
    a stray test fixture would look like.
    """
    stray = [
        path
        for path in repository_root.glob("**/*.jsonl")
        if TRACE_ROOT not in path.parents
    ]

    assert stray == []


def test_m218_the_trace_destination_is_always_explicit():
    """No specification can write to the runtime location by omission.

    `append` takes its destination as a required argument — there is no default
    parameter that would silently resolve to `TRACE_ROOT`. That is the structural
    property that keeps the suite out of the runtime directory, rather than a
    convention each specification has to remember; asserting it here is stronger
    than scanning this file's own text for a call it would itself match.
    """
    path = inspect.signature(append).parameters["path"]

    assert path.default is inspect.Parameter.empty


def test_m218_the_runtime_location_sits_beside_the_module_that_writes_it(repository_root):
    """The RO-09 shape — `scripts/execution_trace/` beside `scripts/execution_trace.py`."""
    assert TRACE_ROOT == repository_root / "scripts" / "execution_trace"
    assert TRACE_FILENAME.endswith(".jsonl")


# ---------------------------------------------------------------------------
# 12. The frozen Milestone 1A path is untouched — RO-14 Decision 2
# ---------------------------------------------------------------------------


def test_m218_no_pipeline_module_learns_about_tracing(repository_root):
    """`sample_rag/` does not import the trace layer, and cannot — §6's direction."""
    for module in (repository_root / "sample_rag").glob("*.py"):
        source = module.read_text(encoding="utf-8")

        assert "execution_trace" not in source
        assert "scripts" not in imported_modules_of(source)


def imported_modules_of(source):
    """Fully-qualified module names imported by a source string."""
    tree = ast.parse(source)
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module.split(".")[0])
    return names


def test_m218_the_milestone_1a_entry_point_is_not_traced(repository_root):
    """`scripts/cli.py` keeps its Milestone 1A chain and writes no trace."""
    source = (repository_root / "scripts" / "cli.py").read_text(encoding="utf-8")

    assert "execution_trace" not in source
    assert "ModelGenerator" not in source


def test_m218_the_generation_components_carry_no_trace_metadata(repository_root):
    """RO-15 Decision 7 — identity is observed at the boundary, not stored on them.

    Asserted over referenced names rather than over the modules' text, which is
    prose as much as code: neither component gained a field, a constant or an
    attribute describing its own contract era, and neither reaches the trace
    layer.
    """
    for name in ("generator.py", "model_generator.py"):
        source = (repository_root / "sample_rag" / name).read_text(encoding="utf-8")
        tree = ast.parse(source)
        referenced = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
        referenced |= {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
        assigned = {
            target.id
            for node in ast.walk(tree)
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)
            for target in [node.target]
        }

        assert "execution_trace" not in imported_modules_of(source)
        assert not {"contract_version", "component", "trace"} & (referenced | assigned)


# ---------------------------------------------------------------------------
# 13. The wiring at the execution boundary — RO-15's implementation location
# ---------------------------------------------------------------------------


def test_m218_a_completed_execution_appends_exactly_one_record(tmp_path, monkeypatch, prompt, retrieval, client):
    """`main` end to end, with retrieval and the provider replaced by fakes.

    The corpus, the FAISS index and the network are all out of scope here — what
    is being specified is that one completed run of the boundary produces one
    record, in the file the module names, and that the record describes *that*
    run.
    """
    import scripts.run_generation as runner

    monkeypatch.setattr(runner, "assemble_prompt", lambda question: (prompt, 3, retrieval))
    monkeypatch.setattr(runner, "DeepSeekClient", lambda: client)
    monkeypatch.setattr(runner, "TRACE_ROOT", tmp_path)

    assert runner.main(["--question", prompt.query]) == 0

    lines = (tmp_path / TRACE_FILENAME).read_text(encoding="utf-8").splitlines()

    assert len(lines) == 1
    recorded = json.loads(lines[0])
    assert recorded["query"] == prompt.query
    assert recorded["generation"]["component"] == "ModelGenerator"
    assert recorded["generation"]["model"] == FAKE_MODEL


def test_m218_two_executions_append_two_records(tmp_path, monkeypatch, prompt, retrieval, client):
    import scripts.run_generation as runner

    monkeypatch.setattr(runner, "assemble_prompt", lambda question: (prompt, 3, retrieval))
    monkeypatch.setattr(runner, "DeepSeekClient", lambda: client)
    monkeypatch.setattr(runner, "TRACE_ROOT", tmp_path)

    runner.main(["--question", prompt.query])
    runner.main(["--question", prompt.query])

    assert len((tmp_path / TRACE_FILENAME).read_text(encoding="utf-8").splitlines()) == 2


def test_m218_a_failed_execution_writes_no_trace(tmp_path, monkeypatch, prompt, retrieval):
    """RO-15 scopes M2-18 to *completed* executions.

    A provider failure propagates, as `scripts/run_generation.py` deliberately
    lets it, and no record is written — so a trace can never describe a
    generation that did not happen, and no misleading "successful" record
    exists. This is placement, not an exception framework: nothing here catches
    anything.
    """
    import scripts.run_generation as runner
    from sample_rag.deepseek import ProviderRequestError

    class FailingClient(FakeClient):
        def complete(self, messages):
            raise ProviderRequestError("transport refused")

    monkeypatch.setattr(runner, "assemble_prompt", lambda question: (prompt, 3, retrieval))
    monkeypatch.setattr(runner, "DeepSeekClient", FailingClient)
    monkeypatch.setattr(runner, "TRACE_ROOT", tmp_path)

    with pytest.raises(ProviderRequestError):
        runner.main(["--question", prompt.query])

    assert not (tmp_path / TRACE_FILENAME).exists()


def test_m218_the_execution_boundary_records_the_run_it_performed(repository_root):
    """The wiring lives in `scripts/run_generation.py` and nowhere else."""
    source = (repository_root / "scripts" / "run_generation.py").read_text(encoding="utf-8")
    called = {
        node.func.id
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }

    assert {"build_trace", "assembly_evidence", "generation_evidence", "retrieval_evidence"} <= called
    assert "append" in called


# ---------------------------------------------------------------------------
# 14. Sprint scope boundary
# ---------------------------------------------------------------------------


def test_m218_the_trace_layer_adds_no_dependency():
    """Standard library plus one repository module — RO-15 authorizes no dependency."""
    assert imported_modules(execution_trace) == {"json", "pathlib", "sample_rag.fusion"}


def test_m218_no_evaluation_tooling_is_activated():
    """M2-07, M2-08 and M3-01 are untouched — a trace measures nothing."""
    source = pathlib.Path(execution_trace.__file__).read_text(encoding="utf-8").lower()

    for tool in ("ragas", "deepeval", "promptfoo"):
        assert tool not in source


def test_m218_the_trace_layer_asserts_no_quality_property():
    """A trace records what happened, never whether it was correct."""
    source = pathlib.Path(execution_trace.__file__).read_text(encoding="utf-8").lower()

    for metric in ("faithfulness", "groundedness", "hallucination", "relevancy", "precision@"):
        assert metric not in source
