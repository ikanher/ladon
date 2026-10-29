# Versioned prose-bound recognition — Task 1.3

The public `investigation contract recognize-prose-bound` operation now recognizes
the unchanged selected authored proposition. It retains global scope and checks
the named input shift against builtin `n + 4` and the output coefficient against
its exact source-instance product. This closes the earlier consumer-grammar gap.
It does not prove the estimate or establish an exposition error.

The new profile `real-bound-prose-shape-v2` supports global and explicitly
set-indexed estimates. It retains the original typed proposition, complete
telescope, guards, predicate/operator parameters, set identity, coefficient
permission scope, and expression origins. Exactly one complete decomposition
must match. No set/domain adapter or estimated coefficient dependency is inserted.

Numeric loss and canonical product features require synchronous Lean kernel
checks of exact expression equalities in the selected source context. Certificates
close over every preceding source binder, including unused proofs and local
instances. The product preserves its actual instance. Unsupported aliases stay
residuals; no predicate law, source meaning or native contract is admitted.

See [the public guide](../../../../../docs/REAL_PROSE_RECOGNITION.md), the
[frozen engineering contract](CONTRACT.md), [runtime source snapshot](runtime/),
and [machine-checked verification](VERIFICATION.json).

## Qualification

| Public case | Result | Scope / loss | Seconds | Peak tree RSS |
|---|---|---|---:|---:|
| Selected unchanged reading | Recognized | Global / 4 | 51.90 | 5.09 GiB |
| Unrelated estimate | Recognized | Global / 5 | 13.40 | 3.43 GiB |
| Unrelated indexed estimate | Recognized | Set-indexed / 7 | 13.67 | 3.42 GiB |
| Incorrect coefficient alias | Unresolved | Global / checked order 5 | 13.94 | 3.43 GiB |

All four use actual Mathlib Real under their existing pinned Lean 4.34.0-rc2
context. The selected formula, symbols, source span and typed proposition match
the prior observation exactly. Its source relocation is inherited explicitly
from the earlier sealed observation evidence. All attempts and the public
historical inspection shared one 600-second clock, 12 GiB RSS and 8 MiB output
cap; no automatic retry, cap increase or clock reset occurred. The outer process
receipts include CLI overhead; nested receipts separately measure worker stages.
The largest selected snapshot is about 5.4 MB, below the configured cap.

Inspection against the current selected context passes, with authority none,
freshCheck false and evidenceAuthentication not-established. Structural validation
and current-source custody do not authenticate saved kernel execution. Fresh
recognition repeats observation and both kernel checks. Prior v1 history remains
readable without a root; its old runtime identity correctly rejects current-root
reuse after these runtime changes.

The 28 focused checks pass. These include global/set skeletons, changed names,
late coefficient permissions, missing guards, preserved aliases, symbolic shifts,
wrong products, exact local instances, altered certificate paths/scope/instances,
immutable CLI outputs, and actual outer-timeout scratch cleanup. Their live
Lean-only fixture deliberately defines a Nat-backed type named Real; those
checks establish syntax and ownership behavior, not Mathlib Real laws. The
separate public matrix above supplies actual Mathlib integration evidence.
The old shape reader remains unchanged and rejects unsupported global input.

Compatibility validation additionally exercises prior proposition observation,
legacy CLI/source contracts, old Real observation and shape/origin checks.
All 63 compatibility checks passed in 164.61 seconds, giving 91 passing
focused and compatibility checks overall. See COMPAT-1.txt. Scoped Ruff, strict_quality_issues,
compileall, strict child/parent OpenSpec validation and git diff --check are
recorded separately. Whole-repository/release qualification is not claimed.

Both frozen Task 1.3 acceptance files are unchanged, as is the frozen v1
observation acceptance file. The full board check also reports one unrelated
older mismatch, test_rational_lean_encoder_v2.py. Its working content matches
HEAD; this task did not edit it or supersede its board registration. The full
board is therefore not reported clean. See UNRELATED-FROZEN-BASELINE.json.

## Feasibility and review

The initial kernel API probe exposed an asynchronous false-green trap: returning
from Core addDecl does not mean the kernel has accepted a declaration. That
failed attempt is preserved. The implementation uses synchronous Kernel.Environment
addDecl with skipKernelTC disabled and accepts only its successful result.
Positive, incorrect-offset, actual Real product, local-instance and unused-proof
closure probes preceded dependent implementation. Compiler/API and canonical
literal mismatches remain in the failed integration receipts; none receives
passing credit. Each distinct feasibility/helper/public objective retained its
declared clock across retries.

Luna workers supplied API discovery, adversarial controls and an isolated helper
proposal. Root reviewed and corrected the proposal, authored production edits,
and ran all Lean and test processes. The helper proposer used an incompatible
board helper and recorded lifecycle entries directly on the existing board;
root verified provenance rather than treating the uncompiled proposal as green.
A red-worker peer answer outside the board was not credited as independent
swarm evidence. Root's scoped kernel probe independently established closure.

A fresh Luna integration auditor reviewed the final 15-file source revision and
found no actionable defect (board 1916; initial report miscounted 14, corrected
by the 15-file follow-up). Documentation and saved selected-case authority
boundaries were independently reviewed in 1918/1919. The auditor omitted its
start event and explicitly recorded that omission without backdating it. Review
is source/evidence review, not independent execution of the runtime checks.
See audit/ and FINAL-REVIEW.jsonl. Root owns acceptance.

VERIFICATION.json checks all 2,670 protected primary files and the earlier sealed
67-file source-pair, 34-file norm-bridge, 41-file feasibility and 76-file
observation packets unchanged. Of the prior observer runtime snapshot, only
real_prose_cli.py and the private observation workspace-parent parameter changed;
old parser/helper/record semantics are preserved. New modules and the alias
helper are additive. No dependency, cache, paper edit, theorem placeholder,
commit or push was introduced.

## Remaining work

Task 1.3 is syntax recognition and checked arithmetic only. Authored native Real
records and persistence/dispatch remain Task 2.1; checked formal connections
remain Task 2.2. Final source-pair/skill qualification remains Task 3.1. Parent
propagation and unfamiliar-source discovery remain open. Counts from this matrix:
three recognized readings, one residual, zero predicate admissions, zero native
semantic contracts, zero formal connections, and no mathematical falsity or
discovery benefit established.
