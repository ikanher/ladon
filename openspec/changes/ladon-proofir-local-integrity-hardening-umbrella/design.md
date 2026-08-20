## Context

Ladon's native ProofIR v3 stack deliberately owns its schemas, algorithms, fixtures, and authority vocabulary. A comparison with recent work in the separated Quux research repository exposed four Ladon-local seams: recursive derivation evaluation can fail before a declared ProofIR depth bound is reached; discovery records a whole-file digest under the name `resolvedArtifactId`; semantic candidate checks select `lake` and `lean` through ambient `PATH`; and some result projections lack an explicit distinction between source/check authority and analysis completeness.

The canonical native-v3 detached artifact identity is already correct and remains stable. SQLite is a rebuildable projection. The semantic candidate operation currently checks an exact candidate application and may return residual goals; it is not equivalent to replaying a declaration's proof value. Existing typed observations, coverage populations, SCC policy, and bounded query schemas remain the governing model.

## Goals / Non-Goals

**Goals:**

- Make valid derivation graphs stack-safe up to explicit ProofIR query budgets.
- Prevent raw bytes, canonical artifacts, environments, and executables from being joined through an untyped `sha256:` string.
- Make trusted-local Lean execution reproducible and attributable to caller-selected executable and repository state.
- Make authority and completeness independent, closed, non-escalating result dimensions.
- Preserve native-v3 canonical identities and implement all behavior with Ladon-owned code and fixtures.

**Non-Goals:**

- Importing or executing Quux from Ladon production, tests, builds, or calibration.
- Adopting Quux's wire dialect, persistence model, object store, provenance lattice, signed anchors, repository-closure policy, or Lean trust-core definitions.
- Claiming theorem truth or declaration-proof replay from a candidate-application check.
- Changing detached native-v3 artifact IDs or migrating disposable SQLite state in place.
- Removing finite query, process, memory, collection, or output bounds.

## Decisions

1. **Use explicit traversal frames for derivation evaluation and slicing.** Satisfaction and complete-slice queries will maintain an explicit work stack plus memoized node/step states. Entry and exit frames will preserve current AND-premise, OR-alternative, stable ordering, truncation, and SCC behavior without invoking Python recursively on graph-controlled depth. Query budgets are charged at the same semantic events as today and remain the only advertised depth/work limits. Raising Python's recursion limit was rejected because it remains process-global, platform-dependent, and disconnected from the public query contract.

2. **Keep the v3 digest spelling but separate identity domains in code and results.** A validated `FileDigest` represents SHA-256 over exact discovered bytes. A validated `ContentArtifactId` represents the detached canonical artifact transform. Their current textual forms may both begin with `sha256:`, but constructors, function parameters, result fields, and comparison helpers will not accept them interchangeably. A future ProofIR wire version may introduce distinct prefixes; this packet does not silently change v3 canonical bytes.

3. **Version the manifest-link observation correction.** Link policy v2 replaces a raw-digest `resolvedArtifactId` with `resolvedFileDigest` and adds nullable `resolvedArtifactId`, populated only from a successfully validated native artifact envelope. Drift diagnostics compare like domains: declared artifact ID to validated artifact ID, while file-digest changes receive a distinct diagnostic. Old derived link observations are discarded by rebuilding the proof-search index; no compatibility alias will preserve the incorrect meaning.

4. **Require an explicit toolchain context for authority-eligible live checks.** A `LeanToolchainContext` will bind a resolved repository root, absolute `lake` and `lean` executables, the exact `lean-toolchain` file content and digest, executable identities, and a minimal allowlisted environment. Before launch, Ladon verifies paths, pin compatibility, and repository containment assumptions, then invokes absolute executables with an explicit working directory. Caller-requested ambient discovery may resolve a convenience context, but the result is labeled `ambient-selected` and cannot receive the authority classification reserved for explicit selection. Silently falling back from explicit selection to ambient `PATH` is forbidden.

5. **Bind result authority to the live operation, not stored evidence.** Candidate-check results will expose an authority basis describing how this exact process was selected and what it checked. Because the operation elaborates a candidate application rather than replaying a declaration proof value, its strongest label will be application-check-specific rather than `lean_replayed`. Reloaded artifacts and database rows remain `stored-observation` even if they quote a formerly successful live run.

6. **Model analysis completeness as a separate closed axis.** Live checks and derived dossier summaries will expose `analysisCompleteness` with `complete`, `partial`, `invalid`, or `not-assessed`. Completeness is derived from registered required populations and terminal operation state; an omitted analysis is `not-assessed`, never complete. Coverage, residuals, truncation, invalid input, or unavailable selectors can only preserve or lower completeness. No projection rule may strengthen authority or completeness.

7. **Land the umbrella as four ordered workstreams with shared gates.** The order is stack-safe derivations, identity-domain separation, explicit toolchain selection, then authority/completeness projections. Identity and result-schema work may require a proof-search index/result schema bump and fixture regeneration, but not a canonical native-v3 artifact version change. Each workstream starts with a red regression or adversarial fixture and remains independently revertible.

## Risks / Trade-offs

- [An iterative solver changes stable OR choice or truncation accounting] → Freeze current shallow-graph outputs before refactoring and compare canonical results across deep, cyclic, alternative, and budget-boundary fixtures.
- [Two identity types share the same textual prefix and are still confused at JSON boundaries] → Use field-specific parsers and typed constructors internally, reject cross-domain parameters, and include negative fixtures where equal-looking digest strings occupy the wrong field.
- [The link field rename breaks downstream snapshots] → Version the link policy/result, document the break, regenerate disposable indexes and owned fixtures, and fail old shapes explicitly rather than guessing their meaning.
- [Absolute executables still disagree with the repository pin] → Verify the pin and executable versions before creating the probe; record the selected identities and fail closed on mismatch.
- [Environment sanitization omits a legitimate toolchain variable] → Maintain a small documented allowlist, test representative pinned projects, and report the effective environment keys without exposing secret values.
- [A successful application check is overread as theorem replay] → Use operation-specific authority labels and retain the existing theorem-truth limitation in text and JSON.
- [Adding dimensions causes projections to invent defaults] → Require exhaustive projection mappings and adversarial tests for stored, partial, invalid, truncated, residual, and not-run inputs.

## Migration Plan

1. Add regression fixtures for derivation chains deeper than Python's default recursion limit, plus existing-output golden tests for shallow alternatives, cycles, and truncation.
2. Replace recursive solvers and slicers and run focused derivation, installed-CLI, and full Python gates.
3. Introduce identity-domain types and link policy v2; change derived link JSON, bump affected disposable projection/result versions, rebuild test indexes, and regenerate owned snapshots.
4. Introduce explicit toolchain resolution and execution, wire it through the semantic candidate CLI, and add ambient-shadowing, pin-mismatch, and sanitized-environment tests.
5. Add authority/completeness axes and non-escalating projection validation to live results and dossier summaries; regenerate result fixtures.
6. Run strict OpenSpec validation, dependency scans proving Quux absence, focused ProofIR suites, the full Python suite, quality checks, and `git diff --check`.

Rollback reverts the affected workstream and rebuilds the disposable index from canonical artifacts. No canonical v3 artifact rewrite or durable database migration is required.

## Open Questions

- Whether distinct textual digest prefixes should be introduced in a future ProofIR major/minor wire version remains a later compatibility decision; this packet resolves the current bug through typed domains and accurate fields.
- The minimum environment allowlist for all supported Lean installations must be frozen from repository-owned integration fixtures before the explicit-toolchain workstream closes.
