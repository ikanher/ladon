# Feasibility baseline checkpoint: capture blocked

This run is **incomplete and not accepted**. It is retained as a harness checkpoint only. No proof-search result, per-case formal outcome, or baseline judgment was produced.

## Frozen inputs

- Policy: `../feasibility-policy-v1.json` (SHA-256 `9178b6453cf940d983490c98b69967f2795a61d41ca9d2ccfad227b1972e2287`)
- Runtime identity: `9043c1d61ca611055087474740419a049e5b554ef839ada4b9e30e3b94f2a78d`
- Runner at launch: SHA-256 `2d5b955daad70f72191493ebee77a5182077a94c39ebc8e0b231880a8f0e63ed`
- Operational case: `assumption-feasibility-01`; request and exclusions are in `case-01/results/operational-input.json` and `excluded-modules.json`.

## What did complete

`case-01/results/isolation-probes.json` records 26 successful checks: the selected module imported, and all 25 excluded imports (23 other corpus modules, `CoreCases`, and `Validation`) failed with the exact missing-module diagnostic. Peak observed RSS among these probes was 1,848,004,608 bytes.

The worker's control flow also passed its unrelated-compiler-failure and injected-forbidden-module guards before reaching goal capture. Their raw process receipts were not yet persisted by the harness; add that receipt before considering the common protocol fully evidenced.

## Known-goal control

The separate [known-goal source](known-goal-control/KnownControl.lean) was captured through the public `ladon proof-search goal capture` command using `runtime_custody.py run` and the same pinned runtime identity. Its source-bound report is `known-goal-control-capture.json` (`captured`, goal `p`); `known-goal-control/launcher.json` preserves the invocation and terminal receipt. Two earlier control attempts correctly failed before Lean execution because the report was inside the target repository and then because the fixture lacked `lean-toolchain`; the final successful invocation supplied the required toolchain pin and kept its report outside the repository.

This establishes that the public capture route can capture a simple known goal. It does not isolate why the generated feasibility probe fails: invocation mode, process resource setup, imported module, and goal shape have not yet been varied one at a time.

## Blocker

The positive source-goal capture report is `case-01/results/capture-positive.json`. It is `unavailable` with `no-goal-at-position`; the launcher receipt records the worker stopping at positive capture. The run therefore did not reach completion/replay or attempt the negative proposition. Earlier trial `feasibility-run-v1-r5` captured the positive goal but failed on the second-position capture; that trial is also incomplete and is not an accepted result. The same probe bytes at r14 returned a different status, so the observation remains unexplained.

Next work should diagnose and regression-test the exact source-position capture contract using the pinned runtime, preserve the raw unrelated-failure/injection receipts, and only then restart the four-case batch under a new run ID. Keep the task checkboxes open and the batch status pending independent adjudication.
