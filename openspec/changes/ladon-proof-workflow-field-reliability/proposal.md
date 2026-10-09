# Proposal

## Why

The initialized-Adam field report records three proof-workflow failures: earlier source declarations disappear during completion replay, repeated binder names invalidate discovery evidence, and later local contexts exceed 64 MiB of capture output. These block users who already have a working Lean project.

## What Changes

- Preserve same-file declaration support when replaying a completed source goal, retaining independent compiler and transitive trust checks.
- Identify application substitutions by declaration-scoped binder positions and retain independently valid candidate observations when another candidate cannot produce valid evidence.
- Diagnose and reduce repeated structural expression output while preserving complete local definitions, exact identities, and fail-closed output bounds.
- Clarify discovery limits and closed/residual counts, and expose intermediate lexical build progress.
- Qualify the result through portable regressions and installed pinned-Lean field reproduction, then bump the package patch version to 0.2.1.

Success is the reported early goal completing with its same-file definition, transitivity returning precise residuals alongside a successful candidate, and the late goal capturing within the recorded 64 MiB bound. Tasks link the owning contracts. Retained lineage still requires an explicit full lexical rebuild; relaxing that association needs separate design.

## Capabilities

### New Capabilities

- `ladon-source-goal-context-preservation`: faithful bounded capture and independent replay of source-goal environments, including same-file declarations and local definitions.
- `ladon-application-substitution-identity`: declaration-scoped application bindings and independently attributable candidate evidence.

### Modified Capabilities

None. Existing exact environment, authority and population contracts remain applicable.

## Impact

Touches source capture/completion Lean helpers and protocols, application evidence producers, compact discovery reports and lexical build progress. No mathematical source edits or Lake reconciliation are needed. Internal helper/fingerprint versions may change; old captures remain historical and must be recaptured for current completion. The user feedback archive is an attributed input, not qualification.
