## 1. Schema And Compatibility Fixtures

- [x] 1.1 Inventory every current top-level section, reader, renderer, and optional absent-state behavior.
- [x] 1.2 Check in the `ladon-report-v2` JSON Schema as package resource `ladon:schemas/ladon-report-v2.schema.json` and include it in sdist/wheel.
- [x] 1.3 Add representative v1 JSON fixtures for analyses using the text-only backend, Lean, optional witness, packet, atlas, and empty-section inputs.
- [x] 1.4 Define stable sort keys, volatile metadata fields, extension registration, and the report-version policy.

## 2. Typed Report Model

- [x] 2.1 Implement typed metadata, diagnostic, finding, provenance, and phase-envelope models.
- [x] 2.2 Represent every registered phase as complete, skipped, partial, or failed with textual reason and counters.
- [x] 2.3 Replace numeric skip-reason lengths with preserved structured text.
- [x] 2.4 Add typed adapters at existing analysis phase boundaries and fail invalid adapters structurally.
- [x] 2.5 Add a typed extension registry/envelope and adapters for existing owners without defining their concrete payload schemas.

## 3. Serialization And Rendering

- [x] 3.1 Implement schema-valid canonical v2 JSON serialization with stable collection order.
- [x] 3.2 Stop injecting a wall-clock timestamp unless the caller supplies one and document timing normalization.
- [x] 3.3 Migrate compact text rendering to the typed v2 model.
- [x] 3.4 Add parity assertions for full selected totals, omitted-detail counts, displayed-row identifiers/severities/authority, and phase states.
- [x] 3.5 Validate every emitted test report against the packaged schema.

## 4. Readers And Migration

- [x] 4.1 Migrate atlas, SQLite, diff, workflow, and bridge readers to explicit version dispatch.
- [x] 4.2 Reject unknown major versions with actionable diagnostics.
- [x] 4.3 Implement a bounded JSON-only v1 compatibility serializer from canonical v2 data with information-loss warnings and invocation-error tests for text/dual-output combinations.
- [x] 4.4 Publish a field/state migration table and the one-v2-alpha compatibility-adapter removal milestone.

## 5. Gates

- [x] 5.1 Run schema validation and normalized-byte determinism across the representative report matrix.
- [x] 5.2 Run `uv run --locked pytest -q tests/test_pipeline.py tests/test_render.py tests/test_atlas.py tests/test_atlas_diff.py tests/test_atlas_sqlite.py tests/test_atlas_workflow.py tests/test_proofir_bridge.py`.
- [x] 5.3 Run `uv run --locked python scripts/clean_checkout_gate.py --candidate worktree --package-resource ladon:schemas/ladon-report-v2.schema.json` to inspect constrained sdist/wheel artifacts and the isolated installed resource.
- [x] 5.4 Run `uv run --locked python scripts/python_quality.py --strict`.
- [x] 5.5 Run `openspec validate ladon-report-contract-v2 --strict`.
