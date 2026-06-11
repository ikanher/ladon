## 1. Fixture Corpus

- [x] 1.1 Add portable Lean fixtures for duplicate basenames, scoped/open syntax, local binder noise, field-like candidates, and repeated declaration families.
- [x] 1.2 Add portable module-DAG fixtures for broad facade imports, narrow owner roots, and intentional root-scope gaps.
- [x] 1.3 Add packet-evidence fixtures for complete, partial, missing, and profile-specific evidence.

## 2. Oracle Evaluator

- [x] 2.1 Define a small oracle schema for focused signal expectations.
- [x] 2.2 Implement a pure oracle evaluator over report payloads or focused analysis rows.
- [x] 2.3 Add human-readable failure messages that include fixture, signal, expected value, and observed value.

## 3. Tests And Workflow

- [x] 3.1 Add tests for positive and negative declaration-reference oracles.
- [x] 3.2 Add tests for unresolved-reference classification oracles.
- [x] 3.3 Add tests for proof-family, root-scope, and packet-evidence oracles.
- [x] 3.4 Add optional smoke handling for Quux, matrix-factorization, or mathlib paths without making CI depend on them.

## 4. Validation

- [x] 4.1 Run `openspec validate ladon-portable-benchmark-fixtures-and-signal-oracles --strict`.
- [x] 4.2 Run `uv run pytest -q tests`.
- [x] 4.3 Run `uv run python scripts/python_quality.py --strict`.
- [x] 4.4 Run `uv run python -m compileall -q src tests scripts`.
