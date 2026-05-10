# Ladon Root Scope Classification

## Why

`root_scope_pressure` currently says a chosen root reaches a narrow slice of a
broad inventory. That is useful, but too blunt. The pre-registered runs showed
two different cases:

- `Mf.lean` is intentionally narrow and should not be treated like a mistaken
  whole-tree root.
- theorem owners such as `Mf.DP.BIFRPackedProfileFiniteSumBounds` are narrow
  owners inside a broad repo, often with large direct import closures.

## What

- Add root-scope classification metadata.
- Include the classification in the finding payload and message.
- Keep the original component signals.

## Non-Goals

- No automatic dead-code claim.
- No root-choice correction.
- No repo-specific hardcoded module names.
