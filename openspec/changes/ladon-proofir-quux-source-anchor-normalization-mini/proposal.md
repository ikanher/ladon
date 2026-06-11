## Why

Quux bridge indexes use both `sourceHash` and nested `sourceAnchor` fields, but
Ladon's bridge currently recognizes only `contentHash` and top-level
`sourcePath`/`sourceRange`. This loses available attachment evidence or risks
future ad hoc interpretation.

## What Changes

- Treat `sourceHash` as a `contentHash` alias for source-hash joins.
- Normalize nested `sourceAnchor` rows into conservative path/line evidence.
- Add a distinct line-anchor join or warning path that does not over-promote
  line hashes to full source-content hash evidence.
- Add frozen local fixtures covering the Quux variants.

## Capabilities

### New Capabilities

- `ladon-proofir-quux-source-anchor-normalization`: Normalizes Quux source hash
  aliases and nested source anchors for conservative ProofIR bridge joins.

### Modified Capabilities

None.

## Impact

- Affected code: bridge normalization and join confidence logic.
- Affected tests: source-hash alias, source-anchor downgrade, stale-source, and
  non-mutation tests.
