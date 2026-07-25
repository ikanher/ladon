# Matrix-Factorization Post-Alpha Discovery Evidence

## Evidence Boundary

This note records an observational product trial against the live sibling
repository at `/home/codex/projects/lean/matrix-factorization`. It is not a
portable test fixture, a proof verdict, or a clean-revision benchmark.

The target was read only. Ladon reports were written under
`temp/matrix-factorization-product-discovery-r01/` in the Ladon checkout and
the Lean cache was directed to `/tmp/ladon-mf-cache-r01`.

## Target Identity

- Git revision: `5c7d0f0d356d6b17fd4ece6721171227f9a2a713`
- Lean toolchain: `leanprover/lean4:v4.30.0`
- Sorted `Mf/**/*.lean` content fingerprint:
  `996e3e5330d28aaa934ae781ab34c36621b4c1760c1a8774a65a3911e66c042f`
- Live Lean status: 6 modified tracked files and 101 untracked files.
- Source scale under `Mf/`: 2,610 files and approximately 1,871,102 lines.
- Ladon inventory: 2,611 modules and 5,727 import edges, including `Mf.lean`.
- The live tree contains about 137,000 lexical declarations. It also contains
  480 `#check` commands, 455 `#print axioms` commands, and 37 command-only audit
  modules.

The dirty state is intentional current research work. Cardinalities and hashes
therefore identify this observation only and must not become universal product
thresholds.

## Ladon Identity

- Git revision: `ffbb5925afc3c6c23443f55c2d4ffcc9bb9b0a63`
- Staged alpha implementation diff fingerprint:
  `5b91ba63d81cb50d49bce8dced0e1733a652e82eb23fa57500cdec81d9874249`
- Analyzer metadata version: `0.1.0`
- Invocation surface: ordinary `bin/ladon`; no caller-specific mode.

## Observed Runs

### Full text-backed inventory as JSON

```bash
bin/ladon \
  --repo-root /home/codex/projects/lean/matrix-factorization \
  --root Mf \
  --format json \
  --output temp/matrix-factorization-product-discovery-r01/project-mf.json
```

- Exit: `0`
- Wall time: `56.98 s`
- Peak RSS: `1,634,976 KiB`
- Output: `217,866,909 bytes`, `4,840,426 lines`
- Output SHA-256:
  `d4a42741dd28af4aa51f9afb9fbd3ca2c2c71f4d5fafc6d4c56b8c6b3019f725`
- Discovery phase: about `42.65 s`
- Module-DAG phase: about `3.71 s`
- Findings: 88 final rows

Compact serialization showed three nearly identical large payloads:

| Location | Compact bytes |
| --- | ---: |
| top-level `module_dag` | 45,614,583 |
| `phases` | 45,888,546 |
| `pipeline.timings` | 45,888,558 |

The phase envelope and legacy pipeline view each embed the same large module
payload that is already present at top level. Pretty printing expands the
combined copies to the observed 218 MB.

### Full text-backed inventory as text

```bash
bin/ladon \
  --repo-root /home/codex/projects/lean/matrix-factorization \
  --root Mf \
  --format text \
  --output temp/matrix-factorization-product-discovery-r01/project-mf.txt
```

- Exit: `0`
- Wall time: `53.44 s`
- Peak RSS: `785,852 KiB`
- Output: `19,386 bytes`, `231 lines`
- Output SHA-256:
  `6d477086dbc001085587dd799f100d3b738e0026b55e31776cc194e594bee6e8`

The compact text surface was readable and included useful signals:

- 24 direct architecture-policy violations;
- 19 shared-dependency candidates;
- 68 refactoring prescriptions;
- the 583-import `Mf.Optimization.SDE` facade;
- generated and handwritten fan-in populations;
- three 13,000–21,000-line modules classified as handwritten.

It also exposed usability gaps:

- no progress for roughly 53 seconds;
- 73 of 88 findings omitted with no installed lookup path;
- the requested `Mf` root reaches only 15 of 2,611 modules, but the report
  cannot plan a useful multi-root review set;
- a findings-phase counter recorded 68 rows even though later prescription
  promotion made the final count 88.

### Lean-backed owner analysis

```bash
bin/ladon \
  --repo-root /home/codex/projects/lean/matrix-factorization \
  --root Mf/DP/OptimalSubsamplingBISLR.lean \
  --extraction-backend lean \
  --lean-extraction-scope root \
  --lean-cache-dir /tmp/ladon-mf-cache-r01 \
  --lean-timeout 120 \
  --format text \
  --output temp/matrix-factorization-product-discovery-r01/owner-optimal-subsampling-bislr-lean.txt
```

- Exit: `1`
- Wall time: `104.54 s`
- Peak RSS: `7,964,652 KiB`
- Output: `23,835 bytes`, `311 lines`
- Output SHA-256:
  `f35a6a629ea6b2f8daf8fe4a5642dcf8957217b180f20d28426e004acdfd037b`
- Discovery phase: about `42.89 s`
- Lean extraction phase: `partial`, about `47.71 s`
- Declaration rows: 1,151
- Declaration edges: 0
- Cache entries after the run: 0

The partial report preserved useful declaration statements and direct trust
references. However:

- neither stderr nor the text phase table explained the partial failure;
- global inventory findings dominated the owner report;
- 2,609 modules and 866 declarations were labeled unreachable;
- imported `Init.*` modules appeared as namespace/module drift;
- compiler-generated families such as `simp_1` and `1` were promoted;
- synthesized structure helpers appeared before authored declarations;
- all declaration fan-in/fan-out values were zero despite the partial state.

## Existing Report-Set Workflow Trial

The checkout-only `scripts/ladon_atlas_export.py` successfully consumed the
218 MB report:

- Wall time: `2.32 s`
- Peak RSS: `789,620 KiB`
- Atlas JSON: about 55 KB
- SQLite: about 144 KB
- Reviewer cards: about 1.5 KB

The cards and canned hotspot query were useful. The workflow is not installed
as a supported command, and its summary called 12 highlighted nodes “modules”
for an underlying 2,611-module report. The implementation should be exposed and
terminology clarified, not rewritten.

## Source-Inspection Opportunities

The live repository also suggests later review-intelligence improvements:

- named public-root sets for deliberately narrow facades;
- changed-frontier and terminal-audit root planning;
- generated-family collapse for hundreds of row/table modules;
- explicit audit surfaces for command-only `#check`/`#print axioms` files;
- configurable distinctions among attempts, obstructions, negative theorems,
  conditional seams, and publication surfaces;
- resource-directive inventory for 382 heartbeat overrides in 227 files;
- configurable producer/bridge/adapter/consumer role policies.

The umbrella adopts audit-command and resource-directive surfaces now. Semantic
status inference and richer role-policy analysis remain follow-on candidates
until the scale and scope foundations are operational.

## Initial Ladon Implementation Anchors

These are investigation starting points, not predetermined patches:

- `src/ladon/report_model.py`: report assembly projects full phase data into
  `phases`, `pipeline.timings`, and canonical top-level sections.
- `src/ladon/analysis/module_dag.py`: lexical declaration rows repeat identical
  authority/nonclaim prose per declaration.
- `src/ladon/extraction.py`: source scanning computes declaration positions and
  currently derives a broad top-namespace inventory for a concrete owner.
- `src/ladon/render.py`: the compact phase table renders status and elapsed time
  but did not expose the observed partial Lean reason.
- `src/ladon/cli.py`: operational exit handling wrote the partial report but
  emitted no controlling stderr diagnostic in the observed owner run.
- `src/ladon/lean_extraction.py`, `src/ladon/lean_runtime.py`, and
  `src/ladon/process_supervisor.py`: the new scale work must reuse these
  selection, cache, batch, timeout, and process-lifecycle seams.
- `src/ladon/atlas*.py` and `scripts/ladon_atlas_*.py`: tested report-set
  engines and checkout wrappers to package through the installed CLI.

## Post-Application Product Acceptance

The applied umbrella was exercised again through the ordinary public CLI. The
target remained read only: reports and progress logs were written under
`temp/matrix-factorization-product-acceptance-r03/`, and source-index entries
were written under `/tmp/ladon-mf-source-index-r03`. Git status was identical
before and after each accepted invocation.

The observed target revision was still
`5c7d0f0d356d6b17fd4ece6721171227f9a2a713` with
`leanprover/lean4:v4.30.0`. The live worktree had 47 tracked changes and 1,363
untracked paths at the stable JSON snapshot. These counts identify that
observation only.

### Product defects exposed and corrected

The first post-application run rejected before report publication because
Ladon treated the Lake default `lean_lib Mf` source directory as an unrestricted
filesystem root. It indexed 9,243 Lean files, including a nested Lean source
checkout, and then encountered a symlink spelling mismatch. Source discovery
now retains lexical repository-relative symlink identity and applies the Lake
library's explicit or default module roots. The same target then selected the
2,620-module `Mf` library surface.

The next run detected that the target inventory changed while the source index
was being built and rejected the unstable snapshot. Source indexing now retries
a bounded number of times, rediscovers layout, incrementally reparses changed
entries, and commits a cache entry only after a stable verification. A
subsequent between-run change added
`Mf.Optimization.SDE.DPAdamFixedBetaFunctionSpaceRowContainment` and changed
`Mf.Optimization.SDE`; Ladon reused 2,619 entries and rebuilt exactly those two.
Because status was stable within each invocation and Ladon performs no target
writes, this between-run drift is retained as concurrent target activity rather
than analyzer output.

### Accepted ordinary-CLI runs

The JSON command used the public analysis surface:

```bash
uv run --locked ladon \
  --repo-root /home/codex/projects/lean/matrix-factorization \
  --root Mf \
  --scope inventory \
  --cache-dir /tmp/ladon-mf-source-index-r03 \
  --overall-timeout 180 \
  --max-rss-mib 1024 \
  --max-report-bytes 33554432 \
  --report-version v3 \
  --projection review \
  --format json \
  --output temp/matrix-factorization-product-acceptance-r03/steady-review.json \
  --progress json
```

| Run | Modules | Cache outcome | Wall | Peak RSS | Output |
| --- | ---: | --- | ---: | ---: | ---: |
| Stable cold | 2,620 | 2,620 rebuilt | 27.58 s | 188,924 KiB | 1,118,008 bytes |
| Incremental | 2,621 | 2,619 reused, 2 rebuilt | 8.82 s | 189,364 KiB | 1,118,133 bytes |
| Exact hit | 2,621 | 2,621 reused, 0 rebuilt | 8.37 s | 191,012 KiB | 1,118,129 bytes |
| Exact-hit text | 2,621 | 2,621 reused, 0 rebuilt | 7.71 s | 179,484 KiB | 24,831 bytes |

The incremental and exact-hit JSON reports describe the same source state.
They share analysis fingerprint
`sha256:329aef764999ba39cf941fdc71e3213d2a373f95e5c9d97ce24696a33c300097`
and normalized report SHA-256
`a7f9728812d370486bdfbf626f5881e29a214412b0aea26289f23950cbe6efc3`.
The exact-hit raw JSON SHA-256 is
`e6ab5ced63b330283b88f6aeb531dd9be9fd912168584859820e0459a129d1ba`;
the text SHA-256 is
`fed1fa91fba3a9bcbaa819ad18857ba6ff963f505413dd42649097aa1dd75013`.
Runtime and cache counters are deliberately excluded from the normalized
semantic comparison.

The review projection retained 88 findings and declared 11 bounded collection
omissions. `ladon findings --report ...` resolved all 88 finding rows without a
dangling-evidence failure. The module report recorded 5,755 import edges, 984
lexical audit commands, 403 resource directives, and 37 command-only modules.
It also retained 435 naming-derived generated-module candidates separately
from population authority. Because the target supplied no generated-family
policy, all 2,621 source modules remained `target_owned`; Ladon did not promote
the naming heuristic into project-generated provenance.

The installed preview surface was also exercised with the same resource
requests. It reported 2,621 selected inventory modules, 328 estimated Lean
batches, the discovered architecture policy fingerprint, absent optional
generated/source policies, and `willRunLake=false`, `willRunLean=false`, and
`willRunVersionControl=false`. The preview completed in 5.08 seconds at
171,576 KiB and preserved another one-entry source invalidation without
starting a target-controlled process.

These measurements are live product evidence, not portable thresholds, Lean
kernel evidence, or a normative CI result.
