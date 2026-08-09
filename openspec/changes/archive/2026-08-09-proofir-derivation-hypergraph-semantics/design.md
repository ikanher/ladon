## Context

Current obligation nodes approximate hyperedges, but path rendering loses conjunctive premise requirements and validation does not enforce all graph promises.

## Goals / Non-Goals

**Goals:** explicit steps, AND premises, OR alternatives, structured substitutions/context, and distinct bounded query meanings.

**Non-Goals:** a universal term AST, automated proof discovery, or claiming a navigation path is a proof.

## Decisions

1. A step has ordered premise statement refs, one conclusion ref, rule ref, substitutions, local-context ref, and observation refs.
2. Multiple steps concluding the same statement are OR alternatives; premises within a step are AND requirements.
3. Derivation, plan, and attempt-log are separate artifact kinds.
4. `navigation-path`, `derivation-slice`, `satisfaction`, `alternatives`, and `scc` are separate result schemas.
5. Acyclic artifacts reject cycles; recursive graphs explicitly declare SCC semantics.
6. Graph/SCC algorithms may be independently reimplemented from public algorithm descriptions, but no production or test import from Quux is permitted.

## Risks / Trade-offs

- [Slices grow combinatorially] → finite node/step/alternative/output caps and truncation ledgers.
- [Recursive SCC declarations can overstate semantics] → validate exact graph membership and retain structural-only nonclaims.

## Migration Plan

Create native derivation fixtures, add distinct navigation/slice/satisfaction/alternative/SCC queries, and migrate planner inputs directly to typed subjects and steps. Retired DAG fixtures remain deleted; no conversion path exists.

## Open Questions

- Recursive SCCs are inspectable structural metadata in v3.0; satisfaction intentionally remains invalid until a separately checked fixed-point semantics is specified.
