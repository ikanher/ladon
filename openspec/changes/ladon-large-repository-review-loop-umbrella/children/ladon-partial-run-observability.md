# `ladon-partial-run-observability`

Owns stderr progress, an overall analysis deadline, cancellation checkpoints,
stable partial failure classes/reasons, phase diagnostics, population
completeness, and concise operational failure summaries.

- Existing owners reused: CLI exit/channel semantics, phase envelopes, process
  supervision, helper cancellation/reaping, and Lean cache fingerprints.
- Enables: trustworthy owner scopes, failure-isolated runsets, and installed
  workflow diagnostics.
- Excludes: a second supervisor/cache, implicit target builds, unbounded
  telemetry, or treating a partial report as successful analysis.
- Exit: timeout, cancellation, helper failure, incomplete dependency
  extraction, and rendering/output failures have deterministic JSON/text/stderr
  behavior; no helper descendants survive; incomplete metrics are suppressed
  or explicitly marked partial.
