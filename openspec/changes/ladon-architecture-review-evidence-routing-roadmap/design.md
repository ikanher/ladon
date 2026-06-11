## Context

Ladon currently has a clean-core Lean analysis pipeline, conservative module and
declaration graph reports, calibrated findings, atlas exports, packet-evidence
checks, and an optional ProofIR bridge. The pro-review feedback recommended a
clear product posture: Ladon should help maintainers decide what to inspect
first and route evidence, while leaving theorem truth to Lean or explicitly
named external artifacts.

The prior packet history already supports this direction:

- `ladon-clean-core-radon-gate` removed the old monolith and made quality gates
  real.
- `ladon-lean-declaration-graph-wiring` and follow-up mini packets added
  conservative declaration graph context.
- `ladon-literature-grounded-quality-signals` and
  `ladon-calibration-regression-suite` established calibrated signals and
  predicate checks.
- `ladon-operational-atlas-suite` made reports queryable and reviewer-facing.
- `ladon-proofir-bridge-mvp` kept ProofIR joins separate from core proof
  authority.

## Goals / Non-Goals

**Goals:**

- Make the roadmap order explicit and inspectable.
- Preserve the clean-core trust boundary in future packet planning.
- Prioritize benchmark credibility before adding new promoted findings.
- Prepare child packets that can be applied independently.

**Non-Goals:**

- Do not implement the child packets in this umbrella.
- Do not add new analyzer signals here.
- Do not make Ladon a proof checker or proof-correctness gate.
- Do not introduce a UI, graph database, LLM explanation layer, or Rust port.

## Decisions

1. Treat benchmark credibility as the first child.

   The review identified the main bottleneck as evidence quality, not signal
   count. The first child therefore creates portable fixtures and signal
   oracles before more findings are promoted.

2. Treat declaration source evidence as the second child.

   A stable declaration table with ranges, hashes, backend, method, and
   confidence strengthens report contracts and enables higher-confidence ProofIR
   joins without claiming proof truth.

3. Treat atlas workflow as the third child.

   The atlas is the product surface most aligned with maintainer needs:
   changed rows, recurring hotspots, review routing, evidence gaps, and optional
   ProofIR diagnostics.

4. Keep OpenSpec self-audit project-local for now.

   Packet hygiene is useful to this repo, but the review did not rank it as a
   core external product direction yet.

## Risks / Trade-offs

- Semantic overclaiming -> Keep non-claims in specs, docs, bridge cards, and
  report text.
- Benchmark overfitting -> Keep CI fixtures portable and treat Quux/MF/mathlib
  as optional smoke targets.
- Roadmap drift -> Keep child packet briefs and parent tasks as the ordering
  source of truth until implementation.
- Too much umbrella scope -> Stop this parent at readiness; apply the child
  packets separately.
