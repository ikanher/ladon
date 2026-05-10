## Design

### Source Patterns

The matrix-factorization skills provide the source pattern:

- `lean-doc-hardening`: theorem-facing prose, honest boundaries, first-mention
  citations, selective comments at proof/notation seams.
- `opacus-doc-hardening`: public API responsibility first, exactness/bound
  semantics, runtime-to-math mappings, selective comments around delicate code.

Ladon needs the same shape, but for analyzer code instead of theorem proofs or
accountant runtime APIs.

### Ladon Adaptation

The Ladon skill should enforce:

- public docs state operational responsibility first;
- reports and docs distinguish implemented clean-core behavior from planned
  proof/witness/packet audits;
- functions/dataclasses with nontrivial contracts document inputs, outputs, and
  failure behavior;
- comments appear only at analyzer seams that are easy to misread:
  CLI compatibility aliases, root/module resolution, graph direction, quality
  thresholds, and unsupported legacy boundaries;
- no filler comments or claims that the clean core audits proof declarations,
  witnesses, packets, or export surfaces.

### Documentation Pass Scope

Harden:

- `README.md`
- `docs/ARCHITECTURE.md`
- active modules under `src/ladon/`
- `scripts/python_quality.py`

Do not edit generated caches or deleted legacy files.

### Validation

Expected validation:

```bash
openspec validate ladon-doc-hardening-skill-pass --strict
uv run pytest -q
uv run python scripts/python_quality.py --strict
uv run python -m compileall -q src tests scripts
uv build
```
