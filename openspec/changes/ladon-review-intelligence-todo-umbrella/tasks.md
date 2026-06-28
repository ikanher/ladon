## 1. Policy Workflow

- [x] 1.1 Create a child packet for repo-local policy persistence and validation.
- [x] 1.2 Add tests for discovered policy source reporting and missing-policy status.
- [x] 1.3 Add docs and examples for `.ladon/architecture-policy.json` and `.ladon/source-pattern-policy.json`.
- [x] 1.4 Smoke a repo-local policy run on a fixture without passing policy paths on the CLI.

## 2. Fix-Oriented Architecture Triage

- [x] 2.1 Create a child packet for fix-oriented policy finding summaries.
- [x] 2.2 Add tests for direct peer-import suggestions with source path, line, group pair, and context class.
- [x] 2.3 Add summary-first text output tests for pair summaries, top offending files, and top common-layer candidates.
- [x] 2.4 Add JSON fields for suggested actions without changing proof or correctness authority.

## 3. Common Layer and Facade Quality

- [x] 3.1 Create a child packet for broad common-layer ranking and facade quality.
- [x] 3.2 Add fixtures for multi-group common dependency positives and intentional shared-foundation negatives.
- [x] 3.3 Add tests that pure barrels and generated aggregation modules are separated from implementation fan-out.
- [x] 3.4 Add tests that mixed barrel/theorem modules are reported as review-pressure rows.

## 4. Generated Artifact Attribution

- [x] 4.1 Create a child packet for generated-artifact attribution.
- [x] 4.2 Add fixtures for duplicate imports emitted by generated modules.
- [x] 4.3 Add grouping by likely generator family and target module.
- [x] 4.4 Add generator-cleanup hints that expose evidence and remain non-authoritative.

## 5. Configurable Lexical Audit Packs

- [x] 5.1 Create a child packet for reusable source-pattern policy packs.
- [x] 5.2 Add pack fixtures for stale terms, local trust markers, TODO classes, and banned prose.
- [x] 5.3 Add tests for zero-match reports, capped match reports, generated filtering, and invalid pattern diagnostics.
- [x] 5.4 Document that project terms live in policy packs, not analyzer code.

## 6. Benchmark and Oracle Coverage

- [x] 6.1 Create a child packet for portable review-signal benchmarks.
- [x] 6.2 Add positive and negative fixtures for architecture policies, source-pattern scans, claim authority routes, common-layer candidates, facade subtypes, and generated attribution.
- [x] 6.3 Add an oracle runner that checks semantic predicates instead of whole JSON snapshots.
- [x] 6.4 Keep Matrix-Factorization and Quux smoke runs optional and outside required CI fixtures.

## 7. Lean Semantic Roadmaps

- [x] 7.1 Create a child packet for theorem-surface changelog extraction.
- [x] 7.2 Define theorem-surface rows for type changes, added premises, conclusion drift, name/type drift, and proof-only changes.
- [x] 7.3 Create a child packet for proof x-ray roadmap boundaries.
- [x] 7.4 Define future elaborated evidence rows for tactic skeletons, axiom/sorry footprint, proof shape, and dependencies with explicit authority labels.

## 8. Umbrella Gates

- [x] 8.1 Run `openspec validate ladon-review-intelligence-todo-umbrella --strict`.
- [x] 8.2 Run the relevant focused tests for any child packet implemented from this umbrella.
- [x] 8.3 Run `uv run python scripts/python_quality.py --strict` after code changes in child packets.
- [x] 8.4 Record live smoke evidence separately from portable fixture evidence.
