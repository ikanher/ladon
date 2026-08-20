## Context

Ladon has many signals. Benchmark oracles prevent each signal from becoming
local folklore tied to one private repo.

## Goals / Non-Goals

**Goals:**

- Cover promoted signals with positive and negative fixtures.
- Prefer predicate oracles over full JSON snapshots.
- Separate live smoke evidence from CI fixtures.

**Non-Goals:**

- No dependency on private sibling repos in required tests.
- No numeric quality score from uncalibrated signals.

## Decisions

- Fixtures should be small synthetic Lean/source snippets.
- Oracles should check stable keys and predicates.

## Risks / Trade-offs

- Fixtures can overfit too -> Include adversarial negatives and document scope.
