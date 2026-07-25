## 1. Prerequisite Contract

- [ ] 1.1 Start implementation only after
  `ladon-elaborated-declaration-surface` and report-contract-v2 are stable.
- [ ] 1.2 Define the changelog row schema as a consumer adapter over those
  declaration rows without another Lean helper or declaration inventory.

## 2. Comparison Fixtures

- [ ] 2.1 Add added/removed declaration and rename-candidate fixtures.
- [ ] 2.2 Add proof-only, added/removed assumption, and conservative conclusion
  drift fixtures.
- [ ] 2.3 Add source-evidence, reduced-confidence, backend-authority, and
  theorem-truth nonclaim fixtures.

## 3. Pure Comparator

- [ ] 3.1 Implement pure before/after declaration comparison with stable,
  inspectable raw surfaces.
- [ ] 3.2 Preserve report-v2 source, backend, name-resolution, confidence, and
  quoted-external-evidence boundaries.

## 4. Gates

- [ ] 4.1 Run focused semantic-changelog tests.
- [ ] 4.2 Run `openspec validate ladon-theorem-surface-changelog --strict`.
