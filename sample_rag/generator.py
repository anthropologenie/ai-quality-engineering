"""Deterministic Generation Runtime.

Sprint P3.5.2: implements the `Generator` pipeline component
(docs/architecture.md §5) returning the `GenerationResult` contract frozen by
`docs/GENERATION_CONTRACT.md` v1.0.0, approved and frozen at Sprint P3.5.1-G.

This module implements an approved contract. It makes no architectural decision:
every public name below traces to a numbered clause of that document, and the
five implementation choices the contract explicitly delegates (§20.2) are
recorded at their point of use with the guarantee each is justified against.

Generation path implemented here:

    query + RetrievalResult -> GenerationResult

Read-only, and structurally so (G-14): no filesystem I/O, no network I/O, and no
mutation of the `RetrievalResult` it consumes. Nothing here reads a repository
authority — not the Knowledge Manifest, the Golden Dataset, the QA Dataset, the
Evidence Trace Dataset, the Chunk Corpus as a file, nor any evaluation layer
(G-13, contract §18). The Generator sees exactly what retrieval handed it, which
is what keeps it capable of answering an arbitrary future query rather than only
the repository's 22 benchmark questions.

No `Prompt`, no Context Builder, no Assemble stage, and no inference. Contract
§6.2 records the approved Milestone 1A signature — `generate(query, retrieval)` —
and why the `docs/architecture.md` §5 `generate(prompt: Prompt)` signature is the
Milestone 2 target rather than this sprint's.

Determinism by exclusion (§12)
------------------------------
No timestamp, no measured duration, no random or hash-seed-dependent value, no
floating-point value, and no set or dict iteration order reaching a serialized
sequence. Repeated execution over an identical query and corpus state therefore
produces equal results and byte-identical serialization (G-9) because the values
that would break it are not constructed, not because a test checks afterwards —
the discipline `docs/MILESTONE_1A.md` build item 1 applied when it removed
`created_at`, and `sample_rag/retriever.py` applied when it fixed
`retrieval_time_ms` at 0.

The outcome literals, duplicated deliberately (§20.4, D-12)
------------------------------------------------------------
`OUTCOME_ANSWER` and `OUTCOME_ABSTAIN` also exist in
`scripts/build_evidence_trace.py`. They are **not** imported from there:
`docs/architecture.md` §6 bars `sample_rag/` from importing `scripts/`, and the
repository has already accepted deliberate duplication over violating that
direction (`SUPPORTED_EXTENSIONS`, register AH-9, recorded in
`sample_rag/retriever.py`'s own module docstring). Contract §20.4 permits this
duplication and asks that it be *checked* rather than trusted;
`tests/test_generator.py` asserts the two definitions agree, which turns the
duplication from a maintenance risk into a mechanically verified invariant.
"""

import json

from dataclasses import asdict, dataclass

from sample_rag.retriever import RetrievalResult

# docs/GENERATION_CONTRACT.md §9.1 — the Milestone 1A outcome domain, adopted
# verbatim from docs/roadmap.md §2.4. `Clarify` is defined by that authority and
# is outside Milestone 1A, so it is never emitted (G-2).
OUTCOME_ANSWER = "Answer"
OUTCOME_ABSTAIN = "Abstain"

# §8.1 / §9.3 — the fixed abstention text. Non-empty on every path (G-3), and it
# asserts nothing about the corpus: it reports what retrieval returned, and makes
# no claim about whether the corpus could answer the query. That distinction is
# the whole point of §9.3 — a text reading "the corpus does not contain this"
# would be an unevidenced claim about repository knowledge, which is exactly what
# `ALTM-INFER-2` (false confidence on an unanswerable question) describes.
ABSTENTION_TEXT = "No supporting evidence was retrieved for this query."

# §8.4 — the Milestone 1A stub marker, following the `RetrievalResult`
# `diagnostics["stub"]` precedent and docs/architecture.md §9's record of
# Generation as a Milestone 1A stub. Milestone 2's DeepSeek `Generator` (**M2-06**)
# is where this changes.
#
# It no longer *mirrors* the retrieval marker's value, and deliberately so: the
# lexical route's marker reads `False` from Sprint M2.03, where BM25 replaced the
# overlap scorer (`sample_rag/retriever.py` `LEXICAL_STUB`), while generation is
# still the deterministic quotation stub. The two markers report two components,
# which is the whole reason each carries its own — a shared value would have made
# one stage's Milestone 2 arrival silently speak for the other's.
GENERATION_STUB = True

# Delegated decision 4 (§20.2) — the deterministic separator by which statements
# are assembled into `answer_text`. A line separator carries no claim of its own,
# so §8.1's "contains no content not present in them" holds: every character of
# `answer_text` other than the separators comes from a statement, and the
# assembly is reversible over any corpus whose statement texts exclude it.
STATEMENT_SEPARATOR = "\n"


@dataclass(frozen=True)
class SupportingEvidence:
    """One citable span of committed corpus evidence — contract §7, §8.3.

    Field order is §7's declaration order, which §13.2 makes the serialized key
    order. Frozen because the artifact records what happened and no consumer has
    a reason to mutate it (§13.1).

    Offsets are **document-frame** — zero-based, inclusive start, exclusive end,
    Unicode code points — the same reference frame `Chunk.character_start` and
    `character_end` use (`docs/CHUNK_CONTRACT.md` §13). This is the repository's
    only offset coordinate system, and a chunk-frame offset would be a second,
    incompatible one over the same corpus (§8.3).

    This is the runtime realization of "a supporting fact" (§7.1). It is named
    `evidence` rather than `fact` because `fact` belongs to
    `datasets/golden/resume_facts.json`, an authority the Generator may not read
    — and the two remain joinable at validation time through `chunk_id`.
    """

    chunk_id: str
    document_id: str
    character_start: int
    character_end: int
    text: str


@dataclass(frozen=True)
class GeneratedStatement:
    """One individually evidenced claim — contract §7, §8.2.

    `supporting_evidence` is non-empty for every statement this module
    constructs (G-4). The contract calls the empty list "not a representable
    state", and it is not one here: a statement is only ever constructed from a
    span, so there is no code path that could produce one without evidence.

    A statement rather than a single answer string is what makes Groundedness
    — *"can every individual claim be traced to a specific, citable piece of
    evidence"* (`docs/AI_Quality_Metrics_Reference.md` Layer 4) — a checkable
    property of the artifact rather than a judgement about it.
    """

    text: str
    supporting_evidence: list


@dataclass(frozen=True)
class GenerationResult:
    """The Generation artifact frozen by `docs/GENERATION_CONTRACT.md` §17.

    Exactly the four fields of §8.1 — no more, no less. Field order is §7's, and
    every field carries a meaningful value on every path including the Abstain
    path; none is ever `None` (G-1). `diagnostics` is the contract's own open
    mapping, the same role it plays in `RetrievalResult` (§8.1, D-5), and is
    where per-request detail lives instead of new top-level fields.

    `statements` is empty if and only if `outcome` is `Abstain` (G-8) — a
    biconditional, not an implication, and one this module satisfies
    structurally: both are derived from the same emptiness test in `generate`.
    """

    answer_text: str
    outcome: str
    statements: list
    diagnostics: dict


def serialize(result: GenerationResult) -> str:
    """Serialize a `GenerationResult` under contract §13.2.

    `json.dumps(..., indent=2) + "\\n"`, UTF-8, insertion-order keys — the
    convention `write_manifest`, `write_chunks` and `write_evidence_trace`
    already share. Keys are not sorted: §7's declaration order *is* the
    contract's order, and `dataclasses.asdict` preserves it, so re-sorting would
    discard information the contract carries.

    A module-level function rather than a method, because §13 requires the
    semantic model and its serialization to remain separate concepts — the
    `GenerationResult` of §7 is satisfiable by representations this function
    knows nothing about, and a method would couple the two.

    Persists nothing (§13.3). `GenerationResult` is a Runtime Artifact
    (`docs/CHUNK_CONTRACT.md` §5): query-derived, single-request, never written
    to `datasets/`, `reports/` or `sample_rag/`. Byte-identical output is
    required (G-9) so that two runs are *comparable*, which is a property worth
    having whether or not anything is written to disk.
    """
    return json.dumps(asdict(result), indent=2) + "\n"


class Generator:
    """Produces an evidenced answer from completed retrieval output.

    `docs/architecture.md` §5: *"Produce an answer from an assembled prompt"*,
    status *"1A — deterministic stub generator"*. The Milestone 1A signature is
    contract §6.2's approved `generate(query, retrieval)`; the §5 signature
    `generate(prompt: Prompt)` is the Milestone 2 target, reached when a Context
    Builder exists to produce a `Prompt`.

    Stateless: unlike `Retriever`, which binds to a chunk collection, the
    Generator holds nothing between calls. Every value it emits is derived from
    the two arguments of a single call, so two calls with equal arguments cannot
    differ (G-9), and no call can observe another.

    Owns the ALTM **Infer** stage (`docs/glossary.md`). Post-Process is not
    exercised in Milestone 1A, so *Raw Output* and *Delivered Output*
    (`docs/altm.md` §4) coincide in this artifact — contract §21.
    """

    def generate(self, query: str, retrieval: RetrievalResult) -> GenerationResult:
        """Generate one evidenced answer.

        The two permitted runtime inputs, and the only two (§18, G-13): the
        request `query`, and a completed `RetrievalResult`.

        **Delegated decision 1 — the abstention predicate (§20.2).** The outcome
        is `Abstain` exactly when retrieval returned no chunk. Contract §9.3
        defines Abstain as the outcome *"produced when the consumed
        `RetrievalResult` yields no evidence the Generator can quote"*, and with
        one span per retrieved chunk (decision 2) a chunk is quotable evidence
        and no chunk is none. This makes G-8's biconditional structural rather
        than checked: `statements` and `outcome` are both decided by the single
        emptiness test below, so they cannot disagree.

        **Delegated decision 5 — retrieved-chunk selection (§20.2).** Every
        chunk of `retrieval.chunks` is used, in the order retrieval ranked them.
        The Retriever has already applied its own `top_k`; re-filtering here
        would be the Generator overriding a decision the retrieval contract
        already made, and would make the statement ordering of §11.1 depend on a
        second, undocumented cutoff.

        **Ordering (§11.1, G-10)** is satisfied by construction: statements are
        emitted in `retrieval.chunks` order, which *is* retrieval rank, which
        `rank_candidates` already froze as descending score then ascending
        committed corpus position. No sort is applied, because there is nothing
        to reorder — and §11.1's tie-break is unreachable here, since each
        statement's rank is the distinct position of its own chunk.

        Returns observed generation only. Nothing here consults the Evidence
        Trace Dataset or any expectation, and nothing here expresses whether the
        answer was correct; that comparison belongs to the evaluation layers.
        """
        statements = [self._statement(chunk) for chunk in retrieval.chunks]

        # §8.4 — the three required keys, in that table's order, which §13.2
        # makes the serialized key order. `retrieval_route` is copied from the
        # consumed result, never re-derived (§8.4). Nothing here varies between
        # runs on identical input (§12).
        diagnostics = {
            "query": query,
            "retrieval_route": retrieval.retrieval_route,
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
            answer_text=self._assemble(statements),
            outcome=OUTCOME_ANSWER,
            statements=statements,
            diagnostics=diagnostics,
        )

    def _statement(self, chunk: dict) -> GeneratedStatement:
        """Derive one evidenced statement from one retrieved chunk.

        **Delegated decision 2 — span selection (§20.2).** The span is the whole
        chunk. Contract §20.2 records this as *"the simplest conforming
        choice"*, and it is the one that makes G-11 — `text` equals
        `document_text[character_start:character_end]` — hold on a corpus
        invariant the repository already validates rather than on this module's
        own slicing: `docs/CHUNK_CONTRACT.md` §17 invariant 3 freezes exactly
        that relationship for every chunk. A narrower span would make the
        verbatim guarantee depend on arithmetic performed here, with no document
        text available at runtime to check it against.

        §17 invariant 9 (the span lies within the chunk it cites) holds with
        equality on both bounds, and invariant 11 (no repeated span within a
        statement) holds because there is exactly one.

        **Delegated decision 3 — statement construction (§20.2).** The statement
        text is the span's text, quoted verbatim, one statement per chunk. G-7
        permits *"verbatim quotation and deterministic template assembly"*;
        quotation with no template is the narrowest option G-7 allows, and it is
        the only one under which "supported by construction" needs no argument
        beyond identity — the statement *is* its evidence.

        §11.2's within-statement ordering is trivially total: one span cannot be
        out of order with itself, and no sort is applied because there is
        nothing to sort. A future implementation emitting several spans per
        statement would sort them by `(document_id, character_start)`.

        Reads the chunk mapping; never writes to it (G-14).
        """
        evidence = SupportingEvidence(
            chunk_id=chunk["id"],
            document_id=chunk["document_id"],
            character_start=chunk["character_start"],
            character_end=chunk["character_end"],
            text=chunk["text"],
        )

        return GeneratedStatement(text=evidence.text, supporting_evidence=[evidence])

    def _assemble(self, statements: list) -> str:
        """Assemble statement texts into one delivered answer.

        **Delegated decision 4 — `answer_text` assembly (§20.2).** Statement
        texts joined by `STATEMENT_SEPARATOR`, in `statements` order. §8.1
        requires the assembled text to contain *"no content not present in
        them"*: every character here other than the separators comes from a
        statement, and no reordering, truncation, summarization or connective
        text is introduced — any of which would be this module asserting
        something its evidence does not carry.

        Deterministic: a fixed separator over an already-ordered list.
        """
        return STATEMENT_SEPARATOR.join(statement.text for statement in statements)
