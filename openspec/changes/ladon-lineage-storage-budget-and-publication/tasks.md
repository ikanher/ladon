## 1. Specify Budget Metadata

- [x] 1.1 Add failing tests for distinct base-build and complete-database ceilings in build, status, refresh, and summary payloads.
- [x] 1.2 Add CLI/config parsing for an explicit complete-database MiB ceiling and define compatibility behavior for old metadata.
- [x] 1.3 Persist budget values, units, policy source, and schema identity; reject contradictory or nonpositive configurations.

## 2. Enforce Transactional Publication

- [x] 2.1 Add preflight row/byte estimates as advisory evidence without using them as the authoritative acceptance check.
- [x] 2.2 Pass the complete-database byte ceiling into `ingest_theorem_lineage` and measure pre/post logical and allocated bytes inside the transaction.
- [x] 2.3 Preserve the active closure under injected budget, integrity, foreign-key, statistics, and commit failures.
- [x] 2.4 Report marginal rows and bytes by affected lineage object using the shared storage-accounting API.

## 3. Refresh Statistics And Recheck Plans

- [x] 3.1 Add a red test proving first lineage publication currently leaves no lineage `sqlite_stat1` rows.
- [x] 3.2 Run targeted statistics refresh for changed lineage tables inside publication and record its elapsed time/identity.
- [x] 3.3 Execute normalized forward/reverse plan probes before commit and roll back if required access paths are absent.

## 4. Guarantee Progress And Terminal Output

- [x] 4.1 Define versioned phase progress and terminal result schemas covering timeout, resource termination, budget rejection, persistence, projection, rendering, and success.
- [x] 4.2 Emit progress on stderr without contaminating JSON stdout and emit exactly one terminal record on every handled path.
- [x] 4.3 Replace direct `Path.write_text` with the shared sibling-temporary, flush, fsync, atomic-replace output primitive.
- [ ] 4.4 Add failure-injection tests for interruption during planning, persistence, statistics, projection, and rendering.

## 5. Verify Lifecycle

- [x] 5.1 Run store, CLI, output, supervisor, signal, budget, schema, integrity, FK, query-plan, and deterministic suites.
- [x] 5.2 Measure refresh overhead and prove warm summary/query behavior remains within child gates.
- [x] 5.3 Validate this OpenSpec change strictly and document base versus complete policy without silently increasing existing generations.
