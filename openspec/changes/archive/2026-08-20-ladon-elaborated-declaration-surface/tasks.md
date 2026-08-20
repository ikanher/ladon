## 1. Prerequisites And Lean Fixtures

- [x] 1.1 Confirm report-v2 extension and batched-helper protocol prerequisites are complete.
- [x] 1.2 Add real-Lean fixtures for theorem, definition, axiom, opaque, unsafe, implicit/typeclass binders, and imported notation.
- [x] 1.3 Add fixtures where parser identifiers disagree with elaborated type/value constants.
- [x] 1.4 Add root-only imported dependency, inventory join, direct `sorryAx`, direct axiom, and large-proof truncation cases.

## 2. Lean Helper Surfaces

- [x] 2.1 Serialize fully qualified name, kind, source range, source hash, and backend/toolchain metadata per declaration.
- [x] 2.2 Pretty-print the elaborated type with recorded options and decompose bounded binders/premises plus conclusion.
- [x] 2.3 Traverse type and value/proof expressions into separate deduplicated direct-constant sets.
- [x] 2.4 Emit declared-axiom, unsafe, direct `sorryAx`, and direct axiom-reference facts with scope.
- [x] 2.5 Replace the discarded full body tree with bounded statement excerpt, statement/proof ranges, and proof presence/form metadata.
- [x] 2.6 Emit explicit truncation and unavailable-state fields for every bounded surface.

## 3. Typed IR And Normalization

- [x] 3.1 Extend typed declaration IR and helper payload version for statement, source, dependency, bounded body, and trust fields.
- [x] 3.2 Normalize older helper payloads to explicit unavailable optional fields.
- [x] 3.3 Preserve parser candidates, type dependencies, and value dependencies as separate authority-bearing collections.
- [x] 3.4 Create imported declaration stubs and deterministic fully qualified-name joins for inventory rows.
- [x] 3.5 Bound and sort all surface collections before report serialization.

## 4. Graph And Report Integration

- [x] 4.1 Add typed report-v2 declaration-surface and elaborated-edge extensions.
- [x] 4.2 Keep parser and elaborated graph edge kinds separate in JSON, text, atlas, SQLite, and diff consumers.
- [x] 4.3 Render a bounded root declaration summary that lets a reviewer locate and read theorem statements.
- [x] 4.4 Render direct trust-footprint rows with Lean authority and no transitive or proof-truth overclaim.
- [x] 4.5 Emit a valid skipped/partial phase when elaboration is absent or incomplete.

## 5. Gates

- [x] 5.1 Add and run `scripts/lean_declaration_gate.py --required`; it provisions the tracked fixture's pinned reference toolchain, gives non-skippable real-Lean coverage to every declaration kind, statement decomposition, dependency split, and trust fixture, and treats unavailable Lean as failure.
- [x] 5.2 Add schema, normalized determinism, report-size, and text/JSON parity assertions.
- [x] 5.3 Run `uv run --locked pytest -q tests/test_lean_extraction.py tests/test_declaration_graph.py tests/test_pipeline.py tests/test_render.py tests/test_atlas.py tests/test_atlas_sqlite.py tests/test_atlas_diff.py`.
- [x] 5.4 Record portable declaration coverage cases and conservative cap evidence for later adoption by `ladon-signal-benchmark-harness`; do not block this child on the downstream harness.
- [x] 5.5 Run `uv run --locked python scripts/python_quality.py --strict`.
- [x] 5.6 Run `openspec validate ladon-elaborated-declaration-surface --strict`.
