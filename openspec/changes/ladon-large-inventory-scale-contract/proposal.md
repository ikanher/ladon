## Why

The first live large-repository trial found that a 2,611-module inventory took
about 53 seconds, full JSON reached 218 MB, and report construction peaked near
1.6 GiB because the same module payload was serialized repeatedly. Later scope,
runset, and report-set work needs a bounded, reusable inventory foundation
instead of carrying those costs into every command.

## What Changes

- Add a portable generated large-project fixture and required cold/warm time,
  RSS, output-size, determinism, and invalidation gates.
- Build one versioned reusable source index with inspectable cache decisions.
- Give every large report payload one canonical owner and replace duplicated
  alpha-v2 payload locations with stable references and a compatibility path.
- Add explicit `summary`, `review`, and `full` report projections with honest
  omission metadata and streaming or otherwise bounded serialization.
- Reuse report version dispatch from `ladon-report-contract-v2`, process and
  channel behavior from `ladon-cli-execution-contract`, and resource
  measurement from `ladon-signal-benchmark-harness`.
- Keep Matrix-Factorization as optional fingerprinted acceptance evidence, not
  required CI input or a source of hard-coded product policy.

## Capabilities

### New Capabilities

- `ladon-large-inventory-scale-contract`: Portable scale budgets, reusable
  source indexing, single report-payload ownership, bounded projections, and
  compatibility behavior for large inventories.

### Modified Capabilities

None. Existing report, CLI, and benchmark contracts remain authoritative.

## Impact

- Affected code: source discovery/indexing, report assembly, projection,
  serialization, text rendering, compatibility adapters, and portable fixtures.
- Downstream changes enabled: `ladon-analysis-root-and-scope-contract`,
  `ladon-analysis-runsets-and-bundles`, and
  `ladon-installed-reportset-workflow`.
- Excluded work: new finding kinds, Lean helper semantics, automatic root
  choice, target-specific generated rules, or mandatory sibling-repository CI.
- The public behavior remains the same ordinary CLI contract for people,
  scripts, editors, and models; no caller-specific command or threshold is
  introduced.
