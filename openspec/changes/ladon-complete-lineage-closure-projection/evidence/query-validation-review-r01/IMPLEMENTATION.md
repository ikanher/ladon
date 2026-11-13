# Stored-lineage query validation repair

The live lineage path now opens the existing index without creating a missing
database, validates its supported schema/layout, and looks up the selected
closure before source capture. A missing closure under `--refresh never` returns
`not_ingested` with zero repository captures. Existing closures are validated
with two source captures; an unstable pair fails closed. The first validated
snapshot supplies identity, removing the former independent third capture.

Full status diagnostics remain available through `proof-search index status`.
They are no longer a dependency of ordinary lineage queries. In particular,
ordinary queries do not hash all registered historical database snapshots.
Historical selection keeps its existing integrity validation and historical
freshness semantics.

Metadata, closure selection and projection share one SQLite read transaction.
Refresh-capable commands retain publication ownership, release the read
transaction before planning/ingestion, reject source or index-identity changes
during planning, and begin a read transaction after successful ingestion. This
preserves the ingester's own `BEGIN IMMEDIATE` and avoids nested transactions.

## Verification

The initial new tests failed on the old path's source scan for an absent closure,
comprehensive diagnostics for a present closure, and unstable-source outcome.
The final affected command was:

```
uv run --locked pytest -q tests/test_theorem_lineage*.py tests/test_index_history*.py tests/test_result_lineage*.py
```

It passed **145 tests**, including 22 new validation cases. These cover zero/two
capture counts; stale source/configuration/toolchain identities; source
instability; missing, corrupt or incompatible indexes; coherent reads across a
concurrent WAL publication; refresh after preflight; rejection of source/index
changes while planning; and read-only results across all seven stored views.
The affected existing tests retain historical, projection, receipt, byte-limit,
publication and consumer behavior. No Lean extraction was needed for this
Python/SQLite orchestration change.

Scoped Ruff passes. Scoped Radon reports no C-or-worse functions in the modified
CLI, new validation helper or new tests. The full `python_quality.py --strict`
command still fails on the same ten existing real-bound source/test complexity
findings; the retained log records those unrelated files. No acceptance policy
was relaxed. No independent-review claim is made.

## Field measurements

| Request | Before | After | Captures before/after |
| --- | ---: | ---: | ---: |
| Existing stored summary | 61.174583 s | 5.703910 s | 3 / 2 |
| Absent stored closure | 61.845867 s | 0.009100 s | 3 / 0 |

Both final result JSONs equal their baseline payloads after removing only
`elapsedSeconds` and `acquisitionElapsedSeconds`. Full results and stage profiles
are retained alongside this report; `IMPLEMENTATION_IDENTITY.json` binds final
implementation/test bytes. The baseline review's separate 51.68-second history
check hashed 49 archived databases totaling 44.63 GiB. Removing that unrelated
work explains the main improvement. These are single local observations, without
cold/warm classification or percentile/general-scaling claims. Source comparison
and existing evidence identity checks still establish the current result; no
cached timestamps or metadata shortcuts provide authority.

## Remaining work

Strict live validation still costs about 5.7 seconds on this repository. Shared
validated snapshots may help repeated independent callers, but need a separate
cross-process lifecycle and explicit snapshot-authority contract. This repair
adds no persistent query cache, snapshot token, database migration, CLI option
or agent-specific behavior. The earlier 0.4.2 release qualification remains
bound to its original production sources.
