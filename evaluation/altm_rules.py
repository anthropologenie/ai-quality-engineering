"""ALTM rule-identifier mapping — a transcription of `docs/altm.md`, not a rule set.

Sprint P3.3.4 Work Package 3: `docs/altm.md` expresses its diagnostic rules as
prose rows in the §5 Failure Localization Matrix and assigns them no identifiers.
This module assigns a stable identifier to each existing row so a diagnosis can
cite one, and does nothing else.

**No diagnostic rule is created here.** Every `symptom`, `stage`, `component` and
`metric` below is copied verbatim from a §5 row; `docs/altm.md` is not modified,
and a rule that is not in §5 does not appear. If the two ever disagree,
`docs/altm.md` is authoritative and this file is wrong.

Identifier scheme
-----------------
`ALTM-<STAGE>-<n>`, where `<STAGE>` is the row's **first-listed** Likely Stage
and `<n>` numbers the rows within that stage in §5's own top-to-bottom order.
Both halves are properties of the document: nothing here re-sorts §5, so adding a
row to §5 later appends an identifier rather than renumbering existing ones.

Rows naming two stages ("Retrieve or Assemble", "Index or Infer", …) take the
first for the identifier. That is an identifier-assignment convention, not a
diagnostic decision — `stages` retains both, and it is the Diagnosis Engine, not
this table, that decides which is reachable.

Reachability
------------
`docs/altm.md` §3 defines eight lifecycle stages. This repository implements
retrieval only — there is no Assemble, Infer, Post-Process, Evaluate or Final
Answer component (`docs/architecture.md` §5 marks Generation a stub; §9 places
generation in Milestone 2) — so Sprint P3.3.4 restricts diagnosis to the three
reachable stages. `REACHABLE_STAGES` records that restriction; it narrows which
documented rules may be applied and changes none of them.
"""

# docs/altm.md §3 lifecycle order. Used for stage ordering, never for attribution.
LIFECYCLE_STAGES = (
    "Knowledge",
    "Index",
    "Retrieve",
    "Assemble",
    "Infer",
    "Post-Process",
    "Evaluate",
    "Final Answer",
)

# Sprint P3.3.4 Work Package 5. The remaining five stages have no implemented
# component in this repository and SHALL NOT appear in any diagnosis.
REACHABLE_STAGES = ("Knowledge", "Index", "Retrieve")

# docs/altm.md §5 Failure Localization Matrix, in document order. `symptom`,
# `stages`, `component`, `metric` and `investigation` are the row's five cells,
# copied verbatim. `rule_id` is this sprint's addition and the only field that is
# not in the document.
FAILURE_LOCALIZATION_MATRIX = (
    {
        "rule_id": "ALTM-INFER-1",
        "symptom": "Hallucinated fact not in any source document",
        "stages": ("Infer",),
        "component": "Generator",
        "metric": "Faithfulness, Hallucination Rate",
        "investigation": (
            "Check assembled prompt for the claim; if absent, it's fabricated at Infer"
        ),
    },
    {
        "rule_id": "ALTM-KNOWLEDGE-1",
        "symptom": "Answer cites the wrong document version",
        "stages": ("Knowledge",),
        "component": "Knowledge Source",
        "metric": "Freshness check",
        "investigation": "Compare corpus hash/timestamp against JobOps source",
    },
    {
        "rule_id": "ALTM-RETRIEVE-1",
        "symptom": "Right topic, wrong specific document retrieved",
        "stages": ("Retrieve",),
        "component": "Retriever",
        "metric": "Context Precision",
        "investigation": "Inspect ranked candidates for the query",
    },
    {
        "rule_id": "ALTM-RETRIEVE-2",
        "symptom": "Missing answer despite evidence existing in the corpus",
        "stages": ("Retrieve", "Assemble"),
        "component": "Retriever / Context Builder",
        "metric": "Context Recall",
        "investigation": (
            "Check whether evidence was retrieved at all vs. retrieved-but-dropped"
        ),
    },
    {
        "rule_id": "ALTM-INDEX-1",
        "symptom": "Contradictory answer across repeated runs on the same input",
        "stages": ("Index", "Infer"),
        "component": "Indexer / Generator",
        "metric": "Chunk coverage; determinism check",
        "investigation": (
            "Confirm indexing is stable before suspecting generation non-determinism"
        ),
    },
    {
        "rule_id": "ALTM-KNOWLEDGE-2",
        "symptom": "Stale answer despite a recent source update",
        "stages": ("Knowledge",),
        "component": "Knowledge Source",
        "metric": "Freshness check",
        "investigation": "Verify re-indexing was triggered on the source change",
    },
    {
        "rule_id": "ALTM-RETRIEVE-3",
        "symptom": "Low recall on a known-answerable query",
        "stages": ("Retrieve",),
        "component": "Retriever",
        "metric": "Context Recall",
        "investigation": "Check ranking cutoff (top-k) and query formulation",
    },
    {
        "rule_id": "ALTM-RETRIEVE-4",
        "symptom": "Low precision on a known-answerable query",
        "stages": ("Retrieve",),
        "component": "Retriever",
        "metric": "Context Precision",
        "investigation": (
            "Check for near-duplicate or loosely-related chunks crowding results"
        ),
    },
    {
        "rule_id": "ALTM-INFER-2",
        "symptom": "False confidence on an unanswerable question",
        "stages": ("Infer", "Final Answer"),
        "component": "Generator / Evaluation Engine",
        "metric": "Hallucination Rate; abstention check",
        "investigation": (
            'Confirm the "No Answer" failure-taxonomy category (`docs/roadmap.md`, '
            "Section 2.3) is represented in the Golden Dataset"
        ),
    },
    {
        "rule_id": "ALTM-ASSEMBLE-1",
        "symptom": "Correct evidence retrieved, answer still wrong",
        "stages": ("Assemble", "Infer"),
        "component": "Context Builder / Generator",
        "metric": "Prompt assembly tests; Faithfulness",
        "investigation": (
            "Diff the assembled prompt against the retrieved chunk set before "
            "suspecting the model"
        ),
    },
    {
        "rule_id": "ALTM-POST-PROCESS-1",
        "symptom": "Answer correct pre-guardrail, wrong as delivered",
        "stages": ("Post-Process",),
        "component": "Generator (guardrail layer)",
        "metric": "Guardrail/output-contract tests",
        "investigation": "Compare pre- and post-processing output directly",
    },
    {
        "rule_id": "ALTM-EVALUATE-1",
        "symptom": "Regression after a prompt or corpus change, previously passing",
        "stages": ("Evaluate",),
        "component": "Evaluation Engine",
        "metric": "Promptfoo diff",
        "investigation": "Re-run the regression suite against the last known-good baseline",
    },
    {
        "rule_id": "ALTM-FINAL-ANSWER-1",
        "symptom": "Faithful, grounded, but doesn't answer the actual question",
        "stages": ("Final Answer",),
        "component": "Evaluation Engine",
        "metric": "Answer Relevancy",
        "investigation": (
            "Re-check the query against a task-specific rubric, not against "
            "truthfulness metrics"
        ),
    },
)

RULES_BY_ID = {rule["rule_id"]: rule for rule in FAILURE_LOCALIZATION_MATRIX}


def reachable_stage(rule_id: str) -> str:
    """The one reachable ALTM stage a rule attributes to, in `docs/altm.md` §5 order.

    A §5 row naming two stages is resolved by dropping the unreachable ones —
    "Retrieve or Assemble" becomes Retrieve because this repository has no
    Context Builder to fail. That is a consequence of what is implemented, not a
    re-reading of the rule: the row's other stage is not ruled out on evidence,
    it is ruled out because the component does not exist.

    Raises if a rule attributes to no reachable stage, so an unreachable rule can
    never silently acquire a stage it does not name (Work Package 5).
    """
    reachable = [stage for stage in RULES_BY_ID[rule_id]["stages"] if stage in REACHABLE_STAGES]
    if len(reachable) != 1:
        raise KeyError(
            f"Rule {rule_id!r} attributes to {len(reachable)} reachable stages "
            f"({reachable}); exactly one is required."
        )
    return reachable[0]
