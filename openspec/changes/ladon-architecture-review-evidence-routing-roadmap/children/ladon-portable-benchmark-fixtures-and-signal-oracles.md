# Child Packet: ladon-portable-benchmark-fixtures-and-signal-oracles

## Purpose

Create a portable fixture and oracle layer for promoted Ladon signals before
new heuristic findings are added.

## Expected Scope

- Synthetic Lean fixtures for import pressure, root-scope classes, duplicate
  declaration basenames, scoped/open syntax, local binder and field-like
  reference noise, repeated proof families, and broad facade imports.
- Synthetic packet/evidence fixtures for present, partial, missing, and stale
  evidence profiles.
- A deterministic oracle evaluator over report payloads or focused signal rows.
- CI-safe tests that do not require Quux, matrix-factorization, mathlib, or
  sibling repositories.

## Non-Goals

- No exact full-report snapshots.
- No external repo dependency in CI.
- No new promoted finding classes before oracles exist.
