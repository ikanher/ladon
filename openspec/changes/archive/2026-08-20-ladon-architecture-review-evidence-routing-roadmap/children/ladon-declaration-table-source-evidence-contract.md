# Child Packet: ladon-declaration-table-source-evidence-contract

## Purpose

Add a stable declaration source-evidence table to Ladon reports so declaration
graph rows, atlas cards, and ProofIR bridge joins are auditable.

## Expected Scope

- Report `declaration_graph.declarations` rows with declaration, module, kind,
  source path, source range, selection range, content hash, extraction backend,
  extractor version, name-resolution method, and confidence.
- Lean-helper normalization for available source and selection ranges.
- ProofIR bridge join ordering that prefers hash, then source range, then exact
  module/declaration, then basename-only warning.
- Report text and docs that clarify source attachment confidence is not proof
  truth.

## Non-Goals

- No elaborated proof dependency claims.
- No theorem-truth validation.
- No broad report schema rewrite beyond the declaration evidence contract.
