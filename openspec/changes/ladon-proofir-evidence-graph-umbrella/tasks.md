## 1. Governance And Evidence Boundaries

- [ ] 1.1 Parse `children/dependency-ledger.json` and verify all five children, start-after edges, existing owners, exit classes, shared project-local database, and ordinary-CLI invariant.
- [ ] 1.2 Compare each standalone child capability spec byte-for-byte with its umbrella copy before starting and after completing that child.
- [ ] 1.3 Preserve catalog-versus-semantic coverage: unsupported artifacts remain visible but create no claims, surfaces, graph rows, attachments, or authority.
- [ ] 1.4 Preserve separate facts for extractor boundaries, replay runs, checker witnesses, ProofIR obligation status, declaration attachment, and Lean lineage.
- [ ] 1.5 Preserve the nonclaim that ProofIR routes and contextual artifacts are not Lean proof-term dependencies or theorem truth.

## 2. Phase A: Artifact Catalog And Generation

- [ ] 2.1 Apply `ladon-proofir-db-schema-and-artifact-catalog` first in the existing `<repo>/.ladon/index/proof-search.sqlite` lifecycle.
- [ ] 2.2 Pass its TDD schema, configured-input, deterministic identity, unsupported/malformed coverage, limits, constraint, foreign-key, required-index, atomicity, and two-build exits.
- [ ] 2.3 Prove no configured inputs reports unavailable/not-configured and no second database or raw JSON store exists.

## 3. Phase B: Surface And Replay Evidence

- [ ] 3.1 Apply `ladon-proofir-surface-and-replay-ingestion` only after the catalog portable exit class passes.
- [ ] 3.2 Pass bundle/claim, replay relation, stale/foreign surface, failed/missing provenance, aggregate deduplication, and 63/52/11 coverage exits.
- [ ] 3.3 Prove `not_replayed_by_extractor` and successful repository-local replay remain separate quoted facts.

## 4. Phase C: Obligation DAG Storage And SQL Queries

- [ ] 4.1 Apply `ladon-proofir-obligation-dag-ingestion-and-queries` after catalog and surface/replay contracts are stable.
- [ ] 4.2 Pass chain, diamond, cycle, malformed endpoint, conflicting node, checker witness, mixed-authority CDC, bounds, deterministic route, and query-plan exits.
- [ ] 4.3 Require recursive SQL for routine traversal and prove ProofIR nodes/edges never enter theorem-lineage tables.

## 5. Phase D: Declaration And Lineage Attachments

- [ ] 5.1 Apply `ladon-proofir-declaration-lineage-attachments` after both stored ProofIR evidence models pass.
- [ ] 5.2 Pass exact source hash/path/name, compatible range, hash-subject mismatch, duplicate-name ambiguity, staleness, rebuild recomputation, and lineage freshness exits.
- [ ] 5.3 Pass the exact CDC negative oracle: nearby witnesses and DAGs remain unattached context for `nonempty_indexedCycleDoubleCover` until an explicit source-backed theorem surface exists.
- [ ] 5.4 Audit that no first-match, basename, module, prose, guarantee, filename, or proximity inference selects a theorem attachment.

## 6. Phase E: Installed CLI And Calibration

- [ ] 6.1 Apply `ladon-proofir-cli-integration-and-calibration` after storage/query contracts are stable.
- [ ] 6.2 Add caller-neutral installed commands and pass help, parser, text/JSON parity, warm read-only, stale/missing policy, stream, signal, timeout, output-cap, and two-build exits.
- [ ] 6.3 Run the portable end-to-end fixture through build, status, theorem evidence, artifact evidence, forward/reverse DAG routes, and canonical database preservation failures.
- [ ] 6.4 Run opt-in fingerprinted Quux and Matrix-Factorization calibration; evaluate cross-evidence answer quality and authority clarity rather than latency alone.
- [ ] 6.5 Update README, CLI/architecture/ProofIR docs, and the authoritative `../codex-skills/ladon` skill using only actual installed commands.

## 7. Full Umbrella Acceptance

- [ ] 7.1 Run all five child validation commands and every child portable exit class in dependency order.
- [ ] 7.2 Run focused and full Python tests, strict quality, compile, installed-wheel, deterministic, signal/resource, integrity/FK/index/query-plan, no-tracked-DB, and `git diff --check` gates.
- [ ] 7.3 Strictly validate the umbrella and all children, validate the global OpenSpec inventory, parse all governance JSON, and compare duplicated specs byte-for-byte.
- [ ] 7.4 Audit for a second database, raw-dialect semantic mirror, unconfigured recursive artifact scan, hidden external execution, unbounded route expansion, arbitrary attachment, status collapse, and authority promotion.
- [ ] 7.5 Record the final go/no-go result and retain the feature only if one stored query materially improves surface/replay/declaration/lineage evidence and one DAG query preserves conditional authority transitions.
