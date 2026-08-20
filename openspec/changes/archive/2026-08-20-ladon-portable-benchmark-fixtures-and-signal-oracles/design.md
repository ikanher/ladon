## Context

Current calibration is useful but local: Quux, matrix-factorization, generated
temp reports, and synthetic unit tests. That supports internal development but
is not enough for external credibility. The new benchmark layer should make
signal behavior reproducible from the Ladon repository alone.

## Goals / Non-Goals

**Goals:**

- Add portable fixtures that exercise the highest-risk Ladon signals.
- Add deterministic oracles over focused report fields and analysis outputs.
- Make fixture failures explain expected versus observed signal behavior.
- Keep external repo smoke runs optional.

**Non-Goals:**

- Do not add new analyzer findings in this packet.
- Do not depend on sibling checkouts or network access.
- Do not introduce exact full-report snapshots as goldens.
- Do not claim benchmark coverage proves theorem correctness.

## Decisions

1. Use focused signal oracles, not full-report snapshots.

   Full reports include timing, ordering, and incidental rows that make tests
   brittle. Oracles should target named signals such as resolved edge,
   actionable unresolved candidate, parser noise, proof-family candidate,
   root-scope class, and packet profile status.

2. Keep fixture inputs small and source-local.

   Lean fixtures should live under `tests/fixtures/` or a similarly portable
   source tree. Packet fixtures should be small directories with enough files to
   trigger evidence classes.

3. Separate CI fixtures from optional smoke roots.

   Quux, matrix-factorization, and mathlib remain useful but optional. Built-in
   expectation suites can keep skip/report behavior when those paths are absent.

4. Make the oracle evaluator reusable.

   A pure module can evaluate report payloads and focused rows; a small script
   can print predicate results for local generated reports.

## Risks / Trade-offs

- Fixture bias -> Include negative and ambiguous cases, not only examples that
  make Ladon look good.
- Too much benchmark machinery -> Start with the signal classes already present
  in reports.
- Lean version drift -> Keep parser-helper fixtures minimal and mark Lean-only
  tests skip-capable when Lean is unavailable.
