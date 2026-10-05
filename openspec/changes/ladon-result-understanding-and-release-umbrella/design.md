## Context

Ladon already separates lexical discovery, explicit Lean checks, stored ProofIR observations, theorem lineage, and optional capsule replay. Its result projections preserve bounds and evidence references. These answer questions about declarations and operations, but do not yet give one paper result an explicit correspondence record, reading guide, research history, and portable handoff.

The motivating source is [Responsible Release of AI-Generated Mathematics](https://agmai.org/general-sep29/) (2026-09-29). `sources.md` maps its recommendations to the six capability specs and separates those recommendations from Ladon's design choices. The stakeholders are mathematicians reviewing or reusing results, LLM agents searching and interpreting Lean projects, and maintainers preparing attributable artifacts.

The existing `ladon-authority-safe-verified-discovery-umbrella` freezes optional expansion until its authority-safe gate and discovery slice exit. Independent artifact-only validation can proceed experimentally following the implementation request; canonical evidence integration and full exits retain those prerequisite receipts. Source scaffolding and checked task counts do not satisfy them.

## Goals / Non-Goals

**Goals:**

- Make AI-assisted results understandable, checkable, attributable and reusable
  by mathematical readers, with model-independent access to explanations and
  checking materials. Engineering status cannot certify understanding.

- Connect one exact informal claim revision to one or more exact formal declarations and explain unresolved correspondence.
- Make additional assumptions, incomplete formalization, stale observations, and missing reviews easy to discover.
- Help humans and LLMs navigate definitions and reusable lemmas with separately reviewed explanations and citation assertions.
- Preserve disclosed research-process evidence, including unsuccessful attempts and unknown population coverage.
- Produce portable, locally inspectable bundles without depending on a hosted model or Ladon service.
- Collect reproducible qualitative feedback from LLMs attempting claim-comprehension and lemma-reuse tasks; defer comparative metrics.

**Non-Goals:**

- Automatically proving natural-language/formal equivalence, novelty, priority, human understanding, or responsible-release compliance.
- A proof-quality score, a replacement Lean checker, another declaration extractor, or a new ProofIR artifact family.
- Generating papers, running autonomous literature searches, capturing undisclosed model internals, or operating a model service.
- Publishing to scholarly repositories, minting persistent scholarly identifiers, contacting reviewers, or allocating funding.
- Replacing the primary proof-discovery workflow or bypassing existing authority/readiness gates.

## Decisions

### 1. One versioned result manifest references existing evidence

Introduce `ladon-result-manifest-v1` as a document-level envelope outside native ProofIR. It references immutable canonical ProofIR artifacts and existing theorem/capsule evidence. It is not an alternative checker receipt. A result has a stable logical `resultId`, an immutable content revision digest, optional predecessor revision, title, claim inventory with coverage, and separately bounded attachment collections.

A claim includes a stable ID within the result, exact supplied statement text, document locator, document/content digest, and declared language/format. Formal targets include qualified declaration name, project revision/source digest, toolchain/environment identity, and an artifact-qualified subject reference when available. A name alone cannot resolve a checked attachment. One claim can link to several declarations; shared lemmas can support several claims. Partial component mappings remain explicit and do not establish that a composite informal claim is covered.

Unknown identities remain unresolved. Search similarity produces candidate links only. Canonical artifacts remain the source of authority, and a disposable SQLite projection can accelerate manifest lookup using existing publication rules.

Alternative considered: put paper text and scholarly review into new ProofIR families. Rejected because it expands the semantic core unnecessarily and risks mixing scholarly assertions with checker authority.

### 2. Correspondence review is independently attributable

Links use an independent resolution axis (`resolved`, `ambiguous`, `unresolved`, `stale`) and correspondence-review axis (`not-reviewed`, `reviewed-aligned`, `reviewed-with-differences`, `disputed`). Review records name the reviewer, reviewer kind (`human`, `model`, `tool`), exact subject revisions, method, timestamp, rationale, and any supported machine comparison. A model review never becomes a human attestation. Reviewer identity is attributed metadata unless separately authenticated; the manifest does not certify it.

Differences can describe assumptions, domains, quantifiers, conclusions, or scope with text/source anchors and evidence basis. Syntactic differences do not prove semantic inequivalence. A formal comparison operation records precisely the relation it checked and its checker observation; it cannot establish arbitrary natural-language faithfulness. Conflicting reviews are retained. A new claim or declaration revision makes old reviews historical and inapplicable until re-reviewed.

Alternative considered: infer correspondence from a matching theorem name or successful compilation. Rejected because either can conceal a stronger hypothesis or a weaker conclusion.

### 3. Dossiers preserve independent evidence dimensions

Build dossiers by joining the manifest to existing exact theorem queries and lineage. Keep source observation, checker operation/outcome, environment/freshness, correspondence reviews, exposition reviews, citations, and collection coverage separate. Formalization coverage records mapped, unmapped, and unresolved claim components plus inventoried obligations; no universal `verified` field is introduced.

Assumptions retain their origin: theorem hypotheses, observed axiom dependencies, declared external mathematical assumptions, placeholders, and unresolved external frontiers. Standard logical axioms are not automatically classified as formalization defects. Imported declarations are not automatically assumed or unproved; report the available checking/trust evidence. Lexical `sorry` observations remain lexical, while an observed `sorryAx` dependency carries its own authority. Unobserved transitive dependencies remain unknown.

Warm dossier inspection is read-only and never refreshes an index, starts Lean, downloads a paper, or invokes a model. Explicit existing checker/replay commands can supply new observations. A zero-residual candidate application, a full theorem replay, and a repository build remain different operation kinds.

Alternative considered: a single readiness score. Rejected because checking, correspondence, and comprehension can vary independently.

### 4. Reading guides are annotations over structural evidence

A guide records ordered reading steps with claim/declaration/source references, purpose, explanations, prerequisites, and author/review metadata. Structural dependency paths come from current lineage/derivation owners; explanatory sequencing is a separate authored assertion. Missing semantic proof structure is not reconstructed from lexical edges. Generated explanations can be imported, but core inspection does not call an LLM.

Citation attachments distinguish bibliographic identity, cited passage/result locator, asserted relationship (`background`, `uses-result`, `related-method`, `attribution-claim`), submitter, and review status. A persistent identifier or URL locates a work; it does not verify that the cited work supports the assertion. Multiple/disputed attributions remain visible. No novelty or historical-priority verdict is inferred.

Alternative considered: automatically narrate a declaration DAG as the proof. Rejected because dependency paths omit mathematical argument and can create misleading explanations.

### 5. Research history uses explicit disclosure and population coverage

Import user-supplied process records with stable problem and attempt IDs, model/provider/version as reported, input/output references and digests, prompts or disclosure status, concise supplied process summaries, tool events, outcome basis, elapsed time, and cost amount/currency/estimation method. Initial output and edited exposition are distinct artifacts. A process summary is an authored explanation, never evidence of unobserved internal reasoning.

The result-to-problem relation explains how AI was used. Problems and attempts are counted separately; repeated trials on one problem cannot inflate the number of problems attempted. Coverage is `complete`, `partial`, or `unknown` relative to a named capture boundary. Success/failure/timeout/abandonment/unassessed outcomes remain separate. Comparability of difficulty is an attributed selection rationale, not an automatic equivalence judgment. Rates require an explicit denominator and coverage; incomplete logs cannot support a global success rate.

Disclosure statuses include supplied, redacted, unavailable, and not-collected. Export requires an explicit attachment allowlist, retains omission reasons, and does not embed undisclosed prompt content or reversible content-derived identifiers for redacted secrets. Core operation does not demand proprietary or inaccessible material.

Alternative considered: synthesize missing provenance from final artifacts. Rejected because successful outputs cannot reveal failed attempts, original prompts, or actual compute expenditure.

### 6. A thin CLI and bounded projections serve both audiences

The proposed additive command family is `ladon result validate|inspect|guide|export|verify`. It consumes an explicit manifest/bundle path; `inspect` and `guide` select a result revision and optional claim. `export --output PATH` prepares a local bundle. `verify` checks bundle integrity only and reports that scope; Lean replay remains a separately requested existing workflow. Implement command contracts through the existing entrypoint and execution/result conventions.

Default LLM output places statement, assumptions, unresolved obligations, checking scope, and review gaps first, with exact drill-down references. JSON and human-readable projections preserve identical evidence meaning. Proposed hard limits for v1 are 16 MiB manifest input, 1,000 claims, 10,000 links/annotations/process rows per collection, 32 KiB compact output, 100 rows per page, and 64 KiB per explanatory text item. Oversized input is rejected before projection; output truncation reports omissions and continuation bound to manifest revision and query. Full export has a configurable finite byte ceiling (default 256 MiB) independent of display limits.

Alternative considered: add a hosted interface or daemon immediately. Rejected because ordinary installed CLI use and portable artifacts suffice for the alpha and are easier to measure.

### 7. Release packages preserve history and verify narrowly

A bundle contains the manifest, selected claims/guides, locally available and explicitly selected evidence attachments, a relative-path inventory of byte sizes and content hashes, a revision/predecessor record, disclosure omissions, and optional existing capsules. Missing external dependencies are declared. Portable inspection is required; fully offline replay is claimed only when separately demonstrated. Content digests identify bytes, not publisher authenticity or scholarly acceptance.

Export is deterministic for identical inputs/options and uses atomic publication. Reject absolute/traversing member paths, symlink escapes, collisions, and size-limit violations before publication or extraction. Reference resolution during inspection never dereferences network URLs implicitly. Preparing a bundle does not submit it anywhere or invent a DOI. Later supplied repository identifiers can be recorded in a new manifest revision.

Community profiles are optional, versioned adapters with pinned upstream specifications and explicit check coverage. `formalization.yaml`, copyright headers, and comparator challenge files originate in the source recommendation, but their formats and comparator semantics must be pinned from their own upstream authorities before an adapter claims support. Presence/schema checks, comparator execution, and interpretation of comparator results remain separate. Unsupported profiles report unavailable; a bundle can still be inspected. There is no universal responsible-release certification.

Alternative considered: copy all evidence and dependencies automatically and label the result reproducible. Rejected because disclosure, redistribution permission, omitted packages, and execution environment all matter.

### 8. Six child contracts deliver a staged alpha

The dependency ledger defines implementation work packages, not already-created or completed child changes. Its external prerequisites name the authority-safe gate and verified-discovery exits under their owning umbrella. Receipt checks must refer to compatible candidate and evidence-contract identities.

1. Claim correspondence establishes the result manifest and exact revision links.
2. Formalization dossiers consume that manifest and canonical theorem evidence.
3. Reading guides add source-linked explanations and citation assertions.
4. Release bundles first implement a core profile over those three children.
5. Qualitative usage feedback exercises the core dossier/guide/bundle slice; reproducible development scenarios precede use.
6. Research provenance and optional community profiles complete the full release-oriented scope. Their exit is required for umbrella completion, but not for the first core alpha evaluation.

The bundle and evaluation children have explicit core/full milestones to avoid making optional research logs a dependency of the first comprehension experiment. `startAfter` references child core exits where specified; `completionDependsOn` records the later full integration. No cyclic prerequisite is introduced.

### 9. Qualitative usage feedback comes first

The October 4 external starter review sharpens the first alpha into one ordinary
read/find/check loop. Freeze a task fixture before the reader attempt: reuse the
fixed-epoch exposition, canonical manifest, authored guide and full product
bundle; explicitly include the existing revision-bound assessment companion
that the guide references, or disclose its absence. Preserve the original r48
bundle and measurements. The fixture also carries a separately labeled synthetic
stale-review variant and the finite-map extra-assumption example; neither is
represented as a real approval of the exposition.

Two fresh reader contexts receive identical exposition, guide, claim map,
assessment records, canonical evidence and Lean sources. One uses Ladon's
ordinary installed CLI and one uses ordinary file inspection and pinned Lean
tooling. This is a descriptive qualitative comparison, not a benchmark. Readers
receive a task and exact new goal/ordered local context, but no evaluator answer
key or preselected lemma name. Both a valid application and a nearby context
missing a prerequisite must be attempted explicitly. An unresolved obligation or
rejected application is not evidence that the goal is false.

Retain the original attempts before presentation/performance changes. Record
commands, outputs, errors, workarounds, interventions, candidate/environment
identities and existing resource telemetry. Offline inspection remains separate
from explicit Lean execution. Repair confirmed obstacles in a bounded work
package, qualify changed candidates separately, and retest in fresh contexts.
Initial repair candidates are component-scope presentation, a reliable transfer
from an inspected target to a new-goal check, and redundant dossier preparation
within a bundled request. Persistent sessions and automatic cache subsetting are
not prerequisites. A maintained producer selection operation is conditional on
observed preparation difficulty or disclosure risk.

Success requires correct mathematical scope and evidence distinctions, an exact
new-goal result, ordinary operation without unrecorded rescue, and a concrete
navigation/decision/error-avoidance contribution from Ladon. If the same guide
and standard tools achieve the useful outcome while Ladon adds only latency and
metadata work, stop expanding this layer and redirect to core search/check.
Environment, discovery or candidate-check failures take priority over new release
features. Return for review with original attempt, repair, repeated attempt and
comparison; do not wait for umbrella completion. Process-provenance and community
profiles remain deferred until this decision. The original and future task
populations remain development data.

The [completed r49 experiment](baselines/read-find-check-r49/REPORT.md) triggers
that stopping rule. Three core repairs enabled compiled reuse, but the fresh
Ladon reader's scope audit remained incomplete and the same-guide plain reader
reached the same application decision. Do not treat completed experiment tasks
as usefulness acceptance. Preserve this infrastructure and prioritize the next
review around ordinary discovery/checking handoff and cost; provenance, profiles
and further result-layer expansion stay deferred. The task used a reader-selected
named candidate, so automatic discovery/ranking benefit is still unestablished.

On 2026-10-02 the user deferred metrics in favor of LLM usage feedback. The current alpha uses small development scenarios with exact inputs and recorded commands/output. Reports identify the task, friction, misleading or missing output, workaround, suggested improvement, and reproduction status. Source or explicit Lean checks validate suspected correctness issues. No model call, telemetry, or external upload is implicit.

Feedback is diagnostic evidence, not an independent measurement of benefit or human understanding. Contract tests remain required. Paired baselines, held-out corpora, human-cohort comparisons, confidence intervals, and promotion thresholds are retained as future work and do not block current usage feedback or downstream implementation. Any later measured-benefit claim must define and freeze that protocol before evaluation.

### 10. Returned r03 review focuses application and exposition workflows

The user supplied the second pro recommendation in the conversation on
2026-10-04, after the standalone [r03 packet](../../../temp/ladon-starter-pro-onboarding-review-data-r03/REVIEW_PROMPT.md).
This section owns its implementation interpretation. The reviewer did not rerun
Lean or qualification; their stated 88% confidence is an opinion, not measured
benefit or an authenticated attestation. r49's compiled reuse, r50's precise
partial application and r53's incomplete reader pair support a product hypothesis,
not comparative usefulness. The historical reports and r03 packet remain unchanged.

The next milestone is: given a manuscript component and a real Lean goal, produce
a checked application or exact contextual obligation, then revise one paragraph
faithfully to that outcome. Proof development asks what can be used and what
remains; exposition review asks what the paragraph can claim. They share existing
goal, premise, source and checking owners, with distinct views rather than one
larger report. The [existing application change](../ladon-goal-capture-and-application-probes/design.md)
owns source capture, contextual residuals and explicit replay completion. Existing
premise-routing work remains advisory and is not a prerequisite for direct use.

First repair compact residual text and component scope. `result_inspection_cards`
currently places the whole claim statement in every component card. Preserve
whole-claim context but identify the selected component, attached target scope,
and uncovered sibling conclusions beside it. No component text is inferred from
a label; absent authored scope remains unavailable, and any supplied explanation
retains attribution. Selected-declaration premise extraction starts from the
authoritative elaborated type, separately from lineage/axiom inventories. New
authored scope metadata must use the existing revision-bound companion or an
explicitly versioned schema, not silent changes to strict v1.

Exposition review consumes exact component/declaration/application references.
Compare assumptions, quantifier domains, inequalities, modeled objects and
uncovered conclusions. A selected inference becomes a local obligation using
the application workflow. A checked translation proves a relation between formal
statements; fidelity of their rendering of prose remains an attributed judgment.
An alternative derivation does not establish the actual formal proof's strategy.
Use existing revision/review bindings to identify paragraphs needing recheck;
a changed hash is not evidence that the mathematics became false. Conventional
argument, unchecked translation, unresolved correspondence and demonstrated
mismatch remain distinct. No universal claim language or automatic proof narration
is required, and offline reading views retain their nonexecuting contract.

Evaluate two short tasks before combining them. The application task discovers
a lemma without its name, completes the valid source-bound case and diagnoses
the nearby residual. The exposition task compares a correct short passage and a
clearly labeled synthetic altered passage that drops an assumption or broadens
scope. Require absence of false alarms on the control; inability to check an
alteration does not prove it false. The external recorder captures operations
without assigning wrappers, command accounting or experiment administration to
the reader. Preflight and freeze the intended reader configuration and competent
baseline Lean operation, then supply identical guide/evidence materials. Do not
attribute r53 omissions to reasoning level or infer general model suitability.

Continue only for a concrete mathematical contribution such as a preserved
premise, avoided wrong application, less goal reconstruction, or supported
paragraph correction. If same-guide native tooling supplies the same application
outcome without a useful Ladon contribution, narrow the standalone search/check
surface and prioritize correspondence/exposition. If exposition only repeats the
guide, keep it optional. After development-fixture success, test a structurally
different small project with an implicit finiteness premise and lemma chain.
Packaging, duplicate preparation, new backend integration and profiles are not
prerequisites. Existing Lean interaction facilities can be assessed against the
capture/replay contract; this recommendation does not authorize a backend rewrite.

### 11. Returned r04 review requires mathematical work

The user returned the r04 recommendation and supplement on 2026-10-05. The
source ZIP is `temp/ladon-r04-review-and-supplement.zip`; its proposed experiment
is not a performed reader study or authorization for outside contact. The review
largely accepts the declared application engineering scope and asks for a useful
application and improved paragraph rather than another infrastructure layer.
Its confidence is an opinion; it did not rerun Lean or product qualification.

Keep checking/capture/replay/trust owners frozen. Repair only two presentation
issues before testing: text must separate implementation-detail locals from
usable premises and preserve local-definition values; focused exposition pages
must prioritize short selected prose, relevant review rationales and named
uncovered components before repeated signatures/metadata. Preserve the 32KiB
page limit, full-input validation, exact omission references and historical
suppression. Deduplicate before clipping; shortened types must be labelled
excerpts with an ordinary complete-statement route. This does not require a new
premise extractor or presentation framework.

Use separate fresh application and exposition tasks with competent ordinary
Lean tools in both arms, plus Ladon in the augmented arm. Supply the same
legitimate guide and mathematics. Preserve declared search population and setup
costs; a known-owner index is not unassisted discovery. Neutral derivative
passages carry no case-specific review verdict, correction or receipt citation
that reveals the evaluator answer. Original r61 engineering controls remain
immutable and are not promoted into independent detection.

The application must preserve its original source goal. Accept a different
successful proof in the incomplete case; otherwise retain the exact residual
of the attempted application, without claiming impossibility. The exposition
must retain correct prose when warranted, correct formal-coverage overstatement
without declaring conventional mathematics false, and identify added hypotheses
as narrowing rather than completion of the old stronger claim. A checked
formal inference still does not certify prose fidelity or actual proof strategy.

Automatic recording belongs outside mathematical reader work. Preflight/freeze
candidate, tasks, model/tool configuration and baseline before sessions. Retain
first attempts; assisted continuations and any targeted repair/retest are
separately identified. No prompt/configuration search until a favorable outcome.
Return for review with actual proof/residual and original/revised paragraph plus
matched baseline/failure/intervention records. Expansion or narrowing follows a
concrete mathematical contribution; further standalone interaction, generic
parameter extraction or backend integration must earn their cost. Metrics,
human cohorts and release profiles remain deferred.

### 12. Returned r05 review narrows to an offset bridge

The returned review and supplement on 2026-10-05 accept the r62 mathematical
outcomes and qualified repairs but identify no contribution from the extra
command surface. Both arms consumed the same Ladon-associated curation as files;
this does not establish or refute artifact-maintenance benefit. Keep direct file
consumption legitimate. Freeze further standalone interaction, generic extractors,
search engines and release expansion; preserve existing checking owners.

The bounded next task resolves component-assessment-10 for `thm:smallbatch`,
`offset`: specialize the general calibrated-offset theorem to fixed positive
integer E. Freeze a formal target with exact calibrated noise, sqrt(2 log T),
quantile(-log(1-delta)/E), and the prose parameter conditions, with T=E+extra
covering admissible integer horizons. Eventual rate agreement must not substitute
for checked calibration-definition equality. An added calibration-equivalence
hypothesis is conditional progress, not completion. Preserve original targets,
proofs/residuals and historical assessment. Do not upgrade `leading` or the whole
claim when offset succeeds. Formal proof and attributed prose fidelity stay separate.

Two fresh sessions receive identical ready sources/guide/evidence and competent
ordinary Lean; augmented additionally has existing qualified Ladon as an option.
Freeze 1800seconds per session and 32GiB tree RSS before attempts. Record outside
the task, with no completed bridge supplied, prompt hunting or forced uptake.
Known owners are legitimate for this correspondence task; no new index required.
Evaluate mathematical outcome and product contribution separately. If no concrete
handoff contribution occurs again, stop interface expansion and consolidate the
artifact/checking utilities; mathematical formalization can continue separately.
Return for review with the intended statement, actual proof/residual, paragraph,
offset coverage, matched baseline and all interventions. A new test-count gate is
not the purpose. The short current frontier in tasks.md owns resume state.

Repair the isolated compaction bug as bounded maintenance: a typed size overflow
can trigger lower compaction levels, while invalid input and omission-reference
errors propagate. Require a valid multi-target public-path regression; preserve
existing row/page allowances and input validation. No presentation redesign.

## Risks / Trade-offs

### Observed source association for the real exposition

The explicit `proof-search check source` operation will compare a frozen owner
source compilation with a selected stored canonical module. Offline resolution
and default candidate checking keep their existing behavior. Source capture
uses the pinned compiler, controlled compiled imports, a supervised process and
scratch output; it does not run Lake or write build artifacts into the target.

Imported declaration ranges remain available after source edits and therefore
cannot establish source association. The real owner also embeds its logical
filename in compiled output. The selected route supplies frozen bytes through
stdin with the original filename, requires byte-identical whole-module output,
and reads exact declaration ranges from the same run's fresh `.ilean` v5 file.
The preliminary real-owner experiment reproduced its recorded `.olean` in
6.694 seconds at 7,179,735,040 bytes peak RSS under the authorized 32 GiB limit.

Candidate checking, discovery, and source capture use 32 GiB RSS defaults
following the user’s October 3 instruction. Keep measured process-tree peak RSS
and elapsed time in field reports and compare like-for-like captures; successful
execution below the cap does not establish acceptable resource consumption.

The remaining-target field run found a distinct compiled-input capacity limit:
the counterexample's imported primary files exceed the former 4 GiB aggregate
allowance while checker RSS remains about 8.56 GiB. Candidate checking and
source association share a 16 GiB streamed primary-input allowance, retaining
the 512 MiB per-file and 8 GiB auxiliary limits. Exact-boundary tests and the
retained failed attempt accompany installed retries. Report compiled bytes,
compiler RSS and elapsed time separately; this changes no canonical identities
or correspondence authority for existing inputs.

The initial profile supports legacy whole-module output and bounded setup
options/package metadata, with no setup plugins or dynamic libraries. It
rejects modular sidecar output, unsupported metadata, missing or changed
compiled inputs, source/setup changes, invalid source ranges, and failed or
bounded compilation. Stored source-map integrity and declared producer identity
do not authenticate arbitrary imported artifacts. The observation concerns the
selected source/module association; it does not promote checker, transitive
source freshness, correspondence or review claims.

### Real-project canonical environment capacity

The October 3 exposition capture reaches 10,517 imported modules at 8.109 GiB
checker RSS under the user's 32 GiB allowance. The current implementation slice
extends only the canonical environment compiled-module array to 32,768 entries;
other collections and the 8 MiB artifact / 32 MiB batch limits stay unchanged.
The root payload and native envelope hashing paths must agree across Python and
Rust, preserve existing IDs, reject duplicate module names, and round-trip
through the semantic registry and result resolver. No import truncation or
proof-note rewrite is part of the fix. Older readers may reject larger artifacts.

The root owns integration and real capture. The durable engineering board is
`.codex/state/ultra-result-evidence.sqlite3`, scoped to the result-evidence task.
Frozen regression tests and the exact real capture are the acceptance evidence;
this repair alone does not complete the dossier/guide/bundle milestone.

### Fixed-epoch baseline decisions

The completed [fixed-epoch baseline v1](baselines/fixed-epoch-v1/README.md)
is development evidence on frozen inputs. Its nine offline scenarios do not
complete the core dossier/guide/bundle exit. Keep that baseline immutable and
record later candidate deltas separately.

The next dossier must show the exact component and its attributed omission
reason, rather than only an aggregate unmapped count. Distinguish a declared
conventional-only component, an unassessed component, an unresolved target,
and an asserted implication without a checked adapter. These are independently
attributed assessments, not inferred absence of mathematics or proof. The
child design must version any manifest extension; do not silently add fields
to the current strict v1 schema or reinterpret existing `unmapped` counts.

Correspondence cards must expose strict versus closed hypotheses and the
released-observation scope (for example, transcript versus average alone).
Keep the article revision, pinned source archive and selected working-tree
target separate. A byte-identical source match supports source attribution,
not a fresh checker observation or natural-language equivalence.

Reading guides should begin with the conditional result, its counterexample
and the distinct sparse regimes. A dependency closure is supporting navigation,
not a substitute for that authored explanation. A missing canonical target must
remain unresolved even when the manifest itself validates successfully.

### Existing risks

- [Claims drift while links still look current] → bind every link/review to both revisions and preserve stale/historical records explicitly.
- [Complete-looking inventories omit claims or assumptions] → require declared inventory scope and separate population/extraction coverage; unknown totals stay unknown.
- [Generated explanations inherit checker credibility] → preserve author/reviewer kind, review scope, and canonical evidence axes in every projection.
- [Metadata overwhelms LLM context] → compact decision-oriented cards, hard limits, revision-bound pagination, and measured navigation cost.
- [Profiles or publication expectations change] → pin each profile's upstream contract and make unsupported versions unavailable without invalidating core inspection.
- [Provenance leaks private material] → explicit disclosure choices and export allowlists; no automatic collection or upload.
- [Roadmap duplicates unfinished owners] → reuse existing evidence, CLI, identity, lineage, capsule, and readiness owners and require prerequisite exits.

## Migration Plan

Add manifests and the command family without reinterpreting older reports or ProofIR. Keep bundles optional; existing search and evidence commands continue to work without a manifest. Build disposable lookup projections only explicitly and rebuild them on schema changes. Reject unsupported manifest/profile versions with migration diagnostics. Rollback removes the additive command/projection layer while preserving canonical evidence and exported manifests as immutable files. Release documentation must distinguish planned, implemented, contract-supported, and externally evaluated milestones.

## Open Questions

- When metrics resume, select independent reviewers and held-out repositories before freezing labels; model self-review cannot substitute for independent reviewers.
- Pin the authoritative comparator and `formalization.yaml` profile revisions during the optional-profile child; no format is guessed from the motivating document.
- When metrics resume, set task-family sample sizes and benefit thresholds before held-out runs. Qualitative feedback does not support external-benefit promotion.

## Application prerequisite qualified (r59/r60)

The application child is now 9/9 complete. [r59](../ladon-goal-capture-and-application-probes/evidence/application-completion-r59/REPORT.md) qualifies captured-original-goal completion, independent compiler replay and transitive trust on candidate `720d28439c4a3a1178163af3b116129cc7ed743e`. [r60](../ladon-goal-capture-and-application-probes/evidence/application-handoff-r60/REPORT.md) records the fixed-epoch complete/missing-premise handoff, its public selected-source indexing workaround and real limit controls on unchanged runtime owners. The capture binds 10,523 imported modules; actual operation RSS is approximately 8.4GiB, below the accepted 32GiB cap, with substantial repeated-operation latency.

The application evidence remains an engineering prerequisite, not task9.1
completion. The [current frontier](tasks.md#current-frontier--r09-editorial-correction-complete-cycle-closed)
and [r61 evidence](baselines/exposition-scope-r61/REPORT.md) own subsequent
component/paragraph implementation, qualification and unresolved reader gates.


## 13. Returned r06 review: durable handoff, then stop

Consolidate the already checked offset specialization through normal mathematical
maintenance. Prepare exact proposed source and prose, recheck adopted bytes,
retain historical version bindings, and reassess only the offset component.
Maintainer acceptance is a concrete human source/editorial decision. The
ordinary-tool recipe precedes optional existing source-bound completion. No
new runtime capability, canonical registration or reader comparison is required.

The unmet benefit gate stays deferred and cannot be closed by compilation or
adoption. Existing compatibility is maintained; further investment requires a
concrete independently arising user need. The current frontier owns acceptance
and any build blocker.

## 14. Request-scoped dossier reuse is bounded maintenance

The user resumes Ladon improvement after successful normal-project handoff checks,
without making mathematical adoption the next dependency. Remove measured
duplicate dossier preparation within each bundled view. Retain the complete
validated dossier in the private snapshot owned by the bundle context, reuse
validated check receipts through the existing checking owner, and project selected
targets without changing complete-input validation, byte output or cursor identity.
Public explicit-file entrypoints retain their validation and signatures.

No persistent cache/session, prepared-input public bypass, runtime dependency,
schema or command expansion is authorized by this maintenance slice. Full suite,
strict quality, installed-distribution smoke and independent source audit are
its engineering checks. One-shot request timings remain separate from usefulness.

### 14. Returned r08 review: explanation and correction before further software

The governing objective is shared mathematical understanding and reuse. The
r68 cost gate is accepted and that maintenance cycle is closed. Prior command
comparisons do not establish community benefit; their absence of uptake does
not refute the value of a faithful explanation. Retain historical experiment
and qualification scopes rather than converting them into understanding claims.

Start from an actual author/maintainer need and selected section. Draft a
companion, then obtain a competent reader's independently chosen question. The user selected fixed-epoch material and a focused offset companion is drafted;
its divergence question has a recorded response and proposed revision. The r09 review accepts the narrow editorial result; the refined companion adds a conventional short divergence argument and portable navigation. The cycle is closed as a reviewed proposal with adoption pending. A proposed
fixed-epoch theorem's adoption is not a dependency; do not choose a theorem merely
to elicit command use. Without a real need, maintain compatibility and wait.

For one section, use a conventional editable companion as the primary artifact:
purpose, exact conditions, key ideas, important inference steps and literature
attribution. Existing claim/guide/assessment/source/checking records provide
optional support, with conventional/unmapped/attributed/checked scopes explicit.
Reading and correction require no privileged model; document actual checking
prerequisites. No new schema, service, viewer or universal proof explanation is
needed. Preserve observed process information only where available/authorized;
label estimates and supplied summaries, never invent internal reasoning history.

Preserve the original passage, reader question, response, any checked obligation,
and adopted or unresolved revision. A responsible author decides adoption.
Added premises narrow a claim; failed application does not prove impossibility;
unformalized does not imply false; alternative derivation does not certify the
original strategy. A checked theorem does not certify its prose interpretation.

End after one substantive question-and-correction round. Mathematical value and
software value remain separate. The r09 review closes this round after bounded
editorial refinements. A further review needs a substantive new question, material
claim/support change or concrete actual-use failure; no third uptake experiment.
Automate only a concrete repeated handoff/error exposed in use. Otherwise keep
ordinary documents plus Lean and stop runtime expansion. Funding, equitable model
access and community governance remain institutional responsibilities.
