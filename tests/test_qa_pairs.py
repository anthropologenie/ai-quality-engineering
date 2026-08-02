"""Specification Family 7 — QA Dataset Authority.

Sprint P3.4.1 (`docs/MILESTONE_1A.md` build item 9): promotes the QA pairs
validation the repository has so far performed at build time and by hand into
permanent committed specifications.

`datasets/golden/resume_qa_pairs.json` is the repository's **question
authority**. Every question the retrieval runtime executes, every expectation
the Evidence Trace Dataset carries, and every metric computed downstream exists
because a QA pair exists — `scripts/build_evidence_trace.py` `main()` iterates
`qa_pairs[]` and derives exactly one Evidence Trace entry per pair, in the QA
Dataset's own order. Until now that artifact was validated only as a side effect
of running that builder, which is not run in CI.

Structure here, resolution in the cross-dataset suite
------------------------------------------------------
A QA pair's references are validated in two places, deliberately split so
neither restates the other:

    here                       the reference is well-formed — present, a string,
                               distinct, and not self-referential
    cross-dataset integrity    the reference *resolves* to a committed fact

QA-9 below can therefore fail on a malformed `supporting_fact_ids` entry without
the Golden Dataset being read at all, which is what makes a failure here
diagnosable: it localises the defect to this artifact.

Value domains come from repository authority, not from the data
----------------------------------------------------------------
`question_category` and `failure_category` are asserted against the domains
`docs/roadmap.md` §2.2 and §2.3 state — the four question forms and the
seven-category failure taxonomy — not against the set of values the committed
file happens to contain. Reading the domain off the artifact would make the
specification agree with any dataset by construction, including one that
introduced a category no authority defines.

What is deliberately *not* specified
-------------------------------------
`fact_relation` carries values (`supports`, `refutes`, `bounds`) that no
repository authority defines a domain for — `docs/roadmap.md`, `datasets/SCHEMA.md`
and `docs/MILESTONE_1A.md` are all silent on the field. Its presence, type and
non-emptiness are specified below; its value domain is not, because freezing the
three values in use today would be this suite inventing an invariant rather than
promoting one, which the Sprint P3.4.1 Existing Validation Policy forbids.

Likewise, `answerable` is specified as a boolean and tied to the one category
`docs/roadmap.md` §2.3 defines in terms of answerability — *"**No Answer** |
Tests abstention"* — and no further. That `False Premise` pairs are also marked
unanswerable is a dataset authoring choice, not a stated rule, and asserting the
biconditional would freeze it as one.

Record schema — frozen here for the first time
-----------------------------------------------
`datasets/SCHEMA.md` §8 fixes the container (`schema_version` + `qa_pairs[]`) and
leaves the per-record schema to *"the first implementation of each artifact
type."* That implementation shipped in Sprint 1A.1 P4 without an executable
specification. QA-2 is it.

Observational only. Nothing here regenerates the QA Dataset, runs a builder, or
repairs a record; the artifact is verified exactly as stored, per the Sprint
P3.4.1 Repository Dependency Rule. QA-n labels are this file's own organizing
labels, not proposed repository terminology.
"""

import json

from scripts.build_evidence_trace import NO_ANSWER_CATEGORY, QA_PAIRS_PATH, load_json

from tests.test_golden_dataset import CANONICAL_SOURCES, SCHEMA_VERSION, duplicates

# `docs/roadmap.md` §2.2 — *"four question categories from a single fact —
# lexical, semantic, summarization, and reasoning"*; the same four
# `docs/MILESTONE_1A.md` build item 7 names.
QUESTION_CATEGORIES = frozenset({"lexical", "semantic", "summarization", "reasoning"})

# `docs/roadmap.md` §2.3, in that table's own row order — the failure taxonomy
# `docs/MILESTONE_1A.md` build item 8 requires the dataset to include in full.
FAILURE_CATEGORIES = frozenset(
    {
        "Exact Fact",
        "Paraphrase",
        "Multi-hop",
        "No Answer",
        "Stale Version",
        "Contradiction",
        "False Premise",
    }
)

# The record schema `datasets/SCHEMA.md` §8 deferred to first implementation,
# frozen here with the type each field carries.
CANONICAL_QA_FIELDS = {
    "id": str,
    "source": str,
    "fact_id": str,
    "supporting_fact_ids": list,
    "fact_relation": str,
    "question": str,
    "question_category": str,
    "failure_category": str,
    "expected_answer": str,
    "answerable": bool,
}

STRING_FIELDS = tuple(
    field for field, expected in CANONICAL_QA_FIELDS.items() if expected is str
)


# --- QA-1 … QA-2: container and record schema -------------------------------


def test_qa1_container_matches_the_schema_contract(real_qa_pairs_collection):
    """QA-1 — the container is `datasets/SCHEMA.md` §8's QA container, at §2's version.

    `{"schema_version": "1.0", "qa_pairs": []}`, and nothing else at the top
    level. `schema_version` is asserted, not merely read: §2 requires a
    structural change to bump it, so an unchanged version over a changed shape is
    the drift this refuses.
    """
    assert set(real_qa_pairs_collection) == {"schema_version", "qa_pairs"}
    assert real_qa_pairs_collection["schema_version"] == SCHEMA_VERSION
    assert isinstance(real_qa_pairs_collection["qa_pairs"], list)


def test_qa2_every_pair_carries_exactly_the_canonical_fields(real_qa_pairs):
    """QA-2 — every record carries the ten canonical fields at their declared types.

    Both directions — nothing missing, nothing added — so a record that grew an
    eleventh field fails here rather than introducing an unratified schema
    silently.

    `answerable` is checked with `type(...) is bool` rather than `isinstance`:
    `bool` is a subclass of `int`, so `isinstance(1, bool)` is False but a stray
    `1` would pass an `int` check, and the repository treats this field as a
    two-valued flag.
    """
    assert real_qa_pairs, "the committed QA Dataset must contain at least one pair"

    for pair in real_qa_pairs:
        assert set(pair) == set(CANONICAL_QA_FIELDS), (
            f"QA pair {pair.get('id')!r} fields {sorted(pair)} != "
            f"{sorted(CANONICAL_QA_FIELDS)}"
        )

        for field, expected_type in CANONICAL_QA_FIELDS.items():
            assert type(pair[field]) is expected_type, (
                f"QA pair {pair['id']!r} field {field!r} must be "
                f"{expected_type.__name__}, got {type(pair[field]).__name__}"
            )


def test_qa2_no_string_field_is_empty_or_whitespace(real_qa_pairs):
    """QA-2 — no required string field is present-but-empty.

    An empty `question` would still be executed by the retrieval runtime, which
    reads `question` from the Evidence Trace entry derived from this pair and
    issues it verbatim; an empty `expected_answer` would be scored against.
    Neither fails any type check.
    """
    for pair in real_qa_pairs:
        for field in STRING_FIELDS:
            assert pair[field].strip(), (
                f"QA pair {pair['id']!r} field {field!r} is empty or whitespace only"
            )


# --- QA-3 … QA-5: identity ---------------------------------------------------


def test_qa3_question_identifiers_are_pairwise_distinct(real_qa_pairs):
    """QA-3 — no two QA pairs share an `id`.

    Load-bearing beyond the dataset itself: the Evidence Trace entry id is
    `meta_<qa_id>` (`scripts/build_evidence_trace.py` `build_evidence_trace_entry`),
    and `validate_evidence_trace` rejects a duplicate Evidence Trace id. Two QA
    pairs sharing an id would therefore surface as an Evidence Trace build
    failure with no indication that the QA Dataset is where the defect lives.
    """
    assert duplicates([pair["id"] for pair in real_qa_pairs]) == []


def test_qa4_question_identifiers_are_derived_from_their_parent_fact(real_qa_pairs):
    """QA-4 — each `id` is `qa_<fact_id>_<question_category>_<serial>`.

    `datasets/SCHEMA.md` §6 derives every question id from exactly one canonical
    fact id, so that *"provenance [is] recoverable from the ID alone without a
    lookup."* The committed dataset extends §6's example with a trailing serial,
    which is what lets one fact and one category yield more than one question —
    the *"one verified fact → many question forms"* principle of
    `docs/roadmap.md` §2.2.

    Checked against the record's own `fact_id` and `question_category`, never
    against a literal, so the specification holds for any fact and any category.
    Whether that `fact_id` *resolves* is `tests/test_cross_dataset_integrity.py`'s
    claim, not this one.
    """
    for pair in real_qa_pairs:
        prefix = f"qa_{pair['fact_id']}_{pair['question_category']}_"

        assert pair["id"].startswith(prefix), (
            f"QA pair id {pair['id']!r} is not derived from its parent fact and "
            f"category (expected prefix {prefix!r})"
        )
        assert pair["id"][len(prefix):].isdigit(), (
            f"QA pair id {pair['id']!r} does not end in a numeric serial"
        )


def test_qa5_every_pair_declares_a_canonical_source_matching_its_fact(real_qa_pairs):
    """QA-5 — `source` is canonical and is the prefix its `fact_id` carries.

    Two independent statements of the same provenance — the pair's `source`
    field, and the source prefix embedded in the fact id it cites — held in
    agreement. Since `datasets/SCHEMA.md` §6's prefix scheme exists to prevent
    collisions *across* sources, a pair labelled `resume` citing a `jobops` fact
    would defeat the scheme while remaining structurally valid.
    """
    for pair in real_qa_pairs:
        assert pair["source"] in CANONICAL_SOURCES, (
            f"QA pair {pair['id']!r} declares non-canonical source {pair['source']!r}"
        )
        assert pair["fact_id"].startswith(f"{pair['source']}_f"), (
            f"QA pair {pair['id']!r} declares source {pair['source']!r} but cites "
            f"fact {pair['fact_id']!r}"
        )


# --- QA-6 … QA-8: value domains and answer integrity -------------------------


def test_qa6_every_question_category_is_one_of_the_four_question_forms(real_qa_pairs):
    """QA-6 — `question_category` is one of `docs/roadmap.md` §2.2's four forms."""
    for pair in real_qa_pairs:
        assert pair["question_category"] in QUESTION_CATEGORIES, (
            f"QA pair {pair['id']!r} category {pair['question_category']!r} is outside "
            f"the four question forms"
        )


def test_qa7_every_failure_category_is_in_the_failure_taxonomy(real_qa_pairs):
    """QA-7 — `failure_category` is one of `docs/roadmap.md` §2.3's seven categories.

    The taxonomy is not decorative: `scripts/build_evidence_trace.py`
    `derive_expected_outcome` reads this field and maps `No Answer` to `Abstain`
    and everything else to `Answer`. A category outside the taxonomy would be
    mapped to `Answer` silently, converting an untestable label into a positive
    expectation.
    """
    for pair in real_qa_pairs:
        assert pair["failure_category"] in FAILURE_CATEGORIES, (
            f"QA pair {pair['id']!r} failure category {pair['failure_category']!r} is "
            f"outside the failure taxonomy"
        )


def test_qa8_questions_are_pairwise_distinct(real_qa_pairs):
    """QA-8 — no two QA pairs ask the same question.

    Answer integrity's precondition. Two identical questions carrying different
    `expected_answer` values are a contradiction in the ground truth itself, and
    the retrieval runtime — which is deterministic and stateless per query —
    would necessarily retrieve identically for both, so at least one would be
    scored wrong for reasons no diagnosis could attribute to retrieval.
    """
    assert duplicates([pair["question"] for pair in real_qa_pairs]) == []


def test_qa8_every_no_answer_question_is_marked_unanswerable(real_qa_pairs):
    """QA-8 — `failure_category == "No Answer"` implies `answerable is False`.

    The one answerability relationship a repository authority states:
    `docs/roadmap.md` §2.3 defines **No Answer** as the category that *"tests
    abstention"*, and `scripts/build_evidence_trace.py` treats it as the sole
    category yielding an `Abstain` outcome. A No Answer pair marked answerable
    would produce an Abstain expectation for a question the dataset itself claims
    the corpus can answer.

    The category constant is imported from the builder rather than restated, so
    the two cannot drift apart. The converse is deliberately not asserted — see
    the module docstring.
    """
    mislabelled = [
        pair["id"]
        for pair in real_qa_pairs
        if pair["failure_category"] == NO_ANSWER_CATEGORY and pair["answerable"]
    ]

    assert mislabelled == [], f"No Answer pairs marked answerable: {mislabelled}"


# --- QA-9: referenced fact identifiers ---------------------------------------


def test_qa9_supporting_fact_identifiers_are_well_formed(real_qa_pairs):
    """QA-9 — `supporting_fact_ids` holds distinct fact-id strings.

    Structure only; resolution is the cross-dataset suite's claim. A repeated id
    would be counted twice by `derive_expected_reasoning_type`, which reads
    `len(supporting_fact_ids)` — so a single supporting fact listed twice would
    classify a single-hop question as Multi-hop, an expectation error no
    downstream layer could detect.
    """
    for pair in real_qa_pairs:
        supporting = pair["supporting_fact_ids"]

        for fact_id in supporting:
            assert isinstance(fact_id, str) and fact_id.strip(), (
                f"QA pair {pair['id']!r} carries a malformed supporting fact id "
                f"{fact_id!r}"
            )

        assert duplicates(supporting) == [], (
            f"QA pair {pair['id']!r} repeats supporting fact ids "
            f"{duplicates(supporting)}"
        )


def test_qa9_no_pair_lists_its_parent_fact_as_its_own_support(real_qa_pairs):
    """QA-9 — `fact_id` never appears in `supporting_fact_ids`.

    `build_evidence_trace_entry` builds its evidence set as
    `[fact_id, *supporting_fact_ids]`. A self-listing pair would contribute the
    parent fact twice, inflating the count `derive_expected_reasoning_type`
    reads while adding no evidence — the same distortion QA-9's duplicate check
    prevents within the supporting list, arriving by a different route.
    """
    self_referential = [
        pair["id"] for pair in real_qa_pairs if pair["fact_id"] in pair["supporting_fact_ids"]
    ]

    assert self_referential == [], (
        f"QA pairs listing their own parent fact as support: {self_referential}"
    )


# --- QA-10: deterministic ordering -------------------------------------------


def test_qa10_the_dataset_reads_identically_on_every_load(real_qa_pairs_collection):
    """QA-10 — repeated reads yield equal collections, in equal order.

    Ordering is load-bearing here in a way it is not for the Golden Dataset:
    `scripts/build_evidence_trace.py` `main()` preserves QA order and never
    re-sorts, *"so the QA Dataset remains the single authority over which
    questions exist and in what sequence."* Equality of the parsed lists is
    order-sensitive, so this specifies sequence as well as content.
    """
    reread = load_json(QA_PAIRS_PATH)

    assert reread == real_qa_pairs_collection
    assert [pair["id"] for pair in reread["qa_pairs"]] == [
        pair["id"] for pair in real_qa_pairs_collection["qa_pairs"]
    ]


def test_qa10_the_committed_artifact_is_in_canonical_serialized_form(real_qa_pairs_collection):
    """QA-10 — the artifact is byte-identical to its canonical serialization.

    2-space indentation, insertion-order keys, one trailing newline — the
    repository's serialization convention — with `ensure_ascii=False`, the
    documented difference the hand-authored Golden Dataset artifacts carry (see
    `tests/test_golden_dataset.py` GD-13; this file contains literal em dashes).

    Freezes representation, not content, and catches the reordering-in-place
    that every content-level check above would pass.
    """
    serialized = json.dumps(real_qa_pairs_collection, indent=2, ensure_ascii=False) + "\n"

    assert serialized == QA_PAIRS_PATH.read_text(encoding="utf-8")
