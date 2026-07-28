"""Specification Family 2 — Construction Behaviour.

Encodes the approved `KnowledgeSource` construction behaviour validated in
*Sprint P3.1.5 Construction Validation Evidence* (§3–§7): deterministic
identity (B3, B4), deterministic normalization (B5–B8), deterministic ordering
(B9, B10), behavioural repeatability (B2, and the cross-process evidence for
contract invariant 3), and corpus/Manifest disagreement behaviour (Case A;
Case B is a failure and is specified in tests/test_knowledge_source_failures.py).

What these specifications protect is observable behaviour only. Determinism is
encoded as *"repeated construction yields equal `Document` values"* — never as
a literal digest of `Document.text`. A digest describes one corpus snapshot
under one extraction mechanism; `docs/DOCUMENT_CONTRACT.md` §8.8 and
`docs/DOCUMENT_CONSTRUCTION_PLAN.md` §11.3 both record that invariant 3 is
mechanism-relative, so freezing a digest would specify something the contract
does not guarantee and would break on a legitimate mechanism change.

Deferred findings F-1 and F-2 are excluded from this suite; see the permanent
record in tests/conftest.py.
"""

import json
import os
import subprocess
import sys

import pytest

from sample_rag.knowledge_source import (
    KnowledgeSource,
    extract_text,
    normalize_text,
    resolve_source_path,
)

REPEAT_RUNS = 10
PURITY_INVOCATIONS = 100

# The seeds Sprint P3.1.5 used for its cross-process determinism measurement.
# Per-process hash randomization changes set and dict iteration order, and
# `SUPPORTED_EXTENSIONS` is a set — so this is a real source of drift that a
# same-process loop structurally cannot detect.
HASH_SEEDS = ("0", "1", "42", "12345", "random")


# --- B3, B4: deterministic identity ----------------------------------------


def test_b3_document_id_matches_the_manifest_id_on_every_run(real_manifest_entries):
    """B3 — `Document.id` equals `documents[].id` on every repeated run.

    Identity is read from the Manifest, so it must not drift between runs; a
    single run could not distinguish a stable read from a coincidentally equal
    derivation.
    """
    expected = [entry["id"] for entry in real_manifest_entries]
    for _ in range(REPEAT_RUNS):
        assert [d.id for d in KnowledgeSource().load()] == expected


def test_b4_manifest_identity_is_passed_through_byte_identically(synthetic_corpus):
    """B4 — identity is reused verbatim: no regeneration, rewriting, casing, or trimming.

    A manifest id carrying mixed case and surrounding whitespace is the case
    that separates "read" from "derived": any regeneration, normalization, or
    trimming step would visibly alter it.
    """
    unusual_id = "  MiXeD Case ID\t"
    synthetic_corpus.text_file("documents/b4.txt", "body text")
    synthetic_corpus.entries((unusual_id, "documents/b4.txt"))

    (document,) = synthetic_corpus.load()

    assert document.id == unusual_id
    assert document.id.encode("utf-8") == unusual_id.encode("utf-8")


# --- B5–B8: deterministic normalization ------------------------------------


def test_b5_normalization_is_idempotent_on_constructed_text(real_documents):
    """B5 — re-normalizing an already-normalized value changes nothing."""
    for document in real_documents:
        assert normalize_text(document.text) == document.text


def test_b6_normalization_is_pure_across_repeated_invocation():
    """B6 — `normalize_text` is a total function of its input alone.

    100 invocations over the real corpus's extracted text must yield exactly
    one distinct result: no clock, locale, environment, randomness, or
    filesystem state may participate (`docs/DOCUMENT_CONSTRUCTION_PLAN.md`
    §11.1).
    """
    raw = extract_text(resolve_source_path("documents/resume/Karthik_SR_Resume_v2_2.docx"))
    results = {normalize_text(raw) for _ in range(PURITY_INVOCATIONS)}
    assert len(results) == 1


def test_b7_constructed_text_satisfies_every_normalization_rule(real_documents):
    """B7 — real corpus output satisfies N2–N5 simultaneously.

    Per-rule behaviour is specified in isolation by B8; this specification is
    the different claim that the rules compose without one undoing another on
    real corpus content.
    """
    for document in real_documents:
        assert "\r" not in document.text, "N2 — no carriage returns survive"
        assert not any(
            line != line.rstrip(" \t") for line in document.text.split("\n")
        ), "N3 — no line ends in spaces or tabs"
        assert "\n\n\n" not in document.text, "N4 — no run of three or more newlines"
        assert document.text == document.text.strip(), "N5 — document is trimmed"


@pytest.mark.parametrize(
    ("rule", "raw", "expected"),
    [
        pytest.param("N2", "alpha\r\nbeta", "alpha\nbeta", id="N2-crlf-becomes-lf"),
        pytest.param("N2", "alpha\rbeta", "alpha\nbeta", id="N2-lone-cr-becomes-lf"),
        pytest.param("N3", "alpha   \nbeta\t\t\ngamma", "alpha\nbeta\ngamma", id="N3-trailing"),
        pytest.param("N4", "alpha\n\n\n\n\nbeta", "alpha\n\nbeta", id="N4-collapse"),
        pytest.param("N5", "\n\n  alpha  \n\n", "alpha", id="N5-trim"),
        pytest.param("N5", "   \t\n  \n\t ", "", id="N5-whitespace-only-becomes-empty"),
    ],
)
def test_b8_each_normalization_rule_behaves_in_isolation(rule, raw, expected):
    """B8 — each normalization rule N2–N5 is measured on its own.

    Isolating the rules is what distinguishes "the pipeline happens to produce
    clean text" from "each documented rule is actually implemented".
    """
    assert normalize_text(raw) == expected, f"normalization rule {rule}"


# --- B9, B10: deterministic ordering ---------------------------------------


def _unsorted_manifest(corpus):
    """A three-entry manifest in deliberately unsorted id order."""
    for name in ("b", "a", "c"):
        corpus.text_file(f"documents/{name}.txt", f"content {name}")
    corpus.entries(
        ("id-b", "documents/b.txt"),
        ("id-a", "documents/a.txt"),
        ("id-c", "documents/c.txt"),
    )
    return ["id-b", "id-a", "id-c"]


def test_b9_manifest_order_is_preserved_and_never_re_sorted(synthetic_corpus):
    """B9 — `load()` returns entries in the Manifest's own order.

    The fixture is deliberately unsorted: against a sorted manifest, "preserves
    manifest order" and "sorts independently" are indistinguishable
    (`docs/DOCUMENT_CONSTRUCTION_PLAN.md` §11.2).
    """
    expected = _unsorted_manifest(synthetic_corpus)
    assert [d.id for d in synthetic_corpus.load()] == expected


def test_b10_ordering_is_stable_across_repeated_runs(synthetic_corpus):
    """B10 — repeated execution over one manifest yields one ordering."""
    expected = _unsorted_manifest(synthetic_corpus)
    for _ in range(REPEAT_RUNS):
        assert [d.id for d in synthetic_corpus.load()] == expected


# --- B2 and invariant 3: behavioural repeatability -------------------------


def test_b2_repeated_construction_produces_identical_documents(real_documents):
    """B2 — contract invariant 3: repeated construction yields equal values.

    Equality of `Document` values is the contract's own statement of
    determinism (§8.7 invariant 3, checkable only by two-run comparison per
    §8.8). No digest is asserted.
    """
    for _ in range(REPEAT_RUNS):
        assert KnowledgeSource().load() == real_documents


def test_invariant_3_determinism_holds_across_independent_processes(repository_root):
    """Invariant 3 — construction is independent of per-process hash randomization.

    Sprint P3.1.5's cross-process measurement, encoded. Each run is a fresh
    interpreter under a different `PYTHONHASHSEED`; the compared payload is the
    `Document` values themselves, serialized as ASCII-escaped JSON so the
    comparison cannot be perturbed by the harness's own encoding choice — the
    artefact that sprint traced and disclosed.
    """
    program = (
        "import json, sys;"
        "sys.path.insert(0, sys.argv[1]);"
        "from sample_rag.knowledge_source import KnowledgeSource;"
        "sys.stdout.write(json.dumps([[d.id, d.text] for d in KnowledgeSource().load()]))"
    )

    outputs = []
    for seed in HASH_SEEDS:
        result = subprocess.run(
            [sys.executable, "-c", program, str(repository_root)],
            env={**os.environ, "PYTHONHASHSEED": seed},
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        assert result.returncode == 0, f"PYTHONHASHSEED={seed} failed: {result.stderr}"
        outputs.append(json.loads(result.stdout))

    assert all(output == outputs[0] for output in outputs)


# --- Corpus/Manifest disagreement, Case A ----------------------------------


def test_case_a_corpus_file_absent_from_the_manifest_is_silently_excluded(synthetic_corpus):
    """Case A — a file on disk with no Manifest entry is excluded, without raising.

    The Manifest — not the filesystem — is the corpus enumeration (identity
    strategy S1, `docs/DOCUMENT_CONSTRUCTION_PLAN.md` §9.1), so an unmanifested
    file never enters the pipeline. Detecting the disagreement would require
    the corpus/Manifest diff that the Construction Plan defers to Data Quality
    Validation, so raising here would be the wrong behaviour, not the safer one.
    """
    for name in ("one", "two", "three"):
        synthetic_corpus.text_file(f"documents/{name}.txt", f"content {name}")
    synthetic_corpus.text_file("documents/unmanifested.txt", "ghost content")
    synthetic_corpus.entries(
        ("id-one", "documents/one.txt"),
        ("id-two", "documents/two.txt"),
        ("id-three", "documents/three.txt"),
    )

    documents = synthetic_corpus.load()

    assert len(list(synthetic_corpus.root.glob("documents/*.txt"))) == 4
    assert len(documents) == 3
    assert all("ghost" not in d.text for d in documents)
