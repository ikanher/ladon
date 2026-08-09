## 1. Specify identity vectors first

- [x] 1.1 Add failing vectors that prove unchanged canonical bytes keep one `contentArtifactId` across paths and generations while observations remain distinct.
- [x] 1.2 Add failing vectors for environment-scoped Lean declarations with equal names but different toolchains, modules, or expression fingerprints.
- [x] 1.3 Add failing vectors that reject cross-artifact bare local IDs and implicit claim-ID/node-ID equality joins.

## 2. Implement owned identity types

- [x] 2.1 Add typed models for content artifacts, generation observations, environments, statements, declarations, terms, contexts, and artifact-scoped local references.
- [x] 2.2 Implement detached canonical hashing that excludes the ID field itself and rejects mismatched supplied IDs.
- [x] 2.3 Define the Lean environment profile with toolchain, dependency/module fingerprints, relevant options, trust configuration, and fingerprint algorithm version.
- [x] 2.4 Keep Lean expression payloads opaque in Python; store display and search-shape fields separately from exact identity.
- [x] 2.5 Replace internal semantic joins based on coincident strings with explicit typed references and delete every retired compatibility join.

## 3. Integrate and verify

- [x] 3.1 Add round-trip and collision-boundary tests for every reference type and deterministic error tests for missing scope.
- [x] 3.2 Add generation-diff tests showing stable content deduplication and distinct repository observations.
- [x] 3.3 Document which identifiers are stable, local, environment-scoped, or display-only.
- [x] 3.4 Run the identity tests plus all ProofIR catalog, store, query, and dossier tests and the strict Python quality gate.
