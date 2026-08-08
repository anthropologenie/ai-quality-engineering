"""Specification Family — the Index stage.

Sprint 1B.1 specifies register capabilities **1B-01** (`EmbeddingProvider`
interface), **1B-02** (`VectorStore` interface), **1B-03** (`Indexer`
component) and **1B-04** (deterministic placeholder vectors).

Sprint M2.01A specifies register capability **M2-01** — the real
`EmbeddingProvider`, `BAAI/bge-small-en-v1.5`. The 1B specifications above are
retained unchanged wherever the transition did not touch them, which is most of
them: that they still pass against a real model is the evidence that the seam
was correct.

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
vector-store, or LLM-evaluation library anywhere in the codebase"* — **remained
binding throughout Milestone 1B** (`docs/DEFERRED_ITEMS_REGISTER.md` §3 exit
condition). The three modules specified here are the first Milestone 1B
additions to `sample_rag/`, and each carries an AST import allowlist below,
following the precedent `tests/test_generator.py` and `tests/test_cli.py` set.
An allowlist fails on any import nobody thought to forbid, which a denylist
would not.

**Sprint M2.01A moves one of those allowlists, and only one.** The
embedding-library portion of A-5 ceases to apply at this sprint, for **M2-01**
alone, so `sample_rag/embedding.py`'s allowlist admits
`sentence_transformers` and nothing else. The other two allowlists are
untouched: `sample_rag/vector_store.py` still admits `typing` only, and
`sample_rag/indexer.py` still admits `dataclasses` and `sample_rag.embedding`
only. A vector-store import (**M2-02**) or an evaluation-tool import
(**M2-07**, **M2-08**, **M3-06**) therefore still fails a specification, which
is how the narrowness of the exception is enforced rather than merely stated.
"""

import ast
import inspect

import pytest

from sample_rag.embedding import (
    EMBEDDING_DIMENSION,
    EMBEDDING_MODEL_ID,
    EMBEDDING_MODEL_REVISION,
    PLACEHOLDER_DIMENSION,
    BGEEmbeddingProvider,
    DeterministicEmbeddingProvider,
    EmbeddingModelUnavailableError,
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


def test_m201_the_embedding_seam_imports_the_embedding_library_and_nothing_more():
    """M2-01 / A-5 — the transition, bounded to one library in one module.

    Through Milestone 1B this specification read *"imports only stdlib"*, and
    passed. Sprint M2.01A is the authorized point at which the
    **embedding-library** portion of `docs/MILESTONE_1A.md` criterion A-5
    ceases to apply, for **M2-01** and nothing else, so the allowlist admits
    `sentence_transformers` and is otherwise unchanged.

    Still an allowlist, and that is the whole point of leaving it here rather
    than deleting it: a vector-store library (**M2-02**), an LLM SDK
    (**M2-06**) or an evaluation tool (**M2-07**, **M2-08**, **M3-06**)
    imported into this module fails, because the exception granted was for one
    library and this specification is what makes "one" checkable.
    """
    import sample_rag.embedding as module

    assert imported_roots(module) <= {"hashlib", "typing", "sentence_transformers"}
    assert imported_modules(module) <= {"hashlib", "typing", "sentence_transformers"}


def test_m201_no_other_pipeline_module_imports_the_embedding_library():
    """M2-01 / A-5 — the exception did not leak past the seam.

    Criterion A-1's *"swappable"* has a consequence that is easy to lose at the
    moment a real model arrives: if the pipeline reached the model directly,
    the seam would be decorative. Every module in `sample_rag/` other than the
    seam itself must therefore still be free of the embedding library, exactly
    as it was at Milestone 1B.

    Stated over the package as a whole rather than module by module, so a
    module added later is covered without anyone remembering to add it here.
    """
    import importlib
    import pathlib

    import sample_rag.embedding

    # `sample_rag` is a namespace package — it has no `__init__.py`, so it has
    # no `__file__` to take a directory from. The seam module is inside the
    # package by construction, so its parent is the package root.
    package_root = pathlib.Path(sample_rag.embedding.__file__).parent

    offenders = []
    for path in sorted(package_root.glob("*.py")):
        if path.name == "embedding.py":
            continue

        module = importlib.import_module(f"sample_rag.{path.stem}")
        if "sentence_transformers" in imported_roots(module):
            offenders.append(path.name)

    assert offenders == [], f"embedding library imported outside the seam: {offenders}"


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
    (**M2-02**), whose engine the Repository Owner has since elected as FAISS
    (register §6, Sprint RO-06 / RO-07) and which no sprint has yet built.
    Sprint M2.01A implements the embedding provider and deliberately not this:
    an implementation appearing here would be the boundary crossing this
    specification exists to catch.

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


# --- M2-01: the real embedding provider -------------------------------------


def cosine(left, right):
    """Cosine similarity between two vectors.

    Written here rather than imported, and deliberately so. No repository
    component computes vector similarity: `sample_rag/vector_store.py` is
    interface-only and `sample_rag/retriever.py` ranks lexically. A similarity
    function in `sample_rag/` would be the first half of a vector-retrieval
    route, which `docs/DEFERRED_ITEMS_REGISTER.md` **M2-02** and **M2-04** own
    and Sprint M2.01A does not implement. Here it is a measuring instrument for
    a specification, not a component of the pipeline.

    Both operands are unit-norm by the checkpoint's own Normalize module, so
    this is also their dot product; the division is kept because the function's
    name promises cosine, not a shortcut that holds only for normalized input.
    """
    dot = sum(x * y for x, y in zip(left, right))
    norms = sum(x * x for x in left) ** 0.5 * sum(y * y for y in right) ** 0.5

    return dot / norms


def test_m201_the_elected_model_and_revision_are_pinned():
    """M2-01 — the model is the elected one, at a fixed revision.

    `docs/architecture.md` §5 (*"BGE-small-en-v1.5 (Milestone 2 default)"*) and
    §9 (*"Real `EmbeddingProvider` implementation (BGE-small-en-v1.5
    default)"*), `docs/roadmap.md` §7 and register **M2-01** all name this
    model. Substituting another is a Repository Owner decision, and this
    specification is what makes a silent substitution impossible.

    The revision literal is frozen here, which is the one place this suite
    freezes a literal on purpose. Everywhere else — see the module docstring —
    a frozen value would specify a snapshot rather than a contract. A model
    revision is the opposite case: it *is* the contract, because it is what
    makes an embedding reproducible at all. A model id alone names a branch
    that can move.
    """
    assert EMBEDDING_MODEL_ID == "BAAI/bge-small-en-v1.5"
    assert EMBEDDING_MODEL_REVISION == "5c38ec7c405ec4b44b94cc5a9bb96e735b38267a"

    provider = BGEEmbeddingProvider()

    assert provider.model_id == EMBEDDING_MODEL_ID
    assert provider.revision == EMBEDDING_MODEL_REVISION


def test_m201_the_real_provider_satisfies_the_embedding_protocol():
    """M2-01 — the real provider conforms to the seam it replaces the stub at.

    The specification criterion A-1 was written for:
    `docs/MILESTONE_1A.md` — *"defined and swappable — a stub implementation
    can be replaced without changing calling code."* The Protocol has not
    changed since Sprint 1B.2; the implementation behind it has.
    """
    assert isinstance(BGEEmbeddingProvider(), EmbeddingProvider)


def test_m201_every_embedding_carries_the_model_dimension():
    """M2-01 — the checkpoint's declared width, whatever the input length.

    384 is the model's own `word_embedding_dimension`, and the shape property
    the Index Layer records. Texts of very different sizes are used, so a
    derivation that leaked input length into the output width would fail here
    rather than pass on same-sized samples — the same standard
    `test_1b04_every_vector_carries_the_declared_dimension` holds the stand-in
    to.
    """
    provider = BGEEmbeddingProvider()

    for text in ["", "a", "alpha beta gamma", "x " * 2048]:
        assert len(provider.embed(text)) == EMBEDDING_DIMENSION

    assert EMBEDDING_DIMENSION == 384


def test_m201_components_are_plain_floats():
    """M2-01 — the return type `docs/architecture.md` §7 states, exactly.

    The model computes in NumPy `float32`. A list of NumPy scalars satisfies
    `list[float]` to a type checker's eye and hands every consumer — including
    a future `VectorStore` and every serializer — a type no repository
    contract names. The conversion is therefore behaviour, and is specified.
    """
    components = BGEEmbeddingProvider().embed("alpha beta gamma")

    assert all(type(component) is float for component in components)


def test_m201_embeddings_are_unit_norm():
    """M2-01 — the checkpoint's Normalize module, observed rather than imposed.

    `BAAI/bge-small-en-v1.5`'s `modules.json` declares Transformer → Pooling →
    Normalize, so its embeddings are L2-normalized by the published model's own
    definition. `sample_rag/embedding.py` passes no normalization argument; if
    it silently renormalized, or if a future change loaded the raw weights
    without the checkpoint's declared modules, this specification is what
    notices.

    The tolerance is float32 rounding, not slack in the claim.
    """
    for text in ["alpha", "a much longer sentence about quality engineering work"]:
        vector = BGEEmbeddingProvider().embed(text)
        norm = sum(component * component for component in vector) ** 0.5

        assert abs(norm - 1.0) < 1e-5


def test_m201_identical_text_yields_an_identical_embedding():
    """M2-01 — determinism, unchanged as a requirement by the model's arrival.

    `docs/architecture.md` §9 and `docs/DOCUMENT_CONTRACT.md` §8.8 item 1 define
    determinism for this repository as *repeated construction yields equal
    values*. A probabilistic **representation** is not a nondeterministic
    **computation**: nothing in this forward pass samples, and an embedding
    that varied between calls would make every downstream artifact
    irreproducible.
    """
    provider = BGEEmbeddingProvider()

    assert provider.embed("alpha beta") == provider.embed("alpha beta")


def test_m201_determinism_holds_across_provider_instances():
    """M2-01 — the derivation carries no per-instance state.

    The same guard `test_1b04_determinism_holds_across_provider_instances`
    places on the stand-in. It has teeth here only because
    `sample_rag/embedding.py` caches the loaded *model* and never the
    *vectors*: a per-text memo would satisfy this specification by construction
    and stop it from checking anything.
    """
    assert BGEEmbeddingProvider().embed("alpha") == BGEEmbeddingProvider().embed("alpha")


def test_m201_differing_text_yields_a_differing_embedding():
    """M2-01 — the representation is content-derived, as the placeholder was.

    Retained from 1B-04 because it remains the floor: whatever else a real
    model adds, it must not collapse distinct inputs onto one vector.
    """
    provider = BGEEmbeddingProvider()

    assert provider.embed("alpha") != provider.embed("beta")


def test_m201_related_text_embeds_nearer_than_unrelated_text():
    """M2-01 — **the capability itself**: semantic representation.

    Everything above this specification was already true of the Milestone 1B
    digest. This is the property that was not, and could not be:
    `sample_rag/embedding.py`'s stand-in *"carries no semantic similarity …
    two texts with the same meaning produce unrelated vectors, because the
    derivation is a digest."*

    Stated as a **relative ordering**, not an absolute threshold. A threshold
    would freeze a number that belongs to one checkpoint on one corpus and
    would specify the model's calibration rather than the repository's claim.
    The claim is that meaning now moves the vector, and the ordering is what
    says so.

    The margin is wide by construction — a resume-domain pair against a
    plainly unrelated sentence — so this specification fails on a broken
    integration (wrong pooling, missing normalization, an untrained head)
    rather than on ordinary model variation.
    """
    provider = BGEEmbeddingProvider()

    subject = provider.embed("The candidate led software quality engineering initiatives.")
    related = provider.embed("The engineer managed software testing and quality assurance.")
    unrelated = provider.embed("Rainfall in the coastal region peaked during the monsoon.")

    assert cosine(subject, related) > cosine(subject, unrelated)


def test_m201_the_placeholder_provider_still_carries_no_semantic_similarity():
    """M2-01 — the contrast that makes the specification above meaningful.

    The stand-in is run against the *same* three texts. Its ordering is a
    property of SHA-256, so it is not required to come out either way — what is
    required is that its similarities are unrelated to meaning, which is
    visible as a near-orthogonal relationship to both texts alike.

    Without this case, the semantic specification above could be read as
    something the repository always had. It is not: this is what Milestone 1B
    validated against, and the difference is the sprint.
    """
    provider = DeterministicEmbeddingProvider()

    subject = provider.embed("The candidate led software quality engineering initiatives.")
    related = provider.embed("The engineer managed software testing and quality assurance.")

    real = BGEEmbeddingProvider()
    real_similarity = cosine(
        real.embed("The candidate led software quality engineering initiatives."),
        real.embed("The engineer managed software testing and quality assurance."),
    )

    assert cosine(subject, related) < real_similarity


def test_m201_providers_declare_whether_they_are_placeholders():
    """M2-01 — the declaration the Index Layer reads to mark an Index.

    `Index.stub` has to come from somewhere. It is declared on the
    implementations rather than added to `EmbeddingProvider`, because
    `docs/architecture.md` §7 freezes that Protocol at one method — so the
    marker is honest about the provider in use without the seam growing a
    field the architecture does not state.
    """
    assert BGEEmbeddingProvider().placeholder is False
    assert BGEEmbeddingProvider().dimension == EMBEDDING_DIMENSION

    assert DeterministicEmbeddingProvider().placeholder is True
    assert DeterministicEmbeddingProvider().dimension == PLACEHOLDER_DIMENSION


def test_m201_an_unobtainable_model_fails_as_a_named_engineering_error():
    """M2-01 — model acquisition failure is a stated condition, not a stack trace.

    Sprint M2.01A's own acquisition rule is that an unobtainable model stops
    the work and is reported — *no substitute may be selected*. The runtime
    equivalent is that the failure must be recognizable: a raw HTTP or
    filesystem error from inside a model loader does not say *the elected
    checkpoint was not obtained*, and a caller cannot distinguish it from a
    bug in this repository.

    The provider is asked for a checkpoint that cannot resolve, which is the
    same failure a missing cache with no network produces at the same call
    site.
    """
    provider = BGEEmbeddingProvider(
        model_id="ai-quality-engineering/no-such-model", revision="0" * 40
    )

    with pytest.raises(EmbeddingModelUnavailableError):
        provider.embed("alpha")


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

    With no vector to measure, the width is taken from the provider's declared
    `dimension` — so an empty Index reports the width its provider *would* have
    produced, rather than a constant that is right for one provider and wrong
    for the other. Both are asserted, because a single fallback constant would
    pass one of them by accident.
    """
    index = Indexer().index([])

    assert index.vectors == {}
    assert index.dimension == EMBEDDING_DIMENSION
    assert Indexer(DeterministicEmbeddingProvider()).index([]).dimension == (
        PLACEHOLDER_DIMENSION
    )


def test_1b03_the_index_declares_what_kind_of_vectors_it_holds():
    """1B-03 / M2-01 — the `stub` marker now reports the provider in use.

    `docs/MILESTONE_1A.md` build item 4 froze `diagnostics["stub"] is True` so
    the suite could *"assert on structure **and** semantics now"*, and this
    specification read `stub is True` throughout Milestone 1B for that reason.

    Sprint M2.01A is where it changes, and the change is the point: the marker
    exists so that *which kind of Index this is* is a stated fact rather than
    an inference, and a marker that could only ever say `True` would have
    stopped being one the moment a real provider existed. Both directions are
    asserted, so the value tracks the provider rather than a milestone
    constant.
    """
    assert Indexer().index([chunk("c0", "alpha")]).stub is False

    placeholder_index = Indexer(DeterministicEmbeddingProvider()).index(
        [chunk("c0", "alpha")]
    )

    assert placeholder_index.stub is True


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
