# V.1a: bounded shared-generation batch search

Implemented in the post-0.4.3 working tree on 2026-11-17. The parent V.1 remains
open for persistent cross-process reuse; this delivers its bounded batch route.
There is no package bump, commit, push, new dependency or SQLite schema migration.

`proof-search search batch --repo-root REPO --queries queries.json --format json`
accepts ordinary name/type-text argument lists. One read transaction binds all
query rows and metadata. Two source/configuration/toolchain captures bracket the
batch, and the active index generation is observed at the end. The existing
query engines and scope rules are reused; field/unit results match standalone
search rows. No agent identifier is part of query identity.

Stale initial inputs avoid query execution. Source or configuration/toolchain
changes during queries withhold all rows and identify observed changes. A writer
can atomically replace the active index while the reader finishes its old
transaction; the batch cannot mix generations. A final generation mismatch also
withholds results. Foreign worktrees and unsupported schemas reject. The normal
publication lock remains owned by writers; batch reads do not create an index
copy or run an updater/Lean process.

Bounds: 64 KiB input, 1–32 queries, at most 32 option/value pairs per query,
4096 characters per value and 100 result rows per query. Pretty JSON output
is bounded to 1 MiB by default, configurable to 16 MiB. Input or output bound
failure produces a diagnostic before a successful result file is published.
Results include source/configuration/toolchain/helper/schema, repository/index,
row-generation identities and capture count. Name result items have a separate
batch schema; type-text items retain shortlist fields plus batch validation.
Neither gains Lean proof authority from source freshness.

## Verification

`batch-integration-final.txt`: 127 tests pass in 4.90 seconds across batch bounds,
source/configuration changes, generation replacement, concurrent updater use,
standalone parity, foreign/missing indexes, update timings, default/explicit
history, cleanup recovery and search consumers. Before implementation the two
initial batch tests failed. Field results/capture count are checked separately.
Repository Ruff, scoped strict complexity/dead-code checks, strict OpenSpec and
both skills validate. No full suite, installed qualification or independent audit
was repeated. The production hashes are recorded in BATCH-VERIFICATION.json.

A read-only MF exercise returned identical rows and generations: name 5.658 s,
type-text 5.749 s, batch 5.834 s for the same two queries using two captures total.
This single sequential observation has uncontrolled cache/order effects and
preceded the final added schema-layout guard; it is not a general speedup claim.
The final guard and other final code are tested in the 127-test run. No source or
index mutation was performed by the exercise. No historical capsule memory run
was attempted.

## Remaining boundary

A saved batch result can be shared with workers as evidence from its observation
window. It cannot authorize later live queries without new validation. Two source
captures detect observed differences, not edits reverted between captures or
changes after the final observation. Persistent tokens/watchers and dynamically
arriving cross-process requests need their own invalidation/observation contract.
The next decision is whether the delivered grouping route suffices in actual
agent work before building a service or cache. Preserve the honest V.1 open
status; do not equate V.1a with automatic live-freshness reuse.
