## 1. Manifest And Bundle Contracts

- [x] 1.1 Add versioned runset and bundle schemas with repository-generic validation.
- [x] 1.2 Add deterministic entry identities, relative report paths, hashes, scope, and phase summaries.
- [x] 1.3 Validate complete manifests and portable paths before execution.

## 2. Execution And Resume

- [x] 2.1 Execute ordinary one-root analyses serially by default with per-entry output isolation.
- [x] 2.2 Reuse only fingerprint-compatible source indexes and Lean caches.
- [x] 2.3 Atomically publish entry reports and durable state after terminal entries.
- [x] 2.4 Add zero-launch resume hits, selective invalidation, and corrupt-output rejection.
- [x] 2.5 Preserve completed reports across required/advisory failure and cancellation.

## 3. Acceptance

- [x] 3.1 Add portable multi-root success, failure, interruption, and resume fixtures.
- [x] 3.2 Test deterministic movable bundles, stream discipline, serial execution, and zero descendants.
