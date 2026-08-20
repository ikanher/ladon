# `ladon-theorem-capsule-planning`

Resolves one fully qualified theorem under the pinned Lean environment and emits a
deterministic, drift-detecting plan with separate semantic and build closures.

- Dependencies: declaration source evidence, elaborated declaration evidence, the
  canonical module DAG, snapshot/configuration identity, Lean helper supervision,
  and the installed CLI contract.
- Enables: deterministic materialization from reviewed, complete evidence.
- Excludes: report-capped dependencies as completeness evidence, target writes,
  target-controlled discovery initializers, source copying, minimization, or replay.
- Exit: portable fixtures prove exact selection, closure beyond presentation caps,
  typed semantic/build frontiers, deterministic plans, drift rejection, and explicit
  unsupported-facet handling.
