"""Executable specification — native Context Precision / Context Recall (M2-07).

Specifies `evaluation/context_metrics.py`, the native metric engine Repository
Owner ruling **RO-17** (`docs/DEFERRED_ITEMS_REGISTER.md` §4.9) authorizes in
place of the Ragas path RO-16 authorized and RO-17 Decision 2 disposes of.

**No specification in this file performs a provider call, and none can.**
**RO-14 Decision 2** — carried forward verbatim by **RO-17 Decision 4** — reads
*"No provider call is introduced into the deterministic pytest suite, and none
may be"*, and **a judge call is a provider call**. Every judgement below comes
from a scripted, non-networked substitute; nothing here imports
`sample_rag.deepseek`, `scripts.evaluate_context`, `urllib` or any HTTP
primitive, and `test_m207_no_specification_can_reach_a_provider` asserts that
structurally rather than leaving it to reading.

Two families, deliberately separated
--------------------------------------
1. **Behavioural** — what the metrics mean, over a scripted judge whose answers
   are fixed by the specification. The engine is deterministic given a
   deterministic judge, so these are exact-value assertions rather than
   tolerances.
2. **Structural / governance-boundary** — RO-17's constraints made executable.
   An import allowlist over the engine, a byte-identity assertion over
   `requirements.txt`, a byte-identity assertion over the authorized provider
   boundary, and specifications that the orchestrator neither modifies retrieval
   nor touches M2-18. These are not documentation: they are what makes a future
   edit that quietly adds `ragas`, widens `sample_rag/deepseek.py` or reaches for
   an embedding library fail here instead of passing unnoticed.
"""

import ast
import hashlib
import pathlib

import pytest

from evaluation.context_metrics import (
    ATTRIBUTION_VERDICTS,
    NOT_RELEVANT,
    NOT_SUPPORTED,
    RELEVANCE_VERDICTS,
    RELEVANT,
    SUPPORTED,
    ContextMetricsError,
    aggregate_precision,
    aggregate_recall,
    attribution_prompt,
    compute,
    context_precision_case,
    context_recall_case,
    decomposition_prompt,
    parse_claims,
    parse_verdict,
    relevance_prompt,
    validate_case,
)

# `requirements.txt` as it stands at commit `d96107f`, the sprint's starting
# point. **RO-17 "What RO-17 does not do": `requirements.txt` is byte-identical**,
# the Ragas declaration stays a declaration, and RO-17 Decision 5 grants no new
# embedding or vector-store exception. A digest rather than a substring scan:
# a denylist of package names fails only on the names someone thought to list,
# and this fails on any edit at all — an addition, a removal, a version pin or a
# reordering.
REQUIREMENTS_DIGEST = "acefe72973bb18a53932a4cadc4057bede93f819ab5d7d391cafeca8754a5ce1"

# `sample_rag/deepseek.py` at the same commit. **RO-17 Decision 4 authorizes the
# existing boundary conditionally** — the authorization holds *"if and only if"*
# the native implementation uses it without modifying its provider architecture
# or credential model — and *"`sample_rag/deepseek.py` is not modified by this
# ruling and may not be rewritten to fit an evaluation caller."* This digest is
# that condition, executable.
DEEPSEEK_BOUNDARY_DIGEST = "281192b3ef8ab151f9f440e3758554db8764334f28731a4ceb5f5ba3d17e8974"

# The engine's entire authorized dependency surface. **An allowlist, following
# `tests/test_indexer.py`'s stated reasoning** — *"An allowlist fails on any
# import nobody thought to forbid, which a denylist cannot"* — and it is one
# standard-library module. It is not copied from another module's allowlist:
# `math` is what `_macro` needs for `fsum` and it is the whole of what this
# engine reached for.
ENGINE_IMPORT_ALLOWLIST = {"math"}

# Named because each is specifically barred, and each is a plausible thing for a
# later edit to reach for. **RO-17 Decision 2** (no Ragas), **Decision 3**
# (NA-07: no LangChain/LangGraph/orchestration, no additional provider SDK, no
# arbitrary HTTP access, no model router), **Decision 5** (no embedding library,
# no vector-store package), **Decision 10** (no DeepEval, no Promptfoo, no
# additional evaluation framework).
BARRED_PACKAGES = (
    "ragas",
    "langchain",
    "langchain_core",
    "langchain_community",
    "langchain_openai",
    "langgraph",
    "llama_index",
    "haystack",
    "deepeval",
    "promptfoo",
    "openai",
    "anthropic",
    "litellm",
    "cohere",
    "google",
    "mistralai",
    "ollama",
    "transformers",
    "sentence_transformers",
    "torch",
    "faiss",
    "chromadb",
    "qdrant_client",
    "pinecone",
    "weaviate",
    "numpy",
    "pandas",
    "sklearn",
    "spacy",
    "nltk",
    "httpx",
    "requests",
    "aiohttp",
    "urllib3",
    "urllib",
    "http",
    "socket",
    "mlflow",
    "langsmith",
    "phoenix",
)


# ---------------------------------------------------------------------------
# Scripted judges — the whole of the non-determinism, held still
# ---------------------------------------------------------------------------


class ScriptedJudge:
    """A judge that answers from a script and records what it was asked.

    Substitutes for the provider at the engine's one injected seam. It holds no
    endpoint, no credential, no client and no network primitive — there is
    nothing here for a specification to reach a provider through, which is the
    property RO-14 Decision 2 requires of this suite.

    `prompts` is kept so a specification can assert what the judge was *not*
    shown — the non-circularity specification below reads it.
    """

    def __init__(self, answers):
        self.answers = list(answers)
        self.prompts = []

    def __call__(self, prompt):
        self.prompts.append(prompt)
        if not self.answers:
            raise AssertionError("The judge was called more times than scripted.")
        return self.answers.pop(0)


class ConstantJudge:
    """A judge that always answers the same way, whatever it is asked."""

    def __init__(self, answer):
        self.answer = answer
        self.calls = 0

    def __call__(self, prompt):
        self.calls += 1
        return self.answer


class RefusingJudge:
    """A judge that fails the way a provider fails — by raising."""

    def __call__(self, prompt):
        raise RuntimeError("provider unavailable")


def case(identity="q1", question="How many years of experience?", reference="Around 7.5 years.", retrieved=("a", "b")):
    """One evaluation case, with passages named by their text for readability."""
    return {
        "id": identity,
        "question": question,
        "reference_answer": reference,
        "retrieved": [
            {"chunk_id": f"chunk_{text}", "text": f"passage {text}"} for text in retrieved
        ],
    }


def imported_modules(source):
    """Top-level package names imported by a source string."""
    tree = ast.parse(source)
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module.split(".")[0])
    return names


def source_of(repository_root, *parts):
    """Read a repository source file as text."""
    return pathlib.Path(repository_root, *parts).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# 1. Context Precision — "of everything retrieved, how much was actually
#    relevant?" (docs/AI_Quality_Metrics_Reference.md §Layer 3)
# ---------------------------------------------------------------------------


def test_m207_fully_relevant_retrieval_scores_one():
    """Every retrieved passage judged relevant — the metric's upper bound."""
    judge = ConstantJudge(RELEVANT)
    measured = context_precision_case(case(retrieved=("a", "b", "c")), judge)

    assert measured["retrieved_passages"] == 3
    assert measured["relevant_passages"] == 3
    assert measured["context_precision"] == 1.0
    assert judge.calls == 3


def test_m207_fully_irrelevant_retrieval_scores_zero():
    """Retrieval returned five passages and none of them bore on the question."""
    measured = context_precision_case(
        case(retrieved=("a", "b", "c", "d", "e")), ConstantJudge(NOT_RELEVANT)
    )

    assert measured["relevant_passages"] == 0
    assert measured["context_precision"] == 0.0


def test_m207_partially_relevant_retrieval_scores_the_proportion():
    """Two of five relevant — the noise proportion `docs/altm.md` §6 describes."""
    judge = ScriptedJudge(
        [RELEVANT, NOT_RELEVANT, RELEVANT, NOT_RELEVANT, NOT_RELEVANT]
    )
    measured = context_precision_case(case(retrieved=tuple("abcde")), judge)

    assert measured["context_precision"] == 0.4
    assert [record["verdict"] for record in measured["passages"]] == [
        RELEVANT,
        NOT_RELEVANT,
        RELEVANT,
        NOT_RELEVANT,
        NOT_RELEVANT,
    ]


def test_m207_empty_retrieval_scores_zero_and_spends_no_judgement():
    """The one reachable zero denominator, on the convention P3.3.3 records.

    `evaluation/retrieval_metrics.py` documents `0.0` for a question that
    retrieved nothing — *"no expected chunk was among those retrieved, because
    none was"* — and the same reading holds here. **No judge call is made**: a
    degenerate case costs no provider interaction.
    """
    judge = ConstantJudge(RELEVANT)
    measured = context_precision_case(case(retrieved=()), judge)

    assert measured["context_precision"] == 0.0
    assert measured["retrieved_passages"] == 0
    assert judge.calls == 0


def test_m207_context_precision_carries_rank_without_depending_on_it():
    """Ordering is evidence, not arithmetic — the derivation, made executable.

    No repository authority ranks, discounts or position-weights either metric:
    *"of everything retrieved, how much was actually relevant"* is a proportion
    of a set. A rank-weighted variant would be a different metric imported from
    outside the repository's own definitions, so permuting the retrieved
    passages must not move the score.
    """
    forward = context_precision_case(
        case(retrieved=("a", "b", "c")), ScriptedJudge([RELEVANT, NOT_RELEVANT, RELEVANT])
    )
    reversed_case = case(retrieved=("a", "b", "c"))
    reversed_case["retrieved"].reverse()
    backward = context_precision_case(
        reversed_case, ScriptedJudge([RELEVANT, NOT_RELEVANT, RELEVANT])
    )

    assert forward["context_precision"] == backward["context_precision"]
    assert [record["rank"] for record in forward["passages"]] == [1, 2, 3]


def test_m207_relevance_is_judged_against_the_question_alone():
    """`docs/altm.md` §6 — Context Precision *"has nothing to do with what is
    eventually said"*, so the reference answer is not shown to this judge.

    Showing it would convert *relevant to the question* into *supports the
    expected answer*, which is Context Recall's proposition under Context
    Precision's name.
    """
    judge = ScriptedJudge([RELEVANT])
    context_precision_case(
        case(reference="THE-REFERENCE-ANSWER-SENTINEL", retrieved=("a",)), judge
    )

    assert "THE-REFERENCE-ANSWER-SENTINEL" not in judge.prompts[0]
    assert "How many years of experience?" in judge.prompts[0]


# ---------------------------------------------------------------------------
# 2. Context Recall — "of everything relevant that exists in the source, how
#    much did retrieval actually find?"
# ---------------------------------------------------------------------------


def test_m207_every_reference_claim_recovered_scores_one():
    """Three reference claims, all supported by what retrieval returned."""
    judge = ScriptedJudge(
        ["claim one\nclaim two\nclaim three", SUPPORTED, SUPPORTED, SUPPORTED]
    )
    measured = context_recall_case(case(), judge)

    assert measured["claims_total"] == 3
    assert measured["claims_supported"] == 3
    assert measured["context_recall"] == 1.0


def test_m207_no_reference_claim_recovered_scores_zero():
    """Retrieval returned context, and none of the reference information is in it."""
    judge = ScriptedJudge(["claim one\nclaim two", NOT_SUPPORTED, NOT_SUPPORTED])
    measured = context_recall_case(case(), judge)

    assert measured["claims_supported"] == 0
    assert measured["context_recall"] == 0.0


def test_m207_partial_recovery_is_representable():
    """The phenomenon the metric exists to detect.

    `docs/AI_Quality_Metrics_Reference.md` §Layer 3 illustrates Context Recall
    with *"Resume mentions 'CrewAI' twice; retrieval surfaces only one
    occurrence"* — a partially recovered reference. A metric that could only say
    "all" or "nothing" would not detect it, which is why the reference is
    decomposed into claims rather than scored whole.
    """
    judge = ScriptedJudge(
        ["claim one\nclaim two\nclaim three\nclaim four", SUPPORTED, NOT_SUPPORTED, SUPPORTED, NOT_SUPPORTED]
    )
    measured = context_recall_case(case(), judge)

    assert measured["claims_total"] == 4
    assert measured["context_recall"] == 0.5


def test_m207_multiple_reference_claims_are_each_judged_separately():
    """One attribution call per claim, each against the whole retrieved context."""
    judge = ScriptedJudge(["alpha\nbeta", SUPPORTED, NOT_SUPPORTED])
    measured = context_recall_case(case(retrieved=("a", "b")), judge)

    assert [record["claim"] for record in measured["claims"]] == ["alpha", "beta"]
    assert "passage a" in judge.prompts[1] and "passage b" in judge.prompts[1]
    assert "alpha" in judge.prompts[1] and "beta" not in judge.prompts[1]


def test_m207_the_recall_reference_never_sees_retrieval_output():
    """**RO-17 Decision 6** — the reference is *"the committed golden ground
    truth — never the system's own retrieval output"*.

    The decomposition call is the first call made, and no retrieved text may
    appear in it. A reference derived from retrieval would make Context Recall a
    measurement of retrieval against itself, which is the circularity this
    ruling exists to prevent. Asserted twice over: the prompt cannot contain the
    retrieved text, and `decomposition_prompt` has no parameter through which it
    could arrive.
    """
    judge = ScriptedJudge(["claim one", SUPPORTED])
    context_recall_case(
        case(reference="Around 7.5 years.", retrieved=("RETRIEVED-SENTINEL",)), judge
    )

    decomposition = judge.prompts[0]
    assert "passage RETRIEVED-SENTINEL" not in decomposition
    assert "chunk_RETRIEVED-SENTINEL" not in decomposition
    assert "Around 7.5 years." in decomposition

    import inspect

    parameters = inspect.signature(decomposition_prompt).parameters
    assert list(parameters) == ["question", "reference_answer"]


def test_m207_empty_retrieval_recall_is_zero_and_says_why():
    """Nothing retrieved recovers nothing, and no judgement is spent discovering it.

    The case carries `unmeasured_reason`, so an empty-retrieval zero is never
    read as a judged zero — a distinction a bare `0.0` would lose.
    """
    judge = ConstantJudge(SUPPORTED)
    measured = context_recall_case(case(retrieved=()), judge)

    assert measured["context_recall"] == 0.0
    assert measured["claims_total"] == 0
    assert measured["unmeasured_reason"] == "retrieval returned no context"
    assert judge.calls == 0


def test_m207_context_recall_is_not_chunk_identifier_overlap():
    """**RO-17 Decision 1** — *"a simplified set-overlap calculation is NOT
    authorized as a substitute for the metric's meaning."*

    `expected_chunk` is not read by the engine, so a case carrying a wrong,
    absurd or absent one measures identically. The two metrics are functions of
    text and judgement, never of identifiers — which is the whole distinction
    `docs/P3.3.3_Retrieval_Metrics_Report.md` §3 draws between these and the
    `chunk_` metrics.
    """
    without = case()
    with_expectation = case()
    with_expectation["expected_chunk"] = ["an-identifier-matching-nothing"]

    plain = context_recall_case(without, ScriptedJudge(["alpha", SUPPORTED]))
    decorated = context_recall_case(with_expectation, ScriptedJudge(["alpha", SUPPORTED]))

    assert plain["context_recall"] == decorated["context_recall"] == 1.0

    engine = pathlib.Path(
        pathlib.Path(__file__).resolve().parent.parent, "evaluation", "context_metrics.py"
    ).read_text(encoding="utf-8")
    tree = ast.parse(engine)
    subscripts = {
        node.slice.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant)
    }
    assert "expected_chunk" not in subscripts
    assert "expected_chunk_ids" not in subscripts


# ---------------------------------------------------------------------------
# 3. Reading the judge — strict, total, and payload-free
# ---------------------------------------------------------------------------


def test_m207_a_verdict_is_matched_exactly_and_not_by_containment():
    """`NOT_SUPPORTED` must never be read as `SUPPORTED`.

    A containment test would invert the verdict silently and inflate the metric
    — the single most damaging parsing bug available here, and the reason
    parsing is an exact match against a closed vocabulary.
    """
    assert parse_verdict(NOT_SUPPORTED, ATTRIBUTION_VERDICTS, "a claim") == NOT_SUPPORTED
    assert parse_verdict(NOT_RELEVANT, RELEVANCE_VERDICTS, "a passage") == NOT_RELEVANT

    measured = context_recall_case(case(), ScriptedJudge(["alpha", NOT_SUPPORTED]))
    assert measured["context_recall"] == 0.0


def test_m207_verdict_formatting_is_normalized_but_content_is_not():
    """Whitespace, a trailing period, backticks and emphasis are shape, not content."""
    for answer in (" SUPPORTED ", "SUPPORTED.", "`SUPPORTED`", "**supported**", "\nSupported\n"):
        assert parse_verdict(answer, ATTRIBUTION_VERDICTS, "a claim") == SUPPORTED


def test_m207_an_unreadable_verdict_raises_rather_than_defaulting():
    """A failed judgement is not a measurement.

    Defaulting to the negative verdict would let this module *fabricate* a score
    from a judge that answered nothing, and a fabricated zero is
    indistinguishable in a report from a judged one.
    """
    with pytest.raises(ContextMetricsError):
        parse_verdict("it depends, probably", ATTRIBUTION_VERDICTS, "a claim")

    with pytest.raises(ContextMetricsError):
        context_precision_case(case(retrieved=("a",)), ConstantJudge("maybe"))

    with pytest.raises(ContextMetricsError):
        parse_verdict(None, RELEVANCE_VERDICTS, "a passage")


def test_m207_a_failed_judgement_never_quotes_what_the_judge_returned():
    """`sample_rag/deepseek.py`'s discipline, one layer up.

    That module states *"no provider response body and no request header reaches
    an error string"*. The same holds here: an unreadable verdict is reported by
    the **proposition** being judged, never by the answer, so an evaluation
    failure can be pasted into a report or a traceback safely.
    """
    secret_shaped = "sk-not-a-key-but-shaped-like-one"
    with pytest.raises(ContextMetricsError) as failure:
        parse_verdict(secret_shaped, ATTRIBUTION_VERDICTS, "reference claim 1 of case 'q1'")

    assert secret_shaped not in str(failure.value)
    assert "reference claim 1 of case 'q1'" in str(failure.value)


def test_m207_a_judge_that_raises_propagates_unchanged():
    """No retry, no fallback, no degraded result.

    `sample_rag/deepseek.py` holds *"no retry policy, no backoff, no circuit
    breaker and no cache"*, and an evaluation layer that added one would turn
    *"a permission for one call"* into an unbounded number of them.
    """
    with pytest.raises(RuntimeError):
        context_precision_case(case(retrieved=("a",)), RefusingJudge())


def test_m207_a_decomposition_returning_nothing_is_a_judge_failure():
    """A non-empty reference cannot decompose to zero claims.

    `validate_case` guarantees the reference answer is non-empty, so an empty
    decomposition describes the judge rather than the reference. Accepting it
    would produce a `0/0` recall of `0.0` that looked like a measurement.
    """
    with pytest.raises(ContextMetricsError):
        context_recall_case(case(), ScriptedJudge(["   \n  \n"]))

    with pytest.raises(ContextMetricsError):
        parse_claims("", "the reference claims of case 'q1'")


def test_m207_claim_shape_is_normalized_but_claim_content_is_not():
    """A bullet or an enumerator the judge added is removed; the text is not touched."""
    claims = parse_claims(
        "- alpha claim\n* beta claim\n1. gamma claim\n2) delta claim\n\n",
        "the reference claims of case 'q1'",
    )

    assert claims == ["alpha claim", "beta claim", "gamma claim", "delta claim"]


# ---------------------------------------------------------------------------
# 4. The measurable domain — malformed input is refused before any judgement
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("field", ["id", "question", "reference_answer"])
def test_m207_a_case_missing_a_reference_field_is_refused(field):
    """Each of the three is load-bearing for one of the two metrics."""
    malformed = case()
    malformed[field] = "   "

    with pytest.raises(ContextMetricsError):
        validate_case(malformed)


def test_m207_a_malformed_retrieval_is_refused_before_a_judge_is_called():
    """A judge asked about a blank passage answers about nothing, and its verdict
    would still enter a denominator."""
    judge = ConstantJudge(RELEVANT)

    for retrieved in (
        "not a list",
        ["not an object"],
        [{"chunk_id": "a"}],
        [{"chunk_id": "a", "text": "  "}],
        [{"text": "orphan text"}],
        [{"chunk_id": "a", "text": "x"}, {"chunk_id": "a", "text": "y"}],
    ):
        malformed = case()
        malformed["retrieved"] = retrieved
        with pytest.raises(ContextMetricsError):
            context_precision_case(malformed, judge)

    assert judge.calls == 0


def test_m207_a_duplicate_case_id_is_refused():
    """A question measured twice is counted twice in every denominator."""
    with pytest.raises(ContextMetricsError):
        compute([case(identity="q1"), case(identity="q1")], ConstantJudge(RELEVANT))


def test_m207_every_case_is_validated_before_any_judgement_is_spent():
    """A malformed dataset costs no provider interaction, and produces no partial
    measurement that looks whole."""
    judge = ConstantJudge(RELEVANT)
    malformed = case(identity="q2")
    malformed["question"] = ""

    with pytest.raises(ContextMetricsError):
        compute([case(identity="q1"), malformed], judge)

    assert judge.calls == 0


# ---------------------------------------------------------------------------
# 5. Aggregation — both standard forms, re-derived independently
# ---------------------------------------------------------------------------


def test_m207_both_aggregations_are_published_and_differ_where_they_should():
    """`docs/P3.3.3_…` §3 — *"No repository authority selects between them."*

    Macro weights every case equally, micro weights every unit equally, so a
    case retrieving more passages moves micro further than macro. Two cases
    engineered to disagree, re-derived here by hand rather than by calling the
    engine's own arithmetic.
    """
    cases = [
        {"id": "a", "retrieved_passages": 1, "relevant_passages": 1},
        {"id": "b", "retrieved_passages": 4, "relevant_passages": 1},
    ]
    aggregated = aggregate_precision(cases)

    assert aggregated["context_precision_macro"] == round((1 / 1 + 1 / 4) / 2, 4)
    assert aggregated["context_precision_micro"] == round(2 / 5, 4)
    assert aggregated["context_precision_macro"] != aggregated["context_precision_micro"]


def test_m207_aggregation_is_re_derivable_over_exact_rationals():
    """An independent recomputation, in `Fraction`, of what the engine published.

    `evaluation/retrieval_metrics_validator.py` establishes the pattern: a
    second derivation from a different arithmetic is a cross-check, where
    disagreement is a finding rather than a duplication. Done here inside the
    specification rather than as a second module, because the engine's
    aggregation is two ratios and a mean.
    """
    from fractions import Fraction

    recall_cases = [
        {"id": "a", "claims_total": 3, "claims_supported": 2, "context_recall": round(2 / 3, 4), "unmeasured_reason": None},
        {"id": "b", "claims_total": 5, "claims_supported": 5, "context_recall": 1.0, "unmeasured_reason": None},
        {"id": "c", "claims_total": 0, "claims_supported": 0, "context_recall": 0.0, "unmeasured_reason": "retrieval returned no context"},
    ]
    aggregated = aggregate_recall(recall_cases)

    micro = Fraction(2 + 5 + 0, 3 + 5 + 0)
    assert aggregated["context_recall_micro"] == round(float(micro), 4)
    assert aggregated["reference_claims"] == 8
    assert aggregated["supported_claims"] == 7
    assert aggregated["cases_without_retrieved_context"] == 1


def test_m207_an_empty_evaluation_reports_zero_rather_than_raising():
    """The report stays total: every field is populated on every path."""
    report = compute([], ConstantJudge(RELEVANT))

    assert report["context_precision"]["context_precision_macro"] == 0.0
    assert report["context_recall"]["context_recall_micro"] == 0.0
    assert report["per_case"] == []


def test_m207_repeated_execution_over_a_fixed_judge_is_identical():
    """The engine is deterministic; **only the judge is not.**

    Given a judge whose answers are held still, two runs produce equal reports —
    prompt construction, parsing, arithmetic and key order are all pure. This
    specification is what makes the report's non-determinism attributable
    entirely to the provider rather than to the measurement.
    """
    def script():
        return ScriptedJudge(
            [RELEVANT, NOT_RELEVANT, "alpha\nbeta", SUPPORTED, NOT_SUPPORTED]
        )

    first = compute([case(retrieved=("a", "b"))], script())
    second = compute([case(retrieved=("a", "b"))], script())

    assert first == second
    assert first["context_precision"]["context_precision_micro"] == 0.5
    assert first["context_recall"]["context_recall_micro"] == 0.5


def test_m207_the_report_carries_the_evidence_that_explains_each_score():
    """**RO-17 Decision 6** — *"M2-07 MUST preserve enough evidence to explain a
    metric result, so a score can be read as evidence rather than as an
    assertion."*

    Per passage: its rank, its chunk id and its verdict. Per claim: its text and
    its verdict. **No prompt and no raw judge response is carried** — a verdict
    and a parsed claim are the derived evaluation evidence the metric is computed
    from; the payloads that carried them are not, and there is nothing in the
    report to redact.
    """
    report = compute(
        [case(retrieved=("a", "b"))],
        ScriptedJudge([RELEVANT, NOT_RELEVANT, "alpha\nbeta", SUPPORTED, NOT_SUPPORTED]),
    )
    row = report["per_case"][0]

    assert row["passages"] == [
        {"rank": 1, "chunk_id": "chunk_a", "verdict": RELEVANT},
        {"rank": 2, "chunk_id": "chunk_b", "verdict": NOT_RELEVANT},
    ]
    assert row["claims"] == [
        {"claim": "alpha", "verdict": SUPPORTED},
        {"claim": "beta", "verdict": NOT_SUPPORTED},
    ]

    def scalars(value):
        if isinstance(value, dict):
            for item in value.values():
                yield from scalars(item)
        elif isinstance(value, list):
            for item in value:
                yield from scalars(item)
        else:
            yield value

    prose = [item for item in scalars(report) if isinstance(item, str)]
    for fragment in ("You are judging", "Answer with exactly one word", "Rules:"):
        assert not any(fragment in item for item in prose)


def test_m207_the_judged_propositions_are_stated_in_one_place_and_are_pure():
    """**The JUDGE SEMANTICS rule** — what the judge evaluates is fixed before
    the metric is computed, not discovered from its output.

    Three propositions, three prompt builders, each a pure function of its
    arguments: same arguments, byte-identical prompt, every time. No judge
    produces an opaque score that becomes a metric; each answers one closed
    question and the aggregation over those answers is the metric.
    """
    assert relevance_prompt("q", "p") == relevance_prompt("q", "p")
    assert decomposition_prompt("q", "a") == decomposition_prompt("q", "a")
    assert attribution_prompt("c", "x") == attribution_prompt("c", "x")

    assert RELEVANT in relevance_prompt("q", "p")
    assert NOT_RELEVANT in relevance_prompt("q", "p")
    assert SUPPORTED in attribution_prompt("c", "x")
    assert NOT_SUPPORTED in attribution_prompt("c", "x")


def test_m207_the_relevance_proposition_states_relevance_not_sufficiency():
    """The correction recorded in `docs/M2.07_…` §9, pinned so it cannot regress.

    A first form of this proposition asked only whether a passage was *"relevant
    to answering the question"*, and the judge reproducibly read that as a
    **sufficiency** test — marking *"managing a cross-functional team of 5"*
    `NOT_RELEVANT` to *"How many engineers did Karthik lead …"* because the
    passage did not settle the count exactly.

    That is a different metric. `docs/AI_Quality_Metrics_Reference.md` §Layer 3
    asks *"how much was actually **relevant**"* and illustrates it by topic;
    `docs/altm.md` §6 calls the quantity *"noise in retrieved evidence"*. Noise
    is content that does not bear on the question, not content that fails to
    settle it — and a sufficiency test would make Context Precision a property
    of chunking rather than of retrieval.

    The proposition must therefore keep saying so explicitly.
    """
    proposition = relevance_prompt("q", "p")

    assert "not sufficiency" in proposition
    assert "only partly" in proposition
    assert "completely" in proposition


# ---------------------------------------------------------------------------
# 6. Structural boundary specifications — RO-17 made executable
# ---------------------------------------------------------------------------


def test_m207_the_engine_imports_exactly_its_authorized_dependency_surface(repository_root):
    """An **allowlist** over the engine's imports, not a denylist.

    `tests/test_indexer.py` states the reasoning this follows: *"An allowlist
    fails on any import nobody thought to forbid, which a denylist cannot."*
    The allowlist is `math` and nothing else — the engine's actual surface,
    derived from what it needed rather than copied from another module.

    This is the specification that fails if a later edit reaches for Ragas,
    LangChain, an embedding library, a vector store, a provider SDK or an HTTP
    client, whether or not anyone remembered to name it.
    """
    imports = imported_modules(source_of(repository_root, "evaluation", "context_metrics.py"))

    assert imports == ENGINE_IMPORT_ALLOWLIST

    for barred in BARRED_PACKAGES:
        assert barred not in imports


def test_m207_the_engine_reaches_no_pipeline_and_no_orchestrator(repository_root):
    """`docs/architecture.md` §6's direction, kept.

    `evaluation/retrieval_metrics.py` states the rule this inherits: the engine
    imports nothing from `sample_rag/`, `scripts/` or another `evaluation/`
    module, performs no filesystem and no network I/O, and reads no repository
    authority. Every input arrives as an argument, so a new retriever changes
    what the cases *say*, not what this engine *is*.
    """
    source = source_of(repository_root, "evaluation", "context_metrics.py")
    imports = imported_modules(source)

    assert not {"sample_rag", "scripts", "evaluation"} & imports

    tree = ast.parse(source)
    called = {
        node.func.id for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    called |= {
        node.func.attr for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }

    assert not {"open", "urlopen", "read_text", "write_text", "loads", "dumps"} & called


def test_m207_no_specification_can_reach_a_provider(repository_root):
    """**RO-14 Decision 2**, carried forward by **RO-17 Decision 4** — *"No
    provider call is introduced into the deterministic pytest suite, and none
    may be."* **A judge call is a provider call.**

    Asserted over this specification file itself: it imports no provider client,
    no network primitive and not the on-demand evaluation script. The judges
    above are scripted substitutes, which is the pattern
    `tests/test_model_generator.py` already established for the generation
    boundary.
    """
    imports = imported_modules(source_of(repository_root, "tests", "test_context_metrics.py"))

    assert "sample_rag" not in imports
    assert "scripts" not in imports
    for barred in BARRED_PACKAGES:
        assert barred not in imports


def test_m207_requirements_are_byte_identical_to_the_starting_commit(repository_root):
    """**RO-17 "What RO-17 does not do"** — *"`requirements.txt` is
    byte-identical"*, and the `ragas` declaration stays a declaration.

    RO-16's fourth A-5 exception is **authorized and untaken**; RO-17 Decision 5
    grants no embedding or vector-store exception; NA-07 bars LangChain
    outright. A digest rather than a name scan: this fails on *any* edit — an
    addition, a removal, a version pin, a reordering — including one nobody
    thought to forbid.
    """
    requirements = pathlib.Path(repository_root, "requirements.txt").read_bytes()

    assert hashlib.sha256(requirements).hexdigest() == REQUIREMENTS_DIGEST


def test_m207_the_authorized_provider_boundary_was_not_widened(repository_root):
    """**RO-17 Decision 4** — the judge authorization is *"CONDITIONAL ON
    TECHNICAL REUSE"*, and *"`sample_rag/deepseek.py` is not modified by this
    ruling and may not be rewritten to fit an evaluation caller."*

    The finding this asserts is that nothing had to change:
    `DeepSeekClient.complete(messages) -> str` was already the whole of what a
    judge needs. A byte-identity digest is the condition made executable — an
    edit to the provider client to accommodate an evaluation caller fails here,
    which is the outcome the condition exists to prevent.
    """
    boundary = pathlib.Path(repository_root, "sample_rag", "deepseek.py").read_bytes()

    assert hashlib.sha256(boundary).hexdigest() == DEEPSEEK_BOUNDARY_DIGEST


def test_m207_no_second_provider_client_was_created(repository_root):
    """One sanctioned boundary, still one.

    RO-17 Decision 4 authorizes no alternate provider client, no second provider
    architecture, no SDK, no model router and no arbitrary HTTP access.
    `sample_rag/deepseek.py` remains the only module in the repository holding a
    network primitive.
    """
    holders = []
    for directory in ("sample_rag", "scripts", "evaluation"):
        for module in pathlib.Path(repository_root, directory).glob("*.py"):
            if {"urllib", "http", "socket", "httpx", "requests"} & imported_modules(
                module.read_text(encoding="utf-8")
            ):
                holders.append(f"{directory}/{module.name}")

    assert holders == ["sample_rag/deepseek.py"]


def test_m207_the_evaluation_entry_point_measures_retrieval_without_changing_it(repository_root):
    """**M2-07 is MEASURE, not IMPROVE.**

    The orchestrator calls each retrieval stage through the function that already
    owns it and takes no ranking, depth, fusion or threshold decision of its own.
    Asserted over declared names rather than over the text — the module docstring
    legitimately *mentions* each to record what it does not do, and a substring
    scan over source would make that prose a failure. This is the convention
    `tests/test_model_generator.py::test_m206_no_context_budget_or_compression_mechanism_exists`
    established.
    """
    source = source_of(repository_root, "scripts", "evaluate_context.py")
    tree = ast.parse(source)

    declared = {
        node.name.lower()
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.ClassDef))
    }
    declared |= {
        node.id.lower()
        for node in ast.walk(tree)
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store)
    }

    for barred in (
        "top_k",
        "rrf",
        "threshold",
        "rerank",
        "rewrite",
        "expand",
        "weight",
        "boost",
        "truncat",
        "budget",
        "retry",
        "fallback",
    ):
        assert not any(barred in name for name in declared), (
            f"scripts/evaluate_context.py declares a {barred!r} name"
        )

    imports = imported_modules(source)
    assert {"sample_rag", "scripts", "evaluation"} <= imports


def test_m207_the_evaluation_entry_point_leaves_m218_alone(repository_root):
    """**RO-17 Decision 9** — M2-18 remains ✅ DISCHARGED and untouched.

    *"Not modified by this ruling, and not to be modified to suit evaluation:
    `scripts/execution_trace.py`, `scripts/run_generation.py`,
    `tests/test_execution_trace.py` and `docs/M2.18_Execution_Evidence_Report.md`.
    No trace field may be added for evaluation, no `VectorStore` widened and no
    semantic similarity score exposed."*

    The evaluation path does not import the trace layer and writes no file at
    all — `reports/baseline/` and `reports/regressions/` are **M3-03** scaffolds
    and are not populated by this sprint.
    """
    source = source_of(repository_root, "scripts", "evaluate_context.py")
    tree = ast.parse(source)

    assert "execution_trace" not in imported_modules(source)

    called = {
        node.func.id for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    called |= {
        node.func.attr for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }

    # `append` is deliberately absent from this set: the M2-18 trace append is
    # already unreachable by the import assertion above, and a list `append` is
    # ordinary composition. Filesystem writes are what this asserts.
    assert not {"open", "write_text", "write_bytes", "mkdir", "touch"} & called


def test_m207_no_evaluation_module_imports_a_barred_package(repository_root):
    """The boundary, swept across every module this sprint could have touched.

    A per-module allowlist protects the module it names; this protects the
    directories against a barred import arriving in a *different* file — which
    is how a dependency actually enters a repository.
    """
    for directory in ("evaluation", "scripts"):
        for module in pathlib.Path(repository_root, directory).glob("*.py"):
            imports = imported_modules(module.read_text(encoding="utf-8"))
            for barred in BARRED_PACKAGES:
                if barred in ("urllib", "http") and module.name == "deepseek.py":
                    continue
                assert barred not in imports, (
                    f"{directory}/{module.name} imports {barred!r}"
                )
