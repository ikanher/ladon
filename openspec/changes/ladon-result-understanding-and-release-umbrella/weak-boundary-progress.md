# Weak receipt and audit boundaries — 2026-10-02

Compact population validation now rejects a present non-object receipt instead
of treating it as absent. This applies to failed/unassessed candidates,
unattributed scratch failures, and candidates omitted from display. Missing or
null receipts remain supported; their compact authority axes stay unknown.
Public completeness metadata cannot fill in a missing receipt's completeness.
Unattributed scratch failures also retain their scratch role in the population.

Valid weak receipts retain attempted toolchain selection and their failed,
non-checker scope without invented environment/check references. This selection
does not establish that the target check ran. Stored text reads now show the
finite historical execution-binding limitation. Raw audit JSON remains an
unchanged detached source copy without registry writes. Raw audit text labels
original observations whose execution binding is not revalidated in that view.

The 225 new contract cases cover seven weak statuses, both semantic operations,
both compact views, malformed scalar/list receipts, omitted rows, missing/null
receipts, three attempted-selection states, scratch role, absent completeness,
raw copy isolation, and text boundaries. After correcting initial fixture and
expectation errors, the pre-patch suite failed 177 cases with 48 controls passing.
The first patch passed 383 related tests and exposed one test fixture lacking
required exact checker references. Correcting that fixture passed 384 tests.
One test was decomposed to pass strict complexity directly. Failed intermediates
and repairs remain in [apply-run-state.json](apply-run-state.json).

Isolated snapshot `e0f3b04` passes 701 relevant installed tests on each of Python
3.11 and 3.12. The clean-candidate gate passes 2,342 maintained tests and 29
installed CLI contracts, strict quality, compilation/build, distribution/resource,
and collection parity. The required benchmark passes 17/17 cases with zero
correctness/stability failures and passing cache/process controls. Six ordinary
installed CLI probes exercise explicit/ambient preflight failures in llm, review,
and audit views; source and compact receipt identities agree, references remain
absent, and audit text shows its boundary.

Coverage inspected across the prerequisite slices includes these paths:

| Path | Receipt owner and boundary |
| --- | --- |
| Candidate, partial batch, scratch | Shared construction; exact subject/check owners for canonical evidence, failed/non-checker scope for weak receipts |
| Canonical observations and SQLite | Immutable original bytes; stored readers validate owners and independently recorded execution context |
| Semantic expansion and theorem dossier | Shared stored projection; missing historical binding weakens to none, dossier query itself is not-run |
| Lineage query, graph, summary | Stored/derived query receipt; no inferred theorem-check execution or completeness |
| Discovery cards and minimal output | Full population validated before selection; derived receipt, exact source/projected identities and finite weakening reason |
| Stored derivation CLI | Exact artifact/query-bound structural receipt; not-run theorem checking, independent structural completion |
| JSON and text | Shared dimension owner; compact receipt axes and exact identities preserved, finite binding limitation visible |
| Raw audit | Detached canonical source, separate from validated read projections; no registry write |

This inventory records inspected seams, not a complete propagation/monotonicity
exit. Native derivation APIs retain their structural contract. The remaining
audit must reconcile every supported path and its compatibility/transition
evidence, then establish compatible complete correctness, authority, integration,
and discovery exits. Counts remain result umbrella 9/50, claim child 5/8,
prerequisite umbrella 37/76. Canonical claim integration remains gated and
quantitative understanding metrics remain deferred.
