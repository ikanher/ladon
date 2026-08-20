## Why

Ladon now has a clean core, but its docs and comments should be held to the
same standard as its radon/vulture gate. We should adapt the proven
matrix-factorization doc-hardening pattern into a Ladon-specific skill and use
it immediately on the active code and docs.

## What Changes

- Add a project-local `ladon-doc-hardening` skill based on the
  matrix-factorization `lean-doc-hardening` and `opacus-doc-hardening` skills.
- Define Ladon-specific documentation rules for analyzer code:
  operational responsibility first, exact support boundary, selective comments
  at non-obvious seams, and no legacy overclaiming.
- Harden active clean-core module docstrings, public dataclass/function
  docstrings, README wording, and architecture docs.
- Keep this documentation-only except for harmless comment/docstring edits.

## Capabilities

### New Capabilities

- `ladon-doc-hardening`: Defines Ladon's documentation/comment hardening
  workflow for Python analyzer modules, Lean helper notes, README/architecture
  docs, and skill text.

### Modified Capabilities

- None.

## Impact

- Affected files: `.codex/skills/`, `src/ladon/`, `README.md`, and
  `docs/ARCHITECTURE.md`.
- Affected workflow: future Ladon doc/comment edits should use the new skill.
- Validation remains unchanged: strict Python quality, tests, compileall, and
  build must still pass.
