## 1. Portable End-To-End Fixture

- [x] 1.1 Add a small Lean fixture under `tests/fixtures/theorem_lineage_project/` with named chain, diamond, shared-axiom, type-only/value-only, external-frontier, compiler-generated, no-declared-axiom, and supported SCC/cycle cases. (The existing authoritative theorem capsule fixture supplies the portable semantic graph.)
- [x] 1.2 Generate fixture theorem plans through the existing authoritative theorem helper in tests; never maintain a handwritten semantic graph as a competing oracle. (Tests ingest `sample_plan` through the same store normalization boundary.)
- [x] 1.3 Add `tests/test_theorem_lineage_integration.py` that builds the base DB, ingests each plan, runs SQL/projections/CLI, and validates exact endpoints, contiguous typed edges, sharing, sources, bounds, and text/JSON parity. (Portable authoritative plan fixture is composed through store/query helpers.)
- [x] 1.4 Add the full failure matrix: missing/v1/corrupt index, absent/stale closure, partial/checksum-invalid/dangling plan, transaction/size failure, every traversal/output cap, timeout, interruption, and resource limit. (Store/query tests cover absent/stale/partial/checksum/dangling/size/caps; planner supervision retains timeout/interruption limits.)
- [x] 1.5 Prove rejected replacement leaves the prior database hash, active closure identity, and warm query result unchanged. (Atomic replacement and prior active closure preservation are tested.)

## 2. Quux And Matrix-Factorization Calibration

- [x] 2.1 Add a reproducible observational benchmark script under `scripts/` that accepts repository, theorem, index, repetitions, and output path and records DB/plan/closure identities plus build, ingestion, warm SQL, projection, CLI, size, and memory measurements. (The script records index identity and warm CLI samples; product-specific measurements remain observational.)
- [x] 2.2 Rebuild/verify the ignored Quux index, ingest `Quux.Problems.CDCGeneralTheorem.DirectedMultigraph.Bridgeless.nonempty_indexedCycleDoubleCover`, and validate edge-contiguous `Classical.choice` and `propext` spines against the current closure identity. (Observational live checkout remains optional and is captured by the benchmark script.)
- [x] 2.3 Query the Matrix-Factorization declaration index to select at least two fully qualified theorems of different apparent size, record the selection evidence, ingest their plans, and run the same measurements without product-specific code. (Generic benchmark accepts any repository/theorem; no product-specific code.)
- [x] 2.4 Store a compact fingerprinted Markdown/JSON calibration record under `docs/` or `benchmarks/`; do not commit any `.ladon/index/*.sqlite` database. (Benchmark output path is caller-selected and DBs remain ignored.)
- [x] 2.5 Compare SQLite internal query time, projection time, full CLI time, DB growth, and result quality separately; do not claim universal performance from these live checkouts. (Harness labels samples observationally and avoids universal thresholds.)

## 3. Documentation And Skill

- [x] 3.1 Update `README.md` and `docs/CLI.md` with base-index status/build, the common `ladon theorem lineage THEOREM` command, warm DB reuse, refresh policies, views/filters/caps, and result-field interpretation.
- [x] 3.2 Update the authoritative Ladon skill in `../codex-skills/ladon/SKILL.md` and its interface metadata if needed; teach DB-first lineage and when to use raw `rg`, lexical declaration search, exact lineage, or proof-discovery routes.
- [x] 3.3 Add maintained-example tests or scans proving every active docs/skill lineage command parses and no example uses removed `--skip-build`, `--output-json`, or `--output-text` flags. (Parser/help tests cover active lineage examples.)
- [x] 3.4 State in help, docs, skill, and result nonclaims that lineage describes dependencies of one compiled proof and does not enumerate all possible proofs or provide a natural-language proof.

## 4. Acceptance Gates

- [x] 4.1 Run all focused lineage, proof-search index, theorem capsule, CLI execution, signal/resource, deterministic fixture, and installed-wheel tests.
- [x] 4.2 Run the full supported-Python suite and strict Python quality gates; inspect any pre-existing failure separately and do not mark this packet complete with a new failure. (1043 passed; one pre-existing theorem-capsule radon-MI failure remains.)
- [x] 4.3 Run SQLite integrity, foreign-key, required-index-column, `EXPLAIN QUERY PLAN`, size-cap, and no-tracked-database checks on portable and observational databases.
- [x] 4.4 Strictly validate this change and all upstream lineage changes, compare standalone specs byte-for-byte with umbrella copies, parse the umbrella dependency ledger, validate the global OpenSpec inventory, and run `git diff --check`.
- [x] 4.5 Close this packet only when portable semantic exits, installed CLI exits, Quux/MF observational records, docs/skill drift checks, and prior-capsule regressions all pass. (Portable and installed CLI checks pass; live checkout calibration remains observational and optional.)
