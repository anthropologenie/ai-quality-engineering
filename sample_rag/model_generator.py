"""Model-backed Generation Runtime — Generation Contract v2.0.0.

Sprint M2.06: register capability **M2-06** — *"DeepSeek API generation"* — the
repository's first real model-backed generation, implemented against
`docs/GENERATION_CONTRACT.md` **§24** (Generation Contract **v2.0.0**) under
Repository Owner ruling **RO-13** (`docs/DEFERRED_ITEMS_REGISTER.md` §4.5).

The generation path implemented here is §24.2's, exactly:

    retrieval -> ordered chunk ids -> ContextBuilder -> Prompt
              -> Generator -> provider -> GenerationResult

**This module implements an approved contract and makes no governance
decision.** Where RO-13 answered a question, the answer is applied; where RO-13
deliberately left an engineering choice to M2-06 (§24.6, §4.5 Decision 4), the
choice is recorded at its point of use with the guarantee it is justified
against, and in `docs/M2.06_Generation_Report.md`.

Why this is a second module and not an edit to `sample_rag/generator.py`
-------------------------------------------------------------------------
**An engineering decision of this sprint, and the one most in need of stating
plainly.**

`docs/GENERATION_CONTRACT.md` §24.1 is explicit that v1.0.0 *"is not withdrawn,
corrected, or falsified"* and *"remains the accurate, frozen record of what the
Milestone 1A deterministic quotation Generator guaranteed"*. Two contracts are
therefore live at once, each authoritative for its own component: v1.0.0 for the
Milestone 1A quotation Generator, v2.0.0 for model-backed Milestone 2
generation. `sample_rag/generator.py` is the former and is **unchanged by this
sprint** — byte for byte, including its 48 frozen specifications.

The alternative was to replace `Generator.generate(query, retrieval)` in place.
That is not available to M2-06, for a reason that is a repository fact rather
than a preference: `scripts/cli.py` is the sole consumer of the v1.0.0
signature, `docs/P3.7.6_Milestone_1A_Closure_and_Frozen_Baseline.md` §3.2 freezes
its 27 specifications and §4 freezes its byte-identical answer and abstain
reproducibility as Milestone 1A acceptance evidence, and a CLI driving this
module would put a live provider call inside the deterministic pytest suite.
Replacing in place would have meant deleting that evidence — and P3.7.6 states
that subsequent milestones *"**SHALL extend** this baseline"* and *"**SHALL NOT
redefine** it"*.

**What this module does not decide.** Which of the two components is the
`docs/architecture.md` §5 `Generator` row is **M2-14**, which RO-13 §24.2
authorized and deliberately did not discharge (*"owned by M2-14, which remains a
separate open capability"*). The class below is therefore named for what it is
rather than claiming that row. **The method contract §24.2 fixes —
`generate(prompt: Prompt) -> GenerationResult` — is implemented literally.**
`docs/M2.06_Generation_Report.md` records the coexistence as a finding for
M2-14 rather than resolving it here.

The guarantee transitions, applied (§24.3)
--------------------------------------------
**G-14** — exactly one sanctioned provider interaction, and it is not made from
this module. `sample_rag/deepseek.py` owns the boundary; this file imports no
network primitive, opens no socket, holds no endpoint and reads no credential.
Filesystem I/O remains barred outright and is structurally absent: no
`pathlib`, no `os`, no `open`.

**G-13 / §18** — the permitted runtime inputs are a `Prompt` and that one call.
**Nothing here reaches the `Retriever`, BM25, FAISS, the `VectorStore`, the
`VectorRuntime`, the fusion layer, the chunk store, the corpus, or
`ContextBuilder.resolve()`.** §18's barred list carries forward in full — the
Knowledge Manifest, Golden Dataset, QA Dataset, Chunk Corpus as a file, Evidence
Trace Dataset, Retrieval Evaluation, Retrieval Metrics, Retrieval Diagnosis and
ALTM rules are unreadable from here, for the reason §18 records: a Generator
that reads any of them can answer the repository's own 22 benchmark questions
and nothing else while appearing to work. `sample_rag/` still does not import
`scripts/`.

**G-9** — split, not weakened. Everything this module computes is deterministic:
provenance mapping, statement construction, evidence construction, message
construction, diagnostics and outcome selection. `answer_text` is the provider's
and **no reproducibility is claimed for it**. `ALTM-INDEX-1` — *"contradictory
answer across repeated runs on the same input"* — was unreachable by
construction under v1.0.0 and, as §24.3 records, **becomes reachable here**. It
is a property to observe, not one this module asserts away.

**G-7** — narrowed to provenance. `answer_text` may be synthesized;
`SupportingEvidence` may not. Every span this module emits derives from the
`Prompt`'s own context and provenance, and from nothing else.

What is deliberately *not* claimed
------------------------------------
**Faithfulness, groundedness and the absence of hallucination are not
established by anything in this file**, and the presence of evidence metadata is
not evidence of any of them. §24.3 keeps three things distinct — structural
evidence provenance, model answer synthesis, and empirical faithfulness — and
records the third as *"later evaluation work, neither established nor claimed
here"*. Ragas (**M2-07**), DeepEval (**M2-08**) and Promptfoo (**M3-01**) are
untouched, and a successful provider call is not evidence of answer quality.

No reranking (**M2-05**), no query rewriting or expansion, no retrieval or
prompt optimization (**M2-15**), no chunking change (**M2-17**), no context
compression, no token budget, no memory, no agent runtime, no tool calling and
no model routing.
"""

from sample_rag.context_builder import CONTEXT_SEPARATOR, Prompt
from sample_rag.deepseek import DeepSeekClient
from sample_rag.generator import (
    ABSTENTION_TEXT,
    OUTCOME_ABSTAIN,
    OUTCOME_ANSWER,
    GeneratedStatement,
    GenerationResult,
    SupportingEvidence,
)

# §24.3: *"§7's data model, §8's field definitions, §9's outcome domain, §10's
# traceability requirements, §11's ordering semantics and §13's serialization
# form"* are unchanged. So the artifact classes and the outcome domain are
# **imported, not redefined**. A v2 copy of `GenerationResult` would be a second
# definition of one contract, and `serialize` would then depend on which copy
# produced the value — the exact defect §20.4's checked duplication exists to
# avoid where duplication is unavoidable. Here it is avoidable.

# §24.5 — the stub marker, required and now `False`, *"because generation is no
# longer a stub"*. `sample_rag/generator.py`'s `GENERATION_STUB = True` is
# **not** rewritten: §24.5 states that *"no historical `stub = True` statement is
# restated as `False`"*, and that marker still describes the Milestone 1A
# component it belongs to.
GENERATION_STUB = False

# Engineering decision — the system instruction (§24.6 leaves the request format
# to M2-06).
#
# **This is not prompt engineering, and it is not an optimized prompt.** Prompt
# and retrieval optimization is **M2-15** and is out of scope; what follows is
# the smallest instruction that makes the provider call a question *about the
# assembled context* rather than an open question, which is the difference
# between a RAG request and a chat request. It contains no repository identity,
# no filesystem path, no chunk id, no document id, no offset and no credential.
#
# It asks the model to say so when the context does not answer the question. That
# is not an abstention mechanism — abstention is `docs/GENERATION_CONTRACT.md`
# §9.3's, decided below from the `Prompt` and never from model prose — and no
# `outcome` is derived from what the model says.
SYSTEM_INSTRUCTION = (
    "You answer questions using only the evidence supplied to you in the "
    "context. Do not use outside knowledge. If the context does not contain "
    "the answer, say that it does not."
)

# Engineering decision — the user message template, and a deterministic one: two
# fixed labels around two values taken verbatim from the `Prompt`. No chunk id,
# document id, character offset, score, rank, citation marker or numbering
# reaches the provider. The Assemble stage already refused to put markup in the
# context (`sample_rag/context_builder.py`), and adding it here would put text in
# front of the model that no corpus chunk supports while telling it nothing the
# Generation Contract needs back.
USER_TEMPLATE = "Context:\n{context}\n\nQuestion:\n{query}"


class GenerationInputError(Exception):
    """The supplied `Prompt` does not satisfy `docs/GENERATION_CONTRACT.md` §24.4.

    Distinct from every `sample_rag/deepseek.py` provider failure, and
    deliberately: this is a **context assembly** failure observed at the
    generation seam — the artifact arrived internally inconsistent — and it is
    raised **before** any provider interaction, so a malformed `Prompt` never
    spends a sanctioned call.

    Named and module-level, following `ContextAssemblyError`,
    `ChunkConstructionError` and `DocumentConstructionError`.
    """


class ModelGenerator:
    """Produces an evidenced answer from an assembled `Prompt` — §24.2.

    Bound at construction to the two things a generation is performed *with*
    rather than *about*: the provider client, and the retrieval route that fed
    the assembly. Both are required, and neither has a default.

    **The client is a required argument, not a default construction.** A
    `ModelGenerator()` that quietly built its own live client would make the
    sanctioned provider interaction reachable by accident — from a fixture, a
    doctest, or a caller that meant to pass a fake. Requiring it makes every
    call site state which provider it is talking to, which is what a boundary
    *"for one call, not a category of access"* needs at the point it is crossed.

    **`retrieval_route` is a required argument for the same reason.** §8.4
    requires the key and §24.5 records that under v2 the route is *"carried on
    the `Prompt`'s provenance chain rather than copied from a consumed
    `RetrievalResult`"*, leaving *"how it reaches the artifact"* to M2-06. It
    reaches it from the caller that ran retrieval, because that caller is the
    only participant that knows the answer: §24.4 authorizes no fifth `Prompt`
    field to carry it, and a default here would be this module **inventing** a
    route rather than recording one. Construction-time binding is the
    repository's existing shape for a pipeline property — `Retriever` and
    `ContextBuilder` both bind their corpus the same way — and it keeps §24.2's
    `generate(prompt)` signature exact.

    Stateless beyond that binding. Every value emitted is derived from one
    call's `Prompt` plus one provider response, so no call can observe another.

    Owns the ALTM **Infer** stage (`docs/glossary.md`). Post-Process is not
    exercised, so *Raw Output* and *Delivered Output* (`docs/altm.md` §4)
    coincide in this artifact — the same position `docs/GENERATION_CONTRACT.md`
    §21 recorded, and one v2.0.0 does not change.
    """

    def __init__(self, client: DeepSeekClient, retrieval_route: str):
        self._client = client
        self._retrieval_route = retrieval_route

    def generate(self, prompt: Prompt) -> GenerationResult:
        """Generate one evidenced answer from an assembled `Prompt` — §24.2.

        `Generator.generate(prompt: Prompt) -> GenerationResult`, the **U-1**
        resolution, implemented at that signature exactly. One argument, and the
        only permitted runtime input beside the sanctioned provider call
        (§24.3's G-13 transition).

        **The order of operations is the security property, not an incidental
        arrangement.** Statements and evidence are constructed from the `Prompt`
        *first*; the provider is called only if that succeeded and only if there
        is evidence to answer from. So:

        - a `Prompt` violating §24.4 raises before any call is made;
        - the Abstain path makes **no** provider call at all;
        - the evidence in the result was fixed before the model produced a
          syllable of the answer, which is what makes *"evidence grounded in the
          `Prompt`"* structural rather than a claim about model behaviour.

        **Abstention is decided from the `Prompt`, never from the answer**
        (§9.3, unchanged by v2.0.0). The outcome is `Abstain` exactly when the
        assembled prompt carries no evidence — which under §24.2's pipeline is
        exactly when retrieval produced no chunk. G-8's biconditional is
        structural here, as it was under v1.0.0: `statements` and `outcome` are
        decided by one emptiness test, so they cannot disagree. A model that
        replies *"I don't know"* still produces an `Answer` with its evidence
        attached, because the corpus **did** supply evidence and what the model
        made of it is an evaluation question (**M2-07**, **M2-08**), not an
        outcome.

        **A provider failure is never a `GenerationResult`.** Every failure path
        in `sample_rag/deepseek.py` propagates as its own exception; no branch
        below converts one into an answer, an abstention, an empty string or a
        partial artifact.

        Returns observed generation only. Nothing here consults the Evidence
        Trace Dataset or any expectation, and nothing here expresses whether the
        answer was correct — that comparison belongs to the evaluation layers,
        and **this artifact carries no quality claim of any kind**.
        """
        statements = self._statements(prompt)

        # §8.4 — the three required keys, in that table's order, which §13.2
        # makes the serialized key order. No fourth key is added: §24.5 states
        # that *"no new required key is added here"*, and §24.4 authorizes no
        # new `GenerationResult` field. No timestamp, no measured duration, no
        # token count and no latency — §15 defers `generation_time_ms` and
        # RO-13 leaves that deferral standing, so latency is sprint evidence and
        # does not enter the artifact.
        diagnostics = {
            "query": prompt.query,
            "retrieval_route": self._retrieval_route,
            "stub": GENERATION_STUB,
        }

        if not statements:
            return GenerationResult(
                answer_text=ABSTENTION_TEXT,
                outcome=OUTCOME_ABSTAIN,
                statements=[],
                diagnostics=diagnostics,
            )

        return GenerationResult(
            answer_text=self._answer(prompt),
            outcome=OUTCOME_ANSWER,
            statements=statements,
            diagnostics=diagnostics,
        )

    def _statements(self, prompt: Prompt) -> list:
        """Derive the evidenced statements from the `Prompt` alone — G-7, G-13.

        One statement per assembled chunk, each carrying exactly the one span
        that chunk contributed. **The model participates in none of this.**

        **Why the statements are not derived from the model's answer.** §24.3
        narrows G-7 for `answer_text` only — *"MAY be synthesized by the
        model"* — while `SupportingEvidence` *"SHALL remain grounded in the
        assembled `Prompt` context and its provenance, and in nothing else"*.
        The provider's chat-completion contract carries **no citation or
        evidence-selection mechanism**: no field identifies which supplied span
        a sentence came from. Splitting prose into claims and attributing each
        to a chunk would therefore be this module *inventing* an attribution the
        provider never made — and an invented citation is worse than none,
        because it is checkable-looking. So the evidence chain records what is
        actually known: these spans were assembled, and this answer was produced
        with them present.

        That is the whole of the claim. **It is not a claim that the answer uses
        the evidence, is entailed by it, or is free of content beyond it** —
        those are Faithfulness and Groundedness, are Layer 3/4 metrics, and are
        §21-excluded and RO-13-disclaimed.

        **Ordering is §11.1's, by construction.** Statements are emitted in
        `provenance` order, which is assembled chunk order, which is the
        retrieval rank `sample_rag/fusion.py` already froze and the Context
        Builder preserved. No sort is applied because there is nothing to
        reorder, and §11.1's tie-break is unreachable: each statement's rank is
        the distinct position of its own chunk.

        §17 invariant 11 (no repeated span within a statement) holds because
        there is exactly one, and §11.2's within-statement ordering is trivially
        total for the same reason.
        """
        return [
            GeneratedStatement(text=evidence.text, supporting_evidence=[evidence])
            for evidence in self._evidence(prompt)
        ]

    def _evidence(self, prompt: Prompt) -> list:
        """Reconstruct each assembled chunk's span from `context` and `provenance`.

        §24.4's *"`SupportingEvidence.text` remains derivable without it"*, made
        executable — the claim that justified keeping chunk text out of
        `provenance`, discharged by the consumer it was made for.

        **By offset arithmetic, not by splitting on the separator.** `context`
        is the separator-joined block sequence, and block *i*'s length is
        `character_end - character_start` because `docs/CHUNK_CONTRACT.md` §17
        invariant 3 freezes `text == document_text[character_start:character_end]`
        for every chunk. Walking those lengths recovers each block exactly.
        Splitting on `CONTEXT_SEPARATOR` would have been shorter and would be
        **wrong on any chunk whose own text contains a blank line** — the
        Context Builder documents its assembly as reversible only over a corpus
        where none does, and a consumer that inherited that condition would
        silently mis-attribute evidence on the day the corpus stopped meeting
        it. Offsets carry no such condition.

        **The arithmetic is checked, not trusted.** A `Prompt` whose
        `provenance` and `context` disagree — wrong lengths, a mismatched
        `chunk_ids`, a non-positive span — raises `GenerationInputError` rather
        than yielding a span sliced from the wrong place. §17 invariant 6
        (`len(text) == character_end - character_start`) then holds by
        construction, and invariant 9 (the span lies within its chunk) holds
        with equality on both bounds.

        The offsets and identities are copied through unchanged, never
        recomputed: G-6's *"the Generator never constructs a chunk id"* is as
        true here as it was under v1.0.0, and the ids reach `SupportingEvidence`
        exactly as the corpus wrote them. The **model cannot influence any of
        it** — no identifier in the result has passed through the provider.
        """
        if len(prompt.chunk_ids) != len(prompt.provenance):
            raise GenerationInputError(
                "The supplied Prompt carries "
                f"{len(prompt.chunk_ids)} chunk ids and "
                f"{len(prompt.provenance)} provenance records; "
                "docs/GENERATION_CONTRACT.md §24.4 requires them to correspond."
            )

        evidence, cursor = [], 0
        for chunk_id, record in zip(prompt.chunk_ids, prompt.provenance):
            if record.chunk_id != chunk_id:
                raise GenerationInputError(
                    f"Prompt provenance names chunk {record.chunk_id!r} where "
                    f"chunk_ids names {chunk_id!r}; docs/GENERATION_CONTRACT.md "
                    "§24.4 requires the two orderings to correspond."
                )

            length = record.character_end - record.character_start
            if length <= 0:
                raise GenerationInputError(
                    f"Prompt provenance for chunk {chunk_id!r} spans "
                    f"{length} characters; a span must be non-empty."
                )

            evidence.append(
                SupportingEvidence(
                    chunk_id=record.chunk_id,
                    document_id=record.document_id,
                    character_start=record.character_start,
                    character_end=record.character_end,
                    text=prompt.context[cursor : cursor + length],
                )
            )
            cursor += length + len(CONTEXT_SEPARATOR)

        consumed = cursor - len(CONTEXT_SEPARATOR) if evidence else 0
        if consumed != len(prompt.context):
            raise GenerationInputError(
                f"Prompt provenance accounts for {consumed} characters of a "
                f"{len(prompt.context)}-character context; the two do not "
                "describe the same assembly."
            )

        return evidence

    def _answer(self, prompt: Prompt) -> str:
        """Obtain `answer_text` through the one sanctioned provider interaction.

        The single point in the repository where a model produces a value that
        reaches an artifact. Called at most once per `generate`, and not at all
        on the Abstain path.

        **Exactly two values leave the repository**: `prompt.context`, which is
        corpus text the model needs in order to answer, and `prompt.query`,
        which is the question. **Nothing else is transmitted** — not a chunk id,
        a document id, a character offset, a retrieval score, an RRF rank, a
        corpus path, a manifest digest, a repository identity or a credential
        beyond the transport header `sample_rag/deepseek.py` applies. §24.4's
        provenance exists so the *repository* can construct evidence; the model
        has no use for it and is not shown it.

        The message construction is deterministic — two fixed strings and two
        `Prompt` values — so the request document is a total function of the
        `Prompt` and the client's configuration (§24.3, request construction).

        **No claim is made about the returned text's quality, faithfulness or
        groundedness.** It is recorded as `answer_text` because the provider
        produced it, and that is the entire assertion.
        """
        return self._client.complete(
            [
                {"role": "system", "content": SYSTEM_INSTRUCTION},
                {
                    "role": "user",
                    "content": USER_TEMPLATE.format(
                        context=prompt.context, query=prompt.query
                    ),
                },
            ]
        )
