# Production closed-proof printer repair

The corrected C05 shifted-state term now completes through Ladon source-goal capture, closed printing, independent compiler replay and the unchanged axiom policy. This resolves the exact failure diagnosed in `../c05-roundtrip-diagnosis-r01/REPORT.md`. The original N.3c failure remains preserved as the pre-fix result.

The helper sets an explicit finite 200000-step printer budget for closed target and proof serialization. The shared proof printer applies that budget to other proof-slice consumers too. The completion helper parses both outputs and rejects omission syntax before Lean can interpret a printed `⋯` as a hole. Existing metavariable, definitional-equality, closed-context, replay and axiom checks stay in force. A larger proof can still hit this budget and receive an explicit rejection; the observed C05 success does not establish a universal bound.

## Acceptance evidence

`N3C05-complete.json` reports `completed`, replay `accepted`, trust `accepted`, and exactly `Classical.choice`, `Quot.sound`, `propext`. The same corrected term digest and original source goal were used. Completion took 49.38 seconds and sampled peak process-tree RSS was 5644619776 bytes (about 5.26 GiB). Capture and completion used this Ladon checkout, pinned Lean 4.33.0, the retained local project/cache, 12 GiB RSS, 16 MiB output and 600-second operation limits. Requests, streams and process receipts are retained under this directory.

The generic regression `tests/test_source_goal_completion_printer_budget.py` failed before the fix with `closed proof round-trip changed its expression` under a deliberately small inherited printer limit. It now completes and verifies replay/trust. The affected focused suite (ordinary completion, placeholder rejection, long telescope, instance round-trip, unsupported contexts and proof-slice limits) passed 14/14. Scoped Ruff, compileall, `git diff --check`, and strict umbrella validation passed.

Two exposed negative source-goal controls were rerun after the fix: `N3C06-complete.json` rejects incompatible shared parameter proofs, and `N3C07Route-complete.json` rejects the wrong conclusion quantifier. Both stop before replay and have no trust acceptance. Placeholder and forbidden-axiom behavior remains covered by the existing completion tests. The original C02 omitted-premise residual was not rerun in this production-fix session.

## Reader consequence

A checked alternative route for the lower-bounded state claim can now be recorded with native completion authority. This says nothing about automatic source interpretation or improved discrepancy discovery. The earlier seven-case qualification and original comparison retain their stated exposure and negative comparative result. Ordinary Lean remains useful for claims outside the supported printing/resource boundary.
