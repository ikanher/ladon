## Why

External review reproduced five contract failures in Ladon's advertised proof-discovery and authority surfaces: `explain` compares a goal with a declaration name instead of its indexed type, type search ignores requested scope and source verification, toolchain preflight can certify a different environment from the worker's, and authority projections can promote ambient or absent evidence to explicit-pinned authority. Ladon's result vocabulary currently looks stronger than those checks warrant, so correctness and execution-integrity repairs must block any authority-safe release before product expansion resumes.

## What Changes

- Repair `proof-search explain` so it compares only a validated, non-truncated candidate type and returns an explicit unavailable result when that evidence is absent.
- **BREAKING**: rename the current lexical `search type` surface to `search type-text` or `search signature`, and either implement every advertised scope/freshness mode or reject it before querying.
- Run executable resolution, pin/version preflight, and the Lean worker under one canonical sanitized environment and record a non-secret environment fingerprint.
- Replace the partial authority check with exhaustive, independently represented execution binding, observation state, operation outcome, freshness/environment match, authority basis, and analysis completeness transitions, and expose `ladon doctor --json` for installed/schema/toolchain/posture diagnosis.
- Remove the dead recursive derivation slicer and keep one stack-safe budget-governed implementation.
- Add an integration packet that forbids the `authority-safe` release label until both correctness and authority repair children pass installed adversarial gates.
- Deliver one installed goal-and-context-to-verified-candidate workflow that batches Lean checks, reports substitutions and exact residual premises or rejection reasons, and records the scratch compilation as the same attributable check operation.
- Replace binary feature support labels with capability readiness levels and held-out external outcome evaluation against Lean/editor baselines.
- Freeze new ProofIR artifact families, Rust parity expansion, daemon work, broad service-class refactoring, and optional atlas/runset/reportset/capsule/bridge/governance expansion until the integration gate and discovery vertical slice exit.

## Capabilities

### New Capabilities

- `ladon-proof-discovery-correctness-repairs`: Correct candidate-type explanation, honest type-text naming, enforced scope/freshness behavior, and adversarial installed regressions.
- `ladon-execution-authority-integrity`: Identical preflight/worker execution context, compact evidence receipts, exhaustive non-escalation transitions, persistence/render round trips, and execution diagnostics.
- `ladon-authority-safe-release-gate`: A release-policy integration gate depending on both correctness and authority repair capabilities.
- `ladon-verified-discovery-loop`: One bounded installed workflow from goal and local context through shortlist, batched Lean verification, exact residuals or rejection, and attributable scratch compilation.
- `ladon-capability-readiness-and-external-evaluation`: Readiness levels, held-out multi-repository goal/finding corpora, baseline comparisons, and outcome-based promotion rules.

### Modified Capabilities

- `proofir-observation-authority-and-coverage-core`: Split execution binding, observation state, operation outcome, freshness/environment match, authority basis, and analysis completeness, with exhaustive non-escalating projection rules.
- `proofir-derivation-hypergraph-semantics`: Require one stack-safe slice implementation and prohibit dormant recursive traversal paths.

## Impact

Touches proof-difference analysis, type-shortlist commands and schemas, scope/freshness verification, toolchain resolution, semantic worker supervision, evidence-result models, SQLite persistence and dossiers, CLI/JSON/text rendering, derivation traversal, installed distribution tests, supported-feature generation, benchmark fixtures, documentation, and the maintained Ladon skill. The type-search rename and evidence-receipt contract are versioned public changes; disposable SQLite projections may require rebuild. No target Lean repository is modified, network access is not introduced, and public package publication remains blocked without an owner-granted license.
