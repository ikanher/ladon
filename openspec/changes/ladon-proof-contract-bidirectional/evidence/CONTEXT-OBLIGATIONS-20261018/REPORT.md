# Native original-context obligations

Ladon now plans and checks separate obligations over a frozen native
correspondence: ordered premise supply, provider validity, formal-domain
admissibility, representation typing and conclusion transfer. The public
`context-obligations` and `check-context-bridge` commands regenerate their own
subjects from exact native owners and a fresh original application observation.
They accept no caller-written goals, extra assumptions or replacement object map.

| Constructed control | Local result | Checked / required | Check wall / case budget |
|---|---|---|---|
| Two ordered premises | checked-support | 9 / 9 | 250.27 / 330 seconds |
| Fin 5 → Nat representation | checked-support | 7 / 7 | 196.15 / 270 seconds |
| Earlier-binder-dependent Fin n | checked-support | 5 / 5 | 143.06 / 210 seconds |
| Missing second premise | unresolved-bridge | 0 / 9 | 36.50 / 90 seconds |
| Excluded parent reference | unresolved-bridge | 0 / 9 | 36.70 / 90 seconds |
| Unjustified stronger conclusion | unresolved-bridge | 0 / 7 | 36.48 / 90 seconds |

All **21 positive obligations** have accepted completion, independent replay and
trust checks. The complete serial driver, including fresh extraction, native
preparation, checkpoint/expiry controls and the deliberate memory stop, took
**810.52 seconds within 1,200 seconds**. The case budgets
include planning before the reported check-call times. The additional checkpoint
was rejected, expiry stopped before any worker, and the deliberate 1 MiB stop
returned the stop/report instruction without retrying. See [acceptance](acceptance.json)
and [raw log](acceptance.log).

The ordered case exercises both public CLI commands. It preserves premise
occurrences 2 and 3 separately, with a provider obligation for each. The
representation case maps an original `Fin 5` index through `Fin.val` to a formal
`Nat` argument. Its source-domain bound is proved separately from typing and
conclusion transfer. The dependent case preserves the original binder order
`n : Nat`, then `i : Fin n`, including formal let-bindings with dependent types.

The `domain` channel supplies equality witnesses inhabiting the observed formal
domains. It is domain admissibility, not a claim that a representation is an
equivalence or invertible. The independent conclusion obligation is what checks
the needed semantic direction. In the negative representation control a typed
finite-index map and formal bound cannot establish the requested equality to
zero. The missing-premise control retains the unsupplied second proposition;
the parent-term control rejects the named parent in the generated context.
These are known constructed controls. Rejected terms or failed searches remain
unresolved and do not establish mathematical falsity.

## Identity, context and authority

The operation validates the entire native batch, resolves the exact
`proofir.correspondence` and interpretation/source-map owners, and rebuilds every
original obligation from the native interpretation, scoped application and
object map. Rehashed native payload mutations to goal text, premise order,
assumptions, status and omitted rows are rejected. Altering the reading cannot
reuse its old plan checkpoint.

The plan commits the original interpretation/quote, source-map reference, map,
source/application identity, environment, ordered premise/provider observations,
strict-prefix digest and all goal digests. Every plan and goal digest in the
final results is independently recomputed in [root verification](source-verification.json).
Checking always regenerates the plan before accepting terms for the saved ID.
The caller supplies one absolute monotonic deadline; all stages retain that
clock. The orchestrator carries the same request between planning and checking.
A plan identity binds mathematical/source inputs rather than granting a new
time budget.

Preparation observes the actual source declaration range and compiles a prefix
ending before the selected parent theorem. Compiler guards exclude that theorem
and its original module. Every term stage rechecks original Lean bytes, prose
bytes, environment and prefix digest before and after capture/completion,
independent replay and trust checks. Formal conditional and provider validity
remain separate from establishing their hypotheses in the original interpreted
context. Original generated positions never replace original source observations.

No residual may be dropped to obtain support. Unmapped/proof-dependent objects,
unsupported operators and escaped binders stay rejected or residual. The
operation supports the existing scoped lowering fragment, including earlier
binder references in domains; it is not a general dependent-type formalizer.
Only every required goal with accepted completion, independent replay and trust,
with no residuals, yields local `checked-support`. Prose fidelity stays attributed
and unreviewed; whole-method authority is none and falsity is not established.

## Bounds and evidence custody

Preparation and each term stage have enclosing process-tree ceilings of
30 seconds, 12 GiB RSS and 8 MiB output, preserving stricter caller limits and the
shared absolute deadline. Larger consumer timeouts in CLI receipts cover several
serial stages, not a larger per-stage allowance. Legacy inner helper settings
remain subordinate to the enclosing supervisor.

Aggregate inputs and complete compact outputs are bounded to 8 MiB. The auditor
found that binding replication could allocate excessive memory before output
compaction. Two new failing regressions preceded a fix: expanded row/binding
costs are now admitted before binding copies, and worker output is counted
before JSON serialization. Large evidence returns an incomplete resource stop.
Two additional failing regressions preceded before/after source/prose/environment
custody checks. Memory-stop instructions survive compaction; no resource stop
is retried. The deliberate 1 MiB case is last in the source driver. Its failure
is expected, and subsequent regression testing is a separate normal-budget run.

The maximum sampled process-tree RSS across all final source receipt shapes is
**3,845,029,888 bytes (3.58 GiB)**. Normal
controls have no memory/output/timeout flag set; only the intentional 1 MiB case
has the expected memory flag and report-back requirement. The six complete
result files are 5,898,320; 4,547,551; 3,199,491; 1,016,830; 1,092,821; and
1,016,608 bytes, each below 8 MiB. Their combined size is not one invocation's
output budget. Original Lean source bytes are unchanged.

[The runtime manifest](RUNTIME.json) and [archive](runtime.tar.gz) preserve
493 entries, adding five modules to the preceding accepted 488-entry runtime and
changing only the additive public CLI dispatch among old runtime files. Live and
archived hashes match. The new [six test files and real-observation fixtures](TESTS.json)
and [archive](context-tests.tar.gz) preserve 36 checks: 22 initial failing-first
boundary checks, four later failing-first resource/custody checks, and ten green
regressions. Original frozen tests are unchanged.

The distinct red, green and audit roles used the canonical project board. Root
integrated the scratch helper, split its complexity without changing frozen
expectations, and ran all source workflows serially. [Initial audit](reviews/FINAL-INTEGRATED-AUDIT.json)
and [fix review](reviews/FOLLOWUP.json) are retained. Source-first independent
review is distinct from root-owned kernel/source evidence. [Independent raw custody review](reviews/RAW-CUSTODY.json) confirms the source
receipts, owners, output bounds and runtime hashes; its scope excludes the
root-owned final regression gate.

An initial feasibility harness passed an unsupported `runner` argument and
failed before Lean. Corrected execution ran under a 30-second supervisor; a real
two-premise extraction and declaration-range observation took 9.68 seconds within
its 60-second cumulative feasibility allowance. A later prototype compared a
minimal observer source record with a richer slice attribution record; comparing
the common path/hash and exact environment fixed the rejected preparation.
The earlier nine-goal replay passed in 243.37 seconds before the final resource
and custody changes. Its inputs/results remain under [exploratory](exploratory);
it is separate from final-runtime acceptance and is not a speed comparison.

## Verification and remaining scope

The full relevant regression gate passed **964 tests across 150 files** in
**388.73 seconds**, with no failures, errors or skips. The preceding
accepted suite contained 928 tests across 144 files; all of those owners remain
in this run, plus the six new files. This is coverage growth, not a detection-benefit
measurement. See [command](integration-command.json), [log](integration.log),
[status](integration-status.json), [JUnit](integration.xml) and [verification](verification.json).
Strict quality over src/tests/scripts, no-cache Ruff, frozen-test verification
and selected child/umbrella strict OpenSpec validation pass. Source acceptance
and this regression run are serial, with the root as sole Lean owner.

This completes the standalone source-context checker capability. Bidirectional
task 1.2 remains open: the richer source interpretation/context must still be
bound to route-generated mathematical contracts and admitted backward-rule
identities. The child remains 7/8 complete; the parent remains 2/12. The existing
norm-specific route bridge retains its bounded universal-Nat identity profile.
Its separate CLI dispatch also remains open. Supporting this new checker does
not imply that the route consumer already uses it.

No beam policy, corpus admission, matrix baseline or Navier–Stokes retest was
added. Held-out C has zero admitted cases, and detection benefit remains
unmeasured. Earlier reports, baselines and handoffs are preserved. No dependencies
were added and nothing was pushed.

A reproduction uses the current checkout, an empty output directory and a Lean
repository destination that does not exist:

```bash
mkdir /tmp/ladon-context-evidence-fresh
PYTHONPATH=src:tests .venv/bin/python \
  openspec/changes/ladon-proof-contract-bidirectional/evidence/CONTEXT-OBLIGATIONS-20261018/run_acceptance.py \
  /tmp/ladon-context-evidence-fresh /tmp/ladon-context-repo-fresh
```

This driver was executed for final serial acceptance. Saved monotonic clocks
refer to that run; a reproduction creates fresh inputs and clocks.
