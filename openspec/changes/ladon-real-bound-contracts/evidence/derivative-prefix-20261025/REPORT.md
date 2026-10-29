# Checked full-joint derivative-prefix adapter

Task 2.3 is complete. The fixed adapter now binds the actual observed predicate
to the norm of its full joint real Fréchet derivatives, preserving all
j ≤ n, p ∈ S and y:Y quantifiers, the function spaces, universes and actual
normed-space instances.

Two independently named generic estimates and both original fixed-loss
estimates passed fresh capture, completion, compiler replay and axiom checks.
**Original derivative bindings are 2/2; full informed semantic contracts remain
0/2.** The paper-norm bridge, estimate-body validation and native activation
remain separate work. No exposition fault is established by this packet.

## Public behavior

- plan-derivative-prefix consumes a full bound observation and produces the
  closed ladon-derivative-prefix-plan-v1 schema. Its profile is
  joint-real-frechet-prefix-v1. No caller-selected measure or admission flag.
- check-derivative-prefix consumes that plan and an exact proof term, freshly
  checks its generated Admission proposition and returns checked-binding,
  derivativeAdmission:checked and exit 0 only on success.
- Even then, admission is unresolved, contract is null and paperNormBridge is
  unresolved. The original observation retains its operator, literal loss,
  regularity premises and constant-permission scope.
- Missing instances, non-product or dependent domains and retained proof-valued
  parameters are unsupported. The checker adds no normed-space hypotheses.
- Named-measure v1 commands retain their behavior with new helper/checker
  identities. The two command families reject one another's plan schemas.

## Mechanism

The clean compiled LadonRealBoundDerivative module defines

~~~text
jointDerivativeMeasure f p y j := ‖iteratedFDeriv Real j f (p,y)‖
~~~

for f:P × Y → Z. The live builder reads the function type from the actual
predicate, exposes a nondependent product domain and synthesizes the six
normed-space data instances in the source's existing local/global environment.
The norm carrier is the full continuous-multilinear-map type on P × Y with
codomain Z; the derivative includes mixed directions. This does not assert
regularity or completeness of those spaces.

The shared bound helper compares the full live normalized statement modulo
bound-variable display names, checks exact input/output predicate prefixes,
builds Admission and closes only used dependencies. Proof-valued dependencies
and escaping locals/metavariables remain rejected. Both adapter paths now use
this shared closure and binding code. The target source is copied and elaborated,
rather than relying on its target-module object file.

The family, binding and derivative helpers compile before target declarations.
Fresh capture/completion/replay bind the closed typed proposition; compiled
inventories, source, helper/checker identities and the no-placeholder axiom
policy are verified. A digest or saved positive JSON is not a fresh certificate.

## Verification and metrics

- Four derivative bindings passed: generic losses zero/seven with three
  independent universes and all six instances, plus the original inverse and
  mean-removal observations. Original losses five/four are retained unchanged.
  The symbolic multiplier observation remains unsupported.
- Eight derivative negative attempts remained unresolved: parameter-only
  derivatives, a restricted point domain, squared norm, missing instances,
  complex-scalar derivatives, a retained proof parameter, a placeholder and a
  non-product function domain. These are rejected admission attempts, not
  mathematical refutations. The placeholder completed and was rejected for
  sorryAx, rather than timing out.
- Eleven fresh v1 compatibility cases passed their expected classifications:
  three valid bindings and eight unresolved negatives, including changed
  definitions, instances, imported compiled meaning, forged expressions,
  unused False premises and placeholders. The compiled-import mutation kept
  selected source and pinned context unchanged; the fresh old proof was rejected.
- Five public boundary controls rejected stale source, saved-result reuse,
  both cross-command schema substitutions and an injected measure. Historical
  Nat validation rejected derivative plans/results in two additional controls.
- All 185 focused tests passed in 118.62 seconds. Thirteen new planner/CLI cases
  were observed red before implementation. Ruff, scoped strict quality,
  OpenSpec strict validation and diff checks passed.
- Both bundled and shared Ladon skills were updated and validated. The narrow
  skill edit preserves invocation policy and adds no example-specific guidance.
  The offline wheel contains exact current adapter/shared-helper sources.
- The twelve derivative attempts took 535.58 seconds in their check commands,
  peaking at 5.802 GiB RSS. The eleven v1 attempts took 326.21 seconds and
  peaked at 4.185 GiB. These exclude planning/formal observations, development,
  boundaries, packaging and the separate pytest execution. Each admission check
  had an explicit 600-second deadline, 60-second internal compiler phases and
  the unchanged 12 GiB process-tree cap. No resource failure was counted as a
  semantic negative.

See VERIFICATION.json, CHECKS.json, IMPLEMENTATION.json and raw results under
generic-first/, matrix/, original/, v1-replay/ and v1-import-replay/.
The exact goal/capture structures agree on every accepted check, with two
capture and four completion receipts plus a separate typing receipt.

## Review and preserved history

Independent route/test workers completed a real peer challenge about instance
ownership. Root integrated their compatible findings and corrected the scratch
seven-loss phrasing to the actual input J f S(n+7)C, preserving prefix quantifiers.
A distinct final auditor found no consequential source-level defect; REVIEW.md
records that this was source review plus root-produced artifacts, not an
independent Lean execution. Root subsequently completed the requested original
and v1 replays.

A new test exceeded the strict complexity threshold because of its assertions.
The helper-only refactor preserved all eleven assertion expressions and all
test cases/actions. The full AST is identical after helper expansion; original,
proposal, equality receipt and copied-test result are preserved under
quality-refactor/. The board explicitly superseded/refroze that test; no
expectation changed. The skill validator lacked YAML in the project venv, so
it ran successfully with existing system Python; no dependency was installed.

All 2,670 primary files and 225 frozen artifacts from the preceding four
packets are unchanged. Historical Nat profile/runtime files are unchanged.
The prior generic rule library and its two-test evidence remain byte-identical.
The one pre-existing frozen-test mismatch is untouched. Previous binding
receipts are historical after the shared helper refactor; the v1 results in
this packet are fresh under the new identity.

Next is task 3.1: closed Real profile/native records and source-bound evidence
dispatch, followed by comparison/propagation. The parent's independent-pair,
unfamiliar-source discovery and evaluation gates remain open. Nothing was pushed.
