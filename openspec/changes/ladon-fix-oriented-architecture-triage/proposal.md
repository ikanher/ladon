## Why

Policy findings are actionable only if reviewers can see the highest-priority
pairs, files, and likely next actions before reading long raw edge lists.

## What Changes

- Rank direct policy findings by pair and offending file.
- Attach source evidence, triage context, and suggested review actions.
- Keep suggestions non-authoritative and source-backed.

## Capabilities

### New Capabilities

- `ladon-fix-oriented-architecture-triage`: Summary-first policy output and
  review-action metadata for direct boundary findings.

### Modified Capabilities

None.

## Impact

- Affected code: architecture policy summaries, render output, finding fields.
- Affected workflow: reviewers inspect pair summary and top files first.
