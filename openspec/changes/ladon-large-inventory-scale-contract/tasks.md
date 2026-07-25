## 1. Portable Scale Fixture

- [x] 1.1 Add the versioned target-neutral large-project manifest and deterministic generator.
- [x] 1.2 Add small generator tests plus the required 2,600-module/1.5M-line/100k-declaration gate.
- [ ] 1.3 Record the Ubuntu reference-job identity and per-sample resource measurements.

## 2. Source Index And Cache

- [x] 2.1 Implement one-pass lexical extraction into a versioned source index.
- [x] 2.2 Add strong source/layout/policy fingerprints, platform cache defaults, and explicit cache outcomes.
- [x] 2.3 Add atomic writes, interrupted-write recovery, and selective invalidation tests.

## 3. Canonical Reports

- [x] 3.1 Add report v3 with single canonical payload ownership and scalar payload references.
- [x] 3.2 Add `summary`, `review`, and `full` projections with omission metadata and analysis fingerprints.
- [x] 3.3 Add bounded file serialization and report-byte enforcement without a second full encoded copy.
- [x] 3.4 Retain v2 reading and add the bounded explicit-v2 writer/deprecation path.

## 4. Acceptance

- [x] 4.1 Run report-reader, schema, installed-CLI, cache, determinism, and payload-ownership tests.
- [ ] 4.2 Run the portable cold/warm wall, RSS, JSON, and text ceilings.
