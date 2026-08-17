"""Native Context Precision / Context Recall engine — Sprint M2.07.

Repository Owner ruling **RO-17** (`docs/DEFERRED_ITEMS_REGISTER.md` §4.9)
rescopes **M2-07**'s implementation path from Ragas activation to *"a native,
repository-owned implementation of Context Precision and Context Recall,
faithful to the repository's own metric definitions."* This module is that
implementation. **The capability is unchanged** — M2-07, Milestone 2, Stage 2A,
Evaluation Tooling — and only the mechanism is native.

The two definitions this module implements, quoted rather than paraphrased
------------------------------------------------------------------------------
`docs/AI_Quality_Metrics_Reference.md` §Layer 3, which RO-17 Decision 1 names as
the authoritative source and which is tool-independent:

    Context Precision   "Of everything retrieved, how much was actually
                         relevant?"
    Context Recall      "Of everything relevant that exists in the source, how
                         much did retrieval actually find?"

`docs/altm.md` §6 places both at the **Retrieve** stage and adds the sentence
that fixes Context Precision's frame here: it *"measures noise in retrieved
evidence — has nothing to do with what is eventually said."* Relevance is
therefore judged **against the question**, not against the reference answer and
not against what generation later produced.

What these metrics are NOT, and why the distinction is structural
------------------------------------------------------------------
`docs/P3.3.3_Retrieval_Metrics_Report.md` §3 records the existing `chunk_`
metrics as **explicitly not proxies** for these two:

    "Chunk Precision@K and Chunk Recall@K are not those metrics. They are
     deterministic set-arithmetic measurements over a committed evaluation.
     They do not approximate Ragas metrics, are not a proxy for them, and must
     not be reported under their names."

RO-17 Decision 1 restates the same bar for this sprint — *"a simplified
set-overlap calculation is NOT authorized as a substitute for the metric's
meaning"* — so the two metrics below are **not** computed from `expected_chunk`
identifier overlap, and `expected_chunk` is not read by this module at all.
The difference is not cosmetic:

    chunk_recall_at_k     |E ∩ O| / |E|     did retrieval return the chunk ids
                                            the golden dataset names?
    context_recall        claims recovered  did retrieval return the
                          / claims total    *information* the golden reference
                                            states, wherever it lives?

A corpus chunk that states the same fact at a different id satisfies the second
and fails the first, which is exactly the case `docs/AI_Quality_Metrics_Reference.md`
§Layer 3 illustrates (*"Resume mentions 'CrewAI' twice; retrieval surfaces only
one occurrence"*). Measuring identifiers would answer a question the metric name
does not ask.

The evaluation units, derived
-------------------------------
| | Unit measured | Reference | Judged proposition |
|---|---|---|---|
| **Context Precision** | one **retrieved passage** | none — the question | *is this passage relevant to the question?* |
| **Context Recall** | one **reference claim** | the golden `expected_answer` | *is this claim supported by the retrieved context?* |

**The Context Recall reference is the committed golden ground truth and never
the system's own retrieval output** — RO-17 Decision 6, and the property that
keeps the metric non-circular. That is enforced structurally rather than
promised: `decomposition_prompt` takes the question and the reference answer and
**has no parameter through which retrieved context could reach it**, so no
retrieved text can participate in constructing the denominator. A reference
derived from retrieval would make Context Recall a measurement of retrieval
against itself.

Ordering is not part of either metric, and that is a derivation
----------------------------------------------------------------
No repository authority ranks, discounts or position-weights either metric.
*"Of everything retrieved, how much was actually relevant"* is a proportion of
a set, and `docs/altm.md` §6's *"noise in retrieved evidence"* is likewise
order-free. A rank-weighted variant would be a different metric imported from
outside the repository's own definitions, so `context_precision` here is
**invariant under permutation of the retrieved passages** — a property
`tests/test_context_metrics.py` asserts rather than assumes. Rank order is still
carried into the evidence, because diagnosis wants it even though the metric
does not.

Why a judge is genuinely required, rather than inherited from the Ragas path
------------------------------------------------------------------------------
Both propositions above are **semantic**: whether a passage is relevant, and
whether a claim is supported, are judgements about meaning that no set operation
over identifiers can make. RO-17 Decision 6 permits the judge *"if the
authoritative definition requires an LLM relevance judgement"* and leaves
establishing that to this sprint; it is established by the definitions, not by
the fact that the abandoned Ragas path used one.

The judge is **injected**, as a `judge(prompt: str) -> str` callable. This module
therefore holds no provider, no client, no endpoint, no credential, no HTTP
primitive and no provider message shape — `scripts/evaluate_context.py` adapts
the repository's one sanctioned boundary (`sample_rag/deepseek.py`, RO-17
Decision 4) to that callable, and `tests/test_context_metrics.py` supplies a
non-networked substitute. **RO-14 Decision 2** — *"No provider call is introduced
into the deterministic pytest suite, and none may be"* — holds because there is
nothing in this file for a specification to reach the network through.

Determinism, and its exact boundary
-------------------------------------
**Everything except the judge's answers is deterministic**: prompt construction,
verdict parsing, claim normalization, the arithmetic and the report's key order
are pure functions of their arguments. **The judge's answers are not**, and no
determinism is claimed for them or for any metric value derived from them. The
recall *denominator* is a judge product too, which is a wider non-determinism
than the precision denominator carries, and the report says so rather than
letting the reader assume otherwise.

Dependency rule, inherited from `evaluation/retrieval_metrics.py`
-------------------------------------------------------------------
Standard library only, and one module of it. This engine imports nothing from
`sample_rag/`, `scripts/` or any other `evaluation/` module, performs no
filesystem and no network I/O, and reads no repository authority — the same
direction `docs/architecture.md` §6 draws between the pipeline under test and
the logic that evaluates it. Every input arrives as an argument.

**No Ragas, no LangChain, no DeepEval, no Promptfoo, no evaluation framework, no
embedding library, no vector-store library, no provider SDK and no HTTP client
is imported here or anywhere reachable from here.** `requirements.txt` is
byte-identical to commit `d96107f`, and `tests/test_context_metrics.py` asserts
both facts structurally rather than recording them as a claim.
"""

import math

# Four places — the repository's established serialization precision
# (`evaluation/retrieval_metrics.py` `PRECISION`), so these figures are directly
# comparable with the `chunk_` metrics they are deliberately not.
PRECISION = 4

# The two verdict vocabularies, one per judged proposition. **Fixed, closed and
# single-token.** A judge free to answer in prose would make verdict parsing a
# heuristic over another party's wording, which is the failure
# `sample_rag/deepseek.py`'s `STATUS_REASONS` table avoids at the provider seam
# and this avoids at the judgement seam.
RELEVANT = "RELEVANT"
NOT_RELEVANT = "NOT_RELEVANT"
SUPPORTED = "SUPPORTED"
NOT_SUPPORTED = "NOT_SUPPORTED"

RELEVANCE_VERDICTS = (RELEVANT, NOT_RELEVANT)
ATTRIBUTION_VERDICTS = (SUPPORTED, NOT_SUPPORTED)

# The separator joining retrieved passages into the single context block the
# attribution proposition is judged against. Retrieval returned a ranked list;
# Context Recall asks what that list as a whole recovered, so the claim is
# judged against all of it at once rather than against each passage in turn.
CONTEXT_SEPARATOR = "\n\n"

# Characters stripped from a verdict before comparison. Formatting a model may
# add around a single word — never content. Parsing stays an exact match against
# the closed vocabulary after this, so `NOT_SUPPORTED` can never be read as
# `SUPPORTED` by a substring test.
VERDICT_TRIM = " \t\r\n.`*\"'"

# List markers stripped from a decomposed claim line. The prompt asks for none;
# removing one that appears anyway is normalization of shape, not tolerance of
# content — a line whose text is a bullet and nothing else still fails, because
# it normalizes to empty.
CLAIM_MARKERS = ("- ", "* ", "• ", "– ")


class ContextMetricsError(Exception):
    """Raised when Context Precision or Context Recall cannot be measured.

    An eighth independent, flat exception type, following the repository's
    per-responsibility pattern (`ManifestValidationError`, `ChunkConstructionError`,
    `ChunkSerializationError`, `ChunkValidationError`, `EvidenceTraceError`,
    `RetrievalEvaluationError`, `RetrievalMetricsError`) — a direct `Exception`
    subclass with no shared validation base class
    (`docs/CHUNK_VALIDATION_PLAN.md` §P6.2).

    **No message this class carries holds a raw judge response, a raw judge
    request, a credential or a provider header.** A verdict that could not be
    read is reported by the *proposition that was being judged* — the case id,
    the passage id, the claim index — and never by quoting what came back. That
    is `sample_rag/deepseek.py`'s discipline (*"no provider response body and no
    request header reaches an error string"*) applied one layer up, and it is
    why an evaluation failure can be pasted into a report safely.
    """


def rate(numerator: int, denominator: int) -> float:
    """A ratio, rounded to the repository's serialization precision.

    A zero denominator yields `0.0` rather than raising, so a report stays
    total. Each call site below reaches zero only in the degenerate case its own
    docstring names.
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
# The judged propositions — what the judge is asked, stated in one place
# ---------------------------------------------------------------------------


def relevance_prompt(question: str, passage: str) -> str:
    """The Context Precision proposition, for one retrieved passage.

    **Judged against the question alone.** The reference answer is deliberately
    not supplied: `docs/altm.md` §6 records that Context Precision *"has nothing
    to do with what is eventually said"*, and showing the judge the expected
    answer would quietly convert *relevant to the question* into *supports the
    expected answer* — which is Context Recall's proposition wearing Context
    Precision's name, and would drag the metric back toward the identifier
    overlap RO-17 Decision 1 bars.

    **Relevance is stated as subject matter, not sufficiency, and that wording
    is a correction rather than a preference.** A first form of this proposition
    asked only whether the passage *"contain[ed] information that is relevant to
    answering the question"*, and the judge reproducibly read it as a
    sufficiency test: asked whether *"Led QA delivery … managing a
    cross-functional team of 5"* was relevant to *"How many engineers did
    Karthik lead …"*, it answered `NOT_RELEVANT` three times out of three,
    reasoning that the passage *"does not state the number of engineers …
    specifically"* and that a *"cross-functional team … may include
    non-engineers"*.

    That is a different metric. `docs/AI_Quality_Metrics_Reference.md` §Layer 3
    asks *"of everything retrieved, how much was actually **relevant**"* and
    illustrates it by topic — *"CrewAI experience, RCA pipeline (relevant) + a
    Bosch internship bullet (irrelevant)"* — and `docs/altm.md` §6 calls the
    quantity *"noise in retrieved evidence"*. Noise is content that does not
    bear on the question, not content that fails to settle it.

    **The repository names the negative class outright, and names it topical.**
    `docs/roadmap.md` §8: *"Retrieval's only failure mode is pulling in
    real-but-irrelevant material (noise)."* `docs/glossary.md`: *"how much was
    actually relevant versus noise."* And `evaluation/altm_rules.py`'s
    `ALTM-RETRIEVE-4` binds `"metric": "Context Precision"` to the investigation
    *"Check for near-duplicate or loosely-related chunks crowding results"* —
    near-duplication and loose relatedness, both topical properties.

    A sufficiency test would additionally relocate the metric: whether one chunk
    carries a complete semantic unit is **Chunk Integrity**, a Layer 2 / Index
    metric, and whether something *"directly, completely … address[es] what was
    actually asked"* is **Answer Relevancy**, a Layer 5 / Final Answer metric.
    Reading either into a Retrieve-stage metric collapses the layer boundary
    `docs/learning-log.md` calls *"the single most load-bearing distinction in
    the entire documentation set."*

    The wording below was validated against a labelled probe in **both**
    directions before adoption, so a proposition that simply answered
    `RELEVANT` to everything would have failed it as loudly: the corpus header,
    the contact line and an off-topic achievement bullet are still judged
    `NOT_RELEVANT`. **It was not tuned against the aggregate score** —
    `docs/M2.07_Native_Context_Metrics_Report.md` §9 records the probe, its
    labels and both results.

    Pure: same arguments, byte-identical prompt, every time.
    """
    return (
        "You are judging retrieval quality in a question-answering system.\n\n"
        f"Question:\n{question}\n\n"
        f"Retrieved passage:\n{passage}\n\n"
        "Does this passage carry information bearing on the question?\n\n"
        "Relevance is about subject matter, not sufficiency. The passage is "
        f"{RELEVANT} if it carries information about what the question asks "
        "about, including information that answers it only partly, only "
        "approximately, or only together with other passages. Do not require "
        "the passage to answer the question completely, exactly, or on its "
        "own.\n\n"
        f"The passage is {NOT_RELEVANT} only if it is about a different "
        "subject, or carries no information bearing on the question.\n\n"
        f"Answer with exactly one word, {RELEVANT} or {NOT_RELEVANT}, and "
        "nothing else."
    )


def decomposition_prompt(question: str, reference_answer: str) -> str:
    """The Context Recall reference, decomposed into claim units.

    **This function has no parameter through which retrieved context could
    reach it, and that is the point.** RO-17 Decision 6 requires the Context
    Recall reference to be *"the committed golden ground truth — never the
    system's own retrieval output"*; a signature that cannot accept retrieval
    output is a structural guarantee of that rather than a promise about a call
    site. The denominator is a function of the golden dataset alone.

    **Why the decomposition is judged rather than split deterministically.**
    A sentence splitter is deterministic and is not faithful here: the golden
    reference answer *"Maruti Suzuki, Betts Group, and Red Earth."* is one
    sentence and three recoverable facts, and scoring it as a single unit would
    make partial recovery — the exact phenomenon Context Recall exists to detect
    — unrepresentable. The alternative was rejected for being convenient rather
    than for being wrong, which is the direction RO-17 Decision 1 warns about.

    The cost is stated rather than hidden: **the recall denominator is not
    deterministic**, and the per-case evidence records the claims a run actually
    used so a score can be read against them.
    """
    return (
        "Break the reference answer below into the individual factual claims it "
        "makes.\n\n"
        f"Question:\n{question}\n\n"
        f"Reference answer:\n{reference_answer}\n\n"
        "Rules:\n"
        "- Each claim must be a single self-contained factual statement.\n"
        "- Use only information stated in the reference answer. Add nothing.\n"
        "- Resolve pronouns so that each claim can be read on its own.\n"
        "- Output one claim per line, with no numbering, bullets, headings or "
        "commentary."
    )


def attribution_prompt(claim: str, context: str) -> str:
    """The Context Recall proposition, for one reference claim.

    Judged against the retrieved context as a whole, because the metric asks
    what retrieval recovered — not which passage recovered it. The judge is told
    to use the context and nothing else, so a claim the model happens to know is
    still not recall.

    Pure: same arguments, byte-identical prompt, every time.
    """
    return (
        "You are judging whether retrieved context supports a claim.\n\n"
        f"Retrieved context:\n{context}\n\n"
        f"Claim:\n{claim}\n\n"
        "Is the claim supported by the retrieved context above? Judge only "
        "against the retrieved context; do not use any outside knowledge. The "
        "claim is supported if the retrieved context states it or directly "
        "entails it.\n\n"
        f"Answer with exactly one word, {SUPPORTED} or {NOT_SUPPORTED}, and "
        "nothing else."
    )


# ---------------------------------------------------------------------------
# Reading what the judge answered — total, strict, and payload-free
# ---------------------------------------------------------------------------


def parse_verdict(answer, vocabulary: tuple, proposition: str) -> str:
    """Read one closed-vocabulary verdict, or refuse to.

    Exact match against `vocabulary` after trimming surrounding whitespace and
    formatting punctuation, and uppercasing. **Not a substring search** — a
    containment test would read `NOT_SUPPORTED` as `SUPPORTED`, silently
    inverting the verdict and inflating the metric.

    An unreadable answer raises rather than defaulting to the negative verdict.
    A default would be this module *fabricating a measurement* from a failed
    judgement, and a fabricated zero is indistinguishable in a report from a
    judged one. `proposition` names what was being judged so the failure is
    locatable; **the answer itself is never quoted**, into this message or any
    other.
    """
    if not isinstance(answer, str):
        raise ContextMetricsError(
            f"The judge returned a non-text answer for {proposition}."
        )

    verdict = answer.strip(VERDICT_TRIM).upper()
    if verdict not in vocabulary:
        raise ContextMetricsError(
            f"The judge returned no readable verdict for {proposition}; "
            f"expected one of {', '.join(vocabulary)}."
        )
    return verdict


def parse_claims(answer, proposition: str) -> list:
    """Read the decomposed reference claims, one per line.

    Normalizes shape only — a leading list marker or numeric prefix is removed,
    blank lines are dropped — and never content. An answer that yields no claim
    is a judge failure and raises: the reference answer supplied to
    `decomposition_prompt` is non-empty by `validate_case`, so a decomposition
    with nothing in it describes the judge, not the reference. A zero-claim
    denominator would otherwise become a `0/0` recall of `0.0` that looked like
    a measurement.
    """
    if not isinstance(answer, str):
        raise ContextMetricsError(
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
        raise ContextMetricsError(
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
    `validate_manifest`, `validate_chunks`, `validate_evidence_trace` and
    `validate_records` established, so a case reaches a metric only through a
    gate.

    The domain, and why each element of it is required:

    * `id` — a non-empty identity, so a per-case evidence row is attributable.
    * `question` — non-empty; it is Context Precision's entire reference.
    * `reference_answer` — non-empty; it is Context Recall's entire reference,
      and an empty one has no claims to recover.
    * `retrieved` — a list of `{chunk_id, text}` passages in retrieval rank
      order. **May be empty**: a retrieval that returned nothing is a real
      observation, not a malformed case, and both metrics have a documented
      value for it.

    A passage carrying blank text is refused rather than judged: a judge asked
    whether an empty passage is relevant answers about nothing, and its verdict
    would enter a denominator regardless.
    """
    if not isinstance(case, dict):
        raise ContextMetricsError("An evaluation case must be an object.")

    for field in ("id", "question", "reference_answer"):
        value = case.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ContextMetricsError(
                f"Evaluation case field {field!r} must be a non-empty string."
            )

    retrieved = case.get("retrieved")
    if not isinstance(retrieved, list):
        raise ContextMetricsError(
            f"Evaluation case {case['id']!r} field 'retrieved' must be a list."
        )

    seen: set = set()
    for index, passage in enumerate(retrieved):
        if not isinstance(passage, dict):
            raise ContextMetricsError(
                f"Retrieved passage at index {index} of case {case['id']!r} "
                f"must be an object."
            )
        for field in ("chunk_id", "text"):
            value = passage.get(field)
            if not isinstance(value, str) or not value.strip():
                raise ContextMetricsError(
                    f"Retrieved passage at index {index} of case "
                    f"{case['id']!r} has no {field!r}."
                )
        if passage["chunk_id"] in seen:
            raise ContextMetricsError(
                f"Case {case['id']!r} retrieved chunk "
                f"{passage['chunk_id']!r} more than once."
            )
        seen.add(passage["chunk_id"])

    return case


# ---------------------------------------------------------------------------
# The two metrics, per case
# ---------------------------------------------------------------------------


def context_precision_case(case, judge) -> dict:
    """Context Precision for one question — *of everything retrieved, how much
    was actually relevant?*

        context_precision = relevant retrieved passages / retrieved passages

    One judge call per retrieved passage, each asking the single proposition
    `relevance_prompt` states. Passages are judged **independently** and in rank
    order; the order affects which evidence row is which and affects no metric
    value, which `tests/test_context_metrics.py` asserts by permutation.

    **Empty retrieval yields `0.0`, by documented convention rather than by
    measurement** — the same convention `evaluation/retrieval_metrics.py`
    records for `chunk_precision_at_k`, and for the same reason: nothing
    relevant was retrieved, because nothing was. No judge call is made, so a
    degenerate case costs no provider interaction.

    The evidence returned is what explains the number: every retrieved passage,
    its rank, and the verdict it received. **No judge prompt and no judge
    response text is carried in it** — a verdict is the derived evaluation
    evidence the metric needs, and the payload that produced it is not.
    """
    validate_case(case)

    verdicts = []
    for rank, passage in enumerate(case["retrieved"], start=1):
        verdict = parse_verdict(
            judge(relevance_prompt(case["question"], passage["text"])),
            RELEVANCE_VERDICTS,
            f"the relevance of chunk {passage['chunk_id']!r} to case {case['id']!r}",
        )
        verdicts.append(
            {"rank": rank, "chunk_id": passage["chunk_id"], "verdict": verdict}
        )

    relevant = sum(1 for record in verdicts if record["verdict"] == RELEVANT)

    return {
        "id": case["id"],
        "retrieved_passages": len(verdicts),
        "relevant_passages": relevant,
        "context_precision": rate(relevant, len(verdicts)),
        "passages": verdicts,
    }


def context_recall_case(case, judge) -> dict:
    """Context Recall for one question — *of everything relevant that exists in
    the source, how much did retrieval actually find?*

        context_recall = supported reference claims / reference claims

    Two stages, in this order and no other:

        golden expected_answer  ->  claims          (retrieval NOT supplied)
        claim + retrieved context  ->  supported?   (one call per claim)

    **The first stage never sees retrieval output**, which is what makes the
    denominator independent of the system being measured (RO-17 Decision 6). The
    second stage is the only place retrieved text enters, and it enters as the
    thing being tested rather than as the thing defining the test.

    **Empty retrieval yields `0.0` without any judge call at all.** Nothing was
    retrieved, so no claim can be supported by it, and decomposing a reference
    to discover that would spend provider calls to reach an answer the metric
    already fixes. The case records `claims_total` as `0` and carries the reason,
    so an empty-retrieval zero is never mistaken for a judged zero.
    """
    validate_case(case)

    if not case["retrieved"]:
        return {
            "id": case["id"],
            "claims_total": 0,
            "claims_supported": 0,
            "context_recall": 0.0,
            "unmeasured_reason": "retrieval returned no context",
            "claims": [],
        }

    claims = parse_claims(
        judge(decomposition_prompt(case["question"], case["reference_answer"])),
        f"the reference claims of case {case['id']!r}",
    )

    context = CONTEXT_SEPARATOR.join(
        passage["text"] for passage in case["retrieved"]
    )

    verdicts = []
    for index, claim in enumerate(claims, start=1):
        verdict = parse_verdict(
            judge(attribution_prompt(claim, context)),
            ATTRIBUTION_VERDICTS,
            f"reference claim {index} of case {case['id']!r}",
        )
        verdicts.append({"claim": claim, "verdict": verdict})

    supported = sum(1 for record in verdicts if record["verdict"] == SUPPORTED)

    return {
        "id": case["id"],
        "claims_total": len(verdicts),
        "claims_supported": supported,
        "context_recall": rate(supported, len(verdicts)),
        "unmeasured_reason": None,
        "claims": verdicts,
    }


# ---------------------------------------------------------------------------
# Aggregation — both standard forms, because no authority selects between them
# ---------------------------------------------------------------------------


def _macro(values: list) -> float:
    """Mean of per-case ratios, rounded once. Empty input yields `0.0`."""
    return round(math.fsum(values) / len(values), PRECISION) if values else 0.0


def aggregate_precision(cases: list) -> dict:
    """Corpus-level Context Precision, macro and micro.

    **Both are published, and that is inherited rather than invented.**
    `docs/P3.3.3_Retrieval_Metrics_Report.md` §3 records the repository's
    position exactly: *"No repository authority selects between them, and they
    answer different questions: macro weights every question equally, micro
    weights every chunk equally. Selecting one here would make a methodological
    choice on Sprint P3.3.4's behalf while presenting it as a measurement."*
    That reasoning is unchanged by the metric's name, and RO-17 Decision 6
    prescribes no aggregation, so this sprint publishes both rather than electing
    one.

    Macro is the mean of the **unrounded** per-case ratios, rounded once at
    publication; `math.fsum` keeps the accumulation correctly rounded regardless
    of case order, so reordering the dataset cannot move the last digit.
    """
    relevant = sum(case["relevant_passages"] for case in cases)
    retrieved = sum(case["retrieved_passages"] for case in cases)

    return {
        "cases_evaluated": len(cases),
        "retrieved_passages": retrieved,
        "relevant_passages": relevant,
        "context_precision_macro": _macro(
            [
                exact_ratio(case["relevant_passages"], case["retrieved_passages"])
                for case in cases
            ]
        ),
        "context_precision_micro": rate(relevant, retrieved),
    }


def aggregate_recall(cases: list) -> dict:
    """Corpus-level Context Recall, macro and micro.

    Macro weights every question equally; micro weights every reference **claim**
    equally, so a question whose reference states more facts weighs more. Both
    are published for the reason `aggregate_precision` records.

    Cases carrying `unmeasured_reason` — an empty retrieval — participate at
    `0.0` macro and contribute nothing to either micro total. Their count is
    published separately so the two aggregations can be read against the number
    of cases that had a denominator at all.
    """
    supported = sum(case["claims_supported"] for case in cases)
    total = sum(case["claims_total"] for case in cases)

    return {
        "cases_evaluated": len(cases),
        "cases_without_retrieved_context": sum(
            1 for case in cases if case["unmeasured_reason"]
        ),
        "reference_claims": total,
        "supported_claims": supported,
        "context_recall_macro": _macro([case["context_recall"] for case in cases]),
        "context_recall_micro": rate(supported, total),
    }


def compute(cases: list, judge) -> dict:
    """Measure Context Precision and Context Recall over a set of cases.

    The engine's single entry point and its output contract:

        {"context_precision": {...},   corpus-level, macro and micro
         "context_recall":    {...},   corpus-level, macro and micro
         "per_case":          [...]}   one row per case, in case order

    Case order is the caller's order, preserved rather than sorted, so a metric
    row reads against a dataset row. Key order is fixed by construction, so two
    runs over equal cases and an equal judge produce equal reports.

    **Every case is validated before any judge call is made**, so a malformed
    dataset costs no provider interaction and cannot produce a partial
    measurement that looks whole.
    """
    for case in cases:
        validate_case(case)

    identities = [case["id"] for case in cases]
    if len(set(identities)) != len(identities):
        raise ContextMetricsError("Evaluation cases carry a duplicate id.")

    precision_cases = [context_precision_case(case, judge) for case in cases]
    recall_cases = [context_recall_case(case, judge) for case in cases]

    return {
        "context_precision": aggregate_precision(precision_cases),
        "context_recall": aggregate_recall(recall_cases),
        "per_case": [
            {
                "id": precision["id"],
                "retrieved_passages": precision["retrieved_passages"],
                "relevant_passages": precision["relevant_passages"],
                "context_precision": precision["context_precision"],
                "claims_total": recall["claims_total"],
                "claims_supported": recall["claims_supported"],
                "context_recall": recall["context_recall"],
                "unmeasured_reason": recall["unmeasured_reason"],
                "passages": precision["passages"],
                "claims": recall["claims"],
            }
            for precision, recall in zip(precision_cases, recall_cases)
        ],
    }
