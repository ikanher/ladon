# Proposal

Add a deterministic atlas exporter that consumes Ladon report JSON files and
emits a compact graph for reviewer navigation.

# Scope

- Add pure atlas-building functions.
- Add a script to export atlas JSON and Markdown.
- Include report, module, declaration, finding, and review-region nodes.
- Include edges from reports to roots, findings, review regions, highlighted
  modules/declarations, and region signals.
- Run the exporter on the root-matrix evidence reports.

# Non-Goals

- No full module-edge duplication across every report.
- No graph layout engine.
- No schema migration/database layer.
