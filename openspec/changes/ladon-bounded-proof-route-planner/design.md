## Context

A proof route applies alternative theorems to individual goals while requiring all resulting premises, yielding an AND/OR state space.

## Goals / Non-Goals

**Goals:** canonical states, Lean-verified transitions, deterministic best-first search, exhaustive bound reporting, reusable route cards, and optional replay.

**Non-Goals:** arbitrary tactic synthesis, unbounded search, or mutating the published SQLite index.

## Decisions

1. A state is a canonical multiset of unresolved goal fingerprints; a transition replaces one selected goal with every residual proof premise.
2. Cost is lexicographic over verified match class, unresolved count/size, adapters, instances, scope, ownership, depth, and stable identity.
3. Every expansion performs SQLite shortlisting followed by batched Lean verification.
4. Optional rejected-route history uses a separate WAL sidecar keyed by all generation/context/policy identities.

## Risks / Trade-offs

- [Search explosion] → explicit state, candidate, depth, goal, request, route, and byte caps.
- [Route becomes stale] → exact identities and optional scratch replay before `replayed` status.
