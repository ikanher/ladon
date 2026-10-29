# Typed bound observation: first implementation stage

The general plan is ready and tasks 1.1–1.2 are implemented. Public
`investigation contract observe-bound` preserves typed estimate syntax from a
verified formal snapshot; `inspect` checks its exact replay. These are separate
`real-bound-shape-v1` observations, with unresolved admission and no mathematical
contract. The prior Nat profile, recognizer, validators and snapshot implementation
are unchanged. See [usage and supported grammar](../../../../../docs/REAL_BOUND_CONTRACTS.md).

## What was established

- Arbitrary predicate/operator names and literal losses 0, 4 and 7 are exercised
  by generic syntax controls. Full typed binders, proof premises, fixed predicate
  parameters, set/function identity and constant permission scope survive.
- Moving K after the input-bound premise changes its permissions without losing
  the exact source origin. A failing regression exposed and then checked this fix.
- Missing guards, mismatched predicates/sets, symbolic inputs, negation/disjunction,
  depth/node limits and malformed bound references do not become admitted estimates.
- An actually compiled Lean fixture deliberately defines a fake type named `Real`
  and a trivial bound predicate. Syntax is observed, but admission stays unresolved.
  This is a negative trust-boundary control, not a positive mathematical-real case.
- Rehashed mutations of the shift, admission, extra fields, implementation or
  nested source identity fail inspection. Immutable publication and exit code 2
  for unresolved semantic work are covered through the public CLI.
- Existing validation, comparison and propagation inputs reject the observation
  wrapper as a semantic contract. Native semantic integration remains task 3.1.

## Informed replay, separately counted

[REPLAY.json](REPLAY.json) records six public observe/inspect commands against the
three preserved original source snapshots. No new compiler process is needed to
observe their syntax; this is replay, not fresh mathematical certification.

| Original statement | Shape result | Literal shift | Admitted contract |
|---|---|---:|---|
| inverse_finiteJets | observed | 5 | none |
| nonbarPart_finiteJets | observed | 4 | none |
| applyMultiplier_finiteJets | unsupported extra multiplier structure | — | none |

The two fixed-loss candidates have different operator identities. The generic
multiplier statement retains its original source and does not receive an invented
numeric loss. Both fixed-loss statements remain **0/2 admitted contracts**; the
new result is **2/2 typed shapes**. A syntax-only fake-name fixture remains
unadmitted as required. These are known-source development results; no unfamiliar
exposition issue or mathematical falsity is established.

All six commands complete in 2.26 seconds including inspection, with a maximum
observed process RSS of 31.05 MiB under the unchanged 12 GiB cap. These costs exclude
the original Lean observation runs preserved in the baseline packet.

## Verification

[CHECKS.json](CHECKS.json) records commands and scope: 63 focused checks plus
23 native/origin checks, with three repeated cases: **83 distinct checks pass**.
Ruff and scoped strict quality pass. No full-suite or full-paper run was launched.
Both changed OpenSpec packets validate strictly; `git diff --check` passes.
Independent read-only review is board #1562, accepted after root-run checks in
#1563. The reviewer ran no tests; root executed the recorded verification.

The root preserved test-first failures (18 parser failures, seven missing public
consumer failures, then one origin regression). A helper-only fixture refactor
and import formatting were explicitly superseded/refrozen: all test-function ASTs
in the first and the entire AST in the second are unchanged. Original and revised
bytes are retained here. No assertion or test case was removed.

[VERIFICATION.json](VERIFICATION.json) confirms 2,670 primary files, 65 earlier
frozen artifacts, and the historical contract runtime modules remain unchanged.
All five newly frozen test/source files match. The board's pre-existing unrelated
`test_rational_lean_encoder_v2.py` mismatch remains; whole-board cleanliness is not
claimed. Runtime/test identities bind this evidence. Nothing was pushed.

## Remaining work

The next gate is task 2.1: the general source-bound predicate/law admission
interface and bounded feasibility check. It must handle unrelated mathematical
families and reject changed definitions/environments before any positive admission.
Generic Real laws, a checked derivative adapter, closed native semantic contracts,
comparison/propagation and the 2/2 admitted-contract metric remain open. The paper
norm bridge remains unresolved. The parent stays 8/12 with its independent-pair,
full qualification and evaluation/discovery gates unchanged.
