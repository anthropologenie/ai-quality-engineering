"""Specification Family 1 — Runtime Contract.

Encodes the approved Document Contract (`docs/DOCUMENT_CONTRACT.md` §8.7) as
executable specifications, one per validated engineering claim A1–A16 from
*Sprint P3.1.5 Construction Validation Evidence* (§2, Contract Validation
Report — Layer A).

These specifications answer, independently: is `Document` still a dataclass, is
it still frozen, does it still expose exactly `id` and `text`, are the field
types preserved, and do equality, hashing, and immutability remain correct.
Each claim is asserted on its own; nothing is inferred from another check —
that separation is the property the P3.1.5 evidence established and this file
preserves.

Contract invariant 3 (determinism) is a property of *repeated* construction,
not of a single value (`docs/DOCUMENT_CONTRACT.md` §8.8), so it is specified in
tests/test_knowledge_source_construction.py, not here.

Deferred findings F-1 and F-2 are excluded from this suite; see the permanent
record in tests/conftest.py.
"""

import dataclasses
import typing

import pytest

from sample_rag.document import Document

CONTRACT_FIELD_NAMES = ("id", "text")


# --- A1–A9: declared shape -------------------------------------------------


def test_a1_load_produces_documents_of_runtime_type_document(real_documents):
    """A1 — every value returned by `load()` has runtime type `Document`."""
    assert real_documents, "the committed corpus must yield at least one Document"
    for document in real_documents:
        assert type(document) is Document


def test_a2_document_is_a_dataclass():
    """A2 — `Document` is a dataclass."""
    assert dataclasses.is_dataclass(Document)


def test_a3_document_is_frozen():
    """A3 — frozen behaviour is declared, not merely conventional."""
    assert Document.__dataclass_params__.frozen is True


def test_a4_document_declares_exactly_two_fields():
    """A4 — the contract's schema has two fields, no more, no less (§8.7)."""
    assert len(dataclasses.fields(Document)) == 2


def test_a5_document_field_names_are_id_and_text():
    """A5 — the two fields are exactly `id` and `text`, in contract order."""
    assert tuple(f.name for f in dataclasses.fields(Document)) == CONTRACT_FIELD_NAMES


def test_a6_declared_field_types_are_str():
    """A6 — both fields are declared `str` (§8.7 schema table)."""
    hints = typing.get_type_hints(Document)
    assert hints == {"id": str, "text": str}


def test_a7_constructed_field_values_are_str_at_runtime(real_documents):
    """A7 — the declared types hold for values construction actually produces."""
    for document in real_documents:
        assert isinstance(document.id, str)
        assert isinstance(document.text, str)


def test_a8_documents_carry_no_extra_instance_attributes(real_documents):
    """A8 — no field beyond the contract's two is silently attached."""
    for document in real_documents:
        assert sorted(vars(document)) == sorted(CONTRACT_FIELD_NAMES)


def test_a9_fields_have_no_defaults_or_default_factories():
    """A9 — both fields are required; neither may be omitted at construction."""
    for field in dataclasses.fields(Document):
        assert field.default is dataclasses.MISSING
        assert field.default_factory is dataclasses.MISSING


# --- A10–A11: immutability -------------------------------------------------


def _mutation_attacks():
    """The four distinct mutation attacks P3.1.5 measured, kept separate."""
    return [
        pytest.param(lambda d: setattr(d, "id", "reassigned"), id="assign-id"),
        pytest.param(lambda d: setattr(d, "text", "reassigned"), id="assign-text"),
        pytest.param(lambda d: delattr(d, "id"), id="delete-id"),
        pytest.param(lambda d: setattr(d, "added", "new"), id="add-attribute"),
    ]


@pytest.mark.parametrize("attack", _mutation_attacks())
def test_a10_mutation_attacks_are_blocked_by_frozen_instance_error(attack):
    """A10 — each mutation attack is refused with `FrozenInstanceError`.

    Parametrized rather than combined: a single assertion block would let one
    attack's success hide behind another's failure, which is precisely the
    separation the P3.1.5 evidence insisted on.
    """
    document = Document(id="doc-a10", text="original text")
    with pytest.raises(dataclasses.FrozenInstanceError):
        attack(document)


@pytest.mark.parametrize("attack", _mutation_attacks())
def test_a11_document_state_is_intact_after_each_mutation_attack(attack):
    """A11 — a refused attack leaves the value unchanged, not partially mutated."""
    document = Document(id="doc-a11", text="original text")
    with pytest.raises(dataclasses.FrozenInstanceError):
        attack(document)
    assert document.id == "doc-a11"
    assert document.text == "original text"


# --- A12–A14: contract invariants 1 and 2 ----------------------------------


def test_a12_document_id_equals_the_manifest_documents_id(real_documents, real_manifest_entries):
    """A12 — invariant 1: `id` is a `str` equal to `documents[].id` (§8.7).

    The manifest entry is read from the artifact independently of construction,
    so this compares the produced value against the source of identity rather
    than against itself.
    """
    assert len(real_documents) == len(real_manifest_entries)
    for document, entry in zip(real_documents, real_manifest_entries):
        assert isinstance(document.id, str)
        assert document.id == entry["id"]


def test_a13_document_identity_is_non_empty(real_documents):
    """A13 — a produced identity is never the empty string."""
    for document in real_documents:
        assert len(document.id) > 0


def test_a14_text_is_str_and_empty_text_is_a_legal_document(real_documents):
    """A14 — invariant 2: `text` is a `str`; empty is permitted, not an error.

    §8.3's non-empty guarantee is deliberately absent from the contract, and
    `docs/CHUNK_CONTRACT.md` §11 already makes a zero-chunk document legal, so
    an empty-text `Document` must remain constructible.
    """
    for document in real_documents:
        assert isinstance(document.text, str)
    assert Document(id="doc-a14", text="").text == ""


# --- A15–A16: behaviour surface, equality, hashing -------------------------


def test_a15_document_exposes_no_behavioural_methods():
    """A15 — `Document` owns no behaviour (Contract Phase 9).

    Only the members a frozen dataclass necessarily synthesizes are permitted;
    any additional public or private callable would make `Document` something
    other than a passive, corpus-derived data value.
    """
    synthesized = {
        "__init__",
        "__repr__",
        "__eq__",
        "__hash__",
        "__setattr__",
        "__delattr__",
        "__dataclass_fields__",
        "__dataclass_params__",
        "__match_args__",
        "__doc__",
        "__module__",
        "__dict__",
        "__weakref__",
        "__annotations__",
        "__firstlineno__",
        "__static_attributes__",
    }
    declared = set(vars(Document)) - synthesized
    assert declared == set(), f"Document declares unexpected members: {sorted(declared)}"


def test_a16_documents_support_value_equality_and_hashing():
    """A16 — equality is by value and instances are hashable.

    Both halves belong to one claim: a frozen dataclass's hashability is
    defined in terms of the same field tuple its equality uses, so specifying
    them apart would assert the same underlying property twice.
    """
    first = Document(id="doc-a16", text="identical text")
    second = Document(id="doc-a16", text="identical text")
    different = Document(id="doc-a16", text="different text")

    assert first == second
    assert first is not second
    assert first != different

    assert hash(first) == hash(second)
    assert len({first, second}) == 1
