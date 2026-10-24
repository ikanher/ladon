# Proposal

## Why

Ladon now checks bounded rational refinement predicates in Python, but those checks have no Lean or ProofIR receipt and are not consumed by existing proof-probe routes. The application-probe pipeline can regenerate goals and bind trusted receipts, yet its current templates use a closed `Nat` context; adding branch IDs there would bind metadata without checking the rational semantics.

## What Changes

- Add an explicitly versioned rational-branch proof route that regenerates a Lean obligation from the validated bounded branch and exact assignment, using Mathlib only when the inspected workspace already provides it.
- Bind branch, source-span, base-goal, derived-goal, assignment, generated-goal and checker identities into the plan and checked receipt, including cache replay.
- Reconcile Python rational evaluation with Lean `Rat` behavior through differential tests, explicitly defining handling for division by zero and unsupported operations.
- Keep ordinary application probes unchanged and report only a checked result for the encoded rational assignment; this does not establish source-formula fidelity or theorem falsity.

See the [capability delta](specs/ladon-contract-probes/spec.md) for acceptance requirements.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `ladon-contract-probes`: add a separately versioned rational-branch obligation and exact replay contract.

## Impact

The likely integration surface is `proof_contract_probes`, its bounded worker and generated ProofIR artifact path. The new route must not widen the existing source-comparison templates or accept caller-written Lean goals. It may require a dedicated rational-to-Lean encoder and worker operation. The route reports unsupported when Mathlib's rational normalization tactics are unavailable in the exact Lean workspace; it adds no Ladon runtime dependency and no Quux dependency.
