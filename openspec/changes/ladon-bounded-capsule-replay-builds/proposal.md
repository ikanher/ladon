# Proposal

## Why

A real theorem capsule's compiled-lineage extraction succeeds at32GiB, while its isolated fresh build exceeds both32GiB and48GiB. The replay currently launches one unrestricted `lake build <module>` and offers no supported build-concurrency policy; callers cannot complete verification merely by raising the process-tree RSS ceiling.

## What Changes

- Investigate and specify bounded capsule-build execution with an explicit, supported scheduling policy and diagnostic evidence. Inspect the actual build fan-out before choosing the implementation; concurrency is a plausible cause, not yet a measured attribution.
- Preserve the existing content, isolation, toolchain, theorem/dependency identity and trust comparisons. A cheaper build must verify the same capsule, not a smaller replacement statement.
- Make selected build policy, resource limits, failure stage and useful bounded process evidence visible in replay receipts.
- Add focused regression and integration gates before another expensive full-capsule attempt. Success means a caller can select an enforceable bounded-build strategy, or receives an actionable unsupported/failure outcome instead of repeated unexplained cap increases.
- Retain the actual32/48GiB failure receipts and exact reproduction commands in this change. The original reporting session was limited to **issue preparation only**. The user subsequently authorized investigation and implementation; the measured result is in [the implementation report](evidence/implementation/REPORT.md).

Detailed requirements are in [the resource-control delta](specs/ladon-capsule-replay-resource-control/spec.md); observed behavior and reproduction are in [REPRODUCTION.md](REPRODUCTION.md).

## Capabilities

### New Capabilities

- `ladon-capsule-replay-resource-control`: Explicit bounded-build policy, diagnostics and evidence-preserving resource handling for theorem capsule replay.

### Modified Capabilities

None in the current synced capability inventory. The archived theorem-capsule replay requirements remain applicable; this capability extends their resource-control boundary without replacing verification semantics.

## Impact

Likely owners are `src/ladon/theorem_cli.py`, `theorem_capsule_replay.py`, process supervision/accounting, the existing replay tests, and CLI documentation. Exact scheduling implementation remains for the Ladon owner to determine. No changes to Lean mathematics, target sources, capsule identity, default trust policy or privacy code are proposed. The original reporting packet changed only OpenSpec documentation and retained evidence. Subsequent authorized implementation adds the ordered scheduling path, bounded observations, CLI flags and regression tests described in the implementation report.
