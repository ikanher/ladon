# Tasks

- [x] Create `.codex/skills/ladon-doc-hardening/SKILL.md` from the
  matrix-factorization doc-hardening patterns.
- [x] Harden README wording so current clean-core support and future features
  are clearly separated.
- [x] Harden `docs/ARCHITECTURE.md` around clean-core module boundaries and
  support limits.
- [x] Add or improve module/public-contract docstrings in active `src/ladon/`
  modules.
- [x] Add concise inline comments only at non-obvious analyzer seams.
- [x] Re-read edits and remove filler comments or overclaims.
- [x] Validate with `openspec validate ladon-doc-hardening-skill-pass --strict`.
- [x] Validate with `uv run pytest -q`.
- [x] Validate with `uv run python scripts/python_quality.py --strict`.
- [x] Validate with `uv run python -m compileall -q src tests scripts`.
- [x] Validate with `uv build`.
