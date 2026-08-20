## Context

Later packets change contracts, SQL access patterns, startup, storage, and Lean execution. A reproducible before-state is required to distinguish improvements from accidental drift.

## Goals / Non-Goals

**Goals:** reusable public-contract fixtures, SQL trace helpers, benchmark metadata, expected-failure reproductions, and portable commands.

**Non-Goals:** changing production behavior or setting absolute cross-host latency promises.

## Decisions

1. Store machine-readable baseline metadata with repository/toolchain identities and command lines.
2. Use fake helper payloads and compact SQLite fixtures for deterministic contract and SQL-count tests.
3. Mark known defects as expected failures tied to later packet IDs; never alter expected output to hide them.

## Risks / Trade-offs

- [Noisy benchmarks] → compare on one fingerprinted host and separate cold/warm phases.
- [Brittle snapshots] → assert semantic predicates and stable public fields, not incidental formatting.
