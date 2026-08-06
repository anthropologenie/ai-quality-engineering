"""Specification Family — the Index stage.

Sprint 1B.1 specifies register capabilities **1B-01** (`EmbeddingProvider`
interface), **1B-02** (`VectorStore` interface), **1B-03** (`Indexer`
component) and **1B-04** (deterministic placeholder vectors).

Scope boundary against Data Quality Validation
-----------------------------------------------
This file specifies the **components**. `tests/test_data_quality.py` specifies
**DQ-7**, index coverage over the committed corpus (register **1B-10**). The
split is not stylistic — `docs/DATA_QUALITY_VALIDATION_PLAN.md` §6.1 assigns
row 9, *"Index coverage — every chunk has a deterministic placeholder
representation behind `EmbeddingProvider`"*, to Data Quality Validation, and
§6.2 keeps single-artifact and corpus-wide claims in separate owners.

Determinism in particular belongs here and not there. Plan §6.1 row 10 assigns
determinism verification to the **Executable Specification Suite**, and §11.3
bars DQV from re-specifying it. So `test_1b04_*` below pins repeated
construction; no DQ-7 specification does.

Behaviour, not artefacts
-------------------------
No specification here freezes a literal vector, a digest, or a corpus fact.
The placeholder derivation is asserted through its *properties* — determinism,
sensitivity to content, stable width — exactly as `tests/conftest.py` records
for `Document.text`: *"a digest is a fact about one corpus snapshot and one
extraction mechanism, not a contractual property."* A frozen vector literal
would break the moment `PLACEHOLDER_DIMENSION` moved, and would specify the
digest rather than the contract.

Criterion A-5, structurally
----------------------------
`docs/MILESTONE_1A.md` criterion A-5 — *"Zero imports of any embedding,
vector-store, or LLM-evaluation library anywhere in the codebase"* — **remains
binding throughout Milestone 1B** (`docs/DEFERRED_ITEMS_REGISTER.md` §3 exit
condition). The three new modules are the first Milestone 1B additions to
`sample_rag/`, and each carries an AST import allowlist below, following the
precedent `tests/test_generator.py` and `tests/test_cli.py` set. An allowlist
fails on any import nobody thought to forbid, which a denylist would not.
"""

import ast
import inspect

import pytest

from sample_rag.embedding import (
    PLACEHOLDER_DIMENSION,
    DeterministicEmbeddingProvider,
    EmbeddingProvider,
)
from sample_rag.indexer import Index, Indexer
from sample_rag.vector_store import VectorStore


def imported_roots(module):
    """The top-level package of every import in `module`'s source."""
    tree = ast.parse(inspect.getsource(module))

    roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".")[0])
    return roots


def imported_modules(module):
    """Every fully-qualified module name imported by `module`'s source."""
    tree = ast.parse(inspect.getsource(module))

    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def chunk(chunk_id, text):
    """A minimal chunk in the serialized form the Index stage receives.

    Only `id` and `text` are read by `Indexer.index`, so only those are
    supplied. Building a full six-field contract chunk here would imply the
    Indexer depends on offsets it never touches.
    """
    return {"id": chunk_id, "text": text}


# --- 1B-01: the `EmbeddingProvider` interface -------------------------------


def test_1b01_embedding_provider_declares_the_architecture_protocol():
    """1B-01 — the seam exists with the shape `docs/architecture.md` §7 states.

    §7's Protocol sketch is `def embed(self, text: str) -> list[float]`, and
    §5's *Interface* column gives the same method as
    `EmbeddingProvider.embed(text: str) -> Vector`.

    The register records why the mere existence of this seam is the capability:
    `docs/DEFERRED_ITEMS_REGISTER.md` §4.1 R-1B-01/02 — *"Milestone 2 must
    replace an implementation behind a contract that already exists; this one
    does not exist."* Its blocking status is **Blocks 2 entry** for that reason.
    """
    signature = inspect.signature(EmbeddingProvider.embed)

    assert list(signature.parameters) == ["self", "text"]
    assert signature.parameters["text"].annotation is str
    assert signature.return_annotation == list[float]


def test_1b01_a_conforming_provider_satisfies_the_protocol_structurally():
    """1B-01 — conformance is by shape, not by inheritance.

    `docs/MILESTONE_1A.md` criterion A-1: *"defined and swappable — a stub
    implementation can be replaced without changing calling code."*

    The local class below imports nothing from the repository and inherits from
    nothing, which is exactly the position a Milestone 2 provider is in. If
    conformance required subclassing, the seam would be nominal and A-1 would
    be unsatisfied in the case it exists for.
    """

    class ForeignProvider:
        def embed(self, text: str) -> list[float]:
            return [0.0]

    assert isinstance(ForeignProvider(), EmbeddingProvider)


def test_1b01_a_non_conforming_object_does_not_satisfy_the_protocol():
    """1B-01 — the Protocol check has teeth.

    Guards the assertion above: a `runtime_checkable` Protocol that accepted
    anything would make the conformance specification vacuous.
    """

    class NotAProvider:
        def encode(self, text: str) -> list[float]:
            return [0.0]

    assert not isinstance(NotAProvider(), EmbeddingProvider)


def test_1b01_embedding_module_imports_only_stdlib():
    """1B-01 / A-5 — the embedding seam imports no embedding library.

    `docs/MILESTONE_1A.md` criterion A-5, binding throughout Milestone 1B. An
    allowlist, so an import nobody thought to forbid fails here.
    """
    import sample_rag.embedding as module

    assert imported_roots(module) <= {"hashlib", "typing"}
    assert imported_modules(module) <= {"hashlib", "typing"}


# --- 1B-02: the `VectorStore` interface -------------------------------------


def test_1b02_vector_store_declares_both_architecture_methods():
    """1B-02 — the seam exists with the shape `docs/architecture.md` §7 states.

    §7: `upsert(self, chunk_id: str, vector: list[float]) -> None` and
    `query(self, vector: list[float], top_k: int) -> list[str]`.

    Same standing as 1B-01 — **Blocks 2 entry** — and the same reasoning at
    §4.1 R-1B-01/02: *"Same seam, same constraint."*
    """
    upsert = inspect.signature(VectorStore.upsert)
    query = inspect.signature(VectorStore.query)

    assert list(upsert.parameters) == ["self", "chunk_id", "vector"]
    assert upsert.parameters["chunk_id"].annotation is str
    assert upsert.parameters["vector"].annotation == list[float]
    assert upsert.return_annotation is None

    assert list(query.parameters) == ["self", "vector", "top_k"]
    assert query.parameters["vector"].annotation == list[float]
    assert query.parameters["top_k"].annotation is int
    assert query.return_annotation == list[str]


def test_1b02_a_conforming_store_satisfies_the_protocol_structurally():
    """1B-02 — conformance by shape, for the same A-1 reason as 1B-01."""

    class ForeignStore:
        def upsert(self, chunk_id: str, vector: list[float]) -> None:
            return None

        def query(self, vector: list[float], top_k: int) -> list[str]:
            return []

    assert isinstance(ForeignStore(), VectorStore)


def test_1b02_a_partial_store_does_not_satisfy_the_protocol():
    """1B-02 — both methods are required, not either.

    A store with `upsert` alone would persist vectors nothing could read back.
    """

    class UpsertOnly:
        def upsert(self, chunk_id: str, vector: list[float]) -> None:
            return None

    assert not isinstance(UpsertOnly(), VectorStore)


def test_1b02_no_vector_store_implementation_is_shipped():
    """1B-02 — *"interface only, no implementation"*, enforced.

    `docs/architecture.md` §5 scopes this component *"1B — interface only, no
    implementation"* and `docs/DEFERRED_ITEMS_REGISTER.md` **1B-02** quotes
    that scope verbatim. The module must therefore define the Protocol and
    nothing else — shipping a stub would implement a Milestone 2 capability
    (**M2-02**), whose engine is itself still unresolved at register §6.

    Asserted structurally over the module's own source, so a future addition
    fails here rather than passing unnoticed.
    """
    import sample_rag.vector_store as module

    tree = ast.parse(inspect.getsource(module))
    declared = [node.name for node in tree.body if isinstance(node, ast.ClassDef)]

    assert declared == ["VectorStore"]


def test_1b02_vector_store_module_imports_only_stdlib():
    """1B-02 / A-5 — the vector-store seam imports no vector-store library."""
    import sample_rag.vector_store as module

    assert imported_roots(module) <= {"typing"}
    assert imported_modules(module) <= {"typing"}


# --- 1B-04: deterministic placeholder vectors -------------------------------


def test_1b04_identical_text_yields_an_identical_vector():
    """1B-04 — determinism, the property `docs/architecture.md` §9 requires.

    §9 scopes Milestone 1B as *"`Indexer` with deterministic placeholder
    vectors"*. Two constructions over equal input must agree, which is how
    `docs/DOCUMENT_CONTRACT.md` §8.8 item 1 defines determinism for this
    repository — *repeated construction yields equal values*, not a frozen
    literal.
    """
    provider = DeterministicEmbeddingProvider()

    assert provider.embed("alpha beta") == provider.embed("alpha beta")


def test_1b04_determinism_holds_across_provider_instances():
    """1B-04 — the derivation carries no per-instance state.

    A provider that memoized into instance state would pass the specification
    above and fail here. `docs/DATA_QUALITY_VALIDATION_PLAN.md` §7.5's
    discipline — no shared mutable state, no iteration-order dependence —
    applied to the stage that produces the values.
    """
    assert DeterministicEmbeddingProvider().embed("alpha") == (
        DeterministicEmbeddingProvider().embed("alpha")
    )


def test_1b04_differing_text_yields_a_differing_vector():
    """1B-04 — the placeholder is *meaningful*, not arbitrary.

    `docs/MILESTONE_1A.md` build item 4 sets the standard: *"Placeholder values
    are meaningful, not arbitrary — they let the pytest suite assert on
    structure **and** semantics now … so Milestone 2 swaps values inside an
    already-correct shape rather than changing the shape itself."*

    This is the specification that standard reduces to for a vector. A constant
    vector would satisfy the type, the width, and determinism, and would fail
    only here — which is why the case exists.
    """
    provider = DeterministicEmbeddingProvider()

    assert provider.embed("alpha") != provider.embed("beta")


def test_1b04_every_vector_carries_the_declared_dimension():
    """1B-04 — a stable width, whatever the input length.

    The shape property a Milestone 2 provider must preserve. Texts of very
    different sizes are used, so a derivation that leaked input length into the
    output width would fail rather than pass on same-sized samples.
    """
    provider = DeterministicEmbeddingProvider()

    for text in ["", "a", "alpha beta gamma", "x" * 4096]:
        assert len(provider.embed(text)) == PLACEHOLDER_DIMENSION


def test_1b04_components_are_floats_in_the_unit_interval():
    """1B-04 — the component type and range the Protocol promises.

    `docs/architecture.md` §7 types the return `list[float]`. The range is a
    construction property of this stand-in rather than a contract clause, and
    is specified so a Milestone 2 swap that changed it is a visible decision
    rather than a silent one.
    """
    components = DeterministicEmbeddingProvider().embed("alpha beta gamma")

    assert all(isinstance(component, float) for component in components)
    assert all(0.0 <= component < 1.0 for component in components)


def test_1b04_the_stub_provider_satisfies_the_embedding_protocol():
    """1B-04 — the stand-in conforms to the 1B-01 seam it stands in behind.

    `docs/MILESTONE_1A.md` build item 3: placeholder vectors stand in for real
    embeddings *"behind the `EmbeddingProvider` interface"*. If the stub did
    not satisfy the Protocol, the interface would not be the seam the
    Milestone 2 provider replaces it at.
    """
    assert isinstance(DeterministicEmbeddingProvider(), EmbeddingProvider)


# --- 1B-03: the `Indexer` component -----------------------------------------


def test_1b03_index_covers_every_chunk_it_was_given():
    """1B-03 — the Indexer's own coverage guarantee.

    `docs/architecture.md` §5: `Indexer.index(chunks: List[Chunk]) -> Index`,
    *"Build a lookup structure over chunks."* Every chunk in, every chunk
    represented.

    Distinct from DQ-7, which asserts the same property over the **committed
    corpus** (`tests/test_data_quality.py`, register **1B-10**). This one is
    about the component; that one is about the repository.
    """
    chunks = [chunk("c0", "alpha"), chunk("c1", "beta"), chunk("c2", "gamma")]

    index = Indexer().index(chunks)

    assert all(index.covers(entry["id"]) for entry in chunks)
    assert set(index.vectors) == {"c0", "c1", "c2"}


def test_1b03_index_introduces_no_chunk_of_its_own():
    """1B-03 — coverage is exact, not merely sufficient.

    The complement of the specification above. An Indexer that emitted a
    representation for an id it never received would satisfy coverage and
    corrupt the join `sample_rag/retriever.py` and DQ-6 both depend on.
    """
    index = Indexer().index([chunk("c0", "alpha")])

    assert set(index.vectors) == {"c0"}


def test_1b03_index_records_the_provider_dimension():
    """1B-03 — `dimension` reports the injected provider's width, not the stub's.

    Read from the produced vectors rather than assumed, so a Milestone 2
    provider of a different width records its own. A hardcoded dimension would
    pass with the stub and misreport for every real provider.
    """

    class WideProvider:
        def embed(self, text: str) -> list[float]:
            return [0.0] * 384

    assert Indexer(WideProvider()).index([chunk("c0", "alpha")]).dimension == 384


def test_1b03_an_empty_chunk_collection_yields_an_empty_index():
    """1B-03 — zero chunks is legal at this stage, as it is at the last one.

    `docs/CHUNK_CONTRACT.md` §11 fixes the cardinality at *"one document
    produces **zero** or more chunks"*, and
    `docs/DATA_QUALITY_VALIDATION_PLAN.md` §8.2 records empty text as *"not a
    failure at all"*. A corpus that legally produced no chunks reaches this
    stage as an empty collection; raising here would make legal upstream state
    fail downstream.
    """
    index = Indexer().index([])

    assert index.vectors == {}
    assert index.dimension == PLACEHOLDER_DIMENSION


def test_1b03_the_index_declares_itself_a_stub():
    """1B-03 — `stub is True`, following the `RetrievalResult` precedent.

    `docs/MILESTONE_1A.md` build item 4 froze `diagnostics["stub"] is True` so
    the suite could *"assert on structure **and** semantics now"*. The same
    marker here is what lets a specification state that this Index holds
    placeholder values rather than inferring it from their provenance — and
    what makes a Milestone 2 Index that dropped the marker a visible change.
    """
    assert Indexer().index([chunk("c0", "alpha")]).stub is True


def test_1b03_a_replacement_provider_changes_no_calling_code():
    """1B-03 / A-1 — the swappability criterion, demonstrated at the seam.

    `docs/MILESTONE_1A.md` criterion A-1: *"a stub implementation can be
    replaced without changing calling code."* The two `index(...)` calls below
    are byte-identical; only the constructor argument differs, and the produced
    vectors differ accordingly.

    This is the specification that makes A-1 checkable rather than asserted.
    """

    class ConstantProvider:
        def embed(self, text: str) -> list[float]:
            return [1.0] * PLACEHOLDER_DIMENSION

    chunks = [chunk("c0", "alpha")]

    default_index = Indexer().index(chunks)
    swapped_index = Indexer(ConstantProvider()).index(chunks)

    assert set(default_index.vectors) == set(swapped_index.vectors)
    assert default_index.vectors["c0"] != swapped_index.vectors["c0"]
    assert swapped_index.vectors["c0"] == [1.0] * PLACEHOLDER_DIMENSION


def test_1b03_indexing_is_deterministic_across_runs():
    """1B-03 — the stage inherits the provider's determinism.

    `docs/architecture.md` §9 scopes Milestone 1B's Index as deterministic.
    Determinism of the *values* is 1B-04's claim; this is determinism of the
    *stage*, which also covers key ordering and would fail if the Indexer
    introduced iteration-order or state dependence between runs.
    """
    chunks = [chunk("c0", "alpha"), chunk("c1", "beta")]

    first = Indexer().index(chunks)
    second = Indexer().index(chunks)

    assert first.vectors == second.vectors
    assert list(first.vectors) == list(second.vectors)


def test_1b03_the_index_is_frozen():
    """1B-03 — `Index` is a value, not a mutable accumulator.

    Follows `Document`, `Chunk` and `RetrievalResult`, all frozen dataclasses.
    A consumer cannot rebind a field to make coverage appear satisfied.

    The `vectors` mapping itself remains mutable, which
    `docs/DEFERRED_ITEMS_REGISTER.md` **NA-04** records as an accepted
    limitation of the same shape in `RetrievalResult`. This specification pins
    the frozen half that the repository does guarantee.
    """
    index = Indexer().index([chunk("c0", "alpha")])

    with pytest.raises(Exception):
        index.stub = False


def test_1b03_indexer_module_imports_only_stdlib_and_the_embedding_seam():
    """1B-03 / A-5 — the Index stage imports no embedding or vector library.

    Also pins `docs/architecture.md` §6's barred direction: `sample_rag/` never
    imports `scripts/`. The allowlist below would fail on such an import.
    """
    import sample_rag.indexer as module

    assert imported_roots(module) <= {"dataclasses", "sample_rag"}
    assert imported_modules(module) <= {"dataclasses", "sample_rag.embedding"}
