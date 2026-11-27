# Proposal

## Why

On the three files in the README demo, `rg -nF` found `fourier_gaussian_real_place` at the same line as Ladon. The README should lead with a reproducible example where Ladon helps answer a theorem-reuse question that goes beyond finding a known literal.

## What Changes

- Replace the headline example with three progressively richer type searches over one Mathlib index. Start with a single fragment, combine clues in one signature, then check applications against a concrete goal using Lean.
- Compare the type queries with literal and formatting-aware source searches during verification. Keep the README focused on the examples and identify what comes from matching source signatures and what comes from checking in Lean.
- Keep the Gaussian example available in the standalone RH walkthrough.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. This is a documentation change using released commands.

## Impact

The README links to a pinned Mathlib setup and application check. The RH walkthrough gains standalone setup for the original queries.
