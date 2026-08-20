## Why

Recent Matrix-Factorization smoke runs show that Ladon can now detect important
review smells, but the remaining TODOs are mostly about making those signals
durable, better prioritized, and semantically safer. The project needs a
roadmap umbrella so follow-on packets improve reviewer utility without
hard-coding target-repo names or overclaiming proof authority.

## What Changes

- Define the next review-intelligence backlog after the sampler-policy and
  source-pattern work.
- Prioritize policy persistence, report prioritization, fix-oriented
  architecture triage, broader common-layer ranking, facade quality,
  generated-artifact attribution, configurable lexical scans, benchmark
  fixtures, and Lean theorem-surface semantics.
- Preserve Ladon's boundary: architecture and source-pattern diagnostics are
  review-routing evidence only; proof truth and proof correctness remain owned
  by Lean or explicitly named external artifacts.
- Split TODOs into child-ready capability tracks so implementation can proceed
  incrementally through focused packets rather than a broad heuristic expansion.
- Record deferrals: no project-specific hard-coding, no full proof-dependency
  engine, no UI-first rewrite, and no Rust rewrite until profiles justify it.

## Capabilities

### New Capabilities

- `ladon-policy-persistence-and-workflow`: Discovers, documents, validates, and
  recommends repo-local Ladon policies so project-specific boundaries can run
  consistently without CLI-only temp files.
- `ladon-fix-oriented-architecture-triage`: Ranks policy findings and
  common-layer candidates with actionable context such as extract-common-layer,
  explicit-bridge, facade-cleanup, obsolete-import, or generator-cleanup.
- `ladon-common-layer-and-facade-quality`: Broadens common-dependency analysis
  beyond policy-near edges and distinguishes intentional public facades from
  mixed implementation/barrel modules.
- `ladon-generated-artifact-attribution`: Attributes generated-module pressure,
  duplicate imports, and repeated generated patterns to likely generator
  families and emits generator-side cleanup hints.
- `ladon-configurable-lexical-audit-packs`: Builds on source-pattern policy to
  support reusable policy packs for stale terms, local trust markers, TODO
  classes, banned prose, and anchored Lean trust constructs without hard-coded
  project terms.
- `ladon-review-signal-benchmarks`: Adds portable fixtures and oracle checks for
  architecture policies, source-pattern scans, claim authority mismatches,
  common-layer candidates, facade subtypes, generated attribution, and false
  positive boundaries.
- `ladon-theorem-surface-changelog`: Adds a future Lean-backed semantic
  changelog for theorem surfaces: changed theorem type, added premise, weakened
  or strengthened conclusion, name/type drift, and proof-only changes.
- `ladon-proof-xray-roadmap`: Defines the later elaborated backend track for
  tactic skeletons, axiom/sorry footprint, proof shape, and dependency evidence
  while keeping parser references separate from elaborated dependencies.

### Modified Capabilities

None.

## Impact

- Affected future code: CLI policy discovery/validation, report rendering,
  architecture policy summaries, source-pattern policy handling,
  module-DAG metadata, generated-module tagging, benchmark fixtures, Lean helper
  extraction, declaration graph reporting, and optional atlas/reviewer-card
  summaries.
- Affected future artifacts: repo-local `.ladon/` policy examples, portable
  regression fixtures, matrix-factorization smoke reports, docs, OpenSpec child
  packets, and pro-review packets.
- Affected workflow: maintainers should be able to run Ladon on a Lean repo and
  see prioritized, source-located review work: which boundary violations matter
  first, which common layer to extract, which facade is intentional, which
  generated source should be cleaned at the generator, and which theorem
  surfaces need semantic review.
