# Ladon Golden Predicate Regressions

## Why

The pre-registered Quux and matrix-factorization runs gave us stable expected
signals. We need a reusable way to check those signals without exact JSON
snapshots.

## What

- Add a pure predicate evaluator over Ladon report payloads.
- Add a small CLI/script for checking a directory of generated reports.
- Add built-in predicate suites for the Quux/MF live-report layout.

## Non-Goals

- No report generation in this child.
- No timing assertions.
- No hard dependency on sibling repositories in unit tests.
