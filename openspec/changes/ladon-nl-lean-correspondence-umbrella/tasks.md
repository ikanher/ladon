# Tasks

## Current state

Packages A/B (M1) and C/D are accepted; see [M1 acceptance](evidence/M1-ACCEPTANCE.md)
and [CD qualification](evidence/CD-QUALIFICATION.md). Package E is complete as a
bounded evaluation, with [source-first findings](evidence/E-PILOT.md): all 16 first
responses and separate corrections are preserved, original checks replayed, and
source-qualified scoring gives three justified faults and four correct controls
per arm. Detection and cost benefit are unmet; no historical target-paper
issue detection is established. Source/CLI factoring and user-approved frozen-test
quality changes are integrated. Package F is accepted: independent integration
review is complete, its database and native-CLI findings are repaired, and the
final default strict gate passed 3,415 tests with zero skips. Strict OpenSpec
validation and source/historical identity checks passed. All 27 tasks are
complete; supported-fragment limits and the unmet pilot benefit remain explicit
in [the integration report](evidence/INTEGRATION.md). No full-paper rerun or archive
has been performed.
[work-packages.md](work-packages.md) owns stage gates and
[design.md](design.md) owns technical decisions. Each package below executes in
this change unless explicitly split into a child; any such split must replace
the relevant detailed tasks with child/evidence links rather than duplicate them.

## 1. Establish an actual local proof application (package A)

Owner: [Lean proof slices](specs/ladon-lean-proof-slices/spec.md).

- [x] 1.1 Freeze relevant dirty source identities, minimal known-case evidence, input/toolchain provenance, and exclusions; verify historical reports and unrelated work remain unchanged in a baseline manifest.
- [x] 1.2 Freeze the public command, structured-fragment, result-dimension, and resource contract for M1; independently challenge it and observe meaningful red tests for unavailable application extraction and missing correspondence checking.
- [x] 1.3 Run the bounded feasibility check on tactic-style and term-style portable proofs plus one named real application; verify exact instantiated arguments/context and local replay, or preserve the concrete failure and revise the route before dependent expansion.
- [x] 1.4 Document the supported extraction profile and measured bounds with actual helper receipts; verify the documented local-checkout invocation reproduces the feasibility result.

## 2. Check one complete prose-to-Lean correspondence (package B / M1)

Owners: [interpretations](specs/ladon-prose-claim-interpretations/spec.md),
[correspondence checks](specs/ladon-proof-correspondence-checks/spec.md), and
the [M1 acceptance gate](work-packages.md#m1-the-first-complete-correspondence).

- [x] 2.1 Implement the minimal scoped interpretation and closed native payload producers/validators; verify faithful renaming, quantifier order, stale source, unsupported expressions, unknown fields, and exact references through the ordinary CLI.
- [x] 2.2 Implement the selected local application slice using package A's observed route; verify actual implicit arguments, local values, source attribution, ordered premise occurrences, and explicit unexpanded providers.
- [x] 2.3 Implement scope-preserving interpretation lowering, object-map elaboration, and original premise-supply/conclusion-transfer goals; verify structural-versus-Lean quantifier mismatches, invented hypotheses, self-dependencies, and silent goal changes with positive and adversarial real Lean checks.
- [x] 2.4 Connect bounded supplied terms to source-goal capture/completion and native attempts/check-runs; verify a faithful control closes by independent replay and a false portable interpretation is refuted by its own checked evidence.
- [x] 2.5 Exercise the same public path on the selected real passage/application; save supported links and all remaining physical/object/quantifier obligations, with independent interpretation review and no stronger finding than the receipts establish.
- [x] 2.6 Publish an executable M1 usage example and acceptance report; verify every M1 condition before starting generalized extraction, search, or additional checker families.

## 3. Preserve scope and premise providers across a local argument (package C)

Owners: [Lean proof slices](specs/ladon-lean-proof-slices/spec.md) and
[correspondence checks](specs/ladon-proof-correspondence-checks/spec.md).

- [x] 3.1 Extend slices to a bounded multi-step example with local have-proofs, witnesses, and branches; verify all AND premises and reject escaped witnesses, unavailable later facts, and swapped instantiations.
- [x] 3.2 Add scoped ambiguity and constant/witness dependency comparisons; verify pointwise versus uniform obligations remain distinct while valid alpha-renaming and checked representation transport remain accepted.
- [x] 3.3 Implement separate conditional, premise-provider, parent-support, fidelity, and method outcomes; verify a false predecessor does not refute a valid downstream conditional and a valid alternate proof does not certify the described method.
- [x] 3.4 Exercise depth/node/expression/process bounds and unsupported source forms; verify explicit residual frontiers, no lossy complete results, and no stale acceptance after context changes.
- [x] 3.5 Document the supported multi-step fragment and qualify one real multi-step slice; verify guide examples and keep general analytic arguments outside available replay labeled as attributed evidence.

## 4. Complete the ordinary review without duplicate transcription (package D)

Owner: [review workflow](specs/ladon-correspondence-review-workflow/spec.md).

- [x] 4.1 Integrate opt-in investigation v3 authoring, native inspection/projection, and shared immutable references; verify one authored record reaches checking, challenge export, and queue inspection without retyping its contract.
- [x] 4.2 Integrate sanitized independent response ingestion and reconciliation; verify original first responses survive corrections, changed contexts require actual new review, and reviewer assignments can be replayed without exposing prior assessments.
- [x] 4.3 Integrate discrepancy priority and independent mathematical/formal completion dimensions; verify absent counterparts, budget exhaustion, unsupported interpretation, and unexamined source remain visible without invented evidence.
- [x] 4.4 Reproduce the recorded declaration-compaction and option-routing failures with minimized current inputs; fix demonstrated consuming-path defects or preserve a precise non-reproduction, with tests retaining malformed-container rejection and honest help behavior.
- [x] 4.5 Verify v1/v2 compatibility, old artifact identities, bounded native query/projection, explicit unsupported-kind behavior, and operation without Quux; update CLI guides and packaged skill and execute their examples from the local checkout.

## 5. Measure detection on fresh passages (package E)

Owner: [predeclared comparative evaluation](specs/ladon-correspondence-review-workflow/spec.md#requirement-predeclared-comparative-evaluation);
protocol: [work-packages.md](work-packages.md#e-bounded-evaluation-protocol).

- [x] 5.1 Independently prepare and freeze the eight-case actual-Lean population, separate justified key, source-selection inputs, budgets, case/arm order, and scoring; verify no development answer or selected fault leaks into auditor inputs.
- [x] 5.2 Run fresh assisted and ordinary-tool contexts with matched resource and reviewer policies; preserve every first response, command, source identity, timing, omission, and exposure before revealing the key.
- [x] 5.3 Replay claimed checks and refutations, adjudicate source fidelity and disputed references, and normalize case verdicts; verify aggregate counts equal the scored rows and preserve corrections separately from frozen first results.
- [x] 5.4 Publish paired case-level findings, controls, abstentions, cost, and an explicit benefit or unmet-benefit decision; verify the report distinguishes constructed/real-source evidence, development/held-out cases, and procedural/enforced isolation.

## 6. Verify the integrated consuming result (package F)

- [x] 6.1 After the final production edit, run focused changed-module and parent CLI, source-goal, native-v3, derivation, investigation, and rendering consumers plus relevant quality/resource gates; preserve actual command receipts and ensure required Lean-backed gates are not silently skipped.
- [x] 6.2 Obtain an independent integrated audit of the final code, contracts, trust boundary, and evaluation claims; reconcile actionable findings and re-run affected gates after any fixes, preserving frozen acceptance tests.
- [x] 6.3 Run strict OpenSpec validation and final source/historical-evidence checks; record capability coverage, exact limitations, evaluation outcome, and reproducible local-checkout commands in the integration report before marking the umbrella implemented.

## Workflow follow-up

- A further full-paper rerun is a separate decision informed by package E, not an automatic completion step.
- Package release, archive, and manuscript modification are outside this implementation checklist.
