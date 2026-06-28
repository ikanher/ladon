## Context

The current clean core is parser/text-first. Proof x-ray belongs to a later
backend with explicit authority and version metadata.

## Goals / Non-Goals

**Goals:**

- Define proof-shape evidence rows.
- Keep parser candidates and elaborated dependencies distinct.
- Add trust footprint labels.

**Non-Goals:**

- No proof correctness gate.
- No theorem proving or proof search.

## Decisions

- Require backend, version, and confidence fields for proof x-ray rows.
- Keep all rows as review evidence, not proof truth.

## Risks / Trade-offs

- Users may overread tactic/dependency rows -> Include trust notes and field
  names that distinguish authority levels.
