## Why

Ladon already provides useful Lean repository topology and review routing, but
the alpha currently mixes strong evidence with verified false positives,
expensive Lean extraction, an unstable report contract, and a workspace-only
green test story. The next milestone should harden the existing product before
adding more analyzer families.

## What Changes

- Coordinate eight bounded child packets covering signal correctness, CLI
  execution semantics, Lean extraction runtime, elaborated declaration
  surfaces, report schema, clean-checkout gates, benchmarks, and OpenSpec state.
- Establish one shared public CLI contract whose commands, defaults, analysis,
  and output behavior are identical for every caller, whether the caller is a
  person, a script, or a model.
- Freeze new heuristic families until the existing promoted signals have
  positive/negative fixtures and measurable false-positive boundaries.
- Sequence foundational contract and correctness work ahead of deeper proof
  surface extraction and performance promotion.
- Define alpha exit criteria around trustworthy evidence, bounded resource use,
  deterministic reports, clean-clone reproducibility, and explicit failures.
- Exclude role-specific commands, prompt-oriented output paths, a UI, daemon,
  agent protocol, theorem proving, and automatic refactoring from this
  umbrella.

## Capabilities

### New Capabilities

- `ladon-alpha-hardening-program`: Cross-packet invariants, dependencies,
  readiness criteria, and scope boundaries for the alpha-hardening milestone.

### Modified Capabilities

None.

## Impact

- Affected change packets: eight new implementation/reconciliation children
  plus existing completed or stale OpenSpec packets referenced as evidence.
- Affected product surfaces: `ladon` CLI behavior, extraction backends, IR,
  analysis findings, report rendering, schemas, fixtures, packaging, CI, and
  project documentation.
- Affected compatibility: individual children may deliberately change finding
  counts, remove the no-op `--skip-build` flag, and introduce a versioned report
  contract; those breaks must be documented and tested.
