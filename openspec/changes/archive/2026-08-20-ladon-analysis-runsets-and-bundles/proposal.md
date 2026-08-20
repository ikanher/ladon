## Why

Large Lean projects often have several coherent review roots. Re-running a
full analysis manually for each root wastes discovery work, loses failure
isolation, and provides no durable record of which reports belong together.

## What Changes

- Add a generic versioned runset manifest for ordinary analysis entries,
  explicit dependencies, resource policy, outputs, and fingerprints.
- Execute serially by default, share only sound indexes/caches, and retain one
  canonical report per root instead of merging report authority.
- Produce a deterministic relative-path bundle manifest with report
  backreferences, per-entry status, and completeness.
- Add fingerprinted resume, selective invalidation, failure isolation, and
  cancellation cleanup through existing analysis and supervisor contracts.
- Consume large-inventory reuse, explicit scope plans, and partial-run
  diagnostics; reuse `ladon-cli-execution-contract` and
  `ladon-report-contract-v2`.

## Capabilities

### New Capabilities

- `ladon-analysis-runsets-and-bundles`: Versioned multi-analysis plans,
  resumable isolated execution, and deterministic report bundles.

### Modified Capabilities

None. The runset orchestrates ordinary analyses and does not create another
analyzer or merged multi-root report format.

## Impact

- Start after `ladon-large-inventory-scale-contract`,
  `ladon-analysis-root-and-scope-contract`, and
  `ladon-partial-run-observability`.
- Affected code: manifest models/schema, CLI dispatch, run orchestration,
  fingerprinting, resume state, bundle serialization, and fixtures.
- Downstream change enabled: `ladon-installed-reportset-workflow`.
- Excluded work: caller-specific defaults, built-in sibling-repository
  matrices, implicit Git-ref orchestration, and merged multi-root authority.
