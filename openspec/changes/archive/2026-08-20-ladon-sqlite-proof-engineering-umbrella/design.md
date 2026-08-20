## Context

The existing proof-discovery umbrella established the direction but grouped several concerns too broadly. The implementation plan supplies a concrete SQLite/Lean/planner architecture and fifteen PR-sized packets. Existing project-local SQLite, process supervision, ProofIR, theorem-lineage, cache, and CLI contracts remain owners of their current concerns.

## Goals / Non-Goals

**Goals:** preserve the plan's PR order; make every child independently testable and recipe-like; keep SQLite as the only canonical persistent index; make Lean the only semantic applicability authority; bound every query and graph operation; reconcile legacy packet overlap explicitly.

**Non-Goals:** a graph database, Python emulation of Lean, implicit Lean execution from lexical commands, unbounded proof search, production-source mutation, or proof-completion claims without replay.

## Decisions

1. The fifteen plan PRs become fifteen child changes. This is more packets than the older umbrella, but each has one dominant ownership boundary and a crisp exit class.
2. Dependencies form five waves: baselines; immediate correctness/performance; semantic storage/extraction; verified P0 queries; adapters/planning/release.
3. Child specs are copied byte-for-byte into the umbrella and governed by a machine-readable ledger. The ledger also maps older proof-discovery concerns to the new owner so implementation does not fork.
4. Public contracts are versioned independently of disposable private schema v4. Old databases receive a rebuild instruction; no in-place migration is required.
5. SQLite performs set-oriented retrieval and deterministic shortlisting. Lean verifies applicability. Pure Python owns only bounded graph/planner algorithms over retrieved or Lean-verified facts.
6. The release packet owns the decision to mark overlapping legacy packets superseded; no legacy change is rewritten merely by creating this umbrella.

## Risks / Trade-offs

- [Fifteen packets create governance overhead] → keep one capability and recipe-like gate sequence per child.
- [Legacy packet duplication] → ledger concern mapping and release-time reconciliation gate.
- [Semantic storage is mistaken for proof authority] → authority fields and Lean verification requirements in every downstream spec.
- [Performance work changes answers] → baseline contracts and contract-equivalence gates precede optimization.
- [Large-project benchmarks vary by host] → portable correctness is authoritative; real-repository metrics use relative, fingerprinted gates.

## Migration Plan

Apply children in ledger order. Keep omitted build mode lexical, preserve compatibility aliases for one transition, rebuild incompatible disposable indexes, and publish each semantic generation atomically. Roll back by disabling semantic commands and retaining the prior lexical generation; no production Lean source is modified.

## Open Questions

- Whether a long-lived semantic worker belongs in P0 or a later latency packet.
- Whether measured dependency-index cost justifies a read-only dependency database after P0.
- Whether optional route-history storage is useful enough to enable after read-only route cards stabilize.
