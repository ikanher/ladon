# Proposal

## Why

Native correspondence inspection exposes result dimensions and an interpretation reference while omitting the stored source interpretation and formal application slice. The pitfalls audits show that reviewers need these objects together to judge whether the checked application answers the source claim.

## What Changes

- Add bounded, owner-qualified source-interpretation and formal-slice context to existing native correspondence inspection.
- Report missing or oversized context explicitly, retaining existing dimensions as stored labels.
- Expose existing per-check receipt targets and compare their plan/obligation/polarity bindings with stored obligations; report consistency gaps explicitly.
- Expose a per-component byte allowance on the public inspection command; version the native inspection response because complete inspection now includes context availability.
- Admit complete slice and captured-receipt module inventories up to the existing 32768-module bound at their exact correspondence paths; retain generic collection, byte and evidence-authority limits.
- Qualify exact identity, omission, historical projection and public CLI behavior. This improves evidence access; comparative reader benefit remains unmeasured.

## Capabilities

### New Capabilities

- `proofir-correspondence-context`: Inspect the exact attributed source and formal context behind a stored correspondence.

### Modified Capabilities

None. Existing observation authority and coverage contracts continue to apply.

## Impact

Existing Python ProofIR query and correspondence CLI, focused tests and audit documentation. No dependency, canonical artifact or SQLite schema change; no Lean execution or source-fidelity authority is added. Parent: [pitfalls umbrella](../ladon-semantic-pitfalls-umbrella/tasks.md).
