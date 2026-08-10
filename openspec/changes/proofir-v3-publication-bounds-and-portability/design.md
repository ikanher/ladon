## Context

Ladon's proof-search index already owns project-local build locking, `max_page_count`, fsync, and atomic replacement behavior. ProofIR should share that production primitive rather than evolve a second weaker publisher.

## Goals / Non-Goals

**Goals:** one writer per project database, explicit owner PID, bounded database growth, durable replacement, cleanup after failure, portable accounting, and semantic query-plan predicates.

**Non-Goals:** a global multi-project database, dependence on `dbstat`, exact SQLite plan strings, or migration of a partially published database.

## Decisions

1. Extract or reuse a Ladon-owned database publication primitive from `proof_search_index.py`; do not import research-project code.
2. Build locks live beside each project-local database and report the live/stale owner PID.
3. Set `PRAGMA max_page_count` from a positive `maxDatabaseBytes` before projection and verify allocated size before replacement.
4. Fsync the database, replace atomically, and fsync the containing directory where supported; failed builds preserve the previous database and remove only their owned temporary file/lock.
5. `dbstat` is optional enrichment. Plan gates inspect normalized access semantics such as required index/table and avoidance of forbidden scans, not exact prose.

## Risks / Trade-offs

- [Shared primitive refactor affects proof search] → preserve proof-search tests and add caller-specific adapters around one small storage helper.
- [SQLite platform differences] → test feature-present and feature-absent branches explicitly.

## Migration Plan

Freeze concurrent/crash/bound/feature red tests, extract the common publisher, adopt it in ProofIR, and retain a disposable rebuild-only database lifecycle.

## Open Questions

- None.
