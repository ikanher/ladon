## Why

ProofIR v3 has sound evidence boundaries, but current implementation seams can still overrun Python recursion on valid bounded derivation queries, confuse whole-file digests with detached artifact identities, select Lean executables from ambient `PATH`, and compress live authority and analysis completeness in derived results. These gaps should be closed before the v3 semantic contract and cross-language behavior are frozen.

## What Changes

- Replace recursive derivation satisfaction and complete-slice traversal with Ladon-owned iterative algorithms that honor declared query bounds independently of Python's recursion limit.
- Separate raw file digests from canonical detached ProofIR artifact IDs in types, validators, link observations, and rendered output.
- **BREAKING**: replace the misleading `resolvedArtifactId` link-observation field when it contains a whole-file digest with an explicit `resolvedFileDigest`; expose a separately validated content artifact ID only when one is available.
- Add an explicit trusted-local Lean toolchain context that binds repository root, absolute executable identities, the repository toolchain pin, and a sanitized execution environment.
- Preserve ambient tool discovery only as explicitly labeled non-authoritative selection rather than silently treating it as pinned replay.
- Represent source/check authority independently from analysis completeness in live checks and derived dossiers, with non-escalating projections and an explicit not-assessed state.
- Add deep-chain, identity-domain, toolchain-substitution, and projection-adversarial fixtures owned entirely by Ladon; no Quux runtime, build, test, or calibration dependency is introduced.
- Defer object-store, provenance-lattice, signed-anchor, repository-closure, and Lean trust-core machinery because they are outside Ladon's trusted-local analysis boundary.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `proofir-derivation-hypergraph-semantics`: bounded derivation queries must use stack-safe traversal and remain governed by declared ProofIR budgets rather than interpreter recursion depth.
- `proofir-content-environment-and-subject-identity`: raw byte digests, detached artifact IDs, environment identities, and executable identities become distinct validated domains, and live Lean execution must bind an explicit toolchain context.
- `proofir-attachment-and-link-observations`: link observations must name raw file digests accurately and expose canonical artifact IDs only after native artifact validation.
- `proofir-observation-authority-and-coverage-core`: live authority and analysis completeness become explicit independent axes, and stored or partial evidence cannot escalate either axis.

## Impact

The change affects derivation solvers and slicers, ProofIR identity helpers and validators, proof-search artifact discovery, link-observation JSON, semantic candidate execution, theorem-dossier/result projections, CLI rendering, schemas or typed models for affected results, and portable conformance tests. Canonical native-v3 artifact identity remains detached and unchanged; SQLite remains a disposable projection; Quux remains outside Ladon's production and verification dependency boundary.
