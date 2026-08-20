## 1. Progress And Limits

- [x] 1.1 Add versioned progress events and `auto|plain|json|off` stderr policies.
- [x] 1.2 Add phase checkpoints and bounded module/serialization updates.
- [x] 1.3 Add overall wall-time, RSS, and report-byte configuration and metadata.
- [x] 1.4 Reuse the existing supervisor for descendant cancellation and cleanup.

## 2. Partial Evidence

- [x] 2.1 Add stable failure classes, reasons, affected subjects, and completed/omitted counters.
- [x] 2.2 Render required incomplete phases in text and JSON and emit one controlling stderr diagnostic.
- [x] 2.3 Suppress or mark metrics whose input populations are incomplete.
- [x] 2.4 Migrate `--lean-strict` to the existing phase-partial failure selector.

## 3. Acceptance

- [x] 3.1 Test progress channel isolation and deterministic event bounds.
- [x] 3.2 Test discovery, helper, overall timeout, RSS, report-size, interruption, and cache-write failures.
- [x] 3.3 Verify schema-valid retained reports and zero surviving descendants.
