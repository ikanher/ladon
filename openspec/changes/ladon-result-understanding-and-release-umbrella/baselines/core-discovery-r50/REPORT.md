# Automatic core discovery follow-up — r50

Ladon completed the fixed-epoch reuse task **without receiving a theorem name**.
With a verified lexical index, the goal's `fixedEpochCenterGap` text and supplied
module selected four candidates. Checking ranked the propagation lemma first,
compiled its application in context A and retained exactly the boundary-gap
premise in B. Three other candidates were rejected and remained visible.

Native Lean also found the valid application. The useful distinction in this
probe is the incomplete case: Ladon returned one bound residual premise;
native `apply?` emitted 280 suggestions, including an application with an
uninstantiated boundary, and a `sorry` warning despite compiler exit zero.
This suggests a role for bounded, structured partial results. It does not
establish added mathematical decision value or general superiority.

## What was exercised

This is a root-operated follow-up to the [paired reader experiment](../read-find-check-r49/REPORT.md),
not a new blind reader test. The operator already knew the expected lemma.
Commands supplied no `--candidate`, inspected no private database selection and
used the ordinary installed CLI. The exact r49 goal, ordered A/B contexts and
pinned Lean 4.33.0 environment are retained in [reader-task.json](reader-task.json).
The module and literal type-text pattern were supplied; automatic module
selection and unrestricted theorem discovery were not tested.

Runtime candidate remains `573dec57fbc187d9f3343fe6eec51b8fea11da1e`, with its
[existing qualification](../read-find-check-r49/qualified-candidate.json).
No production code, neighboring Lean source or shared build was changed.
No new qualification or readiness promotion is inferred from this probe.

The existing matrix index was stale. `--freshness verify` rejected it before
checking. An isolated index was rebuilt through the public command, preserving
the shared index. It took 93.72 recorded command seconds, about 120 MiB peak
tree RSS, and produced a 771,096,576-byte database. The fresh module-scoped
shortlist had four lexical-signature rows with no truncation. Its population
coverage concerns that indexed module and pattern, not every mathematical
candidate or proof dependency.

Retained operator invocation errors include unsupported `--json` and
`--index-path`; the documented spellings are `--format json` and `--index`.
The original failed freshness check and corrected commands remain available.

The discovery command supplies the same checking module and explicit candidate
population separately:

```text
proof-search discover --module Mf.DP.PoissonFixedEpochCenterGapPropagation
  --pattern fixedEpochCenterGap --scope module
  --root Mf.DP.PoissonFixedEpochCenterGapPropagation
  --freshness verify --max-candidates 8 --batch-size 4
  --scratch-mode advisory
```

The complete argv in `commands/` also records the repository, isolated index,
exact goal, ordered locals, explicit Lean/Lake paths and resource limits.
`--module` selects the checking environment; `--root` selects the shortlist
population. Neither is silently inferred from the other.

## Outcomes and resource observations

| Operation | Outcome | Command seconds | Peak tree RSS | Stdout bytes |
| --- | --- | ---: | ---: | ---: |
| Ladon discovery A | One accepted application, compiled scratch; three rejections | 27.28 | 8.36 GiB | 17,081 |
| Ladon discovery B | One application with exact residual; three rejections | 21.28 | 8.37 GiB | 16,051 |
| Native `exact?` A | Found the same lemma and compiled | 7.31 | 9.08 GiB | 2,134 |
| Native `exact?` B | Failed to close the goal | 8.74 | 9.10 GiB | 160 |
| Native `apply?` B | Exploratory suggestions and `sorry`; exit zero is not a proof | 10.55 | 9.12 GiB | 131,277 |

Ladon's B obligation is
`0 ≤ Mf.DP.fixedEpochCenterGap point h boundary`. It does not conceal the missing
premise or infer that the goal is false. Native `apply?` first suggests the
same lemma but leaves a boundary value and three dependent premises unresolved;
it also emits 280 failed-candidate messages. Its intended exploratory semantics
are preserved here rather than classifying its process exit as theorem checking.

The populations and operations differ: Ladon checks a four-row module shortlist;
native tactics search the imported environment. These single shared-host
observations are not a controlled speed benchmark. The highest observed RSS was
9.12 GiB, within the accepted 32 GiB limit. Index cost is separate from checking
cost. No run hit timeout, memory or output limits.

## Cost profile and bounded next repair

An additional installed discovery-A run under Python `cProfile` still accepted
the application and compiled scratch. Profiling took about 72 seconds and adds
substantial instrumentation overhead; these times must not replace ordinary
command timing. Cumulative times overlap and must not be added together.

The [profile summary](profile-summary.json) identifies:

- Six source-tree identity calculations, about 29.74 cumulative profiled seconds.
  Source path enumeration/filtering accounts for about 19.65 seconds within them.
- 103 envelope validations and 26 batch validations, about 18.85 and 17.43
  cumulative seconds respectively, with overlapping calls.
- Semantic result delivery, including registration, rereading and projection,
  about 26.01 cumulative seconds.

The source checks are deliberate identity boundaries; the observation is not
permission to skip them. The next bounded repair should reduce repeated parsing
or validation work while retaining every source/toolchain recheck and complete
evidence validation. Start with source-path normalization/filtering, then consider
owned immutable validation results for repeated environment references inside
one delivery request. Reuse by path or modification time across requests would
not preserve the existing guarantees.

Require byte-identical selected source identities and projected evidence,
unchanged rejection of malformed paths/envelopes and mutations, and a measured
cost reduction on the frozen inputs before adopting a repair. If those checks
cannot be preserved or cost is negligible, stop that route. A new native-search
backend or inspection session is not an automatic prerequisite.

## Decision and evidence

The automatic search-to-check route works for this scoped fixture. The stronger
next product hypothesis is that exact, compact partial applicability can help
an LLM decide which prerequisite needs work. That hypothesis still requires
fresh-reader evidence; the r49 scope/usefulness gate remains unmet. Result-layer,
provenance and community-profile expansion remain deferred. Umbrella task
accounting stays 33/50; this follow-up does not close unrelated acceptance tasks.

[Observations](observations.json) bind all ten supervised commands, outcomes,
streams and telemetry. `commands/` retains failures and outputs; the index remains
in `/home/codex/.cache/ladon-core-discovery-r50/`. The raw profile is identified by
path, size and digest in its summary. [Verification](verification.json) checks
retained bytes and unchanged qualified production. This report is development
evidence, not an independent review or a quantitative benefit claim.
