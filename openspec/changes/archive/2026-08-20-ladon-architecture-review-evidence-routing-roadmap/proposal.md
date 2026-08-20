## Why

External review framed Ladon's strongest posture as a Lean architecture review
and evidence-routing assistant, not a theorem-truth authority. The project needs
a roadmap umbrella that turns that posture into ordered OpenSpec work before
more heuristic findings are added.

## What Changes

- Define the 6-18 month product posture: Ladon routes human review and evidence,
  and never validates theorem truth.
- Order the next implementation packets around benchmark credibility, source
  evidence contracts, and atlas-first reviewer workflows.
- Add child packet briefs for:
  - `ladon-portable-benchmark-fixtures-and-signal-oracles`
  - `ladon-declaration-table-source-evidence-contract`
  - `ladon-atlas-review-workflow-and-bridge-cards`
- Record stop/defer guidance: no new heuristic finding classes before benchmark
  oracles, no full proof-dependency engine in Ladon, and no Rust rewrite before
  workload profiles justify it.

## Capabilities

### New Capabilities

- `ladon-evidence-routing-roadmap`: Governs Ladon's roadmap posture, child
  packet order, trust-boundary language, and future-direction gates.

### Modified Capabilities

None.

## Impact

- Affected artifacts: OpenSpec roadmap, child packet briefs, future tasks, and
  trust-boundary documentation.
- Affected code: none in this umbrella directly; implementation happens in child
  packets.
- Affected workflow: future Ladon feature proposals should explain whether they
  strengthen benchmark evidence, source-evidence contracts, atlas review
  workflow, or an explicitly deferred direction.
