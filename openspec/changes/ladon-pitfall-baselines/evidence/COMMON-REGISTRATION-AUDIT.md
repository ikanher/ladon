# Common registration audit (2026-11-11)

## Result

Task 1.3d is still open. The existing feasibility policy is an accepted,
versioned registration for the four assumption-feasibility cases only. Its
scope must not be silently widened. The r19 run predates any common six-family
registration, so a new registration is post hoc relative to r18/r19 and may
govern only later runs. The original policies, runner locks, case records and
reports remain immutable.

## What the preserved runner accepts

`scripts/feasibility_baseline.py` hardcodes the feasibility policy and rejects
selected cases from any other family in `_acceptance_inputs`. Its host creates
one isolated project per case, but its operational worker accepts exactly
`{"module", "goal"}` and attempts that proposition and its negation with the
fixed tactic repertoire. It does not consume case roles, source expectations,
oracles, or judgment rubrics.

That interface is insufficient as a common registration contract by itself:

- Premise provenance requires a source-scoped proof route and projection
  evidence; checking whether a proposition and its negation are provable does
  not observe that route.
- Existence/default cases use source-attributed property obligations and
  typed context. A free-standing proposition string is not an adequate input
  binding for all of them.
- Operation-semantics cases require the typed operation identities and the
  exact transport/guard property to be scored. A generic proof outcome alone
  does not preserve these judgment dimensions.
- Claim-trust includes declaration-level axiom dependency. Proving a similar
  proposition with the generic tactic does not inspect the selected
  declaration's dependency closure.
- Domain/quantifier cases need a source/formal fidelity judgment; truth of the
  formal proposition alone cannot identify domain narrowing or quantifier
  mismatch.

The r19 runtime and policy therefore establish only the feasibility input and
command profile. The other profile descriptions must name executable commands,
exact case inputs, excluded evidence, output bindings, and family rubrics before
those runs can be frozen. The new runner support must use a new policy/runner
identity; it must not rewrite or relabel r19.

## Population accounting

The accepted corpus contains 24 cases in six families. The three child unlock
batches cover 16 cases: four feasibility, four premise-provenance, and eight
operation-definedness cases (four existence/defaults and four
operation-semantics). The remaining eight cases are four domain/quantifier and
four claim-trust cases. They remain in the full 24-case baseline and final
matched evaluation; they are not additional child unlocks. Task 2.2 owns their
measurement unless a separately reviewed plan assigns them earlier.

## Required work to close Task 1.3d

1. Keep the accepted feasibility profile bound to its existing policy and r19
   evidence.
2. Define each remaining family's exact command, request schema, source/formal
   identity, judgment kind, accepted evidence, control rubric, isolation
   exclusions and resource accounting. Preserve the distinction between
   operational search and supplied-proof validation.
3. Add versioned runner support and protocol regressions for those profiles,
   preserving the r19 entry point and artifacts unchanged.
4. Register all six families against the accepted corpus/runtime identities,
   label the registration post hoc relative to r18/r19, and obtain independent
   review before any newly registered batch runs.

Until these steps are accepted, Task 1.3d and semantic implementation unlocks
remain open. Shared-envelope design and child red-test preparation may continue
in parallel, but they do not bypass this gate.

## Current status addendum (2026-11-12)

Task 1.3d is complete. The [common registration](common-registration-v1.json) freezes all 24 case bindings, six family profiles, staged execution order, budgets, input separation and explicit isolation allowlist. Its [independent review](common-registration-review-v1.md) accepted the configuration after verifying corpus/runtime identity, command parsers, r19 compatibility and shared-module contents. The five non-feasibility profiles remain pending per-batch qualification; they are neither claimed as executed nor as proven unsupported.

## Correction (2026-11-12)

The v1 acceptance above is superseded for current decisions by the
[registration correction record](common-registration-correction-v1.md). A
read-only review found malformed wrapped argv, source-expression selectors
that the proof-slice API does not accept, and an incorrect case 03 rubric.
Task 1.3d is reopened. The proposed
[v2 registration](common-registration-v2.json) is a draft and has not passed
independent review. It registers an exact negative capability probe for case
03; that probe must execute under the preserved runtime and produce the
expected selector-name diagnostic before the case can be classified as
unsupported. No new premise-provenance batch may run under v1 or the current v2
draft.

## Accepted v2 configuration freeze (2026-11-12)

The reviewed [v2 registration](common-registration-v2.json) supersedes that
draft status. Independent review found no remaining configuration defect and
accepted it as a freeze; see [review v2](common-registration-review-v2.md).
Task 1.3d is complete. This does not qualify family execution: the five
non-feasibility profiles still require per-batch qualification, and case 03's
capability probe must run and receive independent review before it can support
an unsupported classification. No new family batch has been accepted, and no
Navier–Stokes exposition fault has been established.

## Case 03 probe contract correction (2026-11-12)

The first preserved-runtime probe observation is recorded in
[execution correction v2](common-registration-correction-v2.md). The selected
Lean helper emitted the exact registered diagnostic on stdout, while v2
required stderr. This is a contract mismatch; the case remains unresolved and
the probe receives no classification credit. The
[v3 registration](common-registration-v3.json) corrects the expected stream,
records the post-hoc chronology, and is pending independent review. The v2
configuration acceptance does not authorize interpreting this observation
under the revised contract.

At the v3 configuration-freeze checkpoint, no new family batch had been
accepted and the case 03 probe still needed its post-freeze run. The independent
v3 review is now complete; see
[review v3](common-registration-review-v3.md). Task 1.3d is closed on the
configuration freeze. The v2 case 03 observation remains post hoc and unscored;
run the exact v3 probe after the freeze before classifying that capability.
The other five non-feasibility profiles remain unqualified, and no new family
batch is accepted.

The post-freeze v3 case 03 probe has since been independently reviewed and
accepted for the narrow conclusion that this runtime's proof-slice API cannot
select the local binder by that selector. The
[probe review](qualification-runs/premise-provenance-v3-case-probe-20261112b/INDEPENDENT-REVIEW.md)
explicitly excludes route-absence, detection, and control credit. This does
not accept the premise-provenance family batch; cases 01, 02, and 04 remain
unmeasured.

## Premise-provenance family acceptance (2026-11-12)

The subsequent four-case batch is accepted under registration v3. See the
[current family acceptance index](family-baseline-acceptance-index-v1.json)
and [independent batch review](qualification-runs/premise-provenance-v3-family-20261112b/INDEPENDENT-REVIEW.md).
Cases 01, 02, and 04 produced complete slices supporting their registered
fault/control judgments. Case 03 remains unsupported only for the local-binder
selector API and gets no score credit. This accepts the premise-provenance
family batch; it does not accept either operation-definedness family or the
full 24-case baseline.

## Pending-profile defect found after v3 acceptance (2026-11-12)

An independent source/CLI audit found the v3 `source-goal-probe-v1` profiles for
`existence-defaults` and `operation-semantics` are not executable as registered:
they retain `<line>` and `<column>` placeholders and provide no per-case query
plans. The capture helper observes `TacticInfo` goals at a source position; it
does not query a declaration's type. Four existence/default subjects and
operation-semantics cases 01–02 are `def subject : Prop := ...`, so selecting
their declarations does not expose a proof goal of the represented proposition.
Operation-semantics cases 03–04 do contain theorem proof blocks, but their
capture positions and target-goal bindings are also absent from v3.

The independent audit is preserved in
[profile audit v3](common-registration-profile-audit-v3.md). No operation or
existence/default batch has run under this finding. Keep v3 and its accepted
feasibility/provenance records immutable, but do not execute or score the two
pending profiles under v3. Task 1.3e now requires a versioned correction that
binds exact proposition queries, source bytes and positions, polarities,
candidate tactic, imports, runtime and evidence interpretation. A failed proof
attempt remains unresolved; a fault claim requires a checked negation or
registered counterexample. The accepted premise-provenance batch and its v3
registration binding are unaffected.
