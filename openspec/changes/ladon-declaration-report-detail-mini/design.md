## Design

### Goal

Make declaration graph output useful without adding new analysis semantics.

### Report Detail

JSON should include:

- `top_unresolved_references`: candidate, count, sample sources.

Text should include:

- top declaration fan-in rows;
- top declaration fan-out rows;
- top unresolved references.

Limit all text sections to a small sample to keep reports readable.

### Validation

```bash
openspec validate ladon-declaration-report-detail-mini --strict
uv run pytest -q
uv run python scripts/python_quality.py --strict
uv run python -m compileall -q src tests scripts
uv build
bin/ladon --repo-root /home/codex/projects/quux --root Quux/Semantics/Propagation.lean --extraction-backend lean --lean-extraction-scope root --output-json /tmp/ladon-lean-detail.json --output-text /tmp/ladon-lean-detail.txt
```
