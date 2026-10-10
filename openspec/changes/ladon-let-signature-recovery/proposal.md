# Proposal

## Why

Update feedback R01 shows theorem signatures cut off at assignments inside `let` expressions, hiding conclusion symbols from type-text search while reporting no truncation. The consumer runbook also still recommends rebuilding ordinary stale sources.

## What Changes

- Preserve supported lexical theorem signatures through consecutive/nested let expressions and binder defaults, stopping at the declaration's proof/body boundary.
- Keep ambiguous extraction visibly incomplete rather than presenting an unsupported fragment as complete; preserve byte limits and lexical authority.
- Version extraction identity and explicitly refresh cached old signatures through the evidence-preserving update path, without invoking Lean or renewing old checks.
- Align the matrix-factorization Ladon runbook with status, source updates, incompatible-input rebuilds and separate compiled acquisition.
- Deliver as a tested 0.2.3 maintenance release. Acceptance is defined in `specs/ladon-lexical-signature-extraction/spec.md`.

## Capabilities

### New Capabilities

- `ladon-lexical-signature-extraction`: bounded lexical declaration signatures, type-text search and extraction-version recovery.

### Modified Capabilities

None in synchronized main specs. Existing index-history authority and publication requirements remain unchanged.

## Impact

Lexical signature extraction, helper/freshness metadata and compatible index update; name/type-text consumers and installed contracts; both skills and the external consumer runbook. No new runtime dependency, backend, watcher, shared Lean build or mathematical source edit. Diagnostic source: `temp/ladon-update-feedback-r01/FEEDBACK.md` (archive in the matrix-factorization temp directory).
