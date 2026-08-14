"""Specifications for model-backed generation — Sprint M2.06.

Register capability **M2-06** — *"DeepSeek API generation"* — implemented
against `docs/GENERATION_CONTRACT.md` **§24** (Generation Contract **v2.0.0**)
under Repository Owner ruling **RO-13**.

**No specification in this file reaches the live DeepSeek service**, and none
may. The provider is exercised through injected fakes and through a patched
`urllib.request.urlopen`; an autouse fixture makes an un-patched network call a
loud failure rather than a slow one, so a specification that accidentally
acquired a real dependency fails immediately and by name. The real-provider
acceptance check is `scripts/run_generation.py`, is not part of this suite, and
is recorded in `docs/M2.06_Generation_Report.md`.

What this suite asserts, and what it deliberately cannot
----------------------------------------------------------
It asserts the **structural** half of §24.3 in full: `Prompt` consumption,
provenance mapping, evidence derivation, statement construction, ordering,
request construction, response parsing, schema mapping, error classification,
diagnostics and outcome selection are all deterministic and all checked here.

It asserts **nothing about answer quality**. There is no faithfulness,
groundedness, hallucination, answer-relevancy, context-precision or
context-recall assertion anywhere below, and there is no *"the same prompt
produces the same answer"* assertion either — §24.3 makes model output
reproducibility explicitly **not guaranteed**, and a specification asserting it
would be claiming what RO-13 declined to claim.

Layout, in order: the `Prompt` contract and its rejection surface; evidence
derivation; statements and ordering; the outcome and its diagnostics; request
construction; response parsing; failure semantics; credential containment; the
determinism boundary; the structural dependency boundary; and the sprint scope
boundary.
"""

import ast
import importlib
import inspect
import io
import json
import pathlib
import urllib.error
import urllib.request

import pytest

from sample_rag.context_builder import CONTEXT_SEPARATOR, ContextBuilder
from sample_rag.deepseek import (
    API_KEY_VARIABLE,
    DEFAULT_MODEL,
    STATUS_REASONS,
    DeepSeekClient,
    ProviderConfigurationError,
    ProviderError,
    ProviderRequestError,
    ProviderResponseError,
    build_request_body,
    parse_completion,
)
from sample_rag.generator import (
    ABSTENTION_TEXT,
    OUTCOME_ABSTAIN,
    OUTCOME_ANSWER,
    GeneratedStatement,
    GenerationResult,
    SupportingEvidence,
    serialize,
)
from sample_rag.model_generator import (
    GENERATION_STUB,
    SYSTEM_INSTRUCTION,
    GenerationInputError,
    ModelGenerator,
)

# The route the fixtures below report. A literal, not an import from
# `sample_rag.retriever`: this module must not import a retrieval component even
# in a specification, because `test_m206_the_generator_reaches_no_retrieval_component`
# states that as a structural property of the module under test and a test that
# borrowed the constant would be reaching across the same boundary to check it.
ROUTE = "RRF"

MODEL_ANSWER = "Cloud platforms named in the evidence: AWS and Azure."


# ---------------------------------------------------------------------------
# helpers and fixtures
# ---------------------------------------------------------------------------


def chunk(chunk_id, text, document_id="doc-a", start=0):
    """One chunk mapping, shaped exactly as the committed Chunk Corpus stores them.

    The same helper `tests/test_generator.py` and `tests/test_context_builder.py`
    use, for the same reason: a specification exercising generation should never
    also be exercising a malformed corpus. Offsets satisfy
    `docs/CHUNK_CONTRACT.md` §17 invariants 1 and 2.
    """
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
    """A provider stand-in that records what it was asked and answers fixed text.

    Recording rather than merely returning: most of what this suite must
    establish is about the request — that it carries the context and the query,
    that it carries **nothing else**, and that it is byte-identical across runs.
    A stand-in that only returned an answer could not show any of it.

    `calls` also makes *"the Abstain path performs no provider interaction"* a
    checkable count rather than an assurance.
    """

    def __init__(self, answer=MODEL_ANSWER, error=None):
        self.answer = answer
        self.error = error
        self.calls = []

    def complete(self, messages):
        self.calls.append(messages)
        if self.error is not None:
            raise self.error
        return self.answer


@pytest.fixture(autouse=True)
def no_live_network(monkeypatch):
    """No specification in this file may reach the network un-patched.

    Autouse, so it protects specifications written later by someone who did not
    read this docstring. A test that needs the transport exercised patches
    `urllib.request.urlopen` itself, which overrides this; anything else that
    reaches it fails here with a message naming the cause rather than timing out
    against a real endpoint or — worse — quietly succeeding and spending a
    credential.
    """

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
def prompt(builder):
    """One assembled `Prompt` carrying three chunks in a non-corpus order."""
    return builder.assemble(builder.resolve(["c2", "c0", "c1"]), "What clouds?")


@pytest.fixture
def client():
    """A fake provider that answers successfully."""
    return FakeClient()


@pytest.fixture
def generator(client):
    """A generator bound to the fake provider and a named retrieval route."""
    return ModelGenerator(client, retrieval_route=ROUTE)


def http_response(payload):
    """A minimal stand-in for the object `urlopen` yields as a context manager."""

    class Response(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *arguments):
            return False

    return Response(json.dumps(payload).encode("utf-8"))


def completion(content):
    """A response document of the provider's documented successful shape."""
    return {
        "id": "chatcmpl-synthetic",
        "object": "chat.completion",
        "model": DEFAULT_MODEL,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
    }


def imported_roots(module):
    """Top-level package names a module imports."""
    tree = ast.parse(pathlib.Path(module.__file__).read_text(encoding="utf-8"))
    roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".")[0])
    return roots


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


# ---------------------------------------------------------------------------
# 1. The interface — U-1, resolved by RO-13 at §24.2
# ---------------------------------------------------------------------------


def test_m206_generate_takes_exactly_a_prompt():
    """§24.2 — `Generator.generate(prompt: Prompt) -> GenerationResult`.

    The **U-1** resolution, stated as a signature. One argument, named `prompt`.
    A second parameter — a query, a route, a client, a `RetrievalResult`, an
    options mapping — would be a second generation input path, and §24.2 states
    that *"there is exactly one authoritative generation input path."*
    """
    parameters = list(inspect.signature(ModelGenerator.generate).parameters)

    assert parameters == ["self", "prompt"]


def test_m206_the_generator_never_consumes_a_retrieval_result(generator, prompt):
    """§24.2 — *"The v2 Generator SHALL NOT consume a `RetrievalResult`."*

    Stated over **referenced names** rather than raw source text, the convention
    `tests/test_lexical_bm25.py` set: the module docstring legitimately *mentions*
    `RetrievalResult` to record that it is not consumed, and a substring check
    would make that prose a failure while missing a consumption expressed under
    any other name. What is asserted is that no executable name in the module —
    no parameter, attribute, annotation, call target or isinstance check —
    refers to it.
    """
    import sample_rag.model_generator as module

    tree = ast.parse(inspect.getsource(module))
    referenced = {
        node.id for node in ast.walk(tree) if isinstance(node, ast.Name)
    } | {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
    referenced |= {
        argument.arg for node in ast.walk(tree)
        if isinstance(node, ast.arg) for argument in [node]
    }

    assert "RetrievalResult" not in referenced
    assert "retrieval" not in referenced
    assert generator.generate(prompt).outcome == OUTCOME_ANSWER


def test_m206_the_client_and_route_are_required_at_construction():
    """Neither has a default — the provider and the route are stated, not assumed.

    A `ModelGenerator()` that built its own live client would make the
    sanctioned interaction reachable by accident. A default `retrieval_route`
    would be this module inventing a route for §8.4's required key rather than
    recording the one that actually fed the assembly.
    """
    parameters = inspect.signature(ModelGenerator.__init__).parameters

    assert list(parameters) == ["self", "client", "retrieval_route"]
    for name in ("client", "retrieval_route"):
        assert parameters[name].default is inspect.Parameter.empty


# ---------------------------------------------------------------------------
# 2. Evidence derivation — G-7 narrowed to provenance (§24.3, §24.4)
# ---------------------------------------------------------------------------


def test_m206_evidence_is_built_from_prompt_provenance(generator, prompt, builder):
    """G-7 — every span derives from the `Prompt`, and from nothing else.

    Each `SupportingEvidence` carries the four provenance values unchanged and a
    `text` recovered from `context`. **No identifier passed through the
    provider**, and none was recomputed: G-6's *"the Generator never constructs
    a chunk id"* holds under v2.0.0 exactly as it did under v1.0.0.
    """
    result = generator.generate(prompt)
    spans = [span for statement in result.statements for span in statement.supporting_evidence]

    assert [span.chunk_id for span in spans] == ["c2", "c0", "c1"]
    assert [span.document_id for span in spans] == ["doc-a", "doc-a", "doc-b"]
    assert [(span.character_start, span.character_end) for span in spans] == [
        (300, 321),
        (100, 125),
        (40, 64),
    ]
    assert [span.text for span in spans] == [
        record["text"] for record in builder.resolve(["c2", "c0", "c1"])
    ]


def test_m206_evidence_text_is_recovered_by_offset_not_by_splitting(builder):
    """The derivation survives a chunk whose own text contains the separator.

    `sample_rag/context_builder.py` documents its assembly as reversible only
    over a corpus whose chunk texts contain no blank line. A consumer that
    recovered blocks by splitting on `CONTEXT_SEPARATOR` would inherit that
    condition and mis-attribute evidence the day the corpus stopped meeting it;
    offset arithmetic carries no such condition, and this states the difference
    on a corpus that breaks the naive approach.
    """
    separator_builder = ContextBuilder(
        [
            chunk("s0", "first line" + CONTEXT_SEPARATOR + "second line", start=0),
            chunk("s1", "plain", start=500),
        ]
    )
    supplied = ["s0", "s1"]
    assembled = separator_builder.assemble(separator_builder.resolve(supplied), "q")

    result = ModelGenerator(FakeClient(), retrieval_route=ROUTE).generate(assembled)
    spans = [span for statement in result.statements for span in statement.supporting_evidence]

    assert len(spans) == 2
    assert spans[0].text == "first line" + CONTEXT_SEPARATOR + "second line"
    assert spans[1].text == "plain"


def test_m206_evidence_satisfies_the_span_length_invariant(generator, prompt):
    """§17 invariant 6 — `len(text) == character_end - character_start`.

    Holds by construction rather than by check: the slice length *is* the offset
    difference, so a span of the wrong length is not a representable state.
    Invariant 5 (`character_end > character_start`) is enforced on the way in.
    """
    result = generator.generate(prompt)

    for statement in result.statements:
        for span in statement.supporting_evidence:
            assert len(span.text) == span.character_end - span.character_start
            assert span.character_end > span.character_start


def test_m206_the_model_answer_never_becomes_evidence(generator, prompt):
    """G-7 — `SupportingEvidence` is not derived from model prose.

    The provider's chat-completion contract carries no citation or
    evidence-selection field, so attributing a sentence of the answer to a chunk
    would be inventing an attribution the provider never made. The answer text
    appears in `answer_text` and **nowhere else in the artifact**.
    """
    result = generator.generate(prompt)

    assert result.answer_text == MODEL_ANSWER
    for statement in result.statements:
        assert statement.text != MODEL_ANSWER
        for span in statement.supporting_evidence:
            assert span.text != MODEL_ANSWER
            assert MODEL_ANSWER not in span.text


def test_m206_evidence_is_fixed_before_the_provider_is_called(prompt):
    """The evidence chain cannot depend on the provider, because it precedes it.

    A malformed `Prompt` raises before a call is made, so no sanctioned
    interaction is ever spent on an artifact that could not have been
    constructed. Stated with a client that would fail loudly if reached.
    """
    broken = type(prompt)(
        query=prompt.query,
        context=prompt.context,
        chunk_ids=prompt.chunk_ids[:2],
        provenance=prompt.provenance,
    )
    client = FakeClient()

    with pytest.raises(GenerationInputError):
        ModelGenerator(client, retrieval_route=ROUTE).generate(broken)

    assert client.calls == []


# ---------------------------------------------------------------------------
# 3. The `Prompt` rejection surface — a context-assembly failure at the seam
# ---------------------------------------------------------------------------


def test_m206_a_prompt_whose_provenance_disagrees_with_its_ids_is_rejected(prompt):
    """§24.4 requires the two orderings to correspond; a `Prompt` that does not, fails.

    Not silently sliced from the wrong place, and not repaired: the artifact
    arrived internally inconsistent, and inventing a correspondence would put
    evidence in the result that no assembly produced.
    """
    scrambled = type(prompt)(
        query=prompt.query,
        context=prompt.context,
        chunk_ids=list(reversed(prompt.chunk_ids)),
        provenance=prompt.provenance,
    )

    with pytest.raises(GenerationInputError):
        ModelGenerator(FakeClient(), retrieval_route=ROUTE).generate(scrambled)


def test_m206_a_prompt_whose_offsets_do_not_span_the_context_is_rejected(prompt):
    """Provenance that accounts for the wrong number of characters is a failure.

    The arithmetic is checked rather than trusted. A context longer or shorter
    than its provenance describes is not one assembly, and a consumer that
    proceeded would emit spans sliced from positions nothing put text at.
    """
    truncated = type(prompt)(
        query=prompt.query,
        context=prompt.context[:-5],
        chunk_ids=prompt.chunk_ids,
        provenance=prompt.provenance,
    )

    with pytest.raises(GenerationInputError):
        ModelGenerator(FakeClient(), retrieval_route=ROUTE).generate(truncated)


def test_m206_a_prompt_failure_is_distinct_from_every_provider_failure(prompt):
    """A context-assembly failure and a provider failure are different conditions.

    The distinction is operational: one is fixed by the repository, the other by
    the provider or the operator. `GenerationInputError` is therefore not a
    `ProviderError` and never will be by inheritance.
    """
    assert not issubclass(GenerationInputError, ProviderError)
    assert not issubclass(ProviderError, GenerationInputError)


# ---------------------------------------------------------------------------
# 4. Statements and ordering — G-4, G-10, §11
# ---------------------------------------------------------------------------


def test_m206_every_statement_carries_at_least_one_span(generator, prompt):
    """G-4 — *"a statement with no evidence is exactly what guarantee 1 forbids."*

    Structural here as under v1.0.0: a statement is only ever constructed from a
    span, so the empty list is not a representable state.
    """
    result = generator.generate(prompt)

    assert result.statements
    for statement in result.statements:
        assert isinstance(statement, GeneratedStatement)
        assert len(statement.supporting_evidence) >= 1
        assert all(isinstance(span, SupportingEvidence) for span in statement.supporting_evidence)


def test_m206_statement_order_is_the_assembled_chunk_order(builder):
    """§11.1 — statements follow retrieval rank, carried through the `Prompt`.

    Exercised on an order that contradicts corpus order in every position, so a
    generator that sorted or fell back to corpus order fails here rather than
    passing by coincidence. No sort is applied because there is nothing to
    reorder: the ranking is `sample_rag/fusion.py`'s and arrives already made.
    """
    supplied = ["c1", "c2", "c0"]
    assembled = builder.assemble(builder.resolve(supplied), "a query")

    result = ModelGenerator(FakeClient(), retrieval_route=ROUTE).generate(assembled)

    assert [
        span.chunk_id for statement in result.statements for span in statement.supporting_evidence
    ] == supplied


def test_m206_no_span_is_repeated_within_a_statement(generator, prompt):
    """§17 invariant 11 — total within-statement ordering, §11.2.

    Holds because there is exactly one span per statement; asserted so that a
    later implementation emitting several cannot violate it unnoticed.
    """
    result = generator.generate(prompt)

    for statement in result.statements:
        keys = [
            (span.chunk_id, span.character_start, span.character_end)
            for span in statement.supporting_evidence
        ]
        assert len(keys) == len(set(keys))


# ---------------------------------------------------------------------------
# 5. Outcome and diagnostics — G-1, G-2, G-3, G-8, §8.4, §24.5
# ---------------------------------------------------------------------------


def test_m206_the_result_carries_exactly_the_four_contract_fields(generator, prompt):
    """G-1 — §8.1's four fields, unchanged by v2.0.0 (§24.3).

    The artifact is the same one; only what fills `answer_text` changed. A v2
    copy of `GenerationResult` would have been a second definition of one
    contract, so the class is imported from `sample_rag/generator.py` rather
    than redeclared — asserted here as identity, not merely shape.
    """
    result = generator.generate(prompt)

    assert isinstance(result, GenerationResult)
    assert [field for field in result.__dataclass_fields__] == [
        "answer_text",
        "outcome",
        "statements",
        "diagnostics",
    ]
    assert not any(getattr(result, field) is None for field in result.__dataclass_fields__)


def test_m206_an_assembled_prompt_produces_the_answer_outcome(generator, prompt):
    """G-2, G-3 — `Answer`, with the provider's text carried through verbatim.

    Not reformatted, trimmed, wrapped, prefixed or post-processed: Post-Process
    is not exercised, so *Raw Output* and *Delivered Output* coincide
    (`docs/altm.md` §4, contract §21).
    """
    result = generator.generate(prompt)

    assert result.outcome == OUTCOME_ANSWER
    assert result.answer_text == MODEL_ANSWER
    assert result.answer_text


def test_m206_an_empty_prompt_abstains_without_calling_the_provider(builder, client):
    """§9.3, G-8 — abstention is decided from the `Prompt`, and costs no call.

    `Abstain` is the outcome in which the Generator makes no claim about the
    corpus. Under §24.2's pipeline an empty assembled prompt is exactly an empty
    retrieval, so the predicate is the same one v1.0.0 used, applied to the
    artifact v2.0.0 consumes. **The provider is not asked**: there is nothing to
    answer from, and a call would spend a sanctioned interaction to obtain text
    the contract requires to be fixed.
    """
    empty = builder.assemble([], "a query with no evidence")

    result = ModelGenerator(client, retrieval_route=ROUTE).generate(empty)

    assert result.outcome == OUTCOME_ABSTAIN
    assert result.statements == []
    assert result.answer_text == ABSTENTION_TEXT
    assert client.calls == []


def test_m206_statements_are_empty_if_and_only_if_the_outcome_is_abstain(builder, prompt):
    """G-8 — a biconditional, satisfied structurally rather than by check.

    Both are decided by one emptiness test in `generate`, so they cannot
    disagree. Stated over both paths, because a biconditional checked on one
    side is an implication.
    """
    answered = ModelGenerator(FakeClient(), retrieval_route=ROUTE).generate(prompt)
    abstained = ModelGenerator(FakeClient(), retrieval_route=ROUTE).generate(
        builder.assemble([], "q")
    )

    for result in (answered, abstained):
        assert (result.statements == []) == (result.outcome == OUTCOME_ABSTAIN)


def test_m206_a_model_that_says_it_does_not_know_still_produces_an_answer(builder, prompt):
    """The outcome is never read off the model's prose.

    A model replying *"the context does not contain the answer"* has produced an
    `Answer` with its evidence attached, because the corpus **did** supply
    evidence. What the model made of that evidence is an evaluation question —
    **M2-07**, **M2-08** — and deriving `outcome` from answer text would put a
    quality judgement inside the runtime artifact.
    """
    client = FakeClient(answer="The context does not contain the answer.")

    result = ModelGenerator(client, retrieval_route=ROUTE).generate(prompt)

    assert result.outcome == OUTCOME_ANSWER
    assert result.statements


def test_m206_diagnostics_carry_the_three_required_keys(generator, prompt):
    """§8.4 — `query`, `retrieval_route`, `stub`, in that order, and no fourth.

    §24.5 states that *"no new required key is added here"*, and §24.4
    authorizes no new `GenerationResult` field, so `diagnostics` is exactly the
    three. No timestamp, no duration, no token count and no latency: §15 defers
    `generation_time_ms` and RO-13 leaves that deferral standing — latency is
    sprint evidence and does not enter the artifact.
    """
    result = generator.generate(prompt)

    assert list(result.diagnostics) == ["query", "retrieval_route", "stub"]
    assert result.diagnostics["query"] == prompt.query
    assert result.diagnostics["retrieval_route"] == ROUTE


def test_m206_the_stub_marker_is_false_and_the_milestone_1a_one_is_untouched():
    """§24.5 — `stub` is `False` *"because generation is no longer a stub"*.

    And the Milestone 1A marker is **not** restated: §24.5 records that *"no
    historical `stub = True` statement is restated as `False`"*, and
    `sample_rag/generator.py`'s marker still describes the component it belongs
    to. Both are asserted together, because the point is the pair.
    """
    import sample_rag.generator as milestone_1a

    assert GENERATION_STUB is False
    assert milestone_1a.GENERATION_STUB is True


def test_m206_the_result_serializes_through_the_existing_contract_form(generator, prompt):
    """§13.2 is unchanged by v2.0.0 (§24.3) — one `serialize`, one form.

    The artifact this module produces is the artifact `sample_rag/generator.py`
    already serializes; nothing here defines a second representation.
    """
    document = serialize(generator.generate(prompt))

    assert document.endswith("\n")
    assert list(json.loads(document)) == [
        "answer_text",
        "outcome",
        "statements",
        "diagnostics",
    ]


# ---------------------------------------------------------------------------
# 6. Request construction — §24.3, deterministic and minimal
# ---------------------------------------------------------------------------


def test_m206_the_request_carries_the_context_and_the_query(generator, prompt, client):
    """The two values the model needs, and the shape they arrive in.

    A system message stating the grounding instruction and a user message
    carrying the assembled context and the question. Two messages, in that
    order.
    """
    generator.generate(prompt)
    messages = client.calls[0]

    assert [message["role"] for message in messages] == ["system", "user"]
    assert messages[0]["content"] == SYSTEM_INSTRUCTION
    assert prompt.context in messages[1]["content"]
    assert prompt.query in messages[1]["content"]


def test_m206_no_provenance_field_is_transmitted_to_the_provider(generator, prompt, client):
    """§24.4's provenance exists for the repository, not for the model.

    No chunk id, no document id and no character offset leaves the repository.
    The model is not shown the identities its answer will be filed against —
    which is also why it cannot influence them.
    """
    generator.generate(prompt)
    transmitted = json.dumps(client.calls[0])

    for record in prompt.provenance:
        assert record.chunk_id not in transmitted
        assert record.document_id not in transmitted
        assert str(record.character_start) not in transmitted.replace(prompt.context, "")


def test_m206_no_repository_internal_detail_is_transmitted(generator, prompt, client):
    """No path, digest, dataset name, credential or module identity is sent.

    A request that carried repository internals would be leaking the system's
    shape to an external party for no contractual reason — and §18's barred
    authorities exist precisely so that generation cannot come to depend on
    them.
    """
    generator.generate(prompt)
    transmitted = json.dumps(client.calls[0]).lower()

    for barred in (
        "sample_rag",
        "chunks.json",
        "knowledge_manifest",
        "resume_facts",
        "resume_qa_pairs",
        "evidence_trace",
        "datasets/",
        "api_key",
        "authorization",
        "bearer",
        "/home/",
    ):
        assert barred not in transmitted


def test_m206_the_request_body_carries_exactly_the_documented_fields():
    """`build_request_body` — five fields, each a documented request parameter.

    No `tools`, no `tool_choice`, no `response_format`, no `stop`, no
    `logprobs`, no `user_id`, no `max_tokens`. Tool calling and model routing
    are barred by §24.3's G-14 transition, and each remaining field would be a
    request-shaping decision no authority asked for.
    """
    body = build_request_body([{"role": "user", "content": "hello"}])

    assert list(body) == ["model", "messages", "stream", "temperature", "thinking"]
    assert body["model"] == DEFAULT_MODEL
    assert body["stream"] is False


def test_m206_request_construction_is_deterministic():
    """§24.3 — *"request construction"* and *"provider request shape"* stay deterministic.

    A total function of its arguments: same messages, byte-identical request
    document. This is the structural half of G-9 and it is unaffected by the
    fact that the response is not reproducible.
    """
    messages = [{"role": "system", "content": "s"}, {"role": "user", "content": "u"}]

    first = json.dumps(build_request_body(messages))
    second = json.dumps(build_request_body(messages))

    assert first == second


def test_m206_the_request_body_never_carries_the_credential(monkeypatch):
    """The key is a transport header, and is not part of the document.

    So `build_request_body` can be exercised, printed and compared in a
    specification with no secret reachable from it — which is why the credential
    is applied in `complete` rather than here.
    """
    monkeypatch.setenv(API_KEY_VARIABLE, "sk-specification-only-not-a-real-key")

    body = json.dumps(build_request_body([{"role": "user", "content": "hi"}]))

    assert "sk-specification-only-not-a-real-key" not in body
    assert "authorization" not in body.lower()


# ---------------------------------------------------------------------------
# 7. Response parsing and schema mapping — §24.3
# ---------------------------------------------------------------------------


def test_m206_a_documented_response_parses_to_its_content():
    """The documented path, and only it: `choices[0].message.content`."""
    assert parse_completion(completion("an answer")) == "an answer"


@pytest.mark.parametrize(
    "payload",
    [
        pytest.param("not a document", id="not-an-object"),
        pytest.param({}, id="no-choices"),
        pytest.param({"choices": []}, id="empty-choices"),
        pytest.param({"choices": [{}]}, id="no-message"),
        pytest.param({"choices": [{"message": {}}]}, id="no-content"),
        pytest.param({"choices": [{"message": {"content": None}}]}, id="null-content"),
        pytest.param({"choices": [{"message": {"content": ""}}]}, id="empty-content"),
        pytest.param({"choices": [{"message": {"content": 7}}]}, id="non-string-content"),
    ],
)
def test_m206_a_malformed_response_never_becomes_an_answer(payload):
    """A malformed provider response raises; it does not degrade into a result.

    §24.3 keeps *"response parsing"* and *"schema mapping"* deterministic, and
    G-3 requires `answer_text` to be non-empty on every path. A response that
    quietly became `""` would satisfy the type and violate the guarantee, so
    every departure from the documented shape — including a present-but-empty
    `content` — is an error.
    """
    with pytest.raises(ProviderResponseError):
        parse_completion(payload)


def test_m206_undocumented_response_fields_are_ignored():
    """`reasoning_content`, `usage`, `logprobs` and the rest are not read.

    The Generation Contract has no field for any of them (§24.4 authorizes no
    new `GenerationResult` field), so reading one would produce a value with
    nowhere to go.
    """
    payload = completion("the answer")
    payload["choices"][0]["message"]["reasoning_content"] = "a trace"

    assert parse_completion(payload) == "the answer"


# ---------------------------------------------------------------------------
# 8. Failure semantics — deterministic classification, no silent success
# ---------------------------------------------------------------------------


def test_m206_a_missing_credential_is_a_configuration_failure(monkeypatch):
    """Distinct from a provider failure, and raised before any network access.

    A missing credential is fixed by the operator; a 503 is fixed by waiting.
    Collapsing the two would make an unconfigured repository look like an
    unavailable provider.
    """
    monkeypatch.delenv(API_KEY_VARIABLE, raising=False)

    with pytest.raises(ProviderConfigurationError):
        DeepSeekClient().complete([{"role": "user", "content": "hi"}])


def test_m206_a_blank_credential_is_also_a_configuration_failure(monkeypatch):
    """An empty variable is unset, not authenticated.

    Sending an empty bearer token would spend a request to be told 401, and
    would report a repository configuration error as a provider one.
    """
    monkeypatch.setenv(API_KEY_VARIABLE, "")

    with pytest.raises(ProviderConfigurationError):
        DeepSeekClient().complete([{"role": "user", "content": "hi"}])


@pytest.mark.parametrize("status", sorted(STATUS_REASONS))
def test_m206_every_documented_status_is_a_provider_failure(monkeypatch, status):
    """The provider's documented status codes, classified from a fixed table.

    §24.3 requires error classification to remain deterministic, so the mapping
    is a lookup rather than a heuristic over provider prose — a classifier that
    parsed the response body would vary with the provider's wording.
    """
    monkeypatch.setenv(API_KEY_VARIABLE, "sk-specification-only")

    def failing(*arguments, **keywords):
        raise urllib.error.HTTPError(
            "https://example.invalid", status, "reason", {}, None
        )

    monkeypatch.setattr(urllib.request, "urlopen", failing)

    with pytest.raises(ProviderRequestError) as raised:
        DeepSeekClient().complete([{"role": "user", "content": "hi"}])

    assert str(status) in str(raised.value)
    assert STATUS_REASONS[status] in str(raised.value)


def test_m206_an_undocumented_status_is_still_a_provider_failure(monkeypatch):
    """A status the table cannot name is classified, not crashed on.

    It is simply not one this repository has a documented reason for, which the
    message says rather than implies.
    """
    monkeypatch.setenv(API_KEY_VARIABLE, "sk-specification-only")

    def failing(*arguments, **keywords):
        raise urllib.error.HTTPError("https://example.invalid", 418, "reason", {}, None)

    monkeypatch.setattr(urllib.request, "urlopen", failing)

    with pytest.raises(ProviderRequestError):
        DeepSeekClient().complete([{"role": "user", "content": "hi"}])


def test_m206_a_timeout_is_a_provider_failure(monkeypatch):
    """A provider that never answers fails as a provider, not as a hang.

    The bounded wait is what makes that true; without it a caller would block
    indefinitely and the failure would have no classification at all.
    """
    monkeypatch.setenv(API_KEY_VARIABLE, "sk-specification-only")

    def timing_out(*arguments, **keywords):
        raise TimeoutError("timed out")

    monkeypatch.setattr(urllib.request, "urlopen", timing_out)

    with pytest.raises(ProviderRequestError):
        DeepSeekClient().complete([{"role": "user", "content": "hi"}])


def test_m206_a_transport_failure_is_a_provider_failure(monkeypatch):
    """DNS, connection refusal and TLS failures classify with the rest."""
    monkeypatch.setenv(API_KEY_VARIABLE, "sk-specification-only")

    def unreachable(*arguments, **keywords):
        raise urllib.error.URLError("name resolution failed")

    monkeypatch.setattr(urllib.request, "urlopen", unreachable)

    with pytest.raises(ProviderRequestError):
        DeepSeekClient().complete([{"role": "user", "content": "hi"}])


def test_m206_a_non_json_response_body_is_a_response_failure(monkeypatch):
    """A body that is not JSON is malformed, not unreachable.

    The distinction matters: one says the provider answered with something this
    repository cannot read, the other says it did not answer.
    """
    monkeypatch.setenv(API_KEY_VARIABLE, "sk-specification-only")

    class NotJson(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *arguments):
            return False

    monkeypatch.setattr(
        urllib.request, "urlopen", lambda *a, **k: NotJson(b"<html>gateway</html>")
    )

    with pytest.raises(ProviderResponseError):
        DeepSeekClient().complete([{"role": "user", "content": "hi"}])


def test_m206_a_provider_failure_never_becomes_a_generation_result(prompt):
    """No provider failure of any kind is representable as a successful artifact.

    The caller receives an exception or an artifact, never a degraded artifact
    standing in for one: there is no fallback answer, no cached result, no
    abstention substitution and no empty-string answer on the failure path.
    """
    for error in (
        ProviderConfigurationError("missing"),
        ProviderRequestError("503"),
        ProviderResponseError("malformed"),
    ):
        with pytest.raises(ProviderError):
            ModelGenerator(FakeClient(error=error), retrieval_route=ROUTE).generate(prompt)


def test_m206_a_successful_transport_round_trip_produces_an_answer(monkeypatch, prompt):
    """The whole path, end to end, with only the socket replaced.

    Credential read, request built, request sent, response parsed, artifact
    constructed. This is the same sequence `scripts/run_generation.py` performs
    against the real service — the transport is the only thing standing in.
    """
    monkeypatch.setenv(API_KEY_VARIABLE, "sk-specification-only")
    sent = {}

    def capture(request, timeout=None):
        sent["url"] = request.full_url
        sent["body"] = json.loads(request.data.decode("utf-8"))
        sent["headers"] = dict(request.header_items())
        return http_response(completion("A synthesized answer."))

    monkeypatch.setattr(urllib.request, "urlopen", capture)

    result = ModelGenerator(DeepSeekClient(), retrieval_route=ROUTE).generate(prompt)

    assert result.outcome == OUTCOME_ANSWER
    assert result.answer_text == "A synthesized answer."
    assert sent["url"].endswith("/chat/completions")
    assert sent["body"]["model"] == DEFAULT_MODEL
    assert len(result.statements) == 3


def test_m206_exactly_one_provider_interaction_is_performed(monkeypatch, prompt):
    """G-14 — *"a permission for one call, not a category of access."*

    One `generate`, one call. No retry, no backoff, no second attempt on
    failure, and no speculative pre-flight: a retry loop would turn one
    sanctioned interaction into an unbounded number of them, and the decision to
    try again belongs to the caller.
    """
    monkeypatch.setenv(API_KEY_VARIABLE, "sk-specification-only")
    calls = []

    def counting(request, timeout=None):
        calls.append(request.full_url)
        return http_response(completion("one answer"))

    monkeypatch.setattr(urllib.request, "urlopen", counting)

    ModelGenerator(DeepSeekClient(), retrieval_route=ROUTE).generate(prompt)

    assert len(calls) == 1


# ---------------------------------------------------------------------------
# 9. Credential containment
# ---------------------------------------------------------------------------


def test_m206_the_credential_is_not_held_on_the_client(monkeypatch):
    """No attribute, `repr`, pickle or traceback frame holding the client has it.

    The key is read from the environment inside `complete` and never bound to
    the instance, so a client escaping into a fixture carries no secret.
    """
    monkeypatch.setenv(API_KEY_VARIABLE, "sk-specification-only-not-a-real-key")
    client = DeepSeekClient()

    assert "sk-specification-only-not-a-real-key" not in repr(vars(client))
    assert "sk-specification-only-not-a-real-key" not in repr(client)


def test_m206_no_exception_message_carries_the_credential(monkeypatch):
    """Every error is built from a fixed vocabulary and non-secret parameters.

    Checked across the configuration, transport and response failure classes
    together, because a single uninstrumented path is all it takes.
    """
    secret = "sk-specification-only-not-a-real-key"
    monkeypatch.setenv(API_KEY_VARIABLE, secret)

    def failing(*arguments, **keywords):
        raise urllib.error.HTTPError("https://example.invalid", 401, "r", {}, None)

    monkeypatch.setattr(urllib.request, "urlopen", failing)

    with pytest.raises(ProviderRequestError) as raised:
        DeepSeekClient().complete([{"role": "user", "content": "hi"}])

    assert secret not in str(raised.value)
    assert secret not in repr(raised.value)
    assert raised.value.__cause__ is None
    assert raised.value.__context__ is None or secret not in repr(raised.value.__context__)


def test_m206_the_credential_variable_is_read_and_never_written():
    """The environment is read; nothing writes to it, and nothing persists it.

    Structural, and stated over the module's **syntax** rather than its text:
    the docstring legitimately uses the words *written*, *logged* and *stored* to
    record what does not happen, so a substring check would make that record a
    failure. What is asserted is that the environment is only ever read, and
    that no filesystem call exists to persist anything through.

    G-14 leaves filesystem I/O *"barred outright"* after the transition.
    """
    import sample_rag.deepseek as module

    tree = ast.parse(inspect.getsource(module))
    called = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    } | {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }

    # The environment is read, and only read.
    assert "get" in called
    assert not any(
        isinstance(node, ast.Subscript)
        and isinstance(node.ctx, ast.Store)
        for node in ast.walk(tree)
    )
    for barred in ("setenv", "putenv", "setdefault", "open", "write", "write_text", "mkdir"):
        assert barred not in called


def test_m206_no_credential_material_appears_in_this_specification_suite():
    """The suite itself carries no secret, and the check is part of the suite.

    Every credential used above is an obvious specification-only literal. This
    states that no plausible real key was ever pasted in — the failure mode a
    reviewer cannot catch by reading, because a real key looks like a fake one.

    Stated over the suite's **string literals** rather than its lines, so that
    the check does not have to exempt itself from its own pattern.
    """
    tree = ast.parse(pathlib.Path(__file__).read_text(encoding="utf-8"))

    literals = [
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    ]

    for literal in literals:
        if literal.startswith("sk-") and len(literal) > len("sk-"):
            assert "specification" in literal, (
                f"suspicious credential literal: {literal[:12]}…"
            )


# ---------------------------------------------------------------------------
# 10. The determinism boundary — §24.3, both halves
# ---------------------------------------------------------------------------


def test_m206_everything_the_repository_computes_is_deterministic(prompt):
    """§24.3 — the structural half, held to field-for-field equality.

    Provenance mapping, evidence derivation, statement construction, ordering,
    diagnostics and outcome selection are all functions of the `Prompt`. Held
    with the provider's contribution fixed, which is the only way to observe the
    repository's half in isolation — and is **not** an assertion that the
    provider would repeat itself.
    """
    first = ModelGenerator(FakeClient(), retrieval_route=ROUTE).generate(prompt)
    second = ModelGenerator(FakeClient(), retrieval_route=ROUTE).generate(prompt)

    assert first == second
    assert serialize(first) == serialize(second)


def test_m206_a_differing_model_answer_leaves_every_structural_field_equal(prompt):
    """§24.3 — the boundary itself, stated as the one property that spans it.

    *"`answer_text` … is **not** required to be byte-identical across
    executions."* The implementation must therefore tolerate a provider that
    answers differently on identical input — and must not let that difference
    reach anything else. Both halves are asserted at once: two runs whose model
    output differs produce artifacts that differ **in `answer_text` alone**,
    with statements, evidence, ordering, outcome and diagnostics all equal.

    This is deliberately **not** the assertion RO-13 forbids. Nothing here
    claims the provider *would* repeat itself or *would* differ; the provider's
    contribution is supplied, and what is specified is the repository's response
    to either case. §24.3: *"no sprint may claim [model-output determinism] from
    repeated calls alone."*

    `ALTM-INDEX-1` — *"contradictory answer across repeated runs on the same
    input"* — was unreachable by construction under v1.0.0 and, as §24.3
    records, **becomes reachable** here. It is a property to observe, not one to
    assert away, and this specification is what makes observing it meaningful:
    a difference in the answer is visibly *only* a difference in the answer.
    """
    first = ModelGenerator(FakeClient(answer="One phrasing."), retrieval_route=ROUTE).generate(
        prompt
    )
    second = ModelGenerator(
        FakeClient(answer="A completely different phrasing."), retrieval_route=ROUTE
    ).generate(prompt)

    assert first.answer_text != second.answer_text
    assert first.outcome == second.outcome
    assert first.statements == second.statements
    assert first.diagnostics == second.diagnostics


def test_m206_the_result_carries_no_value_that_varies_between_runs(generator, prompt):
    """§12, D-14 — no timestamp, duration, random or float reaches the artifact.

    The discipline `docs/MILESTONE_1A.md` build item 1 applied when it removed
    `created_at`, and `sample_rag/retriever.py` applied when it fixed
    `retrieval_time_ms` at 0. §15's deferral of `generation_time_ms` stands
    under RO-13 — **latency is sprint evidence and does not enter the
    artifact** — so a measured duration appearing in `diagnostics` is a
    contract violation, not a diagnostic improvement.
    """
    document = json.loads(serialize(generator.generate(prompt)))

    for barred in ("created_at", "timestamp", "generation_time_ms", "latency", "elapsed"):
        assert barred not in json.dumps(document)
    for value in document["diagnostics"].values():
        assert not isinstance(value, float)


# ---------------------------------------------------------------------------
# 11. The dependency boundary — G-13, G-14, §18
# ---------------------------------------------------------------------------


def test_m206_the_generator_imports_only_the_prompt_the_artifact_and_the_client():
    """G-13 — an allowlist, so an import nobody thought to forbid also fails.

    The permitted runtime inputs are a `Prompt` and the one sanctioned provider
    call. Everything else §18 bars — the Knowledge Manifest, Golden Dataset, QA
    Dataset, Evidence Trace Dataset, Chunk Corpus as a file, and every
    evaluation layer — is unreachable because there is no import to reach it
    through.
    """
    import sample_rag.model_generator as module

    assert imported_roots(module) == {"sample_rag"}
    assert imported_modules(module) == {
        "sample_rag.context_builder",
        "sample_rag.deepseek",
        "sample_rag.generator",
    }


def test_m206_the_generator_performs_no_io_of_its_own():
    """G-14 — filesystem I/O barred outright; network reachable only via the boundary.

    The module that implements the contract holds no network primitive and no
    path primitive at all, so *"the Generator cannot reach the network except
    through the one sanctioned call"* is a structural property of the package
    rather than a promise about a function body.
    """
    import sample_rag.model_generator as module

    assert imported_roots(module) & {
        "urllib",
        "socket",
        "http",
        "requests",
        "httpx",
        "pathlib",
        "os",
        "io",
        "shutil",
        "subprocess",
    } == set()


def test_m206_the_generator_reaches_no_retrieval_component():
    """G-13 — no `Retriever`, BM25, FAISS, `VectorStore`, `VectorRuntime` or fusion.

    §24.2: the v2 Generator *"SHALL NOT reach the `Retriever`, BM25, FAISS, the
    `VectorStore`, the chunk store, the corpus, or `ContextBuilder.resolve()`"*.
    Everything necessary arrives through the `Prompt` or the provider call.

    The `resolve` half is stated over **called names**, not source text: the
    module docstring cites `ContextBuilder.resolve()` by name to record that it
    is not reached, and a substring check would make that citation a failure.
    """
    import sample_rag.model_generator as module

    imported = imported_modules(module)
    for barred in (
        "sample_rag.retriever",
        "sample_rag.fusion",
        "sample_rag.vector_store",
        "sample_rag.vector_runtime",
        "sample_rag.vector_index",
        "sample_rag.indexer",
        "sample_rag.embedding",
        "sample_rag.chunker",
        "sample_rag.knowledge_source",
    ):
        assert barred not in imported

    tree = ast.parse(inspect.getsource(module))
    called = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }

    assert "resolve" not in called
    assert "retrieve" not in called
    assert "assemble" not in called


def test_m206_neither_new_module_imports_from_scripts():
    """`docs/architecture.md` §6 — `sample_rag/` never imports `scripts/`.

    Unchanged by RO-13: §24.3 restates it in those words while carrying §18's
    barred list forward in full.
    """
    import sample_rag.deepseek as provider
    import sample_rag.model_generator as module

    for target in (module, provider):
        assert not any(name.startswith("scripts") for name in imported_modules(target))


def test_m206_the_provider_boundary_is_the_only_networked_module():
    """A-5 / G-14 — the exception did not leak past the boundary that took it.

    Stated over the package by glob, mirroring
    `tests/test_vector_index.py::test_m201b_no_other_pipeline_module_imports_faiss`
    and `tests/test_indexer.py::test_m201_no_other_pipeline_module_imports_the_embedding_library`,
    so a module added later is covered without anyone remembering to add it.
    """
    import sample_rag.deepseek

    package_root = pathlib.Path(sample_rag.deepseek.__file__).parent

    offenders = []
    for path in sorted(package_root.glob("*.py")):
        if path.name == "deepseek.py":
            continue

        module = importlib.import_module(f"sample_rag.{path.stem}")
        if imported_roots(module) & {"urllib", "socket", "http", "requests", "httpx"}:
            offenders.append(path.name)

    assert offenders == [], f"network access outside the provider boundary: {offenders}"


def test_m206_the_prompt_is_not_mutated_by_generation(generator, prompt):
    """§24.3 — the observational-purity property v1.0.0 held, carried forward.

    *"No mutation of the consumed `Prompt` is permitted."* Compared against a
    snapshot taken before the call, so a generator that normalized, annotated or
    reordered the artifact it was given fails here.
    """
    before = (
        prompt.query,
        prompt.context,
        list(prompt.chunk_ids),
        list(prompt.provenance),
    )

    generator.generate(prompt)

    assert (prompt.query, prompt.context, list(prompt.chunk_ids), list(prompt.provenance)) == before


# ---------------------------------------------------------------------------
# 12. Runtime reachability — U-3, without executing the provider
# ---------------------------------------------------------------------------


def test_m206_the_runtime_path_composes_the_contract_pipeline():
    """§24.2's chain exists as an executable composition, and is reachable.

    `scripts/run_generation.py` is the **U-3** answer: retrieval → RRF →
    `ContextBuilder` → `Prompt` → `ModelGenerator` → provider →
    `GenerationResult`. Asserted structurally, so the claim is checked by the
    suite without the suite ever performing the real call the script exists to
    perform.

    **Every stage is imported from the component that already owns it.** The
    fused ordering comes from `scripts/run_hybrid_retrieval.py`'s own route
    functions, so this path cannot disagree with the retrieval runtime the
    repository already measures — which is what makes the generation it produces
    a generation over the repository's retrieval rather than a second one.
    """
    import scripts.run_generation as runtime

    imported = imported_modules(runtime)

    assert {
        "sample_rag.context_builder",
        "sample_rag.deepseek",
        "sample_rag.model_generator",
        "sample_rag.retriever",
        "sample_rag.vector_runtime",
        "scripts.run_hybrid_retrieval",
        "scripts.run_retrieval",
    } <= imported


def test_m206_the_runtime_path_introduced_no_orchestration_mechanism():
    """RO-13 authorized none, and none was created.

    No orchestration layer, runtime adapter, pipeline coordinator, engine,
    router, registry or agent runtime — asserted over declared names, because
    the module docstring names each in order to record its absence.

    `scripts/run_generation.py` is a fifth instance of the existing
    `scripts/run_*.py` pattern (`docs/architecture.md` §6: *"Operational
    scripts … not pipeline logic"*), and **declares no class at all**.
    """
    import scripts.run_generation as runtime

    tree = ast.parse(inspect.getsource(runtime))
    names = {
        node.name.lower()
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.ClassDef))
    }

    assert not any(isinstance(node, ast.ClassDef) for node in ast.walk(tree))
    for barred in (
        "orchestrat",
        "pipeline",
        "coordinator",
        "adapter",
        "engine",
        "router",
        "registry",
        "agent",
        "workflow",
    ):
        assert not any(barred in name for name in names)


def test_m206_reachable_stages_was_not_widened():
    """`evaluation/altm_rules.py` is unchanged — U-3's other half stays closed.

    §24.6: v2.0.0 *"does not resolve U-3: `REACHABLE_STAGES` is not widened"*,
    and `docs/GENERATION_CONTRACT.md` §23 Q-3's reasoning — that widening is *"a
    deliberate scope decision, not a side effect of implementing a component"* —
    is unchanged. **M2-06 made the runtime path executable; it did not decide
    that the Assemble and Infer stages are now diagnosable**, which is a
    separate decision belonging to the Diagnosis layer's owner.
    """
    from evaluation.altm_rules import REACHABLE_STAGES

    assert REACHABLE_STAGES == ("Knowledge", "Index", "Retrieve")


def test_m206_the_milestone_1a_cli_is_unchanged():
    """`scripts/cli.py` keeps its Milestone 1A chain and its frozen determinism.

    `docs/P3.7.6_…` §3.2 freezes its 27 specifications and §4 freezes its
    byte-identical answer and abstain reproducibility as Milestone 1A acceptance
    evidence. Rewiring it to a model would put a live provider call inside the
    deterministic suite and retire that evidence — neither authorized by RO-13.

    So the CLI still imports the Milestone 1A `Generator` and reaches neither
    the Context Builder nor the provider. **`docs/M2.06_Generation_Report.md`
    records the disposition of the two coexisting generators as a finding for
    M2-14**, rather than resolving it here.
    """
    import scripts.cli as cli

    imported = imported_modules(cli)

    assert "sample_rag.generator" in imported
    assert "sample_rag.model_generator" not in imported
    assert "sample_rag.context_builder" not in imported
    assert "sample_rag.deepseek" not in imported


# ---------------------------------------------------------------------------
# 13. Sprint scope — what M2-06 did not activate
# ---------------------------------------------------------------------------


def test_m206_no_evaluation_framework_is_activated():
    """Ragas (**M2-07**), DeepEval (**M2-08**), Promptfoo (**M3-01**) are untouched.

    §24.6: v2.0.0 *"activates no evaluation tooling"*, and authorizes no
    Faithfulness, Groundedness, Hallucination Rate, Answer Relevancy, Context
    Precision or Context Recall claim. **M2-06 creates the generation evidence
    those sprints will consume; it does not consume it itself**, and a
    successful provider call is not evidence of answer quality.

    The metric half is stated over **declared names**, the convention
    `tests/test_lexical_bm25.py` set: both module docstrings legitimately name
    Faithfulness and Groundedness in order to disclaim them — which is exactly
    what RO-13 asks a sprint to do — and a substring check over source would
    turn that disclaimer into a failure while missing a metric computed under
    any other name.
    """
    import sample_rag.deepseek as provider
    import sample_rag.model_generator as module

    for target in (module, provider):
        roots = imported_roots(target)
        assert roots & {"ragas", "deepeval", "promptfoo", "langchain", "llama_index"} == set()

        tree = ast.parse(inspect.getsource(target))
        names = {
            node.name.lower()
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.ClassDef))
        } | {
            node.id.lower()
            for node in ast.walk(tree)
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store)
        }

        for barred in (
            "faithful",
            "grounded",
            "hallucinat",
            "relevanc",
            "precision",
            "recall",
            "score",
            "metric",
            "judge",
        ):
            assert not any(barred in name for name in names), (
                f"{target.__name__} declares a {barred!r} name"
            )


def test_m206_no_dependency_was_added(repository_root):
    """The third A-5 exception is **authorized and not taken**.

    RO-13 authorizes one LLM/provider integration dependency for M2-06.
    `requirements.txt` is unchanged: `urllib.request` and `json` are the whole
    of an HTTP POST carrying a JSON document, and `docs/architecture.md` §10's
    *"minimal dependencies"* decision is binding. The exception remains
    available to a later sprint; it is simply not needed yet.

    Mirrors `tests/test_lexical_bm25.py::test_m203_no_bm25_dependency_was_added`.
    """
    requirements = (repository_root / "requirements.txt").read_text(encoding="utf-8").lower()

    for barred in ("openai", "anthropic", "deepseek", "httpx", "requests", "litellm", "aiohttp"):
        assert barred not in requirements


def test_m206_no_context_budget_or_compression_mechanism_exists():
    """§24.6 — no context-window policy, token budget, compression or memory.

    Nor reranking (**M2-05**), retrieval or prompt optimization (**M2-15**),
    chunking change (**M2-17**), agent runtime, tool calling or model routing.
    Stated over declared names, the convention `tests/test_lexical_bm25.py` set:
    the module docstrings legitimately *mention* each to record what they do not
    do, and a substring check over source would make that prose a failure.
    """
    import sample_rag.deepseek as provider
    import sample_rag.model_generator as module

    for target in (module, provider):
        tree = ast.parse(inspect.getsource(target))
        names = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                names.add(node.name.lower())
            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                names.add(node.id.lower())

        for barred in (
            "budget",
            "truncat",
            "compress",
            "rerank",
            "rewrite",
            "expand",
            "memory",
            "agent",
            "route_model",
            "fallback",
            "retry",
        ):
            assert not any(barred in name for name in names), (
                f"{target.__name__} declares a {barred!r} name"
            )


def test_m206_the_milestone_1a_generator_is_untouched():
    """`sample_rag/generator.py` still conforms to v1.0.0, byte for byte.

    §24.1: v1.0.0 *"is not withdrawn, corrected, or falsified"* and remains
    authoritative for the historical Milestone 1A quotation Generator.
    `docs/P3.7.6_…` §3.2 freezes that component's 48 specifications and
    `scripts/cli.py`'s 27, and P3.7.6 requires subsequent milestones to
    *"**extend** this baseline"* rather than *"**redefine**"* it.

    **Which of the two components is the `docs/architecture.md` §5 `Generator`
    row is M2-14**, which RO-13 §24.2 authorized and deliberately did not
    discharge. This specification records the coexistence; it does not resolve
    it.
    """
    import sample_rag.generator as milestone_1a

    assert list(inspect.signature(milestone_1a.Generator.generate).parameters) == [
        "self",
        "query",
        "retrieval",
    ]
    assert imported_modules(milestone_1a) == {"json", "dataclasses", "sample_rag.retriever"}
