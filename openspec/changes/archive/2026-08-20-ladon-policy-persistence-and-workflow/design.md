## Context

Architecture and source-pattern policies already have explicit CLI flags and
repo-local discovery. This packet hardens that path as the default workflow.

## Goals / Non-Goals

**Goals:**

- Make discovered policies visible in JSON and text reports.
- Add generic policy examples.
- Verify no-policy status remains explicit.

**Non-Goals:**

- No target-repo-specific policy contents in Ladon.
- No automatic policy enforcement beyond project-supplied policy files.

## Decisions

- Keep policy discovery paths small and explicit.
- Treat examples as docs/fixtures, not bundled default policy behavior.
- Keep missing architecture policy visible because peer boundaries cannot be
  inferred soundly.

## Risks / Trade-offs

- Example files can become stale -> Cover them with JSON validation tests.
- Users may expect default policy enforcement -> Keep skipped-policy finding
  explicit and documented.
