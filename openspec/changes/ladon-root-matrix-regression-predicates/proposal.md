# Proposal

The root-matrix evidence pass produced useful Quux/MF calibration rows, but the
checks are still manual. Add first-class regression predicates for the root
matrix so future analyzer changes must preserve selected architecture signals.

# Scope

- Add a named `root-matrix` expectation suite.
- Add predicates for review-region presence and root-scope classification.
- Extend the calibration-regression script with `--suite`.
- Run the suite against `temp/root-matrix-evidence-pass/reports`.

# Non-Goals

- No new analyzer findings.
- No target repository changes.
- No claim that root-matrix predicates are complete coverage.
