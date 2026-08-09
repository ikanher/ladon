# ProofIR v3 identity scopes

ProofIR uses distinct identifiers with explicit scope:

- `contentArtifactId` is the detached hash of canonical artifact content and
  remains stable across paths and index generations.
- `observationId` identifies one repository/path/generation observation of that
  content and may change when the surrounding generation changes.
- `environmentRef` scopes prover and checker semantics to an exact toolchain,
  dependency/module manifest, options, trust configuration, and fingerprint
  scheme.
- each artifact owns its subject descriptors; their exact keys are
  (`ownerContentArtifactId`, `kind`, `localId`), so coincident local spellings
  in different artifacts never join.
- local payload references contain only `kind` and `localId` and resolve inside
  their enclosing artifact. This avoids putting an artifact's own digest inside
  the bytes from which that digest is computed.
- cross-artifact references additionally name the exact `artifactRef` and must
  close against that captured artifact before projection. A name, display text,
  or matching local ID is never an external reference.
- supported fingerprint equality is a separate candidate relation requiring an
  equal environment, scheme/version, and digest. It does not merge exact subject
  rows. Unknown schemes remain opaque and non-comparable.
- display names, search shapes, and opaque Lean payload references are
  diagnostic/indexing fields, not exact semantic identity.
