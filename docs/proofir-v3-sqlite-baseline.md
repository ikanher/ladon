# ProofIR v3 / SQLite scale baseline

Captured 2026-08-09 from commit-under-test with project-local commands.  The
large-repository database was built under `/tmp`; the Lean repository was not
modified.  Timings are calibration observations from this host, not release
budgets or theorem-verification evidence.

## Maintained native-v3 fixture

`publish_v3_database` projected the nine artifacts returned by
`tests/support/proofir_v3_native.py::native_artifacts`.

| Measure | Observed |
| --- | ---: |
| canonical artifacts | 9 |
| distinct subject rows | 24 |
| artifact-subject rows | 24 |
| database bytes | 495,616 |
| empty-schema bytes | 438,272 |
| marginal projection bytes | 57,344 |
| build elapsed | 0.020894 s |
| warm count query | 0.000195 s |
| registered access-path gates | 14 / 14 passed |
| integrity / foreign keys | `ok` / 0 violations |

The fixture retains one row for each native semantic family where the fixture
contains that family: claim, derivation step, plan step, failed attempt,
check result, source surface, selected attachment plus its candidate, and
governance observation.  It intentionally has no recursive SCC or omission;
the populated skew contract test supplies 40 rows for every registered query
family and requires every intended access path with no temporary ordering.

## Large Lean repository

Repository: `../lean/matrix-factorization/Mf`

Command shape:

```text
ladon proof-search index build \
  --repo-root ../lean/matrix-factorization/Mf \
  --index /tmp/<run>/mf.sqlite3 \
  --max-index-mib 768 --mode lexical
```

| Measure | Observed |
| --- | ---: |
| Lean modules | 3,770 |
| declarations | 150,826 |
| module imports | 8,486 |
| structures | 2,049 |
| database bytes | 544,952,320 |
| product build elapsed | 59.247159 s |
| end-to-end wall time | 59.46 s |
| peak resident set | 106,940 KiB |
| canonical ProofIR artifacts | 0 |
| allocated empty ProofIR-v3 group | 172,032 bytes |

The database storage report attributes 254,758,912 bytes to the base group,
42,172,416 bytes to FTS, 214,659,072 bytes to semantic storage, and 172,032
bytes to the empty native-v3 projection.  The dominant cost is therefore the
existing declaration index, not empty ProofIR rows.

Warm product queries were run repeatedly against the published database.  The
reported elapsed time below excludes process startup; median end-to-end time
includes `uv` and CLI startup.

| Query | Mode | Results | Product elapsed | Warm CLI median | Quality observation |
| --- | --- | ---: | ---: | ---: | --- |
| `rankOneKernel2_psd` | all | 1 | 0.002280 s | 0.003016 s | exact theorem first and only |
| `empiricalKernel rankOne Jacobian` | all | 1 | 0.042219 s | 0.043114 s | intended theorem first and only |
| `top sorted tail mean` | all | 10 | 0.041867 s | 0.042652 s | all returned names are in the intended `SortedTail` family |
| `sorted tail rank` | all | 0 | 0.041245 s | 0.042084 s | useful negative: lexical name search does not infer the prose concept “rank” from the source comment |

The quality result is deliberately mixed.  Exact and segmented declaration
names are strong navigation queries; prose-to-concept retrieval remains outside
this lexical index and must not be reported as semantic absence.

## Omissions and query plans

SQLite reported `integrity_check = ok`, no ProofIR diagnostic rows, no native-v3
omission rows, and one repository-discovery omission.  The omission is
attributable and non-silent: `lean.layout.conventional_fallback` records that
no usable Lake library source roots were found, so Ladon used the
repository-relative conventional module layout.  This is a navigation-layout
limitation, not evidence about any theorem.

Fresh `EXPLAIN QUERY PLAN` observations confirmed the intended access paths:

| Access | Observed plan |
| --- | --- |
| exact declaration name | `idx_declarations_name_casefold (name_casefold=?)` |
| segmented declaration name | FTS5 `declaration_search` virtual-table scan followed by integer-primary-key lookup |
| native-v3 statement local ID | covering `idx_v3_subject_local_id (local_id=?)` |

The exact/FTS disjunction uses a temporary B-tree only for the final bounded
name ordering.  The populated-skew contract separately requires every
registered native-v3 access path without temporary ordering; this large
repository contains no ProofIR artifacts, so the native-v3 query-plan
observation here validates the empty projection's schema and index selection,
not populated-row performance.
