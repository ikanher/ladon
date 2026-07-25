## Context

Matrix-Factorization exposed three scale costs in the current ordinary CLI:
three serialized copies of the module payload, repeated full-inventory parsing,
and no portable large-project gate. This child owns the scale foundation while
leaving report dispatch, CLI process behavior, and benchmark measurement with
their existing capability owners.

## Decisions

### Use a versioned reusable source index

The index records normalized module/path identity, imports, source hashes,
lexical declaration summaries, effective policy identity, and a format version.
Cache entries are atomically published and reused only after every registered
fingerprint input agrees. The default cache uses the platform user-cache
directory under `ladon`; `--cache-dir` overrides it.

### Introduce canonical report v3 projections

Report v3 owns each payload once under a canonical section. Phase and legacy
timing views retain scalar status and a payload reference, never a copied
payload. `summary`, `review`, and `full` projections record omissions and a
source-analysis fingerprint. `review` becomes the default when v3 is promoted.

Report v2 remains readable. Explicit v2 writing remains available for the first
two Ladon minor releases after v3 promotion and warns about its duplication
cost. The third minor may remove v2 writing, but not reading.

### Gate scale on a generated portable repository

The fixture is generated from a tracked manifest in disposable storage. The
Ubuntu 24.04 x86-64 reference job exposes four CPU cores and runs all supported
Python minors. Three cold and three warm samples must each satisfy the
committed ceilings; infrastructure reruns do not inflate those ceilings.

## Existing Owners And Exclusions

- `ladon-report-contract-v2` retains old-version reader authority.
- `ladon-cli-execution-contract` retains stream and exit behavior.
- `ladon-signal-benchmark-harness` retains process/resource measurement.
- This child does not add findings, choose mathematical roots, change Lean
  helper semantics, or embed Matrix-Factorization-specific policy.

## Risks

- A stale index could hide source changes. Strong content/layout/policy
  fingerprints and atomic publication make reuse fail closed.
- v3 may strand in-repository readers. Promotion is blocked until parity tests
  pass and the explicit v2 adapter remains available.
- CI resource noise may obscure regressions. Exact samples and reference-image
  identity are recorded separately from semantic determinism.
