# First-Hand Ladon Report

Date: 2026-08-08

Target repository:
`/home/codex/projects/lean/matrix-factorization`

Target proof area: the fixed-beta DP-Adam stopped-region theorem owners under
`Mf/Optimization/SDE/`.

This report records direct use of the current Ladon CLI and the project-local
skill at:

```text
/home/codex/projects/lean/matrix-factorization/.codex/skills/ladon/SKILL.md
```

It does not evaluate the older shared skill copy.

## Overall Assessment

The new declaration index is already useful enough to change my Lean search
workflow. Exact-name and segmented-name search are fast, scoped, and return the
source location plus a bounded signature. The freshness and authority labels
are especially valuable: they make it difficult to confuse lexical navigation
with Lean proof authority.

The strongest current weakness is the semantic-evidence layer around the
lexical index. `consumers`, `constructor`, `explain`, and exact theorem lineage
can currently return statuses that are too confident, reject an obviously
relevant theorem, or consume substantial time and disk without yielding a
terminal result. Those surfaces need coverage-sensitive status reporting and
hard resource controls before I would use them routinely during proof search.

## What Worked Well

### Freshness and explicit rebuilding

The first status query detected the previous database as
`freshness: incompatible-schema`. It did not silently use the old generation.
The explicit rebuild then completed atomically with:

```text
freshness: fresh
schema: sqlite-v4-name2-fts2-lineage1-proofir1
declarations: 150743
modules: 3758
module imports: 8455
elapsed: 57.8 seconds
database: 535212032 bytes
```

This is the right workflow. The updated skill also correctly says that
omitting `--build` is the no-build architecture default and explicitly rejects
the removed `--skip-build` flag.

### Exact-name declaration search

This query:

```bash
../../ladon/bin/ladon proof-search search name \
  --repo-root "$PWD" \
  --text "firstExitCrossingMass_eq_terminalExitProbability_of_initial_region" \
  --query-mode phrase --scope repository --limit 10 \
  --format json --output -
```

returned exactly one row in about 0.46 seconds. It included:

- the fully qualified declaration name;
- theorem kind;
- source file and line;
- the complete lexical signature;
- `typeTextTruncated: false`;
- verified freshness and generation identity;
- an explicit lexical-authority nonclaim.

This is materially better than repeated raw `rg` for declaration discovery.

### Segmented theorem-name search

The query text `path theta succ sub l2 norm le` returned the three useful local
candidates:

```text
pathTheta_succ_sub_l2Norm_le_ae
pathTheta_succ_sub_l2Norm_le_all_row_ae
preExitPathWeight_mul_pathTheta_succ_sub_l2Norm_le_ae
```

That is exactly the shortlist I needed for the next deterministic-confinement
work. Name normalization across Lean's camel-case and underscore conventions
is working well.

### Type-text shortlist

An exact conclusion-pattern query for

```text
firstExitCrossingMass family j region n =
  terminalExitProbability family j region n
```

found the intended theorem in the requested module. The result correctly said
`lexical_shortlist` and `verification: not_requested`.

### Owner-level architecture report

The no-build architecture report completed in about 8.7 seconds and correctly
identified:

```text
modules: 2
edges: 1
acyclic: true
root owner: 1871 lines
direct imported owner: 1141 lines
```

It also made the build phase and declaration extraction omissions explicit.
The module-DAG portion is clear and useful.

### Evidence boundaries

The updated skill and CLI consistently distinguish:

- lexical declaration discovery;
- text-backed architecture evidence;
- stored semantic dependency evidence;
- Lean-backed exact theorem lineage;
- ProofIR evidence.

That separation is excellent. It addresses the biggest trust problem in Lean
search tools: a plausible match is not presented as a proved application.

## High-Priority Problems

### 1. Lineage growth bypasses the declared size policy

The lexical build respected `--max-index-mib 512`, finishing at 535,212,032
bytes, just under 512 MiB. Refreshing one theorem lineage then changed the
database to:

```text
database: 738119680 bytes
lineage closures: 1
lineage nodes: 5423
lineage edges: 203560
```

The configured size ceiling therefore does not govern later lineage writes.
One theorem added roughly 203 MB and pushed the database beyond the declared
cap. The resulting 738 MB database is not intrinsically excessive for this
repository; a ceiling up to roughly 1.5 GB is reasonable if the additional
lineage evidence is useful and warm queries remain fast. The issue is that the
actual storage policy differs from the requested one and the added space did
not yet produce a responsive lineage view.

Recommended behavior:

1. Define whether the limit applies to the base index or the complete database,
   and report that policy explicitly.
2. Permit a configurable complete-database ceiling up to about 1.5 GB for a
   repository of this size.
3. Report per-table bytes and the marginal bytes added by each lineage refresh.
4. Estimate closure growth before publication where possible and publish
   transactionally.
5. Consider storing deduplicated global Lean-environment nodes/edges rather
   than repeating a large closure per theorem.
6. Optimize for warm-query latency; extra storage is justified when it makes
   exact lineage materially more useful.

### 2. Lineage refresh and warm query did not produce a terminal result

The first lineage command printed only:

```text
refreshing theorem lineage for <theorem>
```

It then ran for roughly three minutes. No requested output file was present
when the command ended. The database did contain the new closure afterward.

A subsequent `--refresh never` bottleneck query against that stored closure
also ran for about a minute and ended without visible output.

Recommended behavior:

- emit phase progress such as `planning`, `Lean extraction`, `persisting`, and
  `rendering` with elapsed time;
- always emit a final success or failure record;
- create output files atomically and report their final path;
- distinguish timeout, resource-limit termination, renderer failure, and
  successful persistence with failed presentation;
- make bounded warm views genuinely cheap relative to refresh;
- add a compact closure-summary view that avoids route enumeration.

### 3. `consumers` says `complete` with no dependency coverage

The fresh index status reported:

```text
declaration_dependencies: 0
```

Yet a `consumers` query returned:

```text
proof-search consumers: complete
coverage authority: sqlite_semantic_dependency_index
typeReturned: 0
valueReturned: 0
```

With zero dependency rows in the generation, `complete` reads as “this
declaration has no consumers,” when the actual state is “semantic dependency
coverage is absent.”

Recommended behavior:

- return `status: unavailable` or `coverage: not-populated` when the dependency
  table has no authoritative population;
- include indexed declaration/dependency population counts in every response;
- reserve `complete` for complete coverage of a declared population.

### 4. `constructor` reports an empty structure as available

The index status reported:

```text
structure_fields: 0
```

Querying the known structure
`DPAdamFixedBetaFirstPrinciplesCorrectorUniformity.Data` returned:

```text
status: available
fieldCount: 0
fields: []
residual: 0
```

This can be mistaken for a genuine zero-field structure.

Recommended behavior:

- report `unavailable` or `structure-fields-not-indexed` when field coverage is
  absent;
- distinguish “known zero-field structure” from “known structure, fields not
  extracted”;
- include `structure_fields` population and extraction authority.

### 5. `explain` rejected a theorem with the exact requested conclusion

The candidate theorem's indexed signature was:

```text
(family ...) (j ...) (hregion ...) (n ...) (hinitial ...) :
  firstExitCrossingMass family j region n =
    terminalExitProbability family j region n
```

Given that exact conclusion as the goal, `explain` returned:

```text
classification: not-applicable
reason: conclusion-mismatch
dischargedBinders: []
suggestions: []
```

The useful answer would identify `hregion` and `hinitial` as residual
obligations.

Recommended behavior:

- compare against the declaration conclusion after peeling binders;
- normalize qualification, whitespace, Unicode/ASCII arrows, and implicit
  arguments consistently with type search;
- return unmatched hypotheses as residual goals;
- if lexical parsing cannot establish applicability, say
  `indeterminate-lexical` rather than `not-applicable`.

## Medium-Priority Problems

### Conceptual `any` search is dominated by generic tokens

The query `path theta displacement bound` in import-closure scope returned
many unrelated declarations because `bound` matched broadly. It did not rank
the known `pathTheta_succ_sub_l2Norm_le_ae` declaration near the top.

Possible improvements:

- downweight common theorem tokens such as `bound`, `le`, `eq`, `of`, and
  `path`;
- reward multiple query segments appearing in one candidate name;
- expose per-token match contributions in JSON;
- provide a minimum matched-token count for `any` mode;
- add a “prefer project-local basename segments” ranking mode.

### Owner reports include too much repository-global integrity inventory

The useful owner report was followed by tens of thousands of global collision,
duplicate-block, and projection-stratum candidates. The text output was about
30,000 tokens and was truncated by the caller, even though the selected graph
contained only two modules.

Recommended behavior:

- keep the default owner projection focused on selected/co-reachable evidence;
- summarize repository-global integrity counts in one compact section;
- require an explicit projection or flag to render global candidate samples;
- put the most actionable owner findings before global inventories.

### Base index is already at the configured base-build ceiling

The lexical database finished only about 1.6 MB below the 512 MiB cap. Small
repository growth may require a larger configured base-build cap. This is not
an immediate disk-space concern if the supported total budget is closer to
1.5 GB, but it makes the current default fragile.

Potential mitigations:

- report percentage of both the base-build and complete-database caps;
- document which tables dominate size;
- allow optional omission of expensive global duplicate/source-shape indexes
  for proof-search-only use;
- support separate architecture and theorem-lineage databases.

## Skill Feedback

The project-local skill is a substantial improvement. In particular, it:

- uses the current command names and output flags;
- explicitly removes `--skip-build`;
- requires freshness inspection before query use;
- explains scope semantics precisely;
- separates index search, raw source search, architecture, and exact lineage;
- describes authority and nonclaims well;
- gives Matrix-Factorization-specific query examples.

Two additions would make it more operationally robust:

1. State that `freshness: incompatible-schema` requires a rebuild even when
   top-level `status` says `available`.
2. Explain the distinction between the base index limit and complete database
   growth, and recommend explicit lineage bounds/timeouts until warm-query
   performance and size accounting are clearer.

The skill's direction to use `rg` for proof bodies and syntax fragments is
appropriate. Ladon should replace repeated declaration-name hunting, not raw
source inspection after a candidate is found.

## Recommended Fix Order

1. Make lineage size policy explicit and provide reliable final diagnostics
   and responsive warm views.
2. Make `consumers` and `constructor` statuses coverage-sensitive.
3. Fix `explain` binder peeling and residual-hypothesis reporting.
4. Add a compact owner-report projection that suppresses global inventory
   samples.
5. Improve `any`-mode ranking and stopword handling.
6. Add size-pressure reporting and optional index profiles.

## Bottom Line

I will use the new Ladon index for exact and segmented declaration-name search.
That part is fast, honest, and already better than repeated repository-wide
text search. I will continue to verify candidates in Lean and use raw source
tools for proof bodies, as the skill directs.

I would not yet rely on empty `consumers` or `constructor` results, negative
`explain` classifications, or theorem-lineage presentation without checking
coverage and the underlying database state. Those surfaces are promising, but
their current status vocabulary and resource behavior can mislead a caller.

## Follow-Up: 2026-08-09 Confinement Child

I rebuilt the index after landing the DP-Adam finite-horizon confinement child,
using a 768 MiB configured ceiling. The fresh generation was
`2fec9af2c73f6d3626b195f1d16ca0064dfff5ef82cef3401b060572b311ebc6`.
The rebuild took about 61 seconds and produced a 544,858,112-byte database with
150,754 declarations and 3,762 modules. This is an acceptable footprint for this
repository: it is comfortably below the user's roughly 1.5 GB usefulness ceiling
and did not make exact indexed lookup feel slow.

Exact declaration searches were effective. Ladon found all of these directly:

- `finiteHorizonPrefixRadius`;
- `pathTheta_mem_region_all_row_ae_of_prefixEuclideanClosedBall_subset`;
- the exact scale-indexed confinement consumer;
- `pathTheta_succ_sub_l2Norm_le_all_row_ae` in the accepted path owner.

That was materially better than repeated repository-wide text search for theorem
discovery. I then opened the returned owners to inspect bodies and signatures, as
the skill requires.

The main remaining search friction is broad prose under the default all-term
semantics. The query `path theta prefix radius region all row` returned no rows even
though the intended declarations were present and exact-name queries found them.
A query mode that automatically drops low-information unmatched terms, or reports
which term eliminated all candidates, would make broad discovery more predictable.

The status output also remains much more verbose than needed for routine proof work
because it reports detailed per-object accounting. A compact default summary with an
explicit verbose inventory flag would preserve the diagnostics without obscuring the
freshness, size, declaration count, module count, and active search mode that matter
on the critical path.

Overall assessment after this second use: the larger index is worth its disk cost,
exact and segmented theorem-name discovery is useful, and freshness reporting is
actionable. Broad semantic-style discovery and compact operational status remain the
highest-value improvements.

## Follow-Up: 2026-08-09 Exact Calibration Repair

I rebuilt the index after adding the fixed-beta DP-Adam exact privacy-calibration
owners, this time with a 1 GiB ceiling. The database grew only from 544,858,112 to
545,013,760 bytes, reached 150,770 declarations and 3,766 modules, and reported
`fresh`. The larger ceiling did not cause gratuitous growth.

Exact phrase search worked very well. Searching the calibration namespace returned
all 16 new declarations, including the primitive `Data` structure, row and cumulative
rho identities, the accountant epsilon theorem, the privacy-data constructor, and the
transcript/trajectory privacy consumers. Exact lookup remained effectively instant.

Broad `any` queries were still noisy. Queries such as `accountant cumulativeRho` and
`ExactPrivacyCalibration privacyData` ranked unrelated `Mf.Adaptive` declarations
above the intended owner, while an exact family-name phrase found the complete surface.
The `--min-matched-segments` option may help callers, but the ordinary ranking should
reward multiple segments in one declaration much more strongly than one common token.

The packet-evidence profile was useful. After adding a replayable numerical witness
and checker, it gave the review packet a complete 6/6 evidence score. This is a good
lightweight integration check and its required/optional distinction was honest.

Two documentation mismatches caused avoidable failed invocations:

- the installed skill still recommends `--skip-build`, but current Ladon rejects that
  flag and says omission already means no build;
- the installed skill still shows legacy `--output-json`/`--output-text` flags, which
  force deprecated report-v2 compatibility output. Current usage should prefer
  `--report-version v3 --projection review --emit json=... --emit text=...`.

The default owner report remains too verbose for a three-module target because it
renders large repository-global declaration-integrity samples. The v3 review
projection improves structure but should suppress those samples by default and retain
only compact counts unless explicitly requested.

Overall: indexed exact-name search and packet evidence are now useful in real proof
work. The most urgent fixes are updating the installed skill examples, improving
multi-segment ranking, and making owner reports locally scoped by default.
