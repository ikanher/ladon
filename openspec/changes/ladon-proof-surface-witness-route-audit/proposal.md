## Why

Pipeline-math shows a reusable Lean proof-governance pattern that current Ladon
only sees as generic `sorry` markers and import pressure: frozen spec stubs,
clean proof endpoints, no-drift identity gates, source pins, and axiom-audit
evidence. Ladon should consume that pattern as quoted proof-surface route
evidence so public claims cite proof-backed endpoints instead of frozen stubs,
without making Ladon a proof checker.

## What Changes

- Define a compact `proof-surface-witness` input contract for frozen spec
  surfaces, proof endpoints, no-drift gates, axiom audits, source pins, and
  allowed proof-hole quarantine.
- Extend route-authority auditing so claims can reference proof-surface witness
  endpoints and receive diagnostics when they cite a spec stub as authority,
  omit no-drift gates, omit axiom audits, or expose suspicious axioms.
- Add reviewer diagnostics:
  - `ladon.proof_surface.spec_stub_used_as_authority`
  - `ladon.proof_surface.missing_no_drift_gate`
  - `ladon.proof_surface.missing_axiom_audit`
  - `ladon.proof_surface.suspicious_axiom`
  - `ladon.proof_surface.clean_endpoint`
  - `ladon.proof_surface.frozen_spec_hub`
- Keep expensive Lean checks opt-in. Core Ladon consumes witness JSON; a later
  helper may generate that witness from `#print axioms`, `lake build`, and
  source hash checks.
- Add synthetic pipeline-math-style fixtures under `tests/fixtures` covering
  good endpoints, missing gates, stale pins, spec-stub overclaims, suspicious
  axiom footprints, and quarantined frozen `sorry` stubs.
- Render proof-surface audit summaries in bridge/reviewer output and atlas
  workflow rows as route-governance evidence only.

## Capabilities

### New Capabilities

- `ladon-proof-surface-witness-contract`: Defines the compact witness schema for
  spec stubs, proof endpoints, no-drift gates, axiom audits, source pins, and
  proof-hole quarantine metadata.
- `ladon-proof-surface-route-audit`: Audits proof-surface witness rows against
  claim routes and joined declaration/source evidence, producing
  proof-surface-specific authority diagnostics without deciding theorem truth.
- `ladon-proof-surface-fixtures`: Provides portable synthetic fixtures modeled
  on pipeline-math's `Theorems/Solution/Discharge` pattern.

### Modified Capabilities

None.

## Impact

- Affected code: ProofIR/proof witness input normalization, claim authority
  route audit, bridge reviewer-card output, atlas workflow summaries, benchmark
  oracles, report rendering, and optional CLI plumbing for witness input.
- Affected tests: new proof-surface witness fixtures, route-audit diagnostics,
  bridge output, atlas workflow rows, and benchmark-oracle checks.
- Affected trust model: source pins, no-drift gates, and axiom audits establish
  quoted route evidence and attachment confidence only. Ladon still does not
  validate theorem truth, proof correctness, witness adequacy, or mathematical
  scope.
