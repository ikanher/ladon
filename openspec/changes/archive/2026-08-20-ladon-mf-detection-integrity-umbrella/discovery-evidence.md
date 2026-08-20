# Matrix-Factorization Detection-Integrity Evidence

## Evidence Boundary

This note records a read-only observational product trial against the live sibling
repository at `/home/codex/projects/lean/matrix-factorization`. It is not a proof
verdict, clean-revision benchmark, portable fixture, or required CI dependency.
No Lean build or Lean extraction ran in this pass.

The target was under active development. One already-dirty Lean file changed while
the reports were being rendered, so the JSON, text, and later source census do not
share one immutable source snapshot. That drift is itself evidence for the
snapshot-integrity child; counts below identify the named frozen report only.

## Recorded Identities

- Observation date: 2026-07-26
- Target Git revision: `5c7d0f0d356d6b17fd4ece6721171227f9a2a713`
- Target Lean toolchain: `leanprover/lean4:v4.30.0`
- Target status at a later metadata check: 655 changed or untracked paths
- Analyzer version: `0.1.0`
- Extraction backend: `text`
- Full JSON analysis fingerprint:
  `sha256:3f992d96bf588f0c5aef1f7cda257b2182d724589261aec241634fd68da67a63`
- Full JSON source-index fingerprint:
  `35d8b5dba35564ab6f1f89d7499a0a9a5d4c598e77bde9c876e6a49868a1dac1`

The status count is moving observational metadata, not a product threshold.

## Frozen Artifacts

- `temp/mf-gap-pass-20260726/agent-run/report-full.json`
  - 11,043,229 bytes
  - SHA-256:
    `2b2a5c0aa5c16b97d29e82184a4fe8dbee201c7295ed97c090e364018167c4b0`
- `temp/mf-gap-pass-20260726/agent-run/report-full.txt`
  - 24,833 bytes
  - SHA-256:
    `8d1ddb7b09b4709973b0347dc77587e7a8cd064dc23365c35d8fff886c26d88b`
- `temp/mf-gap-pass-20260726/owner-audit/report-full.json`
  - SHA-256:
    `c71055680ea8142a776e355d7eabb4791ffccbd5ee045b7e54cbbe5c43feb875`

The full inventory run observed 2,628 modules, 5,779 internal edges, 197 facades,
435 name-marked generated modules, 37 command-only modules, and 403 supported
resource directives. It found no import cycle or genuine missing import in the
full inventory.

The v3 full projection declared `omissions: []`, while its nested lexical
declaration summary retained 7,518 of 137,917 candidates and omitted 130,399
(94.55%). This contradiction is a primary coverage predicate.

## Reproduced Integrity Failures

### Known out-of-slice imports reported missing

An ordinary owner-scoped text run selected five modules for
`Mf/DP/OptimalSamplingFinalAudit.lean` and emitted 17 missing-internal-import
rows. Every target path existed in the discovered inventory; the imports were
outside the selected owner context. A portable fixture must reproduce both this
case and one genuinely absent target.

### Rootless inventory silently acquired a root

Inventory scope diagnostics said roots were ignored, but DAG reachability used the
display/report anchor `Mf`. The resulting report called 2,613 modules unreachable.
`Mf.lean` explicitly documents its narrow import surface, so the count does not
establish dead or unpublished modules.

### Composite signals lacked a graph join

`composite_import_pressure` paired the 14-module closure below `Mf.Basic` with the
global fan-in maximum at
`Mf.DP.GeneratedShiftedHiddenHeadRouteAScalarSmoke.Base`, which is outside that
closure. The evidence value summed unrelated quantities. Disjoint hot signals must
be a required negative fixture.

### Declaration collisions were not surfaced

The source census found a strong same-namespace, same-name, same-block lexical
candidate at:

- `Mf/DP/BMinSep/WarmStartCooldown/GenericSmallDelta/ExtendedSeparationStepBackend/Row9.lean:306`
- `Mf/DP/BMinSep/WarmStartCooldown/GenericSmallDelta/ExtendedSeparationStepBackend/Row10.lean:9`

Their aggregation module imports both shards. Another pair of generated
`Base.lean` files was byte-identical. These observations justify lexical collision
and duplicate-source candidates only; Lean must determine actual environment
identity and compatibility.

### Audit role and continuation parsing disagreed with source

Thirty-seven declaration-empty modules contained 858 audit commands yet were
classified as `pure_barrel`; selected examples were then promoted as generic
public-facade pressure. Approximately 109 multiline `#check` or `#print axioms`
subjects were unparsed in the frozen report. Text extraction establishes command
intent and source location, not resolution or axiom results.

### Path-independent generated-looking families were absent

Two unconfigured, non-`Generated...` path families contained:

| Family | Modules | Lines | Declarations |
| --- | ---: | ---: | ---: |
| `StepR01` | 100 | 280,850 | 29,896 |
| `ExtendedSeparationStepBackend` | 66 | 214,902 | 19,430 |
| **Combined** | **166** | **495,752** | **49,326** |

The families have contiguous `RowN` siblings, uniform `Data` imports, and a common
`generatedTypedBMinSep` declaration stem. All remained `target_owned`, and their
largest modules appeared in “handwritten” findings. This evidence supports an
advisory generated-looking candidate, never automatic provenance.

### Proof mechanisms and options were not navigable

The moving source census observed approximately 139,667 `norm_num`, 46,681 `rw`,
46,596 `simp`, 19,836 `simpa`, 3,776 `omega`, 3,663 `ring`, 3,014 `linarith`, and
1,671 `nlinarith` lexical occurrences, plus 2,507 `@[simp]` declarations. These
counts motivate tactic/mechanism navigation but do not establish execution,
dependency, rewrite, or success semantics.

The source contained 1,575 `set_option` sites. Ladon retained 382
`maxHeartbeats` and 21 `maxRecDepth` directives, including 12 unlimited heartbeat
settings and one configured value of 80,000,000, but ignored other option classes
and created no resource review region. Configured values are cost-risk navigation,
not consumed runtime.

## Required Portable Predicates

Implementation acceptance must use tracked target-neutral fixtures to establish:

- full-inventory-aware import classification and rootless inventory semantics;
- positive joined and negative disjoint composites;
- namespace/private/comment-safe lexical collision candidates;
- multiline audit parsing and audit-facade role precedence;
- advisory regular-family detection with regular-handwritten negatives;
- late-page evidence lookup and stale-fingerprint rejection;
- lexical tactic/scope/option rows with explicit nonclaims;
- complete coverage arithmetic, stratified projection, and partial-atlas handling;
- one-analysis multi-format parity; and
- deterministic source-drift injection.

An optional closeout rerun may compare these normalized predicates on the live
target. It must record fresh fingerprints, keep the target read-only, and treat
changing cardinalities as observational.

## Closeout Observation

The optional closeout run used the ordinary installed-style CLI surface against
the live sibling checkout with inventory scope, the text extraction backend, v3
review projection, and one-analysis JSON/text emission. It did not run Lake,
Lean, a build, or any target-writing operation. This is a fresh observation
rather than a longitudinal cardinality comparison with the moving discovery
checkout.

The following target identities matched exactly before and after the closeout
run:

- Git revision:
  `5c7d0f0d356d6b17fd4ece6721171227f9a2a713`
- Lean toolchain: `leanprover/lean4:v4.30.0`
- v2 NUL-delimited porcelain status SHA-256:
  `4a3d1ab23cc6c0a35306d91721ce8731bb2c8af0def43dcd48129e3cdf563597`
- v2 porcelain records: 1,550
- `Mf` path/size/mtime manifest SHA-256:
  `d1571dbb51d6df8924cd955802fdf6eac722851794a7c1c4b60f1aeb446cd068`
- `Mf` files: 2,658
- Ladon source fingerprint:
  `be1ff55979c08be61d1cc85660343783cd8cb5406c96d7cc2bec1052d5fe7706`

The report declared a stable captured snapshot with no mismatch:

- analysis fingerprint:
  `sha256:019addcb7d36815ddf87cdd3019c63aa8a8c20fdd2f7eb3e6cdb8c5cc6efd8c8`
- snapshot identity:
  `sha256:350fc0965f3f3df98e21acc979174af411abcfcc059e6b268b9109dca0db4299`
- source-index fingerprint:
  `2b55773b018ef54f5c32b4fb3265324369f9df25732c0179352f9c84d06528d6`
- JSON: 22,674,142 bytes, SHA-256
  `d54fbdff749c9da51655ee4b9b839ee47ace3a25904d9042a7b842b0acad60f7`
- text: 495,781 bytes, SHA-256
  `59028f1021d4bdb514a2a0d84f91ab91e837d84b4d04c5d8b7471f5e5e1c4abe`
- wall time: 14.32 seconds
- peak RSS: 1,486,568 KiB
- cache outcome: 2,658 hits from 2,658 source rows

The v3 schema validated. Every installed inspection noun returned one
diagnostic-free page with unique stable IDs and resolving canonical,
coverage-row, and coverage-pointer references:

| Noun | Visible | Total |
| --- | ---: | ---: |
| modules | 709 | 2,658 |
| declarations | 2,087 | 138,374 |
| imports | 100 | 6,207 |
| audits | 1,121 | 1,121 |
| options | 426 | 1,603 |
| resources | 112 | 403 |
| proof mechanisms | 2,236 | 372,533 |

Only the audit page is exhaustive under the review projection. The audit review
region retained eight signals against 1,121 observed inputs and recorded 1,113
omissions. All local, external, action, and coverage references resolved. Its
313 lexical candidate-match rows, representing 109 declaration identities, all
carried resolving canonical declaration references. Proof navigation retained
34 mechanisms across 36 evidence kinds, 1,381 modules, and 1,662 declaration
identities. Those rows comprised 2,130 tactic-token and 106 attribute
occurrences.

These remain structural and lexical observations. They do not establish Lean
environment identity, command success, theorem truth, proof correctness,
generator provenance, authorship, freshness, measured proof cost, or a defect in
the target.

## Profile-Guided Performance Observation

A CPU-clock `yappi` run over the same warm-cache CLI workflow completed
successfully and aggregated 2,321 Python functions. Profiler overhead raised its
wall time to 182.11 seconds, so its absolute timings are not acceptance
measurements. Its dominant actionable path was
`declaration_integrity._shared_importer_witness`: 26,900 collision groups each
rescanned every selected graph owner, accounting for 56.58 profiled CPU seconds.

The closeout replaced that repeated scan with one inverse target-to-importer
index built only after exact graph validation. Output-order and operation-count
tests preserve the direct-witness rule, widest-then-lexical tie-break, normalized
edge offsets, and fail-closed fallback. A second change kept all three required
fresh source-map snapshots but pruned already-ignored `.lake`, `.git`, virtual
environment, cache, and temporary directory components before descent.

Against the unchanged target and warm cache, wall time fell from 31.25 to 14.32
seconds, a 54.18% reduction. The discovery phase fell from 7.7945 to 4.7510
seconds and the module-DAG phase from 16.6364 to 4.6143 seconds. A recursive
before/after comparison found differences only in the 21 timing/resource fields;
analysis, snapshot, source-index, coverage, evidence, and inspection semantics
were unchanged. Peak RSS stayed approximately 1.418 GiB. The remaining eager
decode of the monolithic source-index cache, including all proof-mechanism rows,
requires a separately versioned cache-design change; this closeout does not claim
to solve that memory surface.

## Portable Performance Closeout

The final three-sample installed-wheel large-inventory gate passed every
time/RSS/size/cache/determinism contract. Its artifact SHA-256 was
`367f2793b834c880e691798b82198f894b0365e83d196ab2861b3fbcd836aa29`;
the candidate source fingerprint was
`sha256:700b16463f32343e4203733cef567176c7c6f4c469b93fd88f3edb725bcdd069`,
the wheel identity was
`sha256:d54e1730b4a19b3217169b9c408bd59372f4046dce71723738690726f9248e83`,
and the fixture identity was
`sha256:c34835c339d553837c634befaaf4ac44c36b43c7cd5c400388c2fc33f0ea712a`.

Cold wall time ranged from 11.853803 to 12.067843 seconds, warm wall time
from 4.571266 to 4.746627 seconds, and peak RSS from 294.297 to 396.074 MiB.
JSON size ranged from 3,748,957 to 3,748,987 bytes and text size was 64,059
bytes. Cold runs rebuilt all 2,600 cache rows, warm runs hit all 2,600 rows,
and all six JSON observations shared analysis fingerprint
`sha256:2559e33737145c3f53e769d47aa1b9ded49d2bb10e803f095f3f92ef82302a79`
and normalized report SHA-256
`sha256:902f42f18fa05e4051b11505676091c5d434265cbbbbb2024105603c26b26b4f`.
All 36 checks were supported and passed.
The local host was Ubuntu 24.10 with 12 available CPUs rather than the declared
Ubuntu 24.04 four-CPU reference job, so `referencePassed` was false while every
portable product contract passed.
