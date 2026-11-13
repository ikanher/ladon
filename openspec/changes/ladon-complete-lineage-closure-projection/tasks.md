# Tasks

Planning, field reproduction, implementation, and focused regressions are
complete. Repository-wide verification has run; unrelated failures are
recorded in the implementation receipt. The specification owns acceptance;
the design owns algorithms and metrics.

## 1. Reproduce the failure and freeze coverage oracles

- [x] 1.1 Add independent finite-graph fixtures and red tests for a shared 20-layer diamond, single-node closure, typed parallel edges and a cyclic component; verify expected node/edge sets are computed from fixture input rather than the query under test.
- [x] 1.2 Add failing metrics for false completeness, payload/count mismatch, dangling endpoints and graph dependence on route limits; verify exact-cap and cap-plus-one cases fail for the intended reason.
- [x] 1.3 Preserve a small regression of the field discrepancy (stored closure versus route graph), document its scope in test comments, and verify the packet evidence with `python openspec/changes/ladon-complete-lineage-closure-projection/evidence/verify.py`.

## 2. Retrieve complete stored closures within finite budgets

- [x] 2.1 Implement the closure-scoped read query using existing identity/freshness checks and one coherent read transaction; verify full expected node and typed-edge equality on the fixtures and rejection of stale/missing/ambiguous closures.
- [x] 2.2 Implement deterministic target-inclusive node selection, endpoint-closed typed edges and exact cap/filter omissions; verify generated-node, edge-kind, exact-cap, byte-limit and SCC tests.
- [x] 2.3 Add separate source/selected-graph/route/external coverage fields and exact payload counts; verify complete graph coverage never upgrades theorem-check, external-expansion or historical authority.
- [x] 2.4 Document closure-selection semantics and the finite limits next to the query API; run the focused new closure-query tests and existing store/query tests before moving on.

## 3. Make representative-route acquisition scale with unique graph work

- [x] 3.1 Replace path-expanded reachability with indexed distinct-node/minimum-depth acquisition and a finite typed-adjacency work cap; verify each node expands once on layered diamonds and both traversal directions terminate on SCCs.
- [x] 3.2 Build deterministic bounded representative routes after acquisition, retaining typed predecessor information; verify shortest-path tie handling and route-limit changes do not alter already acquired graph coverage.
- [x] 3.3 Split depth-exhaustion tests from actual depth truncation, add the public traversal-work limit and version its work-unit reporting; verify cap-plus-one behavior and document the change from path-row to distinct-node budgets.
- [x] 3.4 Run existing route, tree, bottleneck and query-plan tests; resolve intentional semantic changes explicitly and verify the existing forward/reverse closure indexes remain used.

## 4. Expose the new view through live and historical interfaces

- [x] 4.1 Add `--view closure` and handle inapplicable route-only options explicitly; verify parser/help tests and a CLI fixture returning the complete typed graph while existing `graph` retains representative-route semantics.
- [x] 4.2 Wire live and historical projections through the same coverage logic; verify `--refresh never` triggers no Lean/Lake process, evidence mutation, or historical-to-current authority upgrade.
- [x] 4.3 Retain atomic bounded output and deterministic fingerprints; verify prior output survives byte-limit/rendering failures and insertion order does not change canonical output.
- [x] 4.4 Update `docs/CLI.md`, relevant README guidance and the maintained Ladon skill's lineage instructions; verify documented commands and explain library-frontier versus axiom-complete scope.

## 5. Validate the integrated field result and release boundary

- [x] 5.1 Run the focused lineage store/query/projection/CLI/history/hardening suites and the repository Python-quality gate; retain commands, exit statuses, source identities, and failure classification in an implementation receipt.
- [x] 5.2 Replay the retained gradient field case under the recorded resource ceilings, using stored-only queries after acquisition; verify exact selected node/typed-edge equality and zero false-complete/count/dangling-endpoint metrics, with bounded wall-time/RSS observations.
- [x] 5.3 Compare before/after graph work on the synthetic sharing fixture and field case; reject a repair that depends on increasing the old path-recursion ceiling or enumerating all simple paths.
- [x] 5.4 Verify stored closures remain usable by pre-existing views and rollback requires no data deletion/migration; run strict OpenSpec validation and obtain a source/behavior review of the final implementation before marking this change complete.

## Incoming internal-use review — 2026-11-14

Source: review pasted by the owner in this session; reviewer identity and source
revision were not supplied. Status at intake: **received / pending validation**.
The review reports that a stored-only lineage query runs comprehensive index
inspection, captures the repository twice for freshness/stability, captures it
again to build the query identity, then checks for the selected closure. It
recommends cheap stored lookup, reusing a validated snapshot, shared in-progress
validation, and eventually shared result caching. Latency attribution is a
hypothesis; the reviewer supplied no per-stage profile.

Next checks: confirm the call sequence and database compatibility requirements;
identify existing historical-query and evidence-receipt semantics; measure
captures and status diagnostics separately before adding persistent caching.
Preserve strict live validation and explicit snapshot-bound authority. Caller
labels must not participate in freshness, authority, or cache identity. Distinct
repositories/worktrees and evidence generations require distinct identities.
The completed closure-projection tasks above retain their original acceptance;
this follow-up does not silently reopen or qualify them.

### Initial reconciliation

Source inspection confirms the reported three captures and that the CLI calls
full index status before the selected-closure lookup. Status includes database
counts, history, schema diagnostics and `dbstat` accounting. The projected query
already owns a coherent SQLite read transaction, and `--history` already reports
historical association with current freshness withheld. The third source capture
is independent of the earlier freshness comparison; the follow-up should pass
the validated identity through rather than build another sampled identity.

Accepted first work package (implemented; receipt below):

- [x] F.1 Retain a stage-timed baseline for present and absent stored closures.
  Freeze source/index/helper identities and distinguish inclusive timings from
  disjoint stage costs. Record instability rather than treating a changing donor
  checkout as an unchanged-source comparison.
- [x] F.2 Qualify minimal index/closure preflight and remove comprehensive status
  diagnostics from ordinary lineage queries. Missing `--refresh never` closures
  must perform zero source captures. Preserve missing/corrupt/incompatible index
  outcomes, refresh policy, output bounds and evidence authority.
- [x] F.3 Pass the strictly validated repository snapshot through identity and
  projection construction. Retain explicit source-stability checks and coherent
  database-generation reads; qualify concurrent edits/publication and compare
  unchanged-source output/evidence semantics with the baseline.
- [x] F.4 Repeat the stage measurement, record capture counts and same-query
  evidence equality, and update the CLI guide with measured behavior/limits.
  Decide whether residual cost warrants a separate shared-validation/cache
  packet. No agent-specific workaround, persistent cache or public snapshot-token
  interface is authorized merely by completing these planning tasks.

Shared in-flight validation and persistent results remain proposed follow-ups.
They require a cross-process lifecycle and explicit snapshot-authority contract;
a process-local dictionary or TTL cannot satisfy that contract. Caller labels
are optional accounting metadata and must not determine reuse or authority.

Measured review disposition: [REVIEW.md](evidence/query-validation-review-r01/REVIEW.md)
confirms the call sequence and records a 61.17-second stored query with a
0.000916-second closure lookup. A separate historical-availability check took
51.68 seconds to hash 49 snapshots totaling 44.63 GiB. Three source captures
totaled 8.95 seconds in the first query. Removing comprehensive status from the
query path is the priority; persistent caching is not yet justified as the first
implementation. These single-sample timings are not additive across runs and
provide no percentile or speedup claim. F.1 remains open for an absent-closure
baseline and a controlled before/after comparison at the review checkpoint.
The subsequent implementation and measurements below supersede that pending state.

### Follow-up implementation complete — 2026-11-14

[Implementation report](evidence/query-validation-review-r01/IMPLEMENTATION.md):
22 new contract cases were qualified within 145 passing affected tests. A stored
summary fell from 61.17 to 5.70 seconds and a missing closure from 61.85 seconds
to 0.009 seconds in the recorded single-run comparison. Payloads match except
elapsed-time fields. Present/missing captures are now 2/0, with no comprehensive
status or historical-availability scan. Coherent read transactions, refresh
policies, unstable-source rejection and historical integrity behavior remain
qualified. Scoped Ruff and complexity checks pass. The full strict quality gate
retains ten pre-existing real-bound complexity failures. No persistent cache,
public snapshot token, cross-process validation service or schema migration was
introduced; roughly 5.7 seconds of strict source validation remain. A shared
snapshot API is a separately specified follow-up if repeated-use measurements
justify it. These changes do not retroactively update the 0.4.2 release receipt.
