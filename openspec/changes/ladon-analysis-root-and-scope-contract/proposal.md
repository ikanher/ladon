## Why

Selecting one owner currently still causes a full-inventory scan and global
review surface. Ladon needs an explicit, previewable distinction between the
requested root and the population that will actually be analyzed.

## What Changes

- Add deterministic owner, local import-closure, namespace, named multi-root,
  caller-supplied changed-set, and full-inventory scope plans.
- Add a side-effect-free preview that reports selected, omitted, and truncated
  populations, expected helper batches, policies, limits, and fingerprints.
- Record scope identity and completeness in reports so omitted modules never
  appear observed clean.
- Consume the reusable source index from
  `ladon-large-inventory-scale-contract` after that milestone is available.
- Reuse process and invocation behavior from `ladon-cli-execution-contract`,
  report representation from `ladon-report-contract-v2`, and partial-state
  behavior from `ladon-partial-run-observability`.

## Capabilities

### New Capabilities

- `ladon-analysis-root-and-scope-contract`: Non-executing scope planning and
  exact population contracts for owner, closure, namespace, multi-root,
  changed-set, and inventory analysis.

### Modified Capabilities

None. The change composes existing CLI/report contracts and does not redefine
analysis authority.

## Impact

- Start after `ladon-large-inventory-scale-contract` and
  `ladon-partial-run-observability`.
- Affected code: scope models, index queries, CLI preview/selection options,
  report provenance, helper planning, and portable fixtures.
- Downstream changes enabled: actionable findings, runsets, and bounded audit
  resolution.
- Excluded work: mathematical relevance inference, implicit VCS commands,
  merged multi-root reports, proof-dependency closure, or hard-coded roots.
- Changed-set input is an explicit path list or versioned manifest; Ladon does
  not run Git to discover it.
