# Design

## Context

See proposal.md. Historical audits mixed extraction limits, source interpretation, local checks and final reporting. Known-answer development replay remains useful regression evidence but cannot measure discovery. Existing benchmark and investigation workflows provide identity, clock and first-report preservation.

As of 2026-10-24, further runtime expansion is frozen under
[product scope](../../../docs/PRODUCT_SCOPE.md). The user-requested preparation
of one short local correspondence exercise uses existing tools and does not
admit a held-out C case, freeze an enhanced comparison arm or satisfy a promotion
gate. The protocol below remains unchanged for any future measured evaluation.

## Goals / Non-Goals

**Goals:** isolate which stage improves, test valid controls and qualify any discovery claim. **Non-Goals:** call planted cases real-paper discovery, retrofit old runs into a new baseline, or change the frozen retest-7 runtime identity.

## Decisions

### Three separately scored tracks

A: 24 supplied-contract cases: 12 supported-fragment mismatches, eight valid controls, four deliberately unsupported/truncated cases. Include composition, AND-premise preservation, incomparable routes, quantifier order, domain transport and countermodel lifting. Ground truth is backed by actual small Lean declarations or exact finite checkers. All 24 must receive the specified classification and required evidence; unknown cases must remain unknown. This measures analysis conditional on correct contracts.

B: 12 source-production cases: six exact correspondences, four contract discrepancies and two unsupported expressions. Inputs are original prose and actual Lean sources; contracts are not supplied. Score per-feature extraction, source fidelity, unsupported coverage and final comparisons separately. Supported formal features must be extracted rather than manually inserted under an extraction label. Promotion requires all ten supported cases correct after independently retained review and the two unsupported cases honestly limited; report first-pass errors separately.

C: 12 held-out unfamiliar source fragments with actual formal counterparts: six faults and six valid controls, drawn from source families absent from development. Auditors receive original fragments/formal sources without contract annotations, target locations, verdicts or answer-derived symbol maps. An independent custodian freezes the key and admission criteria before runtime freeze. No implementer or answer-informed root authors the supposedly blind judgments. If such separation is unavailable, label the exercise nonblind and do not satisfy this track.

### Comparison protocol

Freeze a current local-checkout baseline before code edits, including dirty runtime bytes and dependency/toolchain identities; a Git commit alone is insufficient. Freeze the enhanced runtime after functional gates. Both use checkout-backed launchers, equal original inputs, equivalent model/configuration and 90-minute wall-clock budgets per 12-case arm. No pip-installed Ladon. Use separate fresh contexts for baseline and enhanced arms; preserve ordering/randomization seed and every initial output. Code development and fixture compilation are separately accounted for. The comparison measures this bounded portfolio, not a universal causal effect.

Prepare protocol and hidden-case custody early. Execute A and B before C. All artifacts retain source hashes, runtime identity, extraction timings, peak memory, checker results, unresolved queue and review history. Memory caps use the shared 12 GiB default; exhaustion stops dependent progress and is reported, without increasing limits or resetting the clock.

### Decision rule and reporting

Report TP/FP/FN, justified controls, abstentions, extraction errors, coverage, time to first supported finding, number of checker attempts, wall time and RSS by track and arm. Denominators include timeouts and unsupported selections; never silently replace failed cases. Detection requires an exact source location, faithful interpreted discrepancy and independent evidence adjudication, not merely a label.

A bounded full-paper trial is justified only if A and B pass, C's enhanced arm confirms at least four of six faults, justifies at least five of six controls, has zero false accusations, and finds at least one additional confirmed fault over baseline within the same budget. These are an engineering promotion rule, not a statistical significance claim. Otherwise publish the negative/inconclusive result and retain the unmet detection-benefit gate; do not run another paper audit automatically.

### Integration and separation

The umbrella owns product report integration; this child owns harness, fixtures, custody and measured decisions. All findings use the same public CLI path available to auditors. Known target cases may appear only in a clearly labeled development regression partition. Existing retest directories remain immutable; any future handoff gets a fresh directory after runtime freeze and contains no answer clues.

## Risks / Trade-offs

- Synthetic performance overstates discovery → three tracks, distinct source families, direct reporting of source selection and interpretation failures.
- Shared filesystem weakens isolation → export minimal packets and record allowed roots/access incidents; label procedural isolation honestly.
- Small portfolio is noisy → report exact case-level evidence and paired differences, avoid general accuracy claims.
- Independent inputs cannot be obtained → stop C as blocked/nonblind; infrastructure can be complete while discovery remains unestablished.

## Migration Plan

Keep previous benchmark artifacts and first reports untouched. Add a new evaluation version and immutable runtime/corpus manifests. Freeze the baseline as the first implementation action before any contract runtime changes; finish by recording gate results and outstanding limitations, not by changing historical labels.

