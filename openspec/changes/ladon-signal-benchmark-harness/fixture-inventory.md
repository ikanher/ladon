# Portable Fixture Inventory

The benchmark harness reuses maintained fixtures by reference and adds only
integrated cases that need one installed CLI invocation across several signal
families.

| Owner | Existing fixture or oracle | Benchmark use |
| --- | --- | --- |
| clean core | `tests/fixtures/tiny_lean/` | Installed-CLI report stability, cold/warm runtime, report size, and text/JSON parity |
| portable signal oracles | `tests/fixtures/benchmark_oracles/` and `tests/test_benchmark_oracles.py` | Focused architecture, source-pattern, unresolved-reference, facade, generated, similarity, packet, and claim-authority predicates |
| signal correctness | `openspec/changes/ladon-signal-correctness-hardening/benchmark-handoff.md` | Reviewed positive, intentional-negative, and boundary labels for the integrated text and Lean cases |
| report contract v2 | `src/ladon/schemas/ladon-report-v2.schema.json` and `tests/fixtures/report_v1/` | Schema validation and bounded compatibility context; no duplicate report golden |
| Lean runtime | `openspec/changes/ladon-lean-extraction-runtime-hardening/benchmark-results.json` and `tests/fixtures/lean_runtime/` | Real Lean 4.32.1 evidence for three modules in one parser launch, warm hits, invalidation, and bounded runtime behavior |
| elaborated declarations | `openspec/changes/ladon-elaborated-declaration-surface/benchmark-handoff.md` and `tests/fixtures/lean_declarations/` | Real Lean declaration kinds, statement fields, direct type/value dependencies, trust facts, bounds, and parser-authority separation |
| Lean integration | `tests/fixtures/lean_integration/` | Real-Lean compatibility evidence; the required portable benchmark does not duplicate or invoke this toolchain fixture |

The static sources under `tests/fixtures/benchmark_harness/` are intentionally
integrated benchmark inputs. They are not replacement owners for the focused
fixtures above. The required suite contains no sibling checkout, absolute
maintainer path, Quux, matrix-factorization, or mathlib dependency.
