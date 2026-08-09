## Context

Base construction enforces `maxIndexBytes`, but lineage ingestion receives no limit from the CLI. Ingestion is already transactional and has an optional byte check; the packet must turn that primitive into an explicit complete-database policy and add statistics/output lifecycle behavior.

## Goals / Non-Goals

**Goals:** enforce two budgets, preserve active closures on failure, refresh statistics, expose phase/marginal evidence, and guarantee terminal/atomic output.

**Non-Goals:** exact pre-insert byte prediction, automatic vacuuming, or allocating the configured maximum eagerly.

## Decisions

1. Persist `baseBuildMaxBytes` and `completeDatabaseMaxBytes` separately. Keep 512 MiB as the base default and expose 1536 MiB as the documented large-repository complete budget, configurable per build/refresh policy.
2. Use a cheap row/average estimate only for early rejection; the authoritative size check remains inside the transaction after insertion.
3. Run targeted `ANALYZE`/optimization for mutated lineage tables before plan validation and commit. Base-only optimization was rejected as stale after mutable writes.
4. Send human progress to stderr and exactly one versioned terminal result to the selected result channel. Use the shared atomic writer for files.

## Risks / Trade-offs

- [ANALYZE increases refresh time] → target only changed tables and measure separately.
- [A 1536 MiB recommendation is too broad] → keep it explicit/configurable and report policy source; do not silently raise stored limits.

## Migration Plan

Bump metadata contract, default old databases to incompatible/rebuild, wire budgets through CLI/store, then add failure injection. Stored Lean closures are disposable.

## Open Questions

- Whether complete-budget policy belongs in repository config or only CLI metadata after the first release.
