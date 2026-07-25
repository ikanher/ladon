# `ladon-clean-checkout-and-ci`

Owns tracked-source authority, ignore and lock policy, maintained test
discovery, clean-export gates, Python/Lean CI, isolated distribution smoke, and
release support documentation.

- Start dependencies: none; baseline tracked-source work can start immediately.
- Baseline milestone: tasks 1.1-1.6 and 2.1-2.4 are complete and
  `clean_checkout_gate.py --candidate worktree --baseline-only` passes.
- Completion dependencies: OpenSpec-wide validation waits for reconciliation,
  and final installed-release smoke waits for every other alpha child.
- Enables: trustworthy implementation and release gates for every child.
- Excludes: CLI exit semantics and analyzer algorithms.
- Exit: locked bootstrap, maintained tests, strict quality, real Lean, package
  build, and installed CLI smoke for the completed alpha pass from an explicit
  tracked candidate.
