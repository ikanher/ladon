## 1. Capture resolver disagreements

- [x] 1.1 Add failing parity tests that feed identical candidates to native source-map and SQLite paths and expose policy differences.
- [x] 1.2 Add fixtures for exact declaration fingerprints, emitted declaration references, source range/hash matches, duplicate file contents, ambiguous names, stale sources, and escaping paths.
- [x] 1.3 Add a regression test proving a source-hash match at a different path is not labelled `exact_path_name_source_hash`.

## 2. Build one versioned resolver

- [x] 2.1 Implement one Ladon-owned attachment resolver and policy version consumed by native source-map ingestion and SQLite projection.
- [x] 2.2 Order candidates by environment/declaration fingerprint, producer declaration identity, source content/range, source content/name, bounded fallbacks, then name-only diagnostic.
- [x] 2.3 Retain all considered candidates, decisive evidence, confidence, freshness, policy version, and resolver identity in each observation.
- [x] 2.4 Treat name-only matches as diagnostics rather than semantic attachments.
- [x] 2.5 Replace manifest-only semantic relationships with artifact references or separately attributable link observations; diagnose drift and missing endpoints.

## 3. Prove portability

- [x] 3.1 Run the attachment suite with `../quux` unavailable and assert there is no Quux import, build, runtime, or test dependency.
- [x] 3.2 Add source-map/SQLite parity snapshots and bounded ambiguity diagnostics.
- [x] 3.3 Run native source-map, SQLite access-path, attachment-policy tests, and the strict quality gate.
