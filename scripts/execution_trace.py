"""Execution-evidence recording for a completed pipeline run — Sprint M2.18.

Register capability **M2-18** — *"Execution Evidence / Traceability"* —
implemented under Repository Owner ruling **RO-15**
(`docs/DEFERRED_ITEMS_REGISTER.md` §4.7).

What this module is
--------------------
An **evidence layer**, not a pipeline stage. It observes an execution that has
already happened and writes down enough of it to answer, after the process has
exited, *"what actually happened during this run, and why did the system
produce this result?"*

RO-15 Decision 9 fixes that standing: the capability sits **across** the
existing `Retrieve → Assemble → Infer` path and makes already-existing runtime
artifacts durable. It creates no ALTM stage, does not widen `REACHABLE_STAGES`,
and is not an orchestration capability.

What a trace record is, and is not
-----------------------------------
**A distinct execution-evidence envelope** (RO-15 Decision 3), **not** a
serialized `GenerationResult`. `GenerationResult` is the runtime *generation*
artifact; this envelope is a *cross-stage* record about the execution that
produced it.

That distinction is what RO-15 Decision 4 rests on:
`docs/GENERATION_CONTRACT.md` §13.2 / §13.3 govern the serialization of a
`GenerationResult` and of approved persisted artifacts **of that type**. This
envelope is a different artifact and does not become one by containing a
projection of generation evidence — so §13.2's `json.dumps(..., indent=2)` form
does not define this file's storage representation. **JSONL is the authorized
v1 representation**, and one line of JSON cannot carry `indent=2`.

Why `scripts/` and not `sample_rag/`
-------------------------------------
`docs/architecture.md` §6 gives `sample_rag/` *"the pipeline under test"* and
`scripts/` *"operational scripts … not pipeline logic"*. Recording evidence
about an execution is not pipeline logic, and placing it in `sample_rag/` would
make it a pipeline component — which would need an `docs/architecture.md` §5
component row, and **RO-15 modifies no architecture document**. The repository
already holds `build_chunks.py`, `build_manifest.py` and
`build_evidence_trace.py` here: `scripts/` modules that write derived artifacts.
This is a further instance of that seam, not a new mechanism.

**Nothing in `sample_rag/` learns about tracing.** `sample_rag/generator.py`
and `sample_rag/model_generator.py` are untouched and carry no trace metadata:
RO-15 Decision 7 puts component identity at the *observation* boundary, which
is here, and this module reads it off the objects it is handed rather than
asking them to describe themselves.

What is deliberately not recorded
----------------------------------
**Never, under any configuration:** API keys, bearer tokens, `Authorization`
headers, provider secrets, raw provider request bodies and raw provider
response payloads. This module never receives a credential — `DeepSeekClient`
reads `DEEPSEEK_API_KEY` inside `complete` and exposes no accessor — so
credential absence is structural here rather than a promise about a code path.

**Not recorded because the boundary does not expose it:** semantic similarity
scores. `docs/architecture.md` §7 fixes `VectorStore.query -> list[str]`, ids
and not distances, and RO-15 Decision 5 bars widening that contract or
inventing an alternative path to a score. **Semantic rank is authorized;
semantic score is not**, and rank is a property of the returned sequence.

**Not recorded because no repository convention exists:** a wall-clock
timestamp and a synthetic execution identifier. Neither exists anywhere in
`sample_rag/` or `scripts/`, and RO-15 authorizes recording evidence that is
*available*, not manufacturing instrumentation to populate a field. Recorded as
a limitation in `docs/M2.18_Execution_Evidence_Report.md` rather than invented
here.

**Not duplicated:** chunk text, `Prompt.context`, `SupportingEvidence.text` and
`GeneratedStatement.text`. RO-15 Decision 6 says persist what cannot otherwise
be recovered and reference what can; §24.4 already established that a span
*"remains derivable"* from context and offsets, and chunk ids plus provenance
reach the committed corpus deterministically.
"""

import json
import pathlib

from sample_rag.fusion import RRF_SCORE_PRECISION

# The derived runtime artifact's default location, and the file it appends to.
#
# **RO-15 Decision 8 classifies traces as derived runtime artifacts, in the
# class RO-09 fixed for the FAISS index**, and this mirrors that precedent
# structurally: `scripts/execution_trace/` is the ignored runtime directory and
# `scripts/execution_trace.py` is committed source, exactly as
# `sample_rag/vector_index/` is ignored while `sample_rag/vector_index.py` is
# committed. The `.gitignore` rule names the directory for that reason.
#
# RO-15 deliberately prescribes no path, so this is an engineering decision of
# this sprint and is a default rather than a constant read at the point of use:
# every function below takes the destination as an argument, which is what lets
# a specification write to `tmp_path` and never touch this directory.
TRACE_ROOT = pathlib.Path(__file__).resolve().parent / "execution_trace"
TRACE_FILENAME = "executions.jsonl"

# Generation contract era, by observed component name — RO-14 Decision 1 and
# RO-15 Decision 7.
#
# `ModelGenerator` is the Milestone 2 model-backed component and carries
# **v2.0.0** (`docs/GENERATION_CONTRACT.md` §24). The frozen Milestone 1A
# `Generator` carries v1.0.0 and is deliberately **absent**: `scripts/cli.py`
# is not wired to this module and RO-15 authorizes no change to the Milestone
# 1A path, so recording a v1.0.0 era here would describe an execution the
# repository does not trace. An unrecognized component raises rather than
# defaulting — a guessed contract version is fabricated evidence.
CONTRACT_VERSIONS = {"ModelGenerator": "2.0.0"}


class TraceIntegrityError(Exception):
    """A trace was asked to record references that contradict one another.

    Raised rather than written. RO-15 authorizes a **diagnostic** artifact, and
    a diagnostic artifact whose internal references dangle is worse than no
    artifact: it looks checkable. The three relationships checked below —
    selected ⊆ scored, provenance ⊆ candidates, evidence ⊆ provenance — are all
    guaranteed by the current runtime, so this exception is a specification of
    that guarantee rather than a handler for an expected condition.
    """


def candidate_evidence(route_rankings: dict, scored: list) -> list:
    """Describe every candidate in the union, with its per-route attribution.

    `route_rankings` maps a route name to that route's ranked id list, and
    `scored` is `sample_rag.fusion.rank_candidates` output — `(chunk_id, score)`
    over the whole union, best first. Both are what the execution already
    produced; nothing here re-ranks, re-scores or re-retrieves.

    **Rank is position, because that is what a ranked list means.** Each route
    returns `list[str]` and RRF itself reads nothing but position from them
    (`sample_rag/fusion.py` `positional_ranks`). Reading position back out is
    not a second computation of the ranking — it is the ranking.

    **`source_legs` is the route a candidate actually entered through**, taken
    from membership in that route's returned ids. It is not the chunk's
    document, file type, corpus or category, and a chunk is not labelled
    semantic merely because the semantic index contains it — every corpus chunk
    is in that index, so such a label would attribute nothing. A candidate both
    routes returned carries both legs, which is the case RRF's score is
    summed over.

    **A route that did not supply a candidate yields `None`, never `0`.** Zero
    is a rank in a 1-based scheme's neighbourhood and would read as "ranked
    first-ish"; absence is not a rank at all, and the record says so.

    Route names are the caller's — `SEMANTIC` and `LEXICAL` are fixed by
    `scripts/run_hybrid_retrieval.py`, and this module does not restate them.
    The repository's `LEXICAL` route **is** BM25 (`sample_rag/retriever.py`),
    which is what RO-15's authorized *"BM25 rank"* names.
    """
    ranks = {
        route: {chunk_id: position for position, chunk_id in enumerate(ranked, start=1)}
        for route, ranked in route_rankings.items()
    }

    candidates = []
    for position, (chunk_id, score) in enumerate(scored, start=1):
        candidate = {
            "chunk_id": chunk_id,
            "source_legs": sorted(route for route in ranks if chunk_id in ranks[route]),
        }
        for route in route_rankings:
            candidate[f"{route.lower()}_rank"] = ranks[route].get(chunk_id)

        candidate["rrf_rank"] = position
        candidate["rrf_score"] = round(score, RRF_SCORE_PRECISION)
        candidates.append(candidate)

    return candidates


def retrieval_evidence(route: str, top_k: int, route_rankings: dict, scored: list, selected: list) -> dict:
    """Record what retrieval produced, and check the selection against it.

    `selected` is the fused id list the execution actually assembled from — the
    output of `scripts/run_hybrid_retrieval.py` `fuse_routes`, which is the
    repository's own fusion entry point and remains the authority for *which*
    chunks were chosen. It is not recorded as a field, because
    `assembly.provenance` already carries the selected ids in order; it is used
    here to verify that the scored union this record describes is the same
    ranking the execution selected from.

    **That check is the reason `scored` may be read from a second call to
    `rank_candidates`.** `reciprocal_rank_fusion` calls exactly that function
    and truncates its output, so the two are pure functions of identical inputs
    and cannot disagree — but "cannot disagree" is asserted here rather than
    assumed, and a disagreement raises instead of being written down.
    """
    ordered = [chunk_id for chunk_id, _ in scored]
    if list(selected) != ordered[: len(selected)]:
        raise TraceIntegrityError(
            "the selected chunk order is not the leading order of the scored candidate union"
        )

    return {
        "route": route,
        "top_k": top_k,
        "candidates": candidate_evidence(route_rankings, scored),
    }


def assembly_evidence(prompt) -> dict:
    """Record the provenance the `Prompt` carried into generation.

    **The four fields of `docs/GENERATION_CONTRACT.md` §24.4 and no other** —
    `chunk_id`, `document_id`, `character_start`, `character_end` — copied in
    assembled order. `Prompt` is not modified, extended or re-typed to produce
    this; the record is read off the artifact the execution already built.

    **The selected chunk ids are these `chunk_id` values, in this order.**
    `ContextBuilder.assemble` builds `chunk_ids` and `provenance` from the same
    sequence positionally, so `provenance[i].chunk_id == prompt.chunk_ids[i]`,
    and recording both lists would be two copies of one fact — which RO-15
    Decision 6 excludes and which could, uniquely among this record's fields,
    come to disagree with itself.

    **`Prompt.context` is deliberately absent.** It is corpus text, §24.4
    records that a span *"remains derivable"* from offsets, and the ids above
    reach the committed corpus deterministically.
    """
    if [record.chunk_id for record in prompt.provenance] != list(prompt.chunk_ids):
        raise TraceIntegrityError("prompt provenance does not correspond to the assembled chunk ids")

    return {
        "provenance": [
            {
                "chunk_id": record.chunk_id,
                "document_id": record.document_id,
                "character_start": record.character_start,
                "character_end": record.character_end,
            }
            for record in prompt.provenance
        ]
    }


def generation_evidence(generator, client, result, latency_ms: float) -> dict:
    """Record which component generated what, through which provider.

    **Component identity is observed, not declared.** `type(generator).__name__`
    reads the class that actually ran, so a trace cannot claim a component the
    execution did not use. `contract_version` comes from `CONTRACT_VERSIONS`,
    the governance fact RO-14 Decision 1 fixed and RO-15 Decision 7 places at
    this boundary — an unrecognized component raises rather than being given a
    guessed era.

    **`answer_text` is persisted, and it is the one generation field that must
    be.** `docs/GENERATION_CONTRACT.md` §24.3 splits G-9: structural determinism
    holds, and **model-output reproducibility is expressly not guaranteed**. An
    answer that is not reproducible cannot be recovered by re-running the
    execution, so it is evidence in RO-15 Decision 6's sense rather than a
    convenience copy.

    **`statement_evidence_chunk_ids` references, it does not duplicate.** Each
    statement's cited chunk ids are recorded; `document_id`, both offsets and
    the span text are all reachable through `assembly.provenance` and the
    committed corpus. `GeneratedStatement.text` is the span text itself and is
    omitted for the same reason.

    **`GenerationResult.diagnostics` is omitted entirely.** Its three keys are
    `query`, `retrieval_route` and `stub`; the first two are already recorded at
    the boundaries that own them, and `stub` is a milestone marker that
    `component` and `contract_version` state more precisely.

    **No credential, header, endpoint or provider payload is read here.** The
    provider is identified by class name and selected model, which is what
    `scripts/run_generation.py` already treats as safe evidence.
    """
    component = type(generator).__name__
    if component not in CONTRACT_VERSIONS:
        raise TraceIntegrityError(
            f"no generation contract version is recorded for component {component!r}"
        )

    return {
        "component": component,
        "contract_version": CONTRACT_VERSIONS[component],
        "provider": type(client).__name__,
        "model": client.model,
        "outcome": result.outcome,
        "answer_text": result.answer_text,
        "statement_evidence_chunk_ids": [
            [evidence.chunk_id for evidence in statement.supporting_evidence]
            for statement in result.statements
        ],
        "latency_ms": round(latency_ms, 1),
    }


def build_trace(query: str, retrieval: dict, assembly: dict, generation: dict) -> dict:
    """Compose one completed execution's evidence into one record.

    **One completed execution, one record** (RO-15 Decision 4). Composition
    only: every value below was produced by the stage that owns it, and nothing
    here derives, adjusts or re-orders evidence.

    **Reference integrity is checked before the record exists**, not after it is
    written. Every chunk id a statement cites must appear in the assembled
    provenance, and every assembled chunk must appear among the retrieval
    candidates — so a record can never carry evidence for a chunk that never
    reached the prompt, or a prompt chunk that retrieval never produced. The
    current runtime guarantees both; this states the guarantee rather than
    trusting it.
    """
    candidates = {candidate["chunk_id"] for candidate in retrieval["candidates"]}
    assembled = [record["chunk_id"] for record in assembly["provenance"]]

    if not set(assembled) <= candidates:
        raise TraceIntegrityError("an assembled chunk is absent from the retrieval candidate union")

    for cited in generation["statement_evidence_chunk_ids"]:
        if not set(cited) <= set(assembled):
            raise TraceIntegrityError("a statement cites a chunk absent from the assembled prompt")

    return {
        "query": query,
        "retrieval": retrieval,
        "assembly": assembly,
        "generation": generation,
    }


def serialize(trace: dict) -> str:
    """Serialize one trace record as one JSONL line.

    **One execution = one JSON object = one line**, which is what makes the file
    appendable and readable a record at a time.

    **Deliberately not `docs/GENERATION_CONTRACT.md` §13.2's form**, and this is
    the concrete consequence of RO-15 Decision 4: §13.2 fixes
    `json.dumps(result, indent=2) + "\\n"` for a **`GenerationResult`**, and an
    indented object spans many lines, which JSONL cannot carry. The two forms
    differ because the two artifacts differ — the trace envelope is not a
    `GenerationResult`, so §13.2 does not reach it. §13.2 remains in force,
    unamended, for the artifact it governs.

    Keys are not sorted: insertion order is the schema order
    `docs/M2.18_Execution_Evidence_Report.md` §5 records, and re-sorting would
    discard it — the same reasoning §13.2 gives for its own artifact.
    `ensure_ascii=False` keeps corpus text readable as itself rather than as
    escape sequences; the file is UTF-8, as every other artifact this
    repository writes is.
    """
    return json.dumps(trace, ensure_ascii=False) + "\n"


def append(trace: dict, path: pathlib.Path) -> pathlib.Path:
    """Append one record to the JSONL trace file, creating its directory if needed.

    **Append, never rewrite.** Earlier records are evidence of earlier
    executions and are not this execution's to edit.

    One `write` of one complete line, in text-append mode. RO-15 leaves
    concurrency, locking, rotation and retention to this sprint, and the
    simplest repository-native choice is taken: no lock file, no rotation, no
    retention policy and no cross-process coordination. `scripts/run_generation.py`
    performs one execution per invocation, so the concurrent-writer case is not
    one the repository currently produces — recorded as a limitation in
    `docs/M2.18_Execution_Evidence_Report.md` §22 rather than solved
    speculatively.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(serialize(trace))

    return path
