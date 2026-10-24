# Bounded exact-result reuse qualification

## Outcome

Task 2.1's bounded exact-result reuse path passed the final end-to-end qualification
in [attempt 04](attempt-04/RESULT.json), which completed in 118.39 seconds under its
30-minute shared deadline. Fresh preparation and checking accepted both generated
goals. A second call regenerated the source-bound plan, reused both accepted receipts,
and completed in 14.04 seconds. Changed assumptions, template revision, source bytes,
and Lean toolchain were rejected without checker authority. An expired deadline returned
incomplete/timeout without authority.

The receipt records a Ladon-added binding to plan ID, generated goal ID/digest/text, and
proof-term digest. The regression in the active frozen test
`test_probe_exact_result_reuse-v7.py` catches cross-goal receipt transplantation when
the same term digest is used. Its pre-fix expected failure was observed and recorded;
the fixed suite passes. Earlier v1-v6 test files and attempts 01-03 remain preserved as
history with board-recorded supersession reasons.

Independent audit finding #807 confirmed that content hashes and bindings provide
integrity/context checks, not writer authentication. The accepted threat boundary is
that the repository-local `.ladon` store contains trusted Ladon-generated results; do
not reuse cache data from an untrusted workspace. A malicious same-user process with
write access to that store can fabricate accepted-looking JSON, and this cache does not
protect against that. The synthetic test receipts exercise the acceptance predicate,
not origin authentication.

## Verification

- Focused application-probe, calibration, and reuse suite: 58 passed.
- Source-goal checker-route consumer regressions: 36 passed.
- Final reuse, CLI, and changed-term checks: 10 passed.
- Ruff on the four production modules and active evidence helpers/tests: passed.
- Scoped strict quality on the four production modules: passed.
- `compileall` on the four production modules: passed.
- Frozen-test registry: 135 records verified; no hash mismatches.
- Strict OpenSpec validation: child and umbrella passed.

The reuse path still requires fresh bounded preparation and an identical plan; cache
reuse does not assert natural-language fidelity, identify a manuscript error, or certify
the whole mathematical method. The independent integrated audit completed with no
remaining code findings after the trusted-local-store assumption was made explicit.

## Implementation surface

The runner and input validator implement preflight deadline handling, aggregate input
bounds, exact receipt binding, reuse reporting, and ordinary checker fallback. The worker
identity, `check-probe --reuse-result` CLI path, OpenSpec requirements/design, frozen
acceptance tests, and the end-to-end harness cover the contract. No dependency or schema
migration was introduced.
