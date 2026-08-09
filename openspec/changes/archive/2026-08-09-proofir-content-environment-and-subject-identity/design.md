## Context

Current IDs mix content, path, generation, declaration names, and local producer IDs. Stable diffs and explicit references require separate scopes.

## Goals / Non-Goals

**Goals:** define deterministic IDs, environment manifests, typed subjects, and artifact-scoped local references.

**Non-Goals:** parsing Lean expressions outside Lean or defining prover-independent term equality.

## Decisions

1. `contentArtifactId` hashes canonical content with the detached ID field excluded.
2. `observationId` hashes generation/path/content identity; it never replaces content identity.
3. `environmentRef` points to a Merkle-rooted manifest of prover/toolchain, dependencies, compiled modules, options, trust configuration, and fingerprint algorithms.
4. Each envelope owns a closed set of typed subject descriptors. A local payload
   reference serializes only `{kind, localId}` and resolves within that owner;
   the owner's content ID is deliberately absent from its own hashed bytes.
5. A genuine cross-artifact dependency uses the distinct closed shape
   `{artifactRef, kind, localId}`. Batch validation resolves it against that exact
   captured artifact and descriptor. Self external references are rejected.
6. The qualified identity of a subject is `(ownerContentArtifactId, kind,
   localId)`. SQLite keys and semantic foreign keys retain all three fields;
   equal local spellings or environments never create an implicit join.
7. Cross-artifact semantic comparison is separate from reference identity. It
   requires the same environment plus a supported versioned fingerprint scheme
   and digest. Unknown schemes remain opaque evidence and establish no equality.
8. Lean workers own declaration and expression fingerprints; core readers
   validate their bounded structure without parsing Lean terms. Display names,
   search shapes, and opaque payload references remain non-identity metadata.

## Risks / Trade-offs

- [Environment manifests are expensive] → content-address and reuse submanifests.
- [Fingerprint schemes evolve] → scheme and version are mandatory; unsupported
  schemes remain retained but non-comparable.
- [Cross-artifact closure needs more than one file] → validate the complete
  captured batch before mutating the disposable SQLite projection.

## Migration Plan

Freeze native identity vectors, replace ambiguous bare-string joins directly, and require disposable database rebuilds. No dual mapping or retired identity compatibility is retained.

Declarations without a supported value/type fingerprint remain usable as exact
artifact-owned references, but cannot participate in semantic-equality joins.
