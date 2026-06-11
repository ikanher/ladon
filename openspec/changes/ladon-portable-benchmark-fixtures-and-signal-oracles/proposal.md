## Why

Ladon already has many structural and evidence-routing signals; the limiting
factor is proving which signals are reliable enough to influence review. A
portable benchmark and oracle layer is needed before adding more promoted
finding classes or making broader claims.

## What Changes

- Add a fixture corpus for promoted Ladon signals and adversarial negative
  cases.
- Add deterministic signal oracles that check focused outcomes instead of full
  JSON snapshots.
- Keep Quux, matrix-factorization, and mathlib as optional smoke targets rather
  than CI requirements.
- Establish the rule that new promoted findings need benchmark or oracle
  coverage.

## Capabilities

### New Capabilities

- `ladon-benchmark-oracles`: Defines portable fixtures and signal oracles for
  Ladon report findings, classification rows, and evidence checks.

### Modified Capabilities

None.

## Impact

- Affected code: tests, fixtures, optional new oracle module/script, and
  calibration regression helpers.
- Affected reports: no report schema changes required in this packet.
- Affected workflow: future feature packets should add oracle coverage before
  promoting new findings.
