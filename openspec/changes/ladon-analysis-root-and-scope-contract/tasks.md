## 1. Scope Model

- [x] 1.1 Add typed scope plans, normalized roots, population roles, diagnostics, and fingerprints.
- [x] 1.2 Implement deterministic owner and local import-closure selection.
- [x] 1.3 Implement namespace, named multi-root, and full-inventory selection.
- [x] 1.4 Implement caller-supplied changed paths and versioned changed-set manifests.

## 2. Public Preview And Analysis

- [x] 2.1 Add text/JSON `preview` with layout, population, cache, truncation, and helper-batch estimates.
- [x] 2.2 Guarantee preview starts no build, Lean helper, target initializer, or VCS process.
- [x] 2.3 Thread effective scope and primary/context population metadata into reports and cache keys.
- [x] 2.4 Prevent inventory-wide findings from being mislabeled as owner findings.

## 3. Acceptance

- [x] 3.1 Test multi-root order independence, overlap attribution, closure boundaries, and namespace segments.
- [x] 3.2 Test changed manifests, unmapped paths, layout ambiguity, and scope invalidation.
- [x] 3.3 Test preview output/channel parity and zero target-process launches.
