● Sprint P2.3.0 — Persistent Representation Architecture Decision

  1. Repository Discovery Report

  Knowledge Manifest lifecycle (repository fact, from git log and docs/MILESTONE_1A.md):

  ┌────────┬─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
  │ Sprint │                                                                             Action                                                                              │
  ├────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ P1.2.0 │ Contract frozen — in the same document, the same sprint, both the entity-level fields (documents[].id/source/hash/indexed) and the collection-level container   │
  │        │ (manifest_version + documents[]) were specified together (docs/MILESTONE_1A.md, build item 1)                                                                   │
  ├────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ P1.2.1 │ Assembly (assemble_manifest in scripts/build_manifest.py) — implements the already-frozen container directly; invents nothing                                   │
  ├────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ P1.2.2 │ Serialization (write_manifest) — writes the already-assembled structure to disk                                                                                 │
  ├────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ P1.3   │ Structural validation (validate_manifest)                                                                                                                       │
  └────────┴─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘

  No separate "Knowledge Manifest Artifact Contract" sprint or document exists anywhere in the repository. The container shape was never a distinct architectural decision — it
  was one schema-table row, decided at the same time as the entity fields.

  Chunk lifecycle to date:

  ┌───────────────┬────────────────────────────────────────────────────────────────────────────────────────┐
  │    Sprint     │                                         Action                                         │
  ├───────────────┼────────────────────────────────────────────────────────────────────────────────────────┤
  │ P2.1          │ docs/CHUNK_CONTRACT.md frozen — entity-level fields only (the six Chunk fields, §8)    │
  ├───────────────┼────────────────────────────────────────────────────────────────────────────────────────┤
  │ P2.2.1/P2.2.2 │ Runtime Chunker implemented and verified — in-memory construction only, no persistence │
  └───────────────┴────────────────────────────────────────────────────────────────────────────────────────┘

  The decisive piece of repository evidence is the Chunk Contract's own text, not an inference from the runtime implementation:

  ▎ docs/CHUNK_CONTRACT.md §19 (P2.3 readiness note): "one open question this document intentionally does not resolve: whether a wrapping container (analogous to the Knowledge
  ▎ Manifest's manifest_version + documents[] shape) is needed for a persisted chunk collection, and whether that container — not the individual Chunk entity — should carry its
  ▎ own schema-version field... this document recommends the same pattern for Chunk, but leaves the container's actual shape to P2.3."

  This is a repository fact recorded by the Contract itself, satisfying the constraint that architecture must not be inferred solely from the implementation. It establishes two
  things directly: (1) the container question is genuinely open, and (2) the pattern to follow (container carries version, entity does not — mirroring datasets/SCHEMA.md §9's
  documents[]/facts precedent, cited by the Contract itself) is already decided. Only the concrete shape remains open.

  A third relevant precedent — datasets/SCHEMA.md: this is the one case in the repository where a container/representation shape was frozen in its own dedicated sibling
  document, separate from entity content. But its justification is structural, not conceptual: datasets/SCHEMA.md governs nine files — three container types (facts, qa_pairs,
  evidence_trace) × three data sources (resume, job, jobops) — so a shared, reusable representation convention had genuine multi-instance leverage. Chunk has exactly one
  container shape to decide for one artifact family. This precedent does not transfer on its own terms.

  Runtime evidence (supporting, not primary): docs/architecture.md's sequence diagram shows Chunker handing Chunks to Indexer directly, in-memory (C->>IDX: Chunks) — the
  runtime pipeline does not read chunks back from disk. Persistence exists for a different, already-named reason: docs/MILESTONE_1A.md build item 8 requires an Evidence Trace
  Dataset with an Expected Chunk field, i.e., chunks need a stable, reviewable, on-disk ground-truth form for evaluation — the same role knowledge_manifest.json plays for
  corpus freshness validation, not a role requiring new collection-level logic.

  Current corpus scale: sample_rag/knowledge_manifest.json lists exactly one document. No repository evidence describes multi-document chunk-collection concerns (pagination,
  per-document files, partitioning) as a present need — only as a hypothetical future one.

  Conclusion of Discovery: existing repository conventions support adapting the same lightweight pattern already used for the Knowledge Manifest — not creating a new
  architectural concept, and not reusing datasets/SCHEMA.md's heavier multi-artifact pattern (no evidence of the multi-instance pressure that motivated it).

  ---
  2. Architectural Analysis

  Checking the examples of evidence that would justify a separate persistent contract (per this sprint's own P1 prompt):

  ┌───────────────────────────────────────────────┬─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
  │            Candidate justification            │                                               Repository evidence found?                                                │
  ├───────────────────────────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ Collection-level metadata beyond a version +  │ None. The Contract's own §19 note names exactly one candidate field (a container-level version marker) — the same shape │
  │ list wrapper                                  │  Knowledge Manifest already uses. No other collection-level field is named anywhere.                                    │
  ├───────────────────────────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ Persistence-specific logical structure        │ None. The six Chunk fields (§8) are already a complete, flat, serialization-ready shape (str/int only — no nested       │
  │ materially different from the entity schema   │ objects, no runtime-only fields per §15's deferrals). Nothing about persisting a Chunk requires restructuring it.       │
  ├───────────────────────────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ Downstream consumers requiring a canonical    │ None found. The one named downstream consumer of persisted chunks — the Evidence Trace Dataset's Expected Chunk field — │
  │ representation independent of the runtime     │  is described in docs/MILESTONE_1A.md build item 8 with no distinct shape requirement of its own; it references chunks, │
  │ Chunk                                         │  it doesn't demand a second competing schema for them.                                                                  │
  └───────────────────────────────────────────────┴─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘

  Runtime Chunk vs. persisted Chunk: do they have materially different responsibilities? No repository evidence found for this. The entity shape frozen in §8 is already minimal
  and flat by deliberate design (§5 justifies this: Chunk carries no probabilistic content, no query-time fields — those were explicitly routed to RetrievalResult instead,
  §15). There is nothing left in the entity that construction produces and serialization would need to transform or reshape.

  What genuinely remains open is narrower than "a persistent representation architecture": it is a single, bounded, already-precedented decision — does a persisted chunk
  collection get wrapped in a {version, chunks: [...]} container, and does that container (not the entity) carry the version field. The Contract has already answered the second
  half of that question by recommending the datasets/SCHEMA.md/Knowledge-Manifest pattern (§9, §19). Only the first half (the container's exact field names/shape) is undecided
  — the same scope of decision Knowledge Manifest resolved as one schema-table row inside its own contract-freeze sprint, not as a separate architectural layer.

  ---
  3. Architectural Decision Record

  ADR: Chunk Persistent Representation — Separate Contract or Direct Serialization Planning

  Question: Does the repository require a distinct architectural boundary — a separate persistent-representation contract — between the frozen runtime Chunk
  (docs/CHUNK_CONTRACT.md) and Chunk Serialization (P2.3)?

  Repository evidence considered:
  1. Knowledge Manifest precedent: container shape frozen together with entity fields, same sprint, same document (docs/MILESTONE_1A.md build item 1) — no separate layer was
  ever introduced for it.
  2. docs/CHUNK_CONTRACT.md §19: explicitly defers only the container's concrete shape, while already deciding the pattern (container-versioned, entity-unversioned) by direct
  reference to existing precedent.
  3. datasets/SCHEMA.md: the one true "separate representation contract" precedent in the repository — but justified by reuse across nine files/three artifact families, a
  condition Chunk does not share (one artifact family, one container decision).
  4. docs/architecture.md §8 sequence diagram: runtime hand-off from Chunker to Indexer is direct and in-memory; persistence serves the Evidence Trace Dataset
  (docs/MILESTONE_1A.md build item 8), not a runtime-pipeline requirement demanding a second schema.
  5. docs/CHUNK_CONTRACT.md §5: Chunk and Knowledge Manifest are already classified under the identical lifecycle — Data Model → Contract Freeze → Construction → Serialization
  → Validation — with no intermediate stage named for either.
  6. Current corpus scale (sample_rag/knowledge_manifest.json: one document) gives no evidence of multi-document collection complexity that would demand new architecture now.

  Alternatives evaluated:
  - A. Introduce a "Chunk Artifact Contract" as a new sibling document, mirroring docs/CHUNK_CONTRACT.md's own governance weight (discovery, ADR analysis, terminology review,
  freeze, sync). Rejected: no repository evidence of collection-level metadata, structural, or consumer complexity large enough to justify a second full contract-freeze cycle;
  would introduce a new first-class architectural concept without the evidentiary bar this sprint requires.
  - B. Resolve the container shape directly within Serialization Planning (P2.3.1), following Knowledge Manifest's own pattern, using the Contract's own already-stated
  recommendation (§9/§19) as the starting point. Supported by the strongest and most direct evidence: it is literally what happened for the artifact's own closest precedent,
  and it is what the Contract's authors already anticipated ("leaves the container's actual shape to P2.3" — P2.3, not a new P2.3.0.5 architecture layer).

  Decision: Alternative B. No separate persistent-representation contract is warranted. The open container-shape question is real but narrow, and belongs inside Serialization
  Planning, not a new architectural tier.

  Rationale: The repository's own precedent for an artifact in Chunk's exact position — a frozen entity contract, classified as a Persistent Canonical Artifact, needing only a
  wrapping container before serialization — already exists and required no separate layer (Knowledge Manifest). The one case where a separate representation-contract document
  was used (datasets/SCHEMA.md) is justified by a reuse condition (nine files, three artifact families) that Chunk does not have. Introducing a new architectural concept here
  would violate this sprint's own governing principle: "Do not introduce new first-class architectural concepts unless justified by repository evidence" — and no such
  justification was found.

  Consequences:
  - P2.3.1 (Serialization Planning) inherits the responsibility of finalizing the container shape as part of its own planning scope — it is not blocked on a prerequisite
  architecture sprint.
  - P2.3.1 should carry forward, not reopen, the Contract's own §9/§19 recommendation: entities stay unversioned; the container carries the version marker.
  - If, once real serialization is attempted, genuine collection-level complexity surfaces that this Discovery did not find evidence for (e.g., a real multi-document corpus
  revealing pagination needs), that would be new repository evidence and could justify revisiting this decision then — not preemptively now.
  - No new document, no new glossary term, and no new architectural layer is created by this decision.

  ---
  4. Recommendation

  Outcome B: proceed directly to P2.3.1 — Serialization Planning, following the same architectural pattern used by the Knowledge Manifest. Do not create a "Chunk Artifact
  Contract."

  ---
  5. Repository Synchronization Assessment

  Per Outcome B: confirmed — no new architectural terminology is required. No new document, glossary entry, or architectural concept is introduced by this ADR.
  docs/glossary.md, docs/architecture.md, and docs/MILESTONE_1A.md require no changes as a result of this sprint. docs/CHUNK_CONTRACT.md is unchanged and its §19 recommendation
  remains the authoritative starting point for P2.3.1.

  ---
  Per the Stop Condition: this sprint ends here. No specification or implementation work has begun. Awaiting architectural review before Serialization Planning (P2.3.1) begins.
