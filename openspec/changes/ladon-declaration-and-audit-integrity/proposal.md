## Why

Large Lean repositories expose declaration and audit structures that Ladon's
current text path either loses or misclassifies: namespace context is discarded,
same-name declarations cannot be triaged safely, multiline audit subjects remain
unparsed, and command-only audit modules are promoted as generic barrels. The
alpha product needs conservative, authority-labeled navigation over these
surfaces before it can claim dependable repository review.

## What Changes

- Extend canonical lexical declaration rows with safely recognized namespace,
  modifier, privacy/locality, source-range, and normalized source-hash context.
- Produce bounded cross-file collision and duplicate-source candidates while
  keeping lexical candidates separate from Lean-confirmed identities and errors.
- Require selected-context graph witnesses before registering co-reachable
  collision review input.
- Parse supported multiline `#check` and `#print axioms` subjects without
  confusing comments or strings for commands.
- Attach audit evidence before final facade classification so declaration-empty
  audit surfaces are not mislabeled as generic pure barrels.
- Attach unique lexical audit-subject owner candidates conservatively while
  preserving containing owner, candidate owner, Lean result, backend, and
  authority as separate evidence.
- Add deterministic coverage metadata, portable positive and negative fixtures,
  text-backend no-build gates, and optional fingerprinted live observations.

## Capabilities

### New Capabilities

- `ladon-declaration-and-audit-integrity`: Namespace-aware lexical declaration
  candidates, conservative collision evidence, multiline audit parsing, audit
  facade role precedence, and authority-preserving subject ownership.

### Modified Capabilities

None.

## Impact

- Affected code: lexical extraction and source-index models, declaration and
  duplicate analysis, audit parsing and enrichment, module/facade role
  classification, review-registration rows, rendering, report schemas, and
  cache fingerprints.
- Existing owners remain authoritative:
  `ladon-declaration-source-evidence`,
  `ladon-elaborated-declaration-surface`,
  `ladon-lean-audit-command-surface`,
  `ladon-common-layer-and-facade-quality`, and
  `ladon-scope-and-join-integrity`.
- Text evidence remains non-elaborating and cannot establish Lean declaration
  identity, compilation failure, theorem truth, proof correctness, or a captured
  axiom result.
- Required tests use tracked portable fixtures and start no Lake build, Lean
  helper, version-control command, or target initializer. Mutable external
  repositories remain optional, read-only observational evidence.
