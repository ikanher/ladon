## 1. IR And Extraction

- [x] 1.1 Extend declaration IR or report row construction with optional source path, source range, selection range, content hash, backend, extractor version, method, and confidence fields.
- [x] 1.2 Normalize available Lean helper range data into declaration evidence rows.
- [x] 1.3 Compute deterministic source content hashes for extracted declaration files.

## 2. Report Contract

- [x] 2.1 Add `declaration_graph.declarations` to JSON reports when declaration IR exists.
- [x] 2.2 Render concise declaration evidence and confidence information in text reports where useful.
- [x] 2.3 Update docs to describe declaration evidence fields and non-claims.

## 3. Bridge And Atlas Consumers

- [x] 3.1 Update ProofIR bridge declaration-row loading to prefer explicit rows.
- [x] 3.2 Update bridge join precedence and diagnostics for hash, range, module/declaration, basename-only, and unmatched joins.
- [x] 3.3 Update atlas export/cards to preserve or summarize declaration evidence confidence where relevant.

## 4. Tests And Validation

- [x] 4.1 Add tests for explicit declaration table rows from synthetic Lean helper payloads.
- [x] 4.2 Add bridge tests proving hash/range joins outrank module and basename joins.
- [x] 4.3 Add adversarial tests proving basename-only joins remain warning-only.
- [x] 4.4 Run `openspec validate ladon-declaration-table-source-evidence-contract --strict`.
- [x] 4.5 Run `uv run pytest -q tests`.
- [x] 4.6 Run `uv run python scripts/python_quality.py --strict`.
