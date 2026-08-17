"""Native generation-quality metric engine — Sprint M2.08.

Repository Owner ruling **RO-18** (`docs/DEFERRED_ITEMS_REGISTER.md` §4.10)
rescopes **M2-08**'s implementation path from DeepEval activation to *"a native,
repository-owned computation of Faithfulness, Groundedness, Hallucination Rate
and Answer Relevancy"*. This module is that computation. **The capability is
unchanged** — M2-08, Milestone 2, Evaluation Tooling — and only the mechanism is
native.

**The semantics implemented here were frozen before this module existed.**
RO-18 Decision 8 requires the operational propositions to be *"recorded in
implementation evidence before implementing them"*; that record is
`docs/M2.08_Metric_Semantics_Report.md`, and this module implements it rather
than deriving anything of its own. Where a comment below states *why* a
definition is what it is, it cites the authority the frozen report cites; it
does not re-derive it.

The four metrics, and the four propositions they aggregate
------------------------------------------------------------
| Metric | Unit | Evidence frame | Judged proposition |
|---|---|---|---|
| **Faithfulness** | one claim of `answer_text` | the **whole** assembled context | *is this claim supported by the context taken as a whole?* |
| **Groundedness** | one claim of `answer_text` | **one passage**, in isolation | *is this claim supported by this single passage, on its own?* |
| **Hallucination Rate** | one claim of `answer_text` | the **whole** assembled context | the same judgement as Faithfulness, read for its negative classes |
| **Answer Relevancy** | the **whole answer** | **none — the question** | *does this answer directly, completely and only address this question?* |

The claim set comes from `answer_text`, and that is a derivation
-----------------------------------------------------------------
`docs/GENERATION_CONTRACT.md` §14 records that `statements` exists *because*
*"Groundedness is defined per claim"*, and names `statements[].text` *"the unit
Groundedness quantifies over"*. Under **v1.0.0** that was exact: **G-7** required
`answer_text` to be derivable from the statements by verbatim quotation.

Under **v2.0.0** it is not. §24.3 states that `answer_text` *"MAY be synthesized
by the model"*, and §25.1 point 2 states that §8.1's *"contains no content not
present in them"* clause *"does not survive the transition of the guarantee it
restates"*. **A synthesized answer may therefore assert content that appears in
no `GeneratedStatement`** — and that is exactly where a fabrication would live.

The metric definitions quantify over *"everything the model claimed"*
(`docs/AI_Quality_Metrics_Reference.md` §Layer 4, `docs/glossary.md`), and what
the model claimed is what it delivered. **So the claims are decomposed from
`answer_text`, and `statements` / `supporting_evidence` take no part in any
numerator or denominator** — they are diagnostic evidence and are held by the
caller, not by this engine, which has no parameter through which either could
arrive.

What may never be the reference, and why it is refused rather than avoided
----------------------------------------------------------------------------
`docs/GENERATION_CONTRACT.md` §24.3 keeps three things apart — **structural
evidence provenance**, **model answer synthesis**, and **empirical
Faithfulness / Groundedness**, the last being *"later evaluation work — neither
established nor claimed here"* — and §25.1 adds the sentence that closes the
inference: *"That a synthesized `answer_text` is permitted is not a statement
that it is faithful."*

The contract guarantees where a `SupportingEvidence` **came from**. It
guarantees nothing about whether the claim it is attached to is entailed by it.
**Reading the system's own attribution as this metric's reference would convert
a structural guarantee into the empirical property M2-08 exists to measure**, so
`validate_case` **refuses** a case carrying `supporting_evidence`, `statements`,
`expected_answer` or any other name in `BARRED_CASE_FIELDS`. A refused input is
stronger than an unused one: it cannot be smuggled in by a later caller.

**The golden `expected_answer` is refused for the same structural reason and a
different semantic one.** None of the four metrics references it:
`docs/roadmap.md` §5 Layer 3 fixes these metrics as *"consistency with retrieved
context only"*, and Answer Relevancy is *"independent of whether it's true"*
(`docs/AI_Quality_Metrics_Reference.md` §Layer 5). **Correctness against ground
truth is not among RO-18's four metrics**, and a relevancy judgement shown the
reference answer would be judging correctness under relevancy's name.

The evidence frame is the assembled prompt, not the retrieval result
----------------------------------------------------------------------
`docs/altm.md` §4 states the **Infer** failure as *"Model states something not
supported by **the assembled prompt**"*, and `ALTM-INFER-1`'s investigation
clause is *"**Check assembled prompt for the claim**; if absent, it's fabricated
at Infer."* The adjacent **Assemble** failure — *"Correct chunks were retrieved
but did not survive prompt construction"* — is detected by *"prompt assembly
unit/integration tests, **not an LLM metric**"*. Judging against the retrieval
result rather than the assembled prompt would charge **Infer** with an
**Assemble**-stage failure.

So a case carries `context` as the assembled prompt's passages, in assembled
order. `CONTEXT_SEPARATOR` is `sample_rag/context_builder.py`'s separator value,
so the block this engine judges against is byte-identical to the `Prompt.context`
the generator was given — `scripts/evaluate_generation.py` checks that equality
rather than assuming it. The value is restated rather than imported because this
engine imports nothing from `sample_rag/` (below).

What these metrics do not say
-------------------------------
`docs/roadmap.md` §5 Layer 3: they check *"consistency with retrieved context
only — never whether that context was itself current or correct. **A model can
be 100% faithful to a stale document.**"* `docs/altm.md` §4's Infer note says the
same. **No result from this engine is a statement that an answer is correct, or
that the corpus is correct or current**, and no threshold, target or acceptance
score exists in any repository authority or in this module.

Judge injection, and the boundary it keeps
--------------------------------------------
The judge is **injected**, as a `judge(prompt: str) -> str` callable — the seam
`evaluation/context_metrics.py` established under RO-17 and RO-18 Decision 4
names for M2-08: *native M2-08 evaluator → injected judge seam → existing
provider boundary*. This module therefore holds no provider, no client, no
endpoint, no credential, no HTTP primitive and no provider message shape.
`scripts/evaluate_generation.py` adapts `sample_rag/deepseek.py` to that
callable; `tests/test_generation_metrics.py` supplies a non-networked
substitute. **RO-14 Decision 2**, carried forward by **RO-18 Decision 6** — *"no
provider call may enter the deterministic pytest suite"* — holds because there is
nothing in this file for a specification to reach a network through.

Determinism, and its exact boundary
-------------------------------------
**Everything except the judge's answers is deterministic**: prompt construction,
verdict parsing, claim normalization, the arithmetic and the report's key order
are pure functions of their arguments. **The judge's answers are not**, the
**claim denominator is itself a judge product**, and the object being measured is
a `answer_text` that `docs/GENERATION_CONTRACT.md` **G-9** under v2.0.0 does not
require to be reproducible. **No figure this engine returns is deterministic**,
and none is presented as though it were.

Dependency rule, inherited from `evaluation/context_metrics.py`
-----------------------------------------------------------------
Standard library only, and one module of it. This engine imports nothing from
`sample_rag/`, `scripts/` or any other `evaluation/` module, performs no
filesystem and no network I/O, and reads no repository authority — the direction
`docs/architecture.md` §6 draws between the pipeline under test and the logic
that evaluates it. Every input arrives as an argument. `rate`, `parse_verdict`
and their neighbours are therefore restated here rather than imported from
`evaluation/context_metrics.py`: **RO-18 Decision 11 leaves M2-07's artifacts
untouched**, and a shared helper module would make one engine's edit reach the
other's specification.

**No Ragas, no DeepEval, no LangChain, no Promptfoo, no evaluation framework, no
embedding library, no vector-store library, no provider SDK and no HTTP client
is imported here or anywhere reachable from here.** `requirements.txt` is
byte-identical to commit `33f34e0`, `sample_rag/deepseek.py` likewise, and
`tests/test_generation_metrics.py` asserts all of it structurally rather than
recording it as a claim.
"""

import math

# Four places — the repository's established serialization precision
# (`evaluation/retrieval_metrics.py` `PRECISION`), so these figures are directly
# comparable with the metrics already published at other layers.
PRECISION = 4

# The support vocabulary — **four verdicts, and the fourth is load-bearing.**
# `docs/AI_Quality_Metrics_Reference.md` §Layer 4 and `docs/altm.md` §6 both
# record Hallucination Rate as a *"near-complement of Faithfulness in the simple
# case; not guaranteed to sum to 100% once partial/ambiguous claims exist"*. A
# two-verdict vocabulary would force `hallucination_rate == 1 - faithfulness`,
# which is the identity the repository denies. `PARTIALLY_SUPPORTED` is where
# the two metrics are permitted to diverge, and it is why the divergence is a
# property of the definitions rather than a tolerance.
SUPPORTED = "SUPPORTED"
PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"
CONTRADICTED = "CONTRADICTED"
NOT_SUPPORTED = "NOT_SUPPORTED"

SUPPORT_VERDICTS = (SUPPORTED, PARTIALLY_SUPPORTED, CONTRADICTED, NOT_SUPPORTED)

# The per-passage attribution vocabulary. Two verdicts, because Groundedness
# asks one closed question of one passage: does this passage, on its own, carry
# the claim? Partial support, contradiction and "needs another passage" are all
# `NOT_SUPPORTED` here — `docs/glossary.md`: Groundedness is *"weaker on claims
# that require combining sources without a single direct citation"*, and
# `docs/AI_Quality_Metrics_Reference.md` places it above the *"not contradicted"*
# floor rather than at it.
ATTRIBUTION_VERDICTS = (SUPPORTED, NOT_SUPPORTED)

# The claims counted as hallucinated — *"fabricated **or** unsupported"*
# (`docs/AI_Quality_Metrics_Reference.md` §Layer 4), which is the only bucket the
# repository's definition gives. `docs/glossary.md` fixes the fabrication half —
# *"the model states something not present in the retrieved context at all"* —
# and `ALTM-INFER-1` the mechanism: *"check assembled prompt for the claim; if
# absent, it's fabricated at Infer."* A contradicted claim is unsupported in the
# plainest sense and is counted here too; **the two are recorded distinctly in
# the per-claim evidence**, because a contradiction is a different failure from a
# fabrication and RO-18 Decision 8 requires a result to be explainable.
#
# **`PARTIALLY_SUPPORTED` is deliberately absent.** It is not fully entailed, so
# it is not faithful; and it is not *"fabricated"* or *"not present in the
# context at all"*, so it is not hallucinated.
HALLUCINATED_VERDICTS = (NOT_SUPPORTED, CONTRADICTED)

# The three Answer Relevancy conjuncts, each with its own closed pair.
# `docs/AI_Quality_Metrics_Reference.md` §Layer 5 defines the metric as whether
# the answer *"directly, completely, and only"* addresses what was asked; the
# conjunction is what the definition's own "and" means. **They are reported
# separately and no weighting is assigned** — a weighting would be a scale no
# authority defines, and the reference document's *"scores lower"* example (a
# correct answer plus unrequested biography) is representable as a failure of
# `ONLY` alone without one.
DIRECT = "DIRECT"
NOT_DIRECT = "NOT_DIRECT"
COMPLETE = "COMPLETE"
NOT_COMPLETE = "NOT_COMPLETE"
ONLY = "ONLY"
NOT_ONLY = "NOT_ONLY"

DIRECT_VERDICTS = (DIRECT, NOT_DIRECT)
COMPLETE_VERDICTS = (COMPLETE, NOT_COMPLETE)
ONLY_VERDICTS = (ONLY, NOT_ONLY)

RELEVANCY_CONJUNCTS = (
    ("direct", DIRECT_VERDICTS, DIRECT),
    ("complete", COMPLETE_VERDICTS, COMPLETE),
    ("only", ONLY_VERDICTS, ONLY),
)

# The separator that joins the assembled passages back into the block
# Faithfulness is judged against. **`sample_rag/context_builder.py`'s value**, so
# the whole-context frame this engine judges is byte-identical to the
# `Prompt.context` the generator consumed. Restated rather than imported: this
# engine imports nothing from `sample_rag/`, and `scripts/evaluate_generation.py`
# verifies the equality at the seam where both artifacts exist.
CONTEXT_SEPARATOR = "\n\n"

# `docs/GENERATION_CONTRACT.md` §9.2's outcome domain, restated for validation
# only. **G-2**: exactly one of these two. `Clarify` is defined by
# `docs/roadmap.md` §2.4 and is never emitted, so it is not represented here.
ANSWER_OUTCOME = "Answer"
ABSTAIN_OUTCOME = "Abstain"
OUTCOMES = (ANSWER_OUTCOME, ABSTAIN_OUTCOME)

# Case fields this engine **refuses** rather than ignores. Each is a reference a
# metric here must never take, and refusing the field is the structural form of
# that: a later caller cannot pass one by accident, and no prompt function has a
# parameter through which one could reach a judge.
#
#   statements / supporting_evidence  — the system's own attribution.
#       `docs/GENERATION_CONTRACT.md` §24.3 guarantees its provenance, not that
#       the claim is entailed by it. Diagnostic evidence, held by the caller.
#   expected_answer / reference_answer — ground truth. Not the reference of any
#       of the four metrics; see the module docstring.
#   expected_chunk / expected_metrics  — golden dataset annotations. Identifier
#       overlap is `chunk_recall_at_k`, which `docs/P3.3.3_…` §3 records as
#       explicitly not these metrics.
BARRED_CASE_FIELDS = (
    "statements",
    "supporting_evidence",
    "expected_answer",
    "reference_answer",
    "expected_chunk",
    "expected_metrics",
)

# The documented reasons a case carries no metric value. **Neither is a zero.**
# An Abstain answer asserts nothing about the corpus (§9.3) and carries no
# claims (**G-8**), so "0 of 0 claims were faithful" is an absence of a
# denominator, not a measurement of zero — and `docs/M2.08_Metric_Semantics_Report.md`
# §7.4 partitions rather than scoring it.
NO_CLAIMS_REASON = "the answer asserts nothing about the corpus (Abstain)"

# `docs/M2.08_Metric_Semantics_Report.md` §12 finding **U-3**, carried into the
# implementation unresolved and on purpose: no repository authority defines
# whether a conforming abstention *"directly, completely and only"* addresses
# the question it declines. Scoring it 0 would penalize the behaviour the golden
# dataset expects; scoring it 1 would invent a rule. **The gap is recorded in the
# evidence, not filled here.**
RELEVANCY_UNDEFINED_REASON = (
    "Answer Relevancy over an Abstain outcome is undefined by repository "
    "authority (M2.08 semantics report U-3)"
)

# Characters stripped from a verdict before comparison. Formatting a model may
# add around a single word — never content. Parsing stays an exact match against
# the closed vocabulary after this, so `NOT_SUPPORTED` can never be read as
# `SUPPORTED` by a substring test, and `PARTIALLY_SUPPORTED` can never be read as
# either.
VERDICT_TRIM = " \t\r\n.`*\"'"

# List markers stripped from a decomposed claim line. The prompt asks for none;
# removing one that appears anyway is normalization of shape, not tolerance of
# content — a line whose text is a bullet and nothing else still fails, because
# it normalizes to empty.
CLAIM_MARKERS = ("- ", "* ", "• ", "– ")


class GenerationMetricsError(Exception):
    """Raised when a generation-quality metric cannot be measured.

    A ninth independent, flat exception type, following the repository's
    per-responsibility pattern (`ManifestValidationError`,
    `ChunkConstructionError`, `ChunkSerializationError`, `ChunkValidationError`,
    `EvidenceTraceError`, `RetrievalEvaluationError`, `RetrievalMetricsError`,
    `ContextMetricsError`) — a direct `Exception` subclass with no shared
    validation base class (`docs/CHUNK_VALIDATION_PLAN.md` §P6.2).

    **No message this class carries holds a raw judge response, a raw judge
    request, a credential or a provider header.** A verdict that could not be
    read is reported by the *proposition that was being judged* — the case id,
    the claim index, the passage id — and never by quoting what came back. That
    is `sample_rag/deepseek.py`'s discipline (*"no provider response body and no
    request header reaches an error string"*) applied one layer up, and it is
    why an evaluation failure can be pasted into a report safely.
    """


def rate(numerator: int, denominator: int) -> float:
    """A ratio, rounded to the repository's serialization precision.

    Never called with a zero denominator by this module: a case with no claims
    carries `None` and a documented reason instead, because an absent
    denominator is not a measurement of zero.
    """
    return round(exact_ratio(numerator, denominator), PRECISION)


def exact_ratio(numerator: int, denominator: int) -> float:
    """The same ratio, unrounded — the value `rate` publishes a rounding of.

    Macro aggregation sums these rather than the published values, so a mean is
    rounded exactly once, at publication, rather than being a mean of already
    rounded numbers (`evaluation/retrieval_metrics.py`'s convention, unchanged).
    """
    return numerator / denominator if denominator else 0.0


# ---------------------------------------------------------------------------
# The four judged propositions — what the judge is asked, stated in one place
# ---------------------------------------------------------------------------


def claim_prompt(question: str, answer_text: str) -> str:
    """**P1** — the delivered answer, decomposed into the claims it makes.

    **This function has no parameter through which the context could reach it,
    and that is the point.** A decomposer that can see what the context supports
    may suppress claims the context does not — deflating the denominator and
    inflating Faithfulness in the system's favour. **The claim denominator must
    not be a function of the evidence it will subsequently be scored against**,
    and a signature that cannot accept context is a structural guarantee of that
    rather than a promise about a call site.

    **It sees the question**, because an answer's claims are frequently
    elliptical — *"Around 7.5 years"* is a claim only once the question supplies
    its subject. `evaluation/context_metrics.py`'s `decomposition_prompt` set
    that precedent for the reference-side decomposition.

    **It decomposes `answer_text`, not `statements`.** Under
    `docs/GENERATION_CONTRACT.md` v2.0.0 the answer may be synthesized (§24.3)
    and §25.1 point 2 removes §8.1's requirement that it contain nothing outside
    the statements, so content asserted only in `answer_text` would otherwise go
    unmeasured — and that is where a fabrication would live.

    Pure: same arguments, byte-identical prompt, every time.
    """
    return (
        "Break the answer below into the individual claims it makes.\n\n"
        f"Question:\n{question}\n\n"
        f"Answer:\n{answer_text}\n\n"
        "Rules:\n"
        "- Each claim must be a single self-contained factual statement.\n"
        "- Use only information stated in the answer. Add nothing.\n"
        "- Resolve pronouns and references to the question so that each claim "
        "can be read on its own.\n"
        "- Include every claim the answer makes, whether or not you believe it "
        "is true.\n"
        "- Output one claim per line, with no numbering, bullets, headings or "
        "commentary."
    )


def support_prompt(claim: str, context: str) -> str:
    """**P2** — is this claim supported by the context taken as a whole?

    The Faithfulness judgement, and the same judgement Hallucination Rate reads
    for its negative classes. **Judged against the whole assembled context**, and
    **combination across passages is explicitly permitted**: `docs/glossary.md`
    records Faithfulness as satisfied *"even if derived by combining multiple
    sentences"* and *"by multi-hop reasoning across sources"*. Saying so in the
    prompt is what keeps this proposition distinct from `attribution_prompt`
    below — without it, a judge asked the same question twice would answer the
    stricter one twice and the two metrics would collapse.

    **The question is deliberately not supplied.** Support is a relation between
    a claim and a text; admitting the question invites drift toward relevance,
    which is the proposition-drift failure `docs/M2.07_Native_Context_Metrics_Report.md`
    §9 caught and corrected at the other layer.

    Four verdicts, not two. The fourth exists because
    `docs/AI_Quality_Metrics_Reference.md` §Layer 4 records Hallucination Rate as
    diverging from the complement of Faithfulness *"once partial/ambiguous claims
    exist"*, and a claim that is partly carried by the context is neither
    faithful nor fabricated.

    Pure: same arguments, byte-identical prompt, every time.
    """
    return (
        "You are judging whether a context supports a claim.\n\n"
        f"Context:\n{context}\n\n"
        f"Claim:\n{claim}\n\n"
        "Judge only against the context above. Do not use any outside "
        "knowledge. The context may support the claim through one passage or "
        "through several passages combined; combining passages is allowed.\n\n"
        f"{SUPPORTED} — the context states the claim, or fully entails it.\n"
        f"{PARTIALLY_SUPPORTED} — the context supports part of the claim but "
        "not all of it.\n"
        f"{CONTRADICTED} — the context states something incompatible with the "
        "claim.\n"
        f"{NOT_SUPPORTED} — the context carries nothing bearing on the claim.\n\n"
        "Answer with exactly one of those four words, and nothing else."
    )


def attribution_prompt(claim: str, passage: str) -> str:
    """**P3** — is this claim supported by this single passage, on its own?

    The Groundedness judgement. **Exactly one passage reaches this function**,
    and the signature is what makes that structural: there is no parameter
    through which a second passage, the joined context, the question or a prior
    verdict could arrive. `docs/AI_Quality_Metrics_Reference.md` §Layer 4 asks
    whether a claim can be *"traced to a specific, citable piece of evidence —
    stricter than 'not contradicted'"*, and `docs/glossary.md` asks *"can the
    claim be traced to **one** specific, citable piece of evidence?"*

    **The negative class is stated exhaustively**, because Groundedness's
    strictness lives entirely in it. A passage that supports the claim only
    partly, contradicts it, or would need another passage to complete it is
    `NOT_SUPPORTED` — the last of those being the case `docs/glossary.md` names:
    Groundedness is *"weaker on claims that require combining sources without a
    single direct citation"*. That single sentence is the whole difference
    between this proposition and `support_prompt`, and it is why the repository's
    own worked example — *"'Apple's founder passed away in 2011,' derived by
    combining two separate sentences — faithful, but weaker on strict per-claim
    traceability"* — resolves as it does.

    Pure: same arguments, byte-identical prompt, every time.
    """
    return (
        "You are judging whether a single passage supports a claim on its own.\n\n"
        f"Passage:\n{passage}\n\n"
        f"Claim:\n{claim}\n\n"
        "Judge only against this one passage. Do not use any outside "
        "knowledge, and do not assume any other passage exists.\n\n"
        f"{SUPPORTED} — this passage on its own states the claim, or fully "
        "entails it.\n"
        f"{NOT_SUPPORTED} — this passage on its own does not: it carries "
        "nothing bearing on the claim, or supports only part of it, or "
        "contradicts it, or would need another passage alongside it to carry "
        "the claim.\n\n"
        f"Answer with exactly one word, {SUPPORTED} or {NOT_SUPPORTED}, and "
        "nothing else."
    )


def relevancy_prompt(question: str, answer_text: str) -> str:
    """**P4** — does this answer directly, completely and only address this question?

    **The context and the reference answer are both absent from this signature.**
    `docs/AI_Quality_Metrics_Reference.md` §Layer 5 defines the metric as
    *"independent of whether it's true"*, `docs/altm.md` §6 calls it *"the only
    metric independent of truthfulness"*, and `ALTM-FINAL-ANSWER-1`'s
    investigation clause is *"re-check the query against a task-specific rubric,
    **not against truthfulness metrics**"*. Either input would let the judge
    grade truth, which is the collapse RO-18 Decision 8 forbids by name.

    **The independence is stated in the prompt, in both directions**, because
    one direction alone is the easy half. A false answer that addresses the
    question exactly is relevant; a true answer that addresses a different
    question is not. `docs/P3.7.1_Manual_Review_Report.md` Finding 2 is the
    repository's own worked case of the second — five verbatim, fully faithful
    statements against a Rust question, *"the answer is **irrelevant**, not
    **unfaithful**"*.

    **One judgement, three verdicts.** `docs/M2.08_Metric_Semantics_Report.md`
    §9 fixes P4 at one invocation per case yielding the three conjuncts the
    §Layer 5 definition names, so they are reported separately and combined by
    conjunction — with no weighting, which would be a scale no authority defines.

    Pure: same arguments, byte-identical prompt, every time.
    """
    return (
        "You are judging whether an answer addresses the question that was "
        "asked.\n\n"
        f"Question:\n{question}\n\n"
        f"Answer:\n{answer_text}\n\n"
        "Judge only whether the answer addresses the question. Do NOT judge "
        "whether the answer is true, and do not use any outside knowledge "
        "about the subject. An answer that is false but addresses the question "
        "exactly still passes all three judgements below; an answer that is "
        "true but addresses a different question fails them.\n\n"
        "Make three separate judgements:\n"
        f"1. {DIRECT} if the answer addresses what the question asks about, "
        f"{NOT_DIRECT} if it addresses something else.\n"
        f"2. {COMPLETE} if the answer addresses everything the question asks "
        f"for, {NOT_COMPLETE} if it leaves part of the question unaddressed.\n"
        f"3. {ONLY} if the answer carries nothing beyond what the question "
        f"asked for, {NOT_ONLY} if it adds unrequested content.\n\n"
        "Answer with exactly three lines, one word on each line, in that "
        "order, and nothing else."
    )


# ---------------------------------------------------------------------------
# Reading what the judge answered — total, strict, and payload-free
# ---------------------------------------------------------------------------


def parse_verdict(answer, vocabulary: tuple, proposition: str) -> str:
    """Read one closed-vocabulary verdict, or refuse to.

    Exact match against `vocabulary` after trimming surrounding whitespace and
    formatting punctuation, and uppercasing. **Not a substring search** — a
    containment test would read `NOT_SUPPORTED` as `SUPPORTED` and
    `PARTIALLY_SUPPORTED` as either, silently inverting a verdict and moving a
    metric.

    An unreadable answer raises rather than defaulting to a verdict. A default
    would be this module *fabricating a measurement* from a failed judgement,
    and a fabricated value is indistinguishable in a report from a judged one.
    `proposition` names what was being judged so the failure is locatable; **the
    answer itself is never quoted**, into this message or any other.
    """
    if not isinstance(answer, str):
        raise GenerationMetricsError(
            f"The judge returned a non-text answer for {proposition}."
        )

    verdict = answer.strip(VERDICT_TRIM).upper()
    if verdict not in vocabulary:
        raise GenerationMetricsError(
            f"The judge returned no readable verdict for {proposition}; "
            f"expected one of {', '.join(vocabulary)}."
        )
    return verdict


def parse_relevancy(answer, proposition: str) -> dict:
    """Read the three Answer Relevancy conjunct verdicts, one per line.

    Strict in the same way `parse_verdict` is, and for the same reason: exactly
    three readable lines, each matched exactly against **its own** vocabulary in
    the order `relevancy_prompt` states. A response with two lines, four lines,
    or the right words in the wrong order is unreadable rather than repairable —
    guessing which conjunct a stray word belonged to would be this module
    inventing a judgement.
    """
    if not isinstance(answer, str):
        raise GenerationMetricsError(
            f"The judge returned a non-text answer for {proposition}."
        )

    lines = [line for line in answer.splitlines() if line.strip(VERDICT_TRIM)]
    if len(lines) != len(RELEVANCY_CONJUNCTS):
        raise GenerationMetricsError(
            f"The judge returned no readable judgement for {proposition}; "
            f"expected exactly {len(RELEVANCY_CONJUNCTS)} verdict lines."
        )

    return {
        name: parse_verdict(line, vocabulary, f"the {name} judgement of {proposition}")
        for line, (name, vocabulary, _) in zip(lines, RELEVANCY_CONJUNCTS)
    }


def parse_claims(answer, proposition: str) -> list:
    """Read the decomposed answer claims, one per line.

    Normalizes shape only — a leading list marker or numeric prefix is removed,
    blank lines are dropped — and never content. An answer that yields no claim
    is a judge failure and raises: `validate_case` guarantees `answer_text` is
    non-empty, so a decomposition with nothing in it describes the judge, not
    the answer. A zero-claim denominator would otherwise become a `0/0`
    faithfulness that looked like a measurement.
    """
    if not isinstance(answer, str):
        raise GenerationMetricsError(
            f"The judge returned a non-text answer for {proposition}."
        )

    claims = []
    for line in answer.splitlines():
        claim = line.strip()
        for marker in CLAIM_MARKERS:
            if claim.startswith(marker):
                claim = claim[len(marker):].strip()
        claim = _strip_numbering(claim)
        if claim:
            claims.append(claim)

    if not claims:
        raise GenerationMetricsError(
            f"The judge returned no readable claim for {proposition}."
        )
    return claims


def _strip_numbering(claim: str) -> str:
    """Remove a leading `1.` / `1)` enumerator, if the judge added one."""
    head, separator, tail = claim.partition(" ")
    if separator and head[:-1].isdigit() and head[-1:] in (".", ")"):
        return tail.strip()
    return claim


# ---------------------------------------------------------------------------
# The measurable domain — refused before any judge call is spent
# ---------------------------------------------------------------------------


def validate_case(case) -> dict:
    """Verify one evaluation case is measurable, before any judge is called.

    Structural gate, fail-fast, returning the case — the shape
    `validate_manifest`, `validate_chunks`, `validate_evidence_trace`,
    `validate_records` and `evaluation/context_metrics.py`'s `validate_case`
    established, so a case reaches a metric only through a gate.

    The domain, and why each element of it is required:

    * `id` — a non-empty identity, so a per-case evidence row is attributable.
    * `question` — non-empty; it is Answer Relevancy's entire reference, and it
      frames the claim decomposition.
    * `answer_text` — non-empty on **every** path including Abstain, which is
      `docs/GENERATION_CONTRACT.md` **G-3** restated as an input requirement.
    * `outcome` — exactly one of §9.2's two values (**G-2**). It is not derived
      from the presence of claims; it is the artifact's own field, and the
      Abstain partition is read from it.
    * `context` — the assembled prompt's passages as `{chunk_id, text}`, in
      assembled order. **Required non-empty on the `Answer` path**: a conforming
      `Answer` carries at least one statement (**G-8**), every statement at
      least one `SupportingEvidence` (**G-4**), and every evidence resolves to a
      chunk the `Prompt` provenance carried (**G-5** under §25.2) — so an Answer
      assembled from nothing is not a reachable artifact, and refusing it is
      preferable to inventing a convention for a state the contract excludes.
      **Empty is accepted on the Abstain path**, where nothing is judged.

    A passage carrying blank text is refused rather than judged: a judge asked
    whether an empty passage carries a claim answers about nothing, and its
    verdict would enter a denominator regardless.

    **A case carrying any `BARRED_CASE_FIELDS` name is refused outright.** That
    is the circularity boundary made structural rather than promised — see the
    module docstring. The refusal names the field so a caller learns what it may
    not supply, and mentions no value.
    """
    if not isinstance(case, dict):
        raise GenerationMetricsError("An evaluation case must be an object.")

    for field in ("id", "question", "answer_text"):
        value = case.get(field)
        if not isinstance(value, str) or not value.strip():
            raise GenerationMetricsError(
                f"Evaluation case field {field!r} must be a non-empty string."
            )

    for field in BARRED_CASE_FIELDS:
        if field in case:
            raise GenerationMetricsError(
                f"Evaluation case {case['id']!r} carries {field!r}, which is "
                f"not a reference for any M2-08 metric and may not be supplied "
                f"to this engine."
            )

    if case.get("outcome") not in OUTCOMES:
        raise GenerationMetricsError(
            f"Evaluation case {case['id']!r} field 'outcome' must be one of "
            f"{', '.join(OUTCOMES)}."
        )

    context = case.get("context")
    if not isinstance(context, list):
        raise GenerationMetricsError(
            f"Evaluation case {case['id']!r} field 'context' must be a list."
        )

    if case["outcome"] == ANSWER_OUTCOME and not context:
        raise GenerationMetricsError(
            f"Evaluation case {case['id']!r} has outcome {ANSWER_OUTCOME!r} and "
            f"an empty assembled context, which no conforming GenerationResult "
            f"can carry."
        )

    seen: set = set()
    for index, passage in enumerate(context):
        if not isinstance(passage, dict):
            raise GenerationMetricsError(
                f"Context passage at index {index} of case {case['id']!r} must "
                f"be an object."
            )
        for field in ("chunk_id", "text"):
            value = passage.get(field)
            if not isinstance(value, str) or not value.strip():
                raise GenerationMetricsError(
                    f"Context passage at index {index} of case {case['id']!r} "
                    f"has no {field!r}."
                )
        if passage["chunk_id"] in seen:
            raise GenerationMetricsError(
                f"Case {case['id']!r} assembled chunk "
                f"{passage['chunk_id']!r} more than once."
            )
        seen.add(passage["chunk_id"])

    return case


# ---------------------------------------------------------------------------
# The three claim-level metrics, per case — one decomposition, shared
# ---------------------------------------------------------------------------


def claim_metrics_case(case, judge) -> dict:
    """Faithfulness, Groundedness and Hallucination Rate for one answer.

        faithfulness        supported claims          / claims
        groundedness        claims traceable to one   / claims
                            passage on its own
        hallucination_rate  unsupported or            / claims
                            contradicted claims

    **One decomposition, shared by all three.** Decomposing separately per
    metric would spend three times the judgements and could yield three
    different claim sets, which would make the `groundedness <= faithfulness`
    invariant a comparison between different denominators.

        answer_text  ->  claims                       (context NOT supplied)
        claim + whole context  ->  support verdict    (one call per claim)
        claim + one passage    ->  attribution        (one call per pair)

    **The first stage never sees the context**, which is what keeps the
    denominator independent of the evidence the claims are then scored against.

    **An `Abstain` outcome is not scored.** `docs/GENERATION_CONTRACT.md` §9.3
    records that the abstention text *"asserts nothing about the corpus"* and
    **G-8** that `statements` is empty exactly then; the answer makes no claim,
    so there is no denominator. The case carries `None` and
    `NO_CLAIMS_REASON`, **no judge call is made**, and the aggregate publishes
    the count separately — an absent denominator is not a measurement of zero,
    and `docs/M2.08_Metric_Semantics_Report.md` §7.4 partitions rather than
    scoring it.

    **The Groundedness scan stops at the first supporting passage.** Grounding
    is an existential — *"can the claim be traced to **one** specific, citable
    piece of evidence"* — so a later passage cannot change the verdict. This
    spends strictly fewer judgements and **changes no judgement's inputs**: it is
    the only optimization available that does not widen what a judge is shown.
    Batching claims or passages into one call was considered and declined,
    because `docs/M2.08_Metric_Semantics_Report.md` §9 fixes P3's inputs at *one
    claim and exactly one passage* and every batching form available widens one
    of the two. The evidence records the passages actually judged, in assembled
    order, so a grounded claim shows where grounding was established and an
    ungrounded one shows every passage that failed to establish it.

    **The `grounded and not faithful` case is recorded, not repaired.** By the
    definitions a passage that entails the claim is part of the whole context,
    so `Grounded(claim) => Faithful(claim)` and `groundedness <= faithfulness`
    (`docs/M2.08_Metric_Semantics_Report.md` §7.2). A run that produces the
    combination has an inconsistent instrument rather than an interesting
    result; repairing it would fabricate a verdict and raising would discard a
    whole evaluation over one judgement, so it is flagged per claim and counted
    per case — the diagnostic route `docs/M2.07_Native_Context_Metrics_Report.md`
    §9 used when two metrics contradicted each other.
    """
    validate_case(case)

    if case["outcome"] == ABSTAIN_OUTCOME:
        return {
            "id": case["id"],
            "claims_total": 0,
            "claims_faithful": 0,
            "claims_grounded": 0,
            "claims_hallucinated": 0,
            "faithfulness": None,
            "groundedness": None,
            "hallucination_rate": None,
            "unmeasured_reason": NO_CLAIMS_REASON,
            "instrument_inconsistencies": 0,
            "claims": [],
        }

    claims = parse_claims(
        judge(claim_prompt(case["question"], case["answer_text"])),
        f"the claims of case {case['id']!r}",
    )

    context = CONTEXT_SEPARATOR.join(passage["text"] for passage in case["context"])

    records = []
    for index, claim in enumerate(claims, start=1):
        support = parse_verdict(
            judge(support_prompt(claim, context)),
            SUPPORT_VERDICTS,
            f"the support of claim {index} of case {case['id']!r}",
        )
        grounding, passages = _grounding(claim, case["context"], judge, case["id"], index)

        faithful = support == SUPPORTED
        records.append(
            {
                "claim": claim,
                "support_verdict": support,
                "faithful": faithful,
                "hallucinated": support in HALLUCINATED_VERDICTS,
                "grounded": grounding is not None,
                "grounding_chunk_id": grounding,
                "passages": passages,
                "instrument_inconsistency": grounding is not None and not faithful,
            }
        )

    total = len(records)
    faithful = sum(1 for record in records if record["faithful"])
    grounded = sum(1 for record in records if record["grounded"])
    hallucinated = sum(1 for record in records if record["hallucinated"])

    return {
        "id": case["id"],
        "claims_total": total,
        "claims_faithful": faithful,
        "claims_grounded": grounded,
        "claims_hallucinated": hallucinated,
        "faithfulness": rate(faithful, total),
        "groundedness": rate(grounded, total),
        "hallucination_rate": rate(hallucinated, total),
        "unmeasured_reason": None,
        "instrument_inconsistencies": sum(
            1 for record in records if record["instrument_inconsistency"]
        ),
        "claims": records,
    }


def _grounding(claim: str, context: list, judge, case_id: str, index: int) -> tuple:
    """Find the one passage that carries `claim` on its own, if any exists.

    Returns `(chunk_id or None, judged passages)`. Passages are judged in
    assembled order and the scan stops at the first `SUPPORTED`, for the reason
    `claim_metrics_case` records. **Each judgement receives exactly one
    passage's text** — `attribution_prompt` has no parameter for a second — so
    no judgement here can inspect a passage other than its own.
    """
    judged = []
    for passage in context:
        verdict = parse_verdict(
            judge(attribution_prompt(claim, passage["text"])),
            ATTRIBUTION_VERDICTS,
            f"the attribution of claim {index} of case {case_id!r} to chunk "
            f"{passage['chunk_id']!r}",
        )
        judged.append({"chunk_id": passage["chunk_id"], "verdict": verdict})
        if verdict == SUPPORTED:
            return passage["chunk_id"], judged

    return None, judged


# ---------------------------------------------------------------------------
# Answer Relevancy, per case — the whole answer against the question alone
# ---------------------------------------------------------------------------


def relevancy_case(case, judge) -> dict:
    """Answer Relevancy for one answer — *does it address what was asked?*

    One judgement, three conjunct verdicts, and the metric is their conjunction.
    **The unit is the whole answer**, because this is a **Final Answer**-stage
    metric (`docs/altm.md` §4, §6, `ALTM-FINAL-ANSWER-1`) rather than a per-claim
    one — the only one of the four that is.

    **The context never reaches this function**, and neither does any claim-level
    verdict: `relevancy_case` passes the question and the answer, and
    `relevancy_prompt` has no parameter for anything else. That is the
    independence-from-truthfulness property expressed as a signature.

    **An `Abstain` outcome is left unmeasured on purpose.**
    `docs/M2.08_Metric_Semantics_Report.md` §12 records finding **U-3**: no
    repository authority defines whether a conforming abstention addresses the
    question it declines, scoring it 0 would penalize the behaviour the golden
    dataset expects, and scoring it 1 would invent a rule. The case carries
    `None` and `RELEVANCY_UNDEFINED_REASON`, and **no judge call is made**.
    """
    validate_case(case)

    if case["outcome"] == ABSTAIN_OUTCOME:
        return {
            "id": case["id"],
            "answer_relevancy": None,
            "verdicts": None,
            "unmeasured_reason": RELEVANCY_UNDEFINED_REASON,
        }

    verdicts = parse_relevancy(
        judge(relevancy_prompt(case["question"], case["answer_text"])),
        f"the relevancy of case {case['id']!r}",
    )

    return {
        "id": case["id"],
        "answer_relevancy": all(
            verdicts[name] == positive for name, _, positive in RELEVANCY_CONJUNCTS
        ),
        "verdicts": verdicts,
        "unmeasured_reason": None,
    }


# ---------------------------------------------------------------------------
# Aggregation — both standard forms, because no authority selects between them
# ---------------------------------------------------------------------------


def _macro(values: list):
    """Mean of the per-case ratios, rounded once. **`None` on an empty set.**

    Deliberately not `0.0`, which is what `evaluation/context_metrics.py`
    returns in the analogous place — and the difference is the point. There, an
    empty retrieval genuinely recovered nothing, so zero was a measurement.
    Here, an empty set is a set of cases that carried no denominator at all, and
    publishing `0.0` would present the absence of a measurement as a measurement
    of zero.
    """
    return round(math.fsum(values) / len(values), PRECISION) if values else None


def _measured(cases: list) -> list:
    """The cases that carried a claim denominator at all."""
    return [case for case in cases if case["unmeasured_reason"] is None]


def _claim_aggregate(cases: list, metric: str, counted: str) -> dict:
    """One claim-level metric, macro and micro, over `cases`.

    **Both are published, and that is inherited rather than invented.**
    `docs/P3.3.3_Retrieval_Metrics_Report.md` §3 records the repository's
    position: *"No repository authority selects between them, and they answer
    different questions: macro weights every question equally, micro weights
    every chunk equally. Selecting one here would make a methodological choice
    on Sprint P3.3.4's behalf while presenting it as a measurement."* That
    reasoning is unchanged by the metric's name, and RO-18 Decision 8 prescribes
    no aggregation formula, so both are published rather than one elected.

    Micro weights every **claim** equally, so an answer that makes more claims
    weighs more. Macro is the mean of the **unrounded** per-case ratios, rounded
    once at publication; `math.fsum` keeps the accumulation correctly rounded
    regardless of case order, so reordering the dataset cannot move the last
    digit.

    Cases with no claims contribute to neither: they are excluded from the macro
    mean rather than entered at zero, and their count is published so both
    figures can be read against the number of cases that had a denominator.
    """
    measured = _measured(cases)
    numerator = sum(case[counted] for case in measured)
    denominator = sum(case["claims_total"] for case in measured)

    return {
        "cases_evaluated": len(cases),
        "cases_measured": len(measured),
        "cases_without_claims": len(cases) - len(measured),
        "claims_total": denominator,
        counted: numerator,
        f"{metric}_macro": _macro(
            [exact_ratio(case[counted], case["claims_total"]) for case in measured]
        ),
        f"{metric}_micro": rate(numerator, denominator) if denominator else None,
    }


def aggregate_faithfulness(cases: list) -> dict:
    """Corpus-level Faithfulness — *of everything the model claimed, how much is
    supported by the context?*"""
    return _claim_aggregate(cases, "faithfulness", "claims_faithful")


def aggregate_groundedness(cases: list) -> dict:
    """Corpus-level Groundedness — *how much of it traces to one citable passage?*"""
    return _claim_aggregate(cases, "groundedness", "claims_grounded")


def aggregate_hallucination_rate(cases: list) -> dict:
    """Corpus-level Hallucination Rate — *how much was fabricated or unsupported?*

    **Computed from the claim classifications, never from Faithfulness's value.**
    `docs/AI_Quality_Metrics_Reference.md` §Layer 4 and `docs/altm.md` §6 both
    record it as a *"near-complement of Faithfulness in the simple case; not
    guaranteed to sum to 100% once partial/ambiguous claims exist"*, and RO-18
    Decision 8 bars inventing an unrelated formula. Reading `1 - faithfulness`
    would assert the identity the repository denies; counting the two negative
    verdicts leaves the divergence exactly where the definitions put it.
    """
    return _claim_aggregate(cases, "hallucination_rate", "claims_hallucinated")


def aggregate_relevancy(cases: list) -> dict:
    """Corpus-level Answer Relevancy, plus the three conjunct counts.

    **One figure, not two.** The unit is the answer and there is exactly one per
    case, so macro and micro coincide; publishing them as two numbers would
    suggest a distinction that does not exist here
    (`docs/M2.08_Metric_Semantics_Report.md` §6.4).

    The conjunct counts are published beside it as evidence, so an answer that
    fails only on `ONLY` — the reference document's *"same fact plus unrequested
    extra biographical detail"* case — is distinguishable from one that fails on
    all three. **No weighting is applied to them**, because no authority defines
    one.
    """
    measured = [case for case in cases if case["unmeasured_reason"] is None]
    relevant = sum(1 for case in measured if case["answer_relevancy"])

    aggregate = {
        "cases_evaluated": len(cases),
        "cases_measured": len(measured),
        "cases_undefined": len(cases) - len(measured),
        "answers_relevant": relevant,
        "answer_relevancy": rate(relevant, len(measured)) if measured else None,
    }
    for name, _, positive in RELEVANCY_CONJUNCTS:
        aggregate[f"answers_{name}"] = sum(
            1 for case in measured if case["verdicts"][name] == positive
        )
    return aggregate


def compute(cases: list, judge) -> dict:
    """Measure the four generation-quality metrics over a set of cases.

    The engine's single entry point and its output contract:

        {"faithfulness":       {...},   corpus-level, macro and micro
         "groundedness":       {...},   corpus-level, macro and micro
         "hallucination_rate": {...},   corpus-level, macro and micro
         "answer_relevancy":   {...},   corpus-level, one figure plus conjuncts
         "instrument":         {...},   consistency counters — not a metric
         "per_case":           [...]}   one row per case, in case order

    Case order is the caller's order, preserved rather than sorted, so a metric
    row reads against a dataset row. Key order is fixed by construction, so two
    runs over equal cases and an equal judge produce equal reports.

    **Every case is validated before any judge call is made**, so a malformed
    dataset costs no provider interaction and cannot produce a partial
    measurement that looks whole.

    `instrument` is deliberately not a metric block. It counts judgements that
    contradict the definitions — a claim judged grounded but not faithful — so a
    reader can tell an inconsistent instrument from an interesting result.
    """
    for case in cases:
        validate_case(case)

    identities = [case["id"] for case in cases]
    if len(set(identities)) != len(identities):
        raise GenerationMetricsError("Evaluation cases carry a duplicate id.")

    claim_cases = [claim_metrics_case(case, judge) for case in cases]
    relevancy_cases = [relevancy_case(case, judge) for case in cases]
    outcome_of = {case["id"]: case["outcome"] for case in cases}

    return {
        "faithfulness": aggregate_faithfulness(claim_cases),
        "groundedness": aggregate_groundedness(claim_cases),
        "hallucination_rate": aggregate_hallucination_rate(claim_cases),
        "answer_relevancy": aggregate_relevancy(relevancy_cases),
        "instrument": {
            "grounded_but_not_faithful": sum(
                case["instrument_inconsistencies"] for case in claim_cases
            ),
        },
        "per_case": [
            {
                "id": claim["id"],
                "outcome": outcome_of[claim["id"]],
                "claims_total": claim["claims_total"],
                "claims_faithful": claim["claims_faithful"],
                "claims_grounded": claim["claims_grounded"],
                "claims_hallucinated": claim["claims_hallucinated"],
                "faithfulness": claim["faithfulness"],
                "groundedness": claim["groundedness"],
                "hallucination_rate": claim["hallucination_rate"],
                "answer_relevancy": relevancy["answer_relevancy"],
                "relevancy_verdicts": relevancy["verdicts"],
                "unmeasured_reason": claim["unmeasured_reason"],
                "relevancy_unmeasured_reason": relevancy["unmeasured_reason"],
                "instrument_inconsistencies": claim["instrument_inconsistencies"],
                "claims": claim["claims"],
            }
            for claim, relevancy in zip(claim_cases, relevancy_cases)
        ],
    }
