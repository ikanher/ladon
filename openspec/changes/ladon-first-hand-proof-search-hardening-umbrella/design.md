## Context

The prior SQLite proof-engineering umbrella created the intended surfaces, but first-hand use revealed that small unit tests and index-name validation allowed misleading coverage statuses, placeholder handlers, closure-wide recursive scans, uncontrolled post-build growth, and expensive default reports. This program is a corrective hardening pass over those existing owners.

## Goals / Non-Goals

**Goals:** preserve first-hand evidence; make packets TDD-first and recipe-like; align physical SQLite design with production SQL; enforce honest coverage and budgets; retain ordinary caller-neutral CLI and evidence authority.

**Non-Goals:** a graph database, implicit Lean execution, Python semantic proof authority, unbounded traversal, in-place private-schema migration, or production Lean-source edits.

## Decisions

1. Nine children form four waves: baseline; independent SQL/correctness fixes; ranking/report integration; operational release.
2. Every implementation child starts with a named failing fixture or populated plan assertion. Production edits before red evidence violate packet order.
3. Query-plan contracts inspect actual selective predicates on populated skewed data; index inventories remain necessary but insufficient.
4. The database stays project-local and disposable. Schema optimization uses atomic rebuild, while lineage remains mutable only under complete-budget, transaction, statistics, and plan gates.
5. Child capability specs are copied byte-for-byte under the umbrella and governed by a machine-readable dependency ledger.
6. Existing lineage, ProofIR, proof-search, CLI, and architecture contracts remain integration owners; this program hardens them rather than creating parallel surfaces.

## Risks / Trade-offs

- [Physical optimization changes behavior] → freeze payloads first and require contract equivalence except explicitly versioned corrections.
- [Plan assertions overfit SQLite wording] → normalize to relation, access method, and complete leading predicate.
- [Nine packets create overhead] → each packet has one owner, exact files/tests, and a crisp exit class.
- [Large-project timing varies] → portable plan/count gates are authoritative; calibration is same-host and fingerprinted.

## Migration Plan

Apply baseline first. Then apply lineage query, storage lifecycle, schema rightsizing, ProofIR paths, coverage semantics, and binder explanation according to the ledger. Apply ranking/projection after baseline and finish with release integration. Rebuild incompatible databases; do not migrate in place.

## Open Questions

- Final default complete-database budget and default lineage view are release decisions informed by calibration.
