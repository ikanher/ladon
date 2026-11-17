# r04 diagnostic and reporting consolidation

The diagnostic-capacity gap is repaired, role reporting separates both typing
checks, and inspection makes the selected premise boundary explicit. The
[internal reader exercise](../r04-reader-use/DECISION.md) reached a useful
certificate-reuse decision without demonstrating a need for another feature.

## Changes

All three capture-bearing early returns in `_check_goal` retain generated-goal
origin. The two context diagnostics survive native artifact production as
unknown results with no kernel guarantee. The recognized 32,768-module capacity
is unchanged; 32,769 entries, unrelated collections and byte bounds still fail.

New execution accounting uses `correspondence-check-roles-v2` to report actual
attempts by role, including unresolved checks. Interpretation and object-map
typing no longer inflate `substantiveCheckCount`. The legacy `typingProbeCount`
still means interpretation-only; explicit object-map and total-typing fields
avoid breaking its existing consumer. All supported/refuted/unresolved verdict
rules and canonical artifact schemas are unchanged.

Plain and native inspection add `premiseScope`. Native counts use all selected
stored obligations, independently of row display truncation. No direct premise
obligations does not imply no packaged hypotheses or a completed source audit.
The existing check result exposes the same scope in execution accounting.
An [append-only Adam context note](ADAM-CONTEXT.md) identifies the broader source
passages needed for its attributed derived consequence, without changing frozen
interpretations or checked records.

## Verification

- Test-first diagnostic regression: all ten new controls failed for missing
  origin/generic capacity before the fix. An initial harness type mismatch was
  corrected before recording that red run. The byte-bound control later needed
  the producer's existing tuple/decimal normalization; its expected bound was
  not weakened. Diagnostic/capacity/receipt suite: **32 passed**.
- Test-first reporting regression: all seven new controls failed for absent
  role/scope reporting. Focused diagnostic/reporting/context/receipt/accounting
  suite: **49 passed**. Helper-only cleanup preserved assertions and cases;
  the 17 newly added controls pass after cleanup.
- Both retained MF bundles inspect successfully via the checkout CLI. Source
  context, support dimensions and check-evidence bindings match the original
  views; new scope reports zero direct obligations with source assumptions
  unassessed. No large MF Lean replay was performed.
- All nine context anchors match exact source lines and SHA-256 identities.
- Changed-file strict complexity/dead-code checks pass. Repository-wide Ruff
  passes. Repository-wide strict complexity has **ten findings in seven
  unchanged HEAD-identical real-bound files**, recorded in
  [QUALITY-BASELINE.json](QUALITY-BASELINE.json); the global gate is not green.
- Full correspondence integration run: **180 passed, one failed in 1,764.63
  seconds**. The failed historical pressure test stops at `Path.resolve` because
  `/home/codex/projects/navier-stokes-retest-4/formalization` is absent. It never
  reaches checking. The test remains unchanged and this is not an all-green
  suite. The available public CLI, preparation, replay, schema and reporting
  consumers pass. See [full output](correspondence-suite.txt). OpenSpec strict
  validation and diff whitespace checks pass.

Regression tests use controlled process/capture I/O to exercise real checker
branches and the native artifact producer. Those fixtures are not Lean proof
evidence. Existing integration tests cover actual capture/completion and schema
consumers. No dependency, database migration, production memory/time-default
change, release bump, commit or push is part of this work.

## Next decision

Consolidate the current workflow. The new MF note needs its own finite-risk and
changing-momentum proof evidence; the older common-law certificate cannot be
used as a substitute. This is a support boundary, not a newly detected theorem
error. A future repeated retrieval problem can justify a bounded delivery
improvement. One successful reader exercise does not establish comparative
accuracy or lower total effort, and it does not reopen the historical broad
diagnostic integration program.
