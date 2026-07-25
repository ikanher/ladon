# `ladon-installed-reportset-workflow`

Owns packaging and ordinary CLI exposure of the existing atlas export, SQLite,
canned query, generic diff, reviewer-card, and workflow operations.

- Dependencies: bounded report projections, deterministic bundles, and
  actionable finding evidence links.
- Existing owners reused: all atlas/report-set algorithms and schemas.
- Excludes: reimplementing atlas logic, semantic theorem comparison, git-ref
  orchestration, graph databases, dashboards, or generated explanations.
- Exit: an isolated installed wheel can run the full report-to-bundle-to-atlas-
  query/diff flow outside the checkout; stdout/stderr and exit behavior match
  the shared CLI contract; unknown majors fail clearly; normalized outputs are
  deterministic and distinguish highlighted nodes from inventory counts.
