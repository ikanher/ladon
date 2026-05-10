## Design

### Goal

Improve declaration graph usefulness without pretending to be Lean elaboration.

### Resolution Policy

For each candidate reference from declaration `source`:

1. If the candidate exactly matches a known declaration, resolve it.
2. Else if `source.module + "." + candidate` exists, resolve it.
3. Else if exactly one known declaration has basename equal to candidate,
   resolve it.
4. Otherwise leave it unresolved.

Do not resolve ambiguous basenames. Do not infer imports, namespaces, notation,
or projection syntax in this packet.

### Validation

```bash
openspec validate ladon-declaration-reference-resolution-mini --strict
uv run pytest -q
uv run python scripts/python_quality.py --strict
uv run python -m compileall -q src tests scripts
uv build
bin/ladon --repo-root /home/codex/projects/quux --root Quux/Semantics/Propagation.lean --extraction-backend lean --lean-extraction-scope root --output-json /tmp/ladon-lean-resolved.json --output-text /tmp/ladon-lean-resolved.txt
```
