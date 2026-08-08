"""The `EmbeddingProvider` seam, and the implementations behind it.

Sprint 1B.1: implements register capabilities **1B-01** (`EmbeddingProvider`
interface) and **1B-04** (deterministic placeholder vectors).

Sprint M2.01A: implements register capability **M2-01** — the real
`EmbeddingProvider`, `BAAI/bge-small-en-v1.5`. This is the repository's first
probabilistic component.

`docs/architecture.md` §5 scopes this component *"**1B** — interface + stub
only"*, with *"BGE-small-en-v1.5 (Milestone 2 default)"* as its future
evolution; §9 states the same model for Milestone 2 — *"Real
`EmbeddingProvider` implementation (BGE-small-en-v1.5 default)"*. §7 gives the
Protocol shape this module realizes unchanged:

    class EmbeddingProvider(Protocol):
        def embed(self, text: str) -> list[float]: ...

§5's *Interface* column writes the return type as `Vector`; §7 writes the same
type concretely as `list[float]`. This module uses §7's concrete form, because
it is the one stated as code and no repository authority defines a `Vector`
alias.

**The Protocol is unchanged by Sprint M2.01A.** `BGEEmbeddingProvider` is
supplied *behind* it, which is precisely the property Milestone 1B existed to
establish: `docs/DEFERRED_ITEMS_REGISTER.md` §4.1 R-1B-01/02 — *"Milestone 2
must replace an implementation behind a contract that already exists"* — and
**M2-01**'s own rationale, *"replaces 1B-01's stub behind an unchanged
contract."* Nothing was added to the seam to make the real provider fit.

Criterion A-5 — the transition, recorded
-----------------------------------------
`docs/MILESTONE_1A.md` criterion A-5 — *"Zero imports of any embedding,
vector-store, or LLM-evaluation library anywhere in the codebase"* — was
binding through Milestone 1A and **remained binding throughout Milestone 1B**
(`docs/DEFERRED_ITEMS_REGISTER.md` §3 exit condition; `docs/architecture.md`
§9). Sprint M2.01A is the authorized transition point at which the
**embedding-library portion** of that criterion ceases to apply, and this
module is where it ceases: `import sentence_transformers` below is the first
external AI dependency in the repository's history.

The exception is exactly this wide and no wider:

    embedding library      -> permitted here, from Sprint M2.01A, for M2-01
    vector-store library   -> still barred (M2-02; `sample_rag/vector_store.py`
                              remains interface-only)
    LLM-evaluation library -> still barred (M2-07, M2-08, M3-06)

`tests/test_indexer.py` holds the AST allowlist that enforces the boundary, so
the transition is specified rather than asserted, and an import of a vector
store or an evaluation tool still fails there.

Why `sentence-transformers`, and what "the model" means
--------------------------------------------------------
No repository authority names a *library* — only a **model**,
`BAAI/bge-small-en-v1.5`, which the register, `docs/architecture.md` §5 and §9
and `docs/roadmap.md` §7 all name. The library is therefore an implementation
choice made here, on the same standing as `hashlib` for the stand-in below,
and it is `sentence-transformers` for one reason: the published checkpoint
*is* a Sentence-Transformers model. Its `modules.json` declares Transformer →
Pooling → Normalize, its `1_Pooling/config.json` declares CLS pooling, and its
`2_Normalize` module declares L2 normalization. Loading it through
`SentenceTransformer` applies the checkpoint's own declared pooling and
normalization; loading the raw weights through any other runtime would mean
re-implementing them here and calling the result the same model.

So `encode` below passes **no** pooling or normalization arguments of its own.
The published checkpoint defines the semantics of "BGE-small-en-v1.5"; this
module does not redefine them.

Reproducibility — the model revision is pinned
------------------------------------------------
`EMBEDDING_MODEL_REVISION` pins the exact HuggingFace commit the vectors come
from. A model id alone names a moving branch: `main` today and `main` after an
upstream re-upload are not required to produce identical vectors, and a
repository whose validation asserts semantic properties cannot have its inputs
move underneath it silently. The revision is passed to every load, so an
execution either uses that exact checkpoint or fails to load.

Determinism, and what it does and does not mean here
------------------------------------------------------
`docs/architecture.md` §9 and `docs/DOCUMENT_CONTRACT.md` §8.8 item 1 define
determinism for this repository as *repeated construction yields equal values*
— not as a frozen literal. `BGEEmbeddingProvider` satisfies that: the model is
loaded in evaluation mode, on CPU, from a pinned revision, with no sampling
anywhere in the forward pass, so `embed` is a function of `text` alone within
a repository execution and across executions on the same environment.

What it deliberately does **not** claim is bitwise identity across *different*
environments. Floating-point reduction order can differ across CPU
architectures, BLAS builds and thread counts. That is a property of numerical
computation, not a defect introduced here, and it is why every specification
in `tests/test_indexer.py` states embedding behaviour as a **property** —
determinism, width, unit norm, relative semantic ordering — and freezes no
vector literal. The engineering evidence records the environment alongside the
revision for the same reason.

The stand-in is retained, and is no longer the default
--------------------------------------------------------
`DeterministicEmbeddingProvider` remains in this module. It is register
capability **1B-04**, discharged at Sprint 1B.2, and `docs/DEFERRED_ITEMS_REGISTER.md`
§1.3 — *"a capability is never deleted"* — is the disposition this module
follows for the code that realizes one. What Sprint M2.01A changes is which
provider the Index stage uses **by default**: `sample_rag/indexer.py` now
constructs `BGEEmbeddingProvider`, so the repository's committed corpus is
represented by real embeddings. The stand-in survives as an injectable, fast,
network-free provider for specifications that are about the *seam* rather than
about the model.
"""

import hashlib

from typing import Protocol, runtime_checkable

from sentence_transformers import SentenceTransformer

# The model `docs/architecture.md` §5 and §9, `docs/roadmap.md` §7 and
# `docs/DEFERRED_ITEMS_REGISTER.md` **M2-01** all name, and the Repository
# Owner elected for Sprint M2.01A. Not a configurable default: substituting a
# different model is a Repository Owner decision, not an engineering one.
EMBEDDING_MODEL_ID = "BAAI/bge-small-en-v1.5"

# The exact HuggingFace commit the repository's embeddings are produced from.
# `main` at the time of Sprint M2.01A; pinned so that it stays this checkpoint
# whatever `main` becomes later.
EMBEDDING_MODEL_REVISION = "5c38ec7c405ec4b44b94cc5a9bb96e735b38267a"

# The checkpoint's own width, declared by its `1_Pooling/config.json`
# (`word_embedding_dimension: 384`). Recorded rather than discovered so the
# Index Layer has a declared width for a corpus that produced no chunks, in
# the same position `PLACEHOLDER_DIMENSION` held at Milestone 1B.
EMBEDDING_DIMENSION = 384

# Construction values, not contract fields — the same standing
# `sample_rag/chunker.py` gives MAX_STRUCTURAL_CHUNK_CHARACTERS and
# `sample_rag/retriever.py` gives DEFAULT_TOP_K. No repository authority fixes
# an embedding dimension at Milestone 1B: `docs/architecture.md` §5 names the
# Milestone 2 model but this milestone has no model, and §9 requires only that
# the values be deterministic placeholders. 16 is a conservative width that
# makes the shape assertable without implying a model's dimensionality.
PLACEHOLDER_DIMENSION = 16

# Two digest bytes per component, read big-endian, scaled onto [0, 1).
_BYTES_PER_COMPONENT = 2
_COMPONENT_SCALE = float(1 << (8 * _BYTES_PER_COMPONENT))

# Loaded models, keyed by the (id, revision) pair that identifies a checkpoint.
# A memo of an immutable, evaluation-mode model — not shared mutable state in
# the sense `docs/DATA_QUALITY_VALIDATION_PLAN.md` §7.5 bars, because nothing
# reachable from `embed` writes to a loaded model and the cache cannot change
# any vector it returns. It exists because loading is the expensive step and
# every `Indexer()` constructs a provider.
_LOADED_MODELS: dict = {}


class EmbeddingModelUnavailableError(Exception):
    """Raised when the elected embedding checkpoint cannot be loaded.

    Scoped exclusively to model acquisition — a missing local cache with no
    network, a revision that does not resolve, a corrupt download. Not reused
    for anything about the text being embedded, which has no failure mode:
    `embed` is total over `str`.

    A named exception rather than a bare propagation because the failure has a
    specific engineering meaning that Sprint M2.01A's brief states directly —
    the model could not be obtained, no substitute may be selected, and the
    repository's real embeddings therefore do not exist in that environment.
    `sample_rag/chunker.py`, `scripts/build_chunks.py` and
    `sample_rag/knowledge_source.py` each own a scoped exception of this shape
    for the same reason.
    """


@runtime_checkable
class EmbeddingProvider(Protocol):
    """The embedding seam frozen by `docs/architecture.md` §5 and §7.

    `runtime_checkable` so a specification can assert conformance structurally
    rather than by inheritance — which is what criterion A-1's *"swappable"*
    means in practice: a Milestone 2 provider satisfies this Protocol by
    having the method, without importing or subclassing anything here.

    **Unchanged at Sprint M2.01A.** `BGEEmbeddingProvider` conforms to this
    declaration exactly as written at Sprint 1B.2, which is the evidence that
    the seam was correct: a real model was fitted behind it without the
    interface moving.
    """

    def embed(self, text: str) -> list[float]:
        """Convert `text` into its vector representation."""
        ...


def _load_model(model_id: str, revision: str) -> SentenceTransformer:
    """Return the loaded checkpoint for `(model_id, revision)`, loading once.

    `device="cpu"` is fixed rather than auto-selected. Device selection would
    otherwise be an environment property that silently changes the arithmetic
    the repository's embeddings are produced by, and this repository's whole
    disposition — `docs/architecture.md` §9, the byte-identity determinism
    specification — is that an execution's inputs are stated, not discovered.
    No repository capability requires GPU execution: `docs/roadmap.md` §7
    places *"GPU optimization"* out of scope entirely.

    A load failure is translated rather than propagated, because the raw
    failure surfaces as a network or filesystem error whose engineering
    meaning — *the elected model was not obtained* — is not visible in it.
    """
    key = (model_id, revision)

    if key not in _LOADED_MODELS:
        try:
            _LOADED_MODELS[key] = SentenceTransformer(
                model_id, revision=revision, device="cpu"
            )
        except Exception as error:
            raise EmbeddingModelUnavailableError(
                f"could not load the elected embedding model {model_id} at "
                f"revision {revision}: {error}"
            ) from error

    return _LOADED_MODELS[key]


class BGEEmbeddingProvider:
    """The Milestone 2A provider: real semantic embeddings from BGE-small-en-v1.5.

    Register capability **M2-01**, `docs/DEFERRED_ITEMS_REGISTER.md` §4 — *"The
    first probabilistic component; replaces 1B-01's stub behind an unchanged
    contract."*

    Structurally an `EmbeddingProvider` without declaring it, exactly as the
    stand-in is. `docs/MILESTONE_1A.md` criterion A-1 asks that a stub *"can be
    replaced without changing calling code"*; this class is the case that
    criterion was written for, and it satisfies the Protocol by shape alone.

    What changes at this seam, and what does not
    ---------------------------------------------
    The vectors are now **semantic**: two texts that mean similar things
    produce nearby vectors, which the stand-in's digest could never do and
    never claimed to. Everything else the repository asserts about the seam
    holds unchanged — `embed` is a total function of `text`, deterministic,
    of stable width, returning `list[float]`.

    `dimension` and `placeholder`
    ------------------------------
    Two class attributes the Index Layer reads, and the seam does not carry.
    They are declared on implementations rather than added to
    `EmbeddingProvider`, because `docs/architecture.md` §7 freezes that
    Protocol at one method and Sprint M2.01A's brief bars redesigning it.
    `sample_rag/indexer.py` reads both defensively, so a foreign provider that
    declares neither still works — which is the point of a structural seam.
    """

    dimension = EMBEDDING_DIMENSION
    placeholder = False

    def __init__(
        self,
        model_id: str = EMBEDDING_MODEL_ID,
        revision: str = EMBEDDING_MODEL_REVISION,
    ):
        """Construct the provider. **The model is not loaded here.**

        Loading is deferred to the first `embed`, so constructing a provider —
        which `Indexer()` does on every construction, including in
        specifications that never embed anything — costs nothing and needs
        neither a warm model cache nor a network.

        The parameters exist so a specification can name the checkpoint it
        means. They are not a configuration surface: the elected model and
        revision are the defaults, and choosing another is a Repository Owner
        decision.
        """
        self._model_id = model_id
        self._revision = revision

    @property
    def model_id(self) -> str:
        """The checkpoint this provider embeds with."""
        return self._model_id

    @property
    def revision(self) -> str:
        """The exact checkpoint commit this provider embeds with.

        Exposed so engineering evidence can record the revision an execution
        actually used, rather than the one a constant says it should have.
        """
        return self._revision

    def embed(self, text: str) -> list[float]:
        """Return the semantic embedding of `text`.

        `encode` is called with no pooling or normalization arguments: the
        checkpoint's `modules.json` already declares CLS pooling and L2
        normalization, so the returned vector is unit-norm by the published
        model's own definition rather than by a choice made here.

        No instruction prefix is applied. BGE's asymmetric retrieval prefix
        (*"Represent this sentence for searching relevant passages:"*) belongs
        to the **query** side of a retrieval system, and this sprint
        implements no retrieval — `docs/DEFERRED_ITEMS_REGISTER.md` **M2-02**
        and **M2-04** own that. Passages take no prefix in BGE's own usage, and
        every text this seam sees today is a chunk.

        The empty string is a legal input and returns a vector like any other,
        for the reason the stand-in states: `docs/DOCUMENT_CONTRACT.md` §8.3
        leaves `Document.text` free to be empty and `docs/CHUNK_CONTRACT.md`
        §17 invariant 1 keeps empty text out of chunks, so this path is
        unreachable from the committed corpus and is defined rather than
        guarded.

        The components are converted to `float` explicitly. `encode` returns a
        NumPy array of `float32`; `docs/architecture.md` §7 types this return
        `list[float]`, and returning NumPy scalars inside a list would satisfy
        the annotation while handing every consumer a type the contract does
        not name.
        """
        vector = _load_model(self._model_id, self._revision).encode(text)

        return [float(component) for component in vector]


class DeterministicEmbeddingProvider:
    """The Milestone 1B stand-in: content-derived placeholder vectors.

    Register capability **1B-04**, discharged at Sprint 1B.2. **Superseded as
    the repository default at Sprint M2.01A** by `BGEEmbeddingProvider`, and
    retained — never deleted — because `docs/DEFERRED_ITEMS_REGISTER.md` §1.3
    keeps discharged capabilities in the record, and because specifications
    about the *seam* rather than the *model* are better served by a provider
    that needs no checkpoint.

    Pure and total. No filesystem, network, clock, locale, randomness, or
    shared mutable state — so `embed` is a function of `text` alone, and the
    Index built over a fixed Chunk Corpus is itself deterministic
    (`docs/architecture.md` §9; `docs/MILESTONE_1A.md` build item 1's
    deterministic-artifact discipline, applied one stage later).

    Structurally a `EmbeddingProvider` without declaring it: the Protocol is
    satisfied by shape, which is the property criterion A-1 asks for. Declaring
    inheritance would make the seam nominal and would not survive a Milestone 2
    provider that does not import this module.

    It carries no semantic similarity, and never did. Two texts with the same
    meaning produce unrelated vectors, because the derivation is a digest.
    That was the intended Milestone 1B property — `docs/altm.md` §12 records
    Milestone 1B as *"Still no real metric at any stage"* — and it is exactly
    the property `BGEEmbeddingProvider` now supplies.
    """

    dimension = PLACEHOLDER_DIMENSION
    placeholder = True

    def embed(self, text: str) -> list[float]:
        """Return the deterministic placeholder vector for `text`.

        SHA-256 gives 32 bytes; each pair becomes one component scaled onto
        [0, 1). `PLACEHOLDER_DIMENSION` components are taken, so the digest
        bounds the dimension rather than the dimension being padded — a wider
        placeholder would need a stated derivation, not repetition.

        The empty string is a legal input and returns a vector like any other.
        `docs/DOCUMENT_CONTRACT.md` §8.3 leaves `Document.text` free to be
        empty, and `docs/CHUNK_CONTRACT.md` §17 invariant 1 keeps empty text
        out of chunks — so this path is unreachable from the committed corpus
        and is defined rather than guarded, since a guard would raise on input
        no contract forbids.
        """
        digest = hashlib.sha256(text.encode("utf-8")).digest()

        return [
            int.from_bytes(
                digest[offset : offset + _BYTES_PER_COMPONENT], byteorder="big"
            )
            / _COMPONENT_SCALE
            for offset in range(
                0, PLACEHOLDER_DIMENSION * _BYTES_PER_COMPONENT, _BYTES_PER_COMPONENT
            )
        ]
