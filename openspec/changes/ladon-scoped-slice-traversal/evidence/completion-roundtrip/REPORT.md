# Source-goal completion instance-binder repair

The five actual premise-provider closures and selected application now complete
with fresh capture, independent source-context replay, zero residuals and only
standard Lean axioms. Their [premise audit](../../../ladon-proof-contract-analysis-umbrella/evidence/provider-premise-audit-20261025/REPORT.md)
keeps all original assumptions and the paper's full-norm bridge open.

## Failure and patch

The original application's second provider captured successfully but completion
rejected it with `Unknown identifier inst`. The submitted closed proof was valid;
completion's own print-and-reparse step still used Lean's ordinary lambda
printer, which can omit an instance name needed by a later binder type.

A frozen small regression reproduced `Unknown identifier c`; its body-used
instance control already passed. Completion now composes the existing shared
instance-preserving printer and uses it at that exact round-trip boundary. No
expression, trust policy, parser/elaboration check, freshness guard or public
result schema was replaced.

The first two-line patch passed seven real completion tests but accidentally
imported the slice printer's 64-level telescope guard. A second frozen control
showed a 70-binder completion passed before that patch and failed under it. The
final shared printer accepts a depth parameter: slice callers keep the default
64, while completion uses Lean's configured maximum recursion depth (including
Lean's explicit zero/unlimited convention). Process, memory and output bounds
are unchanged. Shared bytes remain part of helper and checker implementation
identity.

## Evidence

- [Initial red](red-command.json): one expected failure and one passing control.
- [First patch](green-command.json): seven real completion checks pass.
- [Compatibility red](long-telescope-red-command.json) and
  [old-consumer baseline](long-telescope-baseline-command.json): the 70-binder
  control fails only under the first patch's unintended 64-level restriction.
- [Final focused gate](final-focused-command.json): **55 passed in 416.59 s**,
  covering completion trust/rejection/residual behavior, identity and freshness,
  long telescopes, both slice profiles, text limits and provider consumers.
- [Final source extraction](actual-command.json): **25.25 s**, **3.72 GiB** peak
  RSS; one application, 14 locals and five providers.
  [Validation](actual-verification.json) confirms shape, identity, current helper,
  unchanged limits, source identity and all closed proof/target texts.
- [Actual conditional replays](../../../ladon-proof-contract-analysis-umbrella/evidence/provider-premise-audit-20261025/VERIFICATION.json):
  six completed, 508.49 s total, 5.12 GiB peak.
- [Independent audit](AUDIT.jsonl), post #1529, found no actionable issue in
  the final production patch; its final-test condition is satisfied.
- Scoped strict quality and Ruff pass; strict OpenSpec validation passes.
  [Custody verification](custody-verification.json) preserves all 40 earlier
  traversal artifacts and 24 earlier extraction-repair artifacts.

The new tests needed import sorting only. Original frozen bytes are retained;
[AST verification](import-order-verification.json) shows the same imported symbols
and every non-import node unchanged. Board revisions record the supersession.
The [three-case rerun](lint-only-regression-command.json) passes after that lint-only edit. The board still reports its pre-existing unrelated rational-encoder test mismatch; this packet does not claim whole-board cleanliness.

## Incident and limits

The strict quality script's `--target` option scopes lint/complexity, but its
subsequent pytest step unconditionally launches the full suite. Root stopped
that unintended command and its descendants on discovery. The
[incident](QUALITY-INCIDENT.json) and interrupted log are preserved; no full-suite
pass is claimed. Direct scoped quality checks replace that command here.

This is a consumer correctness repair, not new mathematical capability. All
provider closures remain conditional; no prose norm bridge, independently
sourced contract frontier, whole-paper audit, or detection benefit is established.
No caching, paper-source edit, full qualification claim or push was made.
