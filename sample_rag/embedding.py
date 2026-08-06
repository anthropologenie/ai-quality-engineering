"""The `EmbeddingProvider` seam, and its deterministic Milestone 1B stand-in.

Sprint 1B.1: implements register capabilities **1B-01** (`EmbeddingProvider`
interface) and **1B-04** (deterministic placeholder vectors).

`docs/architecture.md` §5 scopes this component *"**1B** — interface + stub
only"*, with *"BGE-small-en-v1.5 (Milestone 2 default)"* as its future
evolution. §7 gives the Protocol shape this module realizes unchanged:

    class EmbeddingProvider(Protocol):
        def embed(self, text: str) -> list[float]: ...

§5's *Interface* column writes the return type as `Vector`; §7 writes the same
type concretely as `list[float]`. This module uses §7's concrete form, because
it is the one stated as code and no repository authority defines a `Vector`
alias.

Why an interface plus a stub, and not an implementation
--------------------------------------------------------
`docs/MILESTONE_1A.md` criterion A-1 requires the seam be *"defined and
swappable — a stub implementation can be replaced without changing calling
code."* `docs/architecture.md` §7 states the reason: *"the correctness of the
pipeline's plumbing … is independent of which embedding model eventually fills
the interface."*

`docs/MILESTONE_1A.md` criterion A-5 — *"Zero imports of any embedding,
vector-store, or LLM-evaluation library anywhere in the codebase"* — **remains
binding throughout Milestone 1B** (`docs/DEFERRED_ITEMS_REGISTER.md` §3 exit
condition; `docs/architecture.md` §9). This module imports `hashlib` and
`typing` and nothing else.

Placeholder values are meaningful, not arbitrary
-------------------------------------------------
`docs/MILESTONE_1A.md` build item 3 calls for *"deterministic placeholder
vectors/hashes"*; build item 4 sets the standard the values must meet, in the
`RetrievalResult` precedent: *"Placeholder values are meaningful, not
arbitrary — they let the pytest suite assert on structure **and** semantics
now … so Milestone 2 swaps values inside an already-correct shape rather than
changing the shape itself."*

Applied here, that means the vector is **content-derived**, as a real embedding
is. Three properties follow and are specified in `tests/test_indexer.py`:

    identical text            -> identical vector
    differing text            -> differing vector
    any text                  -> exactly PLACEHOLDER_DIMENSION components

A constant vector would satisfy the type and fail every one of them, and would
let a Milestone 2 swap change the shape rather than only the values.

What this stub deliberately is not
-----------------------------------
It carries no semantic similarity. Two texts with the same meaning produce
unrelated vectors, because the derivation is a digest. That is the intended
Milestone 1B property, not a limitation to be worked around: `docs/altm.md`
§12 records Milestone 1B as *"Still no real metric at any stage"*, and
retrieval-quality behaviour is Milestone 2 (`docs/DEFERRED_ITEMS_REGISTER.md`
**M2-01**). Nothing in the repository consumes these vectors for ranking.
"""

import hashlib

from typing import Protocol, runtime_checkable

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


@runtime_checkable
class EmbeddingProvider(Protocol):
    """The embedding seam frozen by `docs/architecture.md` §5 and §7.

    `runtime_checkable` so a specification can assert conformance structurally
    rather than by inheritance — which is what criterion A-1's *"swappable"*
    means in practice: a Milestone 2 provider satisfies this Protocol by
    having the method, without importing or subclassing anything here.
    """

    def embed(self, text: str) -> list[float]:
        """Convert `text` into its vector representation."""
        ...


class DeterministicEmbeddingProvider:
    """The Milestone 1B stand-in: content-derived placeholder vectors.

    Pure and total. No filesystem, network, clock, locale, randomness, or
    shared mutable state — so `embed` is a function of `text` alone, and the
    Index built over a fixed Chunk Corpus is itself deterministic
    (`docs/architecture.md` §9; `docs/MILESTONE_1A.md` build item 1's
    deterministic-artifact discipline, applied one stage later).

    Structurally a `EmbeddingProvider` without declaring it: the Protocol is
    satisfied by shape, which is the property criterion A-1 asks for. Declaring
    inheritance would make the seam nominal and would not survive a Milestone 2
    provider that does not import this module.
    """

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
