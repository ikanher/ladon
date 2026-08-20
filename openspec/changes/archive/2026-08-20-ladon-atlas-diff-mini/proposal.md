# Proposal

Add a deterministic diff for two Ladon atlas JSON artifacts.

# Why

The architecture-evolution literature points toward change analysis, not only
static smell detection. Reviewers need to know which findings appeared,
disappeared, or changed between two report roots.

# Scope

- Flatten atlas reports, findings, review regions, signals, declaration
  highlights, and module highlights into comparable rows.
- Report added, removed, and changed rows by category.
- Render JSON and compact Markdown diff outputs.
- Add a small script for command-line use.

# Non-Goals

- No semantic proof dependency diff.
- No graph edit-distance algorithm.
- No UI.
- No attempt to infer causality.
