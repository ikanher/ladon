# Design

## Context

See [proposal.md](proposal.md) for motivation and [the audit contract](specs/ladon-proof-correspondence-audit/spec.md) for observable behavior. This design resolves the interpretation and execution boundaries before the first audit.

The existing result layer already stores revision-bound claims, target identities, assessments and guide reviews. `src/ladon/result_assessments.py` validates and detaches supplied assessments; it does not discover discrepancies. `docs/RESULT_EXPOSITION.md` explicitly describes attributed judgments, exact formal types and `mathematicalVerdict: not-inferred`. `docs/SOURCE_GOAL_COMPLETION.md` provides optional checking against a captured original goal with separate replay and trust results. Ordinary files and native Lean remain supported.

The existing `proofir-attachment-and-link-observations` capability owns artifact association rather than mathematical correspondence. The previous umbrella's claim-correspondence and guide contracts already distinguish link resolution, interpretation and proof strategy. This new capability owns the consuming audit workflow and its deliverables, without duplicating those owners or changing their authority.

### Source basis

- Alexander Bastounis, Fabian Circelli and Anders C. Hansen, *Navier–Stokes lost in translation: Why Lean verification of AI autoformalisation does not guarantee correct natural language proofs*, [arXiv:2610.08144v1](https://arxiv.org/abs/2610.08144v1), submitted 2026-10-06; publication metadata checked 2026-10-08.
- Supplied [TeX source](../../../paper/natural-language-proofs/NavierStokes_LostInTranslation_ArXiv.tex), SHA-256 `67b27489185bf10baa92192a47ca25d51ecd4ed320b51374b5571a9cba13c084`. This digest identifies the supplied bytes, not an independently established byte-for-byte match to arXiv's source archive.
- Stable TeX labels: `ex:example1` (wrong polynomial argument), `ex:example2` (alternative matrix argument), `ex:example3` and `sec:why` (existence/default-value issue), `ex:Navier_strong` (derivative estimate), `ex:Navier_weak` (pressure-flux comparison).
- The paper cites `openai/NavierStokesAndEuler` commit `f9e8bc5b38b6e212696e8a30e3e91517af887bbd`. Its Navier–Stokes findings are reported claims to investigate, not findings already independently reproduced by Ladon.
- [AGMAI source mapping](../ladon-result-understanding-and-release-umbrella/sources.md) supplies the broader motivation of conventional exposition and honest informal/formal correlation. The new paper supplies failure cases, not an endorsement of Ladon.

The paper's universal-translator limitation assumes termination with a faithful translation or a determination that translation is impossible, including resolution of arbitrary presuppositions. This investigation instead permits partial results, attributed interpretations and explicit unresolved obligations. It does not attempt to prove or refute the paper's entire complexity argument.

## Goals / Non-Goals

**Goals:** make particular disputed steps inspectable; produce substantive local mathematical evidence where feasible; show what an author would need to revise; identify any concrete software handoff problem separately from the mathematics.

**Non-Goals:** universal semantic equivalence, automatic proof-strategy certification, a general premise extractor, a complete Navier–Stokes audit, a new search engine, an LLM-uptake comparison, a new evidence schema or release platform, or renewal of unrelated qualification. No edits or builds in the concurrent matrix-factorization project are prerequisites.

## Decisions

### 1. Three work packages with explicit exits

These are work packages inside this umbrella, not pre-created implementation children. Create a separate runtime child through OpenSpec only when an observed defect warrants an implementation proposal.

| Package | Inputs and consuming result | Exit |
| --- | --- | --- |
| A — elementary reproductions | Published polynomial, least-element and matrix examples, with author-created faithful controls | Replayable local evidence or precise unavailable result for each, with interpretations and reconstruction changes disclosed |
| B — audit and correction recipe | A's sources and local obligations, existing ordinary-tool and optional Ladon operations | Readable findings, proposed corrections, faithful-control results, and a concrete account of handoff costs/errors |
| C — one published passage | The cited derivative-loss comparison and its exact source context | One justified comparison/correction proposal or exact unresolved relationship, followed by a bounded review handoff |

A and B can inform each other, but preserve the first attempts before changing the recipe. C starts after the elementary boundary checks are characterized. Package C defaults to `ex:Navier_strong`: compare Lemma 8.6 / equation (8.19) with `norm_derivativeWord_inverse_le` in `NavierStokes/SmoothFamilyTorusInverse.lean` at the cited commit. Select the necessary definitions and assumptions as part of that one comparison. Pressure flux is background, not a second automatic task. An unavailable source is recorded rather than silently replaced by a more convenient example.

### 2. Preserve the argument being audited before attempting repair

Each case has immutable original prose and formal source references, a short question, explicit local obligations, actual commands/results and a reader-facing finding. Markdown/TeX and Lean are the primary artifacts. Use existing JSON companions when they serve a concrete consumer; do not require canonical target capture merely to write an audit or imply resolution from a fabricated target identity.

The polynomial case checks the asserted factorization itself, for example by evaluating at an explicit witness, and separately checks a correct derivation of the final inequality. The least-element case checks the defining predicate's nonemptiness independently of the later ring identity, including the concrete polynomial whose root exists for every proposed index. The matrix case inspects both methods and preserves a valid alternative as such. Faithful variants are explicitly authored controls, not additional reported failures of the paper's models.

A report names the exact formal interpretation chosen for each local obligation. Evidence for that proposition is not promoted into a machine verdict on the original sentence. Proof-method findings cite the relevant source argument; a dependency list or generated back-translation alone does not settle the question.

### 3. Use existing checking and retain operational limits

Prepare a small isolated Lean/Mathlib fixture with recorded toolchain and dependency revisions. The current portable integration fixture uses Lean 4.32.1 without Mathlib; do not expand its dependency footprint by default. Prefer a compatible prepared environment whose provenance can be inspected; record any port of the published snippets as a reconstruction.

Use ordinary `lake env lean` and named audit declarations, retaining `#print axioms` observations under the existing standard-no-placeholders policy. Existing Ladon source capture/completion is optional when binding an application to its original goal actually helps. Freeze the selected candidate before describing its behavior. Reuse existing process supervision/recording facilities rather than building another recorder; preserve failures, outputs, interventions and measured resource use. Keep the accepted 32 GiB cap and report the precise enforcement mechanism rather than conflating address-space limits with process-tree RSS.

The initial preparation budget is 60 minutes; each elementary case has 30 minutes of active proof/audit work after setup, and the published-passage investigation has 120 minutes after sources are available. These are initial task bounds, not benchmark targets or proof-impossibility criteria. Record elapsed time, pause points and any explicitly justified extension before continuing. If setup exceeds its budget, retain the missing dependency and continue source inspection where meaningful; do not launch a full external-project build as an unbounded prerequisite.

### 4. Record findings using existing semantics

Use prose findings with the existing assessment `basis`, `scope`, `differences` and evidence references where applicable. Descriptions such as repaired argument, changed estimate, missing presupposition and alternative valid method are audit vocabulary, not proposed new API enums. Map only what the supplied evidence supports; unresolved, historical and conventional material retains its actual status.

Maintain original and revised paragraphs separately. The responsible author's adoption decision is outside automated checking. A concrete unadopted proposal is a valid handoff; no author contact, public posting or manufactured human approval is needed to complete the investigation. Any adopted document later gets a new revision and its own scoped assessment.

### 5. Test semantic boundaries without claiming benchmark results

The published examples already reveal their issues. Their reproductions and corrected controls are development cases, not held-out measures of detection accuracy. An LLM-assisted run, if used, retains its supplied context and interventions; do not conceal knowledge of the paper or claim independent rediscovery.

The immediate checks ask whether findings correctly distinguish the local error, the final theorem and alternative methods, and whether faithful controls avoid false alarms. Do not introduce a matched reader-cohort study or optimize prompts until tool use appears. Mathematical value, operational utility and comparative software advantage remain separate conclusions.

### 6. Conditional implementation and stopping rule

At the end of B, record either a concrete observed handoff defect with source evidence and a proposed consuming fix, or that existing tools suffice. A serious single failure can justify a targeted child; no arbitrary repetition count is required. A child must preserve this contract, reuse existing checking owners, and qualify only affected surfaces. It is not automatically a prerequisite for C or closure; a manual workaround may be sufficient.

Stop after A–C and one assessment of the actual findings, local proofs/counterexamples or residuals, revised prose and interventions. Use the same-pro delta route if external review is requested. Stop earlier for a material semantic/API decision that cannot be resolved within the agreed scope. Negative or unresolved findings may finish the bounded investigation while leaving its mathematical question open. Do not mark that as achieving general fidelity detection or the old umbrella's benefit gate.

## Risks / Trade-offs

- Known published answers can make a run look like independent detection → disclose development status and distinguish reproducing a claim from obtaining new checking evidence.
- A different formal statement may still imply the prose claim through an unexamined bridge → inspect the particular implication and report the missing relation; do not infer falsity from syntax or a failed application.
- Comparing derivative estimates may require substantial PDE context → start with the pinned local statements, definitions, derivative variables and constant dependence; apply the 120-minute bound and preserve the unresolved implication if the context cannot be closed.
- Model-authored interpretations can repeat the original translation mistake → retain exact local propositions, source anchors and attribution, with faithful controls and independent source scrutiny in the review handoff.
- Mathlib or external build setup can dominate the task → use the isolated preparation budget, record prerequisites, keep ordinary source inspection usable, and avoid making the main test suite depend on a research checkout.
- Reusing sidecars may add effort without helping an auditor → record that result and retain the plain-file recipe; no runtime expansion follows automatically.

## Migration Plan

This planning change creates no runtime migration. Add reproducible audit material and documentation through the tasks. Existing commands and formats remain supported. Preserve the older umbrella and its acceptance records unchanged; this new work does not make its deferred tasks complete. A later runtime child, if justified, owns its own deployment, compatibility and rollback plan.
