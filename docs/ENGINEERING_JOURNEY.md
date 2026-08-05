# ENGINEERING_JOURNEY.md

**Purpose:** preserve the *reasoning* behind this project's shape — the pivots, the mistakes caught, the deliberate trade-offs — that don't show up in code diffs or test counts but are the actual demonstrated skill. Sprint reports record what changed; this document records why, in narrative form, for a reader (or an interviewer) who wasn't there.

---

## 1. The governance-spiral catch (P3.1.7–P3.1.8.5, then the correction)

Five consecutive sprints went into hardening the Data Quality Validation layer — mutation evidence, register closures, documentation corrections — with **zero new pipeline capability added**. The work was good engineering. It was not, at that point, serving the project's actual purpose.

The catch was explicit and self-initiated: *"the project is there to assist me to explain why a particular metric has this reading for AI evaluation — not to build a perfect RAG — and I do not want to waste more time achieving perfection."*

This produced a standing principle applied ever since: **"is this good engineering?" and "does this serve the project's actual purpose?" are different questions, and the second overrides the first.** The Golden Dataset was built next, directly as a result of this correction.

## 2. The second catch: an ADR sprint that would have re-derived an already-reached conclusion

Before the `document_id` schema extension (P3.3.5), a nine-work-package "Architecture Decision Review" sprint was proposed — Context, Problem, Evidence, Options, Consequences, the full format. It was rejected: three separately-committed sprint reports (P3.3.3, P3.3.4, and the original P3.3.1 finding) had *already, independently* stated the same missing signal. The decision itself had already been reached, in about three paragraphs of conversation. Running a formal review to conclude what was already concluded would have been governance theater, not decision-making.

**Lesson applied since:** a decision that has only one real option doesn't need an ADR-weight process. Reserve heavy decision frameworks for decisions with genuine competing options — use a short, explicit decision memo otherwise.

## 3. The Fortune 500 correction — catching an error in your own artifact, including an uncomfortable one

While reviewing a generated Golden Dataset fact, a factual problem surfaced: the resume claimed "Fortune 500 data migration programs" for three companies (Maruti Suzuki, Betts Group, Red Earth) — none of which are Fortune 500. The company that *is* Fortune 500 (HP, the current employer) went unlabeled.

This wasn't a dataset-construction defect — the dataset had faithfully extracted what the resume said. The defect was upstream, in the resume itself. The fix: correct the resume (v2.2 → v2.3), then propagate the correction through the dataset.

**Why this matters as a demonstrated skill, not just a fix:** it's a live example of the exact failure mode the project's own metrics documentation describes — a system can be 100% faithful to a source that is itself wrong, and Faithfulness/Groundedness metrics can never catch that, because they only check consistency with the source, never whether the source is accurate. Catching your own resume's overclaim, in the middle of building a project about catching AI overclaims, is the kind of detail that makes the methodology credible rather than performed.

## 4. Why resume v2.2 was kept in the corpus (not deleted after the v2.3 correction)

The natural instinct after fixing v2.2's wording would be to discard it. Instead, it was deliberately retained — specifically because the Golden Dataset's failure taxonomy had two categories (**Stale Version**, **Contradiction**) that structurally require two disagreeing versions of the same source to exist. Without v2.2, those two categories would have stayed permanently unpopulated.

This decision paid dividends repeatedly, in ways not originally anticipated:
- It gave the cross-dataset validation suite (P3.4.1) real, non-vacuous checks — a "wrong version cited" defect is something this corpus can actually produce and catch, not just a hypothetical the tests assert against nothing.
- It became the root cause and testbed for the entire `ALTM-RETRIEVE-1` diagnosis-and-fix arc (see `MILESTONE_1A_CAPABILITY_INVENTORY.md` §3).
- It created a real tension, resolved explicitly at closure (P3.7.5, Finding F-1): a full fix for the v2.2/v2.3 duplication problem (excluding v2.2 from retrieval entirely) would have broken the two questions that need v2.2 reachable. The shipped fix — a tie-break preference, not full exclusion — was correct precisely *because* of this earlier decision. The two decisions, made turns apart, turned out to constrain each other in a way that produced the right answer.

**The general lesson:** a "keep it for now, it might be useful later" decision is worth making deliberately and revisiting explicitly, rather than either discarding prematurely or letting it linger unused. Three separate times this project caught itself with v2.2 sitting in the corpus *unused* despite being retained "for a reason" — and each time, closed the gap by either using it for its stated purpose or explicitly re-deciding.

## 5. The governance chain that caught its own incompleteness (P3.7.1 → P3.7.6)

Manual review (P3.7.1) concluded the pipeline worked and all ten build items existed. Governance synchronization (P3.7.2), run immediately after, cross-referenced those ten items against `MILESTONE_1A.md`'s actual, stricter Definition of Done for the first time — and found four items that were already true facts, scattered across four different committed documents, that nobody had ever assembled side-by-side against the document that defines "done." The Index Layer had no owning sprint. JobOps integration had never been tested. These weren't new discoveries; they were old facts nobody had connected.

This forced a real decision, escalated correctly rather than resolved by an agent: implement the gaps now, or formally re-scope them. The resolution (P3.7.3, the Repository Owner Constitutional Decision) established Milestone 1B specifically to hold the deterministic-but-deferred work, with the reasoning stated in full — including the sharp argument that Milestone 2's own governing rule ("every Milestone 2 component replaces an implementation behind an existing contract") is currently unsatisfiable, because the contract it would replace doesn't exist yet.

**Why this sequence matters more than any individual fix:** it demonstrates the project finding a real gap in its own claim of completeness, refusing to paper over it, and closing the loop with reasoning instead of assertion — closing Milestone 1A via an *annotated* Definition of Done rather than a falsely satisfied one. The closing report says this plainly: *"a closure claiming satisfaction would be the first false statement in the governance record."*

## 6. Working with an AI agent — the actual pattern that emerged

Every implementation sprint in this project followed the same rhythm: a prompt reviewed for scope, unauthorized architecture, or undefined terms *before* it ran; explicit approval required at each contract-freeze point; and an agent instructed to **stop and report rather than guess** when a governing document didn't define something it needed. This happened repeatedly and productively — "Top-k Success Rate" had no defined meaning anywhere, and the agent stopped rather than inventing one. That pattern (STOP-and-report as a designed behavior, not a failure) is arguably the project's clearest demonstration of what disciplined human-AI collaboration on quality-critical work actually looks like — treating the agent's output the same way the project treats a retrieved chunk: never trusted by default, always checked against a source of truth.
