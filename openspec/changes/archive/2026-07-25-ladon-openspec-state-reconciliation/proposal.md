## Why

Immediately before the alpha-hardening umbrella was created, the OpenSpec
inventory reported nine active changes and 81 unchecked tasks. The umbrella and
its eight apply-ready children intentionally expand the live inventory to 18
active changes and 311 unchecked tasks. Seven of the nine pre-program packets
appear implemented, partly superseded, or stale, but each still needs
requirement-level evidence and residual transfer before disposition. Mixing
those legacy candidates with the new program would make the roadmap unreliable.

## What Changes

- Reconcile each active packet against source, tests, completed umbrellas, and
  replacement changes before changing its status.
- Classify the seven legacy candidates as complete, superseded-with-residuals,
  retained, or blocked, preserving requirement-level evidence for each choice.
- Deduplicate the remaining theorem-surface and Review Radar scopes as an
  explicit chain: the alpha declaration surface feeds a bounded theorem-surface
  changelog child, which can later feed a Review Radar MVP child under the
  retained planning umbrella.
- Repair completed packets that fail strict validation or lack required
  automation/validation metadata.
- Archive completed changes in reviewed batches so canonical specs are
  populated without silently overwriting conflicting requirements.
- Carry explicit modified deltas for legacy `ladon-python-quality` and
  `ladon-root-matrix` requirements so canonicalization replaces
  `--skip-build` with the no-build default instead of rewriting history.
- Correct current-state and roadmap documentation. Product-contract
  documentation remains owned by the CLI, report, runtime, declaration, signal,
  and reproducibility children that change those contracts.
- Add a repeatable state-audit gate that rejects unchecked tasks for already
  shipped work and invalid completed packets.

## Capabilities

### New Capabilities

- `ladon-openspec-state-reconciliation`: Evidence-backed status, archive,
  canonical-spec, and documentation hygiene for the Ladon change inventory.

### Modified Capabilities

- `ladon-python-quality`: Update the clean-core smoke scenario to use default
  no-build behavior after `--skip-build` is removed.
- `ladon-root-matrix`: Update text-backed project-root commands to omit
  `--build` rather than passing the removed `--skip-build` flag.
- `ladon-proof-xray-staging`: Require quoted trust-footprint witness rows to
  preserve backend, authority, source-artifact, and theorem-truth nonclaim
  metadata.

## Impact

- Affected artifacts: legacy active and completed OpenSpec changes, archive,
  canonical `openspec/specs`, automation metadata, current-state/roadmap docs,
  and backlog reports. The alpha dependency ledger remains authoritative for
  ordering the new program children.
- Affected workflow: implementation claims must point to source/test/gate
  evidence, and superseded work must name its replacement.
- This is metadata and documentation reconciliation; it does not implement the
  deferred Review Radar product lane.
