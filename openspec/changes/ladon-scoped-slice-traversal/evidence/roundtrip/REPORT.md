# Dependent-instance round-trip repair

The original source-bound application now extracts successfully with the existing
131,072-node default and no traversal cache. The public command completed in
**27.25 seconds**, with **3.72 GiB** peak process-tree RSS. Its four successful
compiler/helper receipts include stable repeated observation. Shape validation,
slice identity, current composed helper identity and selected source identity
all pass.

The [slice](actual-slice.json) records one application of
`NavierStokes.SmoothFourierData.coefficient_seminorm_bound`, 14 local declarations
and five ordered proposition arguments. This closes the extraction task, not
the mathematical audit: four providers remain `provider-unreplayed`, and the
`hzero` premise remains `provider-boundary`. The argument at position 3 is the
actual `w.length + 1` expression. No premise has been removed or replaced to
obtain the observation. See [command receipt](actual-command.json) and
[validation](actual-verification.json).

## Cause and repair

The pinned Lean lambda printer can omit an instance binder's name when it is
absent from the final proof body, even when later binder types mention it.
The captured proof contained an anonymous `[NormedAddCommGroup P]` followed by
types referring to `inst`, which cannot elaborate in an empty local context.
[Diagnostic text](diagnostic-printed-context.txt) preserves this failure.
The diagnostic used an explicitly instrumented helper and is diagnostic evidence
only, not a production extraction receipt.

A small source module with dependent `Carrier` and `Ready` classes reproduces
the error in both extraction profiles. Cases that use the instances in the
proof body already passed. The frozen regression had two matching failures and
two passing controls before the repair; all four then passed.

The shared printer explicitly names and types each binder in the closed proof's
outer lambda telescope, preserving all four binder kinds and hygienic names.
It changes no expression, local identity, target printer or global delaborator
registration. The remaining body uses Lean's ordinary printer. Both helpers
still parse and elaborate under an empty local context, reject unresolved
metavariables, disable errors-to-sorry/postponement, and compare target/proof
against the original expressions by definitional equality. Later unsupported
body-printing cases continue to fail closed rather than receiving fabricated
support. Shared material participates in helper and checker implementation
identity.

Independent review found a pre-existing asymmetry in the unscoped consumer's
text budget. A second frozen regression established that it accepted printed
text over 1 MiB while the scoped helper rejected it. Both now apply the same
pre-parse target/proof text guard. All other node, depth, process, memory and
output limits are unchanged.

## Verification and custody

The [independent audit and addendum](AUDIT.json) record the resource finding and
its resolution, with no weakening of the round-trip guards. The auditor ran no
builds or tests; execution evidence is root-observed. The final unscoped-only
size-guard edit did not change the successful scoped helper's composed bytes;
[identity verification](actual-verification.json) justifies reusing that actual
extraction instead of rerunning it.

The final affected-consumer run passed **17 tests in 371.97 seconds**, covering
both extraction profiles, the oversized-text guard, scoped contexts, provider
replay, identity transport, typed subjects and preparation-helper freshness.
See [command](focused-tests-command.json) and [output](focused-tests.txt).

Both application controls also retain their original outcomes: five-loss is
accepted with zero residuals; four-loss is applicable with two identical residual
premises. They took 4.65 and 4.66 seconds with about 5.02 GiB peak RSS. These
remain ambient selected-application checks, not certification of the full norm
bridge. See [control summary](APPLICATION-SUMMARY.json).

Affected Python strict quality checks and Ruff pass. Both frozen regression
files match the board. The historical board's unrelated rational
encoder mismatch remains outside this change.

[Input verification](input-verification.json) confirms all 2,670 primary files,
21 original diagnostic artifacts and 40 previous node-budget artifacts are
unchanged. The earlier failed extraction and cache measurements remain intact.
No cache, full-suite rerun, new paper audit, source rewrite or push is part of
this repair. The full norm bridge, unsupported formal-contract producer and
unfamiliar-source detection gates remain open.
