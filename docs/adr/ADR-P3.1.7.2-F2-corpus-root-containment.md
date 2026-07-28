# ADR-P3.1.7.2-F2 — Corpus-Root Containment Enforcement

**Repository:** `ai-quality-engineering`
**Status:** **ACCEPTED** — Option A (Construction). Approved by the repository owner at Sprint P3.1.7.2.
**Sprint:** P3.1.7.2 — Assurance Remediation
**Supersedes:** nothing. **Superseded by:** nothing.
**Related documents:** `docs/DOCUMENT_CONSTRUCTION_PLAN.md` (§4.1, §6.2, §10.1, §20.4), `docs/DOCUMENT_CONTRACT.md` (§8.5, §8.7), `docs/P3.1.7.1_Decision_Gate_Report_Evidence_Verification.md` (EV-3), `docs/P3.1.7_Independent_Implementation_Review_Codex.md` (P3.1.7-IMPL-01), `docs/P3.1.7_Independent_Implementation_Review_ClaudeCode.md` (A-2), `docs/ENGINEERING_TRACEABILITY_REGISTER.md`

---

## Decision question

Where should corpus-root containment for `knowledge_manifest.json` `documents[].source` be enforced — **Construction** (`KnowledgeSource.resolve_source_path`) or **Data Quality Validation** (Sprint P3.1.8)?

## Context

`docs/DOCUMENT_CONSTRUCTION_PLAN.md` §4.1 defines the corpus root as fixing *"which filesystem items are corpus items at all."* Until this decision, `resolve_source_path` enforced only one half of that gate — the extension check — while the root itself was unenforced.

This ADR exists because the question was genuinely disputed. Two independent reviews at Sprint P3.1.7 agreed the defect was real and reached **opposite** conclusions on where it belongs. Sprint P3.1.7.1 (Evidence Verification) confirmed the fact and explicitly declined to resolve the disposition, recording it as a Decision Gate item requiring human approval.

## Evidence summary

Independently reproduced at Sprint P3.1.7.1 (finding EV-3, **CONFIRMED**), against a hash-verified checkout of commit `5b903db`:

```
absolute path        : LOADED   text='CONTENT OUTSIDE THE CORPUS ROOT'   inside corpus root? False
relative '..' escape : LOADED   text='CONTENT OUTSIDE THE CORPUS ROOT'   inside corpus root? False
```

- **Locus:** `sample_rag/knowledge_source.py` — `path = SAMPLE_RAG_ROOT / Path(source)`. `pathlib` discards the left operand when the right is absolute, and `..` traverses out of the root. No containment check followed.
- **Bounded exposure:** `scripts/build_manifest.py` `normalize_source_path` emits only repository-relative POSIX paths beneath `DOCUMENTS_ROOT`. A *generated* manifest cannot express an escaping source; reaching the condition requires hand-editing a tracked, version-controlled file. Both reviews agreed on this bound.
- **Not a contract violation:** no `docs/DOCUMENT_CONTRACT.md` §8.7 invariant mentions containment. This is a gap between §4.1's *stated* boundary and what construction *enforced*.

## Options considered

### Option A — Construction

**For.**

1. **It is an intra-artifact check.** Containment is decidable from the configured corpus root plus the single manifest entry being processed. It requires no corpus-wide analysis. This is precisely the criterion `docs/DOCUMENT_CONTRACT.md` §8.5 uses to route **cross-artifact** concerns to Data Quality Validation — and containment is not one.
2. **Half of the same gate already lives here.** `resolve_source_path` enforces §4.1's extension half on the adjacent line. Splitting one stated boundary across two layers, with two different enforcement times, is the anomaly.
3. **The failure class is already defined here.** §10.1 classifies "unsupported extension" and "corpus item missing" as Input failures that must raise. Containment is the same class at the same stage.
4. **Prevention rather than detection.** Construction is the only layer on the runtime path. Data Quality Validation would detect the condition after the fact; `load()` would still have returned outside content to its caller.

**Against.** It modifies runtime code that Sprint P3.1.5 validated and Sprint P3.1.6 specified, and it enforces a constraint the frozen contract does not state.

### Option B — Data Quality Validation

**For.** The manifest is the artifact under suspicion, and A8/§8.5 route manifest-trust concerns to Data Quality Validation. Construction would stay frozen. Finding F-1 (duplicate identifiers) is already deferred to Sprint P3.1.8, and F-1 and F-2 are both "manifest content is untrustworthy" findings that could be handled coherently together. Exposure is bounded, which justifies deferral.

**Against.** Data Quality Validation detects but cannot prevent — `load()` would retain the behaviour until P3.1.8. Its own shape is also not yet settled: `docs/DOCUMENT_CONSTRUCTION_PLAN.md` §13.1 records precondition **V2** (the persistence question) as still open, making the receiving venue less defined than Construction.

### Option C — `scripts/build_manifest.py` `validate_manifest` (rejected)

Containment is decidable without filesystem I/O, so it would fit that function's stated design property. **Rejected on repository evidence:** `KnowledgeSource.load()` does not call it — `sample_rag/knowledge_source.py` imports nothing from `scripts/` — so it would not protect the runtime path at all. `docs/architecture.md` §6 additionally defines `scripts/` as *"not pipeline logic."*

## Decision

**Option A — Construction.** Approved by the repository owner.

**Accepted rationale, as recorded at approval:**

> Corpus-root containment is an intra-artifact construction invariant. The check depends only upon the configured corpus root and the manifest entry currently being processed. It requires no corpus-wide analysis and therefore belongs to Construction rather than Data Quality Validation.
>
> Data Quality Validation remains responsible for cross-artifact repository properties such as duplicate identifiers, uniqueness, completeness, and consistency.

## Implementation

`resolve_source_path` rejects an escaping `documents[].source` before resolving it, raising `DocumentConstructionError` as an Input failure under §10.1.

The check is deliberately made against the **manifest value**, not against resolved filesystem state:

```python
if relative.is_absolute() or ".." in relative.parts:
    raise DocumentConstructionError(...)
```

This choice follows directly from the accepted rationale — the check reads only the corpus root and the entry being processed. Two consequences were verified rather than assumed:

- It performs **no filesystem access**, so containment cannot depend on corpus state, and a rejection is reproducible from the manifest alone.
- It leaves every pre-existing failure mode untouched. A `documents[].source` containing an embedded NUL byte still surfaces through the existing "does not resolve to a file" path with `__cause__` of `None`; a `resolve()`-based check would have raised `ValueError` there and changed an already-approved failure specification.

## Consequences

**Accepted.**

- Construction gains one runtime check; `KnowledgeSource.load()` now refuses an escaping source rather than loading it.
- §4.1's stated corpus boundary is enforced where it is stated, in full rather than in half.
- Sprint P3.1.8 inherits **F-1 only**. F-2 is closed.
- Sequencing permitted AH-8 to be resolved in the same runtime touch, so Construction was opened exactly once.
- The Executable Specification Suite gains the AH-7 specifications, and runtime line coverage of `sample_rag/knowledge_source.py` reached 100%.

**Deliberately not done.**

- The frozen contract is **not** amended. No `docs/DOCUMENT_CONTRACT.md` field, type, invariant, or deferral changed. Containment is a construction-level enforcement of a plan-level boundary, not a new contract invariant.
- Symlink traversal is **not** resolved. A corpus file that is a symlink pointing outside the root is not detected, because the check reads the manifest value rather than filesystem state. This is a deliberate boundary of the accepted rationale, is recorded in `docs/ENGINEERING_TRACEABILITY_REGISTER.md` as an open observation, and is a candidate for Data Quality Validation should evidence for it ever emerge. No such evidence exists today.

**Revisit if.** A future corpus legitimately requires sources outside `sample_rag/` (for example a shared corpus root), or symlinked corpus items enter the repository. Either would be new evidence, not a reason to reopen this decision preemptively.

## Affected artifacts

| Artifact | Change |
|---|---|
| `sample_rag/knowledge_source.py` | Containment check added to `resolve_source_path` |
| `tests/test_knowledge_source_failures.py` | AH-7 specifications; module docstring updated — F-2 is now approved behaviour |
| `tests/conftest.py` | F-2 record updated from "deferred" to "resolved" |
| `docs/DOCUMENT_CONSTRUCTION_PLAN.md` | §20.4 records the decision |
| `docs/ENGINEERING_TRACEABILITY_REGISTER.md` | F-2 disposition recorded |
