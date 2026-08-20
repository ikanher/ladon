## Why

Ladon now has module-DAG analysis and Lean-native root extraction. The next
kernel is declaration graph IR: a small pure representation of declaration
references that future proof graph, dead-surface, and root-to-frontier analyses
can share.

## What Changes

- Add `LeanDeclaration` IR for declaration names, module ownership, kind, and
  reference candidates.
- Add a pure declaration graph summary module.
- Keep this independent from CLI/report wiring for now.
- Add synthetic tests for declaration edges, unresolved references, fan-in,
  fan-out, and root reachability.

## Capabilities

### New Capabilities

- `ladon-declaration-graph`: Defines backend-agnostic declaration graph IR and
  pure summary analysis.

### Modified Capabilities

- None.

## Impact

- Affected code: `src/ladon/ir.py`, `src/ladon/analysis/`.
- Affected tests: new synthetic declaration graph tests.
- No CLI behavior changes in this packet.
