## 1. Plan Compatibility And Capsule Model

- [x] 1.1 Depend on the completed planning contract and add strict plan schema/protocol/toolchain/guarantee compatibility validation.
- [x] 1.2 Add canonical capsule manifest, file-role, inclusion-reason, source-root, external-frontier, nonclaim, and materialized/unverified status models.
- [x] 1.3 Add backward-compatible `ladon theorem materialize` parsing, text/JSON outcomes, safe destination preflight, and the reusable service used by combined extraction.

## 2. Source And Build Layout

- [x] 2.1 Revalidate all plan-bound source/configuration hashes immediately before copying and reject stale or mixed snapshots.
- [x] 2.2 Copy the target module from byte zero through the exact planned theorem command end while preserving bytes, encoding, line endings, and preceding context.
- [x] 2.3 Copy every other repository-owned build-closure module as a whole file while preserving module paths across one or more source roots.
- [x] 2.4 Package pinned `lean-toolchain`, supported Lake configuration, lock/manifest evidence, and generated relocation/control files with explicit copied-versus-generated provenance.

## 3. Safe Transactional And Deterministic Output

- [x] 3.1 Normalize paths and reject absolute/escaping paths, NULs, unsafe links, unsupported special files, logical/filesystem collisions, output-inside-target, and unexpected destination content.
- [x] 3.2 Build in a sibling staging directory, inventory and hash the complete tree, clean failed staging safely, and publish atomically where supported.
- [x] 3.3 Account for every staged file in `capsule.json` and fail on an unaccounted, missing, changed, or multiply-owned entry.
- [x] 3.4 Add reproducible archive output with canonical entry order, timestamps, owners, paths, modes, and JSON serialization.
- [x] 3.5 Ensure host paths, staging names, wall-clock fields, and platform noise do not affect canonical directory or archive identity.

## 4. Guarantee Boundaries And Documentation

- [x] 4.1 Enforce the locked/rebuildable module-prefix boundary and refuse unsupported dynamic/native facets instead of publishing a best-effort capsule.
- [x] 4.2 Keep materialized output explicitly unverified until replay succeeds and document minimality, vendoring, hermeticity, and proof-authority nonclaims.
- [x] 4.3 Document capsule layout, inclusion reasons, output collision policy, archive guarantees, and safe cleanup/retry behavior.

## 5. Portable Acceptance

- [x] 5.1 Add fixtures for exact owner prefixes, later-command exclusion, imports, multiple source roots, locked packages, generated controls, large files, and repeated deterministic output.
- [x] 5.2 Add negative fixtures for stale plans, traversal, absolute paths, symlink escape, case/Unicode collision, special files, output-inside-target, unaccounted files, interrupted copy, and non-empty destinations.
- [x] 5.3 Pass focused materialization tests, installed-wheel CLI/help and channel tests, archive reproducibility checks, target-no-write assertions, strict OpenSpec validation, and Python quality gates.
