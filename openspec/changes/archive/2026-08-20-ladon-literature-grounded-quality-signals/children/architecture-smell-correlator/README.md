# Child 2: Architecture Smell Correlator

## Literature Basis

- `arxiv:2406.17354` Architectural smells and static-analysis warnings.
- `garcia:2015-architecture-recovery` Comparing software architecture recovery.
- `savidis:2022-architecture-mining` Dependency graph clustering and visualization.
- `yamaguchi:2014-cpg` Code Property Graphs.

## Problem

Ladon reports module-DAG signals and declaration graph signals separately. The
literature suggests architectural risk is stronger when multiple independent
signals correlate.

## Proposed First Slice

Add deterministic composite architecture findings:

- high module fan-in plus large root-import closure;
- facade-heavy module plus large fan-out;
- unreachable module count plus broad namespace inventory;
- declaration-family hotspot under a high-closure root import.

## Acceptance Bar

- No defect claims; findings say "architecture pressure".
- Composite findings cite component signals.
- Tests use synthetic module/declaration summaries.
- Smoke reports show whether Quux/matrix-factorization produce meaningful
  composite findings.
