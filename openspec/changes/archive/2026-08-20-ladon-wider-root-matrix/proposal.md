# Ladon Wider Root Matrix

## Why

The current calibration suite checks a small set of roots. We need a maintained
local run matrix that covers more Quux and matrix-factorization surfaces without
making unit tests depend on sibling repositories.

## What

- Add a default local root matrix.
- Add a dry-run/run script that generates Ladon commands and optional reports.
- Keep predicate checking separate from report generation.

## Non-Goals

- No CI requirement to run sibling-repo matrix.
- No exact golden report snapshots.
- No automatic root discovery yet.
