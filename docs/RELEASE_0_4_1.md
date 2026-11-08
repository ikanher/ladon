# Ladon 0.4.1 development snapshot

This internal snapshot adds complete stored theorem-lineage projections and
controlled capsule replay builds. It retains the shared **12 GiB** default
process-tree RSS ceiling (`--max-rss-mib 12288`) for planning and replay,
including `--build-policy ordered`. The earlier 6 GiB capsule failures used an
explicit experimental override; 6 GiB was never the product default.

## Changes

- `theorem lineage --view closure` returns selected stored nodes and typed edges
  independently of representative-route limits, with separate coverage and
  exact cap/count reporting. Route reachability now scales with unique graph
  work. See [lineage options](CLI.md#theorem-lineage).
- `theorem replay --build-policy ordered` and `theorem extract --verify
  --build-policy ordered` schedule project modules in dependency order under one
  shared build-stage deadline. Dependency preflights fail explicitly when the
  strategy cannot proceed safely. Default scheduling remains `lake-default`.
- Replay receipts include versioned policy, resource limits and bounded sampled
  process observations. Non-finite timeouts and oversized ordered-build graphs
  fail early. Existing content, isolation and final theorem/trust checks remain.

## Verification and limits

The implementation qualification passed 80 focused capsule, process-supervisor
and installed-CLI tests, plus scoped strict static checks and independent
review. New default-cap and version checks pass. See the
[implementation report](../openspec/changes/ladon-bounded-capsule-replay-builds/evidence/implementation/REPORT.md)
for measured scheduling results and large-capsule outcomes. This snapshot does
not claim a complete passing repository-wide gate or a verified replay of the
large research capsule. Ordered execution controls overlap; an individual
module may still exceed the cap or the build may exhaust its shared deadline.

No capsule/index migration or Lean toolchain upgrade is required. Earlier
contract-analysis and navigation changes are documented in the
[0.4.0 snapshot notes](RELEASE_0_4_0.md).
