# Design

The atlas is a compact graph:

- nodes have `id`, `kind`, `label`, and optional `data`;
- edges have `source`, `target`, `kind`, and optional `data`;
- report paths are relative to the input report directory;
- module and declaration node IDs are scoped by repo key to avoid collisions
  between Quux and matrix-factorization;
- finding and region nodes are scoped by report path.

The exporter intentionally focuses on report-surface evidence:

- analysis roots;
- top fan-in/fan-out modules;
- top declaration fan-in/fan-out;
- findings;
- review regions and their signals.

Full module import edges remain in source reports. The atlas links to the
important rows instead of multiplying full DAGs by report count.
