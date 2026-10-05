# Traversal quality progress — 2026-10-02

Native derivation queries now expose their complete owner to the quality gate.
The whole-file `reviewed-schema-hotspot` suppression is removed. Graph validation,
finite budgets, and query envelopes share one private core; the AND/OR solver and
selected slice accumulator have separate iterative owners. Public entrypoints,
artifact identities, wire output, stable alternative ordering, repeated premise
slots, residual routes, and bounded unknown/truncation behavior are preserved.
The SCC owner consumes the same core directly. An unused alternative helper and
redundant return-dispatch code are removed from the solver.

Before decomposition, raw inspection reported solver dispatch complexity 41,
slicer complexity 17, and file maintainability index 2.727; the old marker hid
these findings. The five resulting owner files pass strict radon/vulture/Ruff
checks without suppression. Maximum complexity is 10 across those files, and
their maintainability indices are all above 33. A temporary import-spacing
finding and its repair remain recorded as a checker failure, not a theorem
failure.

Verification uses isolated snapshot `bdd0a0b`, not a commit to the user checkout.
The first focused suite passed 53 tests. The installed wheel passes 367 relevant
tests on each supported Python version (3.11 and 3.12), including derivation,
SCC, observation, stored expansion, receipt, and renderer contracts.

A retained probe compares the archived pre-refactor owner with the candidate on
11,664 exact outcomes: 29 fixed/generated acyclic graphs in both input orders,
three available-leaf sets, nine bound configurations, explicit and invalid
selections, invalid references, legacy evaluation, all four native operations,
and a 1,500-edge deep graph. Source and both isolated installed interpreters
produce the same output digest. This is bounded differential evidence; it does
not prove equivalence for every possible graph or confer checker authority.
The probe, baseline, wheel, source inventory, and logs are bound in
[apply-run-state.json](apply-run-state.json).

The clean-candidate gate passes 2,008 maintained tests and 29 installed CLI
contracts, plus strict quality, compilation/build, distribution/resource, and
collection parity. The required benchmark passes with 17/17 coverage, zero
correctness/stability failures, and passing cache/process controls. OpenSpec
validation, status hygiene, and generated-contract checks pass in the user
workspace. No compatible full child exit is inferred from these scoped checks.

Upstream task 3.15 is complete; the authority/discovery prerequisite is 37/76.
The result umbrella remains 9/50 and its claim child remains 5/8. Full receipt
propagation/monotonicity compatibility and compatible complete upstream exits
remain pending. Canonical claim-target integration stays gated; quantitative
understanding metrics remain deferred.
