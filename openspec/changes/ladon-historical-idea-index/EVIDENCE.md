# Acceptance evidence

The implemented change passes its declared preservation gates. The live shared
matrix-factorization index and the installed global Ladon command were not
replaced. Qualification migrated independent SQLite backups only. The updated
checkout exposes the commands documented in `docs/HISTORICAL_IDEAS.md`.

## Baseline and sequence

- Original commit: `bb88c05f705aef7b52957d15942f6a2b33bf7cad`.
- Original tracked tree: clean; unrelated untracked `100000-node` and `8` retained.
- Metrics were tested first: recorded import failure, then 12 passing tests.
  Two additional structural controls initially failed, then passed after the
  metric learned to detect removed foreign keys/indexes. No failing control
  was interpreted as successful migration evidence.
- The complete proposal/specification/design/tasks packet passed
  `openspec validate ladon-historical-idea-index --strict` before schema edits.

## Demonstrated preservation

The real index copy contained **265,961 declarations, 9,618 modules and 238,899
symbols**, with an original allocation of **856,420,352 bytes**. The final
migration took **31.79 seconds**, including validation and full preservation
measurement. See [the complete report](evidence/real-index-report.json).

| Gate | Result |
|---|---:|
| Hard violations | 0 |
| Protected old tables | 69/69 preserved |
| Foreign-key-bearing table invariants | 55/55 preserved |
| Ordered SQL observations | 5/5 preserved |
| Public name-query result arrays | 3/3 identical |
| File size ratio | 1.00010044 (about +0.01004%) |

All old rows and table definitions, indexes, views and triggers are compared;
only the three exact physical-schema metadata substitutions are allowed.
Data/link/query loss fractions are each zero. They count failed invariants,
not lost theorem percentages. The five SQL observations include empty dependency
and lineage tables in this particular real index. **Nonempty lineage coverage
comes from the separate semantic fixture**: three nodes, two edges, trust data,
identity/freshness and complete stored query (excluding elapsed time) survive.
No Lean execution or new mathematical verification is claimed.

## Timing review

The sequential nine-sample type-text median ratio was 1.2558, slightly above the
predeclared 1.25 review threshold. We retained that result and ran one balanced
follow-up: 51 alternating before/after pairs, five query executions per sample,
five warmups, unchanged SQL and query plans. The name/type-text median ratios
were **1.0229 and 1.0211**, respectively; all plans were identical. The other
observations return empty rows and take microseconds, so they do not establish
nonempty graph-query performance. These bounded observations support acceptance
of this migration, not a general performance claim. Raw samples are retained in
[the timing review](evidence/timing-review.json).

## Tests and quality

- **138 affected regression tests passed**: historical catalogue, migration,
  adversarial metrics, name/type queries, index refresh/history, stored lineage
  and atomic publication. See [test output](evidence/regression-results.txt).
- Tests include cyclic and malformed catalogues, selected attribution conflicts,
  stale/missing/ambiguous links, rebuild reproducibility, missing-file retention,
  a populated lineage migration, locked destination, missing database,
  pre-replacement failure and post-replacement durability uncertainty.
- Scoped Ruff and strict complexity/maintainability/dead-code checks passed for
  all changed Python files; see [quality coverage](evidence/quality-report.json).
- OpenSpec strict validation and `git diff --check` passed.

No preservation failure remains, so the rollback condition was not triggered.
Recovery snapshots and the pre-migration real index remain available under the
reported local paths. Large database copies are disposable evidence and are not
committed. Historical coverage is initially zero: the migration creates the
model, not invented dates. Source-reviewed catalogues are subsequent authored
inputs, independently fingerprinted from proof evidence.

## Reproduction

Use the checkout environment and the commands in the regression output's owner
task. `evidence/qualify-real-index.py` records the local source/copy paths and
refuses to overwrite an existing qualification copy. `review-timing.py` records
the balanced follow-up protocol. Adjust only local paths for a different machine;
do not overwrite the shared source index. The JSON report retains the exact
source proof-generation identity and recovery path.
