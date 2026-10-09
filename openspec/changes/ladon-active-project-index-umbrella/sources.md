# Sources and finding ownership

## Frozen input

- Source: [FIRST-HAND-REPORT.md](../../../FIRST-HAND-REPORT.md).
- Report SHA-256 at planning: `15e5a7256f1fc777c6803acb0d87df9f500e1050c60f2e39e12f6baa37512a96`.
- Inspection baseline: Ladon commit `a073eadc3d6204f80f87a8eacc6e43d3797b46b5`; report has user edits in the working tree. Those edits are preserved.
- August sections report historical sessions. The October 8 section identifies the installed commit and a concurrently changing source tree. No new real-project run or 18 GB directory audit has been performed. The historical 93-second benchmark has not been renewed; the r01 portable workload is a different population.

## Planning finding disposition (historical)

| Report finding | Observed current evidence / limitation | Authoritative next action |
| --- | --- | --- |
| Stale identifier returns unrelated hits; stored mode is easy to miss | `proof_search_index.query_proof_search_index` returns freshness plus rows; text header shows the label but no exact-miss summary. CLI name search defaults to verify. | New freshness-diagnostics capability, tasks 1.1 and 2.1–2.4. |
| No added/changed/removed source detail | Snapshot holds source hashes and SQLite modules store source hashes; `_freshness` returns only a status and current identity. | New freshness-diagnostics capability. |
| Incremental refresh absent | `proof_search_cli` index routes expose build/status/query; build extracts a whole new database. | New incremental capability, group 3, with feasibility/cost gate. |
| Private indexes accumulate | Shared publisher uses persistent kernel locks; inactive lock files are intentional and cannot be classified as orphaned by age. No list/prune route found. Report's disk population is not remeasured. | New lifecycle capability, group 4; no cleanup during planning. |
| Two generation identities | Snapshot derives current inputs; stored identity identifies returned rows. They are not two published indexes. | Documentation and additive diagnostics in group 2. |
| August immediate stale-configuration discrepancy | Current `_freshness` compares live configuration and source fingerprints; existing test covers fresh then stale source. Report shows stored fingerprints, not the separate live value. Root cause remains unconfirmed. | Task 1.2 reproduction; only reproduced identity defects enter group 2. |
| Lineage size policy and missing terminal/warm results | Later report records improvement. Existing storage/publication owner has 16/17 tasks checked; interruption tests remain unchecked. Warm-summary implementation is archived. | [Storage/publication owner](../ladon-lineage-storage-budget-and-publication/tasks.md); task 1.3 verifies residuals, no duplicate feature scope. |
| Consumers and constructor report false completeness | Current consumers invokes coverage evaluator; constructor distinguishes absent field population. Existing owner still has unchecked fixture tasks. Source inspection is not new qualification. | [Coverage owner](../ladon-coverage-sensitive-consumers-and-constructors/tasks.md); verify partial/empty/truncation cases and route residuals there. |
| Explain rejects binder-bearing conclusion | Existing binder-aware owner implements conservative parsing and indeterminate states but has unchecked evidence/normalization tasks. | [Binder owner](../ladon-binder-aware-proof-difference/tasks.md); task 1.3 confirms actual CLI behavior. |
| Generic any ranking and verbose owner reports | Query owner already has generic-token policy and minimum matched segments; ranking/projection owner claims implementation with unchecked quality fixtures. | [Ranking/projection owner](../ladon-proof-search-ranking-and-owner-projection/tasks.md); preserve Boolean semantics and verify reported examples. |
| All-term prose query returns nothing | Expected all-term semantics can exclude a useful declaration; automatic term dropping would alter the query. | Document explicit any/minimum-segment alternatives. Automatic relaxation or new ranking modes deferred pending reproduced need after current controls. |
| Verbose routine index status | Status emits per-object schema/accounting fields; these remain useful audit data. | Compact text and explicit details in group 2; preserve JSON compatibility. |
| Old 512 MiB budget and suggested split databases | Current base default is 1 GiB; later report accepts roughly 775 MB. Existing owner separates base and total ceilings. | Verify current budget docs in task 1.3. Splitting stores and lineage deduplication deferred; no evidence here establishes need. |
| Skill uses old flags | External skill was updated earlier; report refers to different copies at different times. | Validate actual maintained and target-installed instructions before declaring current mismatch; group 2/4 docs own new examples. |

The older [first-hand hardening umbrella](../ladon-first-hand-proof-search-hardening-umbrella/tasks.md) has implementation groups marked complete while some child acceptance tasks remain open. This plan preserves that history and requires evidence-backed disposition; it does not automatically mark older work done or inherit its entire operational-release backlog.

## Implementation and verification pointers

- `src/ladon/proof_search_index.py`: snapshot capture, module ingestion, query metadata, status, freshness and atomic full build.
- `src/ladon/proof_search_query.py`, `proof_search_name_query.py`: exact lookup, segmentation, scope and ranked lexical fallback.
- `src/ladon/proof_search_cli.py`: index commands and text projection.
- `src/ladon/proof_search_schema.py`, `sqlite_publication.py`: stored source hashes, ownership and durable publication. Persistent locks intentionally survive release.
- `tests/test_proof_search_index.py`, `test_proof_search_name_v2.py`: freshness, preservation on failure, exact lookup and current query contract.
- `tests/test_proof_search_consumers.py`, `test_proof_search_constructor.py`: existing coverage regression entry points.
- Archived `ladon-proof-search-name-v2-and-freshness` delta: exact-name behavior, explicit query operators and identity-bearing freshness remain applicable.
- Canonical `ladon-pipeline` and `ladon-openspec-state-reconciliation`: additive compatibility, portable fixtures and evidence-backed status/ownership remain applicable. No canonical freshness/update/lifecycle capability currently exists.

## Acceptance record

The current implementation and verification are recorded in [r01 evidence](evidence/r01/REPORT.md), with source hashes in [candidate-hashes.json](evidence/r01/candidate-hashes.json). The planning table above preserves the pre-implementation routing; the current disposition is:

| Finding | Current disposition |
| --- | --- |
| Stale exact miss, missing source delta, unclear identities and verbose status | Addressed by bounded source comparisons, exact/fallback summaries and compact text. Portable and installed smoke cover untracked add, edit, fresh update and cleanup; stable build/status and source-race tests cover identity. |
| Incremental refresh and accumulated private indexes | Addressed for compatible lexical generations and explicitly selected disposable private indexes. The five-pair portable workload clears the preselected cost gate. The reported real-project storage population was neither inspected nor pruned. |
| August immediate stale-configuration discrepancy | Not reproduced by stable, configuration-change or source-race fixtures. Its historical cause remains unknown. |
| Lineage budget/interruption, consumers, constructors, binder explain and ranking/owner projection | Relevant maintained tests passed in the full suite. Existing owner links above retain their unchecked acceptance work; this change does not promote those historical claims. |
| All-term prose query, split stores and lineage deduplication | Explicitly deferred. Current all/any/phrase semantics and the 1 GiB default remain; no automatic query relaxation or storage split was introduced. |
| Skills and routine examples | Repo and adjacent maintained Ladon skill instructions were updated for status/update/list/prune. A wheel-installed active-editing smoke passed on Python 3.11 and 3.12. |

The full strict quality result and any remaining limitations are in the r01 report. No external mathematical checkout was mutated.
