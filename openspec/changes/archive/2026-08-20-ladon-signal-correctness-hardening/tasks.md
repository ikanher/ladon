## 1. Reproduction Fixtures

- [x] 1.1 Add a CLI-level fixture where `Pkg.Owner` imports absent `Pkg.Missing` plus an absent external module.
- [x] 1.2 Add generated/handwritten importer fixtures that distinguish generic, generated, and handwritten fan-in populations.
- [x] 1.3 Add comment/string masking and declaration fixtures for modifiers, `opaque`, `axiom`, and `constant`.
- [x] 1.4 Add conventional parent-namespace and unrelated-namespace fixtures.
- [x] 1.5 Add proof-family pairs with identical coarse unresolved classes but disjoint concrete identifiers.
- [x] 1.6 Add duplicate-promotion and text `sorry`/axiom authority fixtures.

## 2. Structural Corrections

- [x] 2.1 Derive internal missing-import ownership from discovered/configured top namespaces rather than the exact selected owner.
- [x] 2.2 Compute generic, generated, and handwritten fan populations with filters on both importers and targets.
- [x] 2.3 Update fan table identifiers and rendered descriptions to name their actual populations.
- [x] 2.4 Implement offset-preserving comment/string masking for text declaration extraction.
- [x] 2.5 Recognize the documented declaration modifiers and kinds without presenting the scanner as complete Lean parsing.
- [x] 2.6 Update facade classification to consume the corrected declaration inventory.

## 3. Promotion Corrections And Raw Evidence

- [x] 3.1 Replace exact module/namespace equality with tested compatibility and unrelated-namespace diagnostics.
- [x] 3.2 Cap coarse-only proof-family similarity below the high-confidence band.
- [x] 3.3 Add stable semantic finding keys and deduplicate equivalent generic/handwritten promotions.
- [x] 3.4 Preserve raw metric rows while exposing promotion population, threshold, and authority metadata.
- [x] 3.5 Correct missing-import and lexical `sorry`/axiom raw rows with explicit text authority and nonclaim wording without adding a default finding family.

## 4. Integration And Gates

- [x] 4.1 Add installed-CLI regression assertions for every repaired signal and intentional negative.
- [x] 4.2 Update text and JSON rendering tests for counts, stable keys, population labels, and authority.
- [x] 4.3 Record labeled fixture/rationale handoff notes for the benchmark owner without editing its manifest or live-drift policy.
- [x] 4.4 Run `uv run --locked pytest -q tests/test_extraction.py tests/test_module_dag.py tests/test_findings.py tests/test_proof_family_similarity.py tests/test_render.py tests/test_clean_cli.py`.
- [x] 4.5 Run `uv run --locked python scripts/python_quality.py --strict`.
- [x] 4.6 Run `openspec validate ladon-signal-correctness-hardening --strict`.
