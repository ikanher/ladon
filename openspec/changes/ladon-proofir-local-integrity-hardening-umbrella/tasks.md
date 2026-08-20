## 1. Freeze red regressions and compatibility baselines

- [x] 1.1 Add owned 1,500-or-more-step linear derivation fixtures proving satisfaction and complete-slice queries currently exceed Python's recursion depth while remaining inside declared ProofIR budgets.
- [x] 1.2 Freeze canonical shallow-graph outputs for AND premises, stable OR alternatives, acyclic rejection, supported SCCs, and every derivation truncation cause before refactoring traversal.
- [x] 1.3 Add negative identity fixtures that distinguish whole-file SHA-256 digests from detached native-v3 artifact IDs even when both use the `sha256:` textual form.
- [x] 1.4 Add semantic-worker fixtures for an explicit valid toolchain, ambient `PATH` shadowing, repository-pin mismatch, missing executables, and sanitized environment behavior.
- [ ] 1.5 Add a table-driven projection corpus covering explicit live checks, ambient checks, stored observations, residual applications, partial coverage, invalid children, truncation, and analyses that were not run.

## 2. Make derivation queries stack-safe

- [x] 2.1 Replace recursive structural-satisfaction evaluation with explicit traversal frames and memoized terminal states while preserving existing budget charging and result schemas.
- [x] 2.2 Replace recursive complete-slice expansion with explicit traversal frames that preserve ordered premises, stable alternatives, cycle/SCC handling, deduplication, and canonical output ordering.
- [x] 2.3 Verify deep in-bound queries complete without `RecursionError` and deep out-of-bound queries terminate only through the exact declared depth, node, edge, alternative, or output limit.
- [x] 2.4 Run the focused derivation, SCC, query-contract, and installed proof-search CLI suites and compare all frozen shallow outputs byte-for-byte.

## 3. Separate digest and artifact identity domains

- [x] 3.1 Introduce field-specific validated `FileDigest` and `ContentArtifactId` representations and update function signatures so raw file hashes cannot be passed as detached artifact IDs.
- [x] 3.2 Extend ProofIR catalog discovery to retain each raw file digest and, independently, the validated native-v3 envelope artifact ID when validation establishes one.
- [x] 3.3 Implement manifest-link policy v2 with `resolvedFileDigest`, nullable validated `resolvedArtifactId`, domain-specific drift diagnostics, and no heuristic interpretation of legacy observations.
- [ ] 3.4 Bump affected derived result or proof-search index versions, rebuild disposable test indexes, and regenerate repository-owned snapshots without changing canonical native-v3 artifact IDs.
- [x] 3.5 Add validation, catalog, link-observation, projection, and round-trip tests proving equal-looking cross-domain values cannot be substituted or compared.

## 4. Bind live checks to an explicit Lean toolchain

- [x] 4.1 Add an immutable local toolchain context containing the resolved repository root, absolute Lake and Lean paths, exact `lean-toolchain` content and digest, executable identities, selection mode, and effective environment-key policy.
- [x] 4.2 Implement fail-closed context resolution that verifies executable files and versions against the repository pin and never falls back from explicit selection to ambient `PATH`.
- [x] 4.3 Launch semantic candidate checks with absolute executables, the explicit working directory, and a sanitized allowlisted environment; bind the selected context into environment and checker observations.
- [x] 4.4 Add CLI/API selection for explicit toolchain inputs and explicitly requested ambient discovery, with stable diagnostics for pin, path, version, and environment failures.
- [ ] 4.5 Verify ambient shadow executables are ignored under explicit selection, ambient mode is labeled non-authoritative, mismatches fail before launch, and failed checks publish no accepted artifacts.

## 5. Separate authority from analysis completeness

- [x] 5.1 Add closed typed authority-selection and `analysisCompleteness` states to semantic candidate results and shared evidence-result models without using declaration-replay terminology for application checks.
- [ ] 5.2 Implement exhaustive derivation rules for `complete`, `partial`, `invalid`, and `not-assessed` from registered populations, residuals, operation validity, omissions, and truncation.
- [ ] 5.3 Update persistence readers, theorem dossiers, aggregate summaries, and renderers so reloaded observations remain stored evidence and every projection preserves or weakens both axes.
- [ ] 5.4 Add projection invariants that reject authority or completeness escalation and ensure absent optional analysis is never defaulted to complete.
- [ ] 5.5 Update JSON/text fixtures and run candidate-worker, ProofIR query, dossier, coverage, and rendering suites across the full projection corpus.

## 6. Document migration and preserve repository separation

- [ ] 6.1 Document the link-policy/result break, disposable index rebuild, explicit-toolchain invocation, authority vocabulary, completeness states, and theorem-truth nonclaims in the ProofIR operator and schema documentation.
- [ ] 6.2 Add or extend repository-owned dependency scans proving production, packaged, build, test, and calibration paths do not import, execute, or require Quux.
- [ ] 6.3 Record object stores, provenance lattices, signed anchors, repository-closure policies, Lean trust-core predicates, and distinct future digest prefixes as deferred rather than implicit dependencies of this packet.

## 7. Umbrella closure gates

- [ ] 7.1 Run strict OpenSpec validation for this umbrella and verify every modified requirement has executable positive, boundary, and adversarial coverage.
- [ ] 7.2 Run all focused ProofIR v3, derivation, catalog, link-observation, semantic-worker, dossier, installed-CLI, and clean-environment tests.
- [ ] 7.3 Run the full Python test suite and repository quality/type/lint gates with Quux unavailable from the dependency path.
- [ ] 7.4 Run snapshot or generated-artifact verification and `git diff --check`, then record exact commands and outcomes before claiming the umbrella complete.
