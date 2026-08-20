## Why

Review signals should be promoted only after portable fixtures prove their
positive behavior and false-positive boundaries. Private smoke runs are useful
but not enough for CI reliability.

## What Changes

- Add portable benchmark fixtures for architecture, source-pattern,
  claim-authority, common-layer, facade, and generated signals.
- Add oracle checks that validate semantic predicates rather than brittle whole
  JSON snapshots.
- Keep Matrix-Factorization and Quux smoke evidence optional.

## Capabilities

### New Capabilities

- `ladon-review-signal-benchmarks`: Portable review-signal fixtures and oracle
  checks.

### Modified Capabilities

None.

## Impact

- Affected code: benchmark fixtures, oracle scripts/tests, docs.

## Reconciliation Disposition

The portable predicate-oracle foundation is shipped. Complete positive and
intentional-negative coverage for source-pattern and claim-authority
boundaries, together with metric-family and live-drift policy, is transferred
to `ladon-signal-benchmark-harness`. This packet is preserved as
superseded-with-residuals and does not define a second benchmark authority.
