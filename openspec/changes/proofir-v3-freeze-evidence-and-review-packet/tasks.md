## 1. Freeze packet completeness

- [ ] 1.1 Add red packet tests for absent `proof-state.md`, fixture, CLI/support source, child OpenSpec artifact, schema, file hash/size, source-state field, command log, exit code, and log digest.
- [ ] 1.2 Add mutations for a changed source file, stale dirty-tree digest, missing untracked entry, changed toolchain lock, truncated log, and evidence JSON that parses but fails its schema.
- [ ] 1.3 Define the exact packet-local commands and compute their transitive source/test/fixture closure before selecting files.

## 2. Build reproducible evidence

- [ ] 2.1 Add and maintain `proof-state.md` with alpha history, six review blocker classes, current task counts, Rust hold, exact commands, and nonclaims.
- [x] 2.2 Generate a manifest containing relative path, role, bytes, SHA-256, and source classification for every packet file.
- [x] 2.3 Record HEAD, dirty-tree and untracked manifests/digests, Python/Lean/SQLite/tool versions, and relevant lock/toolchain file hashes.
- [ ] 2.4 Capture each command's argv, cwd, bounded environment, timestamps, exit, and content-addressed stdout/stderr logs; validate release evidence with JSON Schema.
- [ ] 2.5 Include the complete packet-local CLI, support, fixture, schema, and child-change closure and fail the build if any advertised command imports or reads an omitted file.

## 3. Review and gate Rust

- [ ] 3.1 Replay every advertised packet-local command from the extracted archive in a clean temporary directory and compare log/content identities.
- [ ] 3.2 Ask the expert reviewer to disposition each original blocker and reproducibility limitation against exact packet evidence.
- [ ] 3.3 Mark the semantic contract frozen only if all blocker dispositions are closed or explicitly accepted as nonblocking and every hardening child exit class is green.
- [ ] 3.4 Keep `proofir-v3-rust-reference-core` blocked otherwise; publish no ready release evidence from stale alpha observations.

## 4. r03 reopening: use the strong manifest in the actual archive

- [x] 4.1 Make manifest validation require the current `proofir-review-packet-manifest-v2`, a non-empty closed file inventory, required source/toolchain state, and exact field types; reject old manifests rather than iterating zero rows.
- [ ] 4.2 Inventory README, manifest-owned metadata, source map, validation summary, sources, tests, fixtures, and logs under an explicit self-manifest/root-hash rule; reject every unadvertised regular file.
- [ ] 4.3 Add immutable command records containing argv, cwd, bounded environment/toolchain, timestamps, exit/resource outcome, and stdout/stderr paths, sizes, and hashes.
- [x] 4.4 Define deterministic manifest identity: exclude or separately observe generation time, hash untracked file contents as well as paths, and bind the archive/root digest without a self-hash cycle.
- [ ] 4.5 Compute the transitive import/read closure for every advertised command, include all missing Ladon modules and native corpus/support fixtures, and run clean extraction without a compatibility overlay.
- [ ] 4.6 Build r04 with the strong manifest, validate its JSON against schemas, replay under supported Python and Lean toolchains, and request a blocker-by-blocker expert disposition.
