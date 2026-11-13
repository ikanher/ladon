# Internal stored-lineage query review — 2026-11-14

The review was supplied by the owner in chat; reviewer identity and reviewed
revision were not supplied. The motivating need is responsive, shared Ladon use
by multiple agents without granting stale results current-source authority.

## Confirmed implementation findings

`theorem_lineage_cli._run_lineage_command` performs comprehensive index status
with source verification, captures the repository again to construct identity,
then checks the selected closure. `proof_search_freshness._freshness_details`
captures twice for comparison and stability. The live path therefore makes three
captures before the selected-closure lookup. The third capture is independent
of the validated pair; identity should instead come from the validated snapshot.

Index status includes database counts, layout/schema diagnostics, source-delta
inventory, retained-history validation, Git visibility and dbstat accounting.
`history_status` calls `validate_history`, which hashes every registered historical
database. That is appropriate evidence for historical availability diagnostics,
but unrelated to reading one current closure. Historical lineage queries already
report historical association and withhold current freshness. Their integrity
checks must remain in the historical path.

## First stage measurement

The [profile](profile.json) measures one unchanged-code stored summary query on
the matrix-factorization index, using `--refresh never`. It returned available,
fresh, Lean-environment evidence. Total elapsed time was 61.174583 seconds;
full inspection took 58.430108 seconds inclusive. Three repository captures took
3.447689, 2.759765 and 2.738223 seconds (8.945677 total). Database counts took
0.279608 seconds, dbstat accounting 0.302970 seconds, and the selected-closure
lookup 0.000916 seconds. Inclusive inspection time overlaps its nested stages;
these are not additive independent costs.

Most inspection time was outside the initially timed sub-stages. The separate
[history timing](history-profile.json) measured **51.676250 seconds** validating
49 registered database snapshots totaling **47,917,117,440 bytes** (about
44.63 GiB). The implementation hashes all of those bytes for each status call.
That separate result is consistent with the first profile's uninstrumented
residual; it is not an exact disjoint decomposition of the same run. These
samples do not establish cold/warm performance, percentiles or general scaling.
[Source identity](SOURCE_IDENTITY.json) and the small
[result scope](QUERY_RESULT_SCOPE.json) bind the observation. No source, index
update, compiled extraction or production cache was performed by these probes.

## Recommendation and dispositions

Accept the separation of cheap closure lookup from comprehensive status as the
first implementation. Keep minimal schema/layout compatibility and a coherent
read transaction. A missing stored closure with refresh disabled needs no source
scan; report the absence without a current-freshness claim. Existing live closures
must still satisfy strict freshness and stability checks. Reuse the exact
validated snapshot rather than taking a third one.

Accept shared cache ownership in Ladon and caller-independent identity as design
principles. Defer persistent result caching until measuring the residual cost of
the simpler path. Shared validation across independent CLI processes requires
cross-process coordination, explicit snapshot authority, bounded wait/cancellation
and invalidation behavior. Reusing an in-flight result does not by itself prove
live freshness at the later caller's query time. Caller labels remain accounting
metadata, not trust or reuse keys. TTL, file metadata and watchers alone cannot
replace strict validation.

F.1–F.4 in the owning task ledger are the proposed bounded implementation and
measurement package. A public token interface and persistent cache remain
separate scope decisions. The earlier projection acceptance is unchanged.
