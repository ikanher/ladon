## Context

One-step adapters bridge common proof boundaries, but hard-coded repository names and unchecked policy would create a second semantic authority.

## Goals / Non-Goals

**Goals:** inspectable versioned rules, built-in and repository sources, declaration resolution, direction/cost/side conditions, and Lean verification.

**Non-Goals:** asserting repository policy as theorem truth or enabling unbounded adapter chains.

## Decisions

1. Built-ins cover generic Lean/Mathlib boundaries; repository JSON covers domain representations, ranges, aliases, and designated theorem families.
2. Registry loading validates schema and fingerprints policy; stale, conflicting, absent, and unresolved rules are explicit.
3. An adapter becomes viable only after Lean verifies its application; side conditions become residual goals.

## Risks / Trade-offs

- [Noisy or false policies] → advisory authority until named declarations resolve and applications verify.
- [Direction mistakes] → direction-specific fixtures and result fields.
