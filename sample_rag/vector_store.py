"""The `VectorStore` seam — interface only, no implementation.

Sprint 1B.1: implements register capability **1B-02**.

`docs/architecture.md` §5 scopes this component *"**1B** — interface only, no
implementation"*, with *"FAISS (Milestone 2 default)"* as its future
evolution. §7 gives the Protocol shape this module realizes unchanged:

    class VectorStore(Protocol):
        def upsert(self, chunk_id: str, vector: list[float]) -> None: ...
        def query(self, vector: list[float], top_k: int) -> list[str]: ...

Why there is no stub here, when `EmbeddingProvider` has one
------------------------------------------------------------
The two seams are scoped differently by the same table, and the difference is
deliberate rather than an omission. `docs/architecture.md` §5 reads
*"interface + stub only"* for `EmbeddingProvider` and *"interface only, no
implementation"* for `VectorStore`; `docs/DEFERRED_ITEMS_REGISTER.md` **1B-02**
quotes that scope verbatim — *"scoped 'interface only, no implementation'"* —
and no register capability allocates a `VectorStore` implementation to
Milestone 1B.

The asymmetry is load-bearing. `docs/MILESTONE_1A.md` build item 3 requires
placeholder vectors to *exist*, so the Index stage has something to hold, and
**1B-04** supplies them behind `EmbeddingProvider`. Nothing at Milestone 1B
queries by vector: `docs/architecture.md` §9 places hybrid retrieval and the
vector route at Milestone 2 (**M2-02**, **M2-04**), and §5 records the
`VectorStore` implementation choice as still unresolved
(`docs/DEFERRED_ITEMS_REGISTER.md` §6). A stub implementing `query` would have
to invent a ranking rule that no authority states, for a route no caller takes.

What this module therefore establishes
---------------------------------------
The contract Milestone 2 replaces an implementation *behind*, which is the
whole reason **1B-02** carries the blocking status *Blocks 2 entry*:
`docs/DEFERRED_ITEMS_REGISTER.md` §4.1 R-1B-01/02 — *"Milestone 2 must replace
an implementation behind a contract that already exists; this one does not
exist."* After this module, it does.

Criterion **A-5** — *"Zero imports of any embedding, vector-store, or
LLM-evaluation library"* — remains binding throughout Milestone 1B. This module
imports `typing` and nothing else.
"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class VectorStore(Protocol):
    """The vector-persistence seam frozen by `docs/architecture.md` §5 and §7.

    `runtime_checkable` for the same reason `EmbeddingProvider` carries it: a
    Milestone 2 implementation satisfies this Protocol by shape, without
    importing or subclassing anything here — which is what
    `docs/MILESTONE_1A.md` criterion A-1's *"swappable"* requires.

    Both methods are declared exactly as `docs/architecture.md` §7 states them.
    `query` returning `list[str]` is chunk **ids**, matching the identity
    `docs/CHUNK_CONTRACT.md` §17 makes globally unique and the join key
    `sample_rag/retriever.py` already ranks on.
    """

    def upsert(self, chunk_id: str, vector: list[float]) -> None:
        """Persist `vector` under `chunk_id`, replacing any existing entry."""
        ...

    def query(self, vector: list[float], top_k: int) -> list[str]:
        """Return the ids of the `top_k` nearest stored vectors to `vector`."""
        ...
