## Context

The preceding ProofIR evidence-graph umbrella established project-local storage. This umbrella consumes that substrate through five child packets whose contracts must remain authority-preserving and dependency ordered.

## Goals / Non-Goals

**Goals:** coordinate query semantics, negative evidence, repository triage, CLI presentation, and calibration; keep child tasks recipe-like; preserve duplicated capability specs byte-for-byte.

**Non-Goals:** new storage engines, raw dialect mirrors, LLM-only commands, or proof verification.

## Decisions

1. Dependency order is theorem dossier and route correctness first; negative evidence builds on their selectors; repository triage builds on normalized negative predicates; CLI/calibration integrates all four.
2. Each child owns one capability spec. The umbrella copies child specs exactly and carries a machine-readable dependency ledger.
3. Acceptance requires portable predicates before opt-in real-repository measurements. Performance is secondary to answer completeness and authority clarity.
4. The existing project-local SQLite database remains the sole canonical index.

## Risks / Trade-offs

- [Cross-packet schema drift] → byte-equal specs and strict OpenSpec validation.
- [Presentation begins before semantics stabilize] → CLI packet depends on all semantic children.
- [Overclaiming combined evidence] → mandatory separate sections and nonclaims throughout.

## Migration Plan

Apply children in ledger order and declare the umbrella complete only after all child exit classes and integrated calibration predicates pass.
