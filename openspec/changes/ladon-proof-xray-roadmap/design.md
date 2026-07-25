## Context

The alpha declaration child owns direct Lean-observed statement, dependency,
axiom, sorry, and unsafe facts. Completed proof-xray staging owns quoted
witness/trust rows. This roadmap is therefore limited to later tactic-skeleton
or InfoTree/proof-shape evidence with explicit authority and version metadata.

## Goals / Non-Goals

**Goals:**

- Define optional tactic-skeleton and InfoTree/proof-shape evidence rows.
- Keep parser candidates, direct declaration facts, quoted witnesses, and
  future proof-shape rows distinct.
- Consume the alpha declaration surface instead of defining another
  declaration extractor.

**Non-Goals:**

- No proof correctness gate.
- No theorem proving or proof search.

## Decisions

- Require backend, version, source-artifact, and confidence fields.
- Keep all rows as inspection aids, not proof truth.
- Do not claim a native generator, proof replay, or complete proof-dependency
  graph until a separately approved backend supplies and tests that evidence.

## Risks / Trade-offs

- Users may overread tactic rows -> Include nonclaims and field names that
  distinguish optional proof-shape evidence from declaration facts.
