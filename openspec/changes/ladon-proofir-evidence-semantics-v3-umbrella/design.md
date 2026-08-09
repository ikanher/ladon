## Context

Ladon currently catalogs several ProofIR dialects and projects them into claims, surfaces, replay rows, DAGs, attachments, dossiers, and triage findings. The adapters preserve useful evidence boundaries, but compatibility conventions are becoming de facto semantics. Quux is a separated research playground and is outside Ladon's inspection, execution, dependency, and calibration boundary.

## Goals / Non-Goals

**Goals:** define one small native-v3 proof-evidence kernel; preserve exact authority and coverage boundaries; derive SQLite and review views; remove legacy ambiguity; make Rust parity feasible.

**Non-Goals:** a universal proof-term AST, a new theorem prover, implicit Lean execution, direct Quux dependencies, in-place SQLite migration, or treating successful processes as theorem truth.

## Decisions

1. Eight changes form four waves: native identity/observation/attachment/schema; derivation; SQLite/Ladon release; Rust parity.
2. Every child begins with red conformance fixtures or invariant tests before production edits.
3. Canonical artifacts remain immutable filesystem objects; SQLite remains a disposable projection.
4. The semantic kernel is envelope, environment, subject, claim, step, observation, and coverage. Surfaces, dossiers, cards, and governance witnesses are derived projections or namespaced extensions.
5. Quux is a separated research playground and SHALL NOT be inspected, executed, imported, or used for calibration. Ladon/ProofIR algorithms are independently implemented and proven with portable owned fixtures.
6. Child capability specs are copied byte-for-byte into the umbrella and governed by a machine-readable dependency ledger.
7. Rust work cannot begin until v3 canonical bytes, schemas, validation diagnostics, and normalized rows are frozen by the language-neutral corpus.
8. Legacy ProofIR kinds are deleted rather than converted. Discovery emits one stable unsupported-legacy diagnostic and never projects their content.

## Risks / Trade-offs

- [Deleting compatibility loses useful semantics] → rewrite only useful semantic cases as native-v3 fixtures, without retaining legacy field or serialization contracts.
- [A broad redesign stalls integration] → children have narrow ownership and executable exit gates.
- [Research algorithms leak into production dependencies] → CI runs portable gates with Quux absent.
- [Identity changes break stored references] → require a clean artifact regeneration and disposable database rebuild; do not migrate stale rows.

## Migration Plan

Delete the obsolete compatibility packets and routes. Freeze the native-v3 envelope, identity, observation, and attachment contracts together, then land derivation semantics. Build a fresh SQLite projection and route Ladon consumers exclusively through it. Start Rust only after cross-language fixture hashes and normalized rows are immutable.

## Open Questions

- Which Lean environment inputs form the minimum sound Merkle manifest?
