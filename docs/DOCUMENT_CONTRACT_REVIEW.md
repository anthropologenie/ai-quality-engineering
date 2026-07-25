  Independent Architectural Review — docs/DOCUMENT_CONTRACT.md

  Sprint: P2.5 Review Gate · Reviewer scope: governance gate, not redesign · Repository state reviewed: main @ a41cc4c, working tree with
  docs/DOCUMENT_CONTRACT.md untracked

  ---
  Executive Summary

  The proposed two-field Document Contract (id, text) is sound, evidence-backed, internally consistent, and construction-ready. Every field,
  invariant, deferral, and boundary in Phase 8 traces to a verifiable repository fact. Phase 0's classification of this sprint as a Contract Freeze
  is correct, and the non-execution of Phases 6–7 is correctly justified.

  However, the document's Phase 9 boundary table and Outstanding Question 2 assert an architectural ownership gap ("no component owns text
  extraction") that repository evidence contradicts — including evidence the document itself cites in Phase 1. docs/architecture.md §5 lists "resume
  file" as a dependency of Knowledge Source and KnowledgeSource.load() -> List[Document] as its interface; docs/architecture.md §10 locks the
  decision "Knowledge ingestion operates on the canonical .docx corpus"; and docs/altm.md line 149 — quoted in Phase 1 — names Knowledge Source as
  the Responsible Component for the Knowledge stage, whose inputs are raw files and whose output is the validated document set. Ownership is
  assigned. What remains open is the internal mechanism, which is Construction Planning's decision, not an architectural one.

  Correcting that overstatement removes the only claimed blocker rather than creating one. Applying the repository's own governance bar — the one
  docs/adr/ADR-0001 used to reject a new architectural layer for an analogous question — no additional ADR is required before Document Construction
  Planning.

  Recommended outcome: A — APPROVED. Three mandatory corrections to the document's analysis sections (not to the contract schema) and five minor
  accuracy corrections are recorded below.

  ---
  Overall Assessment

  ┌────────────────────────────────────┬──────────────────────────────────────────────────────────────────────────────────────────────┐
  │          Review dimension          │                                        Determination                                         │
  ├────────────────────────────────────┼──────────────────────────────────────────────────────────────────────────────────────────────┤
  │ Evidence completeness              │ Strong, with two material omissions (F2, F3)                                                 │
  ├────────────────────────────────────┼──────────────────────────────────────────────────────────────────────────────────────────────┤
  │ Evidence accuracy                  │ Strong on the contract's own evidence; four stale/imprecise citations (F4–F6, F8)            │
  ├────────────────────────────────────┼──────────────────────────────────────────────────────────────────────────────────────────────┤
  │ Traceability                       │ Excellent — every Phase 8 element cites a locatable source                                   │
  ├────────────────────────────────────┼──────────────────────────────────────────────────────────────────────────────────────────────┤
  │ Evidence-to-conclusion consistency │ One failure (F1) — Phase 3/9/11's Loader conclusion contradicts Phase 1's own cited evidence │
  ├────────────────────────────────────┼──────────────────────────────────────────────────────────────────────────────────────────────┤
  │ Contract internal consistency      │ Pass                                                                                         │
  ├────────────────────────────────────┼──────────────────────────────────────────────────────────────────────────────────────────────┤
  │ Contract repository consistency    │ Pass                                                                                         │
  ├────────────────────────────────────┼──────────────────────────────────────────────────────────────────────────────────────────────┤
  │ Construction readiness             │ Pass                                                                                         │
  └────────────────────────────────────┴──────────────────────────────────────────────────────────────────────────────────────────────┘

  ---
  Strengths

  1. The Contract-Freeze classification is genuinely evidence-driven, not roadmap-driven. docs/CHUNK_CONTRACT.md §20 records this exact sprint as
  backlog, in the exact lifecycle terms Phase 2 adopts. Verified verbatim.
  2. Minimalism is disciplined, not lazy. Five candidate fields are individually evaluated and deferred with distinct rationales (§8.6). No optional
  tier — matching the Knowledge Manifest (four required, zero optional) and Chunk (six required, zero optional) precedents exactly.
  3. It closes a real, previously-unowned assumption. docs/CHUNK_CONTRACT.md §11 assumed Document.id == knowledge_manifest.json documents[].id
  without freezing it; sample_rag/chunker.py:50-58 duck-types the same assumption independently. §8.4 promotes it to a contract term in a single
  authoritative location. This is the document's highest-value contribution.
  4. Correct citation of an error other documents propagated. docs/CHUNK_CONTRACT.md §1/§11 attribute Chunker.chunk(doc: Document) to
  architecture.md §7; it is actually §5. DOCUMENT_CONTRACT.md cites §5 correctly and separately notes §7 contains only the four Protocol classes.
  Verified.
  5. The corpus-scale finding is accurate and honestly bounded. knowledge_manifest.json has exactly one entry (3f3797c1134c);
  sample_rag/documents/jobs/ is empty. Verified directly.
  6. Phase 6/7 non-execution is correctly reasoned, and Phase 10 correctly identifies that this contract unblocks CHUNK_VALIDATION_PLAN.md §P1.4's
  partially-checkable invariant 3 and §P5's deferred referential integrity. Both citations verified verbatim.

  ---
  Findings

  F1 — MATERIAL: The "unowned text-extraction responsibility" conclusion is not supported, and contradicts the document's own cited evidence

  Where: Phase 3 (row 8), Phase 9 (Loader row), Phase 10 ("Loader ownership"), Phase 11 Outstanding Question 2.

  Claim under review: "The responsibility of turning a raw source file into Document.text is real … but is not currently owned by any named, frozen
  architectural component" (Phase 3), and OQ2's disposition: "recorded as a genuine gap … likely immediately preceding Document Construction, since
  Construction cannot proceed without it."

  Repository evidence contradicting it:

  ┌──────────────────────────────────────────────────────┬───────────────────────────────────┬─────────────────────────────────────────────────┐
  │                       Evidence                       │             Location              │               What it establishes               │
  ├──────────────────────────────────────────────────────┼───────────────────────────────────┼─────────────────────────────────────────────────┤
  │ Knowledge Source · Dependencies: JobOps SQLite       │                                   │ The raw file is a declared dependency of        │
  │ (read-only), **resume file** · Interface:            │ docs/architecture.md:103          │ Knowledge Source, and List[Document] is its     │
  │ KnowledgeSource.load() -> List[Document]             │                                   │ declared output. No component sits between      │
  │                                                      │                                   │ them.                                           │
  ├──────────────────────────────────────────────────────┼───────────────────────────────────┼─────────────────────────────────────────────────┤
  │ Knowledge stage · Inputs: Resume, job descriptions,  │ docs/architecture.md:88           │ The file→document-set transformation is inside  │
  │ JobOps SQLite → Outputs: Validated document set      │                                   │ the Knowledge stage.                            │
  ├──────────────────────────────────────────────────────┼───────────────────────────────────┼─────────────────────────────────────────────────┤
  │ Knowledge · Responsible Component (per               │                                   │ The stage that performs the transformation has  │
  │ architecture.md): Knowledge Source                   │ docs/altm.md:149                  │ exactly one named owner. This row is quoted in  │
  │                                                      │                                   │ Phase 1 of the document under review.           │
  ├──────────────────────────────────────────────────────┼───────────────────────────────────┼─────────────────────────────────────────────────┤
  │ "Knowledge ingestion operates on the canonical .docx │ docs/architecture.md:288 (§10,    │ .docx ingestion is an already-locked            │
  │  corpus. PDF remains an external export artifact…"   │ locked Architectural Decisions)   │ architectural decision assigned to the          │
  │                                                      │                                   │ Knowledge stage.                                │
  ├──────────────────────────────────────────────────────┼───────────────────────────────────┼─────────────────────────────────────────────────┤
  │ "The Knowledge Source owns the Knowledge Manifest";  │ docs/architecture.md:114;         │ Knowledge-Source-owned code already opens       │
  │ scripts/build_manifest.py opens and hashes every     │ scripts/build_manifest.py         │ corpus files today.                             │
  │ catalogued file (compute_sha256, lines 65–71)        │                                   │                                                 │
  └──────────────────────────────────────────────────────┴───────────────────────────────────┴─────────────────────────────────────────────────┘

  Assessment. The literal premise ("no component named Loader appears in §5") is true. The conclusion drawn from it does not follow. Component-level
  ownership is assigned; what is undecided is internal decomposition and extraction mechanism — the same class of decision
  docs/CHUNK_BUILDER_IMPLEMENTATION_PLAN.md §2.1 resolved for Chunker (file location, module shape, algorithm) inside a construction-planning
  sprint, with evidence and without an ADR.

  Introducing a "Loader" component would mean adding a row to the locked architecture.md §5 table — precisely what docs/adr/ADR-0001 refused to do
  for an analogous question, citing "Do not introduce new first-class architectural concepts unless justified by repository evidence." No such
  justification exists here; the repository evidence points the other way.

  Required correction: Phase 3 row 8, the Phase 9 Loader row, Phase 10's "Loader ownership" bullet, and OQ2 must be restated as: text extraction is
  owned by Knowledge Source per architecture.md §5/§10 and altm.md line 149; the extraction mechanism and internal decomposition are Document
  Construction Planning decisions. The contract schema (§8.2, §8.7) is unaffected.

  ---
  F2 — MATERIAL, UNRECORDED: §8.4's identity invariant creates a module-boundary consequence no phase records

  Document.id must equal knowledge_manifest.json documents[].id, which is produced by generate_document_id(source) = sha256(normalized_path)[:12] in
  scripts/build_manifest.py:74-76. A Document producer in sample_rag/ therefore has exactly three options:

  1. read the persisted knowledge_manifest.json and take its id values;
  2. import generate_document_id from scripts/ — crossing the boundary architecture.md §6 states explicitly (scripts/ = "Operational scripts … not
  pipeline logic");
  3. re-derive the id independently — reintroducing exactly the drift risk §8.4 exists to eliminate.

  This is not hypothetical tension: docs/CHUNK_VALIDATION_PLAN.md §P5.3 already declined an analogous cross-script dependency, calling it "new
  coupling that this sprint's evidence does not yet require introducing."

  Classification: planning work, not architectural work. The contract correctly stays silent on mechanism (all three options satisfy it). But the
  consequence is unrecorded in Phases 9, 10, and 11, so a Construction Planning sprint would rediscover it. Required correction: record it as a
  Phase 10 forward dependency and an explicit Construction Planning agenda item.

  ---
  F3 — MATERIAL, UNRECORDED: the dependency constraint governing text extraction is absent from the evidence base

  Phase 1 records that requirements.txt declares no .docx-parsing library. It does not record the governing constraint:

  - docs/roadmap.md §6 (locked): "Minimal dependencies. Milestone 1A is Python stdlib + pytest only. Dependencies are added only when a milestone
  specifically requires them."
  - docs/MILESTONE_1A.md "Libraries (stdlib-only)" table.
  - docs/roadmap.md §7: excluded items require "a deliberate scope decision recorded in this document."
  - docs/CHUNK_BUILDER_IMPLEMENTATION_PLAN.md §1.4 already treats this as binding: "Add a new external dependency without a recorded scope decision"
  is a prohibited action.

  Classification: planning/governance work with an existing, named resolution path (a recorded scope decision in docs/roadmap.md), not an
  architectural boundary question. Per this review's scope I express no view on any specific library or extraction approach. Required correction:
  record the constraint and its resolution path in Phase 10.

  ---
  F4 — MINOR (accuracy): Outstanding Question 4's stated premise is factually stale

  OQ4 justifies itself with: "that classification was itself a recommendation, not a frozen glossary entry (docs/CHUNK_CONTRACT.md §3)."

  Commit 994f7b1 ("docs: synchronize repository with frozen Chunk Contract") added to docs/glossary.md:117:

  ▎ Persistent Canonical Artifact / Runtime Artifact — Two artifact lifecycles distinguished by lifetime… | CHUNK_CONTRACT.md

  It is a canonical glossary entry. OQ4's disposition (defer; depends on the open Serialization question) remains correct, but its stated reason
  must be replaced.

  ---
  F5 — MINOR (accuracy): Phase 10 asserts the Chunk Contract §18 sync edits are unperformed; they were performed

  Phase 10 states the §18 cross-reference edits "remain a deliberate, separate, not-yet-performed action." Commit 994f7b1 performed edits 2, 3 and
  4: docs/MILESTONE_1A.md:114, docs/architecture.md:116, and docs/glossary.md:99,117. (docs/CHUNK_CONTRACT.md's own closing paragraph is the stale
  source; the document under review inherited it rather than checking repository state.) This has a practical consequence: a comparable
  synchronization pass will be expected after this contract is frozen, which Phase 10 does not anticipate.

  ---
  F6 — MINOR (accuracy): "build_manifest.py … never opens or parses file content"

  compute_sha256 (scripts/build_manifest.py:65-71) opens every catalogued file in binary mode and reads it. The substantive claim — no
  text-extraction capability exists anywhere in the repository — is correct and independently verified. Only the first clause is wrong (inherited
  from CHUNK_BUILDER_IMPLEMENTATION_PLAN.md §2). No conclusion depends on it.

  ---
  F7 — MINOR (under-evidenced, conclusion correct): OQ3's disposition has stronger support than it cites

  OQ3 defers "is JobOps data ever a Document?" as a textual ambiguity. Stronger, implemented evidence already settles it for this contract:
  scripts/build_manifest.py discovers only files under DOCUMENTS_ROOT with SUPPORTED_EXTENSIONS = {".docx", ".md", ".txt"}, so a JobOps SQLite row
  cannot obtain a documents[] entry — and §8.4 requires every Document.id to equal one. The proposed contract therefore already excludes
  JobOps-as-Document structurally, not merely by prose scoping. Recommend citing this.

  ---
  F8 — MINOR: invariant 3's determinism is mechanism-relative and not independently checkable

  §8.7 invariant 3 ("identical source content, extracted by an identical mechanism, produces identical text") is algorithm-relative — the same form
  as Chunk invariant 8, so it is precedent-consistent. But two consequences go unstated: (a) it is not checkable from any single artifact, exactly
  as CHUNK_VALIDATION_PLAN.md §P1.4/§P8 concluded for Chunk invariant 8; and (b) documents[].hash covers source file bytes, so no existing check
  detects extracted-text drift caused by a mechanism change. Recording these keeps a future Document Validation sprint from rediscovering them. Not
  a defect in the invariant.

  ---
  Repository State Check (independent of the document)

  sample_rag/chunks.json does not exist, though scripts/build_chunks.py implements serialization and validation (commits 240363e, a41cc4c) and
  sample_rag/chunker.py implements construction. The Chunk lifecycle is complete through Validation but has never executed against the real corpus,
  because nothing can turn Karthik_SR_Resume_v2_2.docx into a Document.

  This is material to the governance question: the Document gap is now the repository's live critical path, and every downstream artifact is waiting
  on it. It argues for proceeding to Document Construction Planning, not for inserting another architectural sprint ahead of it.

  ---
  Phase-by-Phase Verification

  ┌───────────────────┬───────────┬─────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
  │       Phase       │ Verified? │                                                    Notes                                                    │
  ├───────────────────┼───────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ 0 — Architecture  │ ✅        │ All four evidence points verified verbatim. Document is architecturally established; Contract Freeze is the │
  │ verification      │           │  correct path; Architecture Investigation correctly not performed.                                          │
  ├───────────────────┼───────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ 1 — Evidence      │           │ 14 of 15 rows verified accurate. One imprecision (F6). Two constraints omitted (F2, F3).                    │
  │ discovery         │ ⚠️        │ docs/CHUNK_SERIALIZATION_PLAN.md and scripts/build_chunks.py are absent from the evidence base despite both │
  │                   │           │  recording the same Document forward dependency.                                                            │
  ├───────────────────┼───────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ 2 — Precedent     │ ✅        │ "Adapt" is correct. Manifest-entry-vs-runtime-Document distinction verified against CHUNK_CONTRACT.md §2.   │
  │ review            │           │                                                                                                             │
  ├───────────────────┼───────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ 3 — Evidence      │ ⚠️        │ Rows 1–7 verified. Row 8 (Loader) is an unsupported inference — F1.                                         │
  │ classification    │           │                                                                                                             │
  ├───────────────────┼───────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ 4 — Sprint shape  │ ✅        │ Contract Freeze correctly determined.                                                                       │
  ├───────────────────┼───────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ 5 — Problem       │ ✅        │ All six problems verified against cited sources, including CHUNK_VALIDATION_PLAN.md §P1.4 and §P5.          │
  │ statement         │           │                                                                                                             │
  ├───────────────────┼───────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ 6–7 —             │           │                                                                                                             │
  │ Alternatives /    │ ✅        │ Correctly not executed, with reasoning stated.                                                              │
  │ rationale         │           │                                                                                                             │
  ├───────────────────┼───────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │                   │           │ Schema, identity rules, parent relationships, deferrals, and all three invariants verified as               │
  │ 8 — Repository    │ ✅        │ evidence-backed and internally consistent. The id-derivation description matches generate_document_id       │
  │ decision          │           │ exactly. The "must equal manifest id" term coexisting with deferred referential integrity mirrors           │
  │                   │           │ CHUNK_CONTRACT.md §11 — precedent-consistent, not contradictory.                                            │
  ├───────────────────┼───────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ 9 — Boundaries    │ ⚠️        │ Six of seven rows verified, no responsibility double-assigned. The Loader row is incorrect (F1); correcting │
  │                   │           │  it makes the table complete rather than merely unambiguous.                                                │
  ├───────────────────┼───────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ 10 — Forward      │ ⚠️        │ Four "enabled" items verified. One stale claim (F5); two omissions (F2, F3).                                │
  │ dependencies      │           │                                                                                                             │
  ├───────────────────┼───────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ 11 — Outstanding  │ ⚠️        │ See classification table below. OQ2 misclassified; OQ4's premise stale.                                     │
  │ questions         │           │                                                                                                             │
  └───────────────────┴───────────┴─────────────────────────────────────────────────────────────────────────────────────────────────────────────┘

  ---
  Phase 5 Deliverable — Classification of Every Outstanding Question

  #: 1
  Question: Promote source/document_type to required once real JDs exist?
  Classification: Planning work, evidence-gated — ordinary contract revision under the existing lifecycle. Mirrors CHUNK_CONTRACT.md §15's
  heading/section deferral exactly.
  Evidence basis: sample_rag/documents/jobs/ empty; chunker.py branches on text structure only, never on a type field.
  ADR required?: No
  ────────────────────────────────────────
  #: 2
  Question: Who owns text extraction — a new "Loader," or KnowledgeSource?
  Classification: Not a genuine architectural ambiguity. Ownership is already assigned to Knowledge Source; the open part is mechanism and internal
  decomposition = construction-planning work.
  Evidence basis: architecture.md:103 (dependency: resume file), :88, :288 (locked ingestion decision); altm.md:149 (Responsible Component:
  Knowledge
  Source); ADR-0001 precedent against new architectural concepts.
  ADR required?: No — reclassify per F1
  ────────────────────────────────────────
  #: 3
  Question: Is JobOps SQLite data ever a Document?
  Classification: Documentation/scope clarification. Already structurally settled for this contract by the implemented manifest builder;
  architecture.md §5's prose is broader than any implemented path.
  Evidence basis: build_manifest.py DOCUMENTS_ROOT/SUPPORTED_EXTENSIONS; §8.4's manifest-id binding; MILESTONE_1A.md build item 4 (SQL path bypasses

  Document).
  ADR required?: No — a docs/architecture.md prose clarification, not a decision change (§13)
  ────────────────────────────────────────
  #: 4
  Question: Classify Document as Persistent Canonical vs. Runtime Artifact?
  Classification: Intentionally deferred planning work, resolvable at Document Serialization Planning. Premise stale (F4) but disposition correct.
  Evidence basis: glossary.md:117 (term now canonical); ADR-0001 resolved Chunk's analogous container question inside Serialization Planning.
  ADR required?: No

  No Outstanding Question survives as an architectural responsibility or boundary question requiring a dedicated ADR.

  ---
  Phase 6 Deliverable — Construction Readiness

  The contract is sufficiently complete for Document Construction Planning. That sprint has a concrete target shape (§8.2), a resolved identity
  scheme (§8.4), a determinism requirement (§8.3), and a defined relationship to both the Manifest and Chunk (§8.5) — structurally equivalent to the
  input CHUNK_BUILDER_IMPLEMENTATION_PLAN.md had from CHUNK_CONTRACT.md. Its agenda must additionally include F2 (identity-derivation coupling) and
  F3 (dependency scope decision), plus the ordinary decisions of module location and extraction mechanism.

  ---
  Recommended Review Outcome

  OUTCOME A — APPROVED

  Recommended next sprint: Document Construction Planning. No ADR required.

  The proposed Document Contract (§8.7) is approved as written — no field, type, invariant, deferral, or identity rule requires revision.

  Eight corrections are required to the document's analysis sections before it is frozen: F1, F2, F3 (material) and F4–F8 (accuracy/completeness).
  None touches the schema or invariants.

  Why not Outcome B. B requires repository evidence confirming an unresolved architectural question. The only candidate — OQ2 — fails on the
  evidence (F1): ownership is assigned by three independent locked documents, and the residue is mechanism, which ADR-0001 and
  CHUNK_BUILDER_IMPLEMENTATION_PLAN.md §2.1 both establish is resolved inside a planning sprint. Chartering an ADR here would create the "Loader"
  concept the evidence does not support, against ADR-0001's own stated bar.

  Why not Outcome C. C requires both an unsupported conclusion and revisions to the proposed contract. F1 satisfies the first; the second is not met
  — the contract needs no revision. Blocking Construction Planning to correct a passage that overstates a blocker would delay work on a mistaken
  basis. The corrections are recorded as binding conditions of approval instead.

  ---
  Answer to the Governance Question

  ▎ "Is one or more additional architectural decisions required before Document Construction Planning can begin?"

  NO

  Proceed directly to Document Construction Planning, carrying forward corrections F1–F8 and the two agenda items F2 and F3.

  The determination rests on repository evidence, not the roadmap: architecture.md §5's Knowledge Source row (interface and dependency), §10's
  locked .docx-ingestion decision, altm.md line 149's Responsible Component column, and ADR-0001's established bar for introducing new architectural
  concepts.

  ---
  Optional Future Work

  Beyond this review's scope. Not review findings; not conditions of approval.

  1. Post-freeze repository synchronization pass for Document, mirroring commit 994f7b1 — a Document Contract glossary entry, and pointers from
  architecture.md §5's Knowledge Source row and MILESTONE_1A.md. Anticipating it in a Phase-18-style Repository Impact section would match
  CHUNK_CONTRACT.md's structure.
  2. docs/architecture.md §5 prose clarification so the Knowledge Source responsibility line stops implying JobOps SQLite data flows through
  Document, given MILESTONE_1A.md build item 4's direct SQL path (relates to OQ3).
  3. Extraction-output integrity: documents[].hash covers source bytes only. If extracted text ever gains an independent freshness concern, that is
  a Knowledge-stage validation question for a future Data Quality Validation sprint (relates to F8).
  4. docs/CHUNK_CONTRACT.md's closing paragraph is itself stale regarding its §18 edits (the source of F5); worth correcting when that document is
  next touched
