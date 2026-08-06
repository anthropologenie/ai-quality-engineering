"""Shared fixtures and utilities for the Knowledge Layer Executable Specification Suite.

Sprint P3.1.6: converts the approved *Sprint P3.1.5 Construction Validation
Evidence* (`docs/P3.1.5_Construction_Validation_Evidence_Report.md`) from a
one-off measurement into permanently executable specifications.

The suite spans three specification files, each encoding one evidence family:

    tests/test_document_contract.py           Runtime Contract      (A1–A16)
    tests/test_knowledge_source_construction.py  Construction Behaviour (B2–B10)
    tests/test_knowledge_source_failures.py   Construction Failure Surface

Every specification traces back to exactly one validated engineering claim from
that evidence. No specification here creates new engineering evidence, and none
asserts a repository behaviour the P3.1.5 evidence did not already validate.

Behavioural determinism, not implementation artefacts
-----------------------------------------------------
These specifications protect *observable* behaviour: the `Document` values
`KnowledgeSource.load()` produces, the order it produces them in, and the
failure surface it raises through. They deliberately do **not** freeze
implementation artefacts — no specification asserts a literal SHA-256 digest of
`Document.text`, because a digest is a fact about one corpus snapshot and one
extraction mechanism, not a contractual property (`docs/DOCUMENT_CONTRACT.md`
§8.8; `docs/DOCUMENT_CONSTRUCTION_PLAN.md` §11.3). Determinism is instead
encoded the way the contract defines it: repeated construction yields equal
values.

Architectural findings F-1 and F-2 — current status
---------------------------------------------------
Both were identified during Sprint P3.1.5 Construction Validation and
independently reproduced at Sprint P3.1.7.1 (Evidence Verification), which
confirmed each as CONFIRMED against repository evidence. Their dispositions now
differ, and the canonical record is
`docs/ENGINEERING_TRACEABILITY_REGISTER.md`.

    F-1 — Duplicate `knowledge_manifest.json` `documents[].id` values are
          accepted silently; `load()` returns two `Document`s sharing one id.
          `docs/DOCUMENT_CONTRACT.md` §8.3 states id "is unique across the
          corpus", but uniqueness is not one of §8.7's three invariants and
          §8.5 routes collection-level and cross-artifact checks to the Data
          Quality Validation layer.
          RESOLVED at Sprint P3.1.8.0B by Contract Erratum E-1
          (docs/DOCUMENT_CONTRACT.md §8.9), which records the uniqueness
          guarantee as binding and corpus-scoped and names Data Quality
          Validation as its enforcement owner. Uniqueness is therefore
          approved repository behaviour, and is specified by the DQ-2
          specifications in tests/test_data_quality.py. F-1 closed at
          Sprint P3.1.8.4 — see the register §3.1.

    F-2 — A manifest `documents[].source` escaping the corpus root (a `..`
          relative escape, or an absolute path) resolved and loaded a file
          from outside `sample_rag/`.
          RESOLVED at Sprint P3.1.7.2 by ADR-P3.1.7.2-F2 (accepted Option A —
          Construction). `resolve_source_path` now rejects an escaping source
          as an Input failure, and the behaviour is specified in
          tests/test_knowledge_source_failures.py. F-2 is therefore approved
          repository behaviour and *is* covered by this suite.

The suite excludes only F-1. No intentionally failing specification exists for
it, and it is not redefined as approved behaviour here.

Sprint P3.4.1 — committed dataset authorities
----------------------------------------------
Dataset Authority Validation (`tests/test_golden_dataset.py`,
`tests/test_qa_pairs.py`, `tests/test_evidence_trace_dataset.py`,
`tests/test_cross_dataset_integrity.py`) needs the same committed artifact in
several files at once, so its readers are defined here **once** rather than
once per file: `docs/ENGINEERING_TRACEABILITY_REGISTER.md` §5 rates duplicated
validation logic a **High** drift risk, and four independently written loaders
of the same authority could disagree about what the repository contains.

Every one of those fixtures reads a *committed* artifact through the
repository's own existing reader — `scripts/build_evidence_trace.py`'s
`load_json` / `load_evidence_trace`, and `scripts/build_chunks.py`'s
`validate_chunks(load_chunks())` chained gate. None regenerates a dataset, runs
a builder, or writes anything, per the Sprint P3.4.1 Repository Dependency
Rule. The `real_` prefix follows `real_manifest_entries` and `real_documents`
above and means the same thing: repository state exactly as stored.
"""

import json
import zipfile
from pathlib import Path

import pytest

from scripts.build_chunks import load_chunks, validate_chunks
from scripts.build_evidence_trace import (
    FACTS_PATH,
    QA_PAIRS_PATH,
    load_evidence_trace,
    load_json,
)

from sample_rag import knowledge_source
from sample_rag.knowledge_source import KnowledgeSource

# Captured at import time, before any specification monkeypatches the module
# constants, so real-corpus specifications always address the real corpus.
REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
REAL_SAMPLE_RAG_ROOT = knowledge_source.SAMPLE_RAG_ROOT
REAL_KNOWLEDGE_MANIFEST_PATH = knowledge_source.KNOWLEDGE_MANIFEST_PATH

WORDPROCESSINGML_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

MINIMAL_CONTENT_TYPES = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="xml" ContentType="application/xml"/>'
    "</Types>"
)


def docx_document_xml(paragraphs):
    """Build a minimal, well-formed `word/document.xml` carrying `paragraphs`.

    One `w:p` per paragraph, each with a single `w:t` run — the shape
    `extract_docx_paragraphs` reads. Deliberately minimal: these specifications
    exercise construction behaviour, not .docx fidelity beyond `w:t`, which
    Sprint P3.1.5 recorded as deferred.
    """
    body = "".join(f"<w:p><w:r><w:t>{text}</w:t></w:r></w:p>" for text in paragraphs)
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<w:document xmlns:w="{WORDPROCESSINGML_NS}"><w:body>{body}</w:body></w:document>'
    )


class SyntheticCorpus:
    """A throwaway corpus root plus Knowledge Manifest, wired into the module.

    Construction reads its two inputs through module-level constants —
    `SAMPLE_RAG_ROOT` and `KNOWLEDGE_MANIFEST_PATH`. Redirecting both at a
    `tmp_path` reproduces the in-process monkeypatching Sprint P3.1.5 used for
    its synthetic cases, so a specification can present construction with a
    corpus the repository does not (and must not) contain. `monkeypatch`
    restores both constants at teardown; nothing under `sample_rag/` is
    touched.
    """

    def __init__(self, root, monkeypatch):
        self.root = root
        self.manifest_path = root / "knowledge_manifest.json"
        monkeypatch.setattr(knowledge_source, "SAMPLE_RAG_ROOT", root)
        monkeypatch.setattr(knowledge_source, "KNOWLEDGE_MANIFEST_PATH", self.manifest_path)

    def manifest(self, obj):
        """Persist `obj` as the Knowledge Manifest."""
        self.manifest_path.write_text(json.dumps(obj), encoding="utf-8")

    def raw_manifest(self, raw):
        """Persist `raw` verbatim as the Knowledge Manifest — valid JSON or not."""
        self.manifest_path.write_text(raw, encoding="utf-8")

    def entries(self, *pairs):
        """Persist a manifest whose `documents[]` is `(id, source)` in given order."""
        self.manifest({"documents": [{"id": i, "source": s} for i, s in pairs]})

    def _path(self, relative_source):
        path = self.root / relative_source
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def text_file(self, relative_source, content):
        path = self._path(relative_source)
        path.write_text(content, encoding="utf-8", newline="")
        return path

    def binary_file(self, relative_source, data):
        path = self._path(relative_source)
        path.write_bytes(data)
        return path

    def directory(self, relative_source):
        path = self._path(relative_source)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def docx(self, relative_source, paragraphs):
        return self.docx_package(
            relative_source, {"word/document.xml": docx_document_xml(paragraphs)}
        )

    def docx_package(self, relative_source, members):
        """Write a .docx as a ZIP containing exactly `members` (name -> text)."""
        path = self._path(relative_source)
        with zipfile.ZipFile(path, "w") as package:
            package.writestr("[Content_Types].xml", MINIMAL_CONTENT_TYPES)
            for name, content in members.items():
                package.writestr(name, content)
        return path

    def load(self):
        return KnowledgeSource().load()


@pytest.fixture
def synthetic_corpus(tmp_path, monkeypatch):
    """A `SyntheticCorpus` rooted at `tmp_path`, active for one specification."""
    return SyntheticCorpus(tmp_path, monkeypatch)


@pytest.fixture
def repository_root():
    """The repository root, for specifications that re-enter it in a subprocess."""
    return REPOSITORY_ROOT


@pytest.fixture
def real_manifest_entries():
    """The committed Knowledge Manifest's `documents[]`, read independently.

    Read here with `json` directly rather than through
    `discover_manifest_entries`, so a specification comparing `Document.id`
    against the manifest is comparing against the artifact, not against the
    same code path that produced the value.
    """
    return json.loads(REAL_KNOWLEDGE_MANIFEST_PATH.read_text(encoding="utf-8"))["documents"]


@pytest.fixture
def real_documents():
    """`KnowledgeSource().load()` over the committed repository corpus."""
    return KnowledgeSource().load()


# --- Sprint P3.4.1: the committed dataset authorities -----------------------


@pytest.fixture
def real_documents_by_id(real_documents):
    """The committed corpus keyed by `Document.id`, the repository's document identity.

    `docs/DOCUMENT_CONTRACT.md` §8.4 makes `id` the join key that
    `knowledge_manifest.json` `documents[].id`, `chunk.document_id` and the
    Golden Dataset's `document_id` already share, so every dataset specification
    that needs a document's text addresses it the same way.
    """
    return {document.id: document for document in real_documents}


@pytest.fixture
def real_facts_collection():
    """The committed Golden Dataset container, read but not validated.

    Read with `scripts/build_evidence_trace.py`'s `load_json` — the reader the
    Evidence Trace builder itself uses for this artifact — so specifications
    observe the dataset through the repository's own code path. `load_json`
    performs no structural validation and no repair; the container's shape is
    what `tests/test_golden_dataset.py` specifies, not something a fixture may
    presuppose.
    """
    return load_json(FACTS_PATH)


@pytest.fixture
def real_facts(real_facts_collection):
    """The committed Golden Dataset's `facts[]`, in stored order."""
    return real_facts_collection["facts"]


@pytest.fixture
def real_facts_by_id(real_facts):
    """The committed facts keyed by `id`.

    Keyed exactly as `scripts/build_evidence_trace.py` `main()` keys them, so
    cross-dataset resolution here uses the same index the builder resolves
    through. Uniqueness of those keys is not assumed by this fixture — it is
    specified independently by `tests/test_golden_dataset.py`.
    """
    return {fact["id"]: fact for fact in real_facts}


@pytest.fixture
def real_qa_pairs_collection():
    """The committed QA Dataset container, read but not validated."""
    return load_json(QA_PAIRS_PATH)


@pytest.fixture
def real_qa_pairs(real_qa_pairs_collection):
    """The committed QA Dataset's `qa_pairs[]`, in stored order.

    Stored order is load-bearing: `scripts/build_evidence_trace.py` `main()`
    preserves it and never re-sorts, so it is the order the Evidence Trace
    Dataset inherits.
    """
    return real_qa_pairs_collection["qa_pairs"]


@pytest.fixture
def real_evidence_trace_collection():
    """The committed Evidence Trace Dataset container, read but not validated.

    Deliberately *not* passed through `validate_evidence_trace` here. That gate
    is the subject of `tests/test_evidence_trace_dataset.py`'s specifications; a
    fixture that ran it would make those specifications assert a property their
    own fixture had already guaranteed.
    """
    return load_evidence_trace()


@pytest.fixture
def real_evidence_trace(real_evidence_trace_collection):
    """The committed Evidence Trace Dataset's `evidence_trace[]`, in stored order."""
    return real_evidence_trace_collection["evidence_trace"]


@pytest.fixture
def real_chunks():
    """The committed Chunk Corpus, loaded through its own validation gate.

    `validate_chunks(load_chunks())` is the chained call
    `docs/CHUNK_VALIDATION_PLAN.md` §P7.1 prescribes and `scripts/run_retrieval.py`
    already uses. The Chunk Corpus is **out of scope** for Sprint P3.4.1 and no
    specification in the dataset suites validates it; it is read here only as
    the universe against which Evidence Trace chunk references must resolve.
    """
    return validate_chunks(load_chunks())["chunks"]


@pytest.fixture
def real_chunk_collection():
    """The committed Chunk collection exactly as stored — **not** validated.

    Deliberately distinct from `real_chunks` above, which chains
    `validate_chunks(load_chunks())`. Sprint 1B.1's DQ-5 gate specification
    asserts that the committed artifact *passes* that gate; a fixture that had
    already run it would make the specification assert a property its own
    fixture guaranteed. The same reasoning `real_evidence_trace_collection`
    records for `validate_evidence_trace`.

    `load_chunks` performs *"no structural contract validation and no mutation
    or repair"*, so this is the artifact as committed, container included.
    """
    return load_chunks()


@pytest.fixture
def real_chunks_by_id(real_chunks):
    """The committed Chunk Corpus keyed by chunk `id`."""
    return {chunk["id"]: chunk for chunk in real_chunks}
