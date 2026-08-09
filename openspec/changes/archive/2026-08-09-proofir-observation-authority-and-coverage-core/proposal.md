## Why

Producer assertion, checker acceptance, source freshness, attachment confidence, replay relationship, and coverage are currently expressed through overlapping free-form fields that cannot be safely composed.

## What Changes

- Introduce one typed observation model over typed subjects and exact environments.
- Separate assertion state, validation outcome, freshness, attachment result, replay relationship, authority basis, and guarantee scope.
- Make checker runs observations with exact inputs, subjects, results, bounds, and output digests.
- Make coverage local to a named population and selector with expected, observed, omitted, and bounded counts.
- Give limitations stable identifiers in addition to human-readable nonclaims.

## Capabilities

### New Capabilities
- `proofir-observation-authority-and-coverage-core`: Typed evidence observations and local coverage semantics.

### Modified Capabilities

## Impact

Touches claims, replay provenance, checker witnesses, coverage queries, theorem dossiers, triage, and public evidence schemas.
