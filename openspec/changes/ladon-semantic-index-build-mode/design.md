## Context

Semantic extraction can be cached incrementally, but the public SQLite generation must remain atomic and self-consistent.

## Goals / Non-Goals

**Goals:** explicit modes, conservative cache keys, source-only discovery, fresh temporary assembly, validation, atomic replacement, and prior-generation survival.

**Non-Goals:** silent Lean execution from lexical mode or premature dependency/project database splitting.

## Decisions

1. Omitted mode remains lexical; semantic and hybrid are visibly Lean-executing commands with deadlines and initializer warnings.
2. Initial cache invalidation includes toolchain, helper/protocol, source, Lake state, transitive local imports, and compiled artifacts.
3. Assemble cache hits and new artifacts into a process-specific temporary database in the project-local index directory.
4. Publish only after coverage, FK/integrity, plan, size, and optimization gates pass.

## Risks / Trade-offs

- [Conservative invalidation costs time] → correctness first; later surface fingerprints can narrow invalidation.
- [Source changes during build] → identity recheck before atomic replacement.
