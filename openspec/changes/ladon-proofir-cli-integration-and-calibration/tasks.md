## 1. Lock The Ordinary CLI Contract With Failing Tests

- [ ] 1.1 Verify all four storage/query packet exit classes pass and duplicated umbrella specs match standalone specs.
- [ ] 1.2 Inspect current `ladon index` and `ladon theorem` grammar, choose caller-neutral subcommand names, and record the exact syntax in CLI tests before implementation.
- [ ] 1.3 Add installed help/parser tests for catalog status, theorem evidence, artifact evidence, obligation direction, refresh, bounds, format, output, and timeout behavior.
- [ ] 1.4 Add failing text/JSON parity tests for surface-plus-replay evidence, mixed-authority DAG routes, ambiguous attachment, stale evidence, unsupported input, and unavailable coverage.
- [ ] 1.5 Add failing exit/stream/signal/output-byte tests proving warm queries are read-only and never invoke Lean, replay commands, checkers, or generators.

## 2. Add Versioned Query Results And Renderers

- [ ] 2.1 Define stable render-neutral result schemas for ProofIR catalog status, theorem evidence, artifact evidence, and obligation routes without exposing private table names.
- [ ] 2.2 Include repository/index generation, artifact identity, coverage, freshness, authority, relation method, diagnostics, omissions, truncation, source anchors, and nonclaims.
- [ ] 2.3 Implement compact text renderers and canonical JSON output from the same result dictionaries; keep stderr for progress/diagnostics only.
- [ ] 2.4 Enforce row/depth/edge/route/output-byte caps before rendering and avoid corrupt partial JSON on limit failure.

## 3. Wire Installed Commands And Refresh Policy

- [ ] 3.1 Add ordinary parser entries and orchestration that open the project-local database read-only for fresh warm queries.
- [ ] 3.2 Route catalog, theorem, artifact, and DAG selectors to stored query services with parameterized inputs and deterministic ordering.
- [ ] 3.3 Reuse current index path resolution, PID lock reporting, timeout/signal handling, format/output conventions, and documented exit classes.
- [ ] 3.4 Implement explicit missing/stale refresh or refusal behavior; never run Lean or external artifact commands implicitly during a warm evidence query.
- [ ] 3.5 Extend build/status JSON and text with configured ProofIR fingerprints and distinct catalog/normalized/unsupported/malformed/stale/surface/replay/DAG/attachment counts.

## 4. Build The Portable End-To-End TDD Fixture

- [ ] 4.1 Create a small Lean repository fixture with duplicate declaration names, one exact surface, one claim-only row, exact replay provenance, one conditional DAG, one checker witness, and one unsupported artifact.
- [ ] 4.2 Run build, status, theorem evidence, artifact evidence, forward/reverse DAG routes, and a second unchanged build through installed-wheel entry points.
- [ ] 4.3 Assert exact source links, separate extractor/replay facts, conditional boundary transitions, no arbitrary duplicate attachment, no aggregate double count, and equivalent second-build results.
- [ ] 4.4 Add malformed/stale/oversized/cyclic/ambiguous failure variants and prove canonical database integrity/preservation after each failure.

## 5. Add Fingerprinted Real-Repository Calibration

- [ ] 5.1 Add an opt-in read-only calibration harness that records repository commit/worktree state, config/artifact fingerprints, index identity, exact command, timing, and result predicates.
- [ ] 5.2 On Quux, measure the supported surface/replay population and verify one query reconstructs bundle, surface, replay run, source freshness, and attachment/lineage availability without status promotion.
- [ ] 5.3 On the Quux CDC DAG, verify representative external-conditional and Lean-premise routes preserve every status/authority transition.
- [ ] 5.4 Query the exact CDC theorem and verify current artifacts remain unattached context until an explicit theorem surface exists.
- [ ] 5.5 On Matrix-Factorization, sample duplicated candidate names and verify source evidence is required for selection; record warm DB versus structured JSON timing without using latency alone as success.

## 6. Synchronize Documentation And Skill

- [ ] 6.1 Update README and `docs/CLI.md` with configuration, build/status, theorem/artifact/route queries, `jq` examples, outputs, refresh policy, and project-local database location.
- [ ] 6.2 Update `docs/ARCHITECTURE.md` and ProofIR docs with catalog-versus-semantic support, artifact relations, authority separation, generation replacement, and negative CDC example.
- [ ] 6.3 Update the authoritative Ladon skill in `../codex-skills/ladon`, then verify/install according to that repository's workflow and ensure examples use actual installed commands.
- [ ] 6.4 Add docs/skill command checks to installed-wheel gates and verify no deprecated or caller-specific syntax remains.

## 7. Verify The Packet And Umbrella Exit Class

- [ ] 7.1 Run all ProofIR catalog/surface/replay/DAG/attachment/lineage/CLI/integration tests plus existing bridge, atlas, proof-search, theorem-lineage, and installed-contract suites.
- [ ] 7.2 Run full Python tests, strict quality, compile, installed-wheel, signal/resource, deterministic, integrity/FK/index/query-plan, no-tracked-DB, and `git diff --check` gates.
- [ ] 7.3 Strictly validate all six OpenSpec changes, parse governance JSON, compare duplicated specs byte-for-byte, and verify dependency order.
- [ ] 7.4 Audit for a second database, raw-dialect mirror, hidden external execution, unbounded traversal, first-match attachment, status collapse, and ProofIR-to-Lean authority promotion.
- [ ] 7.5 Record the go/no-go conclusion: retain the feature only if cross-evidence queries materially improve answer completeness and authority clarity over locating one JSON artifact.
