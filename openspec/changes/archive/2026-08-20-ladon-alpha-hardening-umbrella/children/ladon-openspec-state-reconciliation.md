# `ladon-openspec-state-reconciliation`

Owns the evidence ledger, stale active-packet disposition, strict-validation
repair, conflict-aware archive, canonical spec population, and roadmap/doc
reconciliation.

- Dependencies: none.
- Enables: repository-wide OpenSpec CI and truthful ownership for every other
  alpha child.
- Excludes: implementation of Review Radar, semantic changelog, or analyzer
  runtime behavior.
- Exit: no unowned residual requirement or misleading implemented-but-unchecked
  active packet remains, and the reconciled inventory passes its gates.
