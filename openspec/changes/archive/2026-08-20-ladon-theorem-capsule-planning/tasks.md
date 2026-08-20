## 1. Plan Contract And CLI

- [x] 1.1 Add versioned theorem-plan models, canonical JSON serialization, schema validation, guarantee/nonclaim fields, and stable plan identity.
- [x] 1.2 Add backward-compatible `ladon theorem plan` parsing, text/JSON rendering, clean stream behavior, documented exits, and a reusable planning service for the composed extract flow.
- [x] 1.3 Add read-only preflight for repository root, pinned toolchain, Lake configuration/manifest, source roots, exact fully qualified name syntax, and output destination.

## 2. Lean-Authoritative Target And Dependency Evidence

- [x] 2.1 Extend the Lean helper with a versioned exact theorem lookup that confirms name, kind, owner module, source range, selection range, type identity, value availability, and trust facts.
- [x] 2.2 Add a deterministic unbounded dependency stream with typed type/value/generated records, declared counts/checksums, explicit completion, protocol compatibility, and fatal partial/truncation handling.
- [x] 2.3 Join Lean-confirmed target evidence to the parser command boundary and reject not-found, ambiguity, wrong-kind, multiple-owner, or source/environment disagreement cases.
- [x] 2.4 Cover helper failure, malformed output, unsupported toolchain/API behavior, descendant cleanup, and bounded stderr/stdout through the existing process supervisor.

## 3. Semantic And Build Closure Planning

- [x] 3.1 Build a recursive semantic dependency DAG that preserves type/value/generated/trust edges, exact external frontiers, deterministic SCCs, and coverage.
- [x] 3.2 Build a separate module/package DAG from the canonical import graph with repository ownership, source-root mapping, whole-module inclusion reasons, locked external packages, and declared resources.
- [x] 3.3 Detect and classify custom Lake behavior, native plugins/libraries, symlinks, dynamic resources, unsafe external paths, and unknown facets without executing target-controlled discovery initializers.
- [x] 3.4 Bind the plan to source bytes, target prefix end, source-inventory/module-layout/module-DAG identities, toolchain contents, Lake configuration, manifest/lock, and before/after snapshot evidence.

## 4. Determinism, Integration, And Documentation

- [x] 4.1 Canonically sort graph nodes/edges, paths, hashes, frontiers, unsupported facets, and diagnostics so unchanged inputs yield byte-identical plans.
- [x] 4.2 Keep bounded declaration-report projections unchanged and document why they are not a capsule completeness authority.
- [x] 4.3 Document the module-prefix, locked/rebuildable guarantee and the nonclaims for minimality, offline vendoring, hermeticity, and Ladon proof authority.

## 5. Portable Acceptance

- [x] 5.1 Add portable fixtures for exact namespaces, preceding local context, generated auxiliaries, semantic cycles, external packages, multiple source roots, and closures larger than the report cap.
- [x] 5.2 Add negative fixtures for short/ambiguous names, wrong declaration kinds, source/Lean disagreement, partial streams, stale snapshots, unsupported custom/native facets, and missing lock/toolchain inputs.
- [x] 5.3 Pass focused planning tests, installed-wheel CLI/help and channel tests, helper process-tree limits, deterministic plan checks, strict OpenSpec validation, and Python quality gates.
