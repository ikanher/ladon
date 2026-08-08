## Context

General CLI imports and repeated SQL materialization add overhead before semantic Lean work begins.

## Goals / Non-Goals

**Goals:** lazy installed dispatch, one lineage walk, set-oriented boundary/path-node loads, constant statement counts, contract equivalence.

**Non-Goals:** public result redesign or graph algorithm replacement, which belongs to the next packet.

## Decisions

1. Point the console script to a lightweight dispatcher that imports only the selected command family.
2. Keep package-level `main` as a lazy compatibility wrapper.
3. Materialize already-acquired walks and batch metadata by distinct IDs, restoring requested order in Python.

## Risks / Trade-offs

- [Lazy imports alter error timing] → installed-wheel help, stream, signal, and exit tests.
- [Batch joins reorder rows] → stable identity sorting and contract-equivalence fixtures.
