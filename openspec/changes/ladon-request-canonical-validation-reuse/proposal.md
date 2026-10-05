# Proposal

## Why

The retained 89-artifact inspection validates 25 check/environment pairs after
complete catalog validation, preparing 164 envelopes. The returned r07 review
authorizes a bounded attempt to reuse canonical preparation without changing
accepted evidence or any receipt/execution-specific decision.

## What Changes

- Retain an internal canonical-owner-controlled population for one request.
- Validate exactly the same subsets from already owned canonical artifacts,
  preserving occurrence bounds, ambiguity and reference closure.
- Integrate private reuse through dossier/receipt owners; raw APIs stay validating.
- Characterize security/compatibility boundaries before implementation, qualify
  changed shared owners, and retain only if the frozen cost gate passes.
- Correct the active product scope; mathematical adoption is not a prerequisite.

## Capabilities

### New Capabilities

None. This pure maintenance refactor opts out of delta specs (`skip_specs: true`).

### Modified Capabilities

None. Native canonicalization/identity/reference and evidence contracts remain
unchanged; design owns this package's frozen measurement and rollback criteria.

## Impact

Canonical population/reference preparation, dossier resolution, stored receipt
and execution-binding private paths; tests and docs. No command, schema, public
signature, persistent cache, database, dependency or Lean-operation changes.
