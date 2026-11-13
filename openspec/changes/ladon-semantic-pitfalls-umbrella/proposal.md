# Proposal

## Why

A checked prose-to-Lean implication can be vacuous, depend on the desired conclusion as a premise, or use a total operation without establishing the intended existence property. The supplied `temp/pitfalls.tex` identifies concrete gaps alongside safeguards Ladon already implements.

## Current development sequence

The [umbrella task ledger](tasks.md#current-program-state--2026-11-13) owns current progress and sequencing. The DP-SGD control audits, mathematical premise comparison, PLD source audit and S.1–S.3 source-consistency qualification are complete. They establish useful bounded checking and a real source-formula discrepancy; they do not establish a general detector. The sibling repository has completed the bounded source repair and impact review.

The separate [matched pilot](../ladon-matched-source-audit-pilot/evidence/run-20261113-r01/REPORT.md) is also complete. Its discovery gate was not met: both arms judged the same six selected claims faithful, with no discrepancies or serious false accusations. It used source-provided crosswalks and only text analysis in the Ladon arm, so native semantic checking and detection on a faulty claim remain untested.

The synthetic challenge preparation and five-unit paired comparison are complete. The assisted arm found one of the two faults; control found both. No added detection benefit was established. The original aggregate mislabels the assisted missed fault as a serious false accusation; [the current interpretation and correction boundary](design.md#decision-after-synthetic-comparison-r01) distinguish false reassurance from the registered false-accusation category without altering frozen evidence.

The completed bounded milestone is [N.3: explicit premise accounting](tasks.md#completed-bounded-milestone--explicit-premise-accounting). It reconciled the evaluation and qualified source-context application checks with consistent object maps, conclusion transfer and explanatory premise ledgers, using existing tools and exposed development cases. The delivered interface was reproduced by a fresh user; source-only interpretation behavior was not tested. An unmatched premise prevents treating that theorem as sufficient support for the passage; it is not automatically a refutation. Add a narrowly scoped operation only if this exercise demonstrates a missing capability. Broad diagnostics and a fresh comparison remain deferred.

The [seven-case N.3 report](evidence/checked-application-n3c-r01/REPORT.md) records completed faithful/derived/conditional routes, full stochastic counterexamples and a valid shifted-state ordinary Lean proof whose native completion was rejected at that historical checkpoint. The [later printer fix](evidence/c05-printer-fix-r01/REPORT.md) now completes that exact term with replay and trust acceptance. The current disposition is consolidation of verified guidance, with the diagnosed printer limit repaired in the [bounded follow-up](evidence/c05-printer-fix-r01/REPORT.md). No further comparison or broad integration follows automatically.

Matrix-factorization remains a read-only donor. Reuse the retained local capsule and preserve the original source, proof, evaluation reports and registrations. The features below remain deferred acceptance scope; the new development milestone neither implements nor accepts them.

## What Changes

- Coordinate four separately applicable children: [baselines](../ladon-pitfall-baselines/proposal.md), [assumption feasibility](../ladon-assumption-feasibility/proposal.md), [premise provenance](../ladon-premise-provenance/proposal.md), and [operation definedness](../ladon-operation-definedness/proposal.md).
- Retain the separate [PLD development child](../ladon-pld-core-source-audit/proposal.md) and [matched comparison child](../ladon-matched-source-audit-pilot/proposal.md) as bounded evidence, with source discovery, checker validation and comparative benefit distinguished. They change no production capability contract.
- Add opt-in source-bound audit stages and a readable report separating checked formal facts, attributed intent, unresolved obligations, and source coverage.
- Preserve conditional theorem validity; a suspicious assumption or total operation is not automatically an exposition error.
- Freeze the common policy and each child’s family baseline before its semantic runtime changes. Retain the full 24-case comparison for final acceptance, with supplied-interpretation checks separate from prose reading and fault discovery.
- Finish with bounded integration evidence and measured outcomes, including a negative result when improvement is not established.

Detailed acceptance is in [the capability specification](specs/ladon-semantic-pitfall-audit/spec.md). Success is evidence for the declared bounded behavior, with limitations visible to the caller.

## Capabilities

### New Capabilities

- `ladon-semantic-pitfall-audit`: Source-bound coordination and reporting of semantic-pitfall evidence.

### Modified Capabilities

None. Existing probe, identity, authority and coverage requirements remain in force; these additions do not reinterpret historical results.

## Impact

Existing correspondence, contract audit, source-goal completion, investigation reports, documentation, and bundled/shared Ladon skills. The user has authorized applying these bounded additions; current implementation progress is recorded in tasks.md and the linked baseline child. Full-paper reruns, a version bump and pushing are outside this change. Historical receipts and older evaluation gates remain unchanged.

