"""Specification Family 3 — Construction Failure Surface.

Encodes the approved construction failure behaviour validated in *Sprint P3.1.5
Construction Validation Evidence* (§8, Failure Validation — 18/18) together
with the corpus/Manifest disagreement Case B (§7).

The claim being preserved is stronger than "construction raises on bad input".
It is that `DocumentConstructionError` is the **single public construction
failure surface**: every one of the eighteen measured failure modes surfaces as
exactly that type, no `OSError`, `BadZipFile`, `KeyError`, `ParseError`,
`JSONDecodeError`, `UnicodeDecodeError`, or `ValueError` escapes it, and every
wrapped failure preserves its originating cause via `raise ... from exc`. Each
specification therefore asserts the surfaced type, and — where P3.1.5 recorded
one — the chained cause.

`docs/DOCUMENT_CONSTRUCTION_PLAN.md` §10.2's flat exception pattern (one
dedicated, direct `Exception` subclass per responsibility, no shared base) is
specified here too, since a later sprint introducing a shared hierarchy would
silently widen every `except DocumentConstructionError` in the repository.

Deferred findings F-1 and F-2 are excluded from this suite; see the permanent
record in tests/conftest.py. In particular, no specification below asserts that
a `..`-escaping or absolute `documents[].source` is rejected — under approved
repository behaviour it is not (F-2), and writing a failing specification for
unapproved behaviour is out of scope for this sprint.
"""

import json
import os
import xml.etree.ElementTree as ET
import zipfile

import pytest

from scripts.build_manifest import ManifestValidationError

from sample_rag.chunker import ChunkConstructionError
from sample_rag.knowledge_source import DocumentConstructionError

WORDPROCESSINGML_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


# --- Failure-mode constructors ---------------------------------------------
#
# One per row of the P3.1.5 Failure Validation table. Each prepares a corpus
# that reaches exactly one failure path; none relies on another's setup.


def _missing_manifest(corpus):
    pass  # the manifest is simply never written


def _malformed_manifest_json(corpus):
    corpus.raw_manifest('{"documents": [')


def _manifest_not_an_object(corpus):
    corpus.raw_manifest("[]")


def _documents_key_missing(corpus):
    corpus.manifest({"manifest_version": "1.0"})


def _documents_not_a_list(corpus):
    corpus.manifest({"documents": {"id": "a"}})


def _entry_not_an_object(corpus):
    corpus.manifest({"documents": ["documents/a.txt"]})


def _entry_id_missing(corpus):
    corpus.manifest({"documents": [{"source": "documents/a.txt"}]})


def _entry_id_not_a_string(corpus):
    corpus.manifest({"documents": [{"id": 123, "source": "documents/a.txt"}]})


def _entry_source_not_a_string(corpus):
    corpus.manifest({"documents": [{"id": "a", "source": 123}]})


def _unsupported_extension(corpus):
    corpus.binary_file("documents/report.pdf", b"%PDF-1.4")
    corpus.entries(("id-pdf", "documents/report.pdf"))


def _missing_corpus_item(corpus):
    corpus.entries(("id-gone", "documents/gone.txt"))


def _docx_is_not_a_zip(corpus):
    corpus.text_file("documents/broken.docx", "this is plain text, not an OOXML package")
    corpus.entries(("id-docx", "documents/broken.docx"))


def _docx_missing_main_part(corpus):
    corpus.docx_package("documents/partless.docx", {"word/settings.xml": "<settings/>"})
    corpus.entries(("id-docx", "documents/partless.docx"))


def _docx_unparseable_xml(corpus):
    corpus.docx_package("documents/unparseable.docx", {"word/document.xml": "<w:document>"})
    corpus.entries(("id-docx", "documents/unparseable.docx"))


def _docx_without_body(corpus):
    corpus.docx_package(
        "documents/bodyless.docx",
        {
            "word/document.xml": (
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                f'<w:document xmlns:w="{WORDPROCESSINGML_NS}"/>'
            )
        },
    )
    corpus.entries(("id-docx", "documents/bodyless.docx"))


def _non_utf8_text_file(corpus):
    corpus.binary_file("documents/latin1.txt", b"caf\xe9 \xff\xfe not utf-8")
    corpus.entries(("id-latin1", "documents/latin1.txt"))


def _unreadable_file(corpus):
    if os.geteuid() == 0:
        pytest.skip("file permissions are not enforced for the superuser")
    path = corpus.text_file("documents/locked.txt", "unreadable content")
    path.chmod(0o000)
    try:
        path.read_text(encoding="utf-8")
    except PermissionError:
        pass
    else:
        pytest.skip("filesystem does not enforce read permissions here")
    corpus.entries(("id-locked", "documents/locked.txt"))


def _source_names_a_directory(corpus):
    corpus.directory("documents/folder.txt")
    corpus.entries(("id-dir", "documents/folder.txt"))


def _nul_byte_in_source(corpus):
    corpus.entries(("id-nul", "documents/a\x00b.txt"))


FAILURE_MODES = [
    pytest.param(_missing_manifest, FileNotFoundError, id="missing-manifest"),
    pytest.param(_malformed_manifest_json, json.JSONDecodeError, id="malformed-manifest-json"),
    pytest.param(_manifest_not_an_object, None, id="manifest-not-an-object"),
    pytest.param(_documents_key_missing, None, id="documents-key-missing"),
    pytest.param(_documents_not_a_list, None, id="documents-not-a-list"),
    pytest.param(_entry_not_an_object, None, id="entry-not-an-object"),
    pytest.param(_entry_id_missing, None, id="entry-id-missing"),
    pytest.param(_entry_id_not_a_string, None, id="entry-id-not-a-string"),
    pytest.param(_entry_source_not_a_string, None, id="entry-source-not-a-string"),
    pytest.param(_unsupported_extension, None, id="unsupported-extension"),
    pytest.param(_missing_corpus_item, None, id="missing-corpus-item"),
    pytest.param(_docx_is_not_a_zip, zipfile.BadZipFile, id="docx-is-not-a-zip"),
    pytest.param(_docx_missing_main_part, KeyError, id="docx-missing-main-part"),
    pytest.param(_docx_unparseable_xml, ET.ParseError, id="docx-unparseable-xml"),
    pytest.param(_docx_without_body, None, id="docx-without-body"),
    pytest.param(_non_utf8_text_file, UnicodeDecodeError, id="non-utf8-text-file"),
    pytest.param(_unreadable_file, PermissionError, id="unreadable-file"),
    pytest.param(_source_names_a_directory, None, id="source-names-a-directory"),
    pytest.param(_nul_byte_in_source, None, id="nul-byte-in-source"),
]


@pytest.mark.parametrize(("prepare", "expected_cause"), FAILURE_MODES)
def test_every_failure_mode_surfaces_as_document_construction_error(
    synthetic_corpus, prepare, expected_cause
):
    """Each measured failure mode raises exactly `DocumentConstructionError`.

    This is also where "zero leaks" is specified: any escaping `OSError`,
    `BadZipFile`, `KeyError`, `ParseError`, `JSONDecodeError`,
    `UnicodeDecodeError`, or `ValueError` is not caught by `pytest.raises` here
    and fails the corresponding specification outright.

    `type(...) is` rather than `isinstance(...)`: the claim is that this is the
    surface, not that something merely compatible with it was raised. Where
    P3.1.5 recorded a chained cause, the cause is specified too — the wrapping
    must preserve `from exc`, or the underlying failure becomes undiagnosable
    from the caller's side.
    """
    prepare(synthetic_corpus)

    with pytest.raises(DocumentConstructionError) as excinfo:
        synthetic_corpus.load()

    assert type(excinfo.value) is DocumentConstructionError
    assert str(excinfo.value), "the failure surface must carry a diagnostic message"

    if expected_cause is None:
        assert excinfo.value.__cause__ is None
    else:
        assert isinstance(excinfo.value.__cause__, expected_cause)


# --- Corpus/Manifest disagreement, Case B ----------------------------------


def test_case_b_manifest_entry_without_a_corpus_file_raises(synthetic_corpus):
    """Case B — a Manifest entry whose file is absent raises, never narrows silently.

    The mirror of Case A (tests/test_knowledge_source_construction.py): a file
    the Manifest does not list is excluded silently, but a file the Manifest
    *does* list and the corpus lacks is an Input failure
    (`docs/DOCUMENT_CONSTRUCTION_PLAN.md` §10.1) and must raise. Specified
    separately from the `missing-corpus-item` failure mode above because it
    encodes a different approved claim — the asymmetry of the two disagreement
    directions — even though both reach the same code path.
    """
    synthetic_corpus.text_file("documents/present.txt", "present content")
    synthetic_corpus.entries(
        ("id-present", "documents/present.txt"),
        ("id-gone", "documents/gone.txt"),
    )

    with pytest.raises(DocumentConstructionError) as excinfo:
        synthetic_corpus.load()

    assert "documents/gone.txt" in str(excinfo.value)


# --- The failure surface itself --------------------------------------------


def test_document_construction_error_is_a_direct_exception_subclass():
    """`DocumentConstructionError` is a direct `Exception` subclass.

    `docs/DOCUMENT_CONSTRUCTION_PLAN.md` §10.2 inherits the repository's flat
    pattern deliberately. Introducing a base class later would widen every
    existing `except DocumentConstructionError` without any call site changing.
    """
    assert DocumentConstructionError.__bases__ == (Exception,)


def test_document_construction_error_is_independent_of_the_other_error_types():
    """The construction failure surface is scoped to construction alone.

    No catch of `ManifestValidationError` or `ChunkConstructionError` may
    incidentally catch a construction failure, and vice versa — that
    independence is what makes one exception type per responsibility mean
    anything.
    """
    for other in (ManifestValidationError, ChunkConstructionError):
        assert not issubclass(DocumentConstructionError, other)
        assert not issubclass(other, DocumentConstructionError)
