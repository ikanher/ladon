## 1. Freeze publication failures

- [ ] 1.1 Add two concurrent builders for one project database; require one owner PID and one fail-fast conflict without destination damage.
- [ ] 1.2 Add stale-lock recovery, process/build failure, integrity failure, page-limit exhaustion, replacement interruption, and temporary-file cleanup cases.
- [ ] 1.3 Add databases just below/above `maxDatabaseBytes` and queries at positive cap boundaries.
- [ ] 1.4 Run storage accounting and plan gates with `dbstat` available and unavailable and with varied normalized `EXPLAIN QUERY PLAN` details.

## 2. Consolidate the publisher

- [x] 2.1 Extract a small Ladon-owned project-database publication helper from the proof-search implementation or make its existing helper safely reusable.
- [x] 2.2 Acquire/release the same-directory PID lock, create an owner-specific temporary database, configure foreign keys and `max_page_count`, and preserve the old destination on every failure.
- [x] 2.3 Run integrity/foreign-key checks and size accounting before fsync, atomic replace, and directory sync.
- [x] 2.4 Make `dbstat` optional and return an explicit availability marker plus portable page-size/page-count accounting.
- [x] 2.5 Replace exact-plan-text assumptions with predicates over normalized access paths and required indexes.

## 3. Prove the exit class

- [ ] 3.1 Run ProofIR and proof-search publication regressions, concurrent/stale lock tests, crash mutations, page/database/query limits, integrity checks, and feature matrices.
- [ ] 3.2 Verify every build artifact is project-local and names its database, temporary path policy, lock path, owner PID, and configured bounds.
- [x] 3.3 Document database rebuild/disposal, concurrency, resource, and portability guarantees.

## 4. r03 reopening: ownership-safe lock lifecycle

- [x] 4.1 Add an unpredictable owner token and retained file/inode identity to every lock acquisition result.
- [x] 4.2 Replace unconditional cleanup with compare-and-delete that removes the path only when token and file identity still belong to the current build.
- [ ] 4.3 Replace stale-owner unlink/retry with an atomic claim/rename or equivalent compare-and-delete protocol that cannot remove a newly acquired lock.
- [ ] 4.4 Add deterministic races for competitor replacement before cleanup, stale owner replacement, PID reuse, malformed lock replacement, and interruption before/after destination replacement.
- [ ] 4.5 Verify the winning database and competing lock survive every losing-writer cleanup path; retain `partial` until the full concurrency/crash matrix passes.
