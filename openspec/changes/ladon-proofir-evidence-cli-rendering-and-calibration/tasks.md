## 1. Lock The Ordinary CLI Grammar

- [x] 1.1 Add installed parser/help tests for `evidence theorem`, `evidence artifact`, `evidence route`, and `evidence triage` before changing implementation.
- [x] 1.2 Replace the temporary `dag:start` form with explicit `--dag`, `--start`, `--end`, `--direction`, and bound options.
- [x] 1.3 Add format/output/index/repository/freshness/refusal tests and verify no LLM-specific command or terminology appears.
- [ ] 1.4 Add subprocess spies proving warm evidence commands never invoke Lean, Lake, replay, checker, or generator commands.

## 2. Implement Section-Aware Rendering

- [x] 2.1 Dispatch every selector to the versioned stored query service over a read-only SQLite URI.
- [x] 2.2 Add compact text renderers for dossier, artifact, route/tree, triage, coverage, diagnostics, truncation, and nonclaims.
- [ ] 2.3 Serialize canonical JSON from the identical result dictionaries and enforce output-byte limits before writing.
- [ ] 2.4 Keep stdout for results and stderr for operational diagnostics; add valid-JSON-on-error/output tests.

## 3. Implement Freshness And Refresh Policy

- [ ] 3.1 Reuse the existing project-local index path and verify schema/generation/configuration/source identity before a warm query.
- [ ] 3.2 Return explicit missing/stale coverage or refusal with the ordinary explicit build command; never refresh implicitly.
- [ ] 3.3 Add PID-lock/read-only concurrency tests and prove evidence queries do not create a second database.

## 4. Build Portable End-To-End Gates

- [x] 4.1 Extend the portable fixture with exact, claim-only, ambiguous, stale, conditional, cyclic, checker, and unsupported evidence.
- [ ] 4.2 Through installed-wheel entry points, run build, status, all evidence selectors, text/JSON parity, and a second unchanged build.
- [ ] 4.3 Assert exact attachments, separate replay/claim facts, endpoint routes, negative coverage, triage families, deterministic results, and database integrity.
- [ ] 4.4 Add malformed/oversized/stale/cap/signal variants and prove the prior canonical database remains readable.

## 5. Calibrate On Real Repositories

- [x] 5.1 Add an opt-in read-only harness recording commit/worktree, ProofIR config/artifact, index identity, command, timing, and semantic predicates.
- [ ] 5.2 On Quux, verify one theorem dossier reconstructs exact surfaces/replay while the CDC theorem remains context-only without an explicit surface.
- [ ] 5.3 On Quux CDC, verify external-premise and Lean-premise endpoint routes preserve every authority/status transition.
- [ ] 5.4 On Matrix Factorization, sample duplicate names and prove source evidence is required for attachment selection.
- [ ] 5.5 Compare warm database queries with locating/reading structured artifacts, but fail calibration on semantic predicates rather than latency alone.

## 6. Synchronize Documentation And Skill

- [x] 6.1 Update README and `docs/CLI.md` with configuration, explicit build, all evidence selectors, bounds, `jq`, and text examples.
- [x] 6.2 Update architecture/ProofIR docs with evidence sections, negative coverage, authority separation, and the CDC context-only example.
- [x] 6.3 Update the authoritative skill in `../codex-skills/ladon` only after installed examples pass that repository's checks.
- [ ] 6.4 Add docs/skill command checks and reject temporary or caller-specific syntax.

## 7. Verify The Packet And Umbrella Exit Class

- [ ] 7.1 Run all five child suites, existing ProofIR/lineage/index/installed-contract suites, and portable end-to-end fixtures.
- [ ] 7.2 Run full Python, compile, strict quality, integrity/FK/index/query-plan, deterministic, signal/resource, installed-wheel, and `git diff --check` gates.
- [ ] 7.3 Strictly validate umbrella/children, parse governance JSON, compare duplicated specs byte-for-byte, and verify dependency order.
- [ ] 7.4 Audit for second databases, raw mirrors, hidden execution, fuzzy attachment, route post-filtering, status collapse, and authority promotion.
- [ ] 7.5 Record go/no-go based on evidence completeness and authority clarity, not query speed alone.
