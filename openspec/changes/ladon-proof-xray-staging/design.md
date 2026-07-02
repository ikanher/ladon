## Context

Proof x-ray rows may come from InfoTree, LeanDojo/Pantograph-like tooling, or
project-local scripts. Ladon must preserve backend authority and stay absent-safe.

## Goals / Non-Goals

**Goals:**
- Normalize proof-shape rows.
- Require explicit authority labels.
- Report automation and trust-footprint pressure.

**Non-Goals:**
- Do not infer elaborated dependencies from parser candidates.
- Do not validate proof correctness.

## Decisions

- Use `parser_observed`, `lean_elaborated`, `external_tool_quoted`, and
  `unknown` authority labels.
- Emit weak-metadata diagnostics when backend/version/confidence is incomplete.

## Risks / Trade-offs

- Backends vary widely; mitigate by accepting compact quoted rows and preserving
  nonclaim text.
