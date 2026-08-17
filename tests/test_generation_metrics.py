"""Executable specification — native generation-quality metrics (M2-08).

Specifies `evaluation/generation_metrics.py`, the native metric engine Repository
Owner ruling **RO-18** (`docs/DEFERRED_ITEMS_REGISTER.md` §4.10) authorizes in
place of the DeepEval path RO-18 Decision 2 disposes of.

**The semantics specified here were frozen before the engine existed**, in
`docs/M2.08_Metric_Semantics_Report.md`, under RO-18 Decision 8's requirement
that the operational propositions be *"recorded in implementation evidence
before implementing them"*. §10 of that report is a labelled probe set with an
authority citation per row; §11 is its validation gate. **Family 2 below is that
probe set, encoded — the labels are the report's, not this file's**, and a probe
that changed to make an implementation pass would be changing the frozen
semantics rather than the code.

**No specification in this file performs a provider call, and none can.**
**RO-14 Decision 2**, carried forward by **RO-18 Decision 6**, reads *"no
provider call may enter the deterministic pytest suite"*, and **a judge call is a
provider call**. Every judgement below comes from a scripted, non-networked
substitute; nothing here imports `sample_rag.deepseek`,
`scripts.evaluate_generation`, `urllib` or any HTTP primitive, and
`test_m208_no_specification_can_reach_a_provider` asserts that structurally
rather than leaving it to reading.

Four families, deliberately separated
---------------------------------------
1. **Behavioural** — what the four metrics mean, over a scripted judge whose
   answers are fixed by the specification. The engine is deterministic given a
   deterministic judge, so these are exact-value assertions rather than
   tolerances.
2. **Frozen semantic probes** — `docs/M2.08_Metric_Semantics_Report.md` §10's
   FG-1…FG-7 and AR-1…AR-8, each named for the probe it encodes. FG-1 and FG-7
   are the Faithfulness/Groundedness gate; FG-5 is the probe that fails if
   Hallucination Rate is ever implemented as `1 - Faithfulness`; AR-1 and AR-6
   are the two directions of Answer Relevancy's independence from truthfulness.
3. **Judge-input isolation** — the propositions' inputs and *exclusions*,
   asserted over the prompts a recording judge actually received. These are
   **boundary specifications, not outcome specifications**: a metric can be
   numerically right while the judge saw something it must not have, and only
   these detect that.
4. **Structural / governance-boundary** — RO-18's constraints made executable.
   An import allowlist over the engine, byte-identity assertions over
   `requirements.txt` and over the authorized provider boundary, and
   specifications that the new entry point neither modifies the pipeline nor
   touches M2-07 or M2-18. These are what make a future edit that quietly adds
   `deepeval`, widens `sample_rag/deepseek.py` or reaches for an embedding
   library fail here instead of passing unnoticed.

On not sharing the boundary constants with M2-07
--------------------------------------------------
`tests/test_context_metrics.py` holds its own copies of the two digests and its
own barred-package list. **RO-18 Decision 11 leaves M2-07's artifacts untouched
by name** — *"`evaluation/context_metrics.py`, `tests/test_context_metrics.py`,
`scripts/evaluate_context.py` … are untouched"* — so refactoring them into a
shared helper is not available to this sprint, and the constants are restated
here instead. They are also not the same assertion: M2-07's digests execute
RO-17 Decision 4's condition, and these execute RO-18 Decision 4's and Decision
7's, at a different starting commit. Two rulings, two independent checks.
"""

import ast
import hashlib
import inspect
import pathlib

import pytest

from evaluation.generation_metrics import (
    ABSTAIN_OUTCOME,
    ANSWER_OUTCOME,
    ATTRIBUTION_VERDICTS,
    BARRED_CASE_FIELDS,
    COMPLETE,
    CONTEXT_SEPARATOR,
    CONTRADICTED,
    DIRECT,
    HALLUCINATED_VERDICTS,
    NOT_COMPLETE,
    NOT_DIRECT,
    NOT_ONLY,
    NOT_SUPPORTED,
    ONLY,
    PARTIALLY_SUPPORTED,
    SUPPORT_VERDICTS,
    SUPPORTED,
    GenerationMetricsError,
    aggregate_faithfulness,
    aggregate_groundedness,
    aggregate_hallucination_rate,
    aggregate_relevancy,
    attribution_prompt,
    claim_metrics_case,
    claim_prompt,
    compute,
    parse_claims,
    parse_relevancy,
    parse_verdict,
    relevancy_case,
    relevancy_prompt,
    support_prompt,
    validate_case,
)

# `requirements.txt` as it stands at commit `33f34e0`, this sprint's starting
# point. **RO-18 Decision 7 authorizes no new dependency, by name** — DeepEval,
# Promptfoo, Ragas (for M2-08), LangChain, LangGraph, the OpenAI SDK, any new
# HTTP SDK, orchestration and model routers — and records that *"no transitive
# dependency becomes authorized merely because it would be useful"*. A digest
# rather than a name scan: a denylist fails only on the names someone thought to
# list, and this fails on any edit at all — an addition, a removal, a version pin
# or a reordering.
REQUIREMENTS_DIGEST = "acefe72973bb18a53932a4cadc4057bede93f819ab5d7d391cafeca8754a5ce1"

# `sample_rag/deepseek.py` at the same commit. **RO-18 Decision 4 authorizes the
# existing boundary narrowly and conditionally** — not by extending RO-17
# Decision 4 — and bars *"rewriting `sample_rag/deepseek.py`"*, a second provider
# client, a model router and arbitrary HTTP access, requiring that *"the provider
# implementation must remain architecturally unchanged"*. This digest is that
# condition, executable: an edit to the provider client to accommodate an
# evaluation caller fails here, which is the outcome the condition exists to
# prevent.
DEEPSEEK_BOUNDARY_DIGEST = "281192b3ef8ab151f9f440e3758554db8764334f28731a4ceb5f5ba3d17e8974"

# The engine's entire authorized dependency surface. **An allowlist, following
# `tests/test_indexer.py`'s stated reasoning** — *"An allowlist fails on any
# import nobody thought to forbid, which a denylist cannot"* — and it is one
# standard-library module. It is derived from what the engine actually needed
# rather than copied: `math` is what `_macro` uses for `fsum`, and nothing else
# was reached for. `json` is deliberately **not** allowed — this engine
# serializes nothing.
ENGINE_IMPORT_ALLOWLIST = {"math"}

# Named because each is specifically barred and each is a plausible thing for a
# later edit to reach for. **RO-18 Decision 2** (no DeepEval), **Decision 3** (no
# Promptfoo), **Decision 7** (no Ragas for M2-08, no LangChain/LangGraph, no
# OpenAI SDK, no new HTTP SDK, no orchestration, no model router, no new
# embedding or vector-store exception), **Decision 13** (no agent framework, no
# production observability, no OpenTelemetry).
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
    "opentelemetry",
)

# The first line of each proposition's prompt. The recording judge below routes
# on these, so `test_m208_each_proposition_is_identifiable_by_its_opening_line`
# pins them: if a prompt's opening changes, the routing would silently
# misclassify and the isolation specifications would assert about the wrong
# prompts.
P1_CLAIMS = "Break the answer below into the individual claims it makes."
P2_SUPPORT = "You are judging whether a context supports a claim."
P3_ATTRIBUTION = "You are judging whether a single passage supports a claim on its own."
P4_RELEVANCY = "You are judging whether an answer addresses the question that was asked."

PROPOSITIONS = {
    "P1": P1_CLAIMS,
    "P2": P2_SUPPORT,
    "P3": P3_ATTRIBUTION,
    "P4": P4_RELEVANCY,
}


# ---------------------------------------------------------------------------
# Probe material — `docs/M2.08_Metric_Semantics_Report.md` §10's inputs
# ---------------------------------------------------------------------------
#
# The passages and claims are chosen pairwise non-overlapping: no claim is a
# substring of another claim or of any passage. That is not cosmetic — the
# recording judge identifies which claim a prompt is about by containment, and
# raises if a prompt matches more than one, so the probe data itself is part of
# what makes the isolation specifications sound.

APPLE_FOUNDED = "Steve Jobs founded Apple."
APPLE_DIED = "Steve Jobs died in 2011."
APPLE_CLAIM = "Apple's founder passed away in 2011."

YEARS_PASSAGE = (
    "Quality Engineering leader with around 7.5 years of experience across QA "
    "and data validation."
)
YEARS_CLAIM = "Karthik has around 7.5 years of experience."
PROMPTFOO_CLAIM = "Karthik is an expert in Promptfoo."
FIFTEEN_CLAIM = "Karthik has 15 years of experience."

TEAM_PASSAGE = (
    "Led QA delivery for the analytics platform, managing a cross-functional "
    "team of 5."
)
TEAM_CLAIM = "Karthik led a team of 5 engineers."

ROLE_PASSAGE = (
    "Karthik was QA Lead and Test Module Lead at Happiest Minds Technologies, "
    "Bengaluru."
)
DATES_PASSAGE = "He held that role from Sep 2023 to Apr 2025."
ROLE_CLAIM = "Karthik was QA Lead at Happiest Minds from Sep 2023 to Apr 2025."

ABSTENTION_TEXT = (
    "The available context does not contain enough information to answer this "
    "question."
)


# ---------------------------------------------------------------------------
# Scripted judges — the whole of the non-determinism, held still
# ---------------------------------------------------------------------------


class ProbeJudge:
    """A judge that answers from per-proposition tables and records every call.

    Substitutes for the provider at the engine's one injected seam. It holds no
    endpoint, no credential, no client and no network primitive — there is
    nothing here for a specification to reach a provider through, which is the
    property RO-14 Decision 2 requires of this suite.

    **It records the proposition and the exact prompt of every invocation**,
    which is what family 3 inspects. RO-18's isolation requirements are
    statements about what a judge was *shown*, and a metric value cannot witness
    them: a Groundedness figure computed from prompts that carried the whole
    context would look identical to one computed correctly.

    `grounding` maps a claim to the passage texts that carry it **on their own**;
    a claim absent from the mapping is carried by no single passage, which is
    the FG-1 / FG-7 shape. `support` maps a claim to its whole-context verdict,
    and the two are deliberately independent inputs — an engine that derived one
    from the other would pass no probe here.
    """

    def __init__(self, claims=(), support=None, grounding=None, relevancy=None):
        self.claims = list(claims)
        self.support = dict(support or {})
        self.grounding = {
            claim: tuple(passages) for claim, passages in (grounding or {}).items()
        }
        self.relevancy = tuple(relevancy) if relevancy else None
        self.calls = []

    def __call__(self, prompt):
        proposition = self._classify(prompt)
        self.calls.append((proposition, prompt))

        if proposition == "P1":
            return "\n".join(self.claims)
        if proposition == "P2":
            return self.support[self._claim_of(prompt)]
        if proposition == "P3":
            carriers = self.grounding.get(self._claim_of(prompt), ())
            return SUPPORTED if any(text in prompt for text in carriers) else NOT_SUPPORTED
        return "\n".join(self.relevancy)

    def prompts(self, proposition):
        """Every prompt this judge received for one proposition, in call order."""
        return [prompt for name, prompt in self.calls if name == proposition]

    def counts(self):
        """How many times each proposition was judged."""
        return {name: len(self.prompts(name)) for name in PROPOSITIONS}

    @staticmethod
    def _classify(prompt):
        for name, opening in PROPOSITIONS.items():
            if prompt.startswith(opening):
                return name
        raise AssertionError("The judge received an unrecognized proposition.")

    def _claim_of(self, prompt):
        """Which claim this prompt is about — and proof that it is about one.

        A prompt matching two claims would mean a judgement saw a claim it was
        not asked about, so ambiguity fails here rather than being resolved.
        """
        matches = [claim for claim in self.claims if claim in prompt]
        if len(matches) != 1:
            raise AssertionError(
                f"A judged prompt matched {len(matches)} claims; exactly one is "
                f"required for the judgement to be about a single claim."
            )
        return matches[0]


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


def answer_case(
    identity="case",
    question="How many years of experience does Karthik have?",
    answer="Karthik has around 7.5 years of experience.",
    context=(YEARS_PASSAGE,),
):
    """One `Answer`-outcome evaluation case, with passages named by position."""
    return {
        "id": identity,
        "question": question,
        "answer_text": answer,
        "outcome": ANSWER_OUTCOME,
        "context": [
            {"chunk_id": f"chunkid{index}", "text": text}
            for index, text in enumerate(context, start=1)
        ],
    }


def abstain_case(identity="abstained", context=(YEARS_PASSAGE,)):
    """One `Abstain`-outcome case — an answer that asserts nothing (§9.3)."""
    return {
        "id": identity,
        "question": "What salary did Karthik earn at Happiest Minds Technologies?",
        "answer_text": ABSTENTION_TEXT,
        "outcome": ABSTAIN_OUTCOME,
        "context": [
            {"chunk_id": f"chunkid{index}", "text": text}
            for index, text in enumerate(context, start=1)
        ],
    }


def single_row(case, judge):
    """`compute` over one case, returning its per-case row."""
    return compute([case], judge)["per_case"][0]


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
# 1. Faithfulness — "of everything the model claimed, how much is supported
#    or entailed by the context?"
# ---------------------------------------------------------------------------


def test_m208_an_answer_whose_every_claim_is_supported_is_fully_faithful():
    judge = ProbeJudge(
        claims=[YEARS_CLAIM],
        support={YEARS_CLAIM: SUPPORTED},
        grounding={YEARS_CLAIM: (YEARS_PASSAGE,)},
        relevancy=(DIRECT, COMPLETE, ONLY),
    )

    assert single_row(answer_case(), judge)["faithfulness"] == 1.0


def test_m208_only_the_supported_verdict_counts_as_faithful():
    """`PARTIALLY_SUPPORTED`, `CONTRADICTED` and `NOT_SUPPORTED` are all
    unfaithful — `docs/M2.08_Metric_Semantics_Report.md` §6.1: the three are kept
    distinct because Hallucination Rate distinguishes them, not because
    Faithfulness does."""
    for verdict in (PARTIALLY_SUPPORTED, CONTRADICTED, NOT_SUPPORTED):
        judge = ProbeJudge(
            claims=[YEARS_CLAIM],
            support={YEARS_CLAIM: verdict},
            relevancy=(DIRECT, COMPLETE, ONLY),
        )
        assert single_row(answer_case(), judge)["faithfulness"] == 0.0, verdict


def test_m208_faithfulness_is_the_proportion_of_claims_not_of_answers():
    judge = ProbeJudge(
        claims=[YEARS_CLAIM, PROMPTFOO_CLAIM, TEAM_CLAIM],
        support={
            YEARS_CLAIM: SUPPORTED,
            PROMPTFOO_CLAIM: NOT_SUPPORTED,
            TEAM_CLAIM: SUPPORTED,
        },
        relevancy=(DIRECT, COMPLETE, ONLY),
    )
    row = single_row(answer_case(context=(YEARS_PASSAGE, TEAM_PASSAGE)), judge)

    assert row["claims_total"] == 3
    assert row["claims_faithful"] == 2
    assert row["faithfulness"] == round(2 / 3, 4)


# ---------------------------------------------------------------------------
# 2. Groundedness — "can the claim be traced to one specific, citable passage?"
# ---------------------------------------------------------------------------


def test_m208_a_claim_one_passage_carries_alone_is_grounded_and_names_it():
    judge = ProbeJudge(
        claims=[YEARS_CLAIM],
        support={YEARS_CLAIM: SUPPORTED},
        grounding={YEARS_CLAIM: (YEARS_PASSAGE,)},
        relevancy=(DIRECT, COMPLETE, ONLY),
    )
    row = single_row(answer_case(context=(TEAM_PASSAGE, YEARS_PASSAGE)), judge)

    assert row["groundedness"] == 1.0
    assert row["claims"][0]["grounding_chunk_id"] == "chunkid2"


def test_m208_grounding_stops_at_the_first_passage_that_carries_the_claim():
    """The existential is spent, not the whole scan.

    Grounding asks whether **one** passage carries the claim, so a later passage
    cannot change the verdict. This spends strictly fewer judgements and changes
    no judgement's inputs — the only optimization available that does not widen
    what a judge is shown.
    """
    judge = ProbeJudge(
        claims=[YEARS_CLAIM],
        support={YEARS_CLAIM: SUPPORTED},
        grounding={YEARS_CLAIM: (YEARS_PASSAGE,)},
        relevancy=(DIRECT, COMPLETE, ONLY),
    )
    row = single_row(
        answer_case(context=(YEARS_PASSAGE, TEAM_PASSAGE, ROLE_PASSAGE)), judge
    )

    assert judge.counts()["P3"] == 1
    assert [passage["chunk_id"] for passage in row["claims"][0]["passages"]] == ["chunkid1"]


def test_m208_an_ungrounded_claim_records_every_passage_that_failed_to_carry_it():
    judge = ProbeJudge(
        claims=[APPLE_CLAIM],
        support={APPLE_CLAIM: SUPPORTED},
        relevancy=(DIRECT, COMPLETE, ONLY),
    )
    row = single_row(
        answer_case(answer=APPLE_CLAIM, context=(APPLE_FOUNDED, APPLE_DIED)), judge
    )

    assert judge.counts()["P3"] == 2
    assert [passage["verdict"] for passage in row["claims"][0]["passages"]] == [
        NOT_SUPPORTED,
        NOT_SUPPORTED,
    ]
    assert row["claims"][0]["grounding_chunk_id"] is None


# ---------------------------------------------------------------------------
# 3. Hallucination Rate — "of everything claimed, how much was fabricated
#    or unsupported?"
# ---------------------------------------------------------------------------


def test_m208_only_the_unsupported_and_contradicted_verdicts_are_hallucinated():
    """`docs/AI_Quality_Metrics_Reference.md` §Layer 4 gives one bucket —
    *"fabricated **or** unsupported"* — and `docs/glossary.md` fixes the
    fabrication half as *"not present in the retrieved context at all"*."""
    assert set(HALLUCINATED_VERDICTS) == {NOT_SUPPORTED, CONTRADICTED}

    for verdict in SUPPORT_VERDICTS:
        judge = ProbeJudge(
            claims=[YEARS_CLAIM],
            support={YEARS_CLAIM: verdict},
            relevancy=(DIRECT, COMPLETE, ONLY),
        )
        row = single_row(answer_case(), judge)
        assert row["hallucination_rate"] == (
            1.0 if verdict in (NOT_SUPPORTED, CONTRADICTED) else 0.0
        ), verdict


def test_m208_contradiction_and_fabrication_count_alike_but_are_recorded_apart():
    """Both enter the numerator; the verdict that produced each stays visible.

    RO-18 Decision 8 requires M2-08 to *"preserve enough evidence to explain a
    metric result"*, and a contradiction is a different failure from a
    fabrication even though the rate treats them alike.
    """
    judge = ProbeJudge(
        claims=[PROMPTFOO_CLAIM, FIFTEEN_CLAIM],
        support={PROMPTFOO_CLAIM: NOT_SUPPORTED, FIFTEEN_CLAIM: CONTRADICTED},
        relevancy=(DIRECT, COMPLETE, ONLY),
    )
    row = single_row(answer_case(), judge)

    assert row["hallucination_rate"] == 1.0
    assert [claim["support_verdict"] for claim in row["claims"]] == [
        NOT_SUPPORTED,
        CONTRADICTED,
    ]


def test_m208_the_hallucination_denominator_is_every_claim_the_answer_made():
    judge = ProbeJudge(
        claims=[YEARS_CLAIM, PROMPTFOO_CLAIM, FIFTEEN_CLAIM],
        support={
            YEARS_CLAIM: SUPPORTED,
            PROMPTFOO_CLAIM: NOT_SUPPORTED,
            FIFTEEN_CLAIM: CONTRADICTED,
        },
        relevancy=(DIRECT, COMPLETE, ONLY),
    )
    row = single_row(answer_case(), judge)

    assert row["claims_total"] == 3
    assert row["claims_hallucinated"] == 2
    assert row["hallucination_rate"] == round(2 / 3, 4)


# ---------------------------------------------------------------------------
# 4. Answer Relevancy — "does the answer directly, completely and only
#    address what was asked?"
# ---------------------------------------------------------------------------


def test_m208_answer_relevancy_holds_only_when_all_three_conjuncts_hold():
    for verdicts, expected in (
        ((DIRECT, COMPLETE, ONLY), True),
        ((NOT_DIRECT, COMPLETE, ONLY), False),
        ((DIRECT, NOT_COMPLETE, ONLY), False),
        ((DIRECT, COMPLETE, NOT_ONLY), False),
        ((NOT_DIRECT, NOT_COMPLETE, NOT_ONLY), False),
    ):
        judge = ProbeJudge(
            claims=[YEARS_CLAIM],
            support={YEARS_CLAIM: SUPPORTED},
            grounding={YEARS_CLAIM: (YEARS_PASSAGE,)},
            relevancy=verdicts,
        )
        assert single_row(answer_case(), judge)["answer_relevancy"] is expected, verdicts


def test_m208_the_three_conjunct_verdicts_are_published_as_evidence():
    """`docs/M2.08_Metric_Semantics_Report.md` §6.4 — the conjuncts are reported
    separately so a failure of `ONLY` alone is distinguishable from a failure of
    all three, without a weighting or a score scale being invented."""
    judge = ProbeJudge(
        claims=[YEARS_CLAIM],
        support={YEARS_CLAIM: SUPPORTED},
        grounding={YEARS_CLAIM: (YEARS_PASSAGE,)},
        relevancy=(DIRECT, COMPLETE, NOT_ONLY),
    )
    row = single_row(answer_case(), judge)

    assert row["relevancy_verdicts"] == {
        "direct": DIRECT,
        "complete": COMPLETE,
        "only": NOT_ONLY,
    }


def test_m208_answer_relevancy_is_judged_once_per_answer_not_once_per_claim():
    judge = ProbeJudge(
        claims=[YEARS_CLAIM, PROMPTFOO_CLAIM, TEAM_CLAIM],
        support={
            YEARS_CLAIM: SUPPORTED,
            PROMPTFOO_CLAIM: SUPPORTED,
            TEAM_CLAIM: SUPPORTED,
        },
        relevancy=(DIRECT, COMPLETE, ONLY),
    )
    compute([answer_case()], judge)

    assert judge.counts()["P4"] == 1
    assert judge.counts()["P1"] == 1
    assert judge.counts()["P2"] == 3


# ---------------------------------------------------------------------------
# 5. The frozen semantic probes — `docs/M2.08_Metric_Semantics_Report.md` §10
# ---------------------------------------------------------------------------


def test_m208_probe_fg1_a_multi_hop_claim_is_faithful_but_not_grounded():
    """**FG-1 — the Faithfulness / Groundedness gate.**

    `docs/AI_Quality_Metrics_Reference.md` §Layer 4, verbatim: *"'Apple's founder
    passed away in 2011,' derived by combining two separate sentences —
    **faithful, but weaker on strict per-claim traceability**"*.
    `docs/glossary.md`: faithful *"even if derived by combining multiple
    sentences"*; grounded requires *"one specific, citable piece of evidence"*.

    An implementation that asked one question for both metrics returns the same
    value here. This probe is why it cannot.
    """
    judge = ProbeJudge(
        claims=[APPLE_CLAIM],
        support={APPLE_CLAIM: SUPPORTED},
        grounding={},
        relevancy=(DIRECT, COMPLETE, ONLY),
    )
    row = single_row(
        answer_case(
            question="When did Apple's founder die?",
            answer=APPLE_CLAIM,
            context=(APPLE_FOUNDED, APPLE_DIED),
        ),
        judge,
    )

    assert row["faithfulness"] == 1.0
    assert row["groundedness"] == 0.0
    assert row["hallucination_rate"] == 0.0


def test_m208_probe_fg7_a_second_multi_hop_case_separates_them_again():
    """**FG-7** — the same gate on repository corpus subject matter, so the
    discrimination is not carried by one borrowed example."""
    judge = ProbeJudge(
        claims=[ROLE_CLAIM],
        support={ROLE_CLAIM: SUPPORTED},
        grounding={},
        relevancy=(DIRECT, COMPLETE, ONLY),
    )
    row = single_row(
        answer_case(
            question="What role did Karthik hold at Happiest Minds, and when?",
            answer=ROLE_CLAIM,
            context=(ROLE_PASSAGE, DATES_PASSAGE),
        ),
        judge,
    )

    assert row["faithfulness"] == 1.0
    assert row["groundedness"] == 0.0
    assert row["hallucination_rate"] == 0.0


def test_m208_probe_fg2_a_directly_supported_claim_is_faithful_and_grounded():
    """**FG-2** — the metrics must agree where the repository says they agree."""
    judge = ProbeJudge(
        claims=[YEARS_CLAIM],
        support={YEARS_CLAIM: SUPPORTED},
        grounding={YEARS_CLAIM: (YEARS_PASSAGE,)},
        relevancy=(DIRECT, COMPLETE, ONLY),
    )
    row = single_row(answer_case(), judge)

    assert row["faithfulness"] == 1.0
    assert row["groundedness"] == 1.0
    assert row["hallucination_rate"] == 0.0


def test_m208_probe_fg3_a_fabricated_claim_is_neither_and_is_hallucinated():
    """**FG-3** — `docs/AI_Quality_Metrics_Reference.md` §Layer 4's own
    Faithfulness example: *"Resume never mentions Promptfoo; answer claims
    'expert in Promptfoo'"*."""
    judge = ProbeJudge(
        claims=[PROMPTFOO_CLAIM],
        support={PROMPTFOO_CLAIM: NOT_SUPPORTED},
        relevancy=(DIRECT, COMPLETE, ONLY),
    )
    row = single_row(answer_case(answer=PROMPTFOO_CLAIM), judge)

    assert row["faithfulness"] == 0.0
    assert row["groundedness"] == 0.0
    assert row["hallucination_rate"] == 1.0


def test_m208_probe_fg4_a_contradicted_claim_is_neither_and_is_hallucinated():
    """**FG-4** — Groundedness is *"stricter than 'not contradicted'"*, so a
    contradicted claim fails even the weak floor, and *"fabricated **or
    unsupported**"* counts it in the hallucination numerator."""
    judge = ProbeJudge(
        claims=[FIFTEEN_CLAIM],
        support={FIFTEEN_CLAIM: CONTRADICTED},
        relevancy=(DIRECT, COMPLETE, ONLY),
    )
    row = single_row(answer_case(answer=FIFTEEN_CLAIM), judge)

    assert row["faithfulness"] == 0.0
    assert row["groundedness"] == 0.0
    assert row["hallucination_rate"] == 1.0


def test_m208_probe_fg5_a_partially_supported_claim_is_unfaithful_yet_not_hallucinated():
    """**FG-5 — the probe that forbids `hallucination_rate = 1 - faithfulness`.**

    `docs/altm.md` §6 and `docs/AI_Quality_Metrics_Reference.md` §Layer 4:
    Hallucination Rate is a *"near-complement of Faithfulness in the simple
    case; **not guaranteed to sum to 100% once partial/ambiguous claims
    exist**"*. A claim the context carries only partly is not fully entailed, so
    it is not faithful; and it is not *"fabricated"* or *"not present in the
    context at all"*, so it is not hallucinated.

    A `1 - faithfulness` implementation returns `1.0` here. The definition
    returns `0.0`, and `faithfulness + hallucination_rate` is `0.0`.
    """
    judge = ProbeJudge(
        claims=[TEAM_CLAIM],
        support={TEAM_CLAIM: PARTIALLY_SUPPORTED},
        relevancy=(DIRECT, COMPLETE, ONLY),
    )
    row = single_row(
        answer_case(
            question="How many engineers did Karthik lead?",
            answer=TEAM_CLAIM,
            context=(TEAM_PASSAGE,),
        ),
        judge,
    )

    assert row["faithfulness"] == 0.0
    assert row["groundedness"] == 0.0
    assert row["hallucination_rate"] == 0.0
    assert row["faithfulness"] + row["hallucination_rate"] < 1.0


def test_m208_probe_fg6_a_multi_claim_answer_scores_the_proportion():
    """**FG-6** — one supported claim and one fabricated claim."""
    judge = ProbeJudge(
        claims=[YEARS_CLAIM, PROMPTFOO_CLAIM],
        support={YEARS_CLAIM: SUPPORTED, PROMPTFOO_CLAIM: NOT_SUPPORTED},
        grounding={YEARS_CLAIM: (YEARS_PASSAGE,)},
        relevancy=(DIRECT, COMPLETE, ONLY),
    )
    row = single_row(
        answer_case(answer=f"{YEARS_CLAIM} {PROMPTFOO_CLAIM}"), judge
    )

    assert row["faithfulness"] == 0.5
    assert row["groundedness"] == 0.5
    assert row["hallucination_rate"] == 0.5


def test_m208_probe_h1_an_answer_with_no_unsupported_claim_rates_zero():
    judge = ProbeJudge(
        claims=[YEARS_CLAIM, ROLE_CLAIM],
        support={YEARS_CLAIM: SUPPORTED, ROLE_CLAIM: SUPPORTED},
        grounding={YEARS_CLAIM: (YEARS_PASSAGE,), ROLE_CLAIM: (ROLE_PASSAGE,)},
        relevancy=(DIRECT, COMPLETE, ONLY),
    )
    row = single_row(answer_case(context=(YEARS_PASSAGE, ROLE_PASSAGE)), judge)

    assert row["hallucination_rate"] == 0.0
    assert row["faithfulness"] == 1.0


def test_m208_probe_h2_multiple_unsupported_claims_raise_the_rate():
    judge = ProbeJudge(
        claims=[YEARS_CLAIM, PROMPTFOO_CLAIM, FIFTEEN_CLAIM],
        support={
            YEARS_CLAIM: SUPPORTED,
            PROMPTFOO_CLAIM: NOT_SUPPORTED,
            FIFTEEN_CLAIM: CONTRADICTED,
        },
        grounding={YEARS_CLAIM: (YEARS_PASSAGE,)},
        relevancy=(DIRECT, COMPLETE, ONLY),
    )
    row = single_row(answer_case(), judge)

    assert row["hallucination_rate"] == round(2 / 3, 4)
    assert row["faithfulness"] == round(1 / 3, 4)


def test_m208_probe_ar1_a_faithful_grounded_answer_can_still_be_irrelevant():
    """**AR-1** — `docs/P3.7.1_Manual_Review_Report.md` Finding 2, verbatim:
    *"the answer is **irrelevant**, not **unfaithful**"*, and
    `ALTM-FINAL-ANSWER-1`'s symptom *"Faithful, grounded, but doesn't answer the
    actual question"*.

    The claim here is supported and grounded, and the answer is not relevant —
    which is why Answer Relevancy cannot be derived from the other three.
    """
    judge = ProbeJudge(
        claims=[YEARS_CLAIM],
        support={YEARS_CLAIM: SUPPORTED},
        grounding={YEARS_CLAIM: (YEARS_PASSAGE,)},
        relevancy=(NOT_DIRECT, NOT_COMPLETE, NOT_ONLY),
    )
    row = single_row(
        answer_case(question="Describe your Rust programming experience."), judge
    )

    assert row["faithfulness"] == 1.0
    assert row["groundedness"] == 1.0
    assert row["hallucination_rate"] == 0.0
    assert row["answer_relevancy"] is False


def test_m208_probe_ar3_the_only_conjunct_can_fail_alone():
    """**AR-3** — `docs/AI_Quality_Metrics_Reference.md` §Layer 5's own example:
    *"the same fact plus unrequested extra biographical detail — the second
    scores lower despite being equally true"*."""
    judge = ProbeJudge(
        claims=[YEARS_CLAIM],
        support={YEARS_CLAIM: SUPPORTED},
        grounding={YEARS_CLAIM: (YEARS_PASSAGE,)},
        relevancy=(DIRECT, COMPLETE, NOT_ONLY),
    )
    row = single_row(answer_case(), judge)

    assert row["answer_relevancy"] is False
    assert row["relevancy_verdicts"]["direct"] == DIRECT
    assert row["relevancy_verdicts"]["complete"] == COMPLETE


def test_m208_probe_ar4_the_complete_conjunct_can_fail_alone():
    """**AR-4** — a question asking two things, answered on one."""
    judge = ProbeJudge(
        claims=[YEARS_CLAIM],
        support={YEARS_CLAIM: SUPPORTED},
        grounding={YEARS_CLAIM: (YEARS_PASSAGE,)},
        relevancy=(DIRECT, NOT_COMPLETE, ONLY),
    )
    row = single_row(
        answer_case(question="Which databases and which CI tools has Karthik used?"),
        judge,
    )

    assert row["answer_relevancy"] is False
    assert row["relevancy_verdicts"]["complete"] == NOT_COMPLETE


def test_m208_probe_ar5_true_information_answering_a_different_question_is_irrelevant():
    """**AR-5** — faithful, grounded, true, and not what was asked."""
    judge = ProbeJudge(
        claims=[ROLE_CLAIM],
        support={ROLE_CLAIM: SUPPORTED},
        grounding={ROLE_CLAIM: (ROLE_PASSAGE,)},
        relevancy=(NOT_DIRECT, NOT_COMPLETE, NOT_ONLY),
    )
    row = single_row(
        answer_case(answer=ROLE_CLAIM, context=(ROLE_PASSAGE,)), judge
    )

    assert row["faithfulness"] == 1.0
    assert row["answer_relevancy"] is False
    assert row["relevancy_verdicts"]["direct"] == NOT_DIRECT


def test_m208_probe_ar7_adjacent_material_that_is_not_the_question_is_irrelevant():
    """**AR-7** — related, arguably useful, and still not the question asked."""
    judge = ProbeJudge(
        claims=[ROLE_CLAIM],
        support={ROLE_CLAIM: SUPPORTED},
        grounding={ROLE_CLAIM: (ROLE_PASSAGE,)},
        relevancy=(NOT_DIRECT, NOT_COMPLETE, ONLY),
    )
    row = single_row(
        answer_case(
            question="Which Kubernetes clusters has Karthik managed?",
            answer=ROLE_CLAIM,
            context=(ROLE_PASSAGE,),
        ),
        judge,
    )

    assert row["answer_relevancy"] is False
    assert row["relevancy_verdicts"]["only"] == ONLY


def test_m208_probe_ar6_a_hallucinated_answer_can_be_fully_relevant():
    """**AR-6 — independence from truthfulness, in the direction that is easy to
    get wrong.**

    `docs/AI_Quality_Metrics_Reference.md` §Layer 5: *"independent of whether
    it's true"*; `docs/altm.md` §6: *"the only metric independent of
    truthfulness"*; RO-18 Decision 8: relevancy *"MUST NOT be collapsed into
    factual correctness or faithfulness"*.

    Any implementation scoring this `False` has collapsed relevancy into
    correctness.
    """
    judge = ProbeJudge(
        claims=[FIFTEEN_CLAIM],
        support={FIFTEEN_CLAIM: CONTRADICTED},
        relevancy=(DIRECT, COMPLETE, ONLY),
    )
    row = single_row(answer_case(answer=FIFTEEN_CLAIM), judge)

    assert row["hallucination_rate"] == 1.0
    assert row["faithfulness"] == 0.0
    assert row["groundedness"] == 0.0
    assert row["answer_relevancy"] is True


def test_m208_probe_ar8_relevancy_over_an_abstention_stays_undefined():
    """**AR-8 — the frozen report's finding U-3, carried into the implementation
    unresolved.**

    No repository authority defines whether a conforming abstention *"directly,
    completely and only"* addresses the question it declines. Scoring it `0`
    would penalize the behaviour `expected_outcome == "Abstain"` requires;
    scoring it `1` would invent a rule. **The gap is recorded, not filled**, and
    no judgement is spent discovering that.
    """
    judge = ProbeJudge(relevancy=(DIRECT, COMPLETE, ONLY))
    row = single_row(abstain_case(), judge)

    assert row["answer_relevancy"] is None
    assert "U-3" in row["relevancy_unmeasured_reason"]
    assert judge.counts()["P4"] == 0


# ---------------------------------------------------------------------------
# 6. The Faithfulness / Groundedness invariant
# ---------------------------------------------------------------------------


def test_m208_groundedness_never_exceeds_faithfulness_across_the_probe_set():
    """`Grounded(claim) => Faithful(claim)`, therefore
    `groundedness <= faithfulness` — `docs/M2.08_Metric_Semantics_Report.md`
    §7.2, and what *"stricter than Faithfulness"* means arithmetically."""
    cases = [
        answer_case(identity="fg1", answer=APPLE_CLAIM, context=(APPLE_FOUNDED, APPLE_DIED)),
        answer_case(identity="fg2"),
        answer_case(identity="fg3", answer=PROMPTFOO_CLAIM),
        answer_case(identity="fg5", answer=TEAM_CLAIM, context=(TEAM_PASSAGE,)),
    ]
    judge = ProbeJudge(
        claims=[APPLE_CLAIM],
        support={APPLE_CLAIM: SUPPORTED},
        relevancy=(DIRECT, COMPLETE, ONLY),
    )
    # One claim per case keeps the judge scriptable; each case is run alone so
    # its own claim and support verdict apply.
    scripts = (
        ([APPLE_CLAIM], {APPLE_CLAIM: SUPPORTED}, {}),
        ([YEARS_CLAIM], {YEARS_CLAIM: SUPPORTED}, {YEARS_CLAIM: (YEARS_PASSAGE,)}),
        ([PROMPTFOO_CLAIM], {PROMPTFOO_CLAIM: NOT_SUPPORTED}, {}),
        ([TEAM_CLAIM], {TEAM_CLAIM: PARTIALLY_SUPPORTED}, {}),
    )

    for case, (claims, support, grounding) in zip(cases, scripts):
        judge = ProbeJudge(
            claims=claims,
            support=support,
            grounding=grounding,
            relevancy=(DIRECT, COMPLETE, ONLY),
        )
        row = single_row(case, judge)
        assert row["groundedness"] <= row["faithfulness"], case["id"]


def test_m208_a_grounded_but_unfaithful_claim_is_flagged_as_an_instrument_fault():
    """The combination the definitions forbid is **recorded, not repaired**.

    Repairing it would fabricate a verdict, and raising would discard a whole
    evaluation over one judgement. It is flagged per claim and counted per case
    — the diagnostic route `docs/M2.07_Native_Context_Metrics_Report.md` §9 used
    when two metrics contradicted each other.
    """
    judge = ProbeJudge(
        claims=[YEARS_CLAIM],
        support={YEARS_CLAIM: NOT_SUPPORTED},
        grounding={YEARS_CLAIM: (YEARS_PASSAGE,)},
        relevancy=(DIRECT, COMPLETE, ONLY),
    )
    report = compute([answer_case()], judge)
    row = report["per_case"][0]

    assert row["claims"][0]["grounded"] is True
    assert row["claims"][0]["faithful"] is False
    assert row["claims"][0]["instrument_inconsistency"] is True
    assert row["instrument_inconsistencies"] == 1
    assert report["instrument"]["grounded_but_not_faithful"] == 1


def test_m208_a_consistent_run_reports_no_instrument_fault():
    judge = ProbeJudge(
        claims=[YEARS_CLAIM],
        support={YEARS_CLAIM: SUPPORTED},
        grounding={YEARS_CLAIM: (YEARS_PASSAGE,)},
        relevancy=(DIRECT, COMPLETE, ONLY),
    )

    assert compute([answer_case()], judge)["instrument"]["grounded_but_not_faithful"] == 0


# ---------------------------------------------------------------------------
# 7. Abstention — zero claims, and no invented score
# ---------------------------------------------------------------------------


def test_m208_an_abstention_carries_no_claim_metric_and_spends_no_judgement():
    """`docs/GENERATION_CONTRACT.md` **G-8** and §9.3: the abstention text
    *"asserts nothing about the corpus"* and `statements` is empty exactly then.
    No claim means no denominator — and an absent denominator is **not** a
    measurement of zero."""
    judge = ProbeJudge()
    row = single_row(abstain_case(), judge)

    assert row["claims_total"] == 0
    assert row["faithfulness"] is None
    assert row["groundedness"] is None
    assert row["hallucination_rate"] is None
    assert row["unmeasured_reason"]
    assert judge.calls == []


def test_m208_an_abstain_only_dataset_reports_no_score_rather_than_zero():
    judge = ProbeJudge()
    report = compute([abstain_case("a"), abstain_case("b")], judge)

    for metric in ("faithfulness", "groundedness", "hallucination_rate"):
        assert report[metric][f"{metric}_macro"] is None
        assert report[metric][f"{metric}_micro"] is None
        assert report[metric]["cases_measured"] == 0
        assert report[metric]["cases_without_claims"] == 2
    assert report["answer_relevancy"]["answer_relevancy"] is None
    assert report["answer_relevancy"]["cases_undefined"] == 2


def test_m208_a_mixed_dataset_is_partitioned_rather_than_diluted():
    """The Abstain cases are excluded from the measured set and **counted**, so
    both figures can be read against the number of cases that had a
    denominator — `docs/M2.07_Native_Context_Metrics_Report.md` §4.1's precedent,
    carried forward."""
    judge = ProbeJudge(
        claims=[YEARS_CLAIM],
        support={YEARS_CLAIM: SUPPORTED},
        grounding={YEARS_CLAIM: (YEARS_PASSAGE,)},
        relevancy=(DIRECT, COMPLETE, ONLY),
    )
    report = compute([answer_case("answered"), abstain_case("abstained")], judge)

    assert report["faithfulness"]["cases_evaluated"] == 2
    assert report["faithfulness"]["cases_measured"] == 1
    assert report["faithfulness"]["cases_without_claims"] == 1
    assert report["faithfulness"]["faithfulness_macro"] == 1.0
    assert report["faithfulness"]["faithfulness_micro"] == 1.0
    assert report["answer_relevancy"]["cases_measured"] == 1
    assert report["answer_relevancy"]["cases_undefined"] == 1


# ---------------------------------------------------------------------------
# 8. Judge-input isolation — what each proposition was actually shown
# ---------------------------------------------------------------------------
#
# These inspect the prompts a recording judge received. A metric value cannot
# witness an isolation property: a Groundedness figure computed from prompts
# carrying the whole context looks identical to one computed correctly.

ISOLATION_QUESTION = "QUESTIONMARKER when did the founder die?"
ISOLATION_ANSWER = "ANSWERMARKER the founder passed away in 2011."
ISOLATION_CLAIM = "CLAIMMARKER Apple's founder died in 2011."
ISOLATION_PASSAGES = (
    "PASSAGEALPHA Steve Jobs founded Apple.",
    "PASSAGEBETA Steve Jobs died in 2011.",
    "PASSAGEGAMMA an unrelated corpus line.",
)
ISOLATION_CHUNK_IDS = ("chunkid1", "chunkid2", "chunkid3")


def isolation_run():
    """One `compute` over a case whose every input carries a unique marker."""
    case = answer_case(
        identity="isolation",
        question=ISOLATION_QUESTION,
        answer=ISOLATION_ANSWER,
        context=ISOLATION_PASSAGES,
    )
    judge = ProbeJudge(
        claims=[ISOLATION_CLAIM],
        support={ISOLATION_CLAIM: SUPPORTED},
        grounding={},
        relevancy=(DIRECT, COMPLETE, ONLY),
    )
    compute([case], judge)
    return judge


def test_m208_each_proposition_is_identifiable_by_its_opening_line():
    """Pins the routing the recording judge depends on.

    If a prompt's opening line changed, the judge would misclassify silently and
    every isolation specification below would assert about the wrong prompts.
    """
    assert claim_prompt("q", "a").startswith(P1_CLAIMS)
    assert support_prompt("c", "ctx").startswith(P2_SUPPORT)
    assert attribution_prompt("c", "p").startswith(P3_ATTRIBUTION)
    assert relevancy_prompt("q", "a").startswith(P4_RELEVANCY)
    assert len(set(PROPOSITIONS.values())) == 4


def test_m208_p1_claim_decomposition_sees_the_question_and_the_answer_only():
    """**P1 inputs: question, `answer_text`. Nothing else.**

    A decomposer that could see the context might suppress claims the context
    does not support, deflating the denominator and inflating Faithfulness in
    the system's favour. **The claim denominator must not be a function of the
    evidence the claims are then scored against.**
    """
    judge = isolation_run()
    prompt = judge.prompts("P1")[0]

    assert ISOLATION_QUESTION in prompt
    assert ISOLATION_ANSWER in prompt

    for passage in ISOLATION_PASSAGES:
        assert passage not in prompt
    for chunk_id in ISOLATION_CHUNK_IDS:
        assert chunk_id not in prompt
    for verdict in SUPPORT_VERDICTS:
        assert verdict not in prompt
    assert CONTEXT_SEPARATOR.join(ISOLATION_PASSAGES) not in prompt


def test_m208_p2_faithfulness_sees_the_claim_and_the_whole_assembled_context():
    """**P2 inputs: one claim, the whole context. Not the question, not ground
    truth, not the system's attribution, not a prior verdict.**

    The context block is asserted to be exactly the passages joined by
    `CONTEXT_SEPARATOR` — the value `sample_rag/context_builder.py` assembles
    with — so the frame Faithfulness judges is the frame the model was given.
    """
    judge = isolation_run()
    prompt = judge.prompts("P2")[0]

    assert ISOLATION_CLAIM in prompt
    assert CONTEXT_SEPARATOR.join(ISOLATION_PASSAGES) in prompt

    assert ISOLATION_QUESTION not in prompt
    assert ISOLATION_ANSWER not in prompt
    for chunk_id in ISOLATION_CHUNK_IDS:
        assert chunk_id not in prompt


def test_m208_p3_groundedness_sees_exactly_one_passage_and_cannot_reach_another():
    """**P3 inputs: one claim, exactly one passage.**

    The specification that makes Groundedness *Groundedness*. Every judgement is
    checked to contain its own passage and **none of the others**, so a judge
    could not have consulted a passage it was not asked about — which is the one
    property a correct Groundedness figure cannot itself witness.

    **No batching is used**, and this is why: batching claims or passages into
    one call would widen exactly one of P3's two inputs, and
    `docs/M2.08_Metric_Semantics_Report.md` §9 fixes both. The only optimization
    taken is the existential short-circuit, which changes no judgement's inputs.
    """
    judge = isolation_run()
    prompts = judge.prompts("P3")

    assert len(prompts) == len(ISOLATION_PASSAGES)

    for prompt, own in zip(prompts, ISOLATION_PASSAGES):
        assert own in prompt

        others = [passage for passage in ISOLATION_PASSAGES if passage != own]
        for other in others:
            assert other not in prompt, "a grounding judgement saw a second passage"

        assert CONTEXT_SEPARATOR.join(ISOLATION_PASSAGES) not in prompt
        assert ISOLATION_CLAIM in prompt
        assert ISOLATION_QUESTION not in prompt
        assert ISOLATION_ANSWER not in prompt
        for chunk_id in ISOLATION_CHUNK_IDS:
            assert chunk_id not in prompt
        # P2's own vocabulary appearing here would mean the whole-context
        # judgement had leaked into the per-passage one.
        assert PARTIALLY_SUPPORTED not in prompt
        assert CONTRADICTED not in prompt


def test_m208_p4_answer_relevancy_sees_the_question_and_the_answer_only():
    """**P4 inputs: question, `answer_text`. Never the context, never ground
    truth, never a claim-level verdict.**

    Either excluded input would let the judge grade truth, which
    `docs/AI_Quality_Metrics_Reference.md` §Layer 5 (*"independent of whether
    it's true"*) and `ALTM-FINAL-ANSWER-1` (*"not against truthfulness
    metrics"*) exclude, and RO-18 Decision 8 forbids by name.
    """
    judge = isolation_run()
    prompt = judge.prompts("P4")[0]

    assert ISOLATION_QUESTION in prompt
    assert ISOLATION_ANSWER in prompt

    for passage in ISOLATION_PASSAGES:
        assert passage not in prompt
    for chunk_id in ISOLATION_CHUNK_IDS:
        assert chunk_id not in prompt
    for verdict in SUPPORT_VERDICTS:
        assert verdict not in prompt
    assert ISOLATION_CLAIM not in prompt


def test_m208_the_propositions_cannot_accept_what_they_must_not_see():
    """The exclusions expressed as **signatures**, not as call-site discipline.

    `evaluation/context_metrics.py` established the pattern — a function with no
    parameter for retrieval output cannot receive it. Here: no proposition takes
    a reference answer, the system's attribution, a prior verdict or a case; P1
    and P4 take no context; P3 takes one passage.
    """
    assert list(inspect.signature(claim_prompt).parameters) == ["question", "answer_text"]
    assert list(inspect.signature(support_prompt).parameters) == ["claim", "context"]
    assert list(inspect.signature(attribution_prompt).parameters) == ["claim", "passage"]
    assert list(inspect.signature(relevancy_prompt).parameters) == ["question", "answer_text"]


def test_m208_the_judged_propositions_are_stated_in_one_place_and_are_pure():
    """Each proposition is one function returning one byte-identical string for
    given arguments, so what the judge is asked is reviewable in one place and
    cannot vary between calls."""
    assert claim_prompt("q", "a") == claim_prompt("q", "a")
    assert support_prompt("c", "x") == support_prompt("c", "x")
    assert attribution_prompt("c", "p") == attribution_prompt("c", "p")
    assert relevancy_prompt("q", "a") == relevancy_prompt("q", "a")


def test_m208_the_support_proposition_permits_combination_and_attribution_forbids_it():
    """The one sentence that is the whole difference between P2 and P3.

    `docs/glossary.md`: Faithfulness is satisfied *"by multi-hop reasoning across
    sources"*; Groundedness is *"weaker on claims that require combining sources
    without a single direct citation"*. If the prompts stopped saying so, a judge
    asked the same question twice would answer the stricter one twice and the two
    metrics would collapse — which is the FG-1 failure, caught here at the
    wording rather than at the number.
    """
    combining = support_prompt("c", "x")
    isolated = attribution_prompt("c", "p")

    assert "combining passages is allowed" in combining
    assert "on its own" in isolated
    assert "do not assume any other passage exists" in isolated
    assert "would need another passage alongside it" in isolated


def test_m208_the_relevancy_proposition_states_independence_from_truth():
    """`docs/AI_Quality_Metrics_Reference.md` §Layer 5's unique property, stated
    to the judge in **both** directions — the AR-1 and AR-6 probes at the level
    of the wording that produces them."""
    prompt = relevancy_prompt("q", "a")

    assert "Do NOT judge whether the answer is true" in prompt
    assert "false but addresses the question" in prompt
    assert "true but addresses a different question" in prompt


# ---------------------------------------------------------------------------
# 9. Reading what the judge answered — strict, total, payload-free
# ---------------------------------------------------------------------------


def test_m208_a_verdict_is_matched_exactly_and_not_by_containment():
    """A containment test would read `NOT_SUPPORTED` as `SUPPORTED` and
    `PARTIALLY_SUPPORTED` as either, silently inverting a verdict."""
    assert parse_verdict(NOT_SUPPORTED, SUPPORT_VERDICTS, "p") == NOT_SUPPORTED
    assert parse_verdict(PARTIALLY_SUPPORTED, SUPPORT_VERDICTS, "p") == PARTIALLY_SUPPORTED
    assert parse_verdict(SUPPORTED, ATTRIBUTION_VERDICTS, "p") == SUPPORTED

    with pytest.raises(GenerationMetricsError):
        parse_verdict(PARTIALLY_SUPPORTED, ATTRIBUTION_VERDICTS, "p")


def test_m208_verdict_formatting_is_normalized_but_content_is_not():
    assert parse_verdict("  supported.  ", SUPPORT_VERDICTS, "p") == SUPPORTED
    assert parse_verdict("**CONTRADICTED**", SUPPORT_VERDICTS, "p") == CONTRADICTED

    with pytest.raises(GenerationMetricsError):
        parse_verdict("mostly supported", SUPPORT_VERDICTS, "p")


def test_m208_an_unreadable_verdict_raises_rather_than_defaulting():
    """A default would be the engine *fabricating a measurement* from a failed
    judgement, and a fabricated value is indistinguishable in a report from a
    judged one."""
    judge = ConstantJudge("I am not sure about this one.")

    with pytest.raises(GenerationMetricsError):
        compute([answer_case()], judge)


def test_m208_a_failed_judgement_never_quotes_what_the_judge_returned():
    """`sample_rag/deepseek.py`'s discipline one layer up — an evaluation failure
    can be pasted into a report safely."""
    secret = "ZZTOPSECRETPAYLOAD"

    with pytest.raises(GenerationMetricsError) as failure:
        parse_verdict(secret, SUPPORT_VERDICTS, "the support of claim 1")

    assert secret not in str(failure.value)
    assert "the support of claim 1" in str(failure.value)


def test_m208_a_judge_that_raises_propagates_unchanged():
    with pytest.raises(RuntimeError):
        compute([answer_case()], RefusingJudge())


def test_m208_a_decomposition_returning_nothing_is_a_judge_failure():
    judge = ProbeJudge(claims=[], relevancy=(DIRECT, COMPLETE, ONLY))

    with pytest.raises(GenerationMetricsError):
        compute([answer_case()], judge)


def test_m208_claim_shape_is_normalized_but_claim_content_is_not():
    claims = parse_claims("- 1. First claim\n\n2) Second claim\n", "p")

    assert claims == ["First claim", "Second claim"]


def test_m208_the_three_relevancy_verdicts_are_read_in_order_and_strictly():
    assert parse_relevancy(f"{DIRECT}\n{NOT_COMPLETE}\n{ONLY}", "p") == {
        "direct": DIRECT,
        "complete": NOT_COMPLETE,
        "only": ONLY,
    }

    # The right words in the wrong order name the wrong conjuncts, so it is
    # unreadable rather than repairable.
    with pytest.raises(GenerationMetricsError):
        parse_relevancy(f"{ONLY}\n{DIRECT}\n{COMPLETE}", "p")

    for malformed in (f"{DIRECT}\n{COMPLETE}", f"{DIRECT}\n{COMPLETE}\n{ONLY}\n{ONLY}"):
        with pytest.raises(GenerationMetricsError):
            parse_relevancy(malformed, "p")


# ---------------------------------------------------------------------------
# 10. The measurable domain, and the references it refuses
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("field", ("id", "question", "answer_text"))
def test_m208_a_case_missing_a_required_field_is_refused(field):
    case = answer_case()
    del case[field]

    with pytest.raises(GenerationMetricsError):
        validate_case(case)


@pytest.mark.parametrize("field", BARRED_CASE_FIELDS)
def test_m208_a_case_carrying_a_barred_reference_is_refused(field):
    """**The circularity boundary, made structural rather than promised.**

    `supporting_evidence` and `statements` are the system's own attribution:
    `docs/GENERATION_CONTRACT.md` §24.3 guarantees their **provenance**, not that
    a claim is entailed by them, and §25.1 adds *"that a synthesized
    `answer_text` is permitted is not a statement that it is faithful."*
    `expected_answer` is ground truth, which is the reference of **none** of the
    four metrics.

    Refusing the field is stronger than not reading it: a later caller cannot
    pass one by accident, and no proposition has a parameter it could reach a
    judge through.
    """
    case = answer_case()
    case[field] = "anything at all"

    with pytest.raises(GenerationMetricsError) as failure:
        validate_case(case)

    assert field in str(failure.value)


def test_m208_an_unknown_outcome_is_refused():
    case = answer_case()
    case["outcome"] = "Clarify"

    with pytest.raises(GenerationMetricsError):
        validate_case(case)


def test_m208_an_answer_assembled_from_no_context_is_refused():
    """No conforming `GenerationResult` can carry it: **G-8** requires an Answer
    to have a statement, **G-4** requires every statement to have evidence, and
    **G-5** requires that evidence to resolve to a chunk the `Prompt` carried."""
    case = answer_case()
    case["context"] = []

    with pytest.raises(GenerationMetricsError):
        validate_case(case)


def test_m208_an_abstention_may_have_been_given_context_or_none():
    validate_case(abstain_case())
    empty = abstain_case()
    empty["context"] = []

    assert validate_case(empty) is empty


def test_m208_a_malformed_passage_is_refused_before_a_judge_is_called():
    judge = ProbeJudge(claims=[YEARS_CLAIM], relevancy=(DIRECT, COMPLETE, ONLY))
    case = answer_case()
    case["context"] = [{"chunk_id": "c1", "text": "  "}]

    with pytest.raises(GenerationMetricsError):
        compute([case], judge)

    assert judge.calls == []


def test_m208_a_duplicate_case_id_is_refused():
    judge = ProbeJudge(claims=[YEARS_CLAIM], relevancy=(DIRECT, COMPLETE, ONLY))

    with pytest.raises(GenerationMetricsError):
        compute([answer_case("same"), answer_case("same")], judge)


def test_m208_every_case_is_validated_before_any_judgement_is_spent():
    """A malformed dataset costs no provider interaction and cannot produce a
    partial measurement that looks whole."""
    judge = ProbeJudge(
        claims=[YEARS_CLAIM],
        support={YEARS_CLAIM: SUPPORTED},
        relevancy=(DIRECT, COMPLETE, ONLY),
    )
    broken = answer_case("broken")
    broken["outcome"] = "Clarify"

    with pytest.raises(GenerationMetricsError):
        compute([answer_case("fine"), broken], judge)

    assert judge.calls == []


# ---------------------------------------------------------------------------
# 11. Aggregation — both standard forms, and no invented value
# ---------------------------------------------------------------------------


def test_m208_both_aggregations_are_published_and_differ_where_they_should():
    """Macro weights every answer equally; micro weights every **claim** equally,
    so an answer that makes more claims weighs more."""
    rows = [
        {
            "id": "one",
            "claims_total": 1,
            "claims_faithful": 1,
            "claims_grounded": 1,
            "claims_hallucinated": 0,
            "unmeasured_reason": None,
        },
        {
            "id": "many",
            "claims_total": 3,
            "claims_faithful": 0,
            "claims_grounded": 0,
            "claims_hallucinated": 3,
            "unmeasured_reason": None,
        },
    ]
    faithfulness = aggregate_faithfulness(rows)

    assert faithfulness["faithfulness_macro"] == 0.5
    assert faithfulness["faithfulness_micro"] == 0.25
    assert aggregate_hallucination_rate(rows)["hallucination_rate_macro"] == 0.5
    assert aggregate_hallucination_rate(rows)["hallucination_rate_micro"] == 0.75
    assert aggregate_groundedness(rows)["groundedness_micro"] == 0.25


def test_m208_macro_is_the_mean_of_unrounded_ratios_rounded_once():
    rows = [
        {
            "id": str(index),
            "claims_total": 3,
            "claims_faithful": 1,
            "claims_grounded": 0,
            "claims_hallucinated": 2,
            "unmeasured_reason": None,
        }
        for index in range(3)
    ]

    assert aggregate_faithfulness(rows)["faithfulness_macro"] == round(1 / 3, 4)


def test_m208_an_empty_evaluation_reports_no_score_rather_than_zero():
    """Distinct from `evaluation/context_metrics.py`'s `0.0`, and deliberately:
    there an empty retrieval genuinely recovered nothing, so zero was a
    measurement. Here there is no denominator at all."""
    report = compute([], ProbeJudge())

    assert report["faithfulness"]["faithfulness_macro"] is None
    assert report["answer_relevancy"]["answer_relevancy"] is None
    assert report["per_case"] == []


def test_m208_relevancy_publishes_one_figure_and_the_three_conjunct_counts():
    """The unit is the answer and there is one per case, so macro and micro
    coincide — publishing two numbers would suggest a distinction that does not
    exist (`docs/M2.08_Metric_Semantics_Report.md` §6.4)."""
    rows = [
        {
            "id": "a",
            "answer_relevancy": True,
            "verdicts": {"direct": DIRECT, "complete": COMPLETE, "only": ONLY},
            "unmeasured_reason": None,
        },
        {
            "id": "b",
            "answer_relevancy": False,
            "verdicts": {"direct": DIRECT, "complete": COMPLETE, "only": NOT_ONLY},
            "unmeasured_reason": None,
        },
    ]
    aggregate = aggregate_relevancy(rows)

    assert aggregate["answer_relevancy"] == 0.5
    assert aggregate["answers_direct"] == 2
    assert aggregate["answers_complete"] == 2
    assert aggregate["answers_only"] == 1
    assert "answer_relevancy_macro" not in aggregate
    assert "answer_relevancy_micro" not in aggregate


def test_m208_repeated_execution_over_a_fixed_judge_is_identical():
    """Everything except the judge's answers is deterministic, so a fixed judge
    makes the whole report a pure function of the cases."""
    def report():
        judge = ProbeJudge(
            claims=[YEARS_CLAIM, PROMPTFOO_CLAIM],
            support={YEARS_CLAIM: SUPPORTED, PROMPTFOO_CLAIM: NOT_SUPPORTED},
            grounding={YEARS_CLAIM: (YEARS_PASSAGE,)},
            relevancy=(DIRECT, COMPLETE, ONLY),
        )
        return compute([answer_case("a"), abstain_case("b")], judge)

    first, second = report(), report()

    assert first == second
    assert list(first) == list(second)


def test_m208_the_report_carries_the_evidence_that_explains_each_score():
    """RO-18 Decision 8 — *"M2-08 MUST preserve enough evidence to explain a
    metric result, so a score can be read as evidence rather than as an
    assertion."*

    The chain the frozen report requires: case → claim → proposition → verdict →
    classification → the evidence the judgement used.
    """
    judge = ProbeJudge(
        claims=[YEARS_CLAIM, PROMPTFOO_CLAIM],
        support={YEARS_CLAIM: SUPPORTED, PROMPTFOO_CLAIM: NOT_SUPPORTED},
        grounding={YEARS_CLAIM: (YEARS_PASSAGE,)},
        relevancy=(DIRECT, COMPLETE, ONLY),
    )
    row = compute([answer_case("traceable")], judge)["per_case"][0]

    assert row["id"] == "traceable"
    assert row["outcome"] == ANSWER_OUTCOME

    supported, fabricated = row["claims"]
    assert supported["claim"] == YEARS_CLAIM
    assert supported["support_verdict"] == SUPPORTED
    assert supported["faithful"] is True
    assert supported["hallucinated"] is False
    assert supported["grounded"] is True
    assert supported["grounding_chunk_id"] == "chunkid1"
    assert supported["passages"] == [{"chunk_id": "chunkid1", "verdict": SUPPORTED}]

    assert fabricated["support_verdict"] == NOT_SUPPORTED
    assert fabricated["hallucinated"] is True
    assert fabricated["grounding_chunk_id"] is None

    assert row["relevancy_verdicts"] == {
        "direct": DIRECT,
        "complete": COMPLETE,
        "only": ONLY,
    }


def test_m208_the_per_case_rows_follow_the_callers_order():
    judge = ProbeJudge(
        claims=[YEARS_CLAIM],
        support={YEARS_CLAIM: SUPPORTED},
        grounding={YEARS_CLAIM: (YEARS_PASSAGE,)},
        relevancy=(DIRECT, COMPLETE, ONLY),
    )
    report = compute(
        [answer_case("zulu"), abstain_case("alpha"), answer_case("mike")], judge
    )

    assert [row["id"] for row in report["per_case"]] == ["zulu", "alpha", "mike"]


def test_m208_the_case_helpers_are_usable_alone_and_agree_with_compute():
    judge = ProbeJudge(
        claims=[YEARS_CLAIM],
        support={YEARS_CLAIM: SUPPORTED},
        grounding={YEARS_CLAIM: (YEARS_PASSAGE,)},
        relevancy=(DIRECT, COMPLETE, ONLY),
    )
    case = answer_case()

    assert claim_metrics_case(case, judge)["faithfulness"] == 1.0
    assert relevancy_case(case, judge)["answer_relevancy"] is True


# ---------------------------------------------------------------------------
# 12. Structural boundary specifications — RO-18 made executable
# ---------------------------------------------------------------------------


def test_m208_the_engine_imports_exactly_its_authorized_dependency_surface(repository_root):
    """An **allowlist** over the engine's imports, not a denylist.

    `tests/test_indexer.py` states the reasoning this follows: *"An allowlist
    fails on any import nobody thought to forbid, which a denylist cannot."* The
    allowlist is `math` and nothing else — derived from what the engine actually
    needed rather than copied from another module's list.

    This is the specification that fails if a later edit reaches for DeepEval,
    Ragas, Promptfoo, LangChain, an embedding library, a vector store, a provider
    SDK or an HTTP client, whether or not anyone remembered to name it.
    """
    imports = imported_modules(source_of(repository_root, "evaluation", "generation_metrics.py"))

    assert imports == ENGINE_IMPORT_ALLOWLIST

    for barred in BARRED_PACKAGES:
        assert barred not in imports


def test_m208_the_engine_reaches_no_pipeline_and_no_orchestrator(repository_root):
    """`docs/architecture.md` §6's direction, kept.

    The engine imports nothing from `sample_rag/`, `scripts/` or another
    `evaluation/` module — including `evaluation/context_metrics.py`, because
    **RO-18 Decision 11** leaves M2-07 untouched and a shared helper would make
    one engine's edit reach the other's specification. It performs no filesystem
    and no network I/O and reads no repository authority; every input arrives as
    an argument.
    """
    source = source_of(repository_root, "evaluation", "generation_metrics.py")
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


def test_m208_no_specification_can_reach_a_provider(repository_root):
    """**RO-14 Decision 2**, carried forward by **RO-18 Decision 6** — *"no
    provider call may enter the deterministic pytest suite"*, and **a judge call
    is a provider call.**

    Asserted over this specification file itself: it imports no provider client,
    no network primitive and not the on-demand evaluation script. The judges
    above are scripted substitutes, which is the pattern
    `tests/test_model_generator.py` established for the generation boundary and
    `tests/test_context_metrics.py` for the judging one.
    """
    imports = imported_modules(source_of(repository_root, "tests", "test_generation_metrics.py"))

    assert "sample_rag" not in imports
    assert "scripts" not in imports
    for barred in BARRED_PACKAGES:
        assert barred not in imports


def test_m208_requirements_are_byte_identical_to_the_starting_commit(repository_root):
    """**RO-18 Decision 7** — *"No — none, by name: DeepEval, Promptfoo, Ragas
    (for M2-08), LangChain, LangGraph, the OpenAI SDK, any new HTTP SDK,
    orchestration and model routers are all NOT authorized … `requirements.txt`
    is not changed by this governance sprint"*, and *"no transitive dependency
    becomes authorized merely because it would be useful"*.

    A digest rather than a name scan: this fails on *any* edit — an addition, a
    removal, a version pin, a reordering — including one nobody thought to
    forbid.
    """
    requirements = pathlib.Path(repository_root, "requirements.txt").read_bytes()

    assert hashlib.sha256(requirements).hexdigest() == REQUIREMENTS_DIGEST


def test_m208_the_authorized_provider_boundary_was_not_widened(repository_root):
    """**RO-18 Decision 4** — the judge authorization is narrow and conditional:
    *"the provider implementation must remain architecturally unchanged"*, and
    **not authorized** are *"another provider SDK, another provider, a model
    router, arbitrary HTTP access, rewriting `sample_rag/deepseek.py`,
    retry/orchestration architecture, a second provider client, or a generalized
    LLM abstraction created merely for M2-08."*

    The finding this asserts is that nothing had to change:
    `DeepSeekClient.complete(messages) -> str` was already the whole of what a
    judge needs. A byte-identity digest is the condition made executable.
    """
    boundary = pathlib.Path(repository_root, "sample_rag", "deepseek.py").read_bytes()

    assert hashlib.sha256(boundary).hexdigest() == DEEPSEEK_BOUNDARY_DIGEST


def test_m208_no_second_provider_client_was_created(repository_root):
    """One sanctioned boundary, still one.

    `sample_rag/deepseek.py` remains the only module in the repository holding a
    network primitive, so no alternate provider client, second provider
    architecture, SDK, model router or arbitrary HTTP access entered with this
    sprint.
    """
    holders = []
    for directory in ("sample_rag", "scripts", "evaluation"):
        for module in pathlib.Path(repository_root, directory).glob("*.py"):
            if {"urllib", "http", "socket", "httpx", "requests"} & imported_modules(
                module.read_text(encoding="utf-8")
            ):
                holders.append(f"{directory}/{module.name}")

    assert holders == ["sample_rag/deepseek.py"]


def test_m208_no_evaluation_module_imports_a_barred_package(repository_root):
    """The boundary, swept across every module this sprint could have touched.

    A per-module allowlist protects the module it names; this protects the
    directories against a barred import arriving in a *different* file — which is
    how a dependency actually enters a repository.
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


def test_m208_the_evaluation_entry_point_measures_the_pipeline_without_changing_it(repository_root):
    """**M2-08 is MEASURE, not IMPROVE.**

    The entry point calls each stage through the function that already owns it
    and takes no ranking, depth, fusion, assembly or generation decision of its
    own. Asserted over declared names rather than over the text — the module
    docstring legitimately *mentions* each to record what it does not do, and a
    substring scan over source would make that prose a failure. This is the
    convention `tests/test_model_generator.py` established.
    """
    source = source_of(repository_root, "scripts", "evaluate_generation.py")
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
        "temperature",
    ):
        assert not any(barred in name for name in declared), (
            f"scripts/evaluate_generation.py declares a {barred!r} name"
        )

    imports = imported_modules(source)
    assert {"sample_rag", "scripts", "evaluation"} <= imports


def test_m208_the_evaluation_entry_point_leaves_m207_and_m218_alone(repository_root):
    """**RO-18 Decisions 11 and 12** — M2-07 remains as implemented and M2-18
    remains ✅ DISCHARGED and untouched.

    *"No trace field may be added merely to make M2-08 easier, no `VectorStore`
    may be widened and no semantic similarity score exposed."* The evaluation
    path does not import the trace layer or M2-07's engine, and writes no file at
    all — `reports/baseline/` and `reports/regressions/` are **M3-03** scaffolds
    and are not populated by this sprint.
    """
    source = source_of(repository_root, "scripts", "evaluate_generation.py")
    imports = imported_modules(source)
    tree = ast.parse(source)

    assert "execution_trace" not in imports

    referenced = {
        node.module for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }
    assert "evaluation.context_metrics" not in referenced
    assert "scripts.execution_trace" not in referenced

    called = {
        node.func.id for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    called |= {
        node.func.attr for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }

    assert not {"open", "write_text", "write_bytes", "mkdir", "touch"} & called


def test_m208_the_m207_engine_and_entry_point_are_untouched_by_this_sprint(repository_root):
    """**RO-18 Decision 11** — M2-07's committed artifacts are *"untouched"*.

    Asserted the only way that is machine-checkable from inside the suite: the
    M2-07 engine still declares its own metrics and still imports exactly its
    own authorized surface, and nothing in M2-08 was achieved by editing it.
    """
    source = source_of(repository_root, "evaluation", "context_metrics.py")
    tree = ast.parse(source)
    declared = {
        node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
    }

    assert {"context_precision_case", "context_recall_case"} <= declared
    assert imported_modules(source) == {"math"}
    assert "generation_metrics" not in source
