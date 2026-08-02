"""Specification Family 10 — Deterministic Generation.

Sprint P3.5.2: executable specifications for `sample_rag/generator.py`, the
implementation of `docs/GENERATION_CONTRACT.md` v1.0.0 (Approved, Frozen).

Every specification below cites the contract clause it enforces. Nothing here
specifies behaviour the contract does not require, and nothing here relaxes a
guarantee: the file is organized by the contract's own structure — the fourteen
SHALL guarantees of §16, the thirteen invariants of §17, the ordering semantics
of §11, the determinism requirement of §12, the serialization form of §13.2, and
the boundary of §18.

Two kinds of specification, deliberately separated
---------------------------------------------------
    synthetic  constructed `RetrievalResult` values, so a specification can
               present the Generator with inputs the committed corpus does not
               produce — an empty retrieval above all, which is the entire
               Abstain path
    corpus     the committed Chunk Corpus and the repository's own questions,
               generated end to end

The synthetic cases carry the contract algebra; the corpus cases carry the
guarantees that quantify over committed repository state (G-6, G-11).

No answer text is frozen
------------------------
No specification asserts that a particular question produces a particular
answer. Contract §19.2 requires this: the Milestone 1A retriever is a documented
lexical stub whose behaviour Milestone 2 is expected to change, and freezing
today's answers would convert a retrieval improvement into a generation test
failure — the same reasoning `tests/test_retrieval_evaluation.py` already
records for retrieval classifications. What is asserted is *shape, evidence,
ordering, determinism and traceability*, all of which must hold for any
retrieval behaviour.

Validation may read what the runtime may not
---------------------------------------------
Contract §19.4 is explicit that validators, unlike the Generator, may consult
repository authorities. The corpus specifications below read the Chunk Corpus,
the Knowledge Manifest and the Document corpus to check G-6, G-11 and T-2. That
asymmetry is the point of the boundary: the runtime stays capable of answering an
arbitrary query, and the tests still get to prove it answered from committed
evidence. `test_generator_reaches_no_repository_authority` is the executable form
of that boundary.
"""

import ast
import json

from dataclasses import FrozenInstanceError, fields
from pathlib import Path

import pytest

from sample_rag.generator import (
    ABSTENTION_TEXT,
    GENERATION_STUB,
    OUTCOME_ABSTAIN,
    OUTCOME_ANSWER,
    STATEMENT_SEPARATOR,
    GeneratedStatement,
    GenerationResult,
    Generator,
    SupportingEvidence,
    serialize,
)
from sample_rag.retriever import RetrievalResult, Retriever

from scripts.run_retrieval import load_questions

# The public surface `docs/GENERATION_CONTRACT.md` approves, and the clause that
# approves each name. Work Package 6.5 audits the module against exactly this.
APPROVED_PUBLIC_SURFACE = {
    "OUTCOME_ANSWER": "§9.1 outcome domain",
    "OUTCOME_ABSTAIN": "§9.1 outcome domain",
    "ABSTENTION_TEXT": "§8.1 / §9.3 fixed abstention text",
    "GENERATION_STUB": "§8.4 required diagnostics key `stub`",
    "STATEMENT_SEPARATOR": "§20.2 delegated decision 4",
    "SupportingEvidence": "§7 / §8.3",
    "GeneratedStatement": "§7 / §8.2",
    "GenerationResult": "§7 / §8.1 / §17",
    "serialize": "§13.2 serialized form",
    "Generator": "§6.2 / §17 approved interface",
}

CONTRACT_FIELDS = {
    GenerationResult: ("answer_text", "outcome", "statements", "diagnostics"),
    GeneratedStatement: ("text", "supporting_evidence"),
    SupportingEvidence: (
        "chunk_id",
        "document_id",
        "character_start",
        "character_end",
        "text",
    ),
}

REQUIRED_DIAGNOSTICS = ("query", "retrieval_route", "stub")


def chunk(chunk_id, document_id="doc-a", text="a synthetic span", start=0):
    """One chunk mapping, shaped exactly as the committed Chunk Corpus stores them.

    Offsets satisfy `docs/CHUNK_CONTRACT.md` §17 invariants 1 and 2, so a
    specification exercising the Generator is never also exercising a malformed
    corpus.
    """
    return {
        "id": chunk_id,
        "document_id": document_id,
        "text": text,
        "chunk_index": start,
        "character_start": start,
        "character_end": start + len(text),
    }


def retrieval(*chunks, route="LEXICAL"):
    """A `RetrievalResult` carrying `chunks`, in the order given.

    Constructed rather than retrieved, so a specification can present an
    ordering, an empty result, or a route the committed corpus does not produce.
    `score` and `diagnostics` are `RetrievalResult`'s own contract fields and are
    not read by the Generator; they carry deterministic placeholders here for the
    same reason `RetrievalResult` requires them to (Architectural AC2).
    """
    return RetrievalResult(
        chunks=list(chunks),
        retrieval_route=route,
        score=0.0,
        diagnostics={"query": "a synthetic query", "stub": True},
    )


@pytest.fixture
def generator():
    """The Generator under specification. Stateless, so one instance serves any call."""
    return Generator()


@pytest.fixture
def answered(generator):
    """A committed-shape Answer result over three synthetic chunks."""
    return generator.generate(
        "a synthetic query",
        retrieval(
            chunk("c1", text="first span", start=0),
            chunk("c2", text="second span", start=40),
            chunk("c3", document_id="doc-b", text="third span", start=10),
        ),
    )


@pytest.fixture
def abstained(generator):
    """The Abstain result: retrieval returned nothing."""
    return generator.generate("a synthetic query", retrieval())


# ---------------------------------------------------------------------------
# G-1 / §17 invariants — artifact shape, required and prohibited fields
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("artifact", list(CONTRACT_FIELDS))
def test_g1_each_artifact_carries_exactly_the_contract_fields(artifact):
    """G-1, §7 — exactly the contract's fields, in the contract's order.

    Both directions: nothing missing and nothing added. An artifact that grew an
    additional field would satisfy an additive-only check while carrying a
    schema no repository authority ratifies — and §13.2 makes declaration order
    the serialized key order, so order is contract content, not style.
    """
    assert tuple(field.name for field in fields(artifact)) == CONTRACT_FIELDS[artifact]


def test_g1_no_field_is_none_on_the_answer_path(answered):
    """G-1 — every field carries a value; none is `None`."""
    assert answered.answer_text is not None
    assert answered.outcome is not None
    assert answered.statements is not None
    assert answered.diagnostics is not None


def test_g1_no_field_is_none_on_the_abstain_path(abstained):
    """G-1 — the Abstain path populates every field too.

    The path where a `None` is most tempting: there is no answer to give and no
    statement to carry. §8.1 requires meaningful values on *every* path, which is
    `RetrievalResult`'s own discipline (Architectural AC2) applied here.
    """
    assert abstained.answer_text is not None
    assert abstained.outcome is not None
    assert abstained.statements == []
    assert abstained.diagnostics is not None


def test_g1_field_types_match_the_contract(answered):
    """G-1, §8 — each field at its declared type, at every level."""
    assert isinstance(answered.answer_text, str)
    assert isinstance(answered.outcome, str)
    assert isinstance(answered.statements, list)
    assert isinstance(answered.diagnostics, dict)

    for statement in answered.statements:
        assert isinstance(statement, GeneratedStatement)
        assert isinstance(statement.text, str)
        assert isinstance(statement.supporting_evidence, list)

        for evidence in statement.supporting_evidence:
            assert isinstance(evidence, SupportingEvidence)
            assert isinstance(evidence.chunk_id, str)
            assert isinstance(evidence.document_id, str)
            assert isinstance(evidence.character_start, int)
            assert isinstance(evidence.character_end, int)
            assert isinstance(evidence.text, str)


@pytest.mark.parametrize("artifact", list(CONTRACT_FIELDS))
def test_the_artifacts_are_frozen(artifact, answered):
    """§13.1 — frozen dataclasses, mirroring `RetrievalResult`.

    The artifact is a record of what happened; no consumer has a reason to
    mutate it, and a mutable record would make two holders of the same result
    able to disagree about what was generated.
    """
    instance = {
        GenerationResult: answered,
        GeneratedStatement: answered.statements[0],
        SupportingEvidence: answered.statements[0].supporting_evidence[0],
    }[artifact]

    with pytest.raises(FrozenInstanceError):
        instance.text = "mutated"


# ---------------------------------------------------------------------------
# G-2, G-3, G-8 — outcome domain, answer text, abstention exclusivity
# ---------------------------------------------------------------------------


def test_g2_outcome_is_in_the_milestone_1a_domain(answered, abstained):
    """G-2, §9.1 — `Answer` or `Abstain`, and nothing else.

    `Clarify` is defined by `docs/roadmap.md` §2.4 and is outside Milestone 1A
    (§9.1); it is never emitted, and no third value exists to emit.
    """
    assert answered.outcome == OUTCOME_ANSWER
    assert abstained.outcome == OUTCOME_ABSTAIN
    assert {answered.outcome, abstained.outcome} == {"Answer", "Abstain"}


def test_g3_answer_text_is_non_empty_on_both_paths(answered, abstained):
    """G-3 — a non-empty string on every path, including Abstain."""
    assert answered.answer_text.strip()
    assert abstained.answer_text.strip()


def test_g8_empty_retrieval_produces_abstain_with_no_statements(abstained):
    """G-8, §9.3 — no retrieved evidence ⇒ Abstain, and no statements.

    The abstention predicate delegated by §20.2 and implemented as "retrieval
    returned no chunk". This is also the ALTM-INFER-2 failure mode
    (*"false confidence on an unanswerable question"*) made structurally
    unreachable: with nothing to quote, the Generator has no way to express
    confidence at all.
    """
    assert abstained.outcome == OUTCOME_ABSTAIN
    assert abstained.statements == []
    assert abstained.answer_text == ABSTENTION_TEXT


def test_g8_retrieved_evidence_produces_answer_with_statements(answered):
    """G-8 — the other direction of the biconditional.

    Asserting only the Abstain direction would leave a Generator that abstained
    on everything fully conforming.
    """
    assert answered.outcome == OUTCOME_ANSWER
    assert answered.statements != []


def test_g8_is_a_biconditional_across_every_retrieval_size(generator):
    """G-8 — `statements == []` **iff** `outcome == "Abstain"`, at every size.

    Quantified over 0, 1 and several chunks rather than asserted at one size,
    because the biconditional is what the contract states and a single example
    of each side does not establish it holds generally.
    """
    for count in range(4):
        chunks = [chunk(f"c{index}", start=index * 20) for index in range(count)]
        result = generator.generate("a synthetic query", retrieval(*chunks))

        assert (result.statements == []) == (result.outcome == OUTCOME_ABSTAIN)


def test_the_abstention_text_makes_no_claim_about_the_corpus():
    """§9.3 — the fixed abstention text reports retrieval, not repository knowledge.

    §9.3 requires a text that *"asserts nothing about the corpus"*. The
    distinction is load-bearing rather than stylistic: a text reading "the corpus
    does not contain this" would be an unevidenced claim about repository
    knowledge — precisely the false confidence `ALTM-INFER-2` describes, arriving
    through the one path that carries no evidence to check it against.
    """
    assert "retrieved" in ABSTENTION_TEXT
    assert ABSTENTION_TEXT.strip() == ABSTENTION_TEXT
    assert ABSTENTION_TEXT


# ---------------------------------------------------------------------------
# G-4, G-5, G-7 — the evidence chain
# ---------------------------------------------------------------------------


def test_g4_every_statement_carries_at_least_one_supporting_evidence(answered):
    """G-4, §8.2 — no statement without evidence.

    Sprint guarantee 1 in the contract's own terms (§7.1). The empty list is
    described by §8.2 as *"not a representable state"*, and it is not one here:
    a statement is only ever constructed from a span.
    """
    assert answered.statements

    for statement in answered.statements:
        assert statement.supporting_evidence


def test_g5_every_evidence_resolves_to_a_consumed_retrieved_chunk(generator):
    """G-5 — `chunk_id` is a chunk retrieval returned, and `document_id` is its document.

    Sprint guarantee 2. Both halves are checked against the consumed
    `RetrievalResult` rather than against the corpus, because that is what G-5
    states — corpus membership is G-6's separate claim, and checking only the
    corpus would pass a Generator that cited a real chunk retrieval never
    returned.
    """
    chunks = [
        chunk("c1", document_id="doc-a", text="first", start=0),
        chunk("c2", document_id="doc-b", text="second", start=30),
    ]
    documents = {entry["id"]: entry["document_id"] for entry in chunks}

    result = generator.generate("a synthetic query", retrieval(*chunks))

    for statement in result.statements:
        for evidence in statement.supporting_evidence:
            assert evidence.chunk_id in documents
            assert evidence.document_id == documents[evidence.chunk_id]


def test_g7_every_statement_is_a_verbatim_quotation_of_its_evidence(answered):
    """G-7 — statement text is derivable from its spans by quotation alone.

    Sprint guarantee 4, "supported by construction". The implementation takes the
    narrowest option G-7 permits — verbatim quotation with no template — so
    support needs no argument beyond identity: the statement *is* its evidence.

    This is the specification that would fail if a future implementation
    introduced connective text, summarization, or any word not present in the
    corpus.
    """
    for statement in answered.statements:
        quoted = STATEMENT_SEPARATOR.join(
            evidence.text for evidence in statement.supporting_evidence
        )

        assert statement.text == quoted


def test_answer_text_contains_no_content_absent_from_its_statements(answered):
    """§8.1 — the assembled answer introduces nothing its statements do not carry.

    Two claims, deliberately both: every statement text appears in the assembled
    answer, and the assembly is *exactly* the statements joined by the
    separator — so nothing was reordered, truncated, or interleaved with
    connective text.

    The exact-equality half is the delegated decision 4 rule of §20.2 stated
    executably; the containment half holds for any conforming assembly and is
    what would survive a future change of separator.
    """
    for statement in answered.statements:
        assert statement.text in answered.answer_text

    assert answered.answer_text == STATEMENT_SEPARATOR.join(
        statement.text for statement in answered.statements
    )


# ---------------------------------------------------------------------------
# G-10 / §11 — ordering semantics
# ---------------------------------------------------------------------------


def test_g10_statements_follow_retrieval_rank(generator):
    """G-10, §11.1 — statement order is the order retrieval ranked the chunks.

    Retrieval rank is the ordering `RetrievalResult` already froze
    (`rank_candidates`: descending score, then ascending committed corpus
    position). The chunks below are presented in an order that is *not* ascending
    by `character_start` or by id, so a Generator that re-sorted by either would
    fail here — which is the point: §11.1 explicitly rejects the ascending
    `chunk_index` ordering `expected_chunk` uses, because a runtime artifact has
    rank available and discarding it would make the answer's reading order
    contradict the ranking that produced it.
    """
    chunks = [
        chunk("c3", text="ranked first", start=90),
        chunk("c1", text="ranked second", start=10),
        chunk("c2", text="ranked third", start=50),
    ]

    result = generator.generate("a synthetic query", retrieval(*chunks))
    emitted = [
        evidence.chunk_id
        for statement in result.statements
        for evidence in statement.supporting_evidence
    ]

    assert emitted == ["c3", "c1", "c2"]


def test_g10_supporting_evidence_is_ordered_and_total(answered):
    """G-10, §11.2 — within a statement, ascending `(document_id, character_start)`.

    Totality is the second half and is asserted separately: §11.2 requires that
    no two spans within one statement share `(chunk_id, character_start,
    character_end)`, which is what makes the order total rather than merely
    defined. Under this implementation each statement carries exactly one span,
    so both hold trivially — stated here rather than glossed, and specified so
    that a future multi-span implementation inherits a check rather than an
    assumption.
    """
    for statement in answered.statements:
        keys = [
            (evidence.document_id, evidence.character_start)
            for evidence in statement.supporting_evidence
        ]
        identities = [
            (evidence.chunk_id, evidence.character_start, evidence.character_end)
            for evidence in statement.supporting_evidence
        ]

        assert keys == sorted(keys)
        assert len(set(identities)) == len(identities)


# ---------------------------------------------------------------------------
# §17 invariants 5, 6, 9, 12 — span geometry and diagnostics
# ---------------------------------------------------------------------------


def test_invariants_5_and_6_hold_for_every_span(answered):
    """§17 invariants 5–6 — spans are non-empty and their text matches their extent."""
    for statement in answered.statements:
        for evidence in statement.supporting_evidence:
            assert evidence.character_end > evidence.character_start
            assert len(evidence.text) == evidence.character_end - evidence.character_start


def test_invariant_9_every_span_lies_within_the_chunk_it_cites(generator):
    """§17 invariant 9 — the span is contained by its chunk's own extent.

    Checked against the consumed chunk rather than assumed: the implementation
    takes whole chunks (delegated decision 2), so containment holds with equality
    on both bounds, and a future narrower-span implementation would be held to
    the same containment by this specification.
    """
    chunks = [chunk("c1", text="a span of text", start=17)]

    result = generator.generate("a synthetic query", retrieval(*chunks))
    source = {entry["id"]: entry for entry in chunks}

    for statement in result.statements:
        for evidence in statement.supporting_evidence:
            parent = source[evidence.chunk_id]

            assert parent["character_start"] <= evidence.character_start
            assert evidence.character_end <= parent["character_end"]


def test_invariant_12_diagnostics_carries_exactly_the_required_keys(answered, abstained):
    """§8.4, §17 invariant 12 — `query`, `retrieval_route`, `stub`, on both paths.

    Exact key equality, not containment: §8.4 names three required keys, and this
    implementation adds none. Asserting containment would permit metadata to
    accumulate silently in the contract's own open mapping.
    """
    for result in (answered, abstained):
        assert tuple(result.diagnostics) == REQUIRED_DIAGNOSTICS
        assert isinstance(result.diagnostics["query"], str)
        assert isinstance(result.diagnostics["retrieval_route"], str)
        assert result.diagnostics["stub"] is GENERATION_STUB is True


def test_diagnostics_retrieval_route_is_copied_never_re_derived(generator):
    """§8.4 — `retrieval_route` is whatever the consumed result reported.

    A synthetic route no retriever emits is used deliberately: a Generator that
    re-derived the route, or hardcoded `"LEXICAL"`, would pass with a
    corpus-shaped fixture and fail here.
    """
    result = generator.generate("a synthetic query", retrieval(chunk("c1"), route="SYNTHETIC"))

    assert result.diagnostics["retrieval_route"] == "SYNTHETIC"


def test_diagnostics_records_the_query_that_produced_the_result(generator):
    """T-4, §8.4 — the artifact records its own request.

    Read from the `query` argument, not from `retrieval.diagnostics["query"]`:
    §6.2 records that the Generator takes the query explicitly so it does not
    depend on another component's open mapping. The synthetic `RetrievalResult`
    carries a *different* query, so an implementation reading the wrong source
    fails here.
    """
    result = generator.generate("the real request", retrieval(chunk("c1")))

    assert result.diagnostics["query"] == "the real request"


def test_no_value_varies_between_runs(generator):
    """§12, §17 invariant 12 — no timestamp, duration, or float anywhere.

    Determinism is achieved by *excluding* the values that would break it
    (§12), so this inspects the artifact for their presence rather than
    inferring their absence from two runs agreeing. `docs/MILESTONE_1A.md`
    removed `created_at` for this reason and `sample_rag/retriever.py` fixed
    `retrieval_time_ms` at 0 for the same one.
    """
    serialized = serialize(generator.generate("a synthetic query", retrieval(chunk("c1"))))
    payload = json.loads(serialized)

    def scan(node):
        if isinstance(node, dict):
            for key, value in node.items():
                assert not any(
                    marker in key.lower()
                    for marker in ("time", "date", "seed", "created", "random", "uuid", "now")
                ), f"key {key!r} suggests a value that varies between runs"
                scan(value)
        elif isinstance(node, list):
            for item in node:
                scan(item)
        else:
            assert not isinstance(node, float), "no floating-point value in Milestone 1A (§15)"

    scan(payload)


# ---------------------------------------------------------------------------
# G-9 / §13.2 — determinism and serialization
# ---------------------------------------------------------------------------


def test_g9_repeated_execution_produces_equal_results(generator):
    """G-9 — identical query and retrieval ⇒ field-for-field equal results.

    Frozen dataclasses compare by value, so equality here is structural over
    every nested field, not identity.
    """
    chunks = [chunk("c1", text="first", start=0), chunk("c2", text="second", start=20)]

    first = generator.generate("a synthetic query", retrieval(*chunks))
    second = generator.generate("a synthetic query", retrieval(*chunks))

    assert first == second


def test_g9_repeated_execution_serializes_byte_identically(generator):
    """G-9, §13.2 — repeated serialization is byte-identical.

    The property that makes two runs comparable — by a test, a CLI diff, or a
    future regression harness — and the one `ALTM-INDEX-1` (*"contradictory
    answer across repeated runs on the same input"*) describes the absence of.
    """
    chunks = [chunk("c1", text="first", start=0), chunk("c2", text="second", start=20)]

    first = serialize(generator.generate("a synthetic query", retrieval(*chunks)))
    second = serialize(generator.generate("a synthetic query", retrieval(*chunks)))

    assert first == second


def test_g9_holds_on_the_abstain_path(generator):
    """G-9 — determinism is not conditional on having produced an answer."""
    first = generator.generate("a synthetic query", retrieval())
    second = generator.generate("a synthetic query", retrieval())

    assert first == second
    assert serialize(first) == serialize(second)


def test_serialization_uses_the_repository_convention(answered):
    """§13.2 — `json.dumps(..., indent=2) + "\\n"`, UTF-8, one trailing newline.

    The convention `write_manifest`, `write_chunks` and `write_evidence_trace`
    already share, verified against the artifact rather than assumed: two-space
    indentation, and exactly one trailing newline.
    """
    serialized = serialize(answered)

    assert serialized.endswith("\n")
    assert not serialized.endswith("\n\n")
    assert '\n  "outcome"' in serialized
    assert json.loads(serialized) is not None


def test_serialization_preserves_contract_field_order_and_does_not_sort_keys(answered):
    """§13.2 — serialized key order is §7's declaration order, at every level.

    Keys are explicitly not sorted: §13.2 states that declaration order *is* the
    contract's order, so sorting would discard information the contract carries.
    `answer_text` before `outcome` is the observable difference — sorted order
    would put `answer_text` first too, so the nested levels are what discriminate:
    `chunk_id` sorts after `character_end`, and the contract puts it first.
    """
    payload = json.loads(serialize(answered))

    assert tuple(payload) == CONTRACT_FIELDS[GenerationResult]
    assert tuple(payload["diagnostics"]) == REQUIRED_DIAGNOSTICS

    for statement in payload["statements"]:
        assert tuple(statement) == CONTRACT_FIELDS[GeneratedStatement]

        for evidence in statement["supporting_evidence"]:
            assert tuple(evidence) == CONTRACT_FIELDS[SupportingEvidence]
            assert tuple(evidence) != tuple(sorted(evidence))


def test_serialization_is_separate_from_the_semantic_model():
    """§13, Work Package 5 — the model is not coupled to its serialized form.

    `serialize` is a module-level function, not a method: §7's semantic model is
    satisfiable by representations this function knows nothing about, and a
    method would make every `GenerationResult` carry one serialization as part of
    its identity.
    """
    assert not hasattr(GenerationResult, "serialize")
    assert not hasattr(GenerationResult, "to_json")
    assert callable(serialize)


# ---------------------------------------------------------------------------
# G-13, G-14 — dependency boundary and observational purity
# ---------------------------------------------------------------------------


def imported_roots(module):
    """Top-level package names a module imports."""
    tree = ast.parse(Path(module.__file__).read_text(encoding="utf-8"))
    roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".")[0])
    return roots


def imported_modules(module):
    """Fully-qualified module names a module imports."""
    tree = ast.parse(Path(module.__file__).read_text(encoding="utf-8"))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def test_g13_generator_reaches_no_repository_authority():
    """G-13, §18 — the runtime dependency boundary, enforced structurally.

    The Generator may consume the query and a `RetrievalResult`. It cannot import
    the Knowledge Manifest, the Golden Dataset, the QA Dataset, the Evidence
    Trace Dataset, the Chunk Corpus as a file, or any evaluation layer — and an
    allowlist fails on any import nobody thought to forbid, which a denylist
    would not.

    §18 records why this is load-bearing rather than bureaucratic: every barred
    artifact exists for the repository's own 22 benchmark questions, so a
    Generator that reads one can answer those 22 and nothing else while appearing
    to work.
    """
    import sample_rag.generator as module

    assert imported_roots(module) <= {"json", "dataclasses", "sample_rag"}
    assert imported_modules(module) <= {"json", "dataclasses", "sample_rag.retriever"}


def test_g13_generator_does_not_import_from_scripts():
    """`docs/architecture.md` §6 — `sample_rag/` never imports `scripts/`.

    The direction the architecture bars, and the reason §20.4 duplicates the
    outcome literals rather than importing them.
    """
    import sample_rag.generator as module

    assert not any(name.startswith("scripts") for name in imported_modules(module))


def test_g14_generation_does_not_mutate_the_retrieval_result(generator):
    """G-14 — the consumed `RetrievalResult` is unchanged after generation.

    Observational purity, checked structurally rather than promised: the result
    and every chunk mapping inside it are compared against copies taken before
    the call. A Generator that normalized, sorted, or annotated the chunks it was
    given would fail here.
    """
    chunks = [chunk("c1", text="first", start=0), chunk("c2", text="second", start=20)]
    consumed = retrieval(*chunks)
    before = json.dumps(
        {
            "chunks": consumed.chunks,
            "retrieval_route": consumed.retrieval_route,
            "score": consumed.score,
            "diagnostics": consumed.diagnostics,
        },
        indent=2,
    )

    generator.generate("a synthetic query", consumed)

    after = json.dumps(
        {
            "chunks": consumed.chunks,
            "retrieval_route": consumed.retrieval_route,
            "score": consumed.score,
            "diagnostics": consumed.diagnostics,
        },
        indent=2,
    )

    assert before == after


def test_g14_generation_performs_no_filesystem_io():
    """G-14 — no path is opened, and none can be.

    Enforced at the import level rather than by intercepting calls: the module
    imports neither `pathlib`, `os`, nor `open`-bearing helpers, and its only
    repository import is `sample_rag.retriever`, which
    `sample_rag/retriever.py`'s own docstring already establishes performs no
    I/O at all.
    """
    import sample_rag.generator as module

    assert imported_roots(module) & {"pathlib", "os", "io", "shutil", "urllib", "socket"} == set()


# ---------------------------------------------------------------------------
# §20.4 / D-12 — the deliberately duplicated outcome literals
# ---------------------------------------------------------------------------


def test_d12_outcome_literals_agree_with_the_evidence_trace_builder():
    """§20.4, D-12 — the two definitions of the outcome domain remain identical.

    `docs/architecture.md` §6 bars `sample_rag/` from importing `scripts/`, so
    `OUTCOME_ANSWER` and `OUTCOME_ABSTAIN` exist in both modules by design — the
    same accepted duplication as `SUPPORTED_EXTENSIONS` (register AH-9). §20.4
    asks that the duplication be *checked* rather than trusted, which is what
    this is: the invariant becomes mechanically verified rather than a
    maintenance risk.

    A test may import from `scripts/`; only `sample_rag/` may not.
    """
    from scripts.build_evidence_trace import OUTCOME_ABSTAIN as builder_abstain
    from scripts.build_evidence_trace import OUTCOME_ANSWER as builder_answer

    assert OUTCOME_ANSWER == builder_answer
    assert OUTCOME_ABSTAIN == builder_abstain


def test_d12_the_outcome_domain_matches_the_evidence_trace_dataset(real_evidence_trace):
    """§9.1 — the emitted outcome domain is the one the committed dataset uses.

    The Evidence Trace Dataset records an `expected_outcome` for all 22 committed
    questions, derived by `derive_expected_outcome`. The Generator's domain must
    be the same vocabulary, or no generated outcome could ever be compared
    against a committed expectation.

    Subset, not equality: `Abstain` appearing in the dataset depends on the QA
    Dataset containing a `No Answer` question, which is a property of the dataset
    and not of this contract.
    """
    committed = {entry["expected_outcome"] for entry in real_evidence_trace}

    assert committed <= {OUTCOME_ANSWER, OUTCOME_ABSTAIN}


# ---------------------------------------------------------------------------
# Work Package 6.5 — public surface audit
# ---------------------------------------------------------------------------


def test_the_module_exposes_only_the_approved_public_surface():
    """Work Package 6.5 — every public name traces to an approved contract clause.

    Names *defined* by the module, read from its source rather than from
    `dir()`, so imported names (`json`, `dataclass`, `RetrievalResult`) are not
    counted as surface this module offers. Exact equality in both directions: an
    unapproved convenience API fails here, and so does a missing approved name.
    """
    tree = ast.parse(Path(__import__("sample_rag.generator", fromlist=[""]).__file__).read_text(encoding="utf-8"))

    defined = set()
    for node in tree.body:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef)):
            defined.add(node.name)
        elif isinstance(node, ast.Assign):
            defined.update(
                target.id for target in node.targets if isinstance(target, ast.Name)
            )

    assert {name for name in defined if not name.startswith("_")} == set(APPROVED_PUBLIC_SURFACE)


def test_the_generator_exposes_exactly_one_public_method():
    """Work Package 6.5 — `generate` is the whole approved interface.

    §17 approves one method. Helpers are private, so no additional runtime
    responsibility is reachable from outside the component.
    """
    public = {name for name in vars(Generator) if not name.startswith("_")}

    assert public == {"generate"}


def test_no_prompt_context_builder_or_inference_surface_exists():
    """Contract §21, Work Package 3 — the excluded concepts are absent.

    `Prompt`, Context Builder and Assemble are explicitly out of scope, and §6.2
    records that letting the Generator build its own prompt would silently absorb
    the Assemble stage — making a future Assemble-stage failure undiagnosable,
    which is exactly the separation `ALTM-ASSEMBLE-1` exists to preserve.
    """
    import sample_rag.generator as module

    source = Path(module.__file__).read_text(encoding="utf-8")
    defined = {node.name for node in ast.parse(source).body if isinstance(node, ast.ClassDef)}

    assert defined == {"SupportingEvidence", "GeneratedStatement", "GenerationResult", "Generator"}


# ---------------------------------------------------------------------------
# Committed corpus — G-6, G-11, G-12
# ---------------------------------------------------------------------------


@pytest.fixture
def committed_generations(generator, real_chunks):
    """One `GenerationResult` per committed question, over the committed corpus.

    Retrieval is executed through the repository's own `Retriever` rather than
    simulated, so what is generated from is byte-for-byte what the runtime
    produces. Questions come from the Evidence Trace Dataset via
    `load_questions` — a validator reading an authority the runtime may not
    (§19.4).
    """
    retriever = Retriever(real_chunks)

    return [
        (entry_id, generator.generate(question, retriever.retrieve(question, {})))
        for entry_id, question in load_questions()
    ]


def test_g6_every_emitted_chunk_id_exists_in_the_committed_corpus(
    committed_generations, real_chunks_by_id
):
    """G-6 — corpus membership, over every committed question.

    Sprint guarantee 3. §16 records that this holds *by construction* — chunk ids
    are carried through from retrieval and never constructed by the Generator —
    so this specification confirms the construction rather than compensating for
    its absence. The Chunk Corpus is read through its own validation gate (see
    `tests/conftest.py`) and is not otherwise validated here; it is out of scope
    for this sprint and already has committed specifications.
    """
    assert committed_generations

    for entry_id, result in committed_generations:
        for statement in result.statements:
            for evidence in statement.supporting_evidence:
                assert evidence.chunk_id in real_chunks_by_id, (
                    f"{entry_id}: cited chunk {evidence.chunk_id!r} is not in the corpus"
                )


def test_g11_every_span_is_verbatim_in_its_parent_document(
    committed_generations, real_documents_by_id
):
    """G-11 — `text` equals `document_text[character_start:character_end]`.

    The repository's grounding guarantee, applied to generated evidence. Document
    text is obtained through `KnowledgeSource().load()` — the same mechanism GD-8
    uses for Golden Dataset facts — so what is verified is the text the
    repository actually reads.

    This is the specification that proves the Milestone 1A claim in full: every
    claim the Generator makes is a verbatim quotation of committed corpus
    evidence. It is checkable here and not at runtime precisely because the
    runtime may not read the corpus (§18); the offsets carried by the artifact
    are what make the check possible after the fact (T-5).
    """
    for entry_id, result in committed_generations:
        for statement in result.statements:
            for evidence in statement.supporting_evidence:
                document = real_documents_by_id[evidence.document_id]

                assert (
                    evidence.text
                    == document.text[evidence.character_start:evidence.character_end]
                ), f"{entry_id}: span {evidence.chunk_id!r} is not verbatim in its document"


def test_g12_every_emitted_document_id_is_catalogued_by_the_manifest(
    committed_generations, real_manifest_entries
):
    """T-2, G-12 — every cited document resolves to a Knowledge Manifest entry.

    Closes the provenance chain at the Knowledge Authority, the root of
    `docs/MILESTONE_1A.md`'s dependency order. With two overlapping resume
    versions catalogued, `ALTM-KNOWLEDGE-1` (*"answer cites the wrong document
    version"*) is a recorded symptom against exactly this corpus — an answer that
    could not say which version it quoted could not be checked for it at all.
    """
    catalogued = {entry["id"] for entry in real_manifest_entries}

    for entry_id, result in committed_generations:
        for statement in result.statements:
            for evidence in statement.supporting_evidence:
                assert evidence.document_id in catalogued, (
                    f"{entry_id}: cited document {evidence.document_id!r} is not catalogued"
                )


def test_g12_traceability_is_recoverable_from_the_artifact_alone(committed_generations):
    """T-3, T-4, T-5 — the artifact carries its own provenance.

    Every statement reaches at least one chunk and one document, and every result
    records the query that produced it — without re-executing retrieval. T-5 is
    what makes §19.4's cross-authority validation possible while keeping the
    runtime free of any dataset dependency.
    """
    for entry_id, result in committed_generations:
        assert result.diagnostics["query"]

        for statement in result.statements:
            assert {evidence.chunk_id for evidence in statement.supporting_evidence}
            assert {evidence.document_id for evidence in statement.supporting_evidence}


def test_every_committed_question_produces_a_conforming_result(committed_generations):
    """The contract's invariants, over every committed question.

    No answer text is asserted (§19.2): what is asserted is that whatever the
    Milestone 1A lexical retriever returns, the artifact built from it conforms.
    A retrieval change alters which chunks appear here; it cannot make the result
    non-conforming.
    """
    for entry_id, result in committed_generations:
        assert result.outcome in (OUTCOME_ANSWER, OUTCOME_ABSTAIN), entry_id
        assert result.answer_text.strip(), entry_id
        assert (result.statements == []) == (result.outcome == OUTCOME_ABSTAIN), entry_id
        assert tuple(result.diagnostics) == REQUIRED_DIAGNOSTICS, entry_id

        for statement in result.statements:
            assert statement.text
            assert statement.supporting_evidence


def test_generation_over_the_committed_corpus_is_deterministic(generator, real_chunks):
    """G-9 over committed repository state, end to end.

    The determinism claim in the form `docs/CHUNK_CONTRACT.md` §5 states it for
    runtime artifacts — *identical query + identical corpus state ⇒ identical
    result* — executed against the real corpus rather than a synthetic one, and
    checked at both the object and the byte level.
    """
    retriever = Retriever(real_chunks)
    questions = load_questions()

    first = [serialize(generator.generate(q, retriever.retrieve(q, {}))) for _, q in questions]
    second = [serialize(generator.generate(q, retriever.retrieve(q, {}))) for _, q in questions]

    assert first == second
